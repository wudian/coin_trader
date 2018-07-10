# encoding: UTF-8

'''
本文件中实现了风控引擎，用于提供一系列常用的风控功能：
1. 委托流控（单位时间内最大允许发出的委托数量）
2. 总成交限制（每日总成交数量限制）
3. 单笔委托的委托数量控制
'''

import json
import os
import platform

from eventEngine import *
from vtConstant import *
from vtGateway import VtLogData
from vtFunction import *

########################################################################
class RmEngine(object):
    """风控引擎"""
    settingFileName = 'RM_setting.json'
    settingFileName = os.path.join(ROOT_PATH, 'cfg', settingFileName)
    
    name = u'风控模块'

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine):
        """Constructor"""
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        
        # 是否启动风控
        self.active = False
        
        # 流控相关
        self.orderFlowCount = EMPTY_INT     # 单位时间内委托计数
        self.orderFlowLimit = EMPTY_INT     # 委托限制
        self.orderFlowClear = EMPTY_INT     # 计数清空时间（秒）
        self.orderFlowTimer = EMPTY_INT     # 计数清空时间计时
    
        # 单笔委托相关
        self.orderSizeLimit = EMPTY_INT     # 单笔委托最大限制
    
        # 成交统计相关
        self.tradeCount = EMPTY_INT         # 当日成交合约数量统计
        self.tradeLimit = EMPTY_INT         # 当日成交合约数量限制
        
        # 活动合约相关
        self.workingOrderLimit = EMPTY_INT  # 活动合约最大限制

        # Position Control
        self.currentPos = EMPTY_INT
        self.currentPosLimit = EMPTY_INT
        
        self.loadSetting()
        self.registerEvent()
        
    #----------------------------------------------------------------------
    def loadSetting(self):
        """读取配置"""
        with open(self.settingFileName) as f:
            d = json.load(f)
            
            # 设置风控参数
            self.active = d['active']
            
            self.orderFlowLimit = d['orderFlowLimit']
            self.orderFlowClear = d['orderFlowClear']
            
            self.orderSizeLimit = d['orderSizeLimit']
            
            self.tradeLimit = d['tradeLimit']
            
            self.workingOrderLimit = d['workingOrderLimit']

            self.currentPosLimit = d['currentPosLimit']
        
    #----------------------------------------------------------------------
    def saveSetting(self):
        """保存风控参数"""
        with open(self.settingFileName, 'w') as f:
            # 保存风控参数
            d = {}

            d['active'] = self.active
            
            d['orderFlowLimit'] = self.orderFlowLimit
            d['orderFlowClear'] = self.orderFlowClear
            
            d['orderSizeLimit'] = self.orderSizeLimit
            
            d['tradeLimit'] = self.tradeLimit
            
            d['workingOrderLimit'] = self.workingOrderLimit

            d['CurrentPosLimit'] = self.currentPosLimit
            
            # 写入json
            jsonD = json.dumps(d, indent=4)
            f.write(jsonD)
        
    #----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        self.eventEngine.register(EVENT_TRADE, self.updateTrade)
        self.eventEngine.register(EVENT_TIMER, self.updateTimer)
        self.eventEngine.register(EVENT_POSITION, self.updatePosition)

    #----------------------------------------------------------------------
    def updateTrade(self, event):
        """更新成交数据"""
        trade = event.dict_['data']
        self.tradeCount += trade.volume

    #----------------------------------------------------------------------
    def updatePosition(self, event):
        """更新成交数据"""
        pos = event.dict_['data']
        self.currentPos = pos.position
        # print 'currentPos: %s' % self.currentPos
    
    #----------------------------------------------------------------------
    def updateTimer(self, event):
        """更新定时器"""
        self.orderFlowTimer += 1
        
        # 如果计时超过了流控清空的时间间隔，则执行清空
        if self.orderFlowTimer >= self.orderFlowClear:
            self.orderFlowCount = 0
            self.orderFlowTimer = 0
        
    #----------------------------------------------------------------------
    def writeRiskLog(self, content):
        """快速发出日志事件"""
        # 发出报警提示音

        if platform.uname() == 'Windows':
            import winsound
            winsound.PlaySound("SystemHand", winsound.SND_ASYNC) 
        
        # 发出日志事件
        log = VtLogData()
        log.logContent = content
        log.gatewayName = self.name
        event = Event(type_=EVENT_LOG)
        event.dict_['data'] = log
        self.eventEngine.put(event)

    #----------------------------------------------------------------------
    def checkRisk(self, orderReq):
        """检查风险"""
        # 如果没有启动风控检查，则直接返回成功
        if not self.active:
            return True

        if orderReq.offset in [OFFSET_CLOSE, OFFSET_CLOSETODAY, OFFSET_CLOSEYESTERDAY]:
            volume = -orderReq.volume
        else:
            volume = orderReq.volume
        # Check the current all position
        if (self.currentPos + volume) >= self.currentPosLimit:
            self.writeRiskLog(u'Total Position 数量%s，超过限制%s'
                              % (self.currentPos, self.currentPosLimit))
            return False

        # 检查委托数量
        if orderReq.volume > self.orderSizeLimit:
            self.writeRiskLog(u'单笔委托数量%s，超过限制%s' 
                              %(orderReq.volume, self.orderSizeLimit))
            return False
        
        # 检查成交合约量
        if self.tradeCount >= self.tradeLimit:
            self.writeRiskLog(u'今日总成交合约数量%s，超过限制%s' 
                              %(self.tradeCount, self.tradeLimit))
            return False
        
        # 检查流控
        if self.orderFlowCount >= self.orderFlowLimit:
            self.writeRiskLog(u'委托流数量%s，超过限制每%s秒%s' 
                              %(self.orderFlowCount, self.orderFlowClear, self.orderFlowLimit))
            return False
        
        # 检查总活动合约
        workingOrderCount = len(self.mainEngine.getAllWorkingOrders())
        if workingOrderCount >= self.workingOrderLimit:
            self.writeRiskLog(u'当前活动委托数量%s，超过限制%s'
                              %(workingOrderCount, self.workingOrderLimit))
            return False
        
        # 对于通过风控的委托，增加流控计数
        self.orderFlowCount += 1
        
        return True    
    
    #----------------------------------------------------------------------
    def clearOrderFlowCount(self):
        """清空流控计数"""
        self.orderFlowCount = 0
        self.writeRiskLog(u'清空流控计数')
        
    #----------------------------------------------------------------------
    def clearTradeCount(self):
        """清空成交数量计数"""
        self.tradeCount = 0
        self.writeRiskLog(u'清空总成交计数')
        
    #----------------------------------------------------------------------
    def setOrderFlowLimit(self, n):
        """设置流控限制"""
        self.orderFlowLimit = n
        
    #----------------------------------------------------------------------
    def setOrderFlowClear(self, n):
        """设置流控清空时间"""
        self.orderFlowClear = n
        
    #----------------------------------------------------------------------
    def setOrderSizeLimit(self, n):
        """设置委托最大限制"""
        self.orderSizeLimit = n
        
    #----------------------------------------------------------------------
    def setTradeLimit(self, n):
        """设置成交限制"""
        self.tradeLimit = n
        
    #----------------------------------------------------------------------
    def setWorkingOrderLimit(self, n):
        """设置活动合约限制"""
        self.workingOrderLimit = n

    #----------------------------------------------------------------------
    def setCurrentPosLimit(self, n):
        """设置活动合约限制"""
        self.currentPosLimit = n
        
    #----------------------------------------------------------------------
    def switchEngineStatus(self):
        """开关风控引擎"""
        self.active = not self.active
        
        if self.active:
            self.writeRiskLog(u'风险管理功能启动')
        else:
            self.writeRiskLog(u'风险管理功能停止')
