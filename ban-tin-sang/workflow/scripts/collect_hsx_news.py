# -*- coding: utf-8 -*-
"""
collect_hsx_news.py
====================
Thu thập tin tức doanh nghiệp từ HOSE (hsx.vn) theo ngày
và tạo báo cáo Markdown tổng hợp.

Cách dùng:
  python collect_hsx_news.py                    # Lấy tin hôm qua
  python collect_hsx_news.py --date 2026-06-30  # Lấy tin ngày cụ thể
  python collect_hsx_news.py --date 2026-06-30 --open  # Mở file sau khi tạo

Nguồn API: https://api.hsx.vn
URL bài viết: https://www.hsx.vn/vi/tin-tuc/tin-chi-tiet/{id}
"""

import io
import sys

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import requests
import json
import argparse
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

# ─── CẤU HÌNH ────────────────────────────────────────────────────────────────

BASE_API = "https://api.hsx.vn/n/api/v1/1"
BASE_WEB = "https://www.hsx.vn/vi/tin-tuc/tin-chi-tiet"
PAGE_SIZE = 100

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.hsx.vn/",
    "Accept": "application/json",
}

# Danh mục thu thập — (key, tên hiển thị, endpoint, extra_params)
CATEGORIES = [
    {
        "key": "co-phieu",
        "name": "🏢 Tin Doanh nghiệp — Cổ phiếu",
        "url": f"{BASE_API}/news/securitiesType/1",
        "params": {},
        "page_size": 20,  # securitiesType API giới hạn nhỏ hơn
    },
    {
        "key": "trai-phieu",
        "name": "💳 Tin Doanh nghiệp — Trái phiếu",
        "url": f"{BASE_API}/news/securitiesType/2",
        "params": {},
        "page_size": 20,
    },
    {
        "key": "hose",
        "name": "🏦 Tin HOSE",
        "url": f"{BASE_API}/news",
        "params": {"aliasCate": "tin-tuc-hose"},
        "page_size": 30,  # aliasCate API ổn hơn nhưng vẫn giới hạn
    },
    {
        "key": "ctck",
        "name": "🏛️ Tin Thành viên (CTCK)",
        "url": f"{BASE_API}/news",
        "params": {"aliasCate": "tin-ctcktv"},
        "page_size": 30,
    },
]

# ─── THƯ MỤC ĐẦU RA ─────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
# workflow/scripts -> workflow -> ban-tin-sang
PROJECT_DIR = SCRIPT_DIR.parent.parent
OUTPUT_DIR = PROJECT_DIR / "sources" / "raw-feeds"
REPORT_DIR = PROJECT_DIR / "output" / "drafts"


# ─── HÀM TIỆN ÍCH ────────────────────────────────────────────────────────────

def unix_to_hhmm(ts) -> str:
    """Chuyển Unix timestamp (int/float) sang chuỗi HH:MM."""
    if ts is None:
        return "—"
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%H:%M")
    except Exception:
        return "—"


def extract_ticker(title: str) -> str:
    """Trích mã cổ phiếu từ tiêu đề."""
    if not title:
        return ""
    # Pattern: "ABC:" ở đầu tiêu đề (phổ biến nhất trên HSX)
    m = re.match(r"^([A-Z0-9]{2,6})\s*[:]\s*", title)
    if m:
        skip = {"HOSE", "HNX", "UBND", "HDQT", "AGM", "CTCP", "BCTC"}
        if m.group(1) not in skip:
            return m.group(1)
    return ""


