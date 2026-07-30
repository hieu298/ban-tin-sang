import requests

queries = [
    'query{vsForeignHistory(range:"1M"){Date,NetBuyVal}}',
    'query{vsForeignHistory(range:"1M"){date,netBuyVal}}',
    'query{vsForeign(range:"1M"){Date,NetBuyVal}}',
    'query{vsForeignHistory{Date,NetBuyVal}}'
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
            print('FAILED:', q, r.status_code)
    except Exception as e:
        pass
