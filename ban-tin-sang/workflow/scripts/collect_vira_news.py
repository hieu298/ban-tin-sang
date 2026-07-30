# -*- coding: utf-8 -*-
"""
collect_vira_news.py
====================
Thu thập Bản tin Kinh tế - Tài chính ngày từ vira.org.vn
Lưu dạng text sạch và markdown có cấu trúc.

Cách dùng:
  python collect_vira_news.py                    # Hôm nay
  python collect_vira_news.py --date 2026-07-01  # Ngày cụ thể
  python collect_vira_news.py --date 2026-07-01 --open
"""

import io, sys, re, os, argparse
from datetime import datetime, timedelta
from pathlib import Path
from html import unescape

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import requests

# ─── CẤU HÌNH ────────────────────────────────────────────────────────────────

BASE_URL = "https://vira.org.vn/tin/Ban-tin-Kinh-te-Tai-chinh-ngay"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "vi-VN,vi;q=0.9",
    "Referer": "https://vira.org.vn/",
}

SCRIPT_DIR  = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent.parent   # workflow/scripts → workflow → ban-tin-sang
OUTPUT_DIR  = PROJECT_DIR / "sources" / "raw-feeds"
REPORT_DIR  = PROJECT_DIR / "output" / "drafts"

# Noise lines to filter out (navigation, related articles, etc.)
NOISE_PATTERNS = [
    r"^Cùng chuyên mục$",
    r"^Đọc thêm$",
    r"^Bản tin Kinh tế - Tài chính ngày \d{2}/\d{2}/\d{4}\s*$",
    r"^\d{2}/\d{2}/\d{4} \d{2}:\d{2}$",
    r"^Market Watch",
    r"^Tổng hợp Kinh tế",
    r"^KHẢO SÁT",
    r"^\s*$",
]

# ─── UTILS ───────────────────────────────────────────────────────────────────

def build_url(d: datetime) -> str:
    return f"{BASE_URL}/Ban-tin-Kinh-te-Tai-chinh-ngay-{d.strftime('%d-%m-%Y')}-.html"


def is_noise(line: str) -> bool:
    return any(re.match(p, line.strip()) for p in NOISE_PATTERNS)


def clean_html_to_text(html_fragment: str) -> str:
    """HTML → text thuần, loại bỏ script/style và thẻ HTML."""
    t = unescape(html_fragment)
    # Remove <script> và <style>
    t = re.sub(r"<script[^>]*>.*?</script>", " ", t, flags=re.DOTALL | re.IGNORECASE)
    t = re.sub(r"<style[^>]*>.*?</style>",  " ", t, flags=re.DOTALL | re.IGNORECASE)
    # Block elements → newline
    t = re.sub(r"<br\s*/?>",      "\n", t, flags=re.IGNORECASE)
    t = re.sub(r"</?p[^>]*>",    "\n", t, flags=re.IGNORECASE)
    t = re.sub(r"</?div[^>]*>",  "\n", t, flags=re.IGNORECASE)
    t = re.sub(r"</?li[^>]*>",   "\n• ", t, flags=re.IGNORECASE)
    t = re.sub(r"</?tr[^>]*>",   "\n", t, flags=re.IGNORECASE)
    t = re.sub(r"</?td[^>]*>",   " | ", t, flags=re.IGNORECASE)
    # Strip all remaining tags
    t = re.sub(r"<[^>]+>", "", t)
    # Normalize whitespace
    lines = []
    for line in t.split("\n"):
        s = re.sub(r"[ \t]+", " ", line).strip()
        if s and not is_noise(s):
            lines.append(s)
    return "\n".join(lines)


# ─── PARSE ───────────────────────────────────────────────────────────────────

