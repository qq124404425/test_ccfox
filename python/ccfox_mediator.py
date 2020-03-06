#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
CoinPark通用协议,使用Python2.7
运行地址：http://127.0.0.1:6667，端口可指定
由于账户没资产，未作详细测试，欢迎反馈Bug
QQ:1051804485
反馈地址：https://www.botvs.com/bbs-topic/1963
2018.6.26 15:57 更新，修改了Bug
可以把通用协议当成普通机器人，运行在BotVs模拟盘即可，不收取费用
为了使用IO函数，需要重载exchange里的rpc方法，js的例子如下：
exchange.rpc = function(path, obj) {
    return exchange.IO("api","POST", path, "obj="+escape(JSON.stringify(obj)));
}
function main() {
	Log(exchange.rpc("/transfer", {cmd: "transfer/assets", body: {select:1}}));
}
'''

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import json
import urllib
import urllib2
import time
import hmac
import hashlib
import random
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from ccfox import ccfoxClient

def httpDo(url, verb, data, api_key, api_secret):
    expires = int(round(time.time()) + 5)
    
    signature = generate_signature(api_secret, verb, url, expires, data)
    
    headers = {'content-type':'application/json',\
              'apiExpires':expires,\
              'apiKey':api_key,\
              'signature':signature}
    
    base_url = "https://api.ccfox.com"
    url = base_url + url
    
    req = urllib2.Request(url,headers=headers)
    response = urllib2.urlopen(req)
    return json.loads(response.read())

def getsign(data,secret):
    result = hmac.new(secret.encode("utf-8"), data.encode("utf-8"), hashlib.md5).hexdigest()
    return result

def httpPostWithSign(url, cmds, api_key, api_secret):
    headers = {'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'}
    s_cmds = json.dumps(cmds)
    sign = getsign(s_cmds,api_secret)
    req = urllib2.Request(url, urllib.urlencode({'cmds': s_cmds, 'apikey': api_key,'sign':sign}), headers=headers)
    response = urllib2.urlopen(req)
    return json.loads(response.read())

# 签名是 HMAC_SHA256(secret, verb + path + expires + data)，十六进制编码。
# verb 必须是大写的，url 是相对的，expires 必须是 unix 时间戳（以秒为单位）
# 并且数据（如果存在的话）必须是 JSON 格式，并且键值之间没有空格。
def generate_signature(secret, verb, url, expires, data):
    """Generate a request signature compatible with cloud."""
    # 解析该 url 来移除基础地址而得到 path
    parsedURL = urlparse(url)
    path = parsedURL.path
    if parsedURL.query:
        path = path + '?' + parsedURL.query

    if isinstance(data, (bytes, bytearray)):
        data = data.decode('utf8')
    
    print("Computing HMAC: %s" % verb + path + str(expires) + data)
    message = verb + path + str(expires) + data

    signature = hmac.new(bytes(secret, 'utf8'), bytes(message, 'utf8'), digestmod=hashlib.sha256).hexdigest()
    return signature

class MyExchange:

    market_url = "https://api.ccfox.com"
    trade_url = "https://api.ccfox.com"
    kline_period = {1:'1min', 3:'3min', 5:'5min', 15:'15min', 30:'30min',\
                    60:'1hour', 120:'2hour', 240:'4hour', 360:'6hour', \
                    60*12:'12hour', 60*24:'day', 60*24*7:'week'}
    @staticmethod
    def GetTicker(symbol, access_key, secret_key):
        url = MyExchange.market_url + "?cmd=ticker&pair=" + symbol
        raw_data = httpGet(url)
        if 'error' in raw_data.keys():
            return {'error':json.dumps(raw_data['error'],encoding="utf8", ensure_ascii=False)}
        ret_data = {"data": {"time": raw_data['result']['timestamp'], "buy": raw_data['result']['buy'],\
                    "sell": raw_data['result']['sell'], "last": raw_data['result']['last'],\
                    "high": raw_data['result']['high'], "low": raw_data['result']['low'],\
                    "vol": raw_data['result']['vol']}}
        return ret_data
    @staticmethod
    def GetDepth(symbol, access_key, secret_key):
        url = MyExchange.market_url + "?cmd=depth&size=10&pair=" + symbol
        raw_data = httpGet(url)
        if 'error' in raw_data.keys():
            return {'error':json.dumps(raw_data['error'],encoding="utf8", ensure_ascii=False)}
        ret_data = {"data" : {"time" : raw_data['result']['update_time'], "asks" : [], "bids" : []}}
        for bid in raw_data['result']['bids']:
            ret_data['data']['bids'].append([bid['price'],bid['volume']])
        for ask in raw_data['result']['asks']:
            ret_data['data']['asks'].append([ask['price'],ask['volume']])
        return ret_data
    @staticmethod
    def GetRecords(symbol, period, access_key, secret_key):
        url = MyExchange.market_url + "?cmd=kline&size=200&period=%s&pair="%MyExchange.kline_period[period] + symbol
        raw_data = httpGet(url)
        if 'error' in raw_data.keys():
            return {'error':json.dumps(raw_data['error'],encoding="utf8", ensure_ascii=False)}
        ret_data = {"data": []}
        for kline in raw_data['result']:
            ret_data['data'].append([kline['time'], kline['open'], kline['high'],\
            kline['low'], kline['close'], kline['vol']])
        return ret_data
    @staticmethod
    def GetTrades(symbol, access_key, secret_key):
        url = MyExchange.market_url + "?cmd=deals&size=50&pair=" + symbol
        raw_data = httpGet(url)
        if 'error' in raw_data.keys():
            return {'error':json.dumps(raw_data['error'],encoding="utf8", ensure_ascii=False)}
        ret_data = {"data":[]}
        for trade in raw_data["result"]:
            ret_data["data"].append({"id":trade["id"], "time":trade["time"], \
            "price":trade["price"], "amount":trade["amount"],"type":"buy" if int(trade["side"])==1 else "sell"})
        return ret_data
    @staticmethod
    def GetAccount(api_key, api_secret):
        url = MyExchange.trade_url + "/transfer"
        cmds = [{"cmd": "transfer/assets", "body": {"select":1}}]
        raw_data = httpPostWithSign(url, cmds, api_key, api_secret)
        if 'error' in raw_data.keys():
            return {'error':json.dumps(raw_data['error'],encoding="utf8", ensure_ascii=False)}
        ret_data = {"data": []}
        if "assets_list" in raw_data["result"][0]["result"].keys():
            for asset in raw_data["result"][0]["result"]["assets_list"]:
                ret_data["data"].append({"currency":asset["coin_symbol"], \
                "free":asset["balance"], "frozen":asset["freeze"]})
        ret_data["raw"] = raw_data["result"]
        return ret_data
    @staticmethod
    def Trade(api_key, api_secret, pair, order_type, order_side, price, amount):
        url = MyExchange.trade_url + "/orderpending"
        cmds = [{
                'cmd':"orderpending/trade",
                'index': random.randint(0,2000), 
                'body':{
                    'pair':pair,
                    'account_type':0,
                    'order_type':order_type,
                    'order_side':order_side,
                    'price':price,
                    'amount':amount,
                    }
                }]
        if order_type==1:
            cmds['money'] = amount
        raw_data = httpPostWithSign(url, cmds, api_key, api_secret)
        if 'error' in raw_data.keys():
            return {'error':json.dumps(raw_data['error'],encoding="utf8", ensure_ascii=False)}
        ret_data = {"data": {'id':raw_data['result'][0]['result']}}
        return ret_data
    @staticmethod
    def CancelOrder(api_key, api_secret, orders_id):
        url = MyExchange.trade_url + "/orderpending"
        cmds = [{
                'cmd':"orderpending/cancelTrade",
                'index': random.randint(0,2000), 
                'body':{'orders_id':orders_id}
                }]
        raw_data = httpPostWithSign(url, cmds, api_key, api_secret)
        if 'error' in raw_data.keys():
            return {'error':json.dumps(raw_data['error'],encoding="utf8", ensure_ascii=False)}
        ret_data = {"data":True}
        try:
            result = raw_data['result'].encode('utf8')
        except:
            ret_data = {"data":False}
        ret_data['raw'] = raw_data
        return ret_data
    @staticmethod
    def GetOrder(api_key, api_secret, orders_id):
        url = MyExchange.trade_url + "/orderpending"
        cmds = [{
                'cmd':"orderpending/order",
                'index': random.randint(0,2000), 
                'body':{'id':orders_id}
                }]
        raw_data = httpPostWithSign(url, cmds, api_key, api_secret)
        if 'error' in raw_data.keys():
            return {'error':json.dumps(raw_data['error'],encoding="utf8", ensure_ascii=False)}
        status = 'open'
        if not raw_data['result'][0]['result']:
            return {"error":'Id not found'}
        if int(raw_data['result'][0]['result']['status'])==3:
            status = 'closed'
        if int(raw_data['result'][0]['result']['status'])==5:
            status = 'canceled'
        ret_data = { 
                    "data": {
                        "id": raw_data['result'][0]['result']['id'],
                        "amount": raw_data['result'][0]['result']['amount'],
                        "price": raw_data['result'][0]['result']['price'],
                        "status": status,
                        "deal_amount": raw_data['result'][0]['result']['deal_amount'],
                        "type": "buy" if raw_data['result'][0]['result']['order_side']==1 else "sell", 
                        "avg_price": 0,
                    }
                }
        ret_data['raw'] = raw_data
        return ret_data
    @staticmethod
    def GetOrders(api_key, api_secret, pair):
        url = MyExchange.trade_url + "/orderpending"
        cmds = [{
                'cmd':"orderpending/orderPendingList",
                'body':{
                    'pair':pair, 
                    'page':1, 
                    'size':50
                    }
                }]
        raw_data = httpPostWithSign(url, cmds, api_key, api_secret)
        if 'error' in raw_data.keys():
            return {'error':json.dumps(raw_data['error'],encoding="utf8", ensure_ascii=False)}
        ret_data = {"data":[]}
        for order in raw_data["result"][0]["result"]["items"]:
            status = 'open'
            if int(order['status'])==3:
                status = 'closed'
            if int(order['status'])==5:
                status = 'canceled'
            ret_data["data"].append(
                {
                    "id": order['id'],
                    "amount": order['amount'],
                    "price": order['price'],
                    "status": status,
                    "deal_amount": order['deal_amount'],
                    "type": "buy" if order['order_side']==1 else "sell", 
                }
            )
        ret_data['raw'] = raw_data
        return ret_data
    @staticmethod
    def IO(api_key, api_secret, path, params):
        url = MyExchange.trade_url + path
        cmds = [json.loads(str(urllib.unquote(params['obj'])))]
        raw_data = httpPostWithSign(url, cmds, api_key, api_secret)
        if 'error' in raw_data.keys():
            return {'error':json.dumps(raw_data['error'],encoding="utf8", ensure_ascii=False)}
        return {"data":raw_data}

class Server(BaseHTTPRequestHandler):

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
    def do_POST(self):

        self.data_string = self.rfile.read(int(self.headers['Content-Length']))
        data =json.loads(self.data_string.replace("'", '"'))
		
		ccfox = ccfoxClient(data["access_key"],data["access_key"])
		
		
        sent_data = {}
        if data['method'] == "ticker":
            symbol = data['params']['symbol'].upper()
            access_key = data["access_key"]
            secret_key = data["secret_key"]
            sent_data = MyExchange.GetTicker(symbol, access_key, secret_key)
			
        elif data['method'] == "depth":
            symbol = data['params']['symbol'].upper()
            access_key = data["access_key"]
            secret_key = data["secret_key"]
            sent_data = MyExchange.GetDepth(symbol, access_key, secret_key)
        elif data['method'] == "records":
            symbol = data['params']['symbol'].upper()
			symbol.replace('_','/')
            period = data['params']['period']
            # access_key = data["access_key"]
            # secret_key = data["secret_key"]
            # sent_data = MyExchange.GetRecords(symbol, , access_key, secret_key)
			sent_data = ccfox.get_queryCandlestick(symbol, int(period)*60*1000)
        elif data['method'] == "trades":
            symbol = data['params']['symbol'].upper()
            access_key = data["access_key"]
            secret_key = data["secret_key"]
            sent_data = MyExchange.GetTrades(symbol)
        elif data['method'] == "accounts":
            access_key = data["access_key"]
            secret_key = data["secret_key"]
            sent_data = MyExchange.GetAccount(access_key, secret_key)
        elif data['method'] == "trade":
            access_key = data["access_key"]
            secret_key = data["secret_key"]
            pair = data['params']['symbol'].upper()
            order_side = 1 if data['params']['type'] == 'buy' else 2
            price = data['params']['price']
            order_type = 2 if price > 0 else 1
            amount = data['params']['amount']
            sent_data = MyExchange.Trade(access_key, secret_key, pair, order_type, order_side, price, amount)
        elif data['method'] == "cancel":
            access_key = data["access_key"]
            secret_key = data["secret_key"]
            orders_id = int(data['params']['id'])
            sent_data = MyExchange.CancelOrder(access_key, secret_key, orders_id)
        elif data['method'] == "order":
            access_key = data["access_key"]
            secret_key = data["secret_key"]
            orders_id = int(data['params']['id'])
            sent_data = MyExchange.GetOrder(access_key, secret_key, orders_id)
        elif data['method'] == "orders":
            access_key = data["access_key"]
            secret_key = data["secret_key"]
            pair = data['params']['symbol'].upper()
            sent_data = MyExchange.GetOrders(access_key, secret_key, pair)
        elif data['method'][:2] == "__":
            access_key = data["access_key"]
            secret_key = data["secret_key"]
            path = data["method"].split('_')[-1]
            params = data["params"]
            sent_data = MyExchange.IO(access_key, secret_key, path, params)

        self.do_HEAD()
        self.wfile.write(json.dumps(sent_data))
        
def run(server_class=HTTPServer, handler_class=Server, port=6667):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print 'Starting http server...'
    httpd.serve_forever()

if __name__ == "__main__":
    from sys import argv
    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()