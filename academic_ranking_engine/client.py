import os
import re
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx

from academic_ranking_engine.models import PaperMetadata, Author

# Primary & Fallback Endpoints
S2_SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
S2_BULK_URL = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
ARXIV_API_URL = "https://export.arxiv.org/api/query"

S2_DEFAULT_FIELDS = (
    "title,abstract,year,publicationDate,venue,publicationVenue,"
    "citationCount,influentialCitationCount,isOpenAccess,openAccessPdf,"
    "fieldsOfStudy,authors"
)

try:
    from src.fetchers.github_finder import extract_github_url as extract_code_url
except ImportError:
    GITHUB_REGEX = re.compile(r"https?://github\.com/([a-zA-Z0-9_\-]+)/([a-zA-Z0-9_\-\.]+)", re.IGNORECASE)
    def extract_code_url(text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        match = GITHUB_REGEX.search(text)
        if match:
            owner, repo = match.group(1), match.group(2).rstrip(".,;!?:)'\"").removesuffix(".git")
            if owner.lower() not in ["features", "topics", "pulls", "issues"]:
                return f"https://github.com/{owner}/{repo}"
        return None


class AcademicSearchClient:
    """
    Asynchronous scholarly search client with domain locking, rate-limit backoff,
    and automatic endpoint fallback.
    """

    def __init__(self, api_key: Optional[str] = None, timeout: float = 20.0):
        self.api_key = api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
        self.timeout = timeout
        self.headers = {
            "User-Agent": "AcademicRankingEngine/2.0 (mailto:research@academic-agent.org)"
        }
        if self.api_key:
            self.headers["x-api-key"] = self.api_key

    def _parse_s2_item(self, item: Dict[str, Any]) -> Optional[PaperMetadata]:
        title = (item.get("title") or "").strip()
        if not title:
            return None

        pub_date = None
        if item.get("publicationDate"):
            try:
                pub_date = datetime.strptime(item["publicationDate"], "%Y-%m-%d").date()
            except Exception:
                pass

        year = item.get("year") or (pub_date.year if pub_date else datetime.now().year)
        authors = [
            Author(name=a["name"], author_id=a.get("authorId"), h_index=a.get("hIndex"))
            for a in item.get("authors", []) if a.get("name")
        ]

        abstract = (item.get("abstract") or "").strip()
        pub_venue = item.get("publicationVenue") or {}
        venue = pub_venue.get("name") or item.get("venue") or ""
        oa_pdf = item.get("openAccessPdf")
        pdf_url = oa_pdf.get("url") if isinstance(oa_pdf, dict) else None

        return PaperMetadata(
            paper_id=item.get("paperId") or title,
            title=title,
            abstract=abstract or None,
            year=int(year),
            publication_date=pub_date,
            venue=venue,
            fields_of_study=item.get("fieldsOfStudy") or [],
            citation_count=item.get("citationCount") or 0,
            influential_citation_count=item.get("influentialCitationCount") or 0,
            is_open_access=bool(item.get("isOpenAccess") or pdf_url),
            open_access_pdf_url=pdf_url,
            code_url=extract_code_url(abstract),
            authors=authors
        )

    async def fetch_semantic_scholar(
        self,
        query: str,
        year_filter: Optional[str] = None,
        limit: int = 20,
        client: Optional[httpx.AsyncClient] = None
    ) -> List[PaperMetadata]:
        """Queries Semantic Scholar with domain locking and adaptive retries."""
        params = {
            "query": query,
            "fields": S2_DEFAULT_FIELDS,
            "fieldsOfStudy": "Computer Science,Engineering"
        }
        if year_filter:
            params["year"] = year_filter

        # Prioritize bulk search when unauthenticated to prevent CloudFront 429
        endpoint = S2_SEARCH_URL if self.api_key else S2_BULK_URL
        if endpoint == S2_SEARCH_URL:
            params["limit"] = limit

        async_client = client or httpx.AsyncClient(timeout=self.timeout)
        should_close = client is None

        try:
            for attempt in range(3):
                try:
                    await asyncio.sleep(0.3 if self.api_key else 0.8)
                    resp = await async_client.get(endpoint, params=params, headers=self.headers)
                    if resp.status_code == 429:
                        wait = int(resp.headers.get("Retry-After", 3 * (attempt + 1)))
                        await asyncio.sleep(wait)
                        continue
                    if resp.status_code == 200:
                        data = resp.json().get("data", [])
                        papers = []
                        for it in data:
                            parsed = self._parse_s2_item(it)
                            if parsed:
                                papers.append(parsed)
                            if len(papers) >= limit:
                                break
                        return papers
                    elif endpoint == S2_SEARCH_URL and not self.api_key:
                        endpoint = S2_BULK_URL
                        params.pop("limit", None)
                        continue
                except Exception:
                    await asyncio.sleep(1.0)
        finally:
            if should_close:
                await async_client.aclose()
        return []

    async def fetch_arxiv(
        self, query: str, limit: int = 10, client: Optional[httpx.AsyncClient] = None
    ) -> List[PaperMetadata]:
        """ArXiv API fallback if primary scholarly API fails or is depleted."""
        import xml.etree.ElementTree as ET
        from urllib.parse import quote
        url = f"http://export.arxiv.org/api/query?search_query=all:{quote(query)}&start=0&max_results={limit}&sortBy=relevance&sortOrder=descending"
        async_client = client or httpx.AsyncClient(timeout=self.timeout)
        should_close = client is None
        try:
            resp = await async_client.get(url, headers=self.headers)
            if resp.status_code == 200:
                root = ET.fromstring(resp.text)
                papers = []
                for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
                    t = (entry.findtext("{http://www.w3.org/2005/Atom}title") or "").replace("\n", " ").strip()
                    s = (entry.findtext("{http://www.w3.org/2005/Atom}summary") or "").replace("\n", " ").strip()
                    p = entry.findtext("{http://www.w3.org/2005/Atom}published") or str(datetime.now().year)
                    pid = entry.findtext("{http://www.w3.org/2005/Atom}id") or t
                    papers.append(PaperMetadata(
                        paper_id=pid.strip(), title=t, abstract=s, year=int(p[:4]),
                        venue="arXiv", fields_of_study=["Computer Science"],
                        code_url=extract_code_url(s), is_open_access=True
                    ))
                return papers
        except Exception:
            pass
        finally:
            if should_close:
                await async_client.aclose()
        return []


if __name__ == "__main__":
    async def _test():
        client = AcademicSearchClient()
        res = await client.fetch_semantic_scholar("monocular 3d human pose", limit=3)
        print("==================================================")
        print(f"📡 Academic Search Client Diagnostic ({len(res)} papers)")
        print("==================================================")
        for p in res:
            print(f"[*] [{p.year}] {p.title[:65]}... (Cit: {p.citation_count})")
            if p.code_url:
                print(f"    - Code: {p.code_url}")
        print("==================================================")

    asyncio.run(_test())
