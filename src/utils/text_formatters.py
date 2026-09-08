import re
from typing import Optional


def format_github_link(owner: str, repo: str) -> str:
    """Returns standardized markdown link [owner/repo](https://github.com/owner/repo)."""
    clean_repo = repo.removesuffix(".git").rstrip("/.,;:)'\"")
    return f"[{owner}/{clean_repo}](https://github.com/{owner}/{clean_repo})"


def clean_github_markdown_link(text: str) -> str:
    """
    Standardizes all GitHub links in Markdown tables/text into [owner/repo](https://github.com/owner/repo).
    Converts full-URL anchor links, custom anchor text links, and bare URLs.
    Preserves other Markdown links (e.g. ArXiv paper titles) and N/A placeholders.
    """
    if not text:
        return text

    # 1. Standardize existing Markdown links: [anything](https://github.com/owner/repo)
    def _replace_md_link(match):
        owner = match.group(3)
        repo = match.group(4)
        if owner.lower() in ("features", "topics", "pulls", "issues"):
            return match.group(0)
        return format_github_link(owner, repo)

    pattern_md = r'\[([^\]]+)\]\((https?://(?:www\.)?github\.com/([a-zA-Z0-9_\-]+)/([a-zA-Z0-9_\-\.]+)/?)\)'
    text = re.sub(pattern_md, _replace_md_link, text)

    # 2. Standardize bare GitHub URLs not enclosed in Markdown links
    def _replace_bare_url(match):
        owner = match.group(1)
        repo = match.group(2)
        if owner.lower() in ("features", "topics", "pulls", "issues"):
            return match.group(0)
        return format_github_link(owner, repo)

    pattern_bare = r'(?<![\(\[\/])https?://(?:www\.)?github\.com/([a-zA-Z0-9_\-]+)/([a-zA-Z0-9_\-\.]+)(?![^\s\|]*\))'
    text = re.sub(pattern_bare, _replace_bare_url, text)

    return text


if __name__ == "__main__":
    print("🔬 Text Formatters Standalone Diagnostic Test")
    
    # Test 1: Markdown link with full URL as anchor
    t1 = "| [Title (2022)](https://arxiv.org/abs/123) | [https://github.com/GuyTevet/motion-diffusion-model](https://github.com/GuyTevet/motion-diffusion-model) |"
    c1 = clean_github_markdown_link(t1)
    assert "[GuyTevet/motion-diffusion-model](https://github.com/GuyTevet/motion-diffusion-model)" in c1
    assert "[Title (2022)](https://arxiv.org/abs/123)" in c1

    # Test 2: Markdown link with custom text
    t2 = "| Paper | [Code Repo](https://github.com/wuyan01/UniPhys) |"
    c2 = clean_github_markdown_link(t2)
    assert "[wuyan01/UniPhys](https://github.com/wuyan01/UniPhys)" in c2

    # Test 3: Bare GitHub URL
    t3 = "| Paper | https://github.com/akashsengupta1997/STRAPS-3DHumanShapePose | N/A |"
    c3 = clean_github_markdown_link(t3)
    assert "[akashsengupta1997/STRAPS-3DHumanShapePose](https://github.com/akashsengupta1997/STRAPS-3DHumanShapePose)" in c3
    assert "N/A" in c3

    # Test 4: Already standardized link remains identical
    t4 = "| Paper | [GuyTevet/motion-diffusion-model](https://github.com/GuyTevet/motion-diffusion-model) |"
    c4 = clean_github_markdown_link(t4)
    assert c4 == t4

    print("✅ All Text Formatter tests passed successfully!")
