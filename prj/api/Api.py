# encoding: UTF-8

import hashlib
import zlib
import json
from time import sleep
from threading import Thread
import websocket
from abc import ABCMeta, abstractmethod
import sys
sys.path.append('.')
sys.path.append('..')
from prj.common.function import *

class Spi(object):
	# __metaclass__ = ABCMeta 
	def __init__(self):
		self.api = None

	# @abstractmethod
	def onMessage(self, ws, evt):
		print 'onMessage'
		data = self.api.evt2str(evt)
		print data
		# print data[0]['channel'], data
		if 'ping' in data:
			ws.send('{pong')

	# @abstractmethod
	def onError(self, ws, evt):
		"""错误推送"""
		print 'onError'
		print evt

	# @abstractmethod
	def onClose(self, ws):
		"""接口断开"""
		print 'onClose'
		sleep(2)
		self.api.connect()

	# @abstractmethod
	def onOpen(self, ws):
		"""接口打开"""
		print 'onOpen'

	def onPing(self, ws):
		print 'onPing'

	def onPong(self, ws):
		print 'onPong'

class Api(object):
	__metaclass__ = ABCMeta 

	def __init__(self, spi):
		self.name = '' # 交易所的名字
		self.rest_url = '' # private 交易 
		self.websocket_url = '' # public 行情
		self.api_key = ''  
		self.secret_key = ''  
		self.ws = None  # websocket应用对象
		self.thread = None  # 工作线程
		self.spi = spi
		self.spi.api = self

	def connect(self):
		# 读配置
		p = getRootPath()+'/cfg/accounts.json'
		f = open(p)
		j = json.load(f)
		s = j[self.name]
		self.rest_url = s['rest_url']
		self.websocket_url = s['websocket_url']
		self.api_key = s['api_key']
		self.secret_key = s['secret_key']

		if self.websocket_url:
			websocket.enableTrace(False)
			self.ws = websocket.WebSocketApp(self.websocket_url,
											on_message=self.spi.onMessage,
											on_error=self.spi.onError,
											on_close=self.spi.onClose,
											on_open=self.spi.onOpen,
											on_ping=self.spi.onPing,
											on_pong=self.spi.onPong)

			self.thread = Thread(target=self.ws.run_forever)
			self.thread.start()


	def close(self):
		if self.thread and self.thread.isAlive():
			self.ws.close()
			self.thread.join()


	def reconnect(self):
		self.close()

		websocket.enableTrace(False)
		self.ws = websocket.WebSocketApp(self.websocket_url,
										on_message=self.spi.onMessage,
										on_error=self.spi.onError,
										on_close=self.spi.onClose,
										on_open=self.spi.onOpen)

		self.thread = Thread(target=self.ws.run_forever)
		self.thread.start()

	def evt2str(self, evt):
		pass

	def send_request(self, req_str):
		try:
			self.ws.send(req_str)
		except websocket.WebSocketConnectionClosedException:
			# 若触发异常则重连
			self.reconnect()
			self.ws.send(req_str)