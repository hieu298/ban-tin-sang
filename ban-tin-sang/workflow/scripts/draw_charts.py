import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from pathlib import Path
import os
import urllib.request
import json
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import time
from datetime import datetime, timedelta, timezone

def fetch_sector_data():
    url = 'https://mastrade.masvn.com/api/v2/vs/sectorIndex?query=query{vsSectorIndexList(LanguageID:1){_id,SectorName,CloseIndex,InfluenceIndex,Change,PerChange,Vol,Val,ForeignBuyVol,ForeignSellVol,CeilCount,FloorCount,UpCount,DownCount,UnchangeCount,ROA,ROE,VSTSectorID,PerChange1M,PerChange3M,PerChange6M,EPS,PE,PB,MarketCapital}}'
    try:
        data = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=15).json()
        if isinstance(data, list):
            return data
    except:
        pass
    return []

def draw_market_contribution_chart():
    # Thư mục lưu ảnh
    script_dir = Path(__file__).parent.resolve()
    charts_dir = script_dir.parent.parent / "output" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    
    out_path = charts_dir / "market_contrib.png"
    
    # 1. Fetch Real Data from Mastrade API
    sectors = fetch_sector_data()
    if not sectors:
        print("❌ Lỗi: Không thể lấy dữ liệu Nhóm Ngành từ Mastrade.")
        return
        
    valid_sectors = [s for s in sectors if s.get('PerChange') is not None]
    # No filtering, take all valid sectors!
    selected_sectors = valid_sectors

    if not selected_sectors:
        return
        
    # Sort for barh plotting (bottom to top, so lowest PerChange at bottom)
    selected_sectors.sort(key=lambda x: x.get('PerChange', 0))
    
    tickers = [s.get('SectorName', '') for s in selected_sectors]
    contribs = [s.get('PerChange', 0) for s in selected_sectors]
    
    # Tạo màu theo quy tắc: Tăng > 2% (Xanh đậm), Tăng 0-2% (Xanh nhạt), Giảm > 2% (Đỏ đậm), Giảm 0-2% (Hồng)
    colors = []
    for c in contribs:
        if c > 2:
            colors.append('#27ae60') # Tăng mạnh
        elif c >= 0:
            colors.append('#2ecc71') # Tăng nhẹ
        elif c < -2:
            colors.append('#c0392b') # Giảm mạnh
        else:
            colors.append('#e74c3c') # Giảm nhẹ
            
    # Thiết lập kích thước và style (Light theme)
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    # Vẽ biểu đồ ngang
    bars = ax.barh(tickers, contribs, color=colors, height=0.7)
    
    # Minimalist style: Bỏ khung (spines)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    
    # Format axes text
    ax.tick_params(axis='y', colors='#333333', length=0, labelsize=11)
    
    import matplotlib.ticker as mtick
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=100))
    ax.tick_params(axis='x', colors='#666666', labelsize=10)
    ax.xaxis.grid(True, color='#eeeeee', linestyle='-', linewidth=1)
    ax.set_axisbelow(True)
    
    # Thêm trục 0 ở giữa
    ax.axvline(0, color='#f39c12', linewidth=1.5, zorder=3)
    
    # Điền giá trị lên từng thanh bar
    for bar, val in zip(bars, contribs):
        x_offset = 0.1 if val >= 0 else -0.1
        ha = 'left' if val >= 0 else 'right'
        # Dùng màu tối hơn cho chữ để dễ nhìn trên nền trắng
        text_color = '#1e8449' if val > 2 else ('#27ae60' if val >= 0 else ('#922b21' if val < -2 else '#c0392b'))
        ax.text(val + x_offset, bar.get_y() + bar.get_height()/2, 
                f"{val:+.2f}%", 
                va='center', ha=ha, fontsize=10, fontweight='bold', color=text_color)
                
    # Add Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#27ae60', label='Tăng > 2%'),
        Patch(facecolor='#2ecc71', label='Tăng 0-2%'),
        Patch(facecolor='#c0392b', label='Giảm > 2%'),
        Patch(facecolor='#e74c3c', label='Giảm 0-2%')
    ]
    ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.08), 
              ncol=4, frameon=False, labelcolor='#333333', fontsize=10)
              
    # Tiêu đề
    plt.title("SỨC ẢNH HƯỞNG & BIẾN ĐỘNG CÁC NHÓM NGÀNH", 
              fontsize=14, fontweight='bold', color='#2c3e50', pad=20)
        
    # Lưu ảnh
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    
    print(f"✅ Đã vẽ biểu đồ và lưu tại: {out_path}")

def draw_market_breadth_chart():
    script_dir = Path(__file__).parent.resolve()
    charts_dir = script_dir.parent.parent / "output" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    out_path = charts_dir / "market_breadth.png"
    
    # Fetch from VNDirect gainerslosers API
    url = "https://mkw-socket-v2.vndirect.com.vn/mkwsocketv2/gainerslosers?index=VNINDEX"
    advance, no_change, decline = 172, 82, 125
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=15)
        if r.status_code == 200:
            list_data = r.json().get("data", [])
            if list_data:
                latest = list_data[-1]
                advance = latest.get("advance", 172)
                no_change = latest.get("noChange", 82)
                decline = latest.get("decline", 125)
    except Exception as e:
        print("Lỗi lấy độ rộng thị trường từ VNDirect:", e)
        
    count_data = [advance, no_change, decline]
    
    # Fetch latest market liquidity from VNDirect to scale cash flow
    total_val = 16000 # default
    try:
        liq_url = "https://mkw-socket-v2.vndirect.com.vn/mkwsocketv2/liquidity?index=VNINDEX"
        r_l = requests.get(liq_url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=15)
        if r_l.status_code == 200:
            liq_list = r_l.json().get("data", [])
            if liq_list:
                total_val = liq_list[-1].get("value", 16000)
    except Exception as e:
        print("Lỗi lấy thanh khoản để phân bổ dòng tiền:", e)
        
    total_stocks = advance + no_change + decline
    if total_stocks > 0:
        cash_data = [
            total_val * (advance / total_stocks),
            total_val * (no_change / total_stocks),
            total_val * (decline / total_stocks)
        ]
    else:
        cash_data = [7237.01, 489.09, 1786.93]

    labels = ['Tăng', 'Không đổi', 'Giảm']
    colors = ['#2ecc71', '#f1c40f', '#e74c3c']
    
    # Create figure with 2 subplots side-by-side
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5), gridspec_kw={'width_ratios': [1, 1.2]})
    fig.patch.set_facecolor('white')
    
    # --- Subplot 1: Donut Chart (Count) ---
    wedges, texts, autotexts = ax1.pie(
        count_data, labels=labels, colors=colors, autopct='%1.0f', 
        startangle=90, pctdistance=0.75,
        textprops=dict(color='black', fontsize=10, fontweight='bold'),
        wedgeprops=dict(width=0.4, edgecolor='white', linewidth=1.5) # Donut style
    )
    for i, autotext in enumerate(autotexts):
        autotext.set_text(str(count_data[i]))
        autotext.set_color('white' if i != 1 else 'black')
        
    ax1.set_title("Số lượng CP\nTăng, Giảm, Không đổi", fontsize=11, fontweight='bold', color='#333', pad=15)
    
    # --- Subplot 2: Bar Chart (Cash Flow) ---
    bars = ax2.bar(labels, cash_data, color=colors, width=0.5)
    ax2.set_title("Phân bổ dòng tiền", fontsize=11, fontweight='bold', color='#333', pad=15)
    
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    ax2.spines['bottom'].set_color('#dddddd')
    ax2.tick_params(axis='both', which='both', length=0)
    ax2.yaxis.grid(True, linestyle='--', color='#eeeeee', alpha=0.7)
    ax2.set_axisbelow(True)
    
    # Format Y axis as 'k' (nghìn tỷ)
    ticks = ax2.get_yticks()
    ax2.set_yticks(ticks)
    ax2.set_yticklabels([f"{int(t/1000)}k" if t > 0 else "0" for t in ticks])
    
    for bar, val in zip(bars, cash_data):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + total_val*0.02, 
                f"{val:,.0f} tỷ", 
                ha='center', va='bottom', fontsize=9, fontweight='bold', color='#333')
        
    plt.suptitle("ĐỘ RỘNG THỊ TRƯỜNG & DÒNG TIỀN (VNDIRECT)", fontsize=14, fontweight='bold', color='#2c3e50', y=1.05)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✅ Đã vẽ biểu đồ độ rộng thị trường VNDirect và lưu tại: {out_path}")

