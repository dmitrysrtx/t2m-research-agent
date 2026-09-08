import os
import re
from typing import Optional, List, Tuple
import requests
from src.utils.logger import logger

BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
BLACKLIST_NAMES = {
    "topics", "features", "pricing", "about", "explore", "trending",
    "collections", "site", "search", "login", "signup", "settings",
    "marketplace", "pulls", "issues", "security", "organizations"
}


def clean_github_url(raw_url: str) -> Optional[str]:
    """Normalizes and canonicalizes GitHub URLs into https://github.com/{owner}/{repo}."""
    if not raw_url:
        return None
    cleaned = raw_url.strip().lstrip("<([{\"'`").rstrip(">)]}\"'`.,;:?!")
    cleaned_no_query = cleaned.split("?")[0].split("#")[0]

    # Handle direct github.io project pages
    io_m = re.search(r'https?://([a-zA-Z0-9_\-]+)\.github\.io/([a-zA-Z0-9_\-]+)', cleaned_no_query, re.IGNORECASE)
    if io_m:
        owner, repo = io_m.group(1), io_m.group(2)
        if owner.lower() not in BLACKLIST_NAMES and repo.lower() not in BLACKLIST_NAMES:
            return f"https://github.com/{owner}/{repo}"

    # Handle standard github.com URLs
    m = re.search(r'(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_\-]+)/([a-zA-Z0-9_\-\.]+)', cleaned_no_query, re.IGNORECASE)
    if not m:
        return None
    owner, repo = m.group(1), m.group(2).rstrip("/.,;:)'\"]>}").removesuffix(".git")
    if not owner or not repo or owner.lower() in BLACKLIST_NAMES or repo.lower() in BLACKLIST_NAMES:
        return None
    return f"https://github.com/{owner}/{repo}"


def is_github_repo_live(gh_url: str) -> bool:
    """Verifies repository liveness via streaming GET, distinguishing 200 vs 404 vs 403/429."""
    if not gh_url or not gh_url.startswith("https://github.com/"):
        return False
    headers = {"User-Agent": BROWSER_UA, "Accept": "text/html,application/xhtml+xml"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    try:
        resp = requests.get(gh_url, headers=headers, stream=True, timeout=(2.0, 3.0), allow_redirects=True)
        status = resp.status_code
        resp.close()
        if status == 200:
            logger.info(f"[github_finder] [VERIFIED] (HTTP 200): {gh_url}")
            return True
        elif status in (403, 429):
            logger.warning(f"[github_finder] [RATE_LIMITED] (HTTP {status}) for {gh_url} - keeping candidate")
            return True
        elif status == 404:
            logger.info(f"[github_finder] [NOT_FOUND] (HTTP 404): {gh_url}")
            return False
        else:
            logger.warning(f"[github_finder] [UNEXPECTED_STATUS] (HTTP {status}): {gh_url}")
            return False
    except Exception as e:
        logger.warning(f"[github_finder] [ERROR] Network check failed for {gh_url}: {e}")
        return False


def extract_github_candidates(text: str) -> Tuple[List[str], List[str]]:
    """Extracts candidate GitHub repo URLs and project pages from arbitrary text."""
    gh_urls, project_urls = [], []
    if not text:
        return gh_urls, project_urls
    for m in re.finditer(r'(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-\.]+)', text, re.IGNORECASE):
        cleaned = clean_github_url(f"https://github.com/{m.group(1)}")
        if cleaned and cleaned not in gh_urls:
            gh_urls.append(cleaned)
    for m in re.finditer(r'https?://[a-zA-Z0-9_\-\.]+\.github\.io/[^\s"\'>\),;]+', text, re.IGNORECASE):
        url = m.group(0).rstrip(".,;:)'\"]>}")
        if url not in project_urls:
            project_urls.append(url)
    return gh_urls, project_urls


def extract_github_url(text: str) -> Optional[str]:
    """Returns the first verified or valid GitHub repo URL from text."""
    ghs, _ = extract_github_candidates(text)
    return ghs[0] if ghs else None


if __name__ == "__main__":
    print("🔬 Testing GitHub Verifier...")
    assert clean_github_url("https://github.com/GuyTevet/motion-diffusion-model.git") == "https://github.com/GuyTevet/motion-diffusion-model"
    assert clean_github_url("https://mingyuan-zhang.github.io/MotionDiffuse") == "https://github.com/mingyuan-zhang/MotionDiffuse"
    assert clean_github_url("https://github.com/features") is None
    assert is_github_repo_live("https://github.com/GuyTevet/motion-diffusion-model") is True
    assert is_github_repo_live("https://github.com/fakeuser123984123/nonexistent-xyz-999") is False
    print("✅ All GitHub Verifier tests passed!")
