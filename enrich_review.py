import os
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import requests
import time
from src.utils.logger import logger

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LITERATURE_REVIEW_PATH = os.path.join(PROJECT_ROOT, "LITERATURE_REVIEW.md")

def extract_papers_from_markdown(file_path):
    if not os.path.exists(file_path):
        logger.error(f"[!] File not found: {file_path}")
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Exclude existing ACADEMIC CREDIBILITY section to avoid re-parsing output table links
    if "# ACADEMIC CREDIBILITY" in content:
        content = content.split("# ACADEMIC CREDIBILITY")[0]

    pattern = r'\[*\[([^\]]+)\]\((http[s]?://[^\)]+)\)\]*'
    matches = re.findall(pattern, content)
    
    unique_papers = {}
    for raw_title, url in matches:
        clean_title = re.sub(r'^[\[\s]+|[\]\s]+$', '', raw_title)
        clean_title = re.sub(r'\s*\(\d{4}\)\s*$', '', clean_title).strip()
        
        if clean_title not in unique_papers and len(clean_title) > 5:
            unique_papers[clean_title] = {
                "title": clean_title,
                "url": url,
                "display_title": clean_title
            }

    return list(unique_papers.values())

def extract_crossref_year(item):
    for date_key in ['published-print', 'published-online', 'issued', 'created']:
        if date_key in item:
            date_parts = item[date_key].get('date-parts', [])
            if date_parts and date_parts[0] and date_parts[0][0]:
                return str(date_parts[0][0])
    return None

def query_academic_metadata(url, title):
    """
    Queries ArXiv XML + CrossRef API (via query.bibliographic) for exact DOI, Journal Venue, Year, and Citations.
    """
    headers = {'User-Agent': 'T2MResearchAgent/1.0 (mailto:academic@example.com)'}

    arxiv_year = None
    arxiv_id = url.split('/abs/')[-1].split('/pdf/')[-1].replace('.pdf', '').strip()
    xml_url = f'http://export.arxiv.org/api/query?id_list={arxiv_id}'
    try:
        req = urllib.request.Request(xml_url, headers=headers)
        req_data = urllib.request.urlopen(req, timeout=5).read().decode('utf-8')
        root = ET.fromstring(req_data)
        entry = root.find('{http://www.w3.org/2005/Atom}entry')
        
        if entry is not None:
            pub_elem = entry.find('{http://www.w3.org/2005/Atom}published')
            upd_elem = entry.find('{http://www.w3.org/2005/Atom}updated')
            if pub_elem is not None and len(pub_elem.text) >= 4:
                arxiv_year = pub_elem.text[:4]
            elif upd_elem is not None and len(upd_elem.text) >= 4:
                arxiv_year = upd_elem.text[:4]

            doi_elem = entry.find('{http://arxiv.org/schemas/atom}doi')
            jref_elem = entry.find('{http://arxiv.org/schemas/atom}journal_ref')
            
            doi = doi_elem.text if doi_elem is not None else None
            journal_ref = jref_elem.text if jref_elem is not None else None
            
            if doi:
                cr_res = requests.get(f'https://api.crossref.org/works/{doi}', headers=headers, timeout=5)
                if cr_res.status_code == 200:
                    item = cr_res.json().get('message', {})
                    venues = item.get('container-title', [])
                    venue = venues[0] if venues else "Peer-Reviewed Journal"
                    citations = item.get('is-referenced-by-count', 0)
                    year = extract_crossref_year(item) or arxiv_year or "N/A"
                    return {
                        "venue": venue,
                        "year": year,
                        "citations": int(citations),
                        "status": "Peer-Reviewed Journal/Conf"
                    }
            elif journal_ref:
                return {
                    "venue": journal_ref,
                    "year": arxiv_year or "N/A",
                    "citations": 0,
                    "status": "Peer-Reviewed (Journal Ref)"
                }
    except Exception:
        pass

    # 2. Query CrossRef Bibliographic Search
    try:
        clean_search_title = re.sub(r'[^\w\s]', ' ', title)
        cr_url = f"https://api.crossref.org/works?query.bibliographic={urllib.parse.quote(clean_search_title)}&rows=3"
        res = requests.get(cr_url, headers=headers, timeout=8)
        
        if res.status_code == 200:
            items = res.json().get('message', {}).get('items', [])
            orig_words = set(re.findall(r'\w+', title.lower()))
            
            for item in items:
                found_title = item.get('title', [''])[0]
                found_words = set(re.findall(r'\w+', found_title.lower()))
                
                # Check if there is significant overlap in words
                if len(orig_words) > 0 and len(orig_words.intersection(found_words)) / len(orig_words) >= 0.4:
                    venues = item.get('container-title', [])
                    venue = venues[0] if venues else "Peer-Reviewed Journal"
                    citations = item.get('is-referenced-by-count', 0)
                    year = extract_crossref_year(item) or arxiv_year or "N/A"
                    
                    is_arxiv = "arxiv" in venue.lower() or "biorxiv" in venue.lower()
                    status = "ArXiv Preprint" if is_arxiv else "Peer-Reviewed Journal/Conf"
                    
                    return {
                        "venue": venue,
                        "year": year,
                        "citations": int(citations),
                        "status": status
                    }
    except Exception as e:
        logger.error(f"[!] Error querying CrossRef for '{title[:30]}...': {e}")

    return {
        "venue": "ArXiv Preprint",
        "year": arxiv_year or "N/A",
        "citations": 0,
        "status": "Preprint (ArXiv)"
    }

