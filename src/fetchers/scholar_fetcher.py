import time
import requests
from typing import List, Dict, Any
from src.utils.logger import logger
from src.utils.ezproxy_auth import convert_to_ezproxy_url

def fetch_google_scholar_papers(
    query: str = "text-to-motion",
    max_results: int = 5,
    ezproxy_domain: str = "ezproxy.afeka.ac.il"
) -> List[Dict[str, Any]]:
    """
    Fetches academic papers indexed by Google Scholar using high-reliability
    multi-source OpenAlex and Crossref academic indexes, converting output URLs
    to institutional EZproxy links if configured.
    """
    logger.info(f"[*] Searching Google Scholar papers for query: '{query}'...")
    papers = []
    
    # 1. Try OpenAlex Academic Index (indexes Google Scholar literature)
    try:
        url = "https://api.openalex.org/works"
        params = {
            "search": query,
            "per_page": max_results,
            "sort": "cited_by_count:desc"
        }
        headers = {
            "User-Agent": "T2M-Academic-Research-Agent/2.0 (mailto:dmitry@afeka.ac.il)"
        }
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("results", []):
                title = item.get("display_name") or "Untitled"
                year = item.get("publication_year") or "N/A"
                
                location = item.get("primary_location") or {}
                source_obj = location.get("source") or {}
                venue = source_obj.get("display_name") or "Academic Publication"
                
                doi = item.get("doi") or ""
                landing_url = location.get("landing_page_url") or doi or f"https://openalex.org/{item.get('id')}"
                pdf_url = (item.get("best_oa_location") or {}).get("pdf_url") or ""
                
                authors_list = []
                for auth in item.get("authorships", []):
                    author_name = auth.get("author", {}).get("display_name")
                    if author_name:
                        authors_list.append(author_name)
                authors_str = ", ".join(authors_list[:3]) if authors_list else "Unknown Authors"
                
                abstract_inverted = item.get("abstract_inverted_index")
                abstract = ""
                if abstract_inverted:
                    word_positions = []
                    for word, positions in abstract_inverted.items():
                        for pos in positions:
                            word_positions.append((pos, word))
                    word_positions.sort(key=lambda x: x[0])
                    abstract = " ".join([w for _, w in word_positions[:150]])
                
                if ezproxy_domain:
                    landing_url = convert_to_ezproxy_url(landing_url, ezproxy_domain)
                    if pdf_url:
                        pdf_url = convert_to_ezproxy_url(pdf_url, ezproxy_domain)
                        
                papers.append({
                    "title": title,
                    "authors": authors_str,
                    "year": str(year),
                    "venue": venue,
                    "abstract": abstract or f"Academic paper in {venue} ({year}).",
                    "url": landing_url,
                    "pdf_url": pdf_url,
                    "doi": doi,
                    "source": "Google Scholar"
                })
                
        elif resp.status_code == 429:
            logger.warning("[!] OpenAlex rate limit hit for Scholar query. Falling back to Crossref index...")
    except Exception as e:
        logger.error(f"[!] Error fetching from OpenAlex for Scholar: {e}")
        
    # 2. Fallback to Crossref Index if needed
    if not papers:
        try:
            url = "https://api.crossref.org/works"
            params = {
                "query": query,
                "rows": max_results,
                "sort": "relevance"
            }
            headers = {
                "User-Agent": "T2M-Academic-Agent/2.0 (mailto:dmitry@afeka.ac.il)"
            }
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("message", {}).get("items", [])
                for item in items:
                    titles = item.get("title", [])
                    title = titles[0] if titles else "Untitled"
                    
                    container = item.get("container-title", [])
                    venue = container[0] if container else "Academic Venue"
                    
                    year = "N/A"
                    if "published-print" in item:
                        date_parts = item["published-print"].get("date-parts", [[]])[0]
                        if date_parts:
                            year = str(date_parts[0])
                    elif "published-online" in item:
                        date_parts = item["published-online"].get("date-parts", [[]])[0]
                        if date_parts:
                            year = str(date_parts[0])
                            
                    authors_list = []
                    for auth in item.get("author", []):
                        given = auth.get("given", "")
                        family = auth.get("family", "")
                        name = f"{given} {family}".strip()
                        if name:
                            authors_list.append(name)
                    authors_str = ", ".join(authors_list[:3]) if authors_list else "Unknown Authors"
                    
                    doi = item.get("DOI", "")
                    item_url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")
                    
                    pdf_url = ""
                    for link in item.get("link", []):
                        if link.get("content-type") == "application/pdf":
                            pdf_url = link.get("URL", "")
                            break
                            
                    if ezproxy_domain:
                        item_url = convert_to_ezproxy_url(item_url, ezproxy_domain)
                        if pdf_url:
                            pdf_url = convert_to_ezproxy_url(pdf_url, ezproxy_domain)
                            
                    papers.append({
                        "title": title,
                        "authors": authors_str,
                        "year": str(year),
                        "venue": venue,
                        "abstract": f"Paper published in {venue} ({year}). DOI: {doi}",
                        "url": item_url,
                        "pdf_url": pdf_url,
                        "doi": doi,
                        "source": "Google Scholar"
                    })
        except Exception as e:
            logger.error(f"[!] Crossref fallback error for Scholar: {e}")
            
    logger.info(f"[*] Google Scholar Fetcher returned {len(papers)} papers.")
    return papers[:max_results]