def draw_market_breadth_area_chart():
    script_dir = Path(__file__).parent.resolve()
    charts_dir = script_dir.parent.parent / "output" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    out_path = charts_dir / "market_breadth_area.png"
    
    # 1. Fetch data from VNDirect API
    url = "https://mkw-socket-v2.vndirect.com.vn/mkwsocketv2/gainerslosers?index=VNINDEX"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req).read().decode('utf-8')
        data = json.loads(response)
    except Exception as e:
        print(f"Lỗi khi gọi API VNDirect: {e}")
        return
        
    if not data:
        print("Không có dữ liệu từ VNDirect.")
        return

    # 2. Parse data
    times = []
    adv_pcts = []
    no_pcts = []
    dec_pcts = []
    
    data_list = data.get("data", [])
    
    for item in data_list:
        # Tạm lấy ngày hôm nay gắn vào giờ để dùng cho trục X
        time_str = item.get("time", "")
        if not time_str: continue
        
        try:
            dt = datetime.strptime(time_str, "%H:%M:%S")
            # Gắn ngày hiện tại để vẽ (chỉ lấy giờ hiển thị)
            dt = dt.replace(year=datetime.now().year, month=datetime.now().month, day=datetime.now().day)
        except:
            continue
            
        adv = item.get("advance", 0)
        dec = item.get("decline", 0)
        no = item.get("noChange", 0)
        
        total = adv + dec + no
        if total == 0: continue
        
        times.append(dt)
        adv_pcts.append(adv / total * 100)
        no_pcts.append(no / total * 100)
        dec_pcts.append(dec / total * 100)

    # 3. Draw Chart
    fig, ax = plt.subplots(figsize=(10, 4.5))
    fig.patch.set_facecolor('white')
    
    # Stackplot: Thứ tự từ dưới lên: Giảm (Đỏ) -> Không đổi (Vàng) -> Tăng (Xanh lá)
    ax.stackplot(times, dec_pcts, no_pcts, adv_pcts, 
                 labels=['Giảm giá', 'Đứng giá', 'Tăng giá'],
                 colors=['#e74c3c', '#f1c40f', '#2ecc71'])
    
    # Định dạng trục X (thời gian)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    # Định dạng trục Y (0 - 100)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Tỉ lệ %", fontsize=11, fontweight='bold', color='#333')
    
    # Lưới và đường viền (Minimalist)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('#cccccc')
    ax.tick_params(axis='both', which='both', length=0)
    ax.yaxis.grid(True, linestyle='--', color='white', alpha=0.3)
    ax.set_axisbelow(True)
    
    # Thêm Legend ở dưới cùng
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), 
              ncol=3, frameon=False, fontsize=10)
    
    plt.title("DIỄN BIẾN ĐỘ RỘNG THỊ TRƯỜNG (VN-Index)", fontsize=14, fontweight='bold', color='#2c3e50', pad=15)
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✅ Đã vẽ biểu đồ và lưu tại: {out_path}")

    print(f"✅ Đã vẽ biểu đồ và lưu tại: {out_path}")

def draw_liquidity_chart():
    script_dir = Path(__file__).parent.resolve()
    charts_dir = script_dir.parent.parent / "output" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    out_path = charts_dir / "market_liquidity.png"
    
    # 1. Fetch Real Data from Mastrade API for averages
    def fetch_liquidity(range_val):
        url = f"https://mastrade.masvn.com/api/v1/market/liquidityMinute?symbol=VN-INDEX&range={range_val}"
        try:
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=15).json()
            res = list(reversed(res)) # API returns latest first
            times = []
            vals = []
            for item in res:
                t = datetime.fromtimestamp(item['ti']/1000, tz=timezone.utc).replace(tzinfo=None) + timedelta(hours=7)
                times.append(t)
                vals.append(item['va'] / 1e9) # Convert to Tỷ VNĐ
            return times, vals
        except:
            return [], []

    # Fetch Today's Liquidity from VNDirect API
    real_times = []
    val_today = []
    try:
        url = "https://mkw-socket-v2.vndirect.com.vn/mkwsocketv2/liquidity?index=VNINDEX"
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=15)
        if r.status_code == 200:
            list_data = r.json().get("data", [])
            for item in list_data:
                t = datetime.fromtimestamp(item['time']/1000, tz=timezone.utc).replace(tzinfo=None) + timedelta(hours=7)
                real_times.append(t)
                val_today.append(item['value']) # value is already in Billion VNĐ
    except Exception as e:
        print("Lỗi lấy thanh khoản hôm nay từ VNDirect:", e)

    # Fallback to MASVN if VNDirect fails or has no data
    if not real_times:
        real_times, val_today = fetch_liquidity(1)
        
    _, val_week = fetch_liquidity(5)
    _, val_2weeks = fetch_liquidity(10)
    _, val_month = fetch_liquidity(20)
    
    if not real_times:
        print("❌ Lỗi: Không thể lấy dữ liệu thanh khoản từ cả VNDirect và MASVN.")
        return
        
    def align_data(base_times, target_vals):
        if not target_vals:
            return np.full(len(base_times), np.nan)
        if len(target_vals) >= len(base_times):
            return np.array(target_vals[:len(base_times)])
        else:
            arr = np.full(len(base_times), np.nan)
            arr[:len(target_vals)] = target_vals
            return arr

    val_week = align_data(real_times, val_week)
    val_2weeks = align_data(real_times, val_2weeks)
    val_month = align_data(real_times, val_month)

    # Remove trailing zeros (future time) for today's data so the line stops at current time
    # Actually, we find the first index where value stops increasing and is 0 or constant, but wait,
    # Mastrade data for range=1 in simulation seems to have full data. We leave it as is.
    
    # 2. Draw Chart
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('white')
    
    # Bar chart for Today (Green) using REAL API DATA
    ax.bar(real_times, val_today, width=0.0007, color='#2ecc71', alpha=0.9, label="Hiện tại")
    
    # Line charts for History using REAL API DATA
    ax.plot(real_times, val_week, color='#e74c3c', linewidth=2, label="Trung bình 1 tuần (5 ngày)")
    ax.plot(real_times, val_2weeks, color='#f1c40f', linewidth=2, label="Trung bình 2 tuần (10 ngày)")
    ax.plot(real_times, val_month, color='#9b59b6', linewidth=2, label="Trung bình 1 tháng (20 ngày)")
    
    # Format X axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.xticks(rotation=45)
    
    # Format Y axis
    ax.set_ylabel("Thanh khoản (Tỷ VNĐ)", fontsize=11, fontweight='bold', color='#333')
    
    # Styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('#cccccc')
    ax.tick_params(axis='both', which='both', length=0)
    ax.yaxis.grid(True, linestyle='--', color='#eeeeee', alpha=0.7)
    ax.set_axisbelow(True)
    
    # Legend
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), 
              ncol=4, frameon=False, fontsize=10)
    
    plt.title("SO SÁNH THANH KHOẢN KHỚP LỆNH (HOSE)", fontsize=14, fontweight='bold', color='#2c3e50', pad=15)
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✅ Đã vẽ biểu đồ và lưu tại: {out_path}")

    print(f"✅ Đã vẽ biểu đồ và lưu tại: {out_path}")

