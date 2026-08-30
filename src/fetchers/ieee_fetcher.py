import os
import requests
import time
from src.utils.logger import logger
from src.utils.ezproxy_auth import convert_to_ezproxy_url

def fetch_ieee_papers(query="text-to-motion", max_results=10, ezproxy_domain="ezproxy.afeka.ac.il"):
    """
    Fetches IEEE paper metadata using OpenAlex (filtered for IEEE DOIs / venues)
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
    return _fetch_from_openalex_ieee(query, max_results, ezproxy_domain)


def _fetch_from_openalex_ieee(query, max_results, ezproxy_domain):
    url = "https://api.openalex.org/works"
    headers = {'User-Agent': 'T2MResearchAgent/1.0 (mailto:academic@example.com)'}
    
    params = {
        'filter': f'display_name.search:{query}',
        'per_page': max_results * 3,
        'sort': 'cited_by_count:desc'
    }
    
    papers = []
    try:
        response = requests.get(url, headers=headers, params=params, timeout=12)
        if response.status_code != 200:
            logger.error(f"[!] OpenAlex API returned status {response.status_code}")
            return papers
            
        data = response.json()
        results = data.get('results', [])
        
        for item in results:
            doi = item.get('doi', '')
            loc = item.get('primary_location') or {}
            src = loc.get('source') or {}
            venue = src.get('display_name') or 'IEEE Conference/Journal'
            publisher = src.get('publisher') or ''
            
            # Filter for IEEE publications or IEEE DOIs (10.1109/...)
            is_ieee = ("10.1109" in doi) or ("ieee" in venue.lower()) or ("ieee" in publisher.lower())
            if not is_ieee:
                continue
                
            title = item.get('title', '').strip()
            if not title:
                continue
                
            pub_year = item.get('publication_year', '')
            citations = item.get('cited_by_count', 0)
            
            # Reconstruct abstract from OpenAlex inverted index
            abstract = ""
            inv_abstract = item.get('abstract_inverted_index')
            if inv_abstract and isinstance(inv_abstract, dict):
                word_positions = []
                for word, pos_list in inv_abstract.items():
                    for pos in pos_list:
                        word_positions.append((pos, word))
                word_positions.sort()
                abstract = " ".join([w for _, w in word_positions])
                
            # Extract IEEE arnumber if available
            arnumber = None
            ieee_url = None
            
            if doi and "10.1109" in doi:
                doi_suffix = doi.split("10.1109/")[-1]
                # Check if arnumber is inside doi_suffix
                # e.g. 10.1109/TPAMI.2024.3355414 or direct arnumber
                try:
                    # Resolve DOI to get final IEEE URL
                    res = requests.head(doi, allow_redirects=True, timeout=5)
                    if "ieeexplore.ieee.org" in res.url:
                        ieee_url = res.url
                        # Extract arnumber from URL like /document/10416192/
                        if "/document/" in res.url:
                            arnumber = res.url.split("/document/")[1].split("/")[0]
                except Exception:
                    pass

            if not ieee_url:
                ieee_url = doi if doi else f"https://ieeexplore.ieee.org/search/searchresult.jsp?newsearch=true&queryText={title}"

            pdf_url = None
            if arnumber:
                pdf_url = f"https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber={arnumber}"
            elif "ieeexplore.ieee.org" in ieee_url:
                pdf_url = ieee_url
                
            # Convert to EZproxy URL if domain is configured
            if ezproxy_domain and pdf_url:
                ez_pdf_url = convert_to_ezproxy_url(pdf_url, ezproxy_domain)
            else:
                ez_pdf_url = pdf_url

            papers.append({
                "title": title,
                "year": str(pub_year),
                "abstract": abstract if abstract else f"Paper published in {venue}.",
                "url": convert_to_ezproxy_url(ieee_url, ezproxy_domain) if ezproxy_domain else ieee_url,
                "pdf_url": ez_pdf_url,
                "citations": citations,
                "venue": venue,
                "source": "IEEE Xplore (OpenAlex)"
            })
            
            if len(papers) >= max_results:
                break
                
    except Exception as e:
        logger.error(f"[!] Error querying OpenAlex for IEEE papers: {e}")
        
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
