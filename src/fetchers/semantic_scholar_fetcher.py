import requests
import time
from src.utils.logger import logger

def fetch_semantic_scholar_papers(query="text-to-motion", max_results=10, min_citations=2):
    """
    Fetches paper metadata from the Semantic Scholar API.
    Includes retry logic for HTTP 429 (Too Many Requests).
    """
    logger.info(f"[*] Searching Semantic Scholar for query: '{query}'...")
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    
    params = {
        "query": query,
        "limit": max_results * 5, 
        "fields": "title,year,abstract,citationCount,venue,url,paperId,openAccessPdf"
    }
    
    papers = []
    
    # Retry logic for rate limiting (429 Error)
    max_retries = 3
    response = None
    
    for attempt in range(max_retries):
        try:
            # Semantic Scholar limits unauthenticated API heavily.
            # Increased to 3 seconds base delay as requested.
            time.sleep(3) 
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            break # Success, break out of retry loop
            
        except requests.exceptions.HTTPError as e:
            if response is not None and response.status_code == 429:
                logger.warning(f"[!] Semantic Scholar 429 Rate Limit hit. Retrying in 5 seconds (Attempt {attempt + 1}/{max_retries})...")
                time.sleep(5)
            else:
                logger.error(f"[!] HTTP Error fetching from Semantic Scholar: {e}")
                return papers
        except requests.exceptions.RequestException as e:
            logger.error(f"[!] Error fetching from Semantic Scholar: {e}")
            return papers

    if not response or response.status_code != 200:
        logger.error("[!] Failed to fetch from Semantic Scholar after retries.")
        return papers
        
    try:
        data = response.json()
        for item in data.get('data', []):
            if not item.get('abstract'):
                continue
                
            citations = item.get('citationCount', 0)
            if citations < min_citations:
                continue
            
            paper_id = item.get('paperId')
            paper_url = item.get('url') or (f"https://www.semanticscholar.org/paper/{paper_id}" if paper_id else "No URL")
            
            pdf_url = None
            oa_data = item.get('openAccessPdf')
            if oa_data and isinstance(oa_data, dict):
                pdf_url = oa_data.get('url')
                
            papers.append({
                "title": item.get('title', '').strip(),
                "year": str(item.get('year', '')),
                "abstract": item.get('abstract', '').strip(),
                "url": paper_url,
                "pdf_url": pdf_url, 
                "citations": citations,
                "venue": item.get('venue', 'Unknown'),
                "source": "SemanticScholar"
            })
            
            if len(papers) >= max_results:
                break
                
    except Exception as e:
        logger.error(f"[!] Error parsing Semantic Scholar JSON: {e}")
        
    return papers
