import requests

url = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
params = {
    "query": "text to motion kinematics",
    "fields": "title,year,abstract,citationCount,venue,url,paperId,openAccessPdf"
}
headers = {"User-Agent": "T2M-Academic-Research-Agent/2.0"}
resp = requests.get(url, params=params, headers=headers, timeout=15)
with open("test_s2_result2.txt", "w") as f:
    f.write(f"Status: {resp.status_code}\n")
    if resp.status_code == 200:
        data = resp.json()
        f.write(f"Total: {data.get('total')}\n")
        f.write(f"Hits: {len(data.get('data', []))}\n")
        for p in data.get('data', [])[:3]:
            f.write(f" - {p.get('title')} ({p.get('year')}) | has_abs: {bool(p.get('abstract'))}\n")
    else:
        f.write(resp.text[:500])
