import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import agent_config as config
from src.utils.logger import logger

def fetch_arxiv_papers(query=config.DEFAULT_SEARCH_QUERY, max_results=config.MAX_RESULTS_PER_DOMAIN):
    """
    Fetches paper metadata from the ArXiv API, sorted by relevance to find high-impact core papers.
    """
    logger.info(f"[*] Searching ArXiv for query: '{query}'...")
    url = f'http://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(query)}&start=0&max_results={max_results}&sortBy=relevance&sortOrder=descending'
    
    papers = []
    try:
        data = urllib.request.urlopen(url)
        xml_data = data.read().decode('utf-8')
        root = ET.fromstring(xml_data)
        
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            title = entry.find('{http://www.w3.org/2005/Atom}title').text.replace('\n', ' ')
            summary = entry.find('{http://www.w3.org/2005/Atom}summary').text.replace('\n', ' ')
            published = entry.find('{http://www.w3.org/2005/Atom}published').text
            paper_url = entry.find('{http://www.w3.org/2005/Atom}id').text
            
            pdf_url = paper_url.replace('/abs/', '/pdf/') + ".pdf"
            
            papers.append({
                "title": title.strip(),
                "year": published.split('-')[0],
                "abstract": summary.strip(),
                "url": paper_url.strip(),
                "pdf_url": pdf_url.strip(),
                "source": "ArXiv"
            })
    except Exception as e:
        logger.error(f"[!] Error fetching from ArXiv: {e}")
        
    return papers


if __name__ == "__main__":
    results = fetch_arxiv_papers(max_results=2)
    print(f"[*] Fetched {len(results)} ArXiv test papers.")

