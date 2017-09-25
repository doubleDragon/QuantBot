#!/usr/bin/python
# -*- coding: UTF-8 -*-
import hashlib
import hmac
import time
from decimal import Decimal
from urllib import urlencode
from config import settings

import requests

from common import depth, order, constant, account

PROTOCOL = "https"
HOST = "api.liqui.io/api"
VERSION = "3"

BASE_URL = u"{0:s}://{1:s}/{2:s}".format(PROTOCOL, HOST, VERSION)


class LiquiApiError(Exception):
    pass


def url_for(path, path_arg=None, parameters=None):
    url = "%s/%s" % (BASE_URL, path)
    return url


class PublicClient(object):
    def _get(self, url):
        try:
            response = requests.get(url, timeout=5)
        except requests.exceptions.RequestException as e:
            print('liqui get' + url + ' failed: ' + str(e))
        else:
            if response.status_code == requests.codes.ok:
                return response.json()

    def depth(self, symbol):
        path = 'depth/%s' % symbol
        resp = self._get(url_for(path))
        if resp is not None and symbol in resp:
            data = {
                u'bids': [],
                u'asks': []
            }
            tmp = [u'price', u'amount']

            def fn(x):
                return Decimal(str(x))

            asks = resp[symbol][u'asks']
            bids = resp[symbol][u'bids']

            for i in range(5):
                # bid is a array
                bid_dict = dict(zip(tmp, bids[i]))
                bid_dict = dict(zip(bid_dict.keys(), map(fn, bid_dict.values())))

                ask_dict = dict(zip(tmp, asks[i]))
                ask_dict = dict(zip(ask_dict.keys(), map(fn, ask_dict.values())))

                # bid_dict = dict(zip(tmp, bids[i]))
                # ask_dict = dict(zip(tmp, asks[i]))

                data[u'bids'].append(bid_dict)
                data[u'asks'].append(ask_dict)

            return depth.dict_to_depth(data)


class PrivateClient(PublicClient):
    def __init__(self, api_key, api_secret):
        PublicClient.__init__(self)
        self._api_key = api_key
        self._api_secret = api_secret

    @property
    def _nonce(self):
        """
        Returns a nonce
        Used in authentication
        """
        return int(time.time())
        # return str(int(round(time.time() * 10000)))

    def __sign(self, params):
        sig = hmac.new(self._api_secret.encode(), params.encode(), hashlib.sha512)
        return sig.hexdigest()

    def _post(self, method, params):
        params['method'] = method
        params['nonce'] = str(self._nonce)
        params = urlencode(params)

        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Key": self._api_key,
                   "Sign": self.__sign(params)}
        try:
            resp = requests.post('https://api.liqui.io/tapi', data=params, headers=headers)
        except requests.exceptions.RequestException as e:
            print('liqui post' + ' failed: ' + str(e))
        else:
            if resp.status_code == requests.codes.ok:
                return resp.json()

    def _get_info(self):
        """
        need to parse and convert to account object
        :return:
        """
        return self._post('getInfo', {})

    def balance(self):
        """
        dict funds
        need to parse and convert to account object
        :return: account object
        """
        resp = self._get_info()
        if resp is not None:
            return dict_to_account(resp)

    def trade(self, symbol, ttype, trate, tamount):
        """
        :param symbol: such as ltc_btc
        :param ttype: buy or sell
        :param trate: order price
        :param tamount: order amount
        :return: order id
        """
        params = {
            "pair": str(symbol),
            "type": str(ttype),
            "rate": str(trate),
            "amount": str(tamount)}
        resp = self._post('Trade', params)
        return dict_to_order_result(resp)

    def buy(self, symbol, price, amount):
        return self.trade(symbol=symbol, ttype='buy', trate=price, tamount=amount)

    def sell(self, symbol, price, amount):
        return self.trade(symbol, 'sell', price, amount)

    def get_order(self, order_id):
        """
        response detail
        {
            'stat': {
                'isSuccess': True,
                'errors': 'None',
                'serverTime': '00:00:00.0010993',
                'time': '00:00:08.7011518'},
            'return': {
                '63613389': {
                    'status': 0,
                    'timestamp_created': 1505352914,
                    'rate': 0.01501,
                    'amount': 0.1,                      //这个是未成交数
                    'pair': 'ltc_btc',
                    'start_amount': 0.1,                //初始订单数,  成交数=start-amount
                    'type': u'buy'
                 }
            },
            'success': 1}
        """
        params = {"order_id": order_id}
        resp = self._post('OrderInfo', params)
        if resp is not None:
            return dict_to_order(resp, order_id)

    def cancel_order(self, order_id):
        params = {"order_id": order_id}
        resp = self._post('CancelOrder', params)
        if resp is not None:
            return resp[u'success'] == 1

    def active_orders(self):
        params = {}
        resp = self._post('ActiveOrders', params)
        if resp is not None and u'return' in resp:
            resp = resp[u'return']
            keys = resp.keys()
            if keys is None:
                return []
            else:
                return keys

    def trade_history(self, symbol):
        params = {
            "pair": symbol
        }
        return self._post('TradeHistory', params)


def dict_to_order_result(resp):
    if resp is None:
        return order.OrderResult()
    else:
        if resp[u'success'] == 1:
            if (u'return' in resp) and (u'order_id' in resp[u'return']):
                order_id = resp[u'return'][u'order_id']
                if order_id >= 0:
                    # 下单成功
                    matched = (int(order_id) == 0)
                    return order.OrderResult(order_id=order_id, matched=matched)
                else:
                    # 需要去其他地方查询
                    return order.OrderResult(error='order id less than 0, id=' + str(order_id))
            else:
                return order.OrderResult(error='stat is success but not return order id')
        else:
            return order.OrderResult(code=resp[u'code'], error=resp[u'error'])


def dict_to_order(resp, order_id_int):
    if u'return' in resp:
        resp1 = resp[u'return']
        order_id = str(order_id_int)
        if order_id is not None:
            data = resp1[order_id]
            price = data[u'rate']
            amount = data[u'start_amount']
            deal_amount = amount - data[u'amount']
            order_type = data[u'type']
            order_status = order.get_status(constant.EX_LQ, data[u'status'])
            return order.Order(order_id, price, order_status, order_type, amount, deal_amount)


def dict_to_account(resp):
    if u'return' in resp:
        if u'funds' in resp[u'return']:
            resp = resp[u'return'][u'funds']
            balance = resp[u'btc']
            btc_item = account.Item(currency='btc', balance=balance)

            ac = account.Account()
            ac.append(btc_item)
            return ac
