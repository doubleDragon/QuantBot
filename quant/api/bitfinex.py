#!/usr/bin/python
# -*- coding: UTF-8 -*-

from __future__ import absolute_import
import requests
import json
import base64
import hmac
import hashlib
import time

from decimal import Decimal

from quant.common import constant

PROTOCOL = "https"
HOST = "api.bitfinex.com"
VERSION = "v1"

BASE_URL = u"{0:s}://{1:s}/{2:s}".format(PROTOCOL, HOST, VERSION)

# HTTP request timeout in seconds
TIMEOUT = 5.0


class PublicClient(object):
    """
    Client for the bitfinex.com API.

    See https://www.bitfinex.com/pages/api for API documentation.
    """

    def __init__(self):
        pass

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

    def symbols(self):
        """
        GET /symbols

        curl https://api.bitfinex.com/v1/symbols
        ['btcusd','ltcusd','ltcbtc']
        """
        return self._get(self.url_for('symbols'))

    def ticker(self, symbol):
        """
        GET /ticker/:symbol

        curl https://api.bitfinex.com/v1/ticker/btcusd
        {
            'ask': '562.9999',
            'timestamp': '1395552290.70933607',
            'bid': '562.25',
            'last_price': u'562.25',
            'mid': u'562.62495'}
        """
        resp = self._get(self.url_for('ticker/%s', symbol.lower()))
        if resp is not None:
            return dict_to_ticker(resp)

    def depth(self, symbol, parameters=None):
        """
        curl "https://api.bitfinex.com/v1/book/btcusd"

        {"bids":[{"price":"561.1101","amount":"0.985","timestamp":"1395557729.0"}],"asks":[{"price":"562.9999","amount":"0.985","timestamp":"1395557711.0"}]}

        The 'bids' and 'asks' arrays will have multiple bid and ask dicts.

        Optional parameters

        limit_bids (int): Optional. Limit the number of bids returned. May be 0 in which case the array of bids is empty. Default is 50.
        limit_asks (int): Optional. Limit the number of asks returned. May be 0 in which case the array of asks is empty. Default is 50.

        eg.
        curl "https://api.bitfinex.com/v1/book/btcusd?limit_bids=1&limit_asks=0"
        {"bids":[{"price":"561.1101","amount":"0.985","timestamp":"1395557729.0"}],"asks":[]}

        """
        if parameters is None:
            parameters = {}
        parameters.update({
            'limit_bids': 5,
            'limit_asks': 5
        })
        return self._get(self.url_for('book/%s', path_arg=symbol.lower(), parameters=parameters))
        # resp = self._get(self.url_for('book/%s', path_arg=symbol.lower(), parameters=parameters))
        # if resp is not None:
        #     data = {
        #         u'bids': [],
        #         u'asks': []
        #     }
        #
        #     def fn(x):
        #         return Decimal(x)
        #
        #     for i in range(5):
        #         del resp[u'bids'][i][u'timestamp']
        #         del resp[u'asks'][i][u'timestamp']
        #
        #         bid_dict = resp[u'bids'][i]
        #         bid_dict = dict(zip(bid_dict.keys(), map(fn, bid_dict.values())))
        #
        #         ask_dict = resp[u'asks'][i]
        #         ask_dict = dict(zip(ask_dict.keys(), map(fn, ask_dict.values())))
        #
        #         data[u'bids'].append(bid_dict)
        #         data[u'asks'].append(ask_dict)
        #     return depth.dict_to_depth(data)

    @classmethod
    def _get(cls, url):
        try:
            resp = requests.get(url, timeout=TIMEOUT)
        except requests.exceptions.RequestException as e:
            raise e
        else:
            if resp.status_code == requests.codes.ok:
                return resp.json()

    @classmethod
    def _build_parameters(cls, parameters):
        # sort the keys so we can test easily in Python 3.3 (dicts are not
        # ordered)
        keys = list(parameters.keys())
        keys.sort()

        return '&'.join(["%s=%s" % (k, parameters[k]) for k in keys])


