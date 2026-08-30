import os
import re
import time
from src.utils.logger import logger
from src.utils.ezproxy_auth import get_authenticated_session

def sanitize_filename(title):
    clean_name = re.sub(r'[\\/*?:"<>|]', "", title)
    return clean_name[:60].strip()

def download_pdfs(papers_list, output_dir="articles"):
    os.makedirs(output_dir, exist_ok=True)
    session = get_authenticated_session()
    
    downloaded_count = 0
    failed_papers = []
    
    for p in papers_list:
        pdf_url = p.get('pdf_url')
        title = p.get('title', 'Unknown_Paper')
        filename = sanitize_filename(title) + ".pdf"
        filepath = os.path.join(output_dir, filename)
        
        if os.path.exists(filepath):
            logger.info(f"  [-] Already downloaded: {filename}")
            downloaded_count += 1
            continue
            
        success = False
        
        # Try downloading primary IEEE URL (with EZproxy session)
        if pdf_url:
            logger.info(f"  [v] Downloading IEEE PDF [EZproxy / Direct]: {filename}...")
            try:
                response = session.get(pdf_url, stream=True, timeout=25, allow_redirects=True)
                
                # Verify that response is actually a PDF (and not HTML login/error page)
                content_type = response.headers.get('Content-Type', '').lower()
                if response.status_code == 200 and ('pdf' in content_type or pdf_url.endswith('.pdf')):
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(1024 * 16):
                            f.write(chunk)
                    downloaded_count += 1
                    success = True
                    time.sleep(2)
                else:
                    logger.warning(f"  [!] Direct link did not yield PDF (Content-Type: {content_type}, Status: {response.status_code}). Auth/cookies required.")
            except Exception as e:
                logger.error(f"  [!] Exception fetching IEEE PDF for '{title[:30]}...': {e}")

        if not success:
            logger.warning(f"  [~] Could not download IEEE PDF for: '{title[:40]}...'. (Requires valid EZproxy session)")
            failed_papers.append(title)
            
    logger.info(f"\n[*] Successfully secured {downloaded_count} IEEE PDFs inside '{output_dir}/'.")
    if failed_papers:
        logger.info("\n[*] The following IEEE papers could not be downloaded automatically (Login required):")
        for fp in failed_papers:
            logger.info(f"    - {fp}")
            
    return downloaded_count
            
    return downloaded_count
