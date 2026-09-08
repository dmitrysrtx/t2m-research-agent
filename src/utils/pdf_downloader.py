import os
import re
import time
from typing import Optional, List, Dict, Any
import requests
from src.utils.logger import logger
from src.auth.ezproxy_session import get_authenticated_session

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def sanitize_filename(title: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", title)[:60].strip()


def resolve_direct_pdf_url(url: str) -> str:
    """Normalizes candidate URLs (ArXiv, IEEE, OpenAccess) to direct binary PDF endpoints."""
    if not url:
        return url
    if "/stamp/stamp.jsp" in url:
        return url.replace("/stamp/stamp.jsp", "/stampPDF/getPDF.jsp")
    arx = re.search(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)', url)
    return f"https://arxiv.org/pdf/{arx.group(1)}.pdf" if arx else url


def resolve_fulltext_pdf_url(paper: Dict[str, Any], session: Optional[requests.Session] = None) -> Optional[str]:
    """
    Cascading resolver for full-text academic PDFs:
    - Tier 1: Direct OpenAccess PDF (ends with .pdf)
    - Tier 2: IEEE EZProxy Stamp Resolver (High Priority for Afeka SSO)
    - Tier 3: Unpaywall API via DOI
    - Tier 4: ArXiv Fallback direct endpoint
    """
    req = session or requests

    # Tier 1: Direct OpenAccess PDF
    pdf_url = paper.get("pdf_url")
    if pdf_url and str(pdf_url).strip().endswith(".pdf"):
        return resolve_direct_pdf_url(str(pdf_url).strip())

    # Tier 2: IEEE EZProxy Stamp Resolver (High Priority for Afeka SSO)
    doi = paper.get("doi") or ""
    url = paper.get("url") or ""
    arnumber_match = re.search(r'document/(\d+)', url) or re.search(r'arnumber=(\d+)', url)
    if "10.1109" in doi or arnumber_match or "ieee.org" in url:
        arnum = arnumber_match.group(1) if arnumber_match else doi.split(".")[-1].split("/")[-1]
        if arnum.isdigit():
            return f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={arnum}"

    # Tier 3: Unpaywall API via DOI
    if doi:
        try:
            upw = req.get(f"https://api.unpaywall.org/v2/{doi}?email=academic_bot@afeka.ac.il", timeout=4)
            if upw.status_code == 200:
                oa_loc = upw.json().get("best_oa_location")
                if oa_loc and oa_loc.get("url_for_pdf"):
                    return oa_loc["url_for_pdf"]
        except Exception:
            pass

    # Tier 4: ArXiv Fallback
    arxiv_id = paper.get("arxiv_id")
    if arxiv_id:
        return f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    arx_m = re.search(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)', url)
    if arx_m:
        return f"https://arxiv.org/pdf/{arx_m.group(1)}.pdf"

    return resolve_direct_pdf_url(pdf_url or url) if (pdf_url or url) else None


def get_pdf_candidate_urls(paper: Dict[str, Any], session: Optional[requests.Session] = None) -> List[str]:
    """Generates ordered candidate endpoints according to the priority cascade."""
    candidates, seen = [], set()
    doi = paper.get("doi") or ""
    url = paper.get("url") or ""
    arnumber_match = re.search(r'document/(\d+)', url) or re.search(r'arnumber=(\d+)', url)
    ieee_stamp = None
    if "10.1109" in doi or arnumber_match or "ieee.org" in url:
        arnum = arnumber_match.group(1) if arnumber_match else doi.split(".")[-1].split("/")[-1]
        if arnum.isdigit():
            ieee_stamp = f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={arnum}"

    for u in [
        resolve_fulltext_pdf_url(paper, session=session),
        resolve_direct_pdf_url(paper.get("pdf_url", "")) if str(paper.get("pdf_url", "")).endswith(".pdf") else None,
        ieee_stamp,
        f"https://arxiv.org/pdf/{paper['arxiv_id']}.pdf" if paper.get("arxiv_id") else None,
        resolve_direct_pdf_url(paper.get("url", ""))
    ]:
        if u and u not in seen:
            seen.add(u)
            candidates.append(u)
    return candidates


def download_pdfs(papers_list: List[Dict[str, Any]], output_dir: str = "articles", session: Optional[requests.Session] = None, cookie_override: str = None) -> int:
    os.makedirs(output_dir, exist_ok=True)
    try:
        st = os.stat(PROJECT_ROOT)
        os.chown(output_dir, st.st_uid, st.st_gid)
        os.chmod(output_dir, 0o777)
    except Exception:
        pass

    session = session or get_authenticated_session(cookie_override=cookie_override)
    downloaded_count, failed_papers = 0, []

    for p in papers_list:
        title = p.get('title', 'Unknown_Paper')
        filename = sanitize_filename(title) + ".pdf"
        filepath = os.path.join(output_dir, filename)

        if os.path.exists(filepath):
            logger.info(f"  [-] Already downloaded: {filename}")
            p["fulltext_secured"] = True
            p["pdf_path"] = filepath
            downloaded_count += 1
            continue

        success = False
        for target_url in get_pdf_candidate_urls(p, session=session):
            try:
                is_ieee = ("ieee.org" in target_url) or ("doi.org" in target_url)
                req_sess = session if is_ieee else requests
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"}
                if "ieee.org" in target_url:
                    headers["Referer"] = "https://ieeexplore.ieee.org/"

                resp = req_sess.get(target_url, stream=True, timeout=15, allow_redirects=True, headers=headers)
                content_type = resp.headers.get('Content-Type', '').lower()
                peek = resp.content[:128] if hasattr(resp, 'content') else b''
                is_pdf_bytes, is_html = peek.startswith(b'%PDF'), 'html' in content_type or b'<html' in peek.lower()

                if is_html and (not p.get("github_url") or p.get("github_url") == "N/A"):
                    from src.fetchers.github_verifier import extract_github_candidates
                    ghs, _ = extract_github_candidates(resp.text)
                    if ghs:
                        p["github_url"] = ghs[0]
                        logger.info(f"  [github_finder] Found repo on page: {ghs[0]}")

                if not is_pdf_bytes and (is_html or resp.status_code == 200):
                    arx_m = re.search(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)', resp.url + " " + resp.text)
                    if arx_m:
                        resp_arx = requests.get(f"https://arxiv.org/pdf/{arx_m.group(1)}.pdf", stream=True, timeout=15, allow_redirects=True)
                        if resp_arx.status_code == 200 and resp_arx.content[:128].startswith(b'%PDF'):
                            resp, is_pdf_bytes = resp_arx, True

                if resp.status_code == 200 and is_pdf_bytes:
                    with open(filepath, 'wb') as f:
                        f.write(resp.content)
                    try:
                        st = os.stat(PROJECT_ROOT)
                        os.chown(filepath, st.st_uid, st.st_gid)
                        os.chmod(filepath, 0o666)
                    except Exception:
                        pass
                    p["fulltext_secured"] = True
                    p["pdf_path"] = filepath
                    downloaded_count += 1
                    success = True
                    logger.info(f"  [+] Saved PDF ({len(resp.content)} bytes) -> {filename}")
                    time.sleep(0.2)
                    break
            except Exception as e:
                logger.debug(f"  [!] Candidate failed for '{title[:30]}': {target_url} ({e})")

        if not success:
            p["fulltext_secured"] = False
            logger.warning(f"  [~] Could not download full PDF for: '{title[:40]}...'")
            failed_papers.append(title)

    logger.info(f"\n[*] Successfully secured {downloaded_count} PDFs inside '{output_dir}/'.")
    return downloaded_count


if __name__ == "__main__":
    print("==================================================")
    print("📄 Cascading PDF Downloader Priority Diagnostic")
    print("==================================================")
    p_oa = {"title": "Direct OA Paper", "pdf_url": "https://example.org/paper.pdf"}
    assert resolve_fulltext_pdf_url(p_oa) == "https://example.org/paper.pdf"
    print("[*] Tier 1 (Direct OA) Priority: PASSED")

    p_ieee = {"title": "IEEE Paper", "doi": "10.1109/CVPR.2023.98765", "arxiv_id": "2304.01116"}
    u_ieee = resolve_fulltext_pdf_url(p_ieee)
    assert u_ieee == "https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=98765"
    print(f"[*] Tier 2 (IEEE Stamp Precedence over ArXiv): {u_ieee} -> PASSED")

    p_arxiv = {"title": "PhysDiff", "arxiv_id": "2212.02500"}
    u_arxiv = resolve_fulltext_pdf_url(p_arxiv)
    assert u_arxiv == "https://arxiv.org/pdf/2212.02500.pdf"
    print(f"[*] Tier 4 (ArXiv Fallback) Resolution: {u_arxiv} -> PASSED")
    print("==================================================")
