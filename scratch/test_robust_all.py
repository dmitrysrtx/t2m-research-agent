import time
import requests
from src.fetchers.github_finder import extract_github_url

def parse_paper_item(item, min_citations=0):
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

def fetch_s2_robust(query, max_results=5, min_citations=0, api_key=""):
    headers = {"User-Agent": "T2M-Academic-Research-Agent/2.0"}
    if api_key:
        headers["x-api-key"] = api_key

    # Prefer bulk search when unauthenticated for high yield without 429 blocks
    endpoints = []
    if api_key:
        endpoints.append(("https://api.semanticscholar.org/graph/v1/paper/search", {"limit": max_results * 4}))
    endpoints.append(("https://api.semanticscholar.org/graph/v1/paper/search/bulk", {}))
    if not api_key:
        endpoints.append(("https://api.semanticscholar.org/graph/v1/paper/search", {"limit": max_results * 4}))

    for url, extra_params in endpoints:
        params = {
            "query": query,
            "fields": "title,year,abstract,citationCount,venue,url,paperId,openAccessPdf"
        }
        params.update(extra_params)
        
        for attempt in range(3):
            try:
                time.sleep(3.0) # Respect 1 req/sec unauthenticated rate limit
                resp = requests.get(url, params=params, headers=headers, timeout=20)
                if resp.status_code == 429:
                    wait_time = 4 * (attempt + 1)
                    print(f"  [!] 429 on {url}. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                if resp.status_code == 200:
                    data = resp.json().get('data', [])
                    papers = []
                    for it in data:
                        p = parse_paper_item(it, min_citations)
                        if p:
                            papers.append(p)
                        if len(papers) >= max_results:
                            break
                    if papers:
                        return papers
            except Exception as e:
                print(f"  [!] Exception: {e}")
                time.sleep(2.0)
    return []

queries = {
    "kinematic": "kinematic human motion generation",
    "physics": "physics guided motion diffusion",
    "rl": "reinforcement learning humanoid control",
    "pose": "3d human pose estimation SMPL"
}

results = {}
for domain, q in queries.items():
    print(f"\n[*] Testing domain '{domain}' with query: '{q}'")
    papers = fetch_s2_robust(q, max_results=3)
    results[domain] = len(papers)
    print(f"[+] Domain '{domain}' retrieved {len(papers)} papers:")
    for p in papers:
        print(f"    - [{p['year']}] {p['title'][:60]}... | Cit: {p['citations']}")

print("\n" + "="*50)
print(f"FINAL TALLY: {results}")
print("="*50)
