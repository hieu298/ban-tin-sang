import re
from fpdf import FPDF
from pathlib import Path

# Đọc file markdown slide
md_path = Path(r"C:\Users\Lenovo\.gemini\antigravity-ide\brain\5279a4ad-45d6-4cdf-868e-d920f69a8d6a\slide_agentic_coding.md")
with open(md_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Tách các slide dựa trên thẻ <!-- slide -->
# Xóa bỏ ```carousel và ``` ở đầu cuối
content = content.replace("````carousel", "").replace("````", "").strip()
raw_slides = content.split("<!-- slide -->")

class SlidePDF(FPDF):
    def __init__(self):
        # Landscape, mm, A4 (297x210mm)
        super().__init__(orientation='L', unit='mm', format='A4')
        
        # Đăng ký font hỗ trợ Tiếng Việt (chúng ta dùng font arial/calibri nếu có, hoặc tải font Roboto)
        # Vì hệ thống Windows có sẵn Arial, ta dùng fpdf mặc định hoặc font core.
        # Lưu ý fpdf mặc định không hỗ trợ tiếng Việt có dấu. Ta dùng font đã thiết lập trong bản tin VIRA.
        
        font_reg = r"C:\Windows\Fonts\arial.ttf"
        font_bold = r"C:\Windows\Fonts\arialbd.ttf"
        
        self.add_font("VNFont", "", font_reg, uni=True)
        self.add_font("VNFont", "B", font_bold, uni=True)
        self.add_font("VNFont", "I", r"C:\Windows\Fonts\ariali.ttf", uni=True)

    def add_slide(self, text):
        self.add_page()
        self.set_auto_page_break(auto=True, margin=15)
        
        lines = text.strip().split('\n')
        
        y_pos = 30
        for line in lines:
            line = line.strip()
            if not line:
                y_pos += 10
                continue
                
            if line.startswith('# '):
                self.set_font("VNFont", "B", 24)
                self.set_text_color(41, 128, 185) # Blue
                self.set_xy(20, y_pos)
                self.multi_cell(0, 10, line[2:].strip(), align='C')
                y_pos += 20
            elif line.startswith('## '):
                self.set_font("VNFont", "B", 18)
                self.set_text_color(44, 62, 80)
                self.set_xy(20, y_pos)
                self.multi_cell(0, 8, line[3:].strip(), align='C')
                y_pos += 15
            elif line.startswith('> [!'):
                self.set_font("VNFont", "B", 14)
                self.set_text_color(192, 57, 43) # Red/Note
                self.set_xy(20, y_pos)
                self.multi_cell(0, 8, line, align='L')
                y_pos += 10
            elif line.startswith('> '):
                self.set_font("VNFont", "I", 14)
                self.set_text_color(52, 73, 94)
                self.set_xy(25, y_pos)
                self.multi_cell(0, 8, line[2:].strip(), align='L')
                y_pos += 10
            elif line.startswith('- '):
                self.set_font("VNFont", "", 14)
                self.set_text_color(0, 0, 0)
                self.set_xy(25, y_pos)
                self.multi_cell(0, 8, "• " + line[2:].strip(), align='L')
                y_pos += max(8, self.get_y() - y_pos) + 2
            elif line.startswith('1. ') or line.startswith('2. ') or line.startswith('3. ') or line.startswith('4. ') or line.startswith('5. '):
                self.set_font("VNFont", "", 14)
                self.set_text_color(0, 0, 0)
                self.set_xy(25, y_pos)
                self.multi_cell(0, 8, line, align='L')
                y_pos += max(8, self.get_y() - y_pos) + 2
            elif line.startswith('![') and '](' in line and line.endswith(')'):
                # Extract image path
                img_path = line.split('](')[1][:-1]
                # Try to add image centered
                try:
                    # We assume image takes up some space, e.g. 150mm width max, centered
                    img_w = 160
                    x_pos = (297 - img_w) / 2
                    self.image(img_path, x=x_pos, y=y_pos, w=img_w)
                    y_pos += 100 # Add space for image
                except Exception as e:
                    print("Error loading image:", e)
            else:
                if line.startswith('**') and line.endswith('**'):
                    self.set_font("VNFont", "B", 14)
                    line = line.replace('**', '')
                else:
                    self.set_font("VNFont", "", 14)
                self.set_text_color(0, 0, 0)
                self.set_xy(20, y_pos)
                self.multi_cell(0, 8, line, align='L')
                y_pos += max(8, self.get_y() - y_pos) + 2

pdf = SlidePDF()
for slide in raw_slides:
    pdf.add_slide(slide)

out_file = r"e:\Vibe trading\ban-tin-sang\output\published\Agentic_Coding_Slides.pdf"
pdf.output(out_file)
print(f"✅ Slide PDF created at: {out_file}")
