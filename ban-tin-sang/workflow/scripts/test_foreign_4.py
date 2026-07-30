import requests

queries = [
    'query{vsForeignHistory(StockCode:"VNINDEX",FromDate:"20260601",ToDate:"20260701"){TradingDate,NetBuyVal}}',
    'query{vsForeignHistory(StockCode:"VNINDEX",FromDate:"20260601",ToDate:"20260701"){Date,NetBuyVal}}',
    'query{vsForeignHistory(StockCode:"VNINDEX",FromDate:"20260601",ToDate:"20260701"){TradingDate,BuyVal,SellVal}}',
    'query{vsForeignTotalHistory(StockCode:"VNINDEX",FromDate:"20260601",ToDate:"20260701"){TradingDate,NetBuyVal}}',
    'query{vsForeignHistory(StockCode:"VNINDEX",FromDate:"20260601",ToDate:"20260701"){TradingDate}}'
]
headers = {'User-Agent': 'Mozilla/5.0'}

for q in queries:
    q_encoded = q.replace('"', '%22')
    url = f'https://mastrade.masvn.com/api/v2/vs/foreignHistory?query={q_encoded}'
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            print('SUCCESS:', q, r.text[:100])
        else:
            print('FAILED:', q, r.status_code, r.text[:200])
    except Exception as e:
        pass
