# 📰 BẢN TIN SÁNG — AI Workflow Template

> **Mục tiêu**: Sản xuất bản tin sáng hàng ngày chất lượng cao về thị trường tài chính, kinh tế vĩ mô và cổ phiếu Việt Nam — bằng quy trình AI-assisted có thể lặp lại mỗi ngày.

---

## 🗂️ CẤU TRÚC THƯ MỤC

```
ban-tin-sang/
│
├── 📥 sources/              # Nguồn dữ liệu đầu vào
│   ├── raw-feeds/           # Tin thô từ RSS, API, crawler
│   ├── rss-links/           # Danh sách nguồn RSS/URL theo dõi
│   ├── manual-clips/        # Tin bạn tự clip/lưu thủ công
│   └── data-snapshots/      # Snapshot dữ liệu thị trường (giá, dòng tiền...)
│
├── 📤 output/               # Bản tin đầu ra
│   ├── drafts/              # Bản thảo (chưa publish)
│   ├── published/           # Đã đăng (lưu archive theo ngày)
│   ├── archive/             # Archive dài hạn theo tháng
│   └── assets/              # Ảnh, chart, infographic đính kèm
│
├── ⚙️ workflow/              # Quy trình làm việc
│   ├── prompts/             # Prompt AI cho từng bước
│   ├── scripts/             # Script tự động hóa (Python, BAT...)
│   ├── logs/                # Log chạy hàng ngày
│   └── schedules/           # Lịch chạy, cron jobs
│
├── 📋 rules/                # Quy tắc biên tập
│   ├── editorial/           # Quy tắc chọn tin, độ ưu tiên
│   ├── tone-voice/          # Giọng văn, phong cách viết
│   └── format-templates/    # Template format HTML/MD/PDF
│
├── 🧠 skills/               # Kho kỹ năng AI có thể gọi lại
│   ├── writing-techniques/  # Kỹ thuật viết tin tài chính
│   ├── analysis-frameworks/ # Framework phân tích (macro, sector...)
│   └── prompt-library/      # Thư viện prompt đã test & proven
│
├── 🔭 context/              # Bối cảnh nền để AI hiểu thị trường
│   ├── market-baseline/     # Baseline thị trường (VNINDEX, macro...)
│   ├── watchlist/           # Danh sách cổ phiếu/ngành theo dõi
│   └── themes/              # Chủ đề thị trường đang diễn ra
│
└── 🔍 review/               # Kiểm tra & cải thiện
    ├── feedback/            # Feedback từ người đọc / bản thân
    ├── corrections/         # Lỗi đã sửa — học để không lặp lại
    └── versions/            # Version tracking bản tin
```

---

## ⚡ QUICK START — Quy trình mỗi sáng

```
1. 05:30  → Script thu thập tin (workflow/scripts/collect_news.py)
2. 06:00  → AI tóm tắt & phân loại (workflow/prompts/summarize.md)
3. 06:30  → AI viết bản thảo (workflow/prompts/write_brief.md)
4. 07:00  → Review & sửa tay (output/drafts/)
5. 07:30  → Publish (output/published/YYYY-MM-DD.md)
```

---

## 📌 QUY ƯỚC ĐẶT TÊN FILE

- Bản tin: `YYYY-MM-DD_ban-tin-sang.md`
- Data snapshot: `YYYY-MM-DD_HH-MM_<ten-nguon>.json`
- Prompt: `<buoc>_<ten-nhiem-vu>.md` (vd: `01_summarize-news.md`)
- Log: `YYYY-MM-DD_workflow.log`

---

*Cập nhật lần cuối: 2026-07-01*
