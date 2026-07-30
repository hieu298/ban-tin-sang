import requests
import re

url = 'https://mastrade.masvn.com/market/market-watch'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

try:
    print("Fetching HTML...")
    html = requests.get(url, headers=headers).text
    
    # Find js files
    js_files = re.findall(r'src=["\']([^"\']+\.js)["\']', html)
    print('Found JS files:', js_files)
    
    # Combine HTML and all JS content to search for API endpoints
    content = html
    for js in js_files:
        if not js.startswith('http'):
            js_url = 'https://mastrade.masvn.com' + (js if js.startswith('/') else '/' + js)
        else:
            js_url = js
            
        print(f"Fetching JS: {js_url}")
        try:
            content += requests.get(js_url, headers=headers).text
        except Exception as e:
            print(f"Failed to fetch {js_url}: {e}")
            
    print("\n--- EXTRACTED APIS ---")
    apis = re.findall(r'(\/api\/(?:v[1-2]\/)?market\/[a-zA-Z0-9\/\-\_]+)', content)
    unique_apis = sorted(list(set(apis)))
    for api in unique_apis:
        print(api)
        
except Exception as e:
    print('Error:', e)
