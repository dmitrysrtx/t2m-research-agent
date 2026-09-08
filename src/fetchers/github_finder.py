import os
import re
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Any
import requests
from src.utils.logger import logger
from src.fetchers.github_verifier import (
    clean_github_url,
    is_github_repo_live,
    extract_github_candidates,
    extract_github_url,
    BROWSER_UA
)

SKIP_DOMAINS = {"sciencedirect.com", "springer.com", "wiley.com", "nature.com"}
STOPWORDS = {"using", "with", "from", "into", "novel", "towards", "based", "through", "approach"}


def find_github_on_page(url: str, session: Optional[requests.Session] = None) -> Optional[str]:
    """Scans landing HTML or project page for valid GitHub repository links."""
    if not url or not url.startswith("http") or any(d in url.lower() for d in SKIP_DOMAINS):
        return None
    try:
        req = session or requests
        headers = {"User-Agent": BROWSER_UA, "Accept": "text/html,application/xhtml+xml"}
        resp = req.get(url, headers=headers, timeout=(3.0, 4.0), allow_redirects=True)
        if resp.status_code == 200:
            ghs, project_urls = extract_github_candidates(resp.text)
            for gh in ghs:
                if is_github_repo_live(gh):
                    return gh
            for prj in project_urls:
                if prj != url:
                    sub = find_github_on_page(prj, session=session)
                    if sub:
                        return sub
    except Exception as e:
        logger.debug(f"[github_finder] Page scrape error for {url}: {e}")
    return None


def find_arxiv_by_title(title: str) -> Optional[Dict[str, str]]:
    """Resolves paper entry, comment, and project link from ArXiv API by title."""
    clean_words = [w for w in re.findall(r'[a-zA-Z0-9]+', title) if len(w) > 2]
    if len(clean_words) < 3:
        return None
    q = "ti:\"" + " ".join(clean_words[:6]) + "\""
    url = f"https://export.arxiv.org/api/query?search_query={urllib.parse.quote(q)}&max_results=1"
    try:
        resp = requests.get(url, headers={"User-Agent": BROWSER_UA}, timeout=(3.0, 4.0))
        if resp.status_code != 200:
            return None
        root = ET.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        entry = root.find("atom:entry", ns)
        if entry is None:
            return None
        t_elem = entry.find("atom:title", ns)
        ret_title = t_elem.text.strip().replace("\n", " ") if t_elem is not None else ""
        # Validate title similarity
        q_set = set(w.lower() for w in clean_words[:6])
        ret_set = set(re.findall(r'[a-zA-Z0-9]+', ret_title.lower()))
        if len(q_set.intersection(ret_set)) < min(3, len(q_set)):
            return None
        id_elem = entry.find("atom:id", ns)
        comm_elem = entry.find("arxiv:comment", ns)
        summ_elem = entry.find("atom:summary", ns)
        return {
            "url": id_elem.text.strip() if id_elem is not None else "",
            "comment": comm_elem.text.strip() if comm_elem is not None else "",
            "summary": summ_elem.text.strip().replace("\n", " ") if summ_elem is not None else ""
        }
    except Exception as e:
        logger.debug(f"[github_finder] ArXiv title lookup failed for '{title[:30]}': {e}")
        return None


