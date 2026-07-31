import os
import sys
import re
import json
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from datetime import datetime, timedelta

def parse_markdown_to_html(md_text):
    if not md_text:
        return "<p>Bản tin đang được cập nhật tự động...</p>"
        
    # Remove YAML frontmatter
    md_text = re.sub(r'^---[\s\S]*?---\n', '', md_text, flags=re.MULTILINE)
    
    lines = md_text.split('\n')
    html_lines = []
    quote_lines = []
    in_table = False
    table_lines = []
    
    def render_inline(text):
        # Links [text](url)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener" class="styled-link">\1</a>', text)
        # Bold **text**
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        # Italic *text*
        text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
        # Code `text`
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        return text

    def process_table(lines):
        if not lines:
            return ""
        table_html = ['<table class="data-table">']
        headers = [c.strip() for c in lines[0].split('|')[1:-1]]
        table_html.append('<thead><tr>' + ''.join(f'<th>{render_inline(h)}</th>' for h in headers) + '</tr></thead>')
        table_html.append('<tbody>')
        for row in lines:
            if '|' in row and not ('---' in row or ':---' in row):
                cols = [c.strip() for c in row.split('|')[1:-1]]
                if cols != headers:
                    table_html.append('<tr>' + ''.join(f'<td>{render_inline(c)}</td>' for c in cols) + '</tr>')
        table_html.append('</tbody></table>')
        return '\n'.join(table_html)

    for line in lines:
        stripped = line.strip()
        
        # Check Table
        if stripped.startswith('|') and stripped.endswith('|'):
            if not in_table:
                in_table = True
                table_lines = []
            table_lines.append(stripped)
            continue
        elif in_table:
            in_table = False
            html_lines.append(process_table(table_lines))
            table_lines = []
            
        # Check Quote
        if stripped.startswith('>'):
            quote_content = stripped.lstrip('> ').strip()
            if quote_content:
                quote_lines.append(render_inline(quote_content))
            continue
        elif quote_lines:
            html_lines.append(f'<blockquote class="brief-quote">{"<br>".join(quote_lines)}</blockquote>')
            quote_lines = []
            
        # Horizontal Rule
        if stripped in ('---', '***', '___'):
            html_lines.append('<hr class="styled-hr">')
            continue
            
        # Headers
        if stripped.startswith('# '):
            html_lines.append(f'<h3 class="brief-title">{render_inline(stripped[2:])}</h3>')
            continue
        elif stripped.startswith('## '):
            html_lines.append(f'<h3 class="section-title">{render_inline(stripped[3:])}</h3>')
            continue
        elif stripped.startswith('### '):
            html_lines.append(f'<h4 class="sub-title">{render_inline(stripped[4:])}</h4>')
            continue
            
        # Lists
        if stripped.startswith('- ') or stripped.startswith('* '):
            html_lines.append(f'<li class="list-item">{render_inline(stripped[2:])}</li>')
            continue
            
        # Regular paragraph line
        if stripped:
            html_lines.append(f'<p>{render_inline(stripped)}</p>')
            
    if quote_lines:
        html_lines.append(f'<blockquote class="brief-quote">{"<br>".join(quote_lines)}</blockquote>')
    if in_table and table_lines:
        html_lines.append(process_table(table_lines))
        
    return '\n'.join(html_lines)


def generate_web_html(date_str=None):
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
        
    script_dir = Path(__file__).parent.resolve()
    base_dir = script_dir.parent.parent
    drafts_dir = base_dir / "output" / "drafts"
    output_html_path = base_dir / "index.html"
    
    # Read draft texts from VIRA, HOSE, and Vietstock RSS if available
    draft_parts = []
    
    vira_path = drafts_dir / f"{date_str}_vira-ban-tin.md"
    if vira_path.exists():
        with open(vira_path, "r", encoding="utf-8") as f:
            draft_parts.append(f.read())
            
    hsx_path = drafts_dir / f"{date_str}_hsx-news.md"
    if hsx_path.exists():
        with open(hsx_path, "r", encoding="utf-8") as f:
            draft_parts.append(f.read())
            
    vietstock_path = drafts_dir / f"{date_str}_vietstock.md"
    if vietstock_path.exists():
        with open(vietstock_path, "r", encoding="utf-8") as f:
            draft_parts.append(f.read())

    # Fallback to previous day's VIRA draft if today's VIRA draft is missing but we have previous
    if not draft_parts:
        all_vira_drafts = sorted(list(drafts_dir.glob("*_vira-ban-tin.md")), reverse=True)
        if all_vira_drafts:
            with open(all_vira_drafts[0], "r", encoding="utf-8") as f:
                draft_parts.append(f.read())

    content_text = "\n\n---\n\n".join(draft_parts)
    parsed_html_content = parse_markdown_to_html(content_text)
    today_formatted = datetime.now().strftime("%d/%m/%Y")
    version = int(datetime.now().timestamp())

    
    html_template = f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bản tin Chứng khoán Sáng — {today_formatted}</title>
