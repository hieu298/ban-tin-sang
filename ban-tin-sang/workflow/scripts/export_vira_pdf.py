# -*- coding: utf-8 -*-
"""
export_vira_pdf.py
==================
Tạo file PDF đẹp từ bản tin VIRA đã thu thập.
Hỗ trợ tiếng Việt đầy đủ bằng font DejaVu.

Cách dùng:
  python export_vira_pdf.py                    # Hôm nay
  python export_vira_pdf.py --date 2026-07-01  # Ngày cụ thể
  python export_vira_pdf.py --date 2026-07-01 --open
"""

import io, sys, os, re, argparse
from datetime import datetime, timedelta
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Dùng fpdf2 (ưu tiên) hoặc fpdf
try:
    import warnings
    warnings.filterwarnings("ignore")
    from fpdf import FPDF
except ImportError:
    print("❌ Thiếu fpdf2: pip install fpdf2")
    sys.exit(1)

SCRIPT_DIR  = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
REPORT_DIR  = PROJECT_DIR / "output" / "drafts"
OUTPUT_PDF  = PROJECT_DIR / "output" / "published"

# Font hỗ trợ tiếng Việt — dùng font hệ thống Windows
FONT_PATHS = [
    r"C:\Windows\Fonts\Arial.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\calibri.ttf",
    r"C:\Windows\Fonts\times.ttf",
]
FONT_BOLD_PATHS = [
    r"C:\Windows\Fonts\Arialbd.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\calibrib.ttf",
    r"C:\Windows\Fonts\timesbd.ttf",
]

def find_font(paths):
    for p in paths:
        if Path(p).exists():
            return p
    return None


# ── Palette VCSC-style: Deep Green + Cream ──────────────────────────
C_GREEN      = (0, 95, 70)      # Primary deep green
C_GREEN_DARK = (0, 65, 48)      # Darker green for cover
C_CREAM      = (240, 230, 190)  # Accent cream/gold
C_CREAM_LIGHT= (252, 248, 236)  # Very light cream bg
C_SECTION_BG = (232, 244, 238)  # Light green tint bg
C_BODY       = (30, 35, 35)     # Near-black body text
C_MUTED      = (110, 115, 115)  # Gray muted text
C_DIVIDER    = (190, 210, 200)  # Soft green-gray divider
C_WHITE      = (255, 255, 255)
# ────────────────────────────────────────────────────────────────────


def strip_emoji(text: str) -> str:
    """Loại bỏ emoji và ký tự đặc biệt ngoài phạm vi font hỗ trợ."""
    return re.sub(
        r"[^\x00-\x7F\u00C0-\u024F\u1E00-\u1EFF\u2000-\u206F\u2100-\u214F\u2200-\u22FF\s0-9.,;:!?()\-/\"'%+*#@&=_~^<>\[\]{}|]",
        "",
        text
    ).strip()


