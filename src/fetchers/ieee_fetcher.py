import os
import requests
import time
import agent_config as config
from src.utils.logger import logger
from src.auth.ezproxy_auth import convert_to_ezproxy_url

def fetch_ieee_papers(query=config.DEFAULT_SEARCH_QUERY, max_results=config.MAX_RESULTS_PER_DOMAIN, ezproxy_domain=config.EZPROXY_DOMAIN_DEFAULT):
    """
    Fetches IEEE paper metadata using OpenAlex or Crossref API (filtered for 10.1109 IEEE DOIs)
    or IEEE Xplore API if IEEE_API_KEY is configured in environment.
    
    Converts article URLs to institutional EZproxy URLs for seamless full-text PDF download.
    """
    ieee_api_key = os.getenv("IEEE_API_KEY")
    papers = []
    
    if ieee_api_key:
        logger.info(f"[*] Searching IEEE Xplore official REST API for query: '{query}'...")
        papers = _fetch_from_ieee_api(query, ieee_api_key, max_results, ezproxy_domain)
        if papers:
            return papers
            
    logger.info(f"[*] Searching IEEE papers via OpenAlex Academic index for query: '{query}'...")
    papers = _fetch_from_openalex_ieee(query, max_results, ezproxy_domain)
    
    if not papers:
        logger.info(f"[*] Searching IEEE papers via Crossref IEEE index (10.1109) for query: '{query}'...")
        papers = _fetch_from_crossref_ieee(query, max_results, ezproxy_domain)
        
    return papers


def _fetch_from_openalex_ieee(query, max_results, ezproxy_domain):
    url = "https://api.openalex.org/works"
    user_email = os.getenv("IEEE_USERNAME", "dmitry.strizhak@s.afeka.ac.il")
    headers = {'User-Agent': f'T2MResearchAgent/2.0 (mailto:{user_email})'}
    
    params = {
        'filter': f'display_name.search:{query}',
        'per_page': max_results * 5,
        'sort': 'cited_by_count:desc',
        'mailto': user_email
    }
    
    papers = []
    response = None
    
    for attempt in range(1, 3):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=8)
            if response.status_code == 429:
                logger.warning(f"[!] OpenAlex Rate Limit hit. Retrying in 2s (Attempt {attempt}/2)...")
                time.sleep(2)
                continue
            elif response.status_code == 200:
                break
        except Exception as e:
            logger.error(f"[!] OpenAlex request exception: {e}")

    if not response or response.status_code != 200:
        return papers

    try:
        data = response.json()
        results = data.get('results', [])
        
        for item in results:
            doi = item.get('doi') or ''
            loc = item.get('primary_location') or {}
            src = loc.get('source') or {}
            venue = src.get('display_name') or 'IEEE Conference/Journal'
            publisher = src.get('publisher') or ''
            
            doi_str = str(doi) if doi else ''
            venue_str = str(venue) if venue else ''
            publisher_str = str(publisher) if publisher else ''
            
            is_ieee = ("10.1109" in doi_str) or ("ieee" in venue_str.lower()) or ("ieee" in publisher_str.lower())
            
            title = item.get('title', '')
            if not title:
                continue
            title = str(title).strip()
            
            if not is_ieee:
                continue
                
            pub_year = item.get('publication_year', '')
            citations = item.get('cited_by_count', 0)
            
            abstract = ""
            inv_abstract = item.get('abstract_inverted_index')
            if inv_abstract and isinstance(inv_abstract, dict):
                word_positions = []
                for word, pos_list in inv_abstract.items():
                    for pos in pos_list:
                        word_positions.append((pos, word))
                word_positions.sort()
                abstract = " ".join([w for _, w in word_positions])
                
            # 1. Check locations for direct PDF URL
            pdf_url = loc.get('pdf_url')
            if not pdf_url:
                best_oa = item.get('best_oa_location') or {}
                pdf_url = best_oa.get('pdf_url')
            if not pdf_url:
                for location in item.get('locations', []):
                    if location.get('pdf_url'):
                        pdf_url = location.get('pdf_url')
                        break

            # 2. Extract article number from landing URL or DOI if available
            landing_url = loc.get('landing_page_url') or doi_str
            ieee_url = landing_url if landing_url else (doi_str if doi_str else f"https://ieeexplore.ieee.org/search/searchresult.jsp?newsearch=true&queryText={title}")

            if not pdf_url and "10.1109" in doi_str:
                m = re.search(r'arnumber=(\d+)', landing_url) or re.search(r'/document/(\d+)', landing_url) or re.search(r'(\d{7,8})', doi_str)
                if m:
                    pdf_url = f"https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber={m.group(1)}"
                else:
                    pdf_url = doi_str if doi_str.startswith("http") else f"https://doi.org/{doi_str}"

            if ezproxy_domain and pdf_url:
                ez_pdf_url = convert_to_ezproxy_url(pdf_url, ezproxy_domain)
            else:
                ez_pdf_url = pdf_url

            papers.append({
                "title": title,
                "year": str(pub_year),
                "abstract": abstract if abstract else f"Paper published in {venue_str}.",
                "url": convert_to_ezproxy_url(ieee_url, ezproxy_domain) if ezproxy_domain else ieee_url,
                "pdf_url": ez_pdf_url,
                "citations": citations,
                "venue": venue_str,
                "source": "IEEE Xplore (OpenAlex)"
            })
            
            if len(papers) >= max_results:
                break
                
    except Exception as e:
        logger.error(f"[!] Error processing OpenAlex IEEE results: {e}")
        
    return papers