def draw_position_oscillator_chart():
    script_dir = Path(__file__).parent.resolve()
    charts_dir = script_dir.parent.parent / "output" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    out_path = charts_dir / "market_position.png"
    
    # 1. Fetch VNIndex History (Last 1 year)
    to_time = int(time.time())
    from_time = to_time - 365*24*3600
    hose_url = f"https://dchart-api.vndirect.com.vn/dchart/history?symbol=VNINDEX&resolution=D&from={from_time}&to={to_time}"
    hose_res = requests.get(hose_url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=15).json()
    
    hose_t = hose_res.get('t', [])
    hose_c = hose_res.get('c', [])
    
    hose_dict = {}
    for t_val, c_val in zip(hose_t, hose_c):
        dt = (datetime.fromtimestamp(t_val, tz=timezone.utc).replace(tzinfo=None) + timedelta(hours=7)).strftime("%Y-%m-%d")
        hose_dict[dt] = c_val
        
    # 2. Fetch Breadth Ratio (OVER_MA50D_PCT_CR)
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    ratio_url = f"https://api-finfo.vndirect.com.vn/v4/ratios?q=ratioCode:OVER_MA50D_PCT_CR~code:VNIndex~reportDate:gte:{start_date}&sort=reportDate:asc&size=500"
    ratio_res = requests.get(ratio_url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=15).json()
    
    ratio_data = ratio_res.get('data', [])
    ratio_dict = {}
    for item in ratio_data:
        dt = item.get('reportDate')
        val = item.get('value', 0) * 100 # Convert to %
        ratio_dict[dt] = val
        
    # 3. Merge data by common dates
    common_dates = sorted(list(set(hose_dict.keys()).intersection(set(ratio_dict.keys()))))
    
    if not common_dates:
        print("❌ Lỗi: Không có dữ liệu chung giữa 2 API.")
        return
        
    times = [datetime.strptime(d, "%Y-%m-%d") for d in common_dates]
    hose_index = np.array([hose_dict[d] for d in common_dates])
    vi_the = np.array([ratio_dict[d] for d in common_dates])
    
    # 4. Calculate Moving Averages
    def moving_average(x, w):
        if len(x) < w:
            return np.full(len(x), np.nan)
        ma = np.convolve(x, np.ones(w), 'valid') / w
        return np.concatenate((np.full(w-1, np.nan), ma))
        
    ma20 = moving_average(vi_the, 20)
    ma50 = moving_average(vi_the, 50)

    # 3. Draw Chart (Dual Y-Axis)
    fig, ax1 = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('white')
    ax2 = ax1.twinx()
    
    # Ax1 (Left - Vị thế %)
    l1 = ax1.plot(times, ma50, color='#3498db', linewidth=1.5, label="MA50", alpha=0.9)
    l2 = ax1.plot(times, ma20, color='#2ecc71', linewidth=1.5, label="MA20", alpha=0.9)
    l3 = ax1.plot(times, vi_the, color='#f1c40f', linewidth=2, label="Vị thế")
    
    # Ax2 (Right - HOSE Index)
    l4 = ax2.plot(times, hose_index, color='#e74c3c', linewidth=1.5, label="HOSE", alpha=0.9)
    
    # Dashed lines for Oversold/Overbought on Ax1
    ax1.axhline(15, color='#8e44ad', linestyle='--', linewidth=1, alpha=0.7)
    ax1.axhline(80, color='#2980b9', linestyle='--', linewidth=1, alpha=0.7)
    
    # Format X axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
    plt.setp(ax1.get_xticklabels(), rotation=45, ha="right")
    
    # Format Y axis (Left)
    ax1.set_ylim(0, 100)
    ax1.set_yticks([0, 15, 30, 45, 60, 75, 90])
    ax1.set_yticklabels([f"{y}%" for y in ax1.get_yticks()])
    ax1.set_ylabel("Vị thế (%)", fontsize=11, fontweight='bold', color='#333')
    
    # Format Y axis (Right)
    hose_min = np.min(hose_index) * 0.95
    hose_max = np.max(hose_index) * 1.05
    ax2.set_ylim(hose_min, hose_max)
    ax2.set_ylabel("Điểm số HOSE", fontsize=11, fontweight='bold', color='#e74c3c')
    
    # Styling
    ax1.spines['top'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    ax1.spines['bottom'].set_color('#cccccc')
    ax1.tick_params(axis='both', which='both', length=0)
    ax2.tick_params(axis='both', which='both', length=0)
    
    # Grid based on Ax1
    ax1.yaxis.grid(True, linestyle='-', color='#eeeeee', alpha=0.7)
    ax1.set_axisbelow(True)
    
    # Legend
    lines = l1 + l2 + l3 + l4
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.5, -0.15), 
               ncol=4, frameon=False, fontsize=10)
               
    # Add text box with latest values
    latest_date = times[-1].strftime("%d/%m/%Y")
    latest_hose = hose_index[-1]
    latest_vi_the = vi_the[-1]
    latest_ma20 = ma20[-1]
    latest_ma50 = ma50[-1]
    # Use simple text (matplotlib doesn't support emojis well without specific fonts)
    textstr = f"Ngày: {latest_date}\n" \
              f"[MA20]: {latest_ma20:.2f}%\n" \
              f"[MA50]: {latest_ma50:.2f}%\n" \
              f"[Vị thế]: {latest_vi_the:.2f}%\n" \
              f"[HOSE]: {latest_hose:,.2f}"
              
    props = dict(boxstyle='round,pad=0.6', facecolor='#2a2a2a', alpha=0.9, edgecolor='#444444')
    ax1.text(0.02, 0.95, textstr, transform=ax1.transAxes, fontsize=10,
             verticalalignment='top', bbox=props, fontweight='bold', color='white', linespacing=1.6)
    
    plt.title("ĐỊNH VỊ CHU KỲ THỊ TRƯỜNG DÀI HẠN (1 NĂM)", fontsize=14, fontweight='bold', color='#2c3e50', pad=15)
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✅ Đã vẽ biểu đồ và lưu tại: {out_path}")

