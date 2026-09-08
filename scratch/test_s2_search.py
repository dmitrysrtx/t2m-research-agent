import requests

url = "https://api.semanticscholar.org/graph/v1/paper/search"
params = {
    "query": "text to motion kinematics",
    "limit": 3,
    "fields": "title,year,abstract,citationCount,venue,url,paperId,openAccessPdf,tldr"
}
headers = {"User-Agent": "T2M-Academic-Research-Agent/2.0"}
resp = requests.get(url, params=params, headers=headers, timeout=15)
with open("test_s2_search.txt", "w") as f:
    f.write(f"Status: {resp.status_code}\n")
    f.write(resp.text[:500])
