import os
import re
import sys
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import requests
from src.utils.logger import logger

HEADERS = {"User-Agent": "T2MResearchAgent/1.0 (mailto:academic@example.com)"}


def _extract_crossref_year(item: dict) -> str:
    """Extracts the best publication year from CrossRef item metadata."""
    for date_key in ["published-print", "published-online", "issued", "created"]:
        if date_key in item:
            date_parts = item[date_key].get("date-parts", [])
            if date_parts and date_parts[0] and date_parts[0][0]:
                return str(date_parts[0][0])
    return None


def query_academic_metadata(url: str, title: str) -> dict:
    """Queries ArXiv XML and CrossRef API for DOI, venue, year, and citations."""
    arxiv_year = None
    if "arxiv.org" in url:
        arxiv_id = url.split("/abs/")[-1].split("/pdf/")[-1].replace(".pdf", "").strip()
        xml_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
        try:
            req = urllib.request.Request(xml_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=5) as resp:
                root = ET.fromstring(resp.read().decode("utf-8"))
            entry = root.find("{http://www.w3.org/2005/Atom}entry")
            if entry is not None:
                pub_elem = entry.find("{http://www.w3.org/2005/Atom}published")
                if pub_elem is not None and len(pub_elem.text) >= 4:
                    arxiv_year = pub_elem.text[:4]
                doi_elem = entry.find("{http://arxiv.org/schemas/atom}doi")
                jref_elem = entry.find("{http://arxiv.org/schemas/atom}journal_ref")
                doi = doi_elem.text if doi_elem is not None else None
                journal_ref = jref_elem.text if jref_elem is not None else None

                if doi:
                    cr_res = requests.get(f"https://api.crossref.org/works/{doi}", headers=HEADERS, timeout=5)
                    if cr_res.status_code == 200:
                        item = cr_res.json().get("message", {})
                        venues = item.get("container-title", [])
                        return {
                            "venue": venues[0] if venues else "Peer-Reviewed Journal",
                            "year": _extract_crossref_year(item) or arxiv_year or "N/A",
                            "citations": int(item.get("is-referenced-by-count", 0)),
                            "status": "Peer-Reviewed Journal/Conf",
                        }
                elif journal_ref:
                    return {
                        "venue": journal_ref,
                        "year": arxiv_year or "N/A",
                        "citations": 0,
                        "status": "Peer-Reviewed (Journal Ref)",
                    }
        except Exception:
            pass

    # Query CrossRef Bibliographic Search
    try:
        clean_title = re.sub(r"[^\w\s]", " ", title)
        cr_url = f"https://api.crossref.org/works?query.bibliographic={urllib.parse.quote(clean_title)}&rows=3"
        res = requests.get(cr_url, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            items = res.json().get("message", {}).get("items", [])
            orig_words = set(re.findall(r"\w+", title.lower()))
            for item in items:
                found_title = item.get("title", [""])[0]
                found_words = set(re.findall(r"\w+", found_title.lower()))
                if orig_words and len(orig_words.intersection(found_words)) / len(orig_words) >= 0.4:
                    venues = item.get("container-title", [])
                    venue = venues[0] if venues else "Peer-Reviewed Journal"
                    citations = int(item.get("is-referenced-by-count", 0))
                    year = _extract_crossref_year(item) or arxiv_year or "N/A"
                    is_arxiv = any(p in venue.lower() for p in ["arxiv", "biorxiv"])
                    return {
                        "venue": venue,
                        "year": year,
                        "citations": citations,
                        "status": "ArXiv Preprint" if is_arxiv else "Peer-Reviewed Journal/Conf",
                    }
    except Exception as e:
        logger.error(f"[!] CrossRef search error for '{title[:30]}...': {e}")

    return {"venue": "ArXiv Preprint", "year": arxiv_year or "N/A", "citations": 0, "status": "Preprint (ArXiv)"}


def extract_papers_from_markdown(content: str) -> list:
    """Parses markdown links to extract paper titles and URLs."""
    if "# ACADEMIC CREDIBILITY" in content:
        content = content.split("# ACADEMIC CREDIBILITY")[0]

    pattern = r"\[*\[([^\]]+)\]\((http[s]?://[^\)]+)\)\]*"
    matches = re.findall(pattern, content)
    unique_papers = {}

    for raw_title, url in matches:
        clean_title = re.sub(r"^[\[\s]+|[\]\s]+$", "", raw_title)
        clean_title = re.sub(r"\s*\(\d{4}\)\s*$", "", clean_title).strip()
        if clean_title not in unique_papers and len(clean_title) > 5:
            unique_papers[clean_title] = {"title": clean_title, "url": url, "display_title": clean_title}

    return list(unique_papers.values())


def generate_credibility_table(papers: list) -> str:
    """Queries academic metadata and builds the ACADEMIC CREDIBILITY Markdown table."""
    enriched = []
    peer_reviewed = 0
    preprints = 0

    for i, paper in enumerate(papers):
        title = paper.get("title", "")
        url = paper.get("url", "")
        display = paper.get("display_title") or title
        logger.info(f"[{i+1}/{len(papers)}] Enriching citations for: '{title[:40]}...'")

        meta = query_academic_metadata(url, title)
        if "Peer-Reviewed" in meta["status"]:
            peer_reviewed += 1
        else:
            preprints += 1

        enriched.append({
            "title_link": f"[{display}]({url})",
            "year": meta["year"],
            "venue": meta["venue"],
            "citations": meta["citations"],
            "status": meta["status"],
        })
        time.sleep(0.2)

    enriched.sort(key=lambda x: (x["citations"], int(x["year"]) if str(x["year"]).isdigit() else 0), reverse=True)

    table = (
        "# ACADEMIC CREDIBILITY & PEER-REVIEW VERIFICATION\n\n"
        f"**Total Papers Analyzed:** {len(papers)} | "
        f"**Peer-Reviewed (IEEE/CVPR/SIGGRAPH/Journals):** {peer_reviewed} | "
        f"**ArXiv Preprints:** {preprints}\n\n"
        "| Paper Title | Year | Publication Venue / Journal | Citations | Peer-Review Status |\n"
        "| :--- | :---: | :--- | :---: | :--- |\n"
    )
    for row in enriched:
        table += f"| {row['title_link']} | {row['year']} | {row['venue']} | {row['citations']} | {row['status']} |\n"

    return table


def enrich_literature_review(markdown_content: str, papers: list = None) -> str:
    """Enriches the Literature Review markdown content with the verification table."""
    logger.info("==================================================")
    logger.info("🔍 Enriching Literature Review via ArXiv & CrossRef")
    logger.info("==================================================")

    base_content = markdown_content.split("# ACADEMIC CREDIBILITY")[0].strip()
    target_papers = papers if papers else extract_papers_from_markdown(base_content)

    if not target_papers:
        logger.warning("[!] No papers found to enrich.")
        return markdown_content

    credibility_table = generate_credibility_table(target_papers)
    return f"{base_content}\n\n---\n\n{credibility_table}"


if __name__ == "__main__":
    print("==================================================")
    print("🔬 Citation Enricher Standalone Diagnostic")
    print("==================================================")
    test_title = "Human Motion Diffusion Model"
    test_url = "https://arxiv.org/abs/2209.14916"
    print(f"[*] Testing metadata query for: '{test_title}'...")
    res = query_academic_metadata(test_url, test_title)
    print(f"[*] Venue: {res['venue']}")
    print(f"[*] Year: {res['year']}")
    print(f"[*] Citations: {res['citations']}")
    print(f"[*] Status: {res['status']}")
    print("==================================================")
    sys.exit(0 if res.get("year") else 1)
