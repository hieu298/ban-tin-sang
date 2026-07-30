import urllib.request
from bs4 import BeautifulSoup
import re

html = urllib.request.urlopen(urllib.request.Request('https://vietstock.vn/rss', headers={'User-Agent': 'Mozilla/5.0'})).read().decode('utf-8')
soup = BeautifulSoup(html, 'html.parser')
for a in soup.find_all('a', href=True):
    if a['href'].endswith('.rss'):
        print(f"{a.text.strip()}: {a['href']}")
