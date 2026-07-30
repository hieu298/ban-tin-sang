import requests

query = 'query{vsForeignHistory1M{TradingDate,BuyVal,SellVal,NetBuyVal}}'
q_encoded = query.replace('"', '%22')
url = f'https://mastrade.masvn.com/api/v2/vs/foreignHistory?query={q_encoded}'
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
print('Status:', r.status_code)
print('Response:', r.text[:300])
