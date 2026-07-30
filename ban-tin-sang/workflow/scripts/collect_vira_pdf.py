# -*- coding: utf-8 -*-
"""
collect_vira_pdf.py
====================
Tải và trích xuất nội dung PDF bản tin VIRA từ MSB Research.
Kết hợp nội dung web + PDF thành 1 bản tin hoàn chỉnh.

Cách dùng:
  python collect_vira_pdf.py                    # Hôm nay
  python collect_vira_pdf.py --date 2026-07-01  # Ngày cụ thể
  python collect_vira_pdf.py --date 2026-07-01 --open
"""

import io, sys, re, os, argparse, json
from datetime import datetime, timedelta
from pathlib import Path
from html import unescape

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import requests
from vira_table_parser import extract_tables_from_text

SCRIPT_DIR  = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
OUTPUT_DIR  = PROJECT_DIR / "sources" / "raw-feeds"
REPORT_DIR  = PROJECT_DIR / "output" / "drafts"

BASE_URL = "https://vira.org.vn/tin/Ban-tin-Kinh-te-Tai-chinh-ngay"
HEADERS  = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9",
    "Referer": "https://vira.org.vn/",
}

NOISE_PATTERNS = [
    r"^Cùng chuyên mục",
    r"^Đọc thêm",
    r"^\d{2}/\d{2}/\d{4} \d{2}:\d{2}$",
    r"^Market Watch",
    r"^Tổng hợp Kinh tế",
    r"^KHẢO SÁT",
    r"^VIRA",
]


# ─── UTILS ───────────────────────────────────────────────────────────────────

def build_url(d: datetime) -> str:
    return f"{BASE_URL}/Ban-tin-Kinh-te-Tai-chinh-ngay-{d.strftime('%d-%m-%Y')}-.html"


def is_noise(line: str) -> bool:
    return any(re.match(p, line.strip()) for p in NOISE_PATTERNS)


def clean_html(html_fragment: str) -> str:
    t = unescape(html_fragment)
    t = re.sub(r"<script[^>]*>.*?</script>", " ", t, flags=re.DOTALL | re.IGNORECASE)
    t = re.sub(r"<style[^>]*>.*?</style>",   " ", t, flags=re.DOTALL | re.IGNORECASE)
    t = re.sub(r"<br\s*/?>",     "\n",  t, flags=re.IGNORECASE)
    t = re.sub(r"</?p[^>]*>",   "\n",  t, flags=re.IGNORECASE)
    t = re.sub(r"</?div[^>]*>", "\n",  t, flags=re.IGNORECASE)
    t = re.sub(r"</?li[^>]*>",  "\n• ",t, flags=re.IGNORECASE)
    t = re.sub(r"<[^>]+>", "", t)
    lines = []
    for line in t.split("\n"):
        s = re.sub(r"[ \t]+", " ", line).strip()
        if s and not is_noise(s):
            lines.append(s)
    return "\n".join(lines)


# ─── FETCH WEB ───────────────────────────────────────────────────────────────

def fetch_web(url: str) -> dict:
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    html = r.text

    out = dict(title="", published="", meta_desc="", web_text="", pdf_url="")

    m = re.search(r'<h1[^>]*class="detail__title"[^>]*>(.*?)</h1>', html, re.DOTALL)
    if m: out["title"] = clean_html(m.group(1)).strip()

    m = re.search(r'<div[^>]*class="detail__meta"[^>]*>(.*?)</div>', html, re.DOTALL)
    if m: out["published"] = clean_html(m.group(1)).strip()

    m = re.search(r'name="description"\s+content="([^"]+)"', html)
    if m: out["meta_desc"] = unescape(m.group(1)).strip()

    si = html.find('id="abody"')
    if si > -1:
        si = html.find(">", si) + 1
        ei = len(html)
        for em in ['class="content-bottom"', 'class="detail__footer"', 'class="sub-col"']:
            p = html.find(em, si)
            if 0 < p < ei: ei = p
        content_html = html[si:ei]
        pm = re.search(r'href="(/upload/[^"]+\.pdf)"', content_html)
        if pm: out["pdf_url"] = "https://vira.org.vn" + pm.group(1)
        out["web_text"] = clean_html(content_html)

    return out


# ─── FETCH & EXTRACT PDF ─────────────────────────────────────────────────────

