import os
import re
import time
import requests
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
        
        if pdf_url:
            # Transform IEEE iframe URL to direct PDF binary endpoint
            download_target_url = pdf_url
            if "/stamp/stamp.jsp" in download_target_url:
                download_target_url = download_target_url.replace("/stamp/stamp.jsp", "/stampPDF/getPDF.jsp")
                
            logger.info(f"  [v] Downloading PDF [EZproxy / Direct]: {filename}...")
            try:
                response = session.get(download_target_url, stream=True, timeout=25, allow_redirects=True)
                
                content_type = response.headers.get('Content-Type', '').lower()
                
                # Check first 4 bytes of stream for %PDF magic header
                peek = response.content[:4] if hasattr(response, 'content') else b''
                is_pdf_bytes = peek.startswith(b'%PDF')
                
                if response.status_code == 200 and ('pdf' in content_type or is_pdf_bytes or download_target_url.endswith('.pdf')):
                    with open(filepath, 'wb') as f:
                        if hasattr(response, 'content'):
                            f.write(response.content)
                        else:
                            for chunk in response.iter_content(1024 * 16):
                                f.write(chunk)
                    downloaded_count += 1
                    success = True
                    logger.info(f"  [+] Saved PDF ({len(response.content) if hasattr(response, 'content') else 'N/A'} bytes) -> {filename}")
                    time.sleep(1)
                else:
                    if 'html' in content_type or response.status_code in [401, 403]:
                        logger.warning(f"  [!] Received HTML login page / Auth wall (Status: {response.status_code}, Content-Type: {content_type}). Valid SSO session cookies required!")
                    else:
                        logger.warning(f"  [!] Link did not yield binary PDF (Content-Type: {content_type}, Status: {response.status_code}).")
            except Exception as e:
                logger.error(f"  [!] Exception fetching PDF for '{title[:30]}...': {e}")

        if not success:
            logger.warning(f"  [~] Could not download full PDF for: '{title[:40]}...'")
            failed_papers.append(title)
            
    logger.info(f"\n[*] Successfully secured {downloaded_count} PDFs inside '{output_dir}/'.")
    if failed_papers:
        logger.info("\n[*] The following papers could not be downloaded automatically:")
        for fp in failed_papers:
            logger.info(f"    - {fp}")
            
    if downloaded_count == 0 and failed_papers:
        logger.error(
            "\n⛔ ZERO PDFs DOWNLOADED! (AUTHENTICATION REQUIRED)\n"
            "--------------------------------------------------------------------------------\n"
            "All paper targets failed or returned login HTML pages because active session\n"
            "cookies were missing or expired.\n\n"
            "👉 HOW TO FIX THIS ON HEADLESS UBUNTU SERVER:\n"
            "   1. Run the pure-Python SSO authentication script:\n"
            "      python3 src/utils/sso_login.py\n"
            "   2. Approve the 2FA Push notification sent to your mobile phone.\n"
            "   3. Re-run your research query!\n"
            "--------------------------------------------------------------------------------\n"
        )
            
    return downloaded_count
