# encoding: UTF-8

import urllib
import hashlib
import hmac
import base64
import json
import requests
from time import time, sleep
from Queue import Queue, Empty
from threading import Thread
import io
import gzip
import websocket
import datetime

from Api import *


# 火币
class Huobi(Api):
    def __init__(self, spi):
		Api.__init__(self, spi)
		self.name = 'huobi'

    def evt2str(self, evt):
        g = gzip.GzipFile(fileobj=io.BytesIO(evt))
        data = g.read().decode('utf-8')
        return data

    
    def generateSign(self, params):
        """生成签名"""
        params = sorted(params.iteritems(), key=lambda d: d[0], reverse=False)
        message = urllib.urlencode(params)

        m = hashlib.md5()
        m.update(message)
        m.digest()

        sig = m.hexdigest()
        return sig

    def SubTick(self, symbol):
        d = {}
        d['sub'] = 'market.%s.trade.detail' % symbol
        d['id'] = 'sub_trade_detail_%s' % symbol
        j = json.dumps(d)
        Api.send_request(self, j)

    def SubDepth(self, symbol, tp='step0'):
        d = {}
        d['sub'] = 'market.%s.depth.%s' % (symbol, tp)
        d['id'] = 'sub_depth_%s_%s' % (symbol, tp)
        j = json.dumps(d)
        Api.send_request(self, j)

"""
    def SubMarketKline(self, symbol, period):
        d = {}
        d['sub'] = 'market.%s.kline.%s' % (symbol, period)
        d['id'] = 'sub_kline_%s_%s' % (symbol, period)
        j = json.dumps(d)
        Api.send_request(self, j)

    def ReqMarketKline(self, symbol, period, start_date=None, end_date=None):
        d = {}
        d['req'] = 'market.%s.kline.%s' % (symbol, period)
        d['id'] = 'req_kline_%s_%s' % (symbol, period)
        if start_date is not None:
            d['from'] = start_date
        if end_date is not None:
            d['to'] = end_date
        j = json.dumps(d)
        Api.send_request(self, j)


    def ReqMarketDepth(self, symbol, tp='step0'):
        d = {}
        d['req'] = 'market.%s.depth.%s' % (symbol, tp)
        d['id'] = 'req_depth_%s_%s' % (symbol, tp)
        j = json.dumps(d)
        Api.send_request(self, j)

    def ReqTradeDetail(self, symbol):
        d = {}
        d['req'] = 'market.%s.trade.detail' % symbol
        d['id'] = 'req_trade_detail_%s' % symbol
        j = json.dumps(d)
        Api.send_request(self, j)
"""

if __name__ == '__main__':
    spi = Spi()
    api = Huobi(spi)
    api.connect()
    
    # api.SubMarketKline('ethusdt','1min')
    # api.SubMarketDepth('ethusdt','step0')
    api.SubTick('ethusdt')
    # api.ReqMarketKline('ethusdt','1min')

    sleep(200)
