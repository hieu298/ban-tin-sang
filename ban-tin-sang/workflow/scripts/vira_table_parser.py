# -*- coding: utf-8 -*-
import re

def extract_tables_from_text(text: str) -> str:
    """
    Phân tích đoạn text dày đặc, trích xuất số liệu và chuyển thành
    bảng Markdown để hiển thị đẹp hơn. Nếu không trích xuất được thì
    trả về nguyên bản text.
    """
    
    # 1. Thị trường ngoại tệ
    if "Thị trường ngoại tệ" in text or "tỷ giá trung tâm" in text:
        m_tg = re.search(r'tỷ giá trung tâm.*?mức ([\d,.]+)\s*VND/USD', text)
        m_mua = re.search(r'mua giao ngay.*?mức ([\d,.]+)\s*VND/USD', text)
        m_ban = re.search(r'bán giao ngay.*?mức ([\d,.]+)\s*VND/USD', text)
        m_lnh = re.search(r'thị trường LNH, tỷ giá.*?mức ([\d,.]+)\s*VND/USD', text)
        m_td = re.search(r'tự do.*?giao dịch tại ([\d,.]+)\s*VND/USD và ([\d,.]+)\s*VND/USD', text)
        
        if m_tg or m_lnh:
            lines = [
                text, "",
                "**Bảng Tỷ giá (VND/USD):**",
                "| Loại tỷ giá | Mức giá |",
                "|---|---|"
            ]
            if m_tg: lines.append(f"| Tỷ giá trung tâm (NHNN) | {m_tg.group(1)} |")
            if m_mua: lines.append(f"| Mua giao ngay | {m_mua.group(1)} |")
            if m_ban: lines.append(f"| Bán giao ngay | {m_ban.group(1)} |")
            if m_lnh: lines.append(f"| Liên ngân hàng (LNH) | {m_lnh.group(1)} |")
            if m_td: lines.append(f"| Thị trường Tự do (Mua-Bán) | {m_td.group(1)} - {m_td.group(2)} |")
            return "\n".join(lines)

    # 2. Thị trường tiền tệ LNH
    if "lãi suất bình quân LNH" in text or "Lợi suất TPCP" in text:
        lines = [text, ""]
        found_any = False
        
        # Lãi suất LNH
        m_vnd = re.search(r'LNH VND.*?giao dịch tại:\s*([^.]*)', text)
        m_usd = re.search(r'LNH USD.*?giao dịch tại:\s*([^.]*)', text)
        if m_vnd and m_usd:
            vnd_rates = dict(re.findall(r'(ON|1W|2W|1M)\s*([\d,]+%)', m_vnd.group(1)))
            usd_rates = dict(re.findall(r'(ON|1W|2W|1M)\s*([\d,]+%)', m_usd.group(1)))
            lines.extend([
                "**Lãi suất Liên ngân hàng (LNH):**",
                "| Loại | ON | 1W | 2W | 1M |",
                "|---|---|---|---|---|",
                f"| VND | {vnd_rates.get('ON','-')} | {vnd_rates.get('1W','-')} | {vnd_rates.get('2W','-')} | {vnd_rates.get('1M','-')} |",
                f"| USD | {usd_rates.get('ON','-')} | {usd_rates.get('1W','-')} | {usd_rates.get('2W','-')} | {usd_rates.get('1M','-')} |",
                ""
            ])
            found_any = True

        # TPCP
        m_tpcp = re.search(r'Lợi suất TPCP.*?chốt phiên ở mức:\s*([^.]*)', text)
        if m_tpcp:
            rates = dict(re.findall(r'(3Y|5Y|7Y|10Y|15Y)\s*([\d,]+%)', m_tpcp.group(1)))
            lines.extend([
                "**Lợi suất TPCP thứ cấp:**",
                "| Kỳ hạn | 3Y | 5Y | 7Y | 10Y | 15Y |",
                "|---|---|---|---|---|---|",
                f"| Lợi suất | {rates.get('3Y','-')} | {rates.get('5Y','-')} | {rates.get('7Y','-')} | {rates.get('10Y','-')} | {rates.get('15Y','-')} |",
                ""
            ])
            found_any = True
            
        if found_any:
            return "\n".join(lines).strip()

    # 3. Chứng khoán
    if "Thị trường chứng khoán" in text or "VN-Index" in text:
        idx = re.findall(r'(VN-Index|HNX-Index|UPCoM-Index)[^\d]+(tăng|giảm|thêm)\s*([\d,]+)\s*điểm\s*\(([+-]?[\d,]+%)\)[^\d]+([\d,]+(?:,[\d]+)*)', text)
        if idx:
            lines = [
                text, "",
                "**Diễn biến Chỉ số Chứng khoán:**",
                "| Chỉ số | Điểm số | Thay đổi (+/-) | % Thay đổi |",
                "|---|---|---|---|"
            ]
            for name, dir_str, points, pct, current in idx:
                sign = "+" if dir_str in ["tăng", "thêm"] else "-"
                lines.append(f"| {name} | {current} | {sign}{points} | {pct} |")
            return "\n".join(lines)

    return text
