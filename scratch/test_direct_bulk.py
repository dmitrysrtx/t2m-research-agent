import requests

url = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
params = {
    "query": "text to motion kinematics",
    "fields": "title,year,abstract,citationCount,venue,url,paperId,openAccessPdf"
}
headers = {"User-Agent": "T2M-Academic-Research-Agent/2.0"}
resp = requests.get(url, params=params, headers=headers, timeout=15)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"Total: {data.get('total')}, Data: {len(data.get('data', []))}")
else:
    print(resp.text[:200])
