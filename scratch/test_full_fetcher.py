import time
from typing import List, Dict, Any, Optional
import requests
import agent_config as config
from src.utils.logger import logger
from src.fetchers.github_finder import extract_github_url


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


def _fetch_bulk_search(
    query: str,
    headers: Dict[str, str],
    max_results: int,
    min_citations: int
) -> List[Dict[str, Any]]:
    """
    Fallback endpoint using Semantic Scholar Bulk Search.
    Highly resilient against CloudFront HTTP 429 rate-limiting on standard search.
    """
    url = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
    params = {
        "query": query,
        "fields": "title,year,abstract,citationCount,venue,url,paperId,openAccessPdf"
    }
    logger.info(f"[*] Semantic Scholar: Querying Bulk Search fallback for '{query}'...")
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            papers = []
            for item in data.get('data', []):
                p = _parse_paper_item(item, min_citations=min_citations)
                if p:
                    papers.append(p)
                if len(papers) >= max_results:
                    break
            logger.info(f"[+] Bulk Search fallback secured {len(papers)} papers.")
            return papers
        else:
            logger.warning(f"[!] Bulk Search returned HTTP {resp.status_code}: {resp.text[:150]}")
    except Exception as e:
        logger.error(f"[!] Bulk Search request error: {e}")
    return []


def fetch_semantic_scholar_papers(
    query: str = config.DEFAULT_SEARCH_QUERY,
    max_results: int = config.MAX_RESULTS_PER_DOMAIN,
    min_citations: Optional[int] = None,
    api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetches paper metadata from the Semantic Scholar API.
    Supports API key authentication, fast bulk search fallback on 429, and relaxed citations.
    """
    if min_citations is None:
        min_citations = getattr(config, "SEMANTIC_SCHOLAR_MIN_CITATIONS", 0)
    key = api_key or getattr(config, "SEMANTIC_SCHOLAR_API_KEY", "")

    headers = {"User-Agent": "T2M-Academic-Research-Agent/2.0"}
    if key:
        headers["x-api-key"] = key

    logger.info(f"[*] Searching Semantic Scholar (Auth: {'Key' if key else 'Public'}) for: '{query}'...")
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": max_results * 4,
        "fields": "title,year,abstract,citationCount,venue,url,paperId,openAccessPdf"
    }

    papers = []
    max_retries = 3 if key else 1
    backoff_delays = [3, 6, 12]
    response = None

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                time.sleep(backoff_delays[attempt - 1])
            response = requests.get(url, params=params, headers=headers, timeout=12)
            if response.status_code == 429:
                if not key:
                    logger.warning("[!] Semantic Scholar 429 Rate Limit hit (Unauthenticated). Switching immediately to Bulk Search fallback...")
                    return _fetch_bulk_search(query, headers, max_results, min_citations)
                retry_hdr = response.headers.get("Retry-After")
                wait_sec = int(retry_hdr) if retry_hdr and retry_hdr.isdigit() else backoff_delays[attempt]
                logger.warning(f"[!] Semantic Scholar 429 Rate Limit with Key. Backing off {wait_sec}s (Attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait_sec)
                continue
            response.raise_for_status()
            break
        except requests.exceptions.HTTPError as e:
            if response is not None and response.status_code == 429:
                continue
            logger.error(f"[!] HTTP Error fetching from Semantic Scholar: {e}")
            break
        except requests.exceptions.RequestException as e:
            logger.error(f"[!] Request exception from Semantic Scholar: {e}")
            break

    if not response or response.status_code != 200:
        logger.warning("[!] Primary Semantic Scholar search throttled/failed. Engaging bulk fallback...")
        return _fetch_bulk_search(query, headers, max_results, min_citations)

    try:
        data = response.json()
        for item in data.get('data', []):
            p = _parse_paper_item(item, min_citations=min_citations)
            if p:
                papers.append(p)
            if len(papers) >= max_results:
                break
    except Exception as e:
        logger.error(f"[!] Error parsing Semantic Scholar JSON: {e}")

    if not papers:
        logger.info("[*] Primary search returned 0 papers with abstracts. Querying bulk fallback...")
        return _fetch_bulk_search(query, headers, max_results, min_citations)

    return papers


if __name__ == "__main__":
    for q in ["text to motion kinematics", "3d human pose estimation SMPL"]:
        res = fetch_semantic_scholar_papers(q, max_results=3)
        print(f"Results for '{q}': {len(res)}")
        for p in res:
            print(f" - {p['title']} ({p['year']}) | cit: {p['citations']}")