def parse(html: str) -> dict:
    out = dict(title="", published="", meta_desc="", content_raw="", pdf_url="")

    # Title
    m = re.search(r'<h1[^>]*class="detail__title"[^>]*>(.*?)</h1>', html, re.DOTALL)
    if m: out["title"] = clean_html_to_text(m.group(1)).strip()

    # Published time
    m = re.search(r'<div[^>]*class="detail__meta"[^>]*>(.*?)</div>', html, re.DOTALL)
    if m: out["published"] = clean_html_to_text(m.group(1)).strip()

    # Meta description (sapo) — from <head>
    m = re.search(r'name="description"\s+content="([^"]+)"', html)
    if m: out["meta_desc"] = unescape(m.group(1)).strip()

    # Extract #abody content by position
    start_marker = 'id="abody"'
    si = html.find(start_marker)
    if si > -1:
        si = html.find(">", si) + 1          # skip past the opening tag
        # End = first of these markers after si
        end_markers = ['class="content-bottom"', 'class="detail__footer"', 'class="sub-col"']
        ei = len(html)
        for em in end_markers:
            p = html.find(em, si)
            if 0 < p < ei:
                ei = p
        content_html = html[si:ei]

        # PDF link
        pm = re.search(r'href="(/upload/[^"]+\.pdf)"', content_html)
        if pm: out["pdf_url"] = "https://vira.org.vn" + pm.group(1)

        out["content_raw"] = content_html

    return out


# ─── STRUCTURE CONTENT ────────────────────────────────────────────────────────

def structure_content(content_raw: str) -> dict:
    """
    Tách nội dung thô thành các mục có cấu trúc:
    - domestic: Tin trong nước
    - international: Tin quốc tế
    - sections: dict {tên_mục: nội_dung}
    """
    text = clean_html_to_text(content_raw)

    # Tách Tin trong nước / Tin quốc tế
    domestic_raw = ""
    intl_raw = ""

    m_intl = re.search(r"Tin quốc tế\s*:?\s*\n", text)
    m_dom  = re.search(r"Tin trong nước\s*:?\s*\n", text)

    if m_dom and m_intl:
        domestic_raw    = text[m_dom.end():m_intl.start()].strip()
        intl_raw        = text[m_intl.end():].strip()
    elif m_dom:
        domestic_raw = text[m_dom.end():].strip()
    else:
        domestic_raw = text.strip()

    # Tách các tiểu mục trong Tin trong nước
    section_headers = [
        "Thị trường ngoại tệ",
        "Thị trường tiền tệ LNH",
        "Nghiệp vụ thị trường mở",
        "Thị trường chứng khoán",
        "Giá vàng",
        "Giá dầu",
        "Lạm phát",
        "Tín dụng",
    ]

    # Tìm các đoạn bắt đầu bằng tên tiểu mục
    sections = {}
    remaining = domestic_raw
    for header in section_headers:
        # Tìm đoạn bắt đầu bằng header này
        pattern = rf"(?:^|\n)({re.escape(header)}\s*:.*?)(?=\n(?:{'|'.join(re.escape(h) for h in section_headers)})|$)"
        m = re.search(pattern, remaining, re.DOTALL)
        if m:
            sections[header] = m.group(1).strip()

    # Phần còn lại (chính sách, chú thích, v.v.)
    # Loại bỏ các section đã extract
    other = remaining
    for _, v in sections.items():
        other = other.replace(v, "")
    other = "\n".join(l for l in other.split("\n") if l.strip())

    return {
        "domestic_raw": domestic_raw,
        "international_raw": intl_raw,
        "sections": sections,
        "other_domestic": other.strip(),
    }


# ─── FORMAT ──────────────────────────────────────────────────────────────────

