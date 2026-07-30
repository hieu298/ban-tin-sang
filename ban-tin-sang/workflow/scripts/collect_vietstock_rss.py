import argparse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

FEEDS = [
    {
        "name": "Nhận định thị trường",
        "url": "https://vietstock.vn/1636/nhan-dinh-phan-tich/nhan-dinh-thi-truong.rss"
    },
    {
        "name": "Cổ tức",
        "url": "https://vietstock.vn/738/doanh-nghiep/co-tuc.rss"
    },
    {
        "name": "Chứng khoán thế giới",
        "url": "https://vietstock.vn/773/the-gioi/chung-khoan-the-gioi.rss"
    }
]

def fetch_rss_feed(url, limit=5):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        xml_data = urllib.request.urlopen(req).read()
        root = ET.fromstring(xml_data)
        
        items = []
        for item in root.findall('.//item')[:limit]:
            title = item.find('title').text if item.find('title') is not None else ''
            link = item.find('link').text if item.find('link') is not None else ''
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
            
            # Clean up title (remove CDATA if present, though ET usually handles it)
            title = title.replace("<![CDATA[", "").replace("]]>", "").strip()
            
            # Convert pubDate to a shorter format if possible (e.g. "Wed, 01 Jul 2026 09:30:00 GMT")
            # For simplicity, we just keep the raw date or a part of it
            pub_time = pub_date[17:22] if len(pub_date) > 22 else pub_date
            
            items.append({
                'title': title,
                'link': link,
                'time': pub_time
            })
        return items
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description="Collect Vietstock RSS Feeds")
    parser.add_argument("--date", type=str, required=True, help="Date in YYYY-MM-DD format")
    args = parser.parse_args()

    date_str = args.date
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    script_dir = Path(__file__).parent.resolve()
    output_dir = script_dir.parent.parent / "output" / "drafts"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    out_file = output_dir / f"{date_str}_vietstock.md"
    
    lines = [
        f"---",
        f"date: {date_str}",
        f"source: vietstock.vn/rss",
        f"generated: {now}",
        f"---",
        f"",
        f"# 📊 Tin Tức Vietstock — {date_str}",
        f"",
        f"> **Nguồn**: [vietstock.vn](https://vietstock.vn) &nbsp;|&nbsp; **Thu thập**: {now}",
        f"",
        f"---",
        f""
    ]
    
    for feed in FEEDS:
        print(f"Fetching {feed['name']}...")
        items = fetch_rss_feed(feed['url'], limit=6)
        if items:
            lines.append(f"## {feed['name']}")
            for idx, item in enumerate(items):
                lines.append(f"• **{item['time']}**: [{item['title']}]({item['link']})")
            lines.append("")
            lines.append("---")
            lines.append("")
            
    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Đã lưu kết quả tại: {out_file}")

if __name__ == "__main__":
    main()
