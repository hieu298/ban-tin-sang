# 🌅 WORKFLOW: TẠO BẢN TIN SÁNG TỰ ĐỘNG (MORNING NEWSLETTER)

Tài liệu này ghi lại toàn bộ quy trình, các nguồn dữ liệu (Links) và bộ quy tắc (Rules) để tự động hóa việc tạo Bản tin Sáng hằng ngày cho giao dịch cổ phiếu. 

Khi người dùng yêu cầu: *"Tạo bản tin sáng hôm nay"* hoặc *"Chạy luồng tin sáng"*, AI Assistant cần đọc và thực thi đúng tuần tự dưới đây.

---

## 📂 1. CẤU TRÚC LƯU TRỮ
- **Scripts**: `e:\Vibe trading\ban-tin-sang\workflow\scripts\`
- **Drafts (Dữ liệu thô)**: `e:\Vibe trading\ban-tin-sang\output\drafts\`
- **Published (PDF cuối cùng)**: `e:\Vibe trading\ban-tin-sang\output\published\`

---

## 🔗 2. CÁC NGUỒN DỮ LIỆU SỬ DỤNG
1. **Tin Vĩ mô & Tiền tệ (VIRA / MSB Research)**
   - Link: `https://vira.org.vn/`
   - Nhiệm vụ: Lấy tỷ giá, lãi suất liên ngân hàng, nghiệp vụ thị trường mở và tin vĩ mô.
2. **Tin Doanh nghiệp Niêm yết (HOSE)**
   - Link: `https://www.hsx.vn/`
   - Nhiệm vụ: Lấy thông báo từ sàn (Cổ tức, BCTC, Giao dịch nội bộ...).
3. **Góc nhìn & Nhận định (Vietstock RSS)**
   - Link: `https://vietstock.vn/rss`
   - Nhiệm vụ: Lấy các luồng tin *Nhận định thị trường*, *Cổ tức*, *Chứng khoán thế giới*.
4. **Dữ liệu Thị trường & Biểu đồ (Mastrade, VNDirect, TCBS)**
   - Link: Các API ngầm từ `api-finfo.vndirect.com.vn`, `mastrade.masvn.com`, v.v...
   - Nhiệm vụ: Lấy số liệu Intraday VN-Index, Thanh khoản, Khối Ngoại (Top 10 Mua/Bán Ròng), Tự Doanh, Định giá, và Dashboard Hàng hóa Thế giới.

---

## ⚙️ 3. QUY TRÌNH THỰC THI (PIPELINE)
AI Assistant bắt buộc phải chạy các tập lệnh (scripts) theo đúng thứ tự này khi được yêu cầu. Tham số `--date YYYY-MM-DD` là bắt buộc (Ví dụ: `2026-07-01`).

### Bước 1: Thu thập Tin Vĩ mô (VIRA)
```bash
python -X utf8 "e:\Vibe trading\ban-tin-sang\workflow\scripts\collect_vira_pdf.py" --date YYYY-MM-DD
```
*Kết quả:* Tạo ra file `<date>_vira-ban-tin.txt`

### Bước 2: Thu thập Tin Doanh nghiệp (HOSE)
*Lưu ý: Đối với bản tin sáng, tin doanh nghiệp thường lấy của chiều ngày hôm trước. Nếu tham số `--date` là thứ Ba đến thứ Sáu, hãy lấy ngày (T-1). Nếu là thứ Hai, lấy ngày (T-3 là thứ Sáu tuần trước).*
```bash
python -X utf8 "e:\Vibe trading\ban-tin-sang\workflow\scripts\collect_hsx_news.py" --date YYYY-MM-DD
```
*Kết quả:* Tạo ra file `<date>_hsx-news.md`

### Bước 3: Thu thập Góc nhìn Chuyên gia (Vietstock RSS)
```bash
python -X utf8 "e:\Vibe trading\ban-tin-sang\workflow\scripts\collect_vietstock_rss.py" --date YYYY-MM-DD
```
*Kết quả:* Tạo ra file `<date>_vietstock.md`

### Bước 4: Khởi tạo Biểu đồ Đồ họa (Data Visualization)
```bash
python -X utf8 "e:\Vibe trading\ban-tin-sang\workflow\scripts\draw_charts.py"
```
*Kết quả:* Tạo ra một bộ ảnh PNG độ nét cao (lưu trong `output/charts/`) gồm có:
1. **Intraday & Thanh Khoản:** VN-Index trong ngày, thanh khoản thị trường.
2. **Cấu trúc Dòng tiền:** Độ rộng thị trường, Top cổ phiếu đóng góp, Bảng số liệu Ngành.
3. **Dòng tiền Tổ chức:** Top 10 Khối ngoại Mua/Bán Ròng (VNDirect API) & Xu hướng 10 phiên Tự Doanh (Mastrade API).
4. **Thế giới & Hàng hóa:** Dashboard thị trường toàn cầu (DJI, S&P 500, Vàng, Dầu, BTC, ETH, DXY, US Bond 10Y, DRAM ETF...).

### Bước 5: Tổng hợp và Kết xuất PDF (Bloomberg Style)
```bash
python -X utf8 "e:\Vibe trading\ban-tin-sang\workflow\scripts\export_vira_pdf.py" --date YYYY-MM-DD --open
```
*Kết quả:* Script sẽ tự động đọc 3 file drafts ở trên, định dạng lại thành bảng biểu, gắn hyperlink và kết xuất ra PDF hoàn chỉnh tại thư mục `published/`. Tham số `--open` sẽ tự động mở file cho người dùng xem.

---

## 📜 4. RULES (QUY TẮC DÀNH CHO AI)
1. **Không can thiệp thủ công vào Drafts:** Script `export_vira_pdf.py` đã được lập trình chuẩn xác để parse (cắt chữ) bằng Regex. Không dùng text editor sửa thủ công file TXT trừ phi có lỗi hiển thị.
2. **Kiểm tra File Tồn tại:** Trước khi chạy `export_vira_pdf.py`, phải đảm bảo ít nhất luồng VIRA và Vietstock đã tải thành công. Nếu HOSE thất bại do web sập, script export vẫn tự động bỏ qua phần HOSE mà không gây lỗi.
3. **Format Đầu ra:** PDF sinh ra luôn áp dụng phong cách Minimalist Institutional (Không viền màu mè, dùng kẻ ngang mờ, phông VNFont).
4. **Trigger (Từ khóa kích hoạt):** Khi người dùng nói *"Làm bản tin sáng hôm nay"*, AI tự tính toán ngày hiện tại `YYYY-MM-DD` và chạy 1 mạch từ Bước 1 đến Bước 4. Lỗi ở đâu báo cáo ở đó.
