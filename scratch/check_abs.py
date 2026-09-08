import requests

url = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
params = {
    "query": "text to motion kinematics",
    "fields": "title,year,abstract,citationCount,venue,url,paperId,openAccessPdf"
}
headers = {"User-Agent": "T2M-Academic-Research-Agent/2.0"}
resp = requests.get(url, params=params, headers=headers, timeout=15)
if resp.status_code == 200:
    data = resp.json().get('data', [])
    with_abs = [p for p in data if p.get('abstract')]
    print(f"Total: {len(data)}, With abstract: {len(with_abs)}")
    for p in with_abs[:5]:
        print(f" - {p.get('title')} | abstract len: {len(p.get('abstract', ''))}")
else:
    print(resp.status_code, resp.text[:200])
