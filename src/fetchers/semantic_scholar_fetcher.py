import time
from typing import List, Dict, Any, Optional
import requests
import agent_config as config
from src.utils.logger import logger
from src.fetchers.github_finder import extract_github_url

S2_FIELDS = "title,year,abstract,citationCount,venue,url,paperId,openAccessPdf"


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

    return {
        "title": (item.get('title') or '').strip(),
        "year": str(item.get('year') or ''),
        "abstract": abstract_text,
        "url": paper_url,
        "pdf_url": pdf_url,
        "github_url": extract_github_url(abstract_text) or "N/A",
        "citations": citations,
        "venue": item.get('venue') or 'Unknown',
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
    """Executes a query against a Semantic Scholar endpoint with resilient backoff."""
    backoff_delays = [4, 8, 14]
    for attempt in range(3):
        try:
            time.sleep(2.5)  # Politeness interval to prevent burst limits
            resp = requests.get(url, params=params, headers=headers, timeout=20)
            if resp.status_code == 429:
                retry_hdr = resp.headers.get("Retry-After")
                wait_sec = int(retry_hdr) if retry_hdr and retry_hdr.isdigit() else backoff_delays[attempt]
                logger.warning(f"[!] Semantic Scholar ({endpoint_name}) 429 Rate Limit. Backing off {wait_sec}s (Attempt {attempt + 1}/3)...")
                time.sleep(wait_sec)
                continue
            if resp.status_code == 200:
                data = resp.json().get('data', [])
                papers = []
                for it in data:
                    p = _parse_paper_item(it, min_citations=min_citations)
                    if p:
                        papers.append(p)
                    if len(papers) >= max_results:
                        break
                if papers:
                    logger.info(f"[+] Semantic Scholar ({endpoint_name}) retrieved {len(papers)} papers.")
                    return papers
                else:
                    logger.info(f"[*] Semantic Scholar ({endpoint_name}) returned {len(data)} items but 0 matching abstracts.")
                    return []
            else:
                logger.warning(f"[!] Semantic Scholar ({endpoint_name}) returned HTTP {resp.status_code}: {resp.text[:120]}")
                break
        except Exception as e:
            logger.error(f"[!] Semantic Scholar ({endpoint_name}) error: {e}")
            time.sleep(2.0)
    return []


def fetch_semantic_scholar_papers(
    query: str = config.DEFAULT_SEARCH_QUERY,
    max_results: int = config.MAX_RESULTS_PER_DOMAIN,
    min_citations: Optional[int] = None,
    api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetches paper metadata from Semantic Scholar API.
    When unauthenticated, prioritizes Bulk Search to bypass CloudFront standard search 429 blocks.
    When an API key is provided, prioritizes authenticated Standard Search.
    """
    if min_citations is None:
        min_citations = getattr(config, "SEMANTIC_SCHOLAR_MIN_CITATIONS", 0)
    key = api_key or getattr(config, "SEMANTIC_SCHOLAR_API_KEY", "")

    headers = {"User-Agent": "T2M-Academic-Research-Agent/2.0"}
    if key:
        headers["x-api-key"] = key

    bulk_url = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
    search_url = "https://api.semanticscholar.org/graph/v1/paper/search"

    # Define endpoint priority:
    # Authenticated: Primary -> Standard Search, Secondary -> Bulk Search
    # Unauthenticated: Primary -> Bulk Search (high throughput, no 429), Secondary -> Standard Search
    if key:
        endpoints = [
            (search_url, {"query": query, "limit": max_results * 4, "fields": S2_FIELDS}, "Standard Search (Auth)"),
            (bulk_url, {"query": query, "fields": S2_FIELDS}, "Bulk Search Fallback")
        ]
    else:
        endpoints = [
            (bulk_url, {"query": query, "fields": S2_FIELDS}, "Bulk Search (Public)"),
            (search_url, {"query": query, "limit": max_results * 4, "fields": S2_FIELDS}, "Standard Search Fallback")
        ]

    for url, params, name in endpoints:
        papers = _query_endpoint(url, params, headers, max_results, min_citations, name)
        if papers:
            return papers

    return []


if __name__ == "__main__":
    print("==================================================")
    print("🔬 Semantic Scholar Fetcher Diagnostic")
    print("==================================================")
    test_queries = [
        "kinematic human motion generation",
        "3d human pose estimation SMPL"
    ]
    for tq in test_queries:
        res = fetch_semantic_scholar_papers(query=tq, max_results=3)
        print(f"[*] Query: '{tq}' -> Retrieved {len(res)} papers")
        for p in res:
            print(f"    - [{p.get('year')}] {p.get('title')} (Citations: {p.get('citations')})")
    print("==================================================")