def draw_sector_table_chart():
    script_dir = Path(__file__).parent.resolve()
    charts_dir = script_dir.parent.parent / "output" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    out_path = charts_dir / "market_sector_table.png"
    
    sectors = fetch_sector_data()
    if not sectors:
        return
        
    # Sort by Val (Giá trị giao dịch) descending
    sectors.sort(key=lambda x: x.get('Val', 0) or 0, reverse=True)
    
    # Define columns
    cols = ["Ngành", "Điểm số", "+/- %", "GTGD (Tỷ)", "NN Mua(Tr)", "NN Bán(Tr)", "1 Tháng", "3 Tháng", "P/E", "P/B"]
    
    cell_text = []
    
    for s in sectors:
        name = s.get('SectorName', '')
        idx = f"{s.get('CloseIndex', 0):.2f}" if s.get('CloseIndex') else "-"
        
        per_change = s.get('PerChange', 0) or 0
        per_change_str = f"{per_change:+.2f}%"
        
        val_ty = (s.get('Val', 0) or 0) / 1e9
        val_str = f"{val_ty:,.0f}"
        
        nn_buy = (s.get('ForeignBuyVol', 0) or 0) / 1e6
        nn_buy_str = f"{nn_buy:,.1f}"
        
        nn_sell = (s.get('ForeignSellVol', 0) or 0) / 1e6
        nn_sell_str = f"{nn_sell:,.1f}"
        
        p1m = s.get('PerChange1M', 0) or 0
        p1m_str = f"{p1m:+.2f}%"
        
        p3m = s.get('PerChange3M', 0) or 0
        p3m_str = f"{p3m:+.2f}%"
        
        pe = f"{s.get('PE', 0) or 0:.1f}"
        pb = f"{s.get('PB', 0) or 0:.1f}"
        
        cell_text.append([name, idx, per_change_str, val_str, nn_buy_str, nn_sell_str, p1m_str, p3m_str, pe, pb])
        
    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor('white')
    ax.axis('off')
    
    table = ax.table(cellText=cell_text, colLabels=cols, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 1.8)
    
    # Customizing colors for Light Theme
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor('#dcdde1')
        if row == 0:
            cell.set_facecolor('#f1f2f6')
            cell.set_text_props(color='#2c3e50', weight='bold')
        else:
            # Alternating row colors for readability
            cell.set_facecolor('white' if row % 2 == 0 else '#fafafa')
            color = '#333333'
            
            # Highlight +/- %
            if col == 2:
                val = (sectors[row-1].get('PerChange', 0) or 0)
                color = '#27ae60' if val > 0 else ('#c0392b' if val < 0 else '#f39c12')
            elif col == 6:
                val = (sectors[row-1].get('PerChange1M', 0) or 0)
                color = '#27ae60' if val > 0 else ('#c0392b' if val < 0 else '#f39c12')
            elif col == 7:
                val = (sectors[row-1].get('PerChange3M', 0) or 0)
                color = '#27ae60' if val > 0 else ('#c0392b' if val < 0 else '#f39c12')
                
            cell.set_text_props(color=color)
            
    # Custom alignments
    for (row, col), cell in table.get_celld().items():
        if row > 0:
            if col == 0: # Name
                cell.get_text().set_horizontalalignment('left')
                # Add left padding by setting x position
                cell.set_text_props(x=0.05)
            elif col in [1, 3, 4, 5, 8, 9]: # Right align numeric
                cell.get_text().set_horizontalalignment('right')
                cell.set_text_props(x=0.95)
                
    plt.title("BẢNG DỮ LIỆU ĐÁNH GIÁ NHÓM NGÀNH TOÀN DIỆN", color='#2c3e50', fontsize=16, fontweight='bold', pad=20)
    fig.tight_layout()
    plt.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight', dpi=150)
    plt.close()
    
    print(f"✅ Đã vẽ bảng dữ liệu và lưu tại: {out_path}")

def draw_valuation_charts():
    script_dir = Path(__file__).parent.resolve()
    charts_dir = script_dir.parent.parent / "output" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    out_path = charts_dir / "market_valuation.png"
    
    url_pe = 'https://api-finfo.vndirect.com.vn/v4/ratios?q=ratioCode:PRICE_TO_EARNINGS~code:VNINDEX~reportDate:gte:2021-07-01&sort=reportDate:desc&size=10000&fields=value,reportDate'
    url_pb = 'https://api-finfo.vndirect.com.vn/v4/ratios?q=ratioCode:PRICE_TO_BOOK~code:VNINDEX~reportDate:gte:2021-07-01&sort=reportDate:desc&size=10000&fields=value,reportDate'
    
    def fetch_data(url):
        try:
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=15).json()
            data = res.get('data', [])
            # data is descending by date (latest first). Reverse to plot left-to-right (past-to-present).
            data = list(reversed(data))
            dates = [datetime.strptime(item['reportDate'], "%Y-%m-%d") for item in data]
            vals = [item['value'] for item in data]
            return dates, vals
        except:
            return [], []
            
    dates_pe, vals_pe = fetch_data(url_pe)
    dates_pb, vals_pb = fetch_data(url_pb)
    
    if not dates_pe or not dates_pb:
        print("❌ Lỗi: Không thể lấy dữ liệu Định giá từ VNDirect.")
        return
        
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.patch.set_facecolor('white')
    
    # 1. Biểu đồ P/E
    ax1.set_facecolor('white')
    ax1.plot(dates_pe, vals_pe, color='#2980b9', linewidth=1.5, label='P/E VN-Index')
    mean_pe = np.mean(vals_pe)
    ax1.axhline(mean_pe, color='#e74c3c', linestyle='--', linewidth=1.5, label=f'Trung bình 3 năm ({mean_pe:.1f})')
    
    # Tô màu khoảng chênh lệch
    ax1.fill_between(dates_pe, vals_pe, mean_pe, where=(np.array(vals_pe) >= mean_pe), facecolor='#e74c3c', alpha=0.1, interpolate=True)
    ax1.fill_between(dates_pe, vals_pe, mean_pe, where=(np.array(vals_pe) < mean_pe), facecolor='#2ecc71', alpha=0.1, interpolate=True)
    
    ax1.set_title("ĐỊNH GIÁ P/E VN-INDEX (TỪ 07/2021)", fontsize=12, fontweight='bold', color='#2c3e50', pad=15)
    ax1.grid(True, color='#eeeeee', linestyle='-', linewidth=1)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_color('#cccccc')
    ax1.spines['bottom'].set_color('#cccccc')
    ax1.tick_params(axis='both', colors='#666666')
    ax1.legend(loc='upper right', frameon=False, labelcolor='#333333')
    
    latest_pe = vals_pe[-1]
    ax1.text(dates_pe[-1], latest_pe, f"  {latest_pe:.2f}", va='center', ha='left', color='#2980b9', fontweight='bold')
    
    import matplotlib.dates as mdates
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%y'))
    
    # 2. Biểu đồ P/B
    ax2.set_facecolor('white')
    ax2.plot(dates_pb, vals_pb, color='#8e44ad', linewidth=1.5, label='P/B VN-Index')
    mean_pb = np.mean(vals_pb)
    ax2.axhline(mean_pb, color='#e74c3c', linestyle='--', linewidth=1.5, label=f'Trung bình 3 năm ({mean_pb:.2f})')
    
    ax2.fill_between(dates_pb, vals_pb, mean_pb, where=(np.array(vals_pb) >= mean_pb), facecolor='#e74c3c', alpha=0.1, interpolate=True)
    ax2.fill_between(dates_pb, vals_pb, mean_pb, where=(np.array(vals_pb) < mean_pb), facecolor='#2ecc71', alpha=0.1, interpolate=True)
    
    ax2.set_title("ĐỊNH GIÁ P/B VN-INDEX (TỪ 07/2021)", fontsize=12, fontweight='bold', color='#2c3e50', pad=15)
    ax2.grid(True, color='#eeeeee', linestyle='-', linewidth=1)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_color('#cccccc')
    ax2.spines['bottom'].set_color('#cccccc')
    ax2.tick_params(axis='both', colors='#666666')
    ax2.legend(loc='upper right', frameon=False, labelcolor='#333333')
    
    latest_pb = vals_pb[-1]
    ax2.text(dates_pb[-1], latest_pb, f"  {latest_pb:.2f}", va='center', ha='left', color='#8e44ad', fontweight='bold')
    
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%y'))
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✅ Đã vẽ biểu đồ và lưu tại: {out_path}")

