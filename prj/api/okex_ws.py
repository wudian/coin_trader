# encoding: UTF-8

import hashlib
import zlib
import json
from time import sleep
from threading import Thread
import io
import gzip
import websocket

# API地址
OKCOIN_WS = 'wss://real.okex.com:10441/websocket'   # websocket


class DataAPI(object):

    def __init__(self):
        self.apiKey = ''
        self.secretKey = ''
        self.host = ''
        self.ws = None
        self.thread = None

    def connect(self, host, apiKey, secretKey, trace=False):
        self.host = host
        self.apiKey = apiKey
        self.secretKey = secretKey

        websocket.enableTrace(trace)
        self.ws = websocket.WebSocketApp(host,
                                         on_message=self.onMessage,
                                         on_error=self.onError,
                                         on_close=self.onClose,
                                         on_open=self.onOpen)
        self.thread = Thread(target=self.ws.run_forever)
        self.thread.start()

    def reconnect(self):
        self.close()
        self.ws = websocket.WebSocketApp(host,
                                         on_message=self.onMessage,
                                         on_error=self.onError,
                                         on_close=self.onClose,
                                         on_open=self.onOpen)
        self.thread = Thread(target=self.ws.run_forever)
        self.thread.start()

    def readData(self, evt):
        """解压缩推送收到的数据"""
        # try:
        #     # 创建解压器
        #     decompress = zlib.decompressobj(-zlib.MAX_WBITS)
        #     # 将原始数据解压成字符串
        #     inflated = decompress.decompress(evt) + decompress.flush()
        #     # 通过json解析字符串
        #     data = json.loads(inflated)
        #     return data
        #
        # except zlib.error as err:
        #     # print err
        #     # # 创建解压器
        #     # decompress = zlib.decompressobj(16+zlib.MAX_WBITS)
        #     # # 将原始数据解压成字符串
        #     # inflated = decompress.decompress(evt) + decompress.flush()
        #     # 通过json解析字符串
        #     data = json.loads(evt)
        #     return data
        g = gzip.GzipFile(fileobj=io.BytesIO(evt))
        data = g.read().decode('utf-8')
        return data

    # ----------------------------------------------------------------------
    def generateSign(self, params):
        """生成签名"""
        l = []
        for key in sorted(params.keys()):
            l.append('%s=%s' % (key, params[key]))
        l.append('secret_key=%s' % self.secretKey)
        sign = '&'.join(l)
        return hashlib.md5(sign.encode('utf-8')).hexdigest().upper()

    def onMessage(self, ws, evt):
        print('onMessage')
        print(evt)
        data = self.readData(evt)
        print(data)

    def onError(self, ws, evt):
        print('onError')
        print(evt)

    def onClose(self, ws):
        print('onClose')

    def onOpen(self, ws):
        print('onOpen')

    def close(self):
        if self.thread and self.thread.isAlive():
            self.ws.close()
            self.thread.join()

    # 实时行情websocket接口
    def SubMarketTicker(self, symbol):
        """订阅tick"""
        d = {}
        d['event'] = 'addChannel'
        d['channel'] = 'ok_sub_spot_%s_ticker' % symbol
        j = json.dumps(d)
        try:
            self.ws.send(j)
        except websocket.WebSocketConnectionClosedException:
            self.reconnect()
            self.ws.send(j)

    def SubMarketDepth(self, symbol):
        """订阅币币市场深度"""
        d= {}
        d['event'] = 'addChannel'
        d['channel'] = 'ok_sub_spot_%s_depth' % symbol
        j = json.dumps(d)
        try:
            self.ws.send(j)
        except websocket.WebSocketConnectionClosedException:
            self.reconnect()
            self.ws.send(j)

    def SubMarketDepthY(self, symbol, Y):
        """订阅币币市场深度"""
        d= {}
        d['event'] = 'addChannel'
        d['channel'] = 'ok_sub_spot_%s_depth_%s' % (symbol, Y)
        j = json.dumps(d)
        try:
            self.ws.send(j)
        except websocket.WebSocketConnectionClosedException:
            self.reconnect()
            self.ws.send(j)

    def SubMarketDeals(self, symbol):
        """订阅币币市场成交数据"""
        d= {}
        d['event'] = 'addChannel'
        d['channel'] = 'ok_sub_spot_%s_deals' % (symbol)
        j = json.dumps(d)
        try:
            self.ws.send(j)
        except websocket.WebSocketConnectionClosedException:
            self.reconnect()
            self.ws.send(j)

    def SubMarketKline(self, symbol, period):
        """订阅币币市场成交数据"""
        d= {}
        d['event'] = 'addChannel'
        d['channel'] = 'ok_sub_spot_%s_kline_%s' % (symbol,period)
        j = json.dumps(d)
        try:
            self.ws.send(j)
        except websocket.WebSocketConnectionClosedException:
            self.reconnect()
            self.ws.send(j)

    def Login(self):
        """订阅币币市场成交数据"""
        d= {}
        d['event'] = 'login'
        params = {}
        params['api_key'] = self.apiKey

        params['sign'] = self.generateSign(params)

        d['parameters'] = params
        j = json.dumps(d)
        try:
            self.ws.send(j)
        except websocket.WebSocketConnectionClosedException:
            self.reconnect()
            self.ws.send(j)

    def SubUserInfo(self):
        """订阅账户信息"""
        d= {}
        d['event'] = 'addChannel'
        d['channel'] = 'ok_spot_userinfo'
        params = {}
        params['api_key'] = self.apiKey

        params['sign'] = self.generateSign(params)

        d['parameters'] = params
        j = json.dumps(d)
        try:
            self.ws.send(j)
        except websocket.WebSocketConnectionClosedException:
            self.reconnect()
            self.ws.send(j)

    def Order(self, symbol, tradetype, price, amount):
        """下单"""
        d= {}
        d['event'] = 'addChannel'
        d['channel'] = 'ok_spot_order'
        params = {}

        params['api_key'] = self.apiKey
        params['symbol'] = symbol
        params['type'] = tradetype
        params['price'] = price
        params['amount'] = amount
        params['sign'] = self.generateSign(params)

        d['parameters'] = params
        j = json.dumps(d)
        try:
            self.ws.send(j)
        except websocket.WebSocketConnectionClosedException:
            self.reconnect()
            self.ws.send(j)

    def CancelOrder(self, symbol, order_id):
        """下单"""
        d= {}
        d['event'] = 'addChannel'
        d['channel'] = 'ok_spot_cancel_order'
        params = {}

        params['api_key'] = self.apiKey
        params['symbol'] = symbol
        params['order_id'] = order_id
        params['sign'] = self.generateSign(params)

        d['parameters'] = params
        j = json.dumps(d)
        try:
            self.ws.send(j)
        except websocket.WebSocketConnectionClosedException:
            self.reconnect()
            self.ws.send(j)

if __name__ == '__main__':
    apiKey = "54e36db2-96a9-4d32-89de-a44930cc25c3"
    secretKey = "49396C258C1D35847AE3BBBECF0B3423"

    api = DataAPI()
    host = OKCOIN_WS

    api.connect(host, apiKey, secretKey, trace=True)
    sleep(200)


    # api.SubMarketTicker('eth_usdt')