def _fetch_from_crossref_ieee(query, max_results, ezproxy_domain):
    url = "https://api.crossref.org/works"
    params = {
        "query": query,
        "filter": "prefix:10.1109",
        "rows": max_results * 2,
        "sort": "relevance"
    }
    user_email = os.getenv("IEEE_USERNAME", "dmitry.strizhak@s.afeka.ac.il")
    headers = {'User-Agent': f'T2MResearchAgent/2.0 (mailto:{user_email})'}
    papers = []
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            items = r.json().get('message', {}).get('items', [])
            for item in items:
                title_list = item.get('title', [])
                title = title_list[0] if title_list else ''
                doi = item.get('DOI', '')
                pub_year = item.get('created', {}).get('date-parts', [[2023]])[0][0]
                container = item.get('container-title', ['IEEE Conference/Journal'])
                venue = container[0] if container else 'IEEE'
                
                if not title or not doi:
                    continue
                    
                arnumber = doi.split("10.1109/")[-1].split(".")[0] if "10.1109/" in doi else ""
                ieee_url = f"https://doi.org/{doi}"
                pdf_url = f"https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber={arnumber}" if arnumber else ieee_url
                
                abstract_raw = item.get('abstract', '')
                # Clean basic HTML tags in Crossref abstracts if present
                clean_abstract = re.sub(r'<[^>]+>', '', abstract_raw) if abstract_raw else f"IEEE publication from {venue} (DOI: {doi})."
                
                papers.append({
                    "title": title,
                    "year": str(pub_year),
                    "abstract": clean_abstract,
                    "url": convert_to_ezproxy_url(ieee_url, ezproxy_domain) if ezproxy_domain else ieee_url,
                    "pdf_url": convert_to_ezproxy_url(pdf_url, ezproxy_domain) if ezproxy_domain else pdf_url,
                    "citations": item.get('is-referenced-by-count', 0),
                    "venue": venue,
                    "source": "IEEE Xplore (Crossref)"
                })
                
                if len(papers) >= max_results:
                    break
    except Exception as e:
        logger.error(f"[!] Error fetching from Crossref IEEE API: {e}")
        
    return papers


def _fetch_from_ieee_api(query, api_key, max_results, ezproxy_domain):
    url = "https://ieeexploreapi.ieee.org/api/v1/search/articles"
    params = {
        "apikey": api_key,
        "querytext": query,
        "max_records": max_results,
        "format": "json"
    }
    papers = []
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200:
            data = res.json()
            articles = data.get("articles", [])
            for art in articles:
                title = art.get("title", "").strip()
                abstract = art.get("abstract", "").strip()
                pub_year = art.get("publication_year", "")
                arnumber = art.get("article_number", "")
                pdf_url = art.get("pdf_url") or f"https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber={arnumber}"
                article_url = art.get("html_url") or f"https://ieeexplore.ieee.org/document/{arnumber}"
                
                papers.append({
                    "title": title,
                    "year": str(pub_year),
                    "abstract": abstract,
                    "url": convert_to_ezproxy_url(article_url, ezproxy_domain),
                    "pdf_url": convert_to_ezproxy_url(pdf_url, ezproxy_domain),
                    "citations": int(art.get("citing_paper_count", 0)),
                    "venue": art.get("publication_title", "IEEE"),
                    "source": "IEEE Xplore API"
                })
    except Exception as e:
        logger.error(f"[!] Error fetching from IEEE REST API: {e}")
        
    return papers

if __name__ == "__main__":
    results = fetch_ieee_papers("text-to-motion", max_results=2)
    print(f"[*] Fetched {len(results)} IEEE test papers.")
