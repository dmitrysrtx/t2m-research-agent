import requests
from src.fetchers.github_finder import extract_github_url

def parse_item(item, min_citations=0):
    abstract = (item.get('abstract') or '').strip()
    if not abstract:
        return None
    cit = item.get('citationCount') or 0
    if cit < min_citations:
        return None
    pid = item.get('paperId')
    purl = item.get('url') or (f"https://www.semanticscholar.org/paper/{pid}" if pid else "No URL")
    pdf = (item.get('openAccessPdf') or {}).get('url') if isinstance(item.get('openAccessPdf'), dict) else None
    return {
        "title": (item.get('title') or '').strip(),
        "year": str(item.get('year') or ''),
        "abstract": abstract,
        "url": purl,
        "pdf_url": pdf,
        "github_url": extract_github_url(abstract) or "N/A",
        "citations": cit,
        "venue": item.get('venue') or 'Unknown',
        "source": "SemanticScholar"
    }

def bulk_search(query, max_results=5, min_citations=0):
    url = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
    params = {
        "query": query,
        "fields": "title,year,abstract,citationCount,venue,url,paperId,openAccessPdf"
    }
    headers = {"User-Agent": "T2M-Academic-Research-Agent/2.0"}
    r = requests.get(url, params=params, headers=headers, timeout=20)
    if r.status_code == 200:
        data = r.json().get('data', [])
        papers = []
        for it in data:
            p = parse_item(it, min_citations=min_citations)
            if p:
                papers.append(p)
            if len(papers) >= max_results:
                break
        return papers
    return []

for q in ["text to motion kinematics", "3d human pose estimation SMPL"]:
    res = bulk_search(q, max_results=3)
    print(f"Query: '{q}' -> Found {len(res)} papers:")
    for p in res:
        print(f"  - [{p['year']}] {p['title']} (Citations: {p['citations']}, Venue: {p['venue']})")
