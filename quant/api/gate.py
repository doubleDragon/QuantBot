#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import hashlib
import hmac
import urllib

import requests
import time

BASE_URL = "http://data.gate.io/api2/1"


def url_for(path, path_arg=None, parameters=None):
    url = "%s/%s" % (BASE_URL, path)
    return url


class PublicClient(object):
    @classmethod
    def _get(cls, url, params=None):
        try:
            response = requests.get(url, timeout=5, params=params)
        except requests.exceptions.RequestException as e:
            print('gateio get' + url + ' failed: ' + str(e))
        else:
            if response.status_code == requests.codes.ok:
                return response.json()

    def depth(self, symbol):
        """http://data.gate.io/api2/1/orderBook/eth_btc"""
        path = 'orderBook/%s' % symbol.lower()
        return self._get(url_for(path))


class PrivateClient(PublicClient):
    def __init__(self, api_key, api_secret):
        PublicClient.__init__(self)
        self._api_key = api_key
        self._api_secret = api_secret
        self._url = "https://api.gate.io/api2/1/private"

    def __url_for(self, path):
        return "%s/%s" % (self._url, path)

    @classmethod
    def __nonce(cls):
        return str(time.time()).split('.')[0]

    def __signature(self, params):
        return hmac.new(self._api_secret.encode(), params.encode(), digestmod=hashlib.sha512).hexdigest()

    def _post(self, url, params):
        nonce = self.__nonce()
        params['nonce'] = nonce
        params = urllib.urlencode(params)
        headers = {"Content-Type": "application/x-www-form-urlencoded",
                   "Key": self._api_key,
                   "Sign": self.__signature(params)}
        try:
            resp = requests.post(url, data=params, headers=headers)
        except requests.exceptions.RequestException as e:
            print('gateio post' + ' failed: ' + str(e))
        else:
            if resp.status_code == requests.codes.ok:
                return resp.json()

    def balance(self):
        url = self.__url_for('balances')
        return self._post(url, {})

    def buy(self, symbol, price, amount):
        params = {
            'currencyPair': symbol,
            'rate': str(price),
            'amount': str(amount),
        }
        url = self.__url_for('buy')
        return self._post(url, params)

    def sell(self, symbol, price, amount):
        params = {
            'currencyPair': symbol,
            'rate': str(price),
            'amount': str(amount),
        }
        url = self.__url_for('sell')
        return self._post(url, params)

    def get_order(self, order_id, symbol):
        params = {
            'orderNumber': str(order_id),
            'currencyPair': symbol
        }
        url = self.__url_for('getOrder')
        return self._post(url, params)

    def cancel_order(self, order_id, symbol):
        params = {
            'orderNumber': str(order_id),
            'currencyPair': symbol
        }
        url = self.__url_for('cancelOrder')
        return self._post(url, params)
