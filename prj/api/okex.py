# encoding: UTF-8

from Api import *

class Okex(Api):
	def __init__(self, spi):
		Api.__init__(self, spi)
		self.name = 'okex'

	def evt2str(self, evt):
		try:
			# 创建解压器
			decompress = zlib.decompressobj(-zlib.MAX_WBITS)
			# 将原始数据解压成字符串
			inflated = decompress.decompress(evt) + decompress.flush()
			# 通过json解析字符串
			data = json.loads(inflated)
			return data

		except zlib.error as err:
			# print err
			# # 创建解压器
			# decompress = zlib.decompressobj(16+zlib.MAX_WBITS)
			# # 将原始数据解压成字符串
			# inflated = decompress.decompress(evt) + decompress.flush()
			# 通过json解析字符串
			data = json.loads(evt)
			return data


	# ----------------------------------------------------------------------
	def generateSign(self, params):
		"""生成签名"""
		l = []
		for key in sorted(params.keys()):
			l.append('%s=%s' % (key, params[key]))
		l.append('secret_key=%s' % self.secret_key)
		sign = '&'.join(l)
		return hashlib.md5(sign.encode('utf-8')).hexdigest().upper()

	# ----------------------------------------------------------------------
	def sendMarketDataRequest(self, channel_list):
		d_list = []
		for channel in channel_list:
			d = {}
			d['event'] = 'addChannel'
			d['binary'] = True
			d['channel'] = channel
			d_list.append(json.dumps(d))
		
		request = "["+','.join(d_list)+"]"
		super.send_request(self, request)

	def sendTradingRequest(self, channel, params):
		# 在参数字典中加上api_key和签名字段
		params['api_key'] = self.api_key
		params['sign'] = self.generateSign(params)

		d = {}
		d['event'] = 'addChannel'
		d['binary'] = True
		d['channel'] = channel
		d['parameters'] = params

		super.send_request(self, d)

	def subscribeSpotTicker(self, symbol_list):
		channel_list = []
		for symbol in symbol_list:
			channel_list.append('ok_sub_spot_%s_ticker' % symbol)
		self.sendMarketDataRequest() 

	# ----------------------------------------------------------------------
	def subscribeSpotDepth(self, symbol, depth):
		"""订阅现货深度报价"""
		self.sendMarketDataRequest('ok_sub_spot%s_%s_depth_%s' % (self.currency, symbol, depth))

	def spotTrade(self, symbol, type_, price, amount):
		"""现货委托"""
		params = {}
		params['symbol'] = str(symbol + self.currency)
		params['type'] = str(type_)
		params['price'] = str(price)
		params['amount'] = str(amount)
		# print params
		channel = 'ok_spot%s_trade' % (self.currency)

		self.sendTradingRequest(channel, params)

	# ----------------------------------------------------------------------
	def spotCancelOrder(self, symbol, orderid):
		"""现货撤单"""
		params = {}
		params['symbol'] = str(symbol + self.currency)
		params['order_id'] = str(orderid)

		channel = 'ok_spot%s_cancel_order' % (self.currency)

		self.sendTradingRequest(channel, params)

	def spotOrderInfo(self, symbol, orderid):
		"""查询现货委托信息"""
		params = {}
		params['symbol'] = str(symbol + self.currency)
		params['order_id'] = str(orderid)

		channel = 'ok_spot%s_orderinfo' % (self.currency)

		self.sendTradingRequest(channel, params)



if __name__ == '__main__':
	spi = Spi()
	api = Okex(spi)
	api.connect()
	sleep(100)
	# while 1:
	# 	input = raw_input('0.连接 1:订阅tick 2.订阅depth 3.订阅成交记录 4.订阅K线 5.下单 6.撤单 7.查账户 8.查订单 9.订阅交易数据 10.订阅账户 20.断开连接\n')
	# 	if input == '0':
	# 		api.connect(host, apiKey, secretKey, trace=False)
	# 		sleep(2)
	# 	elif input == '1':
	# 		api.subscribeSpotTicker('btc')
	# 	elif input == '2':
	# 		api.subscribeSpotDepth('btc', 20)
	# 	elif input == '3':
	# 		api.subscribeSpotTrades()
	# 	elif input == '4':
	# 		api.subscribeSpotKline('btc', INTERVAL_1M)
	# 	elif input == '5':
	# 		# api.spotTrade('btc_', 'buy', str(17000), str(0.01))
	# 		# api.spotTrade('btc_', 'buy', str(16000), str(0.01))
	# 		pass
	# 	elif input == '6':
	# 		pass
	# 	elif input == '7':
	# 		api.spotUserInfo()
	# 	elif input == '8':
	# 		api.spotOrderInfo('btc', '-1')
	# 	elif input == '9':
	# 		api.subscribeSpotTrades()
	# 	elif input == '10':
	# 		api.subscribeSpotUserInfo()
	# 	elif input == '20':
	# 		api.close()
	# 	else:
	# 		break
