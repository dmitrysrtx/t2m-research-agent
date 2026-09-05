import os
import re
import time
import requests
from src.utils.logger import logger
from src.auth.ezproxy_session import get_authenticated_session

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def sanitize_filename(title):
    clean_name = re.sub(r'[\\/*?:"<>|]', "", title)
    return clean_name[:60].strip()

def resolve_direct_pdf_url(url: str) -> str:
    """Normalizes candidate URLs (ArXiv, IEEE, OpenAccess) to direct binary PDF endpoints."""
    if not url:
        return url
    if "/stamp/stamp.jsp" in url:
        return url.replace("/stamp/stamp.jsp", "/stampPDF/getPDF.jsp")
    arxiv_m = re.search(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)', url)
    if arxiv_m:
        return f"https://arxiv.org/pdf/{arxiv_m.group(1)}.pdf"
    return url


def download_pdfs(papers_list, output_dir="articles", session=None, cookie_override: str = None):
    os.makedirs(output_dir, exist_ok=True)
    try:
        st = os.stat(PROJECT_ROOT)
        os.chown(output_dir, st.st_uid, st.st_gid)
        os.chmod(output_dir, 0o777)
    except Exception:
        pass

    if session is None:
        session = get_authenticated_session(cookie_override=cookie_override)

    downloaded_count = 0
    failed_papers = []

    for p in papers_list:
        pdf_url = p.get('pdf_url') or p.get('url')
        title = p.get('title', 'Unknown_Paper')
        filename = sanitize_filename(title) + ".pdf"
        filepath = os.path.join(output_dir, filename)

        if os.path.exists(filepath):
            logger.info(f"  [-] Already downloaded: {filename}")
            downloaded_count += 1
            continue

        success = False

        if pdf_url:
            download_target_url = resolve_direct_pdf_url(pdf_url)
            logger.info(f"  [v] Downloading PDF: {filename}...")
            try:
                # Use clean headers for non-IEEE targets to prevent header rejection
                is_ieee_host = "ieee.org" in download_target_url
                req_sess = session if is_ieee_host else requests
                headers = {}
                if is_ieee_host:
                    headers["Referer"] = "https://ieeexplore.ieee.org/"

                response = req_sess.get(download_target_url, stream=True, timeout=25, allow_redirects=True, headers=headers)
                content_type = response.headers.get('Content-Type', '').lower()
                peek = response.content[:128] if hasattr(response, 'content') else b''
                is_pdf_bytes = peek.startswith(b'%PDF')
                is_html = 'html' in content_type or b'<html' in peek.lower()

                # 1. Resolve ArXiv direct PDF from landing HTML
                if not is_pdf_bytes and (is_html or response.status_code == 200):
                    arxiv_match = re.search(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)', response.url + " " + response.text)
                    if arxiv_match:
                        arxiv_pdf = f"https://arxiv.org/pdf/{arxiv_match.group(1)}.pdf"
                        resp_arxiv = requests.get(arxiv_pdf, stream=True, timeout=25, allow_redirects=True)
                        if resp_arxiv.status_code == 200 and resp_arxiv.content[:128].startswith(b'%PDF'):
                            response = resp_arxiv
                            is_pdf_bytes = True
                            is_html = False

                # 2. Resolve IEEE arnumber from landing HTML
                if not is_pdf_bytes and (is_html or response.status_code == 200):
                    arnumber_match = (
                        re.search(r'/document/(\d+)', response.url) or
                        re.search(r'arnumber=(\d+)', response.url) or
                        re.search(r'"articleNumber":"(\d+)"', response.text) or
                        re.search(r'arnumber=(\d+)', response.text)
                    )
                    if arnumber_match:
                        arnum = arnumber_match.group(1)
                        stamp_url = f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={arnum}"
                        resp_ieee = session.get(stamp_url, stream=True, timeout=25, allow_redirects=True, headers={"Referer": f"https://ieeexplore.ieee.org/document/{arnum}"})
                        if resp_ieee.status_code == 200:
                            peek_ieee = resp_ieee.content[:128] if hasattr(resp_ieee, 'content') else b''
                            content_type2 = resp_ieee.headers.get('Content-Type', '').lower()
                            is_html2 = 'html' in content_type2 or b'<html' in peek_ieee.lower()
                            if peek_ieee.startswith(b'%PDF') or ('pdf' in content_type2 and not is_html2):
                                response = resp_ieee
                                is_pdf_bytes = True
                                is_html = False

                if response.status_code == 200 and is_pdf_bytes:
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    try:
                        st = os.stat(PROJECT_ROOT)
                        os.chown(filepath, st.st_uid, st.st_gid)
                        os.chmod(filepath, 0o666)
                    except Exception:
                        pass
                    downloaded_count += 1
                    success = True
                    logger.info(f"  [+] Saved PDF ({len(response.content)} bytes) -> {filename}")
                    time.sleep(0.5)
                else:
                    if is_html or response.status_code in [401, 403]:
                        logger.warning(f"  [!] Received HTML login page / Auth wall (Status: {response.status_code}, Content-Type: {content_type}).")
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
        logger.warning(
            "\n⚠️ ZERO PDFs DOWNLOADED\n"
            "Full-text PDFs could not be downloaded automatically.\n"
            "If IEEE publications are required, verify institutional access or provide active cookies in EZPROXY_COOKIE.\n"
        )

    return downloaded_count


if __name__ == "__main__":
    print("==================================================")
    print("📄 PDF Downloader Standalone Diagnostic")
    print("==================================================")
    test_papers = [
        {
            "title": "Test_ArXiv_Resolution_PhysDiff",
            "url": "https://arxiv.org/abs/2212.02500",
            "pdf_url": "https://arxiv.org/abs/2212.02500"
        }
    ]
    count = download_pdfs(test_papers, output_dir="/tmp/test_articles")
    print(f"[*] Standalone test completed. Downloaded: {count}")
    print("==================================================")

