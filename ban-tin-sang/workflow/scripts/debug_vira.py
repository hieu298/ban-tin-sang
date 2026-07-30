# -*- coding: utf-8 -*-
import io, sys, re, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

r = requests.get(
    "https://vira.org.vn/tin/Ban-tin-Kinh-te-Tai-chinh-ngay/Ban-tin-Kinh-te-Tai-chinh-ngay-01-07-2026-.html",
    headers={"User-Agent": "Mozilla/5.0", "Referer": "https://vira.org.vn/"},
    timeout=15
)
html = r.text

# Find abody
idx = html.find("abody")
print("abody found at:", idx)
snippet = html[idx:idx+200]
print("Snippet:", repr(snippet))

# Find content area
idx2 = html.find("content-top")
print("\ncontent-top at:", idx2)
snippet2 = html[idx2:idx2+200]
print("Snippet2:", repr(snippet2))

# Find all div ids
ids = re.findall(r'id="([^"]+)"', html)
print("\nAll div IDs:", ids[:20])

# Find content markers
for marker in ["content-bottom", "detail__footer", "detail__content"]:
    pos = html.find(marker)
    print(f"  [{marker}] at: {pos}")
