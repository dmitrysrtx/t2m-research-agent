import os
import re
import requests
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import time
from src.utils.logger import logger

def sanitize_filename(title):
    clean_name = re.sub(r'[\\/*?:"<>|]', "", title)
    return clean_name[:60].strip()

def search_arxiv_by_title(title):
    try:
        query = f'ti:"{title}"'
        url = f'http://export.arxiv.org/api/query?search_query={urllib.parse.quote(query)}&start=0&max_results=1'
        data = urllib.request.urlopen(url)
        xml_data = data.read().decode('utf-8')
        root = ET.fromstring(xml_data)
        
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            paper_url = entry.find('{http://www.w3.org/2005/Atom}id').text
            if paper_url:
                return paper_url.replace('/abs/', '/pdf/') + ".pdf"
    except Exception:
        pass
    return None

def download_pdfs(papers_list, output_dir="articles"):
    os.makedirs(output_dir, exist_ok=True)
    
    downloaded_count = 0
    failed_papers = []
    
    for p in papers_list:
        original_pdf_url = p.get('pdf_url')
        pdf_url = original_pdf_url
        title = p.get('title', 'Unknown_Paper')
        filename = sanitize_filename(title) + ".pdf"
        filepath = os.path.join(output_dir, filename)
        
        if os.path.exists(filepath):
            logger.info(f"  [-] Already downloaded: {filename}")
            downloaded_count += 1
            continue
            
        fallback_used = False
        if not pdf_url:
            pdf_url = search_arxiv_by_title(title)
            if pdf_url:
                fallback_used = True
                logger.info(f"  [*] Found ArXiv preprint fallback for: '{title[:40]}...'")
                
        if not pdf_url:
            logger.warning(f"  [~] No accessible PDF or preprint found for: '{title[:40]}...'")
            failed_papers.append(title)
            continue
            
        source_label = "ArXiv Fallback" if fallback_used else "Direct Link"
        logger.info(f"  [v] Downloading PDF [{source_label}]: {filename}...")
        
        try:
            # Enhanced browser spoofing to bypass 403 Forbidden blocks from publishers/Cloudflare
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/pdf,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive'
            }
            response = requests.get(pdf_url, stream=True, headers=headers, timeout=20)
            
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                downloaded_count += 1
                time.sleep(2) # Increased delay to prevent ArXiv/Publishers from rate limiting us (403)
            else:
                logger.error(f"  [!] Failed to download (Status {response.status_code}) from {pdf_url.split('/')[2]}")
                failed_papers.append(title)
        except Exception as e:
            logger.error(f"  [!] Exception while downloading '{title[:40]}...': {e}")
            failed_papers.append(title)
            
    logger.info(f"\n[*] Successfully secured {downloaded_count} PDFs inside '{output_dir}/'.")
    if failed_papers:
        logger.info("\n[*] The following papers could not be downloaded automatically (requires manual proxy/check):")
        for fp in failed_papers:
            logger.info(f"    - {fp}")
            
    return downloaded_count
