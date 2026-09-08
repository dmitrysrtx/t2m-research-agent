import requests
import time

queries = [
    "text to motion kinematics",
    "physics guided motion diffusion",
    "reinforcement learning humanoid control",
    "3d human pose estimation SMPL"
]

url = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
headers = {"User-Agent": "T2M-Academic-Research-Agent/2.0"}

for q in queries:
    params = {
        "query": q,
        "fields": "title,year,abstract,citationCount,venue,url,paperId,openAccessPdf"
    }
    resp = requests.get(url, params=params, headers=headers, timeout=20)
    print(f"Query: '{q}' | Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json().get('data', [])
        with_abs = [p for p in data if p.get('abstract')]
        print(f"  Total: {len(data)} | With abstract: {len(with_abs)}")
        if with_abs:
            print(f"  First: {with_abs[0]['title']} ({with_abs[0].get('year')}) | Cit: {with_abs[0].get('citationCount')}")
    else:
        print(f"  Error: {resp.text[:200]}")
    time.sleep(2)
