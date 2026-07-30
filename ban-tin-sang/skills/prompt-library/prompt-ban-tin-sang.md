# 🧠 THƯ VIỆN PROMPT — BẢN TIN SÁNG

> Đây là tập hợp prompt đã được test và hoạt động tốt.
> Gọi từng prompt theo thứ tự trong workflow.

---

## PROMPT 01 — Thu thập & Phân loại Tin

```
Bạn là biên tập viên bản tin tài chính chứng khoán Việt Nam.

Dưới đây là danh sách tin tức thô thu thập được:
[DÁN TIN THÔ VÀO ĐÂY]

Hãy:
1. Phân loại mỗi tin vào 1 trong 4 nhóm: [THỊ_TRƯỜNG] [VĨ_MÔ] [DOANH_NGHIỆP] [QUỐC_TẾ]
2. Đánh độ ưu tiên: [PHẢI CÓ] [NÊN CÓ] [TÙY CHỌN]
3. Loại bỏ tin trùng lặp, giữ nguồn uy tín nhất
4. Trả về danh sách đã phân loại, sắp xếp theo độ ưu tiên

Output format:
[NHÓM] [ƯU_TIÊN] Tiêu đề tin — Nguồn — Điểm nổi bật (1 câu)
```

---

## PROMPT 02 — Lấy dữ liệu thị trường

```
Dựa trên dữ liệu thị trường sau đây:
[DÁN DATA SNAPSHOT]

Hãy điền vào bảng sau:
- Chỉ số: VNINDEX, VN30, HNX, UPCOM (đóng cửa, %, điểm thay đổi)
- Thanh khoản HOSE so với TB 20 phiên
- Top 3 ngành tăng / giảm mạnh nhất
- Dòng tiền ngoại: tổng, top mua, top bán

Chỉ trả về dữ liệu, không giải thích thêm.
```

---

## PROMPT 03 — Viết bản thảo bản tin

```
Bạn là chuyên viên phân tích thị trường chứng khoán Việt Nam, viết bản tin sáng hàng ngày.

PHONG CÁCH:
- Chuyên nghiệp, dễ đọc, dữ liệu cụ thể
- Câu ngắn (<30 chữ), mỗi đoạn 1 ý
- Số liệu dẫn dắt, sau đó giải thích nguyên nhân ngắn

DỮ LIỆU THỊ TRƯỜNG:
[DÁN DATA ĐÃ CHUẨN BỊ]

TIN TỨC PHÂN LOẠI:
[DÁN TIN ĐÃ PHÂN LOẠI]

Hãy viết bản tin sáng theo template sau:
[DÁN TEMPLATE]

Chú ý:
- TL;DR phải viết trước, 1-2 câu
- Phần thị trường: dùng bảng, bullet ngắn
- Phần tin: mỗi tin 80-120 chữ, có số liệu
- Góc nhìn ngày: nhận định khách quan, 2-3 câu
```

---

## PROMPT 04 — Review & Cải thiện bản thảo

```
Đây là bản thảo bản tin sáng:
[DÁN DRAFT]

Hãy review theo các tiêu chí:
1. Có đủ số liệu cụ thể không? (không có câu mơ hồ)
2. Câu nào quá dài (>40 chữ)? → Gợi ý cách rút ngắn
3. Có tin nào trùng lặp ý không?
4. Phần TL;DR có nắm bắt đúng trọng tâm không?
5. Góc nhìn ngày có khách quan, có căn cứ không?

Trả về:
- Danh sách vấn đề tìm thấy (nếu có)
- Phiên bản đã chỉnh sửa
```

---

## PROMPT 05 — Tạo tiêu đề hấp dẫn

```
Dựa trên nội dung bản tin sáng:
[TÓM TẮT NỘI DUNG CHÍNH]

Hãy tạo 5 phương án tiêu đề cho bản tin theo format:
[Ngày] | [Cảm xúc thị trường] — [Điểm nổi bật nhất]

Tiêu chí:
- Có con số cụ thể
- Cảm xúc thị trường rõ ràng (tăng/giảm/giằng co/bùng nổ/thận trọng)
- Dưới 15 chữ phần sau dấu gạch
- Không sensational, không clickbait
```

---

## PROMPT 06 — Tóm tắt để chia sẻ Zalo/Telegram

```
Rút gọn bản tin sau thành tin nhắn Zalo/Telegram:
[DÁN BẢN TIN HOÀN CHỈNH]

Yêu cầu:
- Tối đa 300 chữ
- Dùng emoji đầu dòng để dễ đọc trên mobile
- Giữ tất cả số liệu quan trọng
- Kết thúc bằng link đọc full (để placeholder: [LINK])
- Không dùng bảng (không hiện tốt trên Zalo)
```

---

*Cập nhật prompt khi có improvement mới. Ghi rõ version và ngày test.*
