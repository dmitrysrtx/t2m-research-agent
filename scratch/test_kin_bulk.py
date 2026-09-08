import requests
import time

time.sleep(3)
url = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
headers = {"User-Agent": "T2M-Academic-Research-Agent/2.0"}
params = {
    "query": "kinematic human motion generation",
    "fields": "title,year,abstract,citationCount,venue,url,paperId,openAccessPdf"
}
resp = requests.get(url, params=params, headers=headers, timeout=20)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json().get('data', [])
    with_abs = [p for p in data if p.get('abstract')]
    print(f"Total: {len(data)}, With abstract: {len(with_abs)}")
    if with_abs:
        print(f"Sample: {with_abs[0]['title']} ({with_abs[0].get('year')})")
else:
    print(resp.text[:200])