def format_txt(date_obj: datetime, art: dict, url: str) -> str:
    date_vn  = date_obj.strftime("%d/%m/%Y")
    day_name = ["Thứ Hai","Thứ Ba","Thứ Tư","Thứ Năm","Thứ Sáu","Thứ Bảy","Chủ Nhật"][date_obj.weekday()]
    now      = datetime.now().strftime("%H:%M %d/%m/%Y")
    sep70    = "=" * 70
    dash70   = "-" * 70

    struct = structure_content(art["content_raw"])

    lines = [
        sep70,
        f"BẢN TIN KINH TẾ - TÀI CHÍNH NGÀY {date_vn} ({day_name})",
        sep70,
        f"Nguồn   : VIRA — vira.org.vn",
        f"URL     : {url}",
        f"Đăng    : {art['published']}",
        f"Lưu lúc : {now}",
        sep70,
        "",
    ]

    # Sapo
    if art["meta_desc"]:
        lines += [
            "[ TÓM TẮT ]",
            art["meta_desc"],
            "",
            dash70,
            "",
        ]

    # ── Tin trong nước ──
    lines += ["🇻🇳  TIN TRONG NƯỚC", dash70, ""]

    # Render từng tiểu mục nếu extract được
    section_order = [
        "Thị trường ngoại tệ",
        "Thị trường tiền tệ LNH",
        "Nghiệp vụ thị trường mở",
        "Thị trường chứng khoán",
        "Giá vàng",
        "Giá dầu",
    ]

    rendered_any = False
    for header in section_order:
        if header in struct["sections"]:
            lines += [f"▶ {header}", struct["sections"][header], ""]
            rendered_any = True

    if not rendered_any:
        # Fallback: dump toàn bộ domestic raw text
        lines += [struct["domestic_raw"], ""]

    # Nội dung khác (chính sách, etc.)
    if struct["other_domestic"]:
        lines += ["▶ Chính sách & vĩ mô", struct["other_domestic"], ""]

    lines += [dash70, ""]

    # ── Tin quốc tế ──
    if struct["international_raw"]:
        lines += ["🌍  TIN QUỐC TẾ", dash70, ""]
        # Tách từng quốc gia/vùng
        intl = struct["international_raw"]
        # Loại bỏ noise cuối
        intl = re.sub(r"\nBản tin Kinh tế.*$", "", intl, flags=re.DOTALL).strip()
        lines += [intl, ""]
        lines += [dash70, ""]

    # PDF
    if art["pdf_url"]:
        filename = art["pdf_url"].split("/")[-1]
        lines += [
            "📎 FILE PDF ĐẦY ĐỦ",
            f"   {filename}",
            f"   {art['pdf_url']}",
            "",
        ]

    lines += [sep70, f"Hết bản tin | {now}", sep70]
    return "\n".join(lines)


