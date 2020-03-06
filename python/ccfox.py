# -*- coding: utf-8 -*-
import time
from requests import Request, Session
import hmac


class ccfoxClient:
    _ENDPOINT = 'https://api.ccfox.com/api/v1/'

    def __init__(self,key, secret):
        self._session = Session()
        self._api_key = key # TODO: Place your API key here
        self._api_secret = secret # TODO: Place your API secret here

    def _get(self, path, params = None):
        return self._request('GET', path, params=params)

    def _post(self, path, params = None):
        return self._request('POST', path, json=params)

    def _delete(self, path, params = None):
        return self._request('DELETE', path, params=params)

    def _request(self, method, path, **kwargs):
        request = Request(method, self._ENDPOINT + path, **kwargs)
        self._sign_request(request)
        response = self._session.send(request.prepare())
        return self._process_response(response)

    def _sign_request(self, request):
        ts = int(time.time() * 1000)
        prepared = request.prepare()
        #signature_payload = prepared.method + prepared.path_url + str(ts)
        #signature_payload = f'{prepared.method}{prepared.path_url}{ts}'
        signature_payload = "{}{}{}".format(prepared.method, prepared.path_url,str(ts))
        print(signature_payload)
        if prepared.body:
            signature_payload += prepared.body
        #signature = hmac.new(bytes(self._api_secret, 'utf8'), bytes(signature_payload, 'utf8'), digestmod=hashlib.sha256).hexdigest()
        #signature = hmac.new(self._api_secret.encode(), signature_payload.encode(), 'sha256').hexdigest()
        signature = "2222"       
        request.headers['apiKey'] = self._api_key
        request.headers['signature'] = signature
        request.headers['apiExpires'] = str(ts)
        request.headers['Content-Type'] = 'application/json'

    def _process_response(self, response):
        try:
            data = response.json()
            #pprint(data)
        except ValueError:
            response.raise_for_status()
            raise
        else:
            if 'error' in data:
                raise Exception(data)
            return data



    '''1.基础信息类'''
    def list_futureQueryContract(self):#获取所有合约信息
        return self._get('future/queryContract')['result']
        
    def list_commonQueryCurrency(self):#获取所有币种信息
        return self._get('common/queryCurrency')['result']

    def list_exchange(self):#获取所有法币
        return self._get('common/exchange/list')['result']
    
    def list_exchangecoins(self):#获取计价货币的价格
        return self._get('common/exchange/coins')['result']

    #获取期货交割历史
    def get_queryContractDeliveryList(self,type1='2',pageNum='1',pageSize='1',contractId=None,sort=None):#获取计价货币的价格
        RAW = self._get('future/queryContractDeliveryList',{'type': type1,
                                     'pageNum': pageNum,
                                     'pageSize': pageSize,
                                     'contractId': contractId,
                                     'sort': sort})
        if RAW['msg']=='success': return RAW['data']



    '''2.行情类'''
    def get_queryMarketStat(self,currencyId='2'):#获取24小时统计
        RAW = self._get('/futureQuot/queryMarketStat',{'currencyId': currencyId})
        if RAW['msg']=='success': return RAW['data']

    def get_queryCandlestick(self,symbol,ranges):#获取K线数据
        RAW = self._get('/futureQuot/queryCandlestick',{'symbol': symbol,'range':ranges})
        if RAW['success']==1: return RAW['data']['lines']
    
    def list_querySnapshot(self,contractId):#获取单个合约行情快照
        return self._get('futureQuot/querySnapshot',{'contractId': contractId})['result']

    def list_queryTickTrade(self,contractId):#获取逐笔成交
        return self._get('futureQuot/queryTickTrade',{'contractId': contractId})['data']

    def list_queryIndicatorList(self):#获取所有行情快照
        return self._get('futureQuot/queryIndicatorList')
    

    '''3.用户类'''

    def get_userInfo(self): #获取用户基本信息
        RAW = self._get('future/user')
        if RAW['msg']=='success': return RAW['data']

    def get_usermargin(self): #获取用户资产信息
        RAW = self._get('future/margin')
        if RAW['msg']=='success': return RAW['data']

    def get_position(self): #获取用户持仓信息
        RAW = self._get('future/position')
        if RAW['msg']=='success': return RAW['data']

    def get_queryVarietyMargin(self,varietyId,contractId): #获取用户合约保证金梯度
        RAW = self._get('future/queryVarietyMargin',{'varietyId': varietyId,'contractId': contractId})
        if RAW['msg']=='success': return RAW['data']

    '''4.交易类'''


    # 合约下单
    def future_order(self,contractId,side,price, quantity,orderType,
                    positionEffect, marginType,marginRate):
        return self._post('future/order',{'contractId':contractId ,#	交易对ID
                                     'side': side,#合约委托方向（买1，卖-1）
                                     'price': price,#合约委托价格（order_type等于3（市价）时非必填 ）
                                     'quantity': quantity,#合约委托数量
                                     'orderType': orderType,#合约委托类型（1（限价），3（市价） ）
                                     'positionEffect': positionEffect,#开平标志（开仓1，平仓2）
                                     'marginType': marginType,#仓位模式（全仓1，逐仓2）
                                     'marginRate': marginRate})#保证金率（全仓=0，逐仓>=0）


    # 合约批量下单
    def future_orders(self,contractId,side,price, quantity,orderType,
                    positionEffect, marginType,marginRate):
        '''return self._post('future/orders',{'contractId':contractId ,#交易对ID
                                     'side': side,#合约委托方向（买1，卖-1）
                                     'price': price,#合约委托价格（order_type等于3（市价）时非必填 ）
                                     'quantity': quantity,#合约委托数量
                                     'orderType': orderType,#合约委托类型（1（限价），3（市价） ）
                                     'positionEffect': positionEffect,#开平标志（开仓1，平仓2）
                                     'marginType': marginType,#仓位模式（全仓1，逐仓2）
                                     'marginRate': marginRate})#保证金率（全仓=0，逐仓>=0）
        '''
    
    def delete_order(self,ff): #合约撤单
        RAW = self._delete('future/order',{'filter':ff})
        if RAW['msg']=='success': return RAW['data']

    def delete_orders(self,cancels): #合约批量撤单
        RAW = self._delete('future/orders')
        if RAW['msg']=='success': return RAW['data']

    def delete_allorder(self): #合约撤消所有订单
        RAW = self._delete('future/order/all')
        if RAW['msg']=='success': return RAW['data']

    def get_order(self,orderId): #获取订单信息
        RAW = self._get('future/order',{'filter': orderId})
        if RAW['msg']=='success': return RAW['data']

    def get_queryActiveOrder(self): #获取当前订单列表
        RAW = self._get('future/queryActiveOrder')
        if RAW['msg']=='success': return RAW['data']
        
    def get_queryLastestHistoryOrders(self): #获取历史委托
        RAW = self._get('future/queryLastestHistoryOrders')
        if RAW['msg']=='success': return RAW['data']
        

    def post_positionisolate(self,contractId,marginType,initMarginRate='1'): #获取强减队列
        RAW = self._post('future/position/isolate',{'contractId': contractId,'initMarginRate': initMarginRate,'marginType': marginType})
        if RAW['msg']=='success': return RAW['data']
        

    def post_transferMargin(self,contractId,margin): #调整保证金率
        RAW = self._post('future/position/transferMargin',{'contractId': contractId,'margin': margin})
        if RAW['msg']=='success': return RAW['data']

    def get_queryForceLower(self): #获取强减队列
        RAW = self._get('future/queryForceLower')
        if RAW['msg']=='success': return RAW['data']

        
    def get_queryMatch(self): #获取当前成交
        RAW = self._get('future/queryMatch')
        if RAW['msg']=='success': return RAW['data']