def draw_top_breakout_stocks_chart():
    script_dir = Path(__file__).parent.resolve()
    charts_dir = script_dir.parent.parent / "output" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    out_path = charts_dir / "market_breakout.png"
    
    symbol_list = "NAG,SRT,FBA,AGF,BAF,VSP,BCE,MSB,G20,PTX,TV3,VFR,VCX,CAB,CT3,DXS,PAN,SDY,TMX,NVL,PNC,PGC,SPH,MLS,LDG,LMI,TGP,GVT,NDC,PEN,PVA,SMT,BII,APT,DPD,TMW,HRT,LO5,QNC,VTA,SZG,L18,KTC,VGP,PEQ,SBD,EMC,SIC,BHN,HGT,VIN,BTB,DLR,SJF,SLS,ICC,BSH,CDR,ICG,APP,BCM,X20,GMC,LIG,EID,UNI,MVC,S72,VTD,BST,USC,VTQ,CPI,VCS,TYA,TSB,TUG,TDT,PBT,BFC,BCP,KPF,VNF,BWE,CDG,VNG,BSL,BAX,VAB,XPH,ABI,TVW,AMS,VPS,FCM,STC,HKP,PAP,CTT,SPB,CTB,BMD,CCV,VPB,MEL,VNI,SAV,MIG,TV1,TOW,CE1,NHP,HPT,BCF,MRF,BAL,CKD,HPW,TDW,HTP,FSO,DVN,TNT,VMC,GH3,VIH,VC3,PVS,RBC,PHR,NTP,MPT,ELC,SVT,DVW,TTA,SMA,CTD,STH,SPM,MWG,G36,PXI,NTW,UDL,OIL,AGX,QTC,PSH,HDP,DPP,TTN,ABR,GIC,CCA,CTS,STP,NDW,NED,TCK,IRC,TVM,HD8,TCB,VC7,CNA,FID,DND,HPG,PMT,BHG,PET,BQB,SJS,DCR,BMP,NSS,BIC,HU3,PMS,SII,UDJ,BIG,HNP,PEG,NBP,KGM,TBT,DCL,PVL,CLW,SGP,BSC,ANV,VMG,THB,MVB,ILC,DTV,NAS,NTH,TMP,RCD,PBC,FOC,VQC,HTE,TPB,HQC,HDM,MKV,MDF,LQN,SAB,TN1,CC4,SGN,CFM,PCC,GER,HRC,IDC,TBD,TSJ,TAW,SVG,NDN,PID,HLB,EMG,ACS,CTC,MTL,PCN,QNT,FHN,NBW,BHC,TST,VDB,PNT,TKC,CKV,SZC,C47,HTI,SSB,VCW,BID,SEB,ADC,VCM,VTL,VNM,CDO,EPC,VOS,GIL,TVG,VTG,SGS,DP3,SWC,VCR,TKU,KHW,AMD,VSE,VIE,HHR,DDV,LEC,NJC,SD4,CSI,DPM,VNS,DAH,VLW,ICI,GKM,DC1,BMV,SHA,HHS,GLT,NGC,HOT,SD3,SDP,VHC,DNN,VXT,SJE,UIC,HSP,E12,PIT,HHN,VSA,VC1,MEF,NNT,JOS,X26,PJC,TNH,PGS,WSS,TC6,A32,VRG,CLG,TRS,TDF,TTH,SVI,TJC,NST,CMF,NSL,MCI,MBB,PVP,DPR,CRC,CBS,PMW,VTV,TL4,PVG,PXC,CSM,ABC,BCG,ATS,SCO,CHP,CQT,EIN,GCB,FMC,SBR,HU6,SHB,SGD,GAB,DMN,BVS,AFX,VDS,DSD,SJG,TKA,VGR,VSM,HBD,VOC,DGC,V12,VIW,NAC,SBA,CPH,GTT,TNA,THS,DIG,VTP,NT2,PMJ,DLG,TDB,IBN,CLM,KLF,PGV,SEP,QLT,VLA,NDF,CAG,GVR,TR1,PLC,TAG,LKW,SVC,SDA,SKV,JVC,PVV,NXT,ACE,DS3,PVB,KHP,GDT,LHG,HPD,LPT,IBD,RTB,DHT,TTF,DC2,SZE,VHG,HPX,CVP,GMA,PSI,GEX,ASG,GMX,VNC,LIX,NAB,SAF,DCM,TVH,TIE,CRE,MBS,BEL,BAB,SGR,VNL,ICN,XLV,HDA,ADS,SKN,MCH,HMG,BDB,KKC,HJS,HES,MSH,HHV,THG,BVB,PHS,AIC,VNA,MGR,MGG,EIB,HEJ,BBT,SBL,NHH,VPI,HCD,VE4,SBH,THW,HUB,PVD,TVC,STW,VUA,ACV,ILA,CPC,TDH,L44,UMC,CLL,CDP,KTS,DHP,WTC,PSL,BKC,VSF,STT,HHC,MDC,PSG,ACG,BCA,CMK,SCC,VCA,IPA,QNU,D11,HEC,HDB,BTT,CTG,SKH,DCF,MCF,LGM,PNP,DCS,THN,HDO,MED,ICF,OPC,VAF,H11,TMS,LWS,BXH,BED,GND,GEE,ISG,DHN,FOX,POS,PVY,VID,RCC,IST,HII,KSH,FRC,NQN,LCD,VGC,VEF,VBG,ACL,BSI,SAL,HSG,SDN,NWT,VSC,SVH,HAR,CQN,BBS,ISH,WCS,HLG,TTT,VCE,HCB,TVP,NHA,BTH,VW3,BBC,HGM,BSA,HRB,HND,EVG,VEA,XHC,ITC,STL,PGB,MLC,XMD,DAE,PLX,C69,VCP,VCB,VFC,SPC,NTT,QCC,SD1,PIC,GE2,HDW,SIG,PGT,VRC,L62,PVM,DP1,DXV,PVX,PHC,FCS,AAA,CTN,SMN,QHW,TCH,SHI,SPP,FT1,EME,PDC,HBH,BLF,SSN,TLH,CCT,TTZ,EBS,IDI,CLH,BT1,NHC,PPT,BTV,APL,DSC,MST,CI5,DSP,BDT,WSB,CAV,TH1,DID,PAT,PEC,DTL,TCW,TTB,QSP,ABT,BRS,AAM,DSV,FPT,COM,VIC,MH3,MQN,FBC,VAV,VNT,DCG,TVS,BMC,SBS,VNR,TLD,SDU,NCT,AAS,AGE,BLN,APH,L45,AME,BSQ,CMN,LMC,AAT,VLP,HTC,TDN,SFN,BSR,B82,FRM,KHS,BCV,UDC,VIX,GTA,VCT,VVN,THI,SD9,SED,DBC,PSB,KDM,TMC,FUEIP100,FUESSVFL,FUCTVGF4,FUEKIVFS,GPC,BHI,SBG,KTW,QNP,DSE,MTX,MZG,DKW,VPL,SLD,HHB,VPX,VLS,VCK,ALC,KHX,DCV,CCS,STD,GEL,HPA,UPS,VBT,CLI,GDH,AAN,NHD,ANI"
    url = f"https://mastrade.masvn.com/api/v1/market/symbolLatest?symbolList={symbol_list}"
    
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=15).json()
    except Exception as e:
        print("❌ Lỗi: Không thể lấy dữ liệu symbolLatest từ Mastrade.")
        return
        
    valid_stocks = []
    for item in res:
        # vo = volume, av20 = avg volume 20 days, r = percent change
        if not all(k in item and item[k] is not None for k in ['s', 'vo', 'av20', 'r']):
            continue
            
        vo = item['vo']
        av20 = item['av20']
        pct_change = item['r']
        
        # Tiêu chí: Volume hiện tại > 100k, giá phải tăng > 0, av20 > 0
        if vo >= 100000 and av20 > 0 and pct_change > 0:
            breakout_ratio = vo / av20
            score = breakout_ratio * pct_change # Kết hợp cả 2 yếu tố
            valid_stocks.append({
                'symbol': item['s'],
                'breakout_ratio': breakout_ratio,
                'pct_change': pct_change,
                'score': score
            })
            
    if not valid_stocks:
        print("❌ Lỗi: Không tìm thấy cổ phiếu nào thoả mãn tiêu chí.")
        return
        
    # Sort by score descending and pick top 10
    valid_stocks.sort(key=lambda x: x['score'], reverse=True)
    top10 = valid_stocks[:10]
    
    # Sort ascending for horizontal bar chart
    top10.sort(key=lambda x: x['score'])
    
    labels = [f"{s['symbol']} (+{s['pct_change']:.1f}%)" for s in top10]
    ratios = [s['breakout_ratio'] for s in top10]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    bars = ax.barh(labels, ratios, color='#3498db', height=0.6)
    
    # Minimalist style
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    
    ax.tick_params(axis='y', colors='#2c3e50', length=0, labelsize=11)
    ax.tick_params(axis='x', colors='#7f8c8d', labelsize=10)
    ax.xaxis.grid(True, color='#ecf0f1', linestyle='-', linewidth=1)
    ax.set_axisbelow(True)
    
    for bar, val in zip(bars, ratios):
        ax.text(val + 0.1, bar.get_y() + bar.get_height()/2, 
                f"{val:.1f}x", 
                va='center', ha='left', fontsize=11, fontweight='bold', color='#2980b9')
                
    plt.title("TOP 10 CỔ PHIẾU ĐỘT BIẾN KHỐI LƯỢNG", 
              fontsize=14, fontweight='bold', color='#2c3e50', pad=20)
              
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✅ Đã vẽ biểu đồ và lưu tại: {out_path}")

