# encoding: UTF-8

import json
import shelve
from collections import OrderedDict

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

import sys
sys.path.append('.')
sys.path.append('..')
from common.vtFunction import *
from common.eventEngine import *
from gateway.vtGateway import *
from common.vtFunction import loadMongoSetting

# from ctaAlgo.ctaEngine import CtaEngine
from drEngine import DrEngine
# from riskManager.rmEngine import RmEngine


########################################################################
class MainEngine(object):
	"""主引擎"""

	# ----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""

		def print_log(event):
			log = event.dict_['data']
			print (':'.join([log.logTime, log.logContent]))

		def print_classofclass(event):
			class_data = event.dict_['data'].__dict__
			print (json.dumps(class_data, encoding="UTF-8", ensure_ascii=False))

		# 创建事件引擎
		self.eventEngine = EventEngine2()
		# self.eventEngine.register(EVENT_LOG, print_log)
		# self.eventEngine.register(EVENT_DATARECORDER_LOG, print_log)
		# self.eventEngine.register(EVENT_ACCOUNT, print_classofclass)
		# self.eventEngine.register(EVENT_POSITION, print_classofclass)
		self.eventEngine.start()

		# 创建数据引擎
		# self.dataEngine = DataEngine(self.eventEngine)

		# MongoDB数据库相关
		self.dbClient = None  # MongoDB客户端对象

		# 调用一个个初始化函数
		self.initGateway()
		
		#self._loadSetting()

		# 扩展模块
		# self.ctaEngine = CtaEngine(self, self.eventEngine)
		self.drEngine = DrEngine(self, self.eventEngine)
		# self.rmEngine = RmEngine(self, self.eventEngine)

	# ----------------------------------------------------------------------
	def initGateway(self):
		"""初始化接口对象"""
		# 用来保存接口对象的字典
		self.gatewayDict = OrderedDict()
		
		try:
			from okcoinGateway import OkcoinGateway
			self.addGateway(OkcoinGateway, 'OKCOIN')
			self.gatewayDict['OKCOIN'].setQryEnabled(False)
		except Exception as e:
			print (e)
			
		try:
			from btccGateway import BtccGateway
			self.addGateway(BtccGateway, 'BTCC')
			self.gatewayDict['BTCC'].setQryEnabled(False)
		except Exception, e:
			print e

		try:
			from huobiGateway import HuobiGateway
			self.addGateway(HuobiGateway, 'HUOBI')
			self.gatewayDict['HUOBI'].setQryEnabled(False)
		except Exception, e:
			print e

		try:
			from huobiGateway import HuobiETHGateway
			self.addGateway(HuobiETHGateway, 'HUOBIETH')
			self.gatewayDict['HUOBIETH'].setQryEnabled(False)
		except Exception, e:
			print e


	# DR_setting.json中读入 哪个网关要订哪些合约
	def _loadSetting(self):
		self.gatewaySymbolsDict = {}
		path = settingFileName = getRootPath() + '/cfg/' + 'DR_setting.json'
		with open(path) as f:
			drSetting = json.load(f)
			for gatewayName in self.gatewayDict.keys():
				if gatewayName in drSetting:
					gatewaySymbolsDict[gatewayName] = drSetting[gatewayName]
					
	# ----------------------------------------------------------------------
	# create separate objects from each gateway first
	def addGateway(self, gateway, gatewayName=None):
		"""创建接口"""
		self.gatewayDict[gatewayName] = gateway(self.eventEngine, gatewayName)

	# ----------------------------------------------------------------------
	def connect(self, gatewayName):
		"""连接特定名称的接口"""
		if gatewayName in self.gatewayDict:
			gateway = self.gatewayDict[gatewayName]
			gateway.connect()
		else:
			self.writeLog(u'接口不存在：%s' % gatewayName)

	# ----------------------------------------------------------------------
	def subscribe(self, subscribeReq, gatewayName):
		"""订阅特定接口的行情"""
		if gatewayName in self.gatewayDict:
			gateway = self.gatewayDict[gatewayName]
			gateway.subscribe(subscribeReq)
		else:
			self.writeLog(u'接口不存在：%s' % gatewayName)



	def sendOrder(self, orderReq, gatewayName):
		"""对特定接口发单"""
		# 如果风控检查失败则不发单
		if not self.rmEngine.checkRisk(orderReq):
			return ''

		if gatewayName in self.gatewayDict:
			gateway = self.gatewayDict[gatewayName]
			return gateway.sendOrder(orderReq)
		else:
			self.writeLog(u'接口不存在：%s' % gatewayName)

			# ----------------------------------------------------------------------

	def cancelOrder(self, cancelOrderReq, gatewayName):
		"""对特定接口撤单"""
		if gatewayName in self.gatewayDict:
			gateway = self.gatewayDict[gatewayName]
			gateway.cancelOrder(cancelOrderReq)
		else:
			self.writeLog(u'接口不存在：%s' % gatewayName)

			# ----------------------------------------------------------------------

	def qryAccont(self, gatewayName):
		"""查询特定接口的账户"""
		if gatewayName in self.gatewayDict:
			gateway = self.gatewayDict[gatewayName]
			gateway.qryAccount()
		else:
			self.writeLog(u'接口不存在：%s' % gatewayName)

			# ----------------------------------------------------------------------

	def qryPosition(self, gatewayName):
		"""查询特定接口的持仓"""
		if gatewayName in self.gatewayDict:
			gateway = self.gatewayDict[gatewayName]
			gateway.qryPosition()
		else:
			self.writeLog(u'接口不存在：%s' % gatewayName)

			# ----------------------------------------------------------------------

	def exit(self):
		"""退出程序前调用，保证正常退出"""
		# 安全关闭所有接口
		for gateway in self.gatewayDict.values():
			gateway.close()

		# 停止事件引擎
		self.eventEngine.stop()

		# 停止数据记录引擎
		self.drEngine.stop()

		# 保存数据引擎里的合约数据到硬盘
		self.dataEngine.saveContracts()

	# ----------------------------------------------------------------------
	def writeLog(self, content):
		"""快速发出日志事件"""
		log = VtLogData()
		log.logContent = content
		event = Event(type_=EVENT_LOG)
		event.dict_['data'] = log
		self.eventEngine.put(event)

		# ----------------------------------------------------------------------

	def dbConnect(self):
		"""连接MongoDB数据库"""
		if not self.dbClient:
			# 读取MongoDB的设置

			host, port = loadMongoSetting()
			try:
				# 设置MongoDB操作的超时时间为0.5秒
				self.dbClient = MongoClient(host, port, serverSelectionTimeoutMS=500)

				# 调用server_info查询服务器状态，防止服务器异常并未连接成功
				self.dbClient.server_info()

				self.writeLog(u'MongoDB连接成功')
			except ConnectionFailure:
				self.writeLog(u'MongoDB连接失败')

	# ----------------------------------------------------------------------
	def dbInsert(self, dbName, collectionName, d):
		"""向MongoDB中插入数据，d是具体数据"""
		if self.dbClient:
			db = self.dbClient[dbName]
			collection = db[collectionName]
			collection.insert(d)


	# ----------------------------------------------------------------------
	def dbQuery(self, dbName, collectionName, d):
		"""从MongoDB中读取数据，d是查询要求，返回的是数据库查询的指针"""
		if self.dbClient:
			db = self.dbClient[dbName]
			collection = db[collectionName]
			cursor = collection.find(d)
			return cursor
		else:
			return None

	# ----------------------------------------------------------------------
	def getContract(self, vtSymbol):
		"""查询合约"""
		return self.dataEngine.getContract(vtSymbol)

	# ----------------------------------------------------------------------
	def getAllContracts(self):
		"""查询所有合约（返回列表）"""
		return self.dataEngine.getAllContracts()

	# ----------------------------------------------------------------------
	def getOrder(self, vtOrderID):
		"""查询委托"""
		return self.dataEngine.getOrder(vtOrderID)

	# ----------------------------------------------------------------------
	def getAllWorkingOrders(self):
		"""查询所有的活跃的委托（返回列表）"""
		return self.dataEngine.getAllWorkingOrders()

	