def search_github_api_by_title(title: str) -> Optional[str]:
    """Targeted GitHub search fallback matching paper keywords against repo metadata."""
    words = [w for w in re.findall(r'[a-zA-Z0-9]+', title) if len(w) > 3 and w.lower() not in STOPWORDS]
    if len(words) < 2:
        return None
    query = "+".join(words[:5])
    url = f"https://api.github.com/search/repositories?q={query}+in:name,description&per_page=5"
    headers = {"User-Agent": BROWSER_UA, "Accept": "application/vnd.github.v3+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    try:
        resp = requests.get(url, headers=headers, timeout=(3.0, 4.0))
        if resp.status_code != 200:
            return None
        items = resp.json().get("items", [])
        title_set = set(w.lower() for w in words)
        for it in items:
            repo_text = f"{it.get('name', '')} {it.get('description', '')}".lower()
            overlap = sum(1 for w in title_set if w in repo_text)
            if overlap >= min(3, len(title_set)):
                candidate = clean_github_url(it.get("html_url", ""))
                if candidate and is_github_repo_live(candidate):
                    return candidate
    except Exception as e:
        logger.debug(f"[github_finder] GitHub Search API failed for '{title[:30]}': {e}")
    return None


def resolve_paper_github(paper: Dict[str, Any], session: Optional[requests.Session] = None) -> Optional[str]:
    """Resolves paper repository: Direct Text -> Project Pages -> ArXiv Landing -> GitHub Search."""
    existing = paper.get("github_url")
    if existing and existing != "N/A":
        cleaned = clean_github_url(existing)
        if cleaned and is_github_repo_live(cleaned):
            return cleaned

    # Tier 1: Direct Text (abstract & comment)
    text = f"{paper.get('comment', '')} {paper.get('abstract', '')}"
    direct_ghs, project_urls = extract_github_candidates(text)
    for gh in direct_ghs:
        if is_github_repo_live(gh):
            return gh

    # Tier 2: Project pages in comment/abstract
    for prj in project_urls:
        repo = find_github_on_page(prj, session=session)
        if repo:
            return repo

    # Tier 3: ArXiv Page Resolution (direct or title lookup)
    arxiv_url = paper.get("arxiv_url") or (paper.get("url") if "arxiv.org" in (paper.get("url") or "") else None)
    if not arxiv_url and paper.get("title"):
        arx = find_arxiv_by_title(paper["title"])
        if arx:
            arxiv_url = arx["url"]
            text_arx = f"{arx['comment']} {arx['summary']}"
            g_list, p_list = extract_github_candidates(text_arx)
            for g in g_list:
                if is_github_repo_live(g):
                    return g
            for p in p_list:
                repo = find_github_on_page(p, session=session)
                if repo:
                    return repo
    if arxiv_url:
        abs_url = re.sub(r'/pdf/(.*?)(?:\.pdf)?$', r'/abs/\1', arxiv_url)
        repo = find_github_on_page(abs_url, session=session)
        if repo:
            return repo

    # Tier 4: High-Precision GitHub Search Fallback
    if paper.get("title"):
        repo = search_github_api_by_title(paper["title"])
        if repo:
            return repo
    return None


def enrich_papers_with_github(
    papers: List[Dict[str, Any]],
    session: Optional[requests.Session] = None,
    telemetry: Optional[Any] = None,
    status_callback: Optional[Any] = None
) -> int:
    """Batch-enriches papers in-place with verified 'github_url'."""
    found_count, total = 0, len(papers)
    for i, paper in enumerate(papers):
        title = paper.get("title", "Unknown")[:40]
        if status_callback and (i % 5 == 0 or i == total - 1):
            status_callback(f"🔎 Scanning GitHub repos: [{i+1}/{total}] {title}...")
        gh_url = resolve_paper_github(paper, session=session)
        paper["github_url"] = gh_url if gh_url else "N/A"
        if gh_url:
            found_count += 1
    logger.info(f"[*] Discovered {found_count}/{total} verified GitHub code repositories.")
    return found_count


if __name__ == "__main__":
    print("🔬 Multi-Tier GitHub Finder Diagnostic Test")
    dataset = [
        {"title": "Human Motion Diffusion Model (MDM)", "abstract": "Code: https://github.com/GuyTevet/motion-diffusion-model.", "url": "https://arxiv.org/abs/2209.14916"},
        {"title": "MotionDiffuse", "abstract": "Homepage: https://mingyuan-zhang.github.io/projects/MotionDiffuse.html", "url": "https://arxiv.org/abs/2208.15001"},
        {"title": "UniPhys: Unified Planner and Controller with Diffusion for Flexible Physics-Based Character Control", "abstract": "We introduce UniPhys..."},
        {"title": "Synthetic Training for Accurate 3D Human Pose and Shape Estimation in the Wild", "abstract": "We present a synthetic training method..."},
        {"title": "Physics-Informed Conditional Diffusion for Motion-Robust Retinal Temporal Laser Speckle Contrast Imaging", "abstract": "Code is at https://github.com/QianChen113/RetinaDiff"}
    ]
    found = enrich_papers_with_github(dataset)
    for p in dataset:
        print(f"[*] {p['title'][:38]:38} -> {p['github_url']}")
    assert dataset[0]["github_url"] == "https://github.com/GuyTevet/motion-diffusion-model"
    assert dataset[1]["github_url"] == "https://github.com/mingyuan-zhang/MotionDiffuse"
    assert dataset[2]["github_url"] == "https://github.com/wuyan01/UniPhys"
    assert dataset[3]["github_url"] == "https://github.com/akashsengupta1997/STRAPS-3DHumanShapePose"
    assert dataset[4]["github_url"] == "N/A", "RetinaDiff is 404 and must be N/A!"
    print(f"✅ Discovered {found}/{len(dataset)} repos. All diagnostic assertions passed!")
