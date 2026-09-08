import requests
import time

url = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
params = {
    "query": "3d human pose estimation SMPL",
    "fields": "title,year,abstract,citationCount,venue,url,paperId,openAccessPdf"
}
headers = {"User-Agent": "T2M-Academic-Research-Agent/2.0"}

for attempt in range(3):
    resp = requests.get(url, params=params, headers=headers, timeout=20)
    print(f"Attempt {attempt+1}: Status {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json().get('data', [])
        with_abs = [p for p in data if p.get('abstract')]
        print(f"Success! Papers with abstract: {len(with_abs)}")
        break
    time.sleep(6)