def draw_stock_contribution_chart():
    script_dir = Path(__file__).parent.resolve()
    charts_dir = script_dir.parent.parent / "output" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    out_path = charts_dir / "stock_contrib.png"
    
    url = "https://mkw-socket-v2.vndirect.com.vn/mkwsocketv2/leaderlarger?index=VNINDEX"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=15).json()
        data = res.get('data', []) if isinstance(res, dict) else res
    except Exception as e:
        print("❌ Lỗi: Không thể lấy dữ liệu leaderlarger từ VNDirect.")
        return
        
    if not data:
        return
        
    valid_stocks = [s for s in data if s.get('point') is not None]
    valid_stocks.sort(key=lambda x: x['point'], reverse=True)
    
    if len(valid_stocks) > 20:
        top_positive = [s for s in valid_stocks if s['point'] > 0][:10]
        top_negative = [s for s in valid_stocks if s['point'] < 0][-10:]
        selected = top_positive + top_negative
    else:
        selected = valid_stocks
        
    if not selected:
        return
        
    selected.sort(key=lambda x: x['point']) # Sort for barh (bottom to top)
    
    tickers = [s['symbol'] for s in selected]
    points = [s['point'] for s in selected]
    
    colors = ['#27ae60' if p >= 0 else '#c0392b' for p in points]
    
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    bars = ax.barh(tickers, points, color=colors, height=0.7)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    
    ax.tick_params(axis='y', colors='#333333', length=0, labelsize=11)
    ax.tick_params(axis='x', colors='#666666', labelsize=10)
    ax.xaxis.grid(True, color='#eeeeee', linestyle='-', linewidth=1)
    ax.set_axisbelow(True)
    
    ax.axvline(0, color='#f39c12', linewidth=1.5, zorder=3)
    
    for bar, val in zip(bars, points):
        x_offset = 0.05 if val >= 0 else -0.05
        ha = 'left' if val >= 0 else 'right'
        text_color = '#27ae60' if val >= 0 else '#c0392b'
        ax.text(val + x_offset, bar.get_y() + bar.get_height()/2, 
                f"{val:+.2f}", 
                va='center', ha=ha, fontsize=10, fontweight='bold', color=text_color)
                
    plt.title("TOP CỔ PHIẾU ĐÓNG GÓP VN-INDEX", 
              fontsize=14, fontweight='bold', color='#2c3e50', pad=20)
              
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✅ Đã vẽ biểu đồ và lưu tại: {out_path}")

def draw_vnindex_intraday_chart():
    import matplotlib.dates as mdates
    script_dir = Path(__file__).parent.resolve()
    charts_dir = script_dir.parent.parent / "output" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    out_path = charts_dir / "vnindex_intraday.png"
    
    # 1. Lấy dữ liệu Reference
    url_info = "https://mastrade.masvn.com/api/v1/market/symbolLatest?symbolList=VN-INDEX"
    ref_price = 0
    try:
        res_info = requests.get(url_info, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=15).json()
        if res_info:
            c = res_info[0].get('c', 0)
            ch = res_info[0].get('ch', 0)
            ref_price = c - ch
    except Exception:
        pass
        
    # 2. Lấy dữ liệu MinuteChart
    url = "https://mastrade.masvn.com/api/v1/market/minuteChart?symbol=VN-INDEX"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=15).json()
    except Exception as e:
        print("❌ Lỗi: Không thể lấy dữ liệu minuteChart từ Mastrade.")
        return
        
    if not res or 't' not in res or 'c' not in res:
        return
        
    times_sec = res['t']
    prices = res['c']
    
    if not times_sec or not prices:
        return
        
    if ref_price == 0:
        ref_price = prices[0] # Fallback
        
    from datetime import timezone
    times = [datetime.fromtimestamp(t, timezone.utc) + timedelta(hours=7) for t in times_sec]
    
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    # Plot line
    line = ax.plot(times, prices, color='#2c3e50', linewidth=2)
    
    # Fill between
    ax.fill_between(times, prices, ref_price, where=[p >= ref_price for p in prices], 
                    interpolate=True, color='#2ecc71', alpha=0.3)
    ax.fill_between(times, prices, ref_price, where=[p < ref_price for p in prices], 
                    interpolate=True, color='#e74c3c', alpha=0.3)
                    
    # Plot Reference Line
    ax.axhline(ref_price, color='#f39c12', linestyle='--', linewidth=1.5, zorder=2)
    
    # Minimalist style
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('#bdc3c7')
    
    ax.tick_params(axis='y', colors='#2c3e50', length=0, labelsize=10)
    ax.tick_params(axis='x', colors='#7f8c8d', labelsize=10)
    ax.yaxis.grid(True, color='#ecf0f1', linestyle='-', linewidth=1)
    ax.set_axisbelow(True)
    
    # Format x-axis as HH:MM
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    current_close = prices[-1]
    pct = (current_close - ref_price) / ref_price * 100
    sign = "+" if pct >= 0 else ""
    
    plt.title(f"NHỊP ĐẬP VN-INDEX ({current_close:.2f} | {sign}{pct:.2f}%)", 
              fontsize=14, fontweight='bold', color='#2c3e50', pad=20)
              
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✅ Đã vẽ biểu đồ và lưu tại: {out_path}")