########################################################################
class DataEngine(object):
	"""数据引擎"""
	contractFileName = 'ContractData.vt'

	# ----------------------------------------------------------------------
	def __init__(self, eventEngine):
		"""Constructor"""
		self.eventEngine = eventEngine

		# 保存合约详细信息的字典
		self.contractDict = {}

		# 保存委托数据的字典
		self.orderDict = {}

		# 保存活动委托数据的字典（即可撤销）
		self.workingOrderDict = {}

		# 读取保存在硬盘的合约数据
		self.loadContracts()

		# 注册事件监听
		self.registerEvent()

	# ----------------------------------------------------------------------
	def updateContract(self, event):
		"""更新合约数据"""
		contract = event.dict_['data']
		self.contractDict[contract.vtSymbol] = contract
		self.contractDict[contract.symbol] = contract  # 使用常规代码（不包括交易所）可能导致重复

	# ----------------------------------------------------------------------
	def getContract(self, vtSymbol):
		"""查询合约对象"""
		try:
			return self.contractDict[vtSymbol]
		except KeyError:
			return None

	# ----------------------------------------------------------------------
	def getAllContracts(self):
		"""查询所有合约对象（返回列表）"""
		return self.contractDict.values()

	# ----------------------------------------------------------------------
	def saveContracts(self):
		"""保存所有合约对象到硬盘"""
		f = shelve.open(self.contractFileName)
		f['data'] = self.contractDict
		f.close()

	# ----------------------------------------------------------------------
	def loadContracts(self):
		"""从硬盘读取合约对象"""
		f = shelve.open(self.contractFileName)
		if 'data' in f:
			d = f['data']
			for key, value in d.items():
				self.contractDict[key] = value
		f.close()

	# ----------------------------------------------------------------------
	def updateOrder(self, event):
		"""更新委托数据"""
		order = event.dict_['data']
		self.orderDict[order.vtOrderID] = order

		# 如果订单的状态是全部成交或者撤销，则需要从workingOrderDict中移除
		if order.status == STATUS_ALLTRADED or order.status == STATUS_CANCELLED:
			if order.vtOrderID in self.workingOrderDict:
				del self.workingOrderDict[order.vtOrderID]
		# 否则则更新字典中的数据
		else:
			self.workingOrderDict[order.vtOrderID] = order

	# ----------------------------------------------------------------------
	def getOrder(self, vtOrderID):
		"""查询委托"""
		try:
			return self.orderDict[vtOrderID]
		except KeyError:
			return None

	# ----------------------------------------------------------------------
	def getAllWorkingOrders(self):
		"""查询所有活动委托（返回列表）"""
		return self.workingOrderDict.values()

	# ----------------------------------------------------------------------
	def registerEvent(self):
		"""注册事件监听"""
		self.eventEngine.register(EVENT_CONTRACT, self.updateContract)
		self.eventEngine.register(EVENT_ORDER, self.updateOrder)



if __name__ == '__main__':

	from PyQt4 import QtCore
	import sys

	app = QtCore.QCoreApplication(sys.argv)

	me = MainEngine()

	me.dbConnect()


	for i in sys.argv[1:]:
		print "Connecting Gateway: %s ......" %i
		me.connect(str(i))

	sys.exit(app.exec_())


