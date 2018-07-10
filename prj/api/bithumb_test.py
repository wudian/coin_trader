# encoding: UTF-8

#! /usr/bin/env python
#
# @brief XCoin API-call sample script (for Python 2.x, 3.x)
#
# @author btckorea
# @date 2017-04-14
#
# @details
# First, Build and install pycurl with the following commands::
# (if necessary, become root)
#
# https://pypi.python.org/pypi/pycurl/7.43.0#downloads
#
# tar xvfz pycurl-7.43.0.tar.gz
# cd pycurl-7.43.0
# python setup.py --libcurl-dll=libcurl.so install
# python setup.py --with-openssl install
# python setup.py install
#
# @note
# Make sure current system time is correct.
# If current system time is not correct, API request will not be processed normally.
#
# rdate -s time.nist.gov
#

import sys
from bithumb import *
import pprint
import datetime


api_key = "55cf8f8268c9369f5646772e6c998d9b";
api_secret = "2762a686471de5c75b7c98c3607d3ab0";

api = XCoinAPI(api_key, api_secret);

rgParams = {
	"order_currency" : "BTC",
	"payment_currency" : "CNY"
};


#
# Public API
#
# /public/ticker
# /public/recent_ticker
# /public/orderbook
# /public/recent_transactions

# print("Bithumb Public API URI('/public/ticker') Request...");
# result = api.xcoinApiCall("/public/ticker", rgParams);
# print("- Status Code: " + result["status"]);
# print("- Opening Price: " + result["data"]["opening_price"]);
# print("- Closing Price: " + result["data"]["closing_price"]);
# print("- Sell Price: " + result["data"]["sell_price"]);
# print("- Buy Price: " + result["data"]["buy_price"]);
# print("");


#
# Private API
#
# endpoint => parameters
# /info/current
# /info/account
# /info/balance
# /info/wallet_address



# sys.exit(0);

d1 = datetime.datetime.now()
result = api.xcoinApiCall("/info/account", rgParams)
d2 = datetime.datetime.now()
d = d2 - d1
print "bithumb:发送请求时间%s,收到回报时间%s,用时%s" % (str(d1), str(d2), str(d))
