# ⚙️ QUY TRÌNH LÀM VIỆC — SOP BẢN TIN SÁNG

## 🕐 Timeline mỗi ngày

```
05:30  [AUTO]  collect_news.py    → sources/raw-feeds/YYYY-MM-DD/
06:00  [AI]    Prompt 01          → Phân loại tin
06:15  [AI]    Prompt 02          → Điền data thị trường
06:30  [AI]    Prompt 03          → Viết bản thảo → output/drafts/
06:45  [AI]    Prompt 04          → Review bản thảo
07:00  [HUMAN] Review tay         → Sửa nếu cần
07:15  [AI]    Prompt 05          → Chọn tiêu đề
07:20  [AI]    Prompt 06          → Tóm tắt Zalo
07:30  [HUMAN] Publish            → output/published/ + Zalo/Telegram
```

---

## 🔄 Checklist hàng ngày

### Thu thập (5:30-6:00)
- [ ] Chạy `collect_news.py` — lấy tin từ RSS feeds
- [ ] Lấy snapshot thị trường từ vnstock/API
- [ ] Check lịch sự kiện ngày hôm nay (HOSE, HNX)
- [ ] Check thị trường US qua đêm (S&P, Nasdaq, DXY, vàng, dầu)

### Soạn thảo (6:00-7:00)
- [ ] Chạy Prompt 01 — phân loại tin
- [ ] Chạy Prompt 02 — data thị trường
- [ ] Chạy Prompt 03 — viết bản tin vào template
- [ ] Chạy Prompt 04 — review & sửa
- [ ] Human review: đọc lại toàn bộ, check số liệu

### Publish (7:00-7:30)
- [ ] Chạy Prompt 05 — chọn tiêu đề đẹp nhất
- [ ] Chạy Prompt 06 — tạo bản Zalo/Telegram
- [ ] Lưu vào `output/published/YYYY-MM-DD_ban-tin-sang.md`
- [ ] Post Zalo / Telegram / Web
- [ ] Log kết quả vào `workflow/logs/YYYY-MM-DD_workflow.log`

### Post-publish (sau 9:00)
- [ ] Note feedback nếu có
- [ ] Update context nếu có thay đổi thị trường lớn

---

## 🚨 Xử lý khi có sự cố

| Sự cố | Giải pháp |
|-------|-----------|
| API lấy data lỗi | Dùng data từ CafeF/Vietstock thủ công |
| AI hallucinate số liệu | Luôn cross-check số liệu với nguồn gốc |
| Không có tin nổi bật | Dùng góc nhìn ngành/macro thay thế |
| Trễ deadline | Rút gọn xuống chỉ còn: thị trường + 2 tin + góc nhìn |

---

## 📊 KPI theo dõi hàng tuần

- Publish đúng giờ (trước 7:30): mục tiêu 5/5 ngày
- Không có lỗi số liệu: 0 correction/tuần
- Thời gian soạn thảo tổng: < 90 phút/ngày
- Độ dài bản tin: 600-1000 chữ (target zone)