def draw_sector_intraday_charts():
    from datetime import timezone
    import matplotlib.dates as mdates
    
    script_dir = Path(__file__).parent.resolve()
    charts_dir = script_dir.parent.parent / "output" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    out_path = charts_dir / "sector_intraday.png"
    
    sectors = [
        ("VNFIN", "TÀI CHÍNH"),
        ("VNREAL", "BẤT ĐỘNG SẢN"),
        ("VNMAT", "VẬT LIỆU XÂY DỰNG"),
        ("VNIND", "CÔNG NGHIỆP"),
        ("VNCONS", "TIÊU DÙNG THIẾT YẾU"),
        ("VNCOND", "TD KHÔNG THIẾT YẾU"),
        ("VNHEAL", "Y TẾ"),
        ("VNENE", "NĂNG LƯỢNG"),
        ("VNUTI", "TIỆN ÍCH"),
        ("VNIT", "CN THÔNG TIN")
    ]
    
    fig, axes = plt.subplots(4, 3, figsize=(16, 16))
    fig.patch.set_facecolor('white')
    
    axes = axes.flatten()
    
    for i, (sym, name) in enumerate(sectors):
        ax = axes[i]
        
        url = f"https://mastrade.masvn.com/api/v1/market/minuteChart?symbol={sym}"
        try:
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=15).json()
        except Exception:
            res = {}
            
        if not res or 't' not in res or 'c' not in res:
            ax.axis('off')
            continue
            
        times_sec = res['t']
        prices = res['c']
        
        if not times_sec or not prices:
            ax.axis('off')
            continue
            
        ref_price = prices[0]
        # Thử fetch symbolLatest để lấy tham chiếu chuẩn
        try:
            url_info = f"https://mastrade.masvn.com/api/v1/market/symbolLatest?symbolList={sym}"
            res_info = requests.get(url_info, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=15).json()
            if res_info:
                c = res_info[0].get('c', 0)
                ch = res_info[0].get('ch', 0)
                if c > 0:
                    ref_price = c - ch
        except Exception:
            pass
            
        times = [datetime.fromtimestamp(t, timezone.utc) + timedelta(hours=7) for t in times_sec]
        
        ax.set_facecolor('white')
        ax.plot(times, prices, color='#2c3e50', linewidth=1.5)
        
        ax.fill_between(times, prices, ref_price, where=[p >= ref_price for p in prices], 
                        interpolate=True, color='#2ecc71', alpha=0.3)
        ax.fill_between(times, prices, ref_price, where=[p < ref_price for p in prices], 
                        interpolate=True, color='#e74c3c', alpha=0.3)
                        
        ax.axhline(ref_price, color='#f39c12', linestyle='--', linewidth=1, zorder=2)
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('#bdc3c7')
        
        ax.tick_params(axis='y', colors='#2c3e50', length=0, labelsize=9)
        ax.tick_params(axis='x', colors='#7f8c8d', labelsize=9)
        ax.yaxis.grid(True, color='#ecf0f1', linestyle='-', linewidth=1)
        ax.set_axisbelow(True)
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator())
        
        current_close = prices[-1]
        pct = (current_close - ref_price) / ref_price * 100 if ref_price > 0 else 0
        sign = "+" if pct >= 0 else ""
        color = '#27ae60' if pct >= 0 else '#c0392b'
        
        ax.set_title(f"{name} ({sign}{pct:.1f}%)", fontsize=12, fontweight='bold', color=color, pad=10)
        
    # Hide empty subplots
    for j in range(len(sectors), len(axes)):
        axes[j].axis('off')
        
    plt.tight_layout(pad=3.0)
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✅ Đã vẽ biểu đồ và lưu tại: {out_path}")

def draw_global_markets_chart():
    from datetime import timezone
    import matplotlib.dates as mdates
    
    script_dir = Path(__file__).parent.resolve()
    charts_dir = script_dir.parent.parent / "output" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    out_path = charts_dir / "global_markets.png"
    
    symbols = [
        ("^DJI", "DOW JONES"),
        ("^GSPC", "S&P 500"),
        ("^N225", "NIKKEI 225"),
        ("^KS11", "KOSPI"),
        ("GC=F", "VÀNG (GOLD)"),
        ("CL=F", "DẦU (WTI CRUDE)"),
        ("BTC-USD", "BITCOIN"),
        ("ETH-USD", "ETHEREUM"),
        ("DX-Y.NYB", "DXY (US DOLLAR)"),
        ("^TNX", "US 10Y BOND"),
        ("DRAM", "MEMORY ETF")
    ]
    
    url_template = 'https://query1.finance.yahoo.com/v8/finance/chart/{}?interval=1d&range=3mo'
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    fig, axes = plt.subplots(3, 4, figsize=(18, 12))
    fig.patch.set_facecolor('white')
    axes = axes.flatten()
    
    for i, (sym, name) in enumerate(symbols):
        ax = axes[i]
        try:
            r = requests.get(url_template.format(sym), headers=headers, verify=False, timeout=15)
            if r.status_code == 200:
                data = r.json()
                result = data['chart']['result'][0]
                timestamps = result['timestamp']
                quotes = result['indicators']['quote'][0]
                close_prices = quotes['close']
                
                valid_data = [(t, p) for t, p in zip(timestamps, close_prices) if p is not None]
                if not valid_data:
                    ax.axis('off')
                    continue
                    
                times_sec = [x[0] for x in valid_data]
                prices = [x[1] for x in valid_data]
                
                if len(prices) > 1:
                    last_price = prices[-1]
                    prev_price = prices[-2]
                    pct_change = (last_price - prev_price) / prev_price * 100
                else:
                    last_price = prices[0]
                    pct_change = 0
                    
                times = [datetime.fromtimestamp(t, timezone.utc) for t in times_sec]
                
                ax.set_facecolor('white')
                trend_color = '#27ae60' if prices[-1] >= prices[0] else '#c0392b'
                ax.plot(times, prices, color=trend_color, linewidth=2)
                
                ax.fill_between(times, prices, min(prices) - (max(prices)-min(prices))*0.1, 
                                color=trend_color, alpha=0.1)
                
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_visible(False)
                ax.spines['bottom'].set_color('#bdc3c7')
                
                ax.tick_params(axis='y', colors='#2c3e50', length=0, labelsize=9)
                ax.tick_params(axis='x', colors='#7f8c8d', labelsize=9)
                ax.yaxis.grid(True, color='#ecf0f1', linestyle='-', linewidth=1)
                ax.set_axisbelow(True)
                
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
                ax.xaxis.set_major_locator(mdates.MonthLocator())
                
                sign = "+" if pct_change >= 0 else ""
                day_color = '#27ae60' if pct_change >= 0 else '#c0392b'
                
                if sym in ["GC=F", "CL=F", "BTC-USD", "ETH-USD", "DRAM"]:
                    price_str = f"${last_price:,.2f}"
                elif sym == "^TNX":
                    price_str = f"{last_price:,.3f}%"
                else:
                    price_str = f"{last_price:,.2f}"
                    
                ax.set_title(f"{name}\n{price_str} ({sign}{pct_change:.2f}%)", 
                             fontsize=11, fontweight='bold', color=day_color, pad=8)
            else:
                ax.axis('off')
        except Exception as e:
            print(f"Lỗi khi lấy {sym}: {e}")
            ax.axis('off')
            
    for j in range(len(symbols), len(axes)):
        axes[j].axis('off')
            
    plt.tight_layout(pad=3.0)
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✅ Đã vẽ biểu đồ và lưu tại: {out_path}")

