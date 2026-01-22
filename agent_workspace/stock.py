import json
import urllib.request

def get_stock_price():
    url = 'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=demo'
    req = urllib.request.Request(url)
    response = urllib.request.urlopen(req)
    data = response.read()
    json_data = json.loads(data)
    price = json_data['Global Quote']['05. price']
    return price

print(get_stock_price())