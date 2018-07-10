
# encoding: UTF-8

#
# @brief XCoin API-call related functions (for Python 2.x, 3.x)
#
# @author btckorea
# @date 2017-04-14
#

import sys
import time
import math
import base64
import hmac, hashlib

PY3 = sys.version_info[0] > 2;
if PY3:
	import urllib.parse
else:
	import urllib

import pycurl
import json


class XCoinAPI:
	api_url = "https://api.bithumb.com";
	api_key = "";
	api_secret = "";

	def __init__(self, api_key, api_secret):
		self.api_key = api_key;
		self.api_secret = api_secret;

	def http_body_callback(self, buf):
		self.contents = buf;

	def microtime(self, get_as_float = False):
		if get_as_float:
			return time.time();
		else:
			return '%f %d' % math.modf(time.time());

	def microsectime(self) :
		mt = self.microtime(False);
		mt_array = mt.split(" ")[:2];
		return mt_array[1] + mt_array[0][2:5];

	def xcoinApiCall(self, endpoint, rgParams):
		# 1. Api-Sign and Api-Nonce information generation.
		# 2. Request related information from the Bithumb API server.
		#
		# - nonce: it is an arbitrary number that may only be used once. (Microseconds)
		# - api_sign: API signature information created in various combinations values.

		endpoint_item_array = {
			"endpoint" : endpoint
		};

		uri_array = dict(endpoint_item_array, **rgParams); # Concatenate the two arrays.
		if PY3:
			e_uri_data = urllib.parse.urlencode(uri_array);
		else:
			e_uri_data = urllib.urlencode(uri_array);

		# Api-Nonce information generation.
		nonce = self.microsectime();

		# Api-Sign information generation.
		hmac_key = self.api_secret;
		utf8_hmac_key = hmac_key.encode('utf-8');

		hmac_data = endpoint + chr(0) + e_uri_data + chr(0) + nonce;
		utf8_hmac_data = hmac_data.encode('utf-8');

		hmh = hmac.new(bytes(utf8_hmac_key), utf8_hmac_data, hashlib.sha512);
		hmac_hash_hex_output = hmh.hexdigest();
		utf8_hmac_hash_hex_output = hmac_hash_hex_output.encode('utf-8');
		utf8_hmac_hash = base64.b64encode(utf8_hmac_hash_hex_output);

		api_sign = utf8_hmac_hash;
		utf8_api_sign = api_sign.decode('utf-8');

		# Connects to Bithumb API server and returns JSON result value.
		curl_handle = pycurl.Curl();
		curl_handle.setopt(pycurl.POST, 1);
		#curl_handle.setopt(pycurl.VERBOSE, 1); # vervose mode :: 1 => True, 0 => False
		curl_handle.setopt(pycurl.POSTFIELDS, e_uri_data);

		url = self.api_url + endpoint;
		curl_handle.setopt(curl_handle.URL, url);
		curl_handle.setopt(curl_handle.HTTPHEADER, ['Api-Key: ' + self.api_key, 'Api-Sign: ' + utf8_api_sign, 'Api-Nonce: ' + nonce]);
		curl_handle.setopt(curl_handle.WRITEFUNCTION, self.http_body_callback);
		curl_handle.perform();

		#response_code = curl_handle.getinfo(pycurl.RESPONSE_CODE); # Get http response status code.

		curl_handle.close();

		return (json.loads(self.contents));