def clean_html(text: str) -> str:
    """Xóa HTML tags và whitespace thừa."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:200] + "..." if len(text) > 200 else text


# ─── THU THẬP DỮ LIỆU ────────────────────────────────────────────────────────

def fetch_page(url: str, params: dict, date_str: str, page: int, page_size: int = PAGE_SIZE) -> dict:
    """Gọi 1 page từ HSX API."""
    p = {
        "pageIndex": page,
        "pageSize": page_size,
        "startDate": date_str,
        "endDate": date_str,
    }
    p.update(params)
    try:
        r = requests.get(url, params=p, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"    ⚠️  Lỗi HTTP [{url}]: {e}")
        return {}


def fetch_category(cat: dict, date_str: str) -> list:
    """Lấy toàn bộ tin của 1 danh mục trong ngày."""
    all_items = []
    page = 1
    ps = cat.get("page_size", PAGE_SIZE)

    while True:
        data = fetch_page(cat["url"], cat["params"], date_str, page, ps)
        if not data or not data.get("success"):
            break

        block = data.get("data", {})
        items = block.get("list", [])
        paging = block.get("paging", {})
        total_pages = paging.get("totalPages", 1)

        all_items.extend(items)

        if page >= total_pages or not items:
            break
        page += 1

    return all_items


def normalize(item: dict) -> dict:
    """Chuẩn hóa 1 item tin tức."""
    item_id = item.get("id", "")
    title = (item.get("title") or "").strip()
    ticker = extract_ticker(title)

    # Thời gian
    ts = item.get("postedDate") or item.get("publishFrom") or item.get("createdDate")
    time_str = unix_to_hhmm(ts)

    # URL
    url = f"{BASE_WEB}/{item_id}" if item_id else ""

    # Tóm tắt
    summary = clean_html(item.get("summary") or item.get("description") or "")

    return {
        "id": item_id,
        "title": title,
        "ticker": ticker,
        "time": time_str,
        "url": url,
        "summary": summary,
        "_ts": int(ts) if ts else 0,
        "_raw": item,
    }


# ─── TẠO BÁO CÁO MARKDOWN ────────────────────────────────────────────────────

def build_report(date_str: str, all_data: dict) -> str:
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    date_vn = date_obj.strftime("%d/%m/%Y")
    day_name = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"][date_obj.weekday()]
    now_str = datetime.now().strftime("%H:%M — %d/%m/%Y")

    total = sum(len(v) for v in all_data.values())

    lines = [
        f"---",
        f"date: {date_str}",
        f"source: hsx.vn",
        f"total_news: {total}",
        f"generated: {datetime.now().isoformat()}",
        f"---",
        f"",
        f"# 🏛️ Tin Tức HOSE — {day_name}, {date_vn}",
        f"",
        f"> **Nguồn**: [hsx.vn](https://www.hsx.vn/vi/tin-tuc) &nbsp;|&nbsp; **Thu thập**: {now_str} &nbsp;|&nbsp; **Tổng**: {total} tin",
        f"",
        f"---",
        f"",
        f"## 📊 Tổng Quan",
        f"",
        f"| Danh mục | Số tin |",
        f"|:---------|-------:|",
    ]

    for cat in CATEGORIES:
        count = len(all_data.get(cat["key"], []))
        lines.append(f"| {cat['name']} | {count} |")
    lines.append(f"| **📌 Tổng cộng** | **{total}** |")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # Chi tiết từng danh mục
    for cat in CATEGORIES:
        key = cat["key"]
        items = all_data.get(key, [])
        lines.append(f"## {cat['name']}")
        lines.append(f"")

        if not items:
            lines.append(f"*Không có tin trong ngày {date_vn}.*")
            lines.append(f"")
            lines.append(f"---")
            lines.append(f"")
            continue

        # Sắp xếp theo thời gian
        sorted_items = sorted(items, key=lambda x: x["_ts"])

        lines.append(f"| Giờ | Mã | Tiêu đề |")
        lines.append(f"|:---:|:---:|:--------|")

        for item in sorted_items:
            ticker_cell = f"`{item['ticker']}`" if item["ticker"] else "—"
            title_safe = item["title"].replace("|", "\\|")
            url = item["url"]
            title_linked = f"[{title_safe}]({url})" if url else title_safe
            lines.append(f"| {item['time']} | {ticker_cell} | {title_linked} |")

        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")

    # Footer
    lines.append(f"*Báo cáo tự động tạo bởi `collect_hsx_news.py` | {now_str}*")
    return "\n".join(lines)


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Thu thập tin HOSE theo ngày")
    parser.add_argument("--date", default=None,
                        help="Ngày lấy tin (YYYY-MM-DD). Mặc định: hôm qua")
    parser.add_argument("--open", action="store_true",
                        help="Mở file báo cáo sau khi tạo")
    parser.add_argument("--no-json", action="store_true",
                        help="Không lưu JSON raw")
    args = parser.parse_args()

    # Xác định ngày
    if args.date:
        try:
            target = datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print(f"❌ Ngày không hợp lệ: {args.date}. Dùng: YYYY-MM-DD")
            sys.exit(1)
    else:
        target = datetime.now() - timedelta(days=1)

    date_str = target.strftime("%Y-%m-%d")
    date_vn = target.strftime("%d/%m/%Y")

    print(f"\n{'='*60}")
    print(f"  📡 THU THẬP TIN HOSE — {date_vn}")
    print(f"{'='*60}\n")

    # Tạo thư mục
    raw_dir = OUTPUT_DIR / date_str
    raw_dir.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Thu thập từng danh mục
    all_data: dict[str, list] = {}
    for cat in CATEGORIES:
        print(f"  🔄 {cat['name']}...")
        raw = fetch_category(cat, date_str)
        normalized = [normalize(item) for item in raw]
        # Bỏ duplicate theo id
        seen = set()
        unique = []
        for n in normalized:
            if n["id"] not in seen:
                seen.add(n["id"])
                unique.append(n)
        all_data[cat["key"]] = unique
        print(f"     → {len(unique)} tin")

    total = sum(len(v) for v in all_data.values())
    print(f"\n  ✅ Tổng: {total} tin\n")

    # Báo cáo Markdown
    md_content = build_report(date_str, all_data)
    md_path = REPORT_DIR / f"{date_str}_hsx-news.md"
    md_path.write_text(md_content, encoding="utf-8")
    print(f"  📄 Báo cáo: {md_path}")

    # JSON raw
    if not args.no_json:
        json_payload = {
            "date": date_str,
            "fetched_at": datetime.now().isoformat(),
            "total": total,
            "categories": {
                k: [i["_raw"] for i in v] for k, v in all_data.items()
            },
        }
        json_path = raw_dir / f"{date_str}_hsx-news.json"
        json_path.write_text(
            json.dumps(json_payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  💾 JSON raw: {json_path}")

    # Thống kê cuối
    print(f"\n{'─'*60}")
    for cat in CATEGORIES:
        key = cat["key"]
        count = len(all_data.get(key, []))
        bar = "█" * min(count // 2, 25)
        print(f"  {cat['name'][:35]:35s}  {count:4d}  {bar}")
    print(f"{'─'*60}")
    print(f"  {'TỔNG':35s}  {total:4d}")
    print(f"{'='*60}\n")

    # Mở file
    if args.open:
        os.startfile(str(md_path))

    return str(md_path)


if __name__ == "__main__":
    main()
