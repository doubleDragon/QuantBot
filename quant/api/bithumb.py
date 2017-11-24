#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import base64
import hashlib
import hmac
import json
import math
import urllib

import requests
import time

import pycurl


class PublicClient(object):
    """
    https://www.bithumb.com/u1/US127
    """

    def __init__(self):
        super(PublicClient, self).__init__()
        self.base_url = 'https://api.bithumb.com'

    def _build_for(self, path):
        return "%s/%s" % (self.base_url, path)

    @classmethod
    def _get(cls, url, params=None):
        try:
            response = requests.get(url, timeout=5, params=params)
        except requests.exceptions.RequestException as e:
            print('bithumb get' + url + ' failed: ' + str(e))
        else:
            if response.status_code == requests.codes.ok:
                return response.json()

    def ticker(self, currency):
        """
        https://api.bithumb.com/public/ticker/eth
        """
        path = "public/ticker/%s" % currency
        url = self._build_for(path)

        return self._get(url)

    def depth(self, currency):
        """
        这里的currency指的是market_currency, base_currency为krw
        https://api.bithumb.com/public/orderbook/eth
        :param currency: eth
        "data": {
            "timestamp": "1510145644014",
            "payment_currency": "KRW",
            "order_currency": "ETH",
            "bids": [
                {
                "quantity": "81.46910000",
                "price": "336500"
                },
                {
                "quantity": "9.45210000",
                "price": "336450"
                }
            ],
            "asks": [
                {
                "quantity": "10.04779881",
                "price": "336750"
                },
                {
                "quantity": "50.00000000",
                "price": "336800"
                }
            ]
        }
        """
        path = "public/orderbook/%s" % currency
        url = self._build_for(path)

        params = {
            'count': 5
        }
        return self._get(url, params)


class PrivateClient(PublicClient):
    def __init__(self, api_key, api_secret):
        super(PrivateClient, self).__init__()
        self._key = api_key
        self._secret = api_secret
        self.contents = ''

    def http_body_callback(self, buf):
        self.contents = buf

    @classmethod
    def micro_time(cls, get_as_float=False):
        if get_as_float:
            return time.time()
        else:
            return '%f %d' % math.modf(time.time())

    @classmethod
    def micro_sec_time(cls):
        mt = cls.micro_time(False)
        mt_array = mt.split(" ")[:2]
        return mt_array[1] + mt_array[0][2:5]

    def _api_call(self, endpoint, params):
        # 1. Api-Sign and Api-Nonce information generation.
        # 2. Request related information from the Bithumb API server.
        #
        # - nonce: it is an arbitrary number that may only be used once. (Microseconds)
        # - api_sign: API signature information created in various combinations values.

        endpoint_item_array = {
            "endpoint": endpoint
        }

        uri_array = dict(endpoint_item_array, **params)  # Concatenate the two arrays.
        e_uri_data = urllib.urlencode(uri_array)

        # Api-Nonce information generation.
        nonce = self.micro_sec_time()

        # Api-Sign information generation.
        hmac_key = self._secret
        utf8_hmac_key = hmac_key.encode('utf-8')

        hmac_data = endpoint + chr(0) + e_uri_data + chr(0) + nonce
        utf8_hmac_data = hmac_data.encode('utf-8')

        hmh = hmac.new(bytes(utf8_hmac_key), utf8_hmac_data, hashlib.sha512)
        hmac_hash_hex_output = hmh.hexdigest()
        utf8_hmac_hash_hex_output = hmac_hash_hex_output.encode('utf-8')
        utf8_hmac_hash = base64.b64encode(utf8_hmac_hash_hex_output)

        api_sign = utf8_hmac_hash
        utf8_api_sign = api_sign.decode('utf-8')

        # Connects to Bithumb API server and returns JSON result value.
        curl_handle = pycurl.Curl()
        curl_handle.setopt(pycurl.POST, 1)
        # vervose mode :: 1 => True, 0 => False
        curl_handle.setopt(pycurl.VERBOSE, 0)
        curl_handle.setopt(pycurl.POSTFIELDS, e_uri_data)

        url = self.base_url + endpoint
        curl_handle.setopt(curl_handle.URL, url)
        curl_handle.setopt(curl_handle.HTTPHEADER,
                           ['Api-Key: ' + self._key, 'Api-Sign: ' + utf8_api_sign, 'Api-Nonce: ' + nonce])
        curl_handle.setopt(curl_handle.WRITEFUNCTION, self.http_body_callback)
        curl_handle.perform()

        # Get http response status code. Just for test
        # response_code = curl_handle.getinfo(pycurl.RESPONSE_CODE)
        # print(self.contents)

        curl_handle.close()
        if self.contents:
            try:
                return json.loads(self.contents)
            except ValueError:
                return None
        else:
            return None

    def balances(self, currency):
        """
        currency必须传, 目前传ALL 有bug
        """
        endpoint = '/info/balance'
        params = {
            'currency': currency
        }
        return self._api_call(endpoint, params)

    def account(self, currency='BTC'):
        endpoint = '/info/account'
        params = {
            'currency': currency
        }
        return self._api_call(endpoint, params)

    def place_order(self, currency, price, amount, order_type):
        endpoint = '/trade/place'
        params = {
            'order_currency': currency,
            'payment_currency': 'KRW',
            'units': float(amount),
            'price': int(price),
            'type': order_type
        }
        return self._api_call(endpoint, params)

    def buy_limit(self, currency, price, amount):
        return self.place_order(currency, price, amount, 'bid')

    def sell_limit(self, currency, price, amount):
        return self.place_order(currency, price, amount, 'ask')

    def buy_market(self, currency, amount):
        endpoint = '/trade/market_buy'
        params = {
            'currency': currency,
            'units': float(amount),
        }
        return self._api_call(endpoint, params)

    def sell_market(self, currency, amount):
        endpoint = '/trade/market_sell'
        params = {
            'currency': currency,
            'units': float(amount),
        }
        return self._api_call(endpoint, params)

    def order_detail(self, currency, order_id, order_type):
        endpoint = '/info/order_detail'
        params = {
            'order_id': str(order_id),
            'type': order_type,
            'currency': currency
        }

        return self._api_call(endpoint, params)

    def cancel_order(self, order_id, currency, order_type):
        endpoint = '/trade/cancel'
        params = {
            'order_id': str(order_id),
            'type': order_type,
            'currency': currency
        }
        return self._api_call(endpoint, params)

    def get_order(self, order_id, currency, order_type, after=None, count=1):
        """
        经验证，所有参数必须传，单次只能获取一个订单信息，需要逻辑处自己存储订单id和订单类型
        after 默认为1个小时
        """
        endpoint = '/trade/orders'
        if not after:
            now = int(round(time.time() * 1000))
            before = 1000 * 60 * 60
            after = now - before
        params = {
            'order_id': str(order_id),
            'type': order_type,
            'currency': currency,
            'count': count,
            'after': after
        }
        return self._api_call(endpoint, params)
