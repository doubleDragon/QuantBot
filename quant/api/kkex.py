#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from urllib import urlencode
from urlparse import urljoin

import requests
from hashlib import md5

BASE_URL = 'https://kkex.com/api/v1'
TIMEOUT = 5


class PublicClient(object):
    def __init__(self):
        super(PublicClient, self).__init__()

    @classmethod
    def _build_parameters(cls, parameters):
        # sort the keys so we can test easily in Python 3.3 (dicts are not
        # ordered)
        keys = list(parameters.keys())
        keys.sort()

        return '&'.join(["%s=%s" % (k, parameters[k]) for k in keys])

    def url_for(self, path, path_arg=None, parameters=None):

        # build the basic url
        url = "%s/%s" % (BASE_URL, path)

        # If there is a path_arh, interpolate it into the URL.
        # In this case the path that was provided will need to have string
        # interpolation characters in it, such as PATH_TICKER
        if path_arg:
            url = url % (path_arg)

        # Append any parameters to the URL.
        if parameters:
            url = "%s?%s" % (url, self._build_parameters(parameters))

        return url

    @classmethod
    def _get(cls, url, params=None):
        try:
            resp = requests.get(url, timeout=TIMEOUT, params=params)
        except requests.exceptions.RequestException as e:
            raise e
        else:
            if resp.status_code == requests.codes.ok:
                return resp.json()

    def depth(self, symbol):
        url = self.url_for('depth')
        params = {
            'symbol': symbol
        }
        return self._get(url, params)


class PrivateClient(PublicClient):
    def __init__(self, api_key, api_secret):
        super(PrivateClient, self).__init__()
        self._key = api_key
        self._secret = api_secret
        self.api_root = 'https://kkex.com'

    def _sign(self, params):
        sign = list(sorted(params.items()) + [('secret_key', self._secret)])
        signer = md5()
        signer.update(urlencode(sign).encode('utf-8'))
        return signer.hexdigest().upper()

    def _post(self, path, params=None):
        if params is None:
            params = {}

        params['api_key'] = self._key
        sign = self._sign(params)
        params['sign'] = sign

        url = urljoin(self.api_root, path)
        try:
            resp = requests.post(url, data=params, timeout=5)
        except requests.exceptions.RequestException as e:
            raise e
        else:
            if resp.status_code == requests.codes.ok:
                return resp.json()

    def profile(self):
        return self._post('/api/v1/profile')

    def balance(self):
        return self._post('/api/v1/userinfo')

    def buy_limit(self, symbol, amount, price):
        params = {
            'symbol': symbol,
            'type': 'buy',
            'price': price,
            'amount': amount
        }
        return self._post('/api/v1/trade', params)

    def sell_limit(self, symbol, amount, price):
        params = {
            'symbol': symbol,
            'type': 'sell',
            'price': price,
            'amount': amount
        }
        return self._post('/api/v1/trade', params)

    def cancel_order(self, symbol, order_id):
        params = {'symbol': symbol,
                  'order_id': order_id}
        return self.trade_api('/api/v1/cancel_order', params)

    def order_info(self, symbol, order_id):
        params = {
            'symbol': symbol,
            'order_id': order_id
        }
        return self._post('/api/v1/order_info', params)

    def orders_info(self, symbol, order_ids):
        order_id_p = ','.join(order_ids)
        params = {
            'symbol': symbol,
            'order_id': order_id_p
        }
        return self._post('/api/v1/orders_info', params)

    def get_orders_history(self, symbol, status=0, page=1, pagesize=10):
        params = {
            'symbol': symbol,
            'status': status,
            'current_page': page,
            'page_length': pagesize
        }
        return self._post('/api/v1/order_history', params)
