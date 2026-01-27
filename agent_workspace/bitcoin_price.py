import requests
import json

data = requests.get('https://api.coindesk.com/v1/bpi/currentprice.json').json()
bitcoin_price = data['bpi']['USD']['rate']
print(bitcoin_price)

with open('bitcoin_price.txt', 'w') as f:
    f.write(bitcoin_price)