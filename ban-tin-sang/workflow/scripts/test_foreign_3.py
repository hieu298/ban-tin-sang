import requests

query = 'query{vsForeignTotal(range:"1D"){BuyVal,SellVal,NetBuyVal,BuyVol,SellVol,NetBuyVol}}'
q_encoded = query.replace('"', '%22')
url = f'https://mastrade.masvn.com/api/v2/vs/foreignHistory?query={q_encoded}'
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
print('Status:', r.status_code)
print('Response:', r.text)