class BanTinPDF(FPDF):
    """PDF Bản tin chuyên nghiệp — VCSC-style Deep Green + Cream theme."""

    def __init__(self, font_reg: str, font_bold: str, total_pages: int = 0):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.font_reg    = font_reg
        self.font_bold   = font_bold
        self._hdr_date   = ""       # set từ bên ngoài trước khi add_page
        self._cover_page = True     # trang đầu không có header/footer thường
        self.add_font("VNFont", "",  font_reg,  uni=True)
        self.add_font("VNFont", "B", font_bold, uni=True)
        self.set_auto_page_break(auto=True, margin=22)
        self.set_margins(left=20, top=36, right=20)

    # ── Helpers nội bộ ───────────────────────────────────────────────
    def _set_color(self, rgb, kind="draw"):
        r, g, b = rgb
        if kind == "fill":  self.set_fill_color(r, g, b)
        elif kind == "text": self.set_text_color(r, g, b)
        else:                self.set_draw_color(r, g, b)

    def _accent_stripe(self, x, y, h, w=3, color=C_CREAM):
        """Vẽ dải accent dọc màu cream."""
        self._set_color(color, "fill")
        self.rect(x, y, w, h, style="F")

    def check_space(self, h: float):
        """Kiểm tra không gian còn lại trên trang, nếu không đủ h (mm) thì sang trang mới."""
        # Vùng in được của A4 (cao 297mm) với bottom margin 22mm là đến y = 275mm
        # Chỉ sang trang nếu không phải đang ở đầu trang (tránh tạo trang trắng liên tục)
        if self.get_y() + h > 275 and self.get_y() > self.t_margin + 5:
            self.add_page()

    # ── Header / Footer ─────────────────────────────────────────────
    def header(self):
        if self._cover_page:
            return  # cover page tự vẽ header riêng

        # Dải xanh lá đầu trang
        self._set_color(C_GREEN, "fill")
        self.rect(0, 0, 210, 12, style="F")

        # Chữ trên dải xanh
        self.set_font("VNFont", "B", 8)
        self._set_color(C_WHITE, "text")
        self.set_xy(20, 3)
        self.cell(100, 6, "MARKET RESEARCH | MACROECONOMICS", align="L")
        self.set_xy(110, 3)
        self.cell(80, 6, self._hdr_date, align="R")

        # Đường cream mỏng dưới dải
        self._set_color(C_CREAM, "draw")
        self.set_line_width(0.5)
        self.line(0, 12, 210, 12)
        self.set_line_width(0.2)
        self._set_color(C_BODY, "text")

        # Quan trọng: reset cursor về đầu vùng nội dung (dưới header bar)
        # fpdf2 KHÔNG tự reset sau header() — phải set thủ công
        self.set_xy(20, self.t_margin)


    def footer(self):
        if self._cover_page:
            return

        # Đường cream trên footer
        self._set_color(C_CREAM, "draw")
        self.set_line_width(0.5)
        self.line(20, 284, 190, 284)
        self.set_line_width(0.2)

        self.set_y(-14)
        self.set_font("VNFont", "", 7)
        self._set_color(C_MUTED, "text")
        self.cell(60, 6, "Lưu hành nội bộ", align="L")
        self.cell(60, 6, f"Trang {self.page_no() - 1}", align="C")
        self.cell(60, 6, "Nguồn: VIRA / MSB Research", align="R")
        self._set_color(C_BODY, "text")

    # ── Cover page ──────────────────────────────────────────────────
    def cover_page(self, date_vn: str, day_name: str, published: str, summary: str = ""):
        """Trang bìa chuyên nghiệp kiểu VCSC."""
        self._cover_page = True
        self.set_auto_page_break(auto=False)  # Tắt auto-break trong cover page
        self.add_page()

        # ── Banner xanh đậm phía trên ──
        self._set_color(C_GREEN_DARK, "fill")
        self.rect(0, 0, 210, 72, style="F")

        # Dải cream ngang giữa banner
        self._set_color(C_CREAM, "fill")
        self.rect(0, 68, 210, 2.5, style="F")

        # Tiêu đề báo cáo (trắng)
        self.set_font("VNFont", "B", 22)
        self._set_color(C_WHITE, "text")
        self.set_xy(20, 18)
        self.cell(170, 10, "BAN TIN KINH TE - TAI CHINH", align="L")

        self.set_font("VNFont", "B", 13)
        self._set_color(C_CREAM, "text")
        self.set_xy(20, 32)
        self.cell(170, 8, f"{day_name.upper()}  |  {date_vn}", align="L")

        self.set_font("VNFont", "", 9)
        self._set_color((200, 230, 215), "text")
        self.set_xy(20, 44)
        self.cell(170, 6, "Phan tich Kinh te Vi mo & Thi truong Tai chinh", align="L")

        self.set_font("VNFont", "", 8)
        self._set_color((180, 215, 200), "text")
        self.set_xy(20, 52)
        self.cell(170, 6, f"Xuat ban: {published or date_vn}", align="L")

        # ── Phần thân bên dưới banner ──
        self._set_color(C_BODY, "text")

        # Nguồn dữ liệu
        self.set_xy(20, 80)
        self.set_font("VNFont", "B", 9)
        self._set_color(C_GREEN, "text")
        self.cell(170, 6, "NGUON DU LIEU", align="L")
        self._set_color(C_DIVIDER, "draw")
        self.set_line_width(0.4)
        self.line(20, 87, 190, 87)
        self.set_line_width(0.2)

        sources = [
            ("VIRA",      "Ban tin Kinh te - Tai chinh (vira.org.vn)"),
            ("MSB Research", "Bao cao phan tich hang ngay (PDF)"),
            ("HOSE",      "Cong bo thong tin Doanh nghiep & CTCK"),
            ("Vietstock", "Goc nhin Chuyen gia & RSS tin tuc"),
            ("MAS/Mastrade", "Du lieu thi truong real-time (VN-Index, Nganh)"),
        ]
        self.set_xy(20, 90)
        for src_name, src_desc in sources:
            self.set_font("VNFont", "B", 8.5)
            self._set_color(C_GREEN, "text")
            self.cell(38, 6, src_name, align="L")
            self.set_font("VNFont", "", 8.5)
            self._set_color(C_BODY, "text")
            self.cell(140, 6, src_desc, align="L", ln=1)

        # Tóm tắt nếu có
        if summary:
            y = self.get_y() + 8
            self.set_xy(20, y)
            self.set_font("VNFont", "B", 9)
            self._set_color(C_GREEN, "text")
            self.cell(170, 6, "TOM TAT BAN TIN", ln=1)
            self._set_color(C_DIVIDER, "draw")
            self.set_line_width(0.4)
            self.line(20, self.get_y(), 190, self.get_y())
            self.set_line_width(0.2)
            self.ln(3)

            # Callout box tóm tắt
            self.callout_box(summary)

        # Footer cover
        self._set_color(C_GREEN, "fill")
        self.rect(0, 282, 210, 15, style="F")
        self._set_color(C_CREAM, "fill")
        self.rect(0, 282, 210, 1.2, style="F")
        self.set_xy(20, 285)
        self.set_font("VNFont", "", 7.5)
        self._set_color(C_WHITE, "text")
        self.cell(170, 5, "Tong hop: VIRA  |  MSB Research  |  Vietstock  |  HOSE", align="C")
        self._set_color(C_BODY, "text")

        # Tái bật auto-break và tắt cover mode khi sang trang nội dung
        self._cover_page = False
        self.set_auto_page_break(auto=True, margin=22)

    # ── Sections ────────────────────────────────────────────────────
    def section_header(self, text: str, color: tuple = None):
        """Section header xanh lá đậm, accent stripe cream bên trái."""
        # Yêu cầu ít nhất 50mm không gian cho Section Header + Nội dung đi kèm
        self.check_space(50)
            
        text = strip_emoji(re.sub(r"[^\x00-\x7F\u00C0-\u024F\u1E00-\u1EFF\s0-9/()&,.-]", "", text).strip())
        h = 8
        y0 = self.get_y()

        # Nền xanh lá full width
        self._set_color(C_GREEN, "fill")
        self.rect(20, y0, 170, h, style="F")

        # Dải cream trái 3mm
        self._set_color(C_CREAM, "fill")
        self.rect(20, y0, 3, h, style="F")

        # Text trắng
        self.set_font("VNFont", "B", 10)
        self._set_color(C_WHITE, "text")
        self.set_xy(25, y0 + 0.8)
        self.cell(163, h - 1.6, text.upper(), align="L")
        self._set_color(C_BODY, "text")
        self.ln(h + 3)

    def subsection_header(self, text: str):
        """Tiêu đề tiểu mục — xanh lá đậm, gạch dưới cream."""
        # Yêu cầu ít nhất 40mm không gian cho Subsection + Nội dung
        self.check_space(40)
            
        text = strip_emoji(re.sub(r"[^\x00-\x7F\u00C0-\u024F\u1E00-\u1EFF\s0-9/()&,.-]", "", text).strip())
        self.set_font("VNFont", "B", 10)
        self._set_color(C_GREEN, "text")
        self.cell(0, 6, text, ln=1)
        # Gạch dưới cream
        y = self.get_y()
        self._set_color(C_CREAM, "draw")
        self.set_line_width(0.8)
        self.line(20, y, 80, y)
        self.set_line_width(0.2)
        self._set_color(C_BODY, "text")
        self.ln(2)

    def callout_box(self, text: str):
        """Hộp highlight — viền trái cream 3pt, nền cream nhạt."""
        text = strip_emoji(re.sub(r"[^\x00-\x7F\u00C0-\u024F\u1E00-\u1EFF\s.,;:!?()\-/\"'0-9%&]", "", text).strip())
        if not text:
            return
        x0   = 20
        w    = 170
        pad  = 4

        # Đo chiều cao text trước
        self.set_font("VNFont", "", 9)
        # ước lượng số dòng
        lines_est = max(1, len(text) // 90 + text.count('\n') + 1)
        h_est = lines_est * 5.5 + pad * 2

        y0 = self.get_y()

        # Đảm bảo có đủ chỗ cho hộp highlight
        self.check_space(h_est + 5)
        y0 = self.get_y()

        # Nền cream nhạt
        self._set_color(C_CREAM_LIGHT, "fill")
        self.rect(x0, y0, w, h_est, style="F")

        # Dải cream đậm trái
        self._set_color(C_CREAM, "fill")
        self.rect(x0, y0, 3.5, h_est, style="F")

        # Text
        self._set_color(C_BODY, "text")
        self.set_xy(x0 + pad + 1.5, y0 + pad)
        self.multi_cell(w - pad * 2 - 1.5, 5.5, text, align="L")
        self.ln(pad + 1)

    def chart_caption(self, caption: str):
        """Caption nhỏ bên dưới biểu đồ."""
        self.set_font("VNFont", "", 7.5)
        self._set_color(C_MUTED, "text")
        self.cell(0, 5, strip_emoji(caption), align="C", ln=1)
        self._set_color(C_BODY, "text")
        self.ln(1)

    def body_text(self, text: str, indent: int = 8):
        """Đoạn văn bản thường (hỗ trợ bảng markdown)."""
        self.set_left_margin(20 + indent)
        self.set_right_margin(20)

        lines = text.split('\n')
        in_table = False
        col_widths = []

        for line in lines:
            line = line.strip()
            if not line:
                self.ln(2)
                continue

            if line.startswith('|') and line.endswith('|'):
                cells = [c.strip() for c in line.strip('|').split('|')]
                if all(re.match(r'^-+$', c) for c in cells):
                    continue
                if not in_table:
                    in_table = True
                    num_cols  = len(cells)
                    w_first   = 52
                    w_others  = (170 - w_first - indent) / max(1, num_cols - 1)
                    col_widths = [w_first] + [w_others] * (num_cols - 1)
                    self.set_font("VNFont", "B", 8)
                    self._set_color(C_SECTION_BG, "fill")
                    self._set_color(C_DIVIDER, "draw")
                    for i, cell in enumerate(cells):
                        self.cell(col_widths[i], 6, cell, border="TB", fill=True,
                                  align="L" if i == 0 else "R")
                    self.ln()
                else:
                    self.set_font("VNFont", "", 8)
                    self._set_color(C_WHITE, "fill")
                    for i, cell in enumerate(cells):
                        w = col_widths[i] if i < len(col_widths) else 30
                        self.cell(w, 6, cell.replace('**', ''), border="B",
                                  align="L" if i == 0 else "R")
                    self.ln()
            else:
                if in_table:
                    in_table = False
                    self._set_color(C_BODY, "draw")
                    self.ln(2)

                # Markdown heading ### -> subsection header
                if line.startswith('###'):
                    heading = strip_emoji(line.lstrip('#').strip())
                    if heading:
                        self.set_left_margin(20)
                        self.subsection_header(heading)
                        self.set_left_margin(20 + indent)
                    continue

                if line.startswith('**') and line.endswith('**'):
                    self.check_space(30) # Tăng lên 30mm để đảm bảo chứa đủ vài dòng sau tiêu đề
                    self.ln(1)
                    self.set_font("VNFont", "B", 9)
                    self._set_color(C_GREEN, "text")
                    self.cell(0, 5.5, strip_emoji(line.replace('**', '')), ln=1)
                    self._set_color(C_BODY, "text")
                    continue

                # Strip markdown links [text](url) → chỉ hiển text
                clean = strip_emoji(re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', line.replace('**', '')))
                # Đoán chiều cao của đoạn văn (ước tính 95 ký tự / dòng)
                lines_est = max(1, len(clean) // 95 + clean.count('\n'))
                self.check_space(lines_est * 5.8 + 2)

                self.set_font("VNFont", "", 9)
                self._set_color(C_BODY, "text")
                if clean.startswith(("•", "-", "▪")):
                    self.multi_cell(0, 5.8, clean, align="L")
                else:
                    self.multi_cell(0, 5.8, clean, align="J")
                self.ln(0.8)

        self.set_left_margin(20)
        self._set_color(C_BODY, "text")
        self.ln(1.5)

    def divider(self):
        self._set_color(C_DIVIDER, "draw")
        self.set_line_width(0.3)
        self.line(20, self.get_y(), 190, self.get_y())
        self.set_line_width(0.2)
        self.ln(4)


def parse_txt_file(txt_path: Path) -> dict:
    """Đọc file txt đã tạo và tách thành các section."""
    content = txt_path.read_text(encoding="utf-8")

    result = {
        "meta_desc":  "",
        "published":  "",
        "web_dom":    "",
        "web_intl":   "",
        "pdf_pages":  [],
    }

    # Meta desc (TÓM TẮT)
    m = re.search(r"\[ TÓM TẮT \]\n(.+?)(?=\n-{10})", content, re.DOTALL)
    if m:
        result["meta_desc"] = m.group(1).strip()

    # Published
    m = re.search(r"Đăng\s+:\s+(.+)", content)
    if m:
        result["published"] = m.group(1).strip()

    # Web nội dung — từ "TIN TRONG NƯỚC" đến "TIN QUỐC TẾ"
    m_dom  = re.search(r"🇻🇳 TIN TRONG NƯỚC\n-+\n(.*?)(?=🌍 TIN QUỐC TẾ|\n-{10}\n\n📋)", content, re.DOTALL)
    m_intl = re.search(r"🌍 TIN QUỐC TẾ\n-+\n(.*?)(?=\n-{10}\n\n📋|$)", content, re.DOTALL)

    if m_dom:  result["web_dom"]  = m_dom.group(1).strip()
    if m_intl: result["web_intl"] = m_intl.group(1).strip()

    # PDF pages
    pages = re.findall(r"\[Trang \d+/\d+\]\n(.*?)(?=\[Trang \d+|\Z)", content, re.DOTALL)
    result["pdf_pages"] = [p.strip() for p in pages if p.strip()]

    # Vietstock RSS Parsing
    result["vietstock_news"] = {}
    try:
        vs_file = txt_path.parent / f"{txt_path.stem[:10]}_vietstock.md"
        if vs_file.exists():
            vs_content = vs_file.read_text(encoding="utf-8")
            # Parse sections: ## Header \n items \n ---
            sections = re.findall(r"## (.*?)\n(.*?)(?=\n---|##|$)", vs_content, re.DOTALL)
            for sec_title, sec_content in sections:
                lines = [line.strip() for line in sec_content.split("\n") if line.strip().startswith("•")]
                if lines:
                    result["vietstock_news"][sec_title.strip()] = lines
    except Exception as e:
        print(f"Lỗi khi đọc tin Vietstock: {e}")

    # HSX News Parsing
    result["hsx_news"] = []
    # Try to find HSX file (either for today or the previous business day)
    try:
        dt = datetime.strptime(txt_path.stem[:10], "%Y-%m-%d")
        prev_dt = dt - timedelta(days=1)
        if dt.weekday() == 0: # Monday
            prev_dt = dt - timedelta(days=3)
            
        # Ưu tiên lấy file của ngày hiện tại (dt) trước, nếu không có mới lấy ngày hôm trước
        date_candidates = [dt.strftime("%Y-%m-%d"), prev_dt.strftime("%Y-%m-%d")]
        
        for d in date_candidates:
            hsx_file = txt_path.parent / f"{d}_hsx-news.md"
            if hsx_file.exists():
                hsx_content = hsx_file.read_text(encoding="utf-8")
                
                # Lấy tất cả các section (trừ Tổng Quan)
                sections = re.findall(r"##\s+(.*?)\n+(.*?)(?=\n##\s+|$)", hsx_content, re.DOTALL)
                for sec_name, sec_content in sections:
                    if "Tổng Quan" in sec_name: continue
                    # Extract rows: | Giờ | Mã | [Tiêu đề](link) |
                    rows = re.findall(r"\|\s*([\d:]+)\s*\|\s*([^|]+?)\s*\|\s*\[([^\]]+)\]\(([^)]+)\)", sec_content)
                    if rows:
                        result["hsx_news"].append(f"**{sec_name.strip()}**")
                        for time_str, ticker, title, url in rows:
                            ticker = ticker.replace("`", "").strip()
                            ticker_str = f" [{ticker}]" if ticker and ticker != "—" else ""
                            result["hsx_news"].append(f"• {time_str}{ticker_str}: [{title}]({url})")
                
                if result["hsx_news"]:
                    break # Nếu đã tìm thấy tin, ngừng tìm ngày cũ
    except Exception as e:
        print(f"Lỗi khi đọc tin HSX: {e}")

    return result


def build_pdf(date_obj: datetime, txt_path: Path, out_path: Path):
    font_reg  = find_font(FONT_PATHS)
    font_bold = find_font(FONT_BOLD_PATHS)

    if not font_reg or not font_bold:
        print("  ❌ Không tìm thấy font hệ thống Windows")
        print("  → Thử dùng font mặc định...")
        # Fallback: dùng font latin mặc định (không có dấu)
        font_reg  = FONT_PATHS[0]
        font_bold = FONT_BOLD_PATHS[0]

    date_vn  = date_obj.strftime("%d/%m/%Y")
    day_name = ["Thứ Hai","Thứ Ba","Thứ Tư","Thứ Năm","Thứ Sáu","Thứ Bảy","Chủ Nhật"][date_obj.weekday()]

    data = parse_txt_file(txt_path)

    pdf = BanTinPDF(font_reg, font_bold)

    # ── Cover Page (trang 1) ──
    pdf._hdr_date = date_vn
    pdf.cover_page(date_vn, day_name, data["published"], summary=data.get("meta_desc", ""))
    # Mở trang nội dung (trang 2)
    pdf.add_page()

    # -- Tin trong nuoc (web) --
    if data["web_dom"]:
        pdf.section_header(f"TIN TRONG NƯỚC ({date_vn})")

        dom = data["web_dom"]
        # Tach tung tieu muc theo the ###
        parts = re.split(r"\n### ([^\n]+)\n", dom)
        if len(parts) > 1:
            # parts[0] la doan text truoc tieu muc dau tien (neu co)
            if parts[0].strip():
                pdf.body_text(parts[0])
            for i in range(1, len(parts), 2):
                header = parts[i].strip()
                content = parts[i+1].strip() if i+1 < len(parts) else ""
                if header:
                    pdf.subsection_header(header)
                if content:
                    pdf.body_text(content)
                
                if "chứng khoán" in header.lower() or "thi truong" in header.lower():
                    charts_dir = txt_path.parent.parent / "charts"

                    def _insert_chart(path, w, caption):
                        if path.exists():
                            # Biểu đồ cần khoảng không gian lớn (ước lượng 90-100mm)
                            pdf.check_space(100)
                            pdf.ln(2)
                            pdf.image(str(path), x="C", w=w)
                            pdf.chart_caption(caption)

                    _insert_chart(charts_dir/"vnindex_intraday.png",    160, "Biểu đồ nhịp đập VN-Index trong phiên")
                    _insert_chart(charts_dir/"market_liquidity.png",    160, "Thanh khoản & Dòng tiền thị trường")
                    _insert_chart(charts_dir/"market_breadth_area.png", 160, "Độ rộng thị trường (Area Chart)")
                    _insert_chart(charts_dir/"market_breadth.png",      150, "Phân loại cổ phiếu: Tăng / Giảm / Không đổi")
                    _insert_chart(charts_dir/"market_contrib.png",      150, "Đóng góp ngành vào VN-Index")
                    _insert_chart(charts_dir/"stock_contrib.png",       150, "Top cổ phiếu đóng góp")
                    _insert_chart(charts_dir/"market_sector_table.png", 180, "Dữ liệu chỉ số ngành")

                    dashboard_path = charts_dir / "sector_intraday.png"
                    if dashboard_path.exists():
                        pdf.check_space(110)
                        pdf.ln(3)
                        pdf.subsection_header("Diễn biến Dòng tiền 10 Nhóm Ngành trong phiên")
                        pdf.image(str(dashboard_path), x="C", w=190)
                        pdf.chart_caption("Nguồn: MAS / Mastrade")

                    _insert_chart(charts_dir/"market_position.png",     170, "Vị thế Chu kỳ thị trường (Oscillator)")
                    _insert_chart(charts_dir/"market_breakout.png",     170, "Top cổ phiếu đột biến khối lượng")
                    _insert_chart(charts_dir/"market_valuation.png",    190, "Định giá thị trường: P/E & P/B")
        else:
            pdf.body_text(dom)

        pdf.divider()

    # -- Dòng tiền tổ chức --
    inst_path = txt_path.parent.parent / "charts" / "institutional_flow.png"
    if inst_path.exists():
        pdf.check_space(110)
        pdf.section_header("DÒNG TIỀN TỔ CHỨC (KHỐI NGOẠI & TỰ DOANH)")
        pdf.ln(2)
        pdf.image(str(inst_path), x="C", w=190)
        pdf.chart_caption("Dòng tiền Khối ngoại & Tự doanh — Nguồn: MAS / Mastrade")
        pdf.divider()

    # -- Tin quoc te (web) --
    if data["web_intl"]:
        pdf.section_header("TIN QUỐC TẾ")

        # Chèn Dashboard Quốc Tế
        global_path = txt_path.parent.parent / "charts" / "global_markets.png"
        if global_path.exists():
            pdf.check_space(110)
            pdf.ln(2)
            pdf.set_font("VNFont", "B", 10)
            pdf.set_text_color(44, 62, 80)
            pdf.cell(0, 6, "Dashboard Thị trường Thế giới & Hàng hóa (3 tháng):", ln=True, align="L")
            pdf.ln(2)
            pdf.image(str(global_path), x="C", w=190)
            pdf.ln(5)

        intl = data["web_intl"]
        intl = re.sub(r"\nBan tin Kinh te.*$", "", intl, flags=re.DOTALL).strip()
        intl = re.sub(r"\n<div.*$", "", intl, flags=re.DOTALL).strip()

        paragraphs = [p.strip() for p in intl.split("\n") if p.strip()]
        for para in paragraphs:
            pdf.body_text(para)

        pdf.divider()

    # -- Tin Vietstock --
    if data.get("vietstock_news"):
        pdf.section_header("GÓC NHÌN & TÂM ĐIỂM ĐẦU TƯ (Vietstock)")
        for sec_title, items in data["vietstock_news"].items():
            # Tính toán linh hoạt chiều cao của cả khối: 
            # 7mm cho tiêu đề + khoảng 8mm cho mỗi gạch đầu dòng + 2mm margin dưới
            req_height = 7 + len(items) * 8 + 2
            pdf.check_space(req_height) 
            
            pdf.set_font("VNFont", "B", 10)
            pdf.set_text_color(40, 40, 40)
            pdf.cell(0, 7, strip_emoji(sec_title), ln=1)
            for item in items:
                pdf.body_text(item, indent=5)
            pdf.ln(2)
        pdf.divider()

    # -- Tin doanh nghiep (HSX) --
    if data.get("hsx_news"):
        pdf.section_header("TIN DOANH NGHIỆP (HOSE)")
        for news_item in data["hsx_news"]:
            pdf.body_text(news_item, indent=0)
        pdf.divider()

    # -- Noi dung PDF day du --
    if data["pdf_pages"]:
        pdf.section_header("NỘI DUNG ĐẦY ĐỦ  (MSB Research)")

        for i, page_text in enumerate(data["pdf_pages"], 1):
            if i > 1:
                pdf.set_font("VNFont", "B", 8)
                pdf.set_text_color(150, 150, 150)
                pdf.cell(0, 5, f"--- Tiếp trang {i} của bản tin gốc ---", align="C", ln=1)
                pdf.set_text_color(0, 0, 0)
                pdf.ln(2)

            lines = page_text.split("\n")
            current_bullet = []
            for line in lines:
                line = line.strip()
                if not line:
                    if current_bullet:
                        pdf.body_text(" ".join(current_bullet))
                        current_bullet = []
                    continue
                if line.startswith("\u25aa") or line.startswith("\u2022"):
                    if current_bullet:
                        pdf.body_text(" ".join(current_bullet))
                    current_bullet = [line]
                elif current_bullet:
                    current_bullet.append(line)
                else:
                    if re.match(r"^(Tin trong n|Tin qu\u1ed1c t|Th\u1ecb tr\u01b0\u1eddng|L\u1ecbch s\u1ef1 ki\u1ec7n|B\u1ea3ng s\u1ed1 li\u1ec7u)", line):
                        pdf.subsection_header(line)
                    else:
                        pdf.body_text(line)

            if current_bullet:
                pdf.body_text(" ".join(current_bullet))

    # Lưu
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out_path))
    print(f"  ✅ PDF: {out_path}")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Tạo PDF bản tin VIRA")
    parser.add_argument("--date",  default=None, help="YYYY-MM-DD. Mặc định: hôm nay")
    parser.add_argument("--open",  action="store_true")
    args = parser.parse_args()

    if args.date:
        try:    target = datetime.strptime(args.date, "%Y-%m-%d")
        except: print(f"❌ Ngày không hợp lệ"); sys.exit(1)
    else:
        target = datetime.now()

    date_str = target.strftime("%Y-%m-%d")
    date_vn  = target.strftime("%d/%m/%Y")

    # Tìm file txt nguồn
    txt_path = REPORT_DIR / f"{date_str}_vira-ban-tin.txt"
    if not txt_path.exists():
        print(f"  ❌ Không tìm thấy: {txt_path}")
        print(f"     Chạy collect_vira_pdf.py trước!")
        sys.exit(1)

    out_path = OUTPUT_PDF / f"{date_str}_vira-ban-tin.pdf"

    print(f"\n{'='*60}")
    print(f"  📄 TẠO PDF BẢN TIN VIRA — {date_vn}")
    print(f"{'='*60}\n")

    build_pdf(target, txt_path, out_path)

    size_kb = out_path.stat().st_size // 1024
    print(f"  📦 Kích thước: {size_kb} KB")
    print(f"  📁 Lưu tại  : {out_path}\n")

    if args.open:
        os.startfile(str(out_path))


if __name__ == "__main__":
    main()