def main():
    logger.info("==================================================")
    logger.info("🔍 Enriching Literature Review via ArXiv & CrossRef")
    logger.info("==================================================\n")

    papers = extract_papers_from_markdown(LITERATURE_REVIEW_PATH)
    logger.info(f"[*] Found {len(papers)} unique papers in {LITERATURE_REVIEW_PATH}")

    # Remove existing ACADEMIC CREDIBILITY section if present before re-appending
    if os.path.exists(LITERATURE_REVIEW_PATH):
        with open(LITERATURE_REVIEW_PATH, "r", encoding="utf-8") as f:
            full_text = f.read()
        if "# ACADEMIC CREDIBILITY" in full_text:
            full_text = full_text.split("# ACADEMIC CREDIBILITY")[0].strip()
            with open(LITERATURE_REVIEW_PATH, "w", encoding="utf-8") as f:
                f.write(full_text + "\n\n")

    enriched_results = []
    peer_reviewed_count = 0
    preprint_count = 0

    for i, paper in enumerate(papers):
        title = paper["title"]
        url = paper["url"]
        logger.info(f"[{i+1}/{len(papers)}] Checking CrossRef/ArXiv for: '{title[:40]}...'")
        
        metadata = query_academic_metadata(url, title)
        
        if "Peer-Reviewed" in metadata["status"]:
            peer_reviewed_count += 1
        else:
            preprint_count += 1

        enriched_results.append({
            "title_link": f"[{paper['display_title']}]({paper['url']})",
            "year": metadata["year"],
            "venue": metadata["venue"],
            "citations": metadata["citations"],
            "status": metadata["status"]
        })
        time.sleep(0.3)

    # Sort table by Citations descending, then Year descending
    enriched_results.sort(
        key=lambda x: (x["citations"], int(x["year"]) if str(x["year"]).isdigit() else 0),
        reverse=True
    )

    # Generate Markdown Table
    verification_md = "# ACADEMIC CREDIBILITY & PEER-REVIEW VERIFICATION\n\n"
    verification_md += f"**Total Papers Analyzed:** {len(papers)} | "
    verification_md += f"**Peer-Reviewed (IEEE/CVPR/SIGGRAPH/Journals):** {peer_reviewed_count} | "
    verification_md += f"**ArXiv Preprints:** {preprint_count}\n\n"
    
    verification_md += "| Paper Title | Year | Publication Venue / Journal | Citations | Peer-Review Status |\n"
    verification_md += "| :--- | :---: | :--- | :---: | :--- |\n"
    
    for item in enriched_results:
        verification_md += f"| {item['title_link']} | {item['year']} | {item['venue']} | {item['citations']} | {item['status']} |\n"

    # Append to LITERATURE_REVIEW.md
    with open(LITERATURE_REVIEW_PATH, "a", encoding="utf-8") as f:
        f.write(verification_md)

    logger.info(f"\n✅ Enrichment Complete! Added Peer-Review Verification table (sorted by Citations) to {LITERATURE_REVIEW_PATH}")
    logger.info(f"📊 Summary: {peer_reviewed_count} Peer-Reviewed, {preprint_count} Preprints.")

if __name__ == "__main__":
    main()
