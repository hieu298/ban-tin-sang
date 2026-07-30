# -*- coding: utf-8 -*-
import io, sys, requests
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.hsx.vn/"}

# Test securitiesType/1 with pageSize=20
print("=== securitiesType/1 ===")
for pg in [1, 2, 3, 4, 5, 6]:
    r = requests.get("https://api.hsx.vn/n/api/v1/1/news/securitiesType/1", params={
        "pageIndex": pg, "pageSize": 20,
        "startDate": "2026-06-30", "endDate": "2026-06-30",
    }, headers=headers)
    if r.status_code == 200:
        d = r.json()
        items = d.get("data", {}).get("list", [])
        p = d.get("data", {}).get("paging", {})
        print(f"  Page {pg}: OK  count={len(items)}  total={p.get('totalCount')}  pages={p.get('totalPages')}")
    else:
        print(f"  Page {pg}: {r.status_code} ERROR")

# Test aliasCate hose with pageSize=30
print("")
print("=== tin-tuc-hose ===")
for pg in [1, 2, 3, 7, 8]:
    r = requests.get("https://api.hsx.vn/n/api/v1/1/news", params={
        "pageIndex": pg, "pageSize": 30,
        "startDate": "2026-06-30", "endDate": "2026-06-30",
        "aliasCate": "tin-tuc-hose",
    }, headers=headers)
    if r.status_code == 200:
        d = r.json()
        items = d.get("data", {}).get("list", [])
        p = d.get("data", {}).get("paging", {})
        print(f"  Page {pg}: OK  count={len(items)}  total={p.get('totalCount')}  pages={p.get('totalPages')}")
    else:
        print(f"  Page {pg}: {r.status_code} ERROR")
