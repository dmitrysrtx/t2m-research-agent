import time
from typing import List, Dict, Any, Optional
import requests
import agent_config as config
from src.utils.logger import logger
from src.fetchers.github_finder import extract_github_url

S2_FIELDS = "title,year,abstract,citationCount,influentialCitationCount,venue,publicationVenue,url,paperId,openAccessPdf,externalIds"


def _parse_paper_item(item: Dict[str, Any], min_citations: int = 0) -> Optional[Dict[str, Any]]:
    """Standardizes a raw Semantic Scholar paper record into the pipeline format."""
    abstract_text = (item.get('abstract') or '').strip()
    if not abstract_text:
        return None

    citations = item.get('citationCount') or 0
    if citations < min_citations:
        return None

    paper_id = item.get('paperId')
    paper_url = item.get('url') or (f"https://www.semanticscholar.org/paper/{paper_id}" if paper_id else "No URL")

    pdf_url = None
    oa_data = item.get('openAccessPdf')
    if oa_data and isinstance(oa_data, dict):
        pdf_url = oa_data.get('url')

    ext_ids = item.get('externalIds') or {}
    arxiv_id = ext_ids.get('ArXiv') or ext_ids.get('arxiv')
    doi = ext_ids.get('DOI') or ext_ids.get('doi')
    arxiv_url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None
    if not pdf_url and arxiv_id:
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    pub_venue = item.get('publicationVenue')
    venue_name = (pub_venue.get('name') if isinstance(pub_venue, dict) else None) or item.get('venue') or 'Unknown'

    return {
        "title": (item.get('title') or '').strip(),
        "year": str(item.get('year') or ''),
        "abstract": abstract_text,
        "url": paper_url,
        "pdf_url": pdf_url,
        "arxiv_id": arxiv_id,
        "arxiv_url": arxiv_url,
        "doi": doi,
        "github_url": extract_github_url(abstract_text) or "N/A",
        "citations": citations,
        "influential_citations": item.get('influentialCitationCount') or 0,
        "venue": venue_name,
        "source": "SemanticScholar"
    }


def _query_endpoint(
    url: str,
    params: Dict[str, Any],
    headers: Dict[str, str],
    max_results: int,
    min_citations: int,
    endpoint_name: str
) -> List[Dict[str, Any]]:
    """Executes a query against Semantic Scholar endpoint with resilient backoff."""
    backoff_delays = [3, 6, 10]
    for attempt in range(3):
        try:
            time.sleep(1.2)  # Polite spacing to avoid burst rate limits
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            if resp.status_code == 429:
                retry_hdr = resp.headers.get("Retry-After")
                wait_sec = int(retry_hdr) if retry_hdr and retry_hdr.isdigit() else backoff_delays[attempt]
                logger.warning(f"[!] Semantic Scholar ({endpoint_name}) 429. Backoff {wait_sec}s (Attempt {attempt+1}/3)...")
                time.sleep(wait_sec)
                continue
            if resp.status_code == 200:
                data = resp.json().get('data', [])
                papers = []
                for it in data:
                    p = _parse_paper_item(it, min_citations=min_citations)
                    if p:
                        papers.append(p)
                # If emergency bulk search was used, sort candidates to prioritize recent & cited papers
                if "bulk" in url.lower():
                    papers.sort(
                        key=lambda x: (int(x.get('year') or 0) >= 2019, x.get('citations', 0), int(x.get('year') or 0)),
                        reverse=True
                    )
                if papers:
                    logger.info(f"[+] Semantic Scholar ({endpoint_name}) retrieved {len(papers[:max_results])} papers.")
                    return papers[:max_results]
                return []
            else:
                logger.warning(f"[!] Semantic Scholar ({endpoint_name}) HTTP {resp.status_code}: {resp.text[:100]}")
                break
        except Exception as e:
            logger.error(f"[!] Semantic Scholar ({endpoint_name}) error: {e}")
            time.sleep(1.5)
    return []


def fetch_semantic_scholar_papers(
    query: str = config.DEFAULT_SEARCH_QUERY,
    max_results: int = config.MAX_RESULTS_PER_DOMAIN,
    min_citations: Optional[int] = None,
    api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetches paper metadata from Semantic Scholar API.
    Enforces Computer Science & Engineering domain filtering.
    Always prioritizes relevance-ranked Standard Search over unranked Bulk Search.
    """
    if min_citations is None:
        min_citations = getattr(config, "SEMANTIC_SCHOLAR_MIN_CITATIONS", 0)
    key = api_key or getattr(config, "SEMANTIC_SCHOLAR_API_KEY", "")
    fields_of_study = getattr(config, "SEMANTIC_SCHOLAR_FIELDS_OF_STUDY", "Computer Science,Engineering")

    headers = {"User-Agent": "T2M-Academic-Research-Agent/2.0"}
    if key:
        headers["x-api-key"] = key

    search_url = "https://api.semanticscholar.org/graph/v1/paper/search"
    bulk_url = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"

    search_params = {
        "query": query,
        "limit": min(max_results * 3, 50),
        "fields": S2_FIELDS,
        "fieldsOfStudy": fields_of_study
    }
    bulk_params = {
        "query": query,
        "fields": S2_FIELDS,
        "fieldsOfStudy": fields_of_study
    }

    # Primary: Relevance-ranked Standard Search (with 429 adaptive backoff)
    papers = _query_endpoint(search_url, search_params, headers, max_results, min_citations, "Standard Search")
    if papers:
        return papers

    # Emergency Fallback: Bulk Search with CS domain & post-sorting by year/citations
    logger.info("[*] Falling back to Semantic Scholar Bulk Search (CS Domain)...")
    return _query_endpoint(bulk_url, bulk_params, headers, max_results, min_citations, "Bulk Search Fallback")


if __name__ == "__main__":
    print("==================================================")
    print("🔬 Semantic Scholar Fetcher CS Domain Diagnostic")
    print("==================================================")
    test_q = "kinematic human motion generation"
    res = fetch_semantic_scholar_papers(query=test_q, max_results=3)
    print(f"[*] Query: '{test_q}' -> Retrieved {len(res)} papers")
    for p in res:
        print(f"    - [{p.get('year')}] {p.get('title')}")
        print(f"      Venue: {p.get('venue')} | Citations: {p.get('citations')} | Inf: {p.get('influential_citations')}")
        print(f"      ArXiv: {p.get('arxiv_id')} | PDF: {p.get('pdf_url')}")
    print("==================================================")
