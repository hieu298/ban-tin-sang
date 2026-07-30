import requests

queries = [
    'query{vsForeignTotal(range:"1M"){NetBuyVal}}',
    'query{vsForeignHistory(FromDate:"20260601",ToDate:"20260701"){Date,NetBuyVal}}',
    'query{vsForeignTotalHistory(FromDate:"20260601",ToDate:"20260701"){Date,NetBuyVal}}',
    'query{vsForeignHistory(StockCode:"VNINDEX",FromDate:"20260601",ToDate:"20260701"){Date,NetBuyVal}}'
]
headers = {'User-Agent': 'Mozilla/5.0'}

for q in queries:
    q_encoded = q.replace('"', '%22')
    url = f'https://mastrade.masvn.com/api/v2/vs/foreignHistory?query={q_encoded}'
    print('Testing:', q_encoded)
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            print('SUCCESS:', r.text[:200])
        else:
            print('FAILED:', r.status_code)
    except Exception as e:
        print('Error:', e)