class PrivateClient(PublicClient):
    def __init__(self, api_key, api_secret):
        PublicClient.__init__(self)
        self.api_key = api_key
        self.api_secret = api_secret

    @property
    def _nonce(self):
        """
        Returns a nonce
        Used in authentication
        """

        return str(int(round(time.time() * 10000)))

    def _sign_payload(self, payload):
        j = json.dumps(payload)
        data = base64.standard_b64encode(j.encode('utf-8'))

        h = hmac.new(self.api_secret.encode('utf-8'), data, hashlib.sha384)
        signature = h.hexdigest()
        return {
            "X-BFX-APIKEY": self.api_key,
            "X-BFX-SIGNATURE": signature,
            "X-BFX-PAYLOAD": data
        }

    def _post(self, url, headers):
        try:
            resp = requests.post(url, headers=headers, verify=True)
        except requests.exceptions.RequestException as e:
            print('Bitfinex post' + url + ' failed: ' + str(e))
        else:
            if resp.status_code == requests.codes.ok:
                return resp.json()

    def place_order(self, amount, price, side, ord_type, symbol, exchange='bitfinex'):
        """
        委单，包括exchange和margin
        Submit a new order.
        :param amount:
        :param price:
        :param side:
        :param ord_type:
        :param symbol:
        :param exchange:
        :return: order id
        """
        payload = {

            "request": "/v1/order/new",
            "nonce": self._nonce,
            "symbol": symbol,
            "amount": str(amount),
            "price": str(price),
            "exchange": exchange,
            "side": side,
            "type": ord_type

        }

        signed_payload = self._sign_payload(payload)
        url = BASE_URL + "/order/new"
        resp = self._post(url=url, headers=signed_payload)
        return dict_to_order(resp)

    def buy(self, symbol, amount, price):
        side = 'buy'
        order_type = 'exchange limit'
        return self.place_order(symbol=symbol, amount=amount, price=price, side=side, ord_type=order_type)

    def sell(self, symbol, amount, price):
        side = 'sell'
        order_type = 'exchange limit'
        return self.place_order(symbol=symbol, amount=amount, price=price, side=side, ord_type=order_type)

    def margin_sell(self, symbol, amount, price):
        side = 'sell'
        order_type = 'limit'
        return self.place_order(symbol=symbol, amount=amount, price=price, side=side, ord_type=order_type)

    def _balances_inner(self):
        """
        Fetch balances

        :return:
        """
        payload = {
            "request": "/v1/balances",
            "nonce": self._nonce
        }

        signed_payload = self._sign_payload(payload)
        url = BASE_URL + "/balances"
        return self._post(url=url, headers=signed_payload)

    def balance(self):
        """
        bal_type: exchange or trading or deposit
        :return: btc and usd
        """
        return self._balances_inner()
        # if resp is not None:
            # filter wrong type information
            # def is_right_symbol(pp):
            #     return (pp[u'currency'] == u'btc' or pp[u'currency'] == u'usd') and pp[u'type'] == bal_type
            #
            # data = filter(is_right_symbol, resp)
            #
            # if data is not None:
            #     return dict_to_account(data)

    def get_order(self, order_id):
        """
        Get the status of an order. Is it active? Was it cancelled? To what extent has it been executed? etc.
        :param order_id: must
        :return:
        """
        payload = {
            "request": "/v1/order/status",
            "nonce": self._nonce,
            "order_id": order_id
        }

        signed_payload = self._sign_payload(payload)
        url = BASE_URL + "/order/status"
        resp = self._post(url=url, headers=signed_payload)
        return dict_to_order(resp)

    def cancel_order(self, order_id):
        payload = {
            "request": "/v1/order/cancel",
            "nonce": self._nonce,
            "order_id": order_id
        }

        signed_payload = self._sign_payload(payload)

        url = BASE_URL + "/order/cancel"
        resp = self._post(url=url, headers=signed_payload)
        if resp is not None:
            return resp[u'id'] is not None

    def cancel_all_orders(self):
        """
        Cancel all orders.

        :return:
        """
        payload = {
            "request": "/v1/order/cancel/all",
            "nonce": self._nonce,
        }

        signed_payload = self._sign_payload(payload)
        url = BASE_URL + "/order/cancel/all"
        resp = self._post(url=url, headers=signed_payload)
        if resp is not None:
            return True


def dict_to_account(data):
    ac = account.Account()
    for item in data:
        balance = Decimal(item[u'amount'])
        available_balance = Decimal(item[u'available'])
        frozen_balance = balance - available_balance
        currency = item[u'currency']

        bean = account.Item(currency=currency, balance=balance, available_balance=available_balance,
                            frozen_balance=frozen_balance)
        ac.append(bean)
    return ac


def dict_to_order(resp):
    if resp is not None:
        origin_amount = Decimal(str(resp[u'original_amount']))
        executed_amount = Decimal(str(resp[u'executed_amount']))

        is_cancelled = resp[u'is_cancelled']
        is_completed = (executed_amount == origin_amount)
        if is_completed:
            order_status = constant.ORDER_STATE_CLOSED
        else:
            if is_cancelled:
                order_status = constant.ORDER_STATE_CANCELED
            else:
                order_status = constant.ORDER_STATE_PENDING
        order_id = resp[u'id']
        price = resp[u'price']
        order_type = resp[u'type']
        return order.Order(order_id=order_id, price=price, status=order_status, order_type=order_type,
                           amount=origin_amount, deal_amount=executed_amount), None
    else:
        return None, error.HttpError()


def dict_to_order_result(resp):
    if resp is not None:
        order_id = resp['order_id']
        if order_id is not None and order_id > 0:
            return order.OrderResult(order_id=order_id)
        else:
            return order.OrderResult(error='order id not exists')
    else:
        return order.OrderResult(error='unknown error, may be balance not enough')


def dict_to_ticker(resp):
    sell = Decimal(resp[u'ask'])
    buy = Decimal(resp[u'bid'])
    last = Decimal(resp[u'last_price'])
    data = ticker.Ticker(buy=buy, sell=sell, last=last)
    return data
