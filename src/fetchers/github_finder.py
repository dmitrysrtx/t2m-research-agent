import os
import re
import urllib.parse
from typing import Optional, List, Dict, Any
import requests
from src.utils.logger import logger

GITHUB_RE = re.compile(
    r'(?:https?://(?:www\.)?github\.com/|github\.com/)([a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-\.]+)',
    re.IGNORECASE
)
GITHUB_IO_RE = re.compile(
    r'https?://([a-zA-Z0-9_\-]+)\.github\.io/([a-zA-Z0-9_\-]+)',
    re.IGNORECASE
)
BLACKLIST_NAMES = {
    "topics", "features", "pricing", "about", "explore", "trending",
    "collections", "site", "search", "login", "signup", "settings",
    "marketplace", "pulls", "issues", "security", "organizations"
}
SKIP_SCRAPE_DOMAINS = {
    "ieeexplore.ieee.org", "sciencedirect.com", "springer.com",
    "wiley.com", "nature.com", "tandfonline.com", "acm.org"
}


def clean_github_url(raw_url: str) -> Optional[str]:
    """Cleans, normalizes, and filters candidate GitHub repository URLs."""
    if not raw_url:
        return None
    cleaned = raw_url.strip().rstrip(".,;:)'\"]>}")

    io_match = GITHUB_IO_RE.search(cleaned)
    if io_match:
        owner, repo = io_match.group(1), io_match.group(2)
        if owner.lower() not in BLACKLIST_NAMES and repo.lower() not in BLACKLIST_NAMES:
            return f"https://github.com/{owner}/{repo}"

    m = GITHUB_RE.search(cleaned)
    if not m:
        return None
    repo_path = m.group(1).rstrip("/").rstrip(".,;:)'\"]>}")
    parts = repo_path.split("/")
    if len(parts) < 2:
        return None
    owner, repo = parts[0], parts[1]
    repo = re.sub(r'\.git$', '', repo)
    if owner.lower() in BLACKLIST_NAMES or repo.lower() in BLACKLIST_NAMES:
        return None
    return f"https://github.com/{owner}/{repo}"


def is_github_repo_live(gh_url: str) -> bool:
    """Verifies that the candidate repository exists, is public, and not 404/deleted."""
    if not gh_url or not gh_url.startswith("https://github.com/"):
        return False
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AcademicResearchAgent/2.0"}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"
        r = requests.head(gh_url, headers=headers, timeout=2.5, allow_redirects=True)
        return r.status_code == 200
    except Exception:
        return False


def extract_github_url(text: str) -> Optional[str]:
    """Extracts the first valid GitHub repository URL from arbitrary text or HTML."""
    if not text:
        return None
    for match in GITHUB_RE.finditer(text):
        candidate = clean_github_url(f"https://github.com/{match.group(1)}")
        if candidate:
            return candidate

    for match in GITHUB_IO_RE.finditer(text):
        candidate = clean_github_url(f"https://github.com/{match.group(1)}/{match.group(2)}")
        if candidate:
            return candidate
    return None


def find_github_on_page(url: str, session: Optional[requests.Session] = None) -> Optional[str]:
    """Fetches candidate landing page HTML and scans for GitHub links."""
    if not url or not url.startswith("http"):
        return None
    if any(d in url.lower() for d in SKIP_SCRAPE_DOMAINS) and session is None:
        return None
    try:
        req_sess = session or requests
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AcademicAgent/2.0"}
        resp = req_sess.get(url, headers=headers, timeout=3, allow_redirects=True)
        if resp.status_code == 200 and "html" in resp.headers.get("Content-Type", "").lower():
            return extract_github_url(resp.text)
    except Exception as e:
        logger.debug(f"[github_finder] Page check error for {url}: {e}")
    return None


def resolve_paper_github(paper: Dict[str, Any], session: Optional[requests.Session] = None) -> Optional[str]:
    """Multi-tiered resolution: Abstract -> Comment -> Landing Page with HTTP liveness check."""
    existing = paper.get("github_url")
    if existing and existing != "N/A":
        cleaned = clean_github_url(existing)
        if cleaned and is_github_repo_live(cleaned):
            return cleaned

    # Tier 1: Abstract and comment text
    abstract = paper.get("abstract", "")
    comment = paper.get("comment", "")
    url_from_text = extract_github_url(f"{comment} {abstract}")
    if url_from_text and is_github_repo_live(url_from_text):
        return url_from_text

    # Tier 2: Landing page / ArXiv abs page
    landing_url = paper.get("url") or ""
    if "arxiv.org" in landing_url:
        arxiv_abs = landing_url.replace("/pdf/", "/abs/").replace(".pdf", "")
        page_gh = find_github_on_page(arxiv_abs, session=session)
        if page_gh and is_github_repo_live(page_gh):
            return page_gh
    elif landing_url:
        page_gh = find_github_on_page(landing_url, session=session)
        if page_gh and is_github_repo_live(page_gh):
            return page_gh

    return None


def enrich_papers_with_github(
    papers: List[Dict[str, Any]],
    session: Optional[requests.Session] = None,
    telemetry: Optional[Any] = None,
    status_callback: Optional[Any] = None
) -> int:
    """Batch-enriches papers in-place with verified 'github_url' and returns count of discovered repos."""
    found_count = 0
    total = len(papers)
    for i, paper in enumerate(papers):
        title = paper.get("title", "Unknown")[:40]
        if status_callback and (i % 5 == 0 or i == total - 1):
            status_callback(f"🔎 Scanning GitHub repos: [{i+1}/{total}] {title}...")
        gh_url = resolve_paper_github(paper, session=session)
        if gh_url:
            paper["github_url"] = gh_url
            found_count += 1
        else:
            paper["github_url"] = "N/A"

    logger.info(f"[*] Discovered {found_count}/{total} verified GitHub code repositories.")
    return found_count


if __name__ == "__main__":
    print("==================================================", flush=True)
    print("🔬 GitHub Finder Standalone Diagnostic Test", flush=True)
    print("==================================================", flush=True)
    test_sample = [
        {
            "title": "Human Motion Diffusion Model",
            "abstract": "We introduce MDM. Code: https://github.com/GuyTevet/motion-diffusion-model.",
            "url": "https://arxiv.org/abs/2209.14916"
        },
        {
            "title": "PhysDiff: Physics-Guided Human Motion Diffusion Model",
            "comment": "ICCV 2023 (Oral). Project: https://nvlabs.github.io/PhysDiff",
            "abstract": "Denoising diffusion models hold great promise.",
            "url": "https://arxiv.org/abs/2212.02500"
        },
        {
            "title": "Non-existent repo test",
            "abstract": "Check code at https://github.com/fakeuser123891048123/nonexistent-repo-test-xyz.",
            "url": "https://arxiv.org/abs/2001.00000"
        }
    ]
    count = enrich_papers_with_github(test_sample)
    for p in test_sample:
        print(f"[*] Paper: {p['title']}", flush=True)
        print(f"    GitHub: {p['github_url']}", flush=True)
    print(f"[*] Total Discovered: {count}/{len(test_sample)}", flush=True)
    print("==================================================", flush=True)
    assert test_sample[0]["github_url"] == "https://github.com/GuyTevet/motion-diffusion-model"
    assert test_sample[2]["github_url"] == "N/A", "Non-existent repo should be N/A!"
    print("✅ All GitHub Finder assertions passed!", flush=True)
