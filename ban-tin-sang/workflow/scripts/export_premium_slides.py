import os
from fpdf import FPDF

class PremiumSlidePDF(FPDF):
    def __init__(self):
        super().__init__(orientation='L', unit='mm', format='A4')
        self.set_auto_page_break(auto=False)
        
        # Fonts
        self.font_reg = r"C:\Windows\Fonts\arial.ttf"
        self.font_bold = r"C:\Windows\Fonts\arialbd.ttf"
        self.font_italic = r"C:\Windows\Fonts\ariali.ttf"
        
        try:
            self.add_font("VNFont", "", self.font_reg, uni=True)
            self.add_font("VNFont", "B", self.font_bold, uni=True)
            self.add_font("VNFont", "I", self.font_italic, uni=True)
        except:
            pass # Fallback to core fonts if error
            
    def hero_slide(self, title, subtitle):
        self.add_page()
        # Nền tối (Navy)
        self.set_fill_color(15, 23, 42) # #0F172A
        self.rect(0, 0, 297, 210, 'F')
        
        # Tiêu đề
        self.set_y(80)
        self.set_text_color(255, 255, 255)
        self.set_font("VNFont", "B", 48)
        self.cell(0, 20, title, align='C', ln=1)
        
        # Subtitle
        self.set_y(105)
        self.set_text_color(37, 99, 235) # #2563EB Blue
        self.set_font("VNFont", "", 24)
        self.cell(0, 15, subtitle, align='C', ln=1)
        
    def comparison_slide(self, title):
        self.add_page()
        # Nền trắng
        self.set_fill_color(255, 255, 255)
        self.rect(0, 0, 297, 210, 'F')
        
        # Title
        self.set_y(20)
        self.set_text_color(15, 23, 42)
        self.set_font("VNFont", "B", 36)
        self.cell(0, 20, title, align='L', ln=1)
        
        # Đường kẻ
        self.set_draw_color(226, 232, 240)
        self.line(10, 45, 287, 45)
        
        # Cột trái
        self.set_xy(20, 60)
        self.set_text_color(100, 116, 139) # Gray
        self.set_font("VNFont", "B", 24)
        self.cell(120, 15, "CHATBOT", ln=1)
        
        self.set_xy(20, 90)
        self.set_font("VNFont", "", 18)
        self.set_text_color(71, 85, 105)
        self.cell(120, 15, "- Thụ động (Chờ lệnh)", ln=1)
        self.set_x(20)
        self.cell(120, 15, "- Trả lời bằng văn bản", ln=1)
        self.set_x(20)
        self.cell(120, 15, "- Người dùng phải Copy & Paste", ln=1)
        
        # Đường cắt giữa
        self.line(148, 60, 148, 180)
        
        # Cột phải
        self.set_xy(160, 60)
        self.set_text_color(37, 99, 235) # Blue
        self.set_font("VNFont", "B", 24)
        self.cell(120, 15, "AGENT", ln=1)
        
        self.set_xy(160, 90)
        self.set_font("VNFont", "B", 18)
        self.set_text_color(15, 23, 42)
        self.cell(120, 15, "- Tự chủ (Tự lên kế hoạch)", ln=1)
        self.set_x(160)
        self.cell(120, 15, "- Đọc toàn bộ file dự án", ln=1)
        self.set_x(160)
        self.cell(120, 15, "- Tự động viết và sửa code", ln=1)

    def big_number_slide(self, title):
        self.add_page()
        self.set_y(20)
        self.set_text_color(15, 23, 42)
        self.set_font("VNFont", "B", 36)
        self.cell(0, 20, title, align='L', ln=1)
        
        self.set_draw_color(226, 232, 240)
        self.line(10, 45, 287, 45)
        
        # Number 1
        self.set_xy(10, 70)
        self.set_text_color(37, 99, 235)
        self.set_font("VNFont", "B", 60)
        self.cell(90, 30, "100%", align='C', ln=1)
        
        self.set_xy(10, 110)
        self.set_text_color(15, 23, 42)
        self.set_font("VNFont", "", 16)
        self.multi_cell(90, 10, "Khả năng đọc hiểu Context toàn dự án", align='C')
        
        # Number 2
        self.set_xy(105, 70)
        self.set_text_color(37, 99, 235)
        self.set_font("VNFont", "B", 60)
        self.cell(90, 30, "0", align='C', ln=1)
        
        self.set_xy(105, 110)
        self.set_text_color(15, 23, 42)
        self.set_font("VNFont", "", 16)
        self.multi_cell(90, 10, "Tự động tạo và sửa file trực tiếp, không cần thao tác tay", align='C')
        
        # Number 3
        self.set_xy(200, 70)
        self.set_text_color(37, 99, 235)
        self.set_font("VNFont", "B", 60)
        self.cell(90, 30, "24/7", align='C', ln=1)
        
        self.set_xy(200, 110)
        self.set_text_color(15, 23, 42)
        self.set_font("VNFont", "", 16)
        self.multi_cell(90, 10, "Tự chạy Terminal, tự gỡ lỗi độc lập", align='C')

    def image_slide(self, title, img_path, caption1="", caption2=""):
        self.add_page()
        self.set_y(15)
        self.set_text_color(15, 23, 42)
        self.set_font("VNFont", "B", 30)
        self.cell(0, 15, title, align='L', ln=1)
        
        self.set_draw_color(226, 232, 240)
        self.line(10, 35, 287, 35)
        
        if os.path.exists(img_path):
            # Căn giữa ảnh
            self.image(img_path, x=48, y=45, w=200)
            
        # Thêm text chú thích dưới ảnh
        self.set_xy(20, 175)
        self.set_font("VNFont", "B", 16)
        if caption1:
            self.cell(120, 10, caption1, align='C')
        self.set_xy(160, 175)
        if caption2:
            self.cell(120, 10, caption2, align='C')

if __name__ == "__main__":
    pdf = PremiumSlidePDF()
    
    # 1. Hero
    pdf.hero_slide("AGENTIC CODING", "Tương lai của lập trình tự động hóa")
    
    # 2. Compare
    pdf.comparison_slide("Sự Tiến Hóa")
    
    # 3. Big Numbers
    pdf.big_number_slide("3 Nền Tảng Cốt Lõi")
    
    # 4. Hero 2
    pdf.hero_slide("Google Antigravity", "Kỹ sư phần mềm từ Google DeepMind")
    
    # 5. Image Pair Programming
    img_path_pair = r"C:\Users\Lenovo\.gemini\antigravity-ide\brain\5279a4ad-45d6-4cdf-868e-d920f69a8d6a\antigravity_pair_programming_1782922081313.png"
    pdf.image_slide("Pair Programming", img_path_pair, "Con người: Đưa ra quyết định", "AI Agent: Trực tiếp thực thi code")
    
    # 6. Image IDE
    img_path_ide = r"C:\Users\Lenovo\.gemini\antigravity-ide\brain\5279a4ad-45d6-4cdf-868e-d920f69a8d6a\antigravity_ide_layout_1782922290218.png"
    pdf.image_slide("Không Gian Tối Ưu", img_path_ide, "1. Explorer & 2. Artifact Viewer", "3. Editor & 4. Chat Interface")
    
    # 7. Closing
    pdf.hero_slide("Trở Thành Nhà Quản Trị", "Ngừng gõ code. Hãy bắt đầu ra quyết định.")
    
    out_file = r"e:\Vibe trading\ban-tin-sang\output\published\Premium_Agentic_Coding_Slides.pdf"
    pdf.output(out_file)
    print(f"✅ Premium Slide PDF created at: {out_file}")