<style>
  :root {{
    color-scheme: light dark;
    --page:        #f9f9f7;
    --surface:     #fcfcfb;
    --ink:         #0b0b0b;
    --ink-2:       #52514e;
    --muted:       #898781;
    --hairline:    #e1e0d9;
    --border:      rgba(11,11,11,0.10);
    --up:          #006300;
    --down:        #d03b3b;
    --accent:      #2a78d6;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --page:        #0d0d0d;
      --surface:     #1a1a19;
      --ink:         #ffffff;
      --ink-2:       #c3c2b7;
      --muted:       #898781;
      --hairline:    #2c2c2a;
      --border:      rgba(255,255,255,0.10);
      --up:          #0ca30c;
      --down:        #e66767;
      --accent:      #3987e5;
    }}
  }}
  :root[data-theme="dark"] {{
    --page:        #0d0d0d;
    --surface:     #1a1a19;
    --ink:         #ffffff;
    --ink-2:       #c3c2b7;
    --muted:       #898781;
    --hairline:    #2c2c2a;
    --border:      rgba(255,255,255,0.10);
    --up:          #0ca30c;
    --down:        #e66767;
    --accent:      #3987e5;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--page); color: var(--ink);
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    font-size: 15.5px; line-height: 1.6; padding: 0 16px 48px;
  }}
  .wrap {{ max-width: 800px; margin: 0 auto; }}
  header {{ padding: 24px 0 12px; border-bottom: 2px solid var(--hairline); margin-bottom: 16px; }}
  .masthead {{ display: flex; align-items: center; justify-content: space-between; gap: 8px; }}
  h1 {{ font-size: 1.4rem; margin: 0; }}
  .dateline {{ color: var(--ink-2); font-size: 0.9rem; margin-top: 4px; }}
  #themeBtn {{
    background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
    font-size: 1.1rem; padding: 6px 12px; cursor: pointer; color: var(--ink);
  }}
  .tiles {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 16px 0; }}
  @media (min-width: 560px) {{ .tiles {{ grid-template-columns: repeat(4, 1fr); }} }}
  .tile {{
    background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
    padding: 12px 14px;
  }}
  .tile .label {{ color: var(--ink-2); font-size: 0.82rem; }}
  .tile .value {{ font-weight: 700; font-size: 1.1rem; margin-top: 4px; }}
  .tile .delta {{ font-size: 0.85rem; margin-top: 2px; }}
  .delta.up {{ color: var(--up); }}
  .delta.down {{ color: var(--down); }}
  
  .content-box {{
    background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
    padding: 20px 24px; margin-top: 20px; line-height: 1.7;
  }}
  .brief-title {{ color: var(--ink); font-size: 1.3rem; margin-top: 8px; margin-bottom: 16px; }}
  .section-title {{ color: var(--accent); border-bottom: 1px solid var(--hairline); padding-bottom: 6px; font-size: 1.15rem; margin-top: 24px; }}
  .sub-title {{ font-size: 1.05rem; color: var(--ink); margin-top: 18px; margin-bottom: 8px; font-weight: 700; }}
  .brief-quote {{ background: rgba(42, 120, 214, 0.06); border-left: 4px solid var(--accent); padding: 12px 16px; margin: 14px 0; border-radius: 6px; font-size: 0.95rem; }}
  .data-table {{ width: 100%; border-collapse: collapse; margin: 16px 0; background: var(--page); border-radius: 8px; overflow: hidden; font-size: 0.92rem; }}
  .data-table th, .data-table td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--border); }}
  .data-table th {{ background: rgba(42, 120, 214, 0.12); font-weight: 600; color: var(--ink); }}
  .styled-link {{ color: var(--accent); text-decoration: none; font-weight: 500; word-break: break-all; }}
  .styled-link:hover {{ text-decoration: underline; }}
  .styled-hr {{ border: none; border-top: 1px solid var(--hairline); margin: 24px 0; }}
  .list-item {{ margin-left: 20px; margin-bottom: 6px; }}
  p {{ margin: 10px 0; }}
  code {{ background: rgba(128,128,128,0.15); padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }}
  
  .charts-grid {{ display: grid; grid-template-columns: 1fr; gap: 16px; margin-top: 20px; }}
  @media (min-width: 600px) {{ .charts-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
  .chart-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 10px; text-align: center; }}
  .chart-card img {{ width: 100%; height: auto; border-radius: 6px; }}
  footer {{ margin-top: 40px; padding-top: 16px; border-top: 1px solid var(--hairline); color: var(--muted); font-size: 0.85rem; text-align: center; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="masthead">
      <div>
        <h1>📈 Bản tin Chứng khoán Sáng</h1>
        <div class="dateline">Ngày {today_formatted} · Cập nhật tự động 8:00 AM</div>
      </div>
      <button id="themeBtn" onclick="toggleTheme()">🌙</button>
    </div>
  </header>

  <div class="tiles">
    <div class="tile"><div class="label">VN-INDEX</div><div class="value">1.704,68</div><div class="delta up">▲ +1,43%</div></div>
    <div class="tile"><div class="label">HNX-INDEX</div><div class="value">271,68</div><div class="delta up">▲ +0,83%</div></div>
    <div class="tile"><div class="label">S&amp;P 500</div><div class="value">7.316,15</div><div class="delta down">▼ −1,52%</div></div>
    <div class="tile"><div class="label">Dầu WTI</div><div class="value">84,20 $</div><div class="delta up">▲ +6,44%</div></div>
  </div>

  <div class="content-box">
    {parsed_html_content}
  </div>

  <h2 class="section-title">🏢 Phân tích Nhóm Ngành (Dữ liệu MASVN Mastrade)</h2>
  <div class="charts-grid">
    <div class="chart-card">
      <img src="ban-tin-sang/output/charts/market_contrib.png?v={version}" onerror="if(!this.dataset.fallback){{this.dataset.fallback=true;this.src='output/charts/market_contrib.png?v={version}';}}" alt="Phân hóa Nhóm Ngành MASVN">
      <div style="font-size:0.85rem; margin-top:6px; font-weight: 500;">Biến động &amp; Đóng góp Nhóm ngành (MASVN)</div>
    </div>
    <div class="chart-card">
      <img src="ban-tin-sang/output/charts/sector_intraday.png?v={version}" onerror="if(!this.dataset.fallback){{this.dataset.fallback=true;this.src='output/charts/sector_intraday.png?v={version}';}}" alt="Diễn biến Ngành MASVN">
      <div style="font-size:0.85rem; margin-top:6px; font-weight: 500;">Diễn biến Nhóm ngành In-day (MASVN)</div>
    </div>
  </div>

  <h2 class="section-title">📊 Biểu đồ Thị trường &amp; Dòng tiền</h2>
  <div class="charts-grid">
    <div class="chart-card">
      <img src="ban-tin-sang/output/charts/vnindex_intraday.png?v={version}" onerror="if(!this.dataset.fallback){{this.dataset.fallback=true;this.src='output/charts/vnindex_intraday.png?v={version}';}}" alt="VNIndex Intraday">
      <div style="font-size:0.85rem; margin-top:6px; font-weight: 500;">Diễn biến VN-Index In-day</div>
    </div>
    <div class="chart-card">
      <img src="ban-tin-sang/output/charts/market_liquidity.png?v={version}" onerror="if(!this.dataset.fallback){{this.dataset.fallback=true;this.src='output/charts/market_liquidity.png?v={version}';}}" alt="Thanh khoản">
      <div style="font-size:0.85rem; margin-top:6px; font-weight: 500;">Thanh khoản Thị trường</div>
    </div>
    <div class="chart-card">
      <img src="ban-tin-sang/output/charts/institutional_flow.png?v={version}" onerror="if(!this.dataset.fallback){{this.dataset.fallback=true;this.src='output/charts/institutional_flow.png?v={version}';}}" alt="Dòng tiền Tổ chức">
      <div style="font-size:0.85rem; margin-top:6px; font-weight: 500;">Dòng tiền Khối ngoại &amp; Tự doanh</div>
    </div>
    <div class="chart-card">
      <img src="ban-tin-sang/output/charts/market_breadth.png?v={version}" onerror="if(!this.dataset.fallback){{this.dataset.fallback=true;this.src='output/charts/market_breadth.png?v={version}';}}" alt="Độ rộng Thị trường">
      <div style="font-size:0.85rem; margin-top:6px; font-weight: 500;">Độ rộng Thị trường</div>
    </div>
  </div>

  <h2 class="section-title">🌍 Vĩ mô &amp; Thị trường Quốc tế</h2>
  <div class="charts-grid">
    <div class="chart-card">
      <img src="ban-tin-sang/output/charts/global_markets.png?v={version}" onerror="if(!this.dataset.fallback){{this.dataset.fallback=true;this.src='output/charts/global_markets.png?v={version}';}}" alt="Thị trường Quốc tế">
      <div style="font-size:0.85rem; margin-top:6px; font-weight: 500;">Thị trường Quốc tế &amp; Hàng hóa</div>
    </div>
    <div class="chart-card">
      <img src="ban-tin-sang/output/charts/market_valuation.png?v={version}" onerror="if(!this.dataset.fallback){{this.dataset.fallback=true;this.src='output/charts/market_valuation.png?v={version}';}}" alt="Định giá Thị trường">
      <div style="font-size:0.85rem; margin-top:6px; font-weight: 500;">Định giá P/E Thị trường</div>
    </div>
  </div>

  <footer>
    <p>Hệ thống tự động tổng hợp &amp; xuất bản bởi VIRA AI Newsletter Automation</p>
  </footer>
</div>

<script>
  function toggleTheme() {{
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    document.getElementById('themeBtn').innerText = next === 'dark' ? '☀️' : '🌙';
  }}
</script>
</body>
</html>
"""
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"✅ Đã xuất trang HTML web định dạng chuẩn tại: {output_html_path}")

if __name__ == "__main__":
    generate_web_html()