def format_md(date_obj: datetime, art: dict, url: str) -> str:
    date_str = date_obj.strftime("%Y-%m-%d")
    date_vn  = date_obj.strftime("%d/%m/%Y")
    day_name = ["Thứ Hai","Thứ Ba","Thứ Tư","Thứ Năm","Thứ Sáu","Thứ Bảy","Chủ Nhật"][date_obj.weekday()]
    now      = datetime.now().strftime("%H:%M %d/%m/%Y")

    struct = structure_content(art["content_raw"])

    lines = [
        f"---",
        f"date: {date_str}",
        f"source: vira.org.vn",
        f"category: ban-tin-kinh-te-tai-chinh-ngay",
        f"published: {art['published']}",
        f"url: {url}",
        f"---",
        f"",
        f"# 📊 Bản tin Kinh tế - Tài chính | {day_name} {date_vn}",
        f"",
        f"> **Nguồn**: [VIRA]({url}) &nbsp;|&nbsp; **Đăng**: {art['published']}",
        f"",
    ]

    if art["meta_desc"]:
        lines += [f"> **Tóm tắt**: {art['meta_desc']}", f""]

    lines += ["---", ""]

    # ── Tin trong nước ──
    lines += ["## 🇻🇳 Tin trong nước", ""]

    section_order = [
        ("Thị trường ngoại tệ", "💱"),
        ("Thị trường tiền tệ LNH", "🏦"),
        ("Nghiệp vụ thị trường mở", "⚙️"),
        ("Thị trường chứng khoán", "📈"),
        ("Giá vàng", "🥇"),
        ("Giá dầu", "🛢️"),
    ]

    rendered_any = False
    for header, icon in section_order:
        if header in struct["sections"]:
            content = struct["sections"][header]
            # Bold key numbers
            content = re.sub(r"(\d[\d.,]+(?:\s*(?:tỷ|triệu|nghìn|%|VND|USD|đpt|điểm))?)", r"**\1**", content)
            lines += [f"### {icon} {header}", "", content, ""]
            rendered_any = True

    if not rendered_any:
        text = struct["domestic_raw"]
        # Bold markers
        text = re.sub(r"(Thị trường [^:]+:|Nghiệp vụ [^:]+:|Giá [^:]+:)", r"**\1**", text)
        lines += [text, ""]

    if struct["other_domestic"]:
        text = struct["other_domestic"]
        text = re.sub(r"(Nghị quyết \S+|GDP|NHNN|Bộ Tài chính)", r"**\1**", text)
        lines += ["### 🏛️ Chính sách & Vĩ mô", "", text, ""]

    lines += ["---", ""]

    # ── Tin quốc tế ──
    if struct["international_raw"]:
        lines += ["## 🌍 Tin quốc tế", ""]
        intl = struct["international_raw"]
        intl = re.sub(r"\nBản tin Kinh tế.*$", "", intl, flags=re.DOTALL).strip()
        # Bold key numbers
        intl = re.sub(r"(\d[\d.,]+(?:\s*(?:%|điểm|triệu|tỷ))?)", r"**\1**", intl)
        lines += [intl, "", "---", ""]

    # PDF
    if art["pdf_url"]:
        fname = art["pdf_url"].split("/")[-1]
        lines += [
            f"## 📎 File đính kèm",
            f"",
            f"[{fname}]({art['pdf_url']}) — Bản tin đầy đủ PDF",
            f"",
            f"---",
            f"",
        ]

    lines += [f"*Thu thập bởi `collect_vira_news.py` | {now}*"]
    return "\n".join(lines)


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None, help="YYYY-MM-DD. Mặc định: hôm nay")
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()

    if args.date:
        try:    target = datetime.strptime(args.date, "%Y-%m-%d")
        except: print(f"❌ Ngày không hợp lệ: {args.date}"); sys.exit(1)
    else:
        target = datetime.now()

    date_str = target.strftime("%Y-%m-%d")
    date_vn  = target.strftime("%d/%m/%Y")
    url      = build_url(target)

    print(f"\n{'='*60}")
    print(f"  📡 BẢN TIN VIRA — {date_vn}")
    print(f"  {url}")
    print(f"{'='*60}\n")
    print(f"  🔄 Đang tải...")

    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        html = r.text
    except requests.exceptions.HTTPError as e:
        print(f"  ❌ HTTP {r.status_code} — Có thể chưa có bản tin ngày {date_vn}")
        sys.exit(1)
    except Exception as e:
        print(f"  ❌ Lỗi: {e}"); sys.exit(1)

    print(f"  🔍 Đang trích xuất...")
    art = parse(html)

    if not art["content_raw"]:
        print("  ❌ Không tìm thấy nội dung #abody")
        sys.exit(1)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    raw_dir = OUTPUT_DIR / date_str
    raw_dir.mkdir(parents=True, exist_ok=True)

    # File TXT
    txt = format_txt(target, art, url)
    txt_path = REPORT_DIR / f"{date_str}_vira-ban-tin.txt"
    txt_path.write_text(txt, encoding="utf-8")

    # File MD
    md = format_md(target, art, url)
    md_path = REPORT_DIR / f"{date_str}_vira-ban-tin.md"
    md_path.write_text(md, encoding="utf-8")

    # Raw backup
    raw_path = raw_dir / f"{date_str}_vira-raw.txt"
    raw_path.write_text(clean_html_to_text(art["content_raw"]), encoding="utf-8")

    # Stats
    struct = structure_content(art["content_raw"])
    print(f"\n  ✅ TXT : {txt_path}")
    print(f"  ✅ MD  : {md_path}")
    print(f"  ✅ Raw : {raw_path}")
    print(f"\n{'─'*60}")
    print(f"  Tiêu đề  : {art['title']}")
    print(f"  Đăng     : {art['published']}")
    print(f"  Nội dung : {len(clean_html_to_text(art['content_raw']))} ký tự")
    print(f"  Tiểu mục : {list(struct['sections'].keys())}")
    if art["pdf_url"]:
        print(f"  PDF      : {art['pdf_url'].split('/')[-1]}")
    print(f"{'='*60}\n")

    if args.open:
        os.startfile(str(txt_path))

if __name__ == "__main__":
    main()
