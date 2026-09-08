import requests

url = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
params = {
    "query": "3d human pose estimation SMPL",
    "fields": "title,year,abstract,citationCount,venue,url,paperId,openAccessPdf"
}
headers = {"User-Agent": "T2M-Academic-Research-Agent/2.0"}
resp = requests.get(url, params=params, headers=headers, timeout=15)
with open("test_s2_pose.txt", "w") as f:
    f.write(f"Status: {resp.status_code}\n")
    if resp.status_code == 200:
        data = resp.json()
        f.write(f"Total: {data.get('total')}\n")
        f.write(f"Hits: {len(data.get('data', []))}\n")
        with_abs = [p for p in data.get('data', []) if p.get('abstract')]
        f.write(f"With abstract: {len(with_abs)}\n")
        for p in with_abs[:3]:
            f.write(f" - {p.get('title')} ({p.get('year')}) | cit: {p.get('citationCount')} | venue: {p.get('venue')}\n")
    else:
        f.write(resp.text[:500])
