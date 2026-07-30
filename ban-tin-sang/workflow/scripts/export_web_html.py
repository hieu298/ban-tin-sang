import os
import sys
import re
import json
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from datetime import datetime, timedelta

def generate_web_html(date_str=None):
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
        
    script_dir = Path(__file__).parent.resolve()
    base_dir = script_dir.parent.parent
    draft_path = base_dir / "output" / "drafts" / f"{date_str}_vira-ban-tin.md"
    output_html_path = base_dir / "index.html"
    
    # Read draft text if available
    content_text = ""
    if draft_path.exists():
        with open(draft_path, "r", encoding="utf-8") as f:
            content_text = f.read()
            
    today_formatted = datetime.now().strftime("%d/%m/%Y")
    
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
  .content-box h2 {{ color: var(--accent); border-bottom: 1px solid var(--hairline); padding-bottom: 6px; font-size: 1.15rem; }}
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
    <h2>📰 Nội dung Bản tin Hôm nay</h2>
    <div>
      {content_text.replace('\n', '<br>') if content_text else 'Bản tin đang được cập nhật tự động...'}
    </div>
  </div>

  <h2>📊 Biểu đồ Thị trường Tự động</h2>
  <div class="charts-grid">
    <div class="chart-card">
      <img src="output/charts/vnindex_intraday.png" alt="VNIndex Intraday" onerror="this.style.display='none'">
      <div style="font-size:0.85rem; margin-top:6px;">Diễn biến VN-Index In-day</div>
    </div>
    <div class="chart-card">
      <img src="output/charts/market_liquidity.png" alt="Thanh khoản" onerror="this.style.display='none'">
      <div style="font-size:0.85rem; margin-top:6px;">Thanh khoản Thị trường</div>
    </div>
    <div class="chart-card">
      <img src="output/charts/institutional_flow.png" alt="Dòng tiền Tổ chức" onerror="this.style.display='none'">
      <div style="font-size:0.85rem; margin-top:6px;">Dòng tiền Khối ngoại &amp; Tự doanh</div>
    </div>
    <div class="chart-card">
      <img src="output/charts/market_breadth.png" alt="Độ rộng Thị trường" onerror="this.style.display='none'">
      <div style="font-size:0.85rem; margin-top:6px;">Độ rộng Thị trường</div>
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
    print(f"✅ Đã xuất trang HTML web tại: {output_html_path}")

if __name__ == "__main__":
    generate_web_html()