def fetch_pdf_text(pdf_url: str, save_path: Path) -> str:
    """Tải PDF và extract text bằng pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        print("  ⚠️  pdfplumber chưa cài. Chạy: pip install pdfplumber")
        return ""

    print(f"  📥 Tải PDF: {pdf_url.split('/')[-1]}")
    r = requests.get(pdf_url, headers=HEADERS, timeout=30, stream=True)
    r.raise_for_status()

    # Lưu PDF
    save_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_bytes = r.content
    save_path.write_bytes(pdf_bytes)
    print(f"  💾 PDF lưu: {save_path} ({len(pdf_bytes)//1024} KB)")

    # Extract text from PDF is removed because MSB Research PDFs contain
    # 2-column layouts and charts that get parsed as garbled text (e.g. "V N D 2 9 , 0 0 0").
    # The web text already contains the full newsletter content.
    return ""


# ─── FORMAT OUTPUT ────────────────────────────────────────────────────────────

def format_complete_txt(date_obj: datetime, web: dict, pdf_text: str, url: str) -> str:
    date_vn  = date_obj.strftime("%d/%m/%Y")
    day_name = ["Thứ Hai","Thứ Ba","Thứ Tư","Thứ Năm","Thứ Sáu","Thứ Bảy","Chủ Nhật"][date_obj.weekday()]
    now      = datetime.now().strftime("%H:%M %d/%m/%Y")
    S70 = "=" * 70
    D70 = "-" * 70

    lines = [
        S70,
        f"BẢN TIN KINH TẾ - TÀI CHÍNH NGÀY {date_vn} ({day_name})",
        S70,
        f"Nguồn    : VIRA × MSB Research — vira.org.vn",
        f"URL web  : {url}",
        f"PDF      : {web['pdf_url'] or 'N/A'}",
        f"Đăng     : {web['published']}",
        f"Lưu lúc  : {now}",
        S70,
        "",
    ]

    # Sapo
    if web["meta_desc"]:
        lines += ["[ TÓM TẮT ]", web["meta_desc"], "", D70, ""]

    # Nội dung web (súc tích)
    if web["web_text"]:
        lines += [
            "🌐 NỘI DUNG TÓM TẮT (WEB)",
            D70,
            "",
        ]
        # Tách và format theo section
        text = web["web_text"]

        # Loại dòng cuối noise
        text = re.sub(r"\nBản tin Kinh tế - Tài chính ngày \d{2}/\d{2}/\d{4}\s*$", "", text).strip()

        text = re.sub(r"(Tin trong nước\s*:?)",   "🇻🇳 TIN TRONG NƯỚC\n" + D70, text)
        text = re.sub(r"(Tin quốc tế\s*:?)",      "\n🌍 TIN QUỐC TẾ\n" + D70, text)
        
        # Parse numerical data into Markdown tables for specific sections
        sections = re.split(r"(Thị trường [^\n:]+:|Nghiệp vụ [^\n:]+:|Ngày \d{2}/\d{2}/\d{4}, Chính Phủ)", text)
        processed_parts = []
        for i in range(0, len(sections)):
            part = sections[i].strip()
            if not part: continue
            
            if re.match(r"(Thị trường [^\n:]+:|Nghiệp vụ [^\n:]+:)", part):
                # Clean up the header, remove the trailing colon
                header_text = part.rstrip(':').strip()
                processed_parts.append(f"\n\n### {header_text}\n")
            elif re.match(r"Ngày \d{2}/\d{2}/\d{4}, Chính Phủ", part):
                processed_parts.append(f"\n\n### Chính sách\n{part} ")
            else:
                processed_parts.append(extract_tables_from_text(part) + "\n")
                
        text = "".join(processed_parts).strip()
        lines += [text, "", D70, ""]

    # N/A: PDF raw text is no longer inserted to avoid garbled charts.
    if web["pdf_url"]:
        lines += [
            f"📎 File PDF Gốc: {web['pdf_url']}",
            f"   (Tải thủ công để xem bảng biểu và biểu đồ)",
            "",
            D70,
        ]
        lines += [
            f"📎 File PDF: {web['pdf_url']}",
            f"   (Tải thủ công để xem nội dung đầy đủ)",
            "",
        ]

    lines += ["", S70, f"Hết bản tin | {now}", S70]
    return "\n".join(lines)


def format_complete_md(date_obj: datetime, web: dict, pdf_text: str, url: str) -> str:
    date_str = date_obj.strftime("%Y-%m-%d")
    date_vn  = date_obj.strftime("%d/%m/%Y")
    day_name = ["Thứ Hai","Thứ Ba","Thứ Tư","Thứ Năm","Thứ Sáu","Thứ Bảy","Chủ Nhật"][date_obj.weekday()]
    now      = datetime.now().strftime("%H:%M %d/%m/%Y")

    pdf_name = web["pdf_url"].split("/")[-1] if web["pdf_url"] else ""

    lines = [
        f"---",
        f"date: {date_str}",
        f"source: vira.org.vn × MSB Research",
        f"published: {web['published']}",
        f"url: {url}",
        f"pdf: {web['pdf_url']}",
        f"---",
        f"",
        f"# 📊 Bản tin Kinh tế - Tài chính | {day_name} {date_vn}",
        f"",
        f"> **Nguồn**: [VIRA]({url}) × MSB Research",
        f"> **Đăng**: {web['published']} &nbsp;|&nbsp; **Lưu**: {now}",
        f"",
    ]

    if web["meta_desc"]:
        lines += [f"> 💡 **{web['meta_desc']}**", ""]

    lines += ["---", ""]

    # Web content section
    if web["web_text"]:
        text = web["web_text"]
        text = re.sub(r"\nBản tin Kinh tế - Tài chính ngày \d{2}/\d{2}/\d{4}\s*$", "", text).strip()

        # Tách tin trong nước / quốc tế
        m_intl = re.search(r"Tin quốc tế\s*:?\n", text)
        m_dom  = re.search(r"Tin trong nước\s*:?\n", text)

        dom_text  = text[m_dom.end():m_intl.start()].strip() if (m_dom and m_intl) else text
        intl_text = text[m_intl.end():].strip() if m_intl else ""

        lines += ["## 🇻🇳 Tin trong nước", ""]

        # Tách từng tiểu mục
        section_splits = re.split(r"(\n(?:Thị trường [^\n]+:|Nghiệp vụ [^\n]+:|Ngày \d{2}/\d{2}/\d{4}))", dom_text)
        if len(section_splits) > 1:
            i = 0
            while i < len(section_splits):
                part = section_splits[i].strip()
                if part and part.endswith(":"):
                    # This is a header + next is content
                    header = part
                    content = extract_tables_from_text(section_splits[i+1].strip()) if i+1 < len(section_splits) else ""
                    # Pick icon
                    icon = "💱" if "ngoại tệ" in header.lower() else \
                           "🏦" if "tiền tệ" in header.lower() else \
                           "⚙️" if "thị trường mở" in header.lower() else \
                           "📈" if "chứng khoán" in header.lower() else \
                           "🏛️" if "chính sách" in header.lower() else "▶"
                    lines += [f"### {icon} {header}", "", content, ""]
                    i += 2
                else:
                    if part:
                        lines += [part, ""]
                    i += 1
        else:
            # Format đơn giản
            dom_fmt = re.sub(r"(Thị trường [^\n:]+:|Nghiệp vụ [^\n:]+:)", r"\n**\1**", dom_text)
            lines += [dom_fmt, ""]

        if intl_text:
            lines += ["## 🌍 Tin quốc tế", "", intl_text, ""]

        lines += ["---", ""]

    # PDF section
    if web["pdf_url"]:
        lines += [
            f"## 📎 Tải PDF đầy đủ",
            f"",
            f"[{pdf_name}]({web['pdf_url']}) (Xem bảng biểu và biểu đồ)",
            f"",
            f"---",
            f"",
        ]

    lines += [f"*Thu thập bởi `collect_vira_pdf.py` | {now}*"]
    return "\n".join(lines)


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Thu thập bản tin VIRA + PDF MSB Research")
    parser.add_argument("--date",     default=None, help="YYYY-MM-DD. Mặc định: hôm nay")
    parser.add_argument("--open",     action="store_true")
    parser.add_argument("--no-pdf",   action="store_true", help="Bỏ qua tải PDF")
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
    print(f"  📡 BẢN TIN VIRA + PDF MSB RESEARCH — {date_vn}")
    print(f"{'='*60}\n")

    # 1. Fetch web
    print(f"  🌐 Tải trang web...")
    try:
        web = fetch_web(url)
    except requests.exceptions.HTTPError as e:
        print(f"  ❌ HTTP error — có thể chưa có bản tin ngày {date_vn}")
        sys.exit(1)

    print(f"     → Web: {len(web['web_text'])} ký tự | PDF URL: {'Có' if web['pdf_url'] else 'Không'}")

    # 2. Fetch PDF
    pdf_text = ""
    raw_dir  = OUTPUT_DIR / date_str
    raw_dir.mkdir(parents=True, exist_ok=True)

    if web["pdf_url"] and not args.no_pdf:
        pdf_filename = web["pdf_url"].split("/")[-1]
        pdf_save     = raw_dir / pdf_filename
        try:
            pdf_text = fetch_pdf_text(web["pdf_url"], pdf_save)
            print(f"     → PDF: {len(pdf_text)} ký tự từ file")
        except Exception as e:
            print(f"  ⚠️  Lỗi tải/đọc PDF: {e}")
    elif args.no_pdf:
        print(f"  ⏭️  Bỏ qua PDF (--no-pdf)")
    else:
        print(f"  ℹ️  Không tìm thấy URL PDF trên trang web")

    # 3. Format & save
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    txt = format_complete_txt(target, web, pdf_text, url)
    md  = format_complete_md(target, web, pdf_text, url)

    txt_path = REPORT_DIR / f"{date_str}_vira-ban-tin.txt"
    md_path  = REPORT_DIR / f"{date_str}_vira-ban-tin.md"

    txt_path.write_text(txt, encoding="utf-8")
    md_path.write_text(md,  encoding="utf-8")

    print(f"\n  ✅ TXT hoàn chỉnh : {txt_path}")
    print(f"  ✅ MD  hoàn chỉnh : {md_path}")
    print(f"\n{'─'*60}")
    print(f"  Web    : {len(web['web_text'])} ký tự")
    print(f"  PDF    : {len(pdf_text)} ký tự")
    print(f"  Tổng   : {len(web['web_text']) + len(pdf_text)} ký tự")
    print(f"{'='*60}\n")

    if args.open:
        os.startfile(str(txt_path))


if __name__ == "__main__":
    main()
