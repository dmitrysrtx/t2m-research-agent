import os
import sys
import re
import time
from typing import Optional, List, Dict, Any
import requests

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.logger import logger
from src.auth.ezproxy_session import get_authenticated_session


def sanitize_filename(title: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", title)[:60].strip()


def resolve_direct_pdf_url(url: str) -> str:
    """Normalizes candidate URLs (ArXiv, IEEE, OpenAccess, OpenReview) to direct binary PDF endpoints."""
    if not url:
        return url
    url_str = str(url).strip()
    if "/stamp/stamp.jsp" in url_str:
        return url_str.replace("/stamp/stamp.jsp", "/stampPDF/getPDF.jsp")
    # ArXiv normalization
    arx = re.search(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)', url_str)
    if arx:
        return f"https://export.arxiv.org/pdf/{arx.group(1)}.pdf"
    # OpenReview normalization
    if "openreview.net/forum?id=" in url_str:
        return url_str.replace("/forum?id=", "/pdf?id=")
    return url_str


def resolve_fulltext_pdf_url(paper: Dict[str, Any], session: Optional[requests.Session] = None) -> Optional[str]:
    """
    Cascading resolver for full-text academic PDFs:
    - Tier 1: Direct OpenAccess PDF (ends with .pdf)
    - Tier 1.5: ArXiv DOI pattern (10.48550/arXiv.XXXX.XXXXX)
    - Tier 2: IEEE EZProxy Stamp Resolver (High Priority for Afeka SSO)
    - Tier 3: OpenReview endpoints
    - Tier 4: Unpaywall API via DOI
    - Tier 5: ArXiv Fallback direct endpoint
    """
    req = session or requests

    # Tier 1: Direct OpenAccess PDF
    pdf_url = paper.get("pdf_url")
    if pdf_url and str(pdf_url).strip().lower().endswith(".pdf"):
        return resolve_direct_pdf_url(str(pdf_url).strip())

    doi = str(paper.get("doi") or "")
    url = str(paper.get("url") or "")

    # Tier 1.5: ArXiv DOI pattern (e.g. 10.48550/arXiv.2307.14535)
    if "10.48550" in doi or "arxiv" in doi.lower():
        arx_doi_m = re.search(r'arxiv\.(\d{4}\.\d{4,5}(?:v\d+)?)', doi, re.IGNORECASE)
        if arx_doi_m:
            return f"https://export.arxiv.org/pdf/{arx_doi_m.group(1)}.pdf"

    # Tier 2: IEEE EZProxy Stamp Resolver (High Priority for Afeka SSO)
    arnumber_match = re.search(r'document/(\d+)', url) or re.search(r'arnumber=(\d+)', url)
    if "10.1109" in doi or arnumber_match or "ieee.org" in url:
        arnum = arnumber_match.group(1) if arnumber_match else doi.split(".")[-1].split("/")[-1]
        if arnum.isdigit():
            return f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={arnum}"

    # Tier 3: OpenReview
    if "openreview.net" in url:
        return resolve_direct_pdf_url(url)

    # Tier 4: Unpaywall API via DOI
    if doi and "10.48550" not in doi:
        try:
            upw = req.get(f"https://api.unpaywall.org/v2/{doi}?email=academic_bot@afeka.ac.il", timeout=4)
            if upw.status_code == 200:
                oa_loc = upw.json().get("best_oa_location")
                if oa_loc and oa_loc.get("url_for_pdf"):
                    return oa_loc["url_for_pdf"]
        except Exception:
            pass

    # Tier 5: ArXiv Fallback
    arxiv_id = paper.get("arxiv_id")
    if arxiv_id:
        return f"https://export.arxiv.org/pdf/{arxiv_id}.pdf"
    arx_m = re.search(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)', url)
    if arx_m:
        return f"https://export.arxiv.org/pdf/{arx_m.group(1)}.pdf"

    return resolve_direct_pdf_url(pdf_url or url) if (pdf_url or url) else None


def get_pdf_candidate_urls(paper: Dict[str, Any], session: Optional[requests.Session] = None) -> List[str]:
    """Generates ordered candidate endpoints according to the priority cascade."""
    candidates = []
    seen = set()

    doi = str(paper.get("doi") or "")
    url = str(paper.get("url") or "")
    pdf_url = str(paper.get("pdf_url") or "")

    # 1. Direct OpenAccess PDF
    if pdf_url and pdf_url.strip().lower().endswith(".pdf"):
        candidates.append(resolve_direct_pdf_url(pdf_url.strip()))

    # 2. ArXiv IDs from explicit field, DOI, or URLs
    arxiv_id = paper.get("arxiv_id")
    if not arxiv_id and doi:
        arx_doi_m = re.search(r'arxiv\.(\d{4}\.\d{4,5}(?:v\d+)?)', doi, re.IGNORECASE)
        if arx_doi_m:
            arxiv_id = arx_doi_m.group(1)
    if not arxiv_id and url:
        arx_url_m = re.search(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)', url)
        if arx_url_m:
            arxiv_id = arx_url_m.group(1)

    if arxiv_id:
        candidates.append(f"https://export.arxiv.org/pdf/{arxiv_id}.pdf")
        candidates.append(f"https://arxiv.org/pdf/{arxiv_id}.pdf")

    # 3. IEEE EZProxy Stamp
    arnumber_match = re.search(r'document/(\d+)', url) or re.search(r'arnumber=(\d+)', url)
    if "10.1109" in doi or arnumber_match or "ieee.org" in url:
        arnum = arnumber_match.group(1) if arnumber_match else doi.split(".")[-1].split("/")[-1]
        if arnum.isdigit():
            candidates.append(f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={arnum}")

    # 4. OpenReview
    if "openreview.net" in url:
        candidates.append(resolve_direct_pdf_url(url))

    # 5. Unpaywall via DOI
    if doi and "10.48550" not in doi:
        try:
            req = session or requests
            upw = req.get(f"https://api.unpaywall.org/v2/{doi}?email=academic_bot@afeka.ac.il", timeout=4)
            if upw.status_code == 200:
                oa_loc = upw.json().get("best_oa_location")
                if oa_loc and oa_loc.get("url_for_pdf"):
                    candidates.append(oa_loc["url_for_pdf"])
        except Exception:
            pass

    # 6. Fallback raw URLs
    if pdf_url:
        candidates.append(resolve_direct_pdf_url(pdf_url))
    if url:
        candidates.append(resolve_direct_pdf_url(url))

    # Deduplicate preserving order
    clean_candidates = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            clean_candidates.append(c)
    return clean_candidates


def _extract_pdf_links_from_html(html_text: str, base_url: str = "") -> List[str]:
    """Scrapes potential PDF endpoints and citation meta tags from academic HTML pages."""
    discovered = []

    # 1. Academic Meta tags: citation_pdf_url
    meta_matches = re.findall(r'<meta[^>]+(?:name|property)=["\']citation_pdf_url["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    for m in meta_matches:
        if m.startswith("http"):
            discovered.append(m)

    # 2. ArXiv IDs embedded in HTML
    arx_matches = re.findall(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)', html_text, re.I)
    for arx_id in arx_matches:
        discovered.append(f"https://export.arxiv.org/pdf/{arx_id}.pdf")
        discovered.append(f"https://arxiv.org/pdf/{arx_id}.pdf")

    # 3. Direct href links ending in .pdf
    href_matches = re.findall(r'href=["\'](https?://[^"\'\s]+\.pdf(?:\?[^"\'\s]*)?)["\']', html_text, re.I)
    for h in href_matches:
        discovered.append(h)

    # 4. OpenReview PDF links
    or_matches = re.findall(r'href=["\'](/pdf\?id=[^"\'\s]+)["\']', html_text, re.I)
    for or_m in or_matches:
        discovered.append(f"https://openreview.net{or_m}")

    return list(dict.fromkeys(discovered))


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
        candidate_urls = get_pdf_candidate_urls(p, session=session)

        for target_url in candidate_urls:
            try:
                is_ieee = ("ieee.org" in target_url) or ("doi.org" in target_url)
                req_sess = session if is_ieee else requests
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    "Accept": "application/pdf,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                }
                if "ieee.org" in target_url:
                    headers["Referer"] = "https://ieeexplore.ieee.org/"

                resp = req_sess.get(target_url, stream=True, timeout=15, allow_redirects=True, headers=headers)
                content_type = resp.headers.get('Content-Type', '').lower()
                peek = resp.content[:128] if hasattr(resp, 'content') else b''
                is_pdf_bytes = peek.startswith(b'%PDF')
                is_html = 'html' in content_type or b'<html' in peek.lower()

                # If HTML returned, extract GitHub links if missing
                if is_html and (not p.get("github_url") or p.get("github_url") == "N/A"):
                    from src.fetchers.github_verifier import extract_github_candidates
                    ghs, _ = extract_github_candidates(resp.text)
                    if ghs:
                        p["github_url"] = ghs[0]
                        logger.info(f"  [github_finder] Found repo on page: {ghs[0]}")

                # If page was HTML, inspect for embedded PDF endpoints
                if not is_pdf_bytes and is_html and resp.status_code == 200:
                    html_pdf_links = _extract_pdf_links_from_html(resp.text, base_url=resp.url)
                    for sub_url in html_pdf_links:
                        try:
                            sub_resp = requests.get(sub_url, stream=True, timeout=12, allow_redirects=True, headers=headers)
                            sub_peek = sub_resp.content[:128] if hasattr(sub_resp, 'content') else b''
                            if sub_resp.status_code == 200 and sub_peek.startswith(b'%PDF'):
                                resp = sub_resp
                                is_pdf_bytes = True
                                logger.info(f"  [+] Discovered direct PDF in HTML metadata -> {sub_url}")
                                break
                        except Exception:
                            continue

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
    assert u_arxiv == "https://export.arxiv.org/pdf/2212.02500.pdf"
    print(f"[*] Tier 5 (ArXiv Fallback) Resolution: {u_arxiv} -> PASSED")
    print("==================================================")