def draw_institutional_flow_charts():
    from datetime import datetime, timedelta
    
    script_dir = Path(__file__).parent.resolve()
    charts_dir = script_dir.parent.parent / "output" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    out_path = charts_dir / "institutional_flow.png"
    
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(24, 6))
    fig.patch.set_facecolor('white')
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 1. Khối Ngoại (Top 10 Buy/Sell - VNDirect API)
    # Tìm ngày giao dịch gần nhất có dữ liệu
    today = datetime.now()
    foreign_data = []
    for i in range(5): # Thử lùi lại tối đa 5 ngày
        test_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        url = f'https://api-finfo.vndirect.com.vn/v4/foreigns?q=tradingDate:{test_date}~floor:UPCOM,HNX,HOSE~type:STOCK,IFC,ETF&size=10000'
        try:
            r = requests.get(url, headers=headers, verify=False, timeout=15)
            if r.status_code == 200:
                data = r.json().get('data', [])
                if len(data) > 0:
                    foreign_data = data
                    break
        except Exception:
            pass
            
    ax1.set_facecolor('white')
    
    if foreign_data:
        # data format: {"code": "SSI", "netVal": 5000000000.0, ...}
        # Tính tổng mua ròng toàn thị trường
        total_net_val = sum(item.get('netVal', 0) for item in foreign_data)
        total_net_bil = total_net_val / 1e9
        
        # Sắp xếp theo netVal giảm dần
        sorted_data = sorted(foreign_data, key=lambda x: x.get('netVal', 0), reverse=True)
        
        # Top 10 Mua Ròng
        top_buy = sorted_data[:10]
        # Top 10 Bán Ròng (Lấy từ cuối mảng lên)
        top_sell = sorted_data[-10:]
        top_sell.reverse() # Để mã bán mạnh nhất lên đầu
        
        # Vẽ Diverging Bar Chart
        y_pos = np.arange(10, 0, -1)
        
        buy_codes = [item.get('code', '') for item in top_buy]
        buy_vals = [item.get('netVal', 0) / 1e9 for item in top_buy]
        
        sell_codes = [item.get('code', '') for item in top_sell]
        sell_vals = [abs(item.get('netVal', 0)) / 1e9 for item in top_sell]
        
        ax1.barh(y_pos, buy_vals, color='#27ae60', height=0.6, align='center', label='Mua Ròng')
        ax1.barh(y_pos, [-v for v in sell_vals], color='#c0392b', height=0.6, align='center', label='Bán Ròng')
        
        for i, (code, val) in enumerate(zip(buy_codes, buy_vals)):
            if val > 0:
                ax1.text(val + max(buy_vals)*0.02, y_pos[i], f"{code} ({val:.0f})", va='center', ha='left', fontsize=9, color='#2c3e50', fontweight='bold')
                
        for i, (code, val) in enumerate(zip(sell_codes, sell_vals)):
            if val > 0:
                ax1.text(-val - max(sell_vals)*0.02, y_pos[i], f"({val:.0f}) {code}", va='center', ha='right', fontsize=9, color='#2c3e50', fontweight='bold')
        
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.spines['left'].set_visible(False)
        ax1.spines['bottom'].set_visible(False)
        ax1.set_yticks([])
        ax1.set_xticks([])
        ax1.axvline(0, color='#95a5a6', linewidth=1)
        
        net_sign = "+" if total_net_bil >= 0 else ""
        net_color = '#27ae60' if total_net_bil >= 0 else '#c0392b'
        ax1.set_title(f"TOP GIAO DỊCH KHỐI NGOẠI\nTổng: {net_sign}{total_net_bil:,.0f} Tỷ VNĐ", 
                     fontsize=14, fontweight='bold', color=net_color, pad=15)
    else:
        ax1.axis('off')
        ax1.text(0.5, 0.5, "Không có dữ liệu Khối Ngoại", ha='center', va='center')
    
    # 2. Khối Ngoại (10 phiên gần nhất)
    foreign_dates = []
    foreign_net = []
    count_f = 0
    for i in range(25):
        test_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        url_f = f'https://api-finfo.vndirect.com.vn/v4/foreigns?q=tradingDate:{test_date}~floor:UPCOM,HNX,HOSE~type:STOCK,IFC,ETF&size=10000'
        try:
            r = requests.get(url_f, headers=headers, verify=False, timeout=15)
            if r.status_code == 200:
                data_f = r.json().get('data', [])
                if data_f:
                    total_net = sum(item.get('netVal', 0) for item in data_f) / 1e9
                    date_obj = datetime.strptime(test_date, "%Y-%m-%d")
                    foreign_dates.append(date_obj.strftime("%d/%m"))
                    foreign_net.append(total_net)
                    count_f += 1
                    if count_f >= 10:
                        break
        except Exception:
            pass
            
    foreign_dates.reverse()
    foreign_net.reverse()
    
    ax2.set_facecolor('white')
    ax2.set_title("KHỐI NGOẠI (10 PHIÊN GẦN NHẤT)", fontsize=14, fontweight='bold', color='#2c3e50', pad=20)
    
    if foreign_dates:
        colors_f = ['#27ae60' if val >= 0 else '#c0392b' for val in foreign_net]
        bars_f = ax2.bar(foreign_dates, foreign_net, color=colors_f, width=0.6)
        
        for bar, val in zip(bars_f, foreign_net):
            yval = bar.get_height()
            offset = max(abs(max(foreign_net)), abs(min(foreign_net))) * 0.05
            if val >= 0:
                ax2.text(bar.get_x() + bar.get_width()/2.0, yval + offset, f"{val:.0f}", ha='center', va='bottom', fontsize=10, fontweight='bold', color='#27ae60')
            else:
                ax2.text(bar.get_x() + bar.get_width()/2.0, yval - offset, f"{val:.0f}", ha='center', va='top', fontsize=10, fontweight='bold', color='#c0392b')
                
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_visible(False)
        ax2.spines['bottom'].set_color('#bdc3c7')
        
        ax2.tick_params(axis='y', colors='#2c3e50', length=0, labelsize=10)
        ax2.tick_params(axis='x', colors='#7f8c8d', labelsize=10)
        ax2.yaxis.grid(True, color='#ecf0f1', linestyle='-', linewidth=1)
        ax2.set_axisbelow(True)
        ax2.set_ylabel("Mua/Bán Ròng (Tỷ VNĐ)", color='#7f8c8d', fontsize=10)
    else:
        ax2.axis('off')
        ax2.text(0.5, 0.5, "Không có dữ liệu", ha='center', va='center')
        
    # 3. Tự Doanh (10 phiên gần nhất)
    today = datetime.now()
    past = today - timedelta(days=20)
    to_str = today.strftime("%Y%m%d")
    from_str = past.strftime("%Y%m%d")
    
    prop_url = f'https://mastrade.masvn.com/api/v1/proprietaryHistory?to={to_str}&from={from_str}&sortBy=1&sortType=0'
    
    prop_dates = []
    prop_net = []
    
    try:
        r_p = requests.get(prop_url, headers=headers, verify=False, timeout=15)
        if r_p.status_code == 200:
            data = r_p.json().get('data', [])
            data = sorted(data, key=lambda x: x['date'])
            data = data[-10:]
            
            for item in data:
                date_obj = datetime.strptime(item['date'], "%Y%m%d")
                prop_dates.append(date_obj.strftime("%d/%m"))
                prop_net.append(item['nval'] / 1000)
    except Exception as e:
        print("Lỗi lấy dữ liệu Tự doanh:", e)
        
    ax3.set_facecolor('white')
    ax3.set_title("TỰ DOANH (10 PHIÊN GẦN NHẤT)", fontsize=14, fontweight='bold', color='#2c3e50', pad=20)
    
    if prop_dates:
        colors = ['#27ae60' if val >= 0 else '#c0392b' for val in prop_net]
        bars = ax3.bar(prop_dates, prop_net, color=colors, width=0.6)
        
        for bar, val in zip(bars, prop_net):
            yval = bar.get_height()
            offset = max(abs(max(prop_net)), abs(min(prop_net))) * 0.05
            if val >= 0:
                ax3.text(bar.get_x() + bar.get_width()/2.0, yval + offset, f"{val:.0f}", ha='center', va='bottom', fontsize=10, fontweight='bold', color='#27ae60')
            else:
                ax3.text(bar.get_x() + bar.get_width()/2.0, yval - offset, f"{val:.0f}", ha='center', va='top', fontsize=10, fontweight='bold', color='#c0392b')
                
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False)
        ax3.spines['left'].set_visible(False)
        ax3.spines['bottom'].set_color('#bdc3c7')
        
        ax3.tick_params(axis='y', colors='#2c3e50', length=0, labelsize=10)
        ax3.tick_params(axis='x', colors='#7f8c8d', labelsize=10)
        ax3.yaxis.grid(True, color='#ecf0f1', linestyle='-', linewidth=1)
        ax3.set_axisbelow(True)
        ax3.set_ylabel("Mua/Bán Ròng (Tỷ VNĐ)", color='#7f8c8d', fontsize=10)
    else:
        ax3.axis('off')
        ax3.text(0.5, 0.5, "Không có dữ liệu", ha='center', va='center')
        
    plt.tight_layout(pad=3.0)
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✅ Đã vẽ biểu đồ dòng tiền tổ chức và lưu tại: {out_path}")

if __name__ == "__main__":
    draw_vnindex_intraday_chart()
    draw_market_contribution_chart()
    draw_market_breadth_chart()
    draw_market_breadth_area_chart()
    draw_liquidity_chart()
    draw_position_oscillator_chart()
    draw_sector_table_chart()
    draw_valuation_charts()
    draw_top_breakout_stocks_chart()
    draw_stock_contribution_chart()
    draw_sector_intraday_charts()
    draw_global_markets_chart()
    draw_institutional_flow_charts()
