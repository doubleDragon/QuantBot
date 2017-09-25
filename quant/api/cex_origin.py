# -*- coding: utf-8 -*-
import hashlib
import hmac
import time
from decimal import Decimal

import requests

from common import depth, account, constant, order, error

BASE_URL = 'https://cex.io/api'


class PublicClient(object):
    def __init__(self):
        self.url = BASE_URL

    def _get(self, url, params=None):
        try:
            resp = requests.get(url=url, params=params, timeout=5)
        except requests.exceptions.RequestException as e:
            print("cex get %s failed: " % url + str(e))
        else:
            if resp.status_code == requests.codes.ok:
                return resp.json()

    def depth(self, symbol):
        """
        api返回的ask是降序排列，需要转换一下
        {
            "timestamp":1505833871,
            "bids":[
                [0.07242200,0.17000000],
                [0.07232997,61.80311400]
            ],
            "asks":[
                [0.07259999,0.10000000],
                [0.07260000,0.30519200]
            ],
            "pair":"ETH:BTC",
            "id":79460657,
            "sell_total":"9719.80191000",
            "buy_total":"563.31321512"
        }
        """
        url = self.url + ("/order_book/%s/" % symbol)
        params = {
            'depth': 5
        }
        resp = self._get(url=url, params=params)
        if resp is not None:
            if u'error' in resp and resp[u'error'] is not None:
                return None
            data = {
                u'bids': [],
                u'asks': []
            }
            tmp = [u'price', u'amount']

            def fn(x):
                return Decimal(str(x))

            # sort the bids and asks
            resp[u'asks'] = sorted(resp[u'asks'], key=lambda ask_item: ask_item[0])

            for i in range(5):
                # bid is a array
                bid_dict = dict(zip(tmp, resp[u'bids'][i]))
                bid_dict = dict(zip(bid_dict.keys(), map(fn, bid_dict.values())))

                ask_dict = dict(zip(tmp, resp[u'asks'][i]))
                ask_dict = dict(zip(ask_dict.keys(), map(fn, ask_dict.values())))

                data[u'bids'].append(bid_dict)
                data[u'asks'].append(ask_dict)

            return depth.dict_to_depth(data)


class PrivateClient(PublicClient):
    def __init__(self, api_user=None, api_key=None, api_secret=None):
        super(PrivateClient, self).__init__()
        self.__user = api_user
        self.__key = api_key
        self.__secret = api_secret

    def __nonce(self):
        self.__nonce_v = '{:.10f}'.format(time.time() * 1000).split('.')[0]

    def __signature(self):
        message = self.__nonce_v + self.__user + self.__key
        return hmac.new(self.__secret, msg=message, digestmod=hashlib.sha256).hexdigest().upper()

    def __post(self, url, params=None):
        """
        Makes an API POST request using the provided parameters. Returns a
        JSON result on HTTP status code 200. In other cases it will return
        either the response object or, in case of an exception, None.
        """
        if params is None:
            params = {}
        self.__nonce()
        params.update({
            'key': self.__key,
            'signature': self.__signature(),
            'nonce': self.__nonce_v
        })

        try:
            resp = requests.post(url=url, data=params, timeout=5)
        except requests.RequestException as e:
            print("cex post %s failed: " % url + str(e))
        else:
            if resp.status_code == requests.codes.ok:
                return resp.json()

    def balance(self):
        url = BASE_URL + "/balance/"
        resp = self.__post(url=url)
        if resp is not None:
            return dict_to_account(resp)

    def place_order(self, symbol, order_type, order_amount, order_price):
        """
        return json response
            id - order id
            time - timestamp
            type - buy or sell
            price - price
            amount - amount
            pending - pending amount (if partially executed)

        error response like below:
        {u'safe': True, u'error': u'There was an error while placing your order: Invalid amount'}

        """
        url = BASE_URL + "/place_order/%s" % symbol
        params = {
            'type': order_type,
            'amount': str(order_amount),
            'price': str(order_price),
        }
        resp = self.__post(url=url, params=params)
        return dict_to_order(resp)

    def buy(self, symbol, price, amount):
        return self.place_order(symbol=symbol, order_type='buy', order_amount=amount, order_price=price)

    def sell(self, symbol, price, amount):
        return self.place_order(symbol=symbol, order_type='sell', order_amount=amount, order_price=price)

    def get_order(self, order_id):
        """
        {
            "id": "22347874",
            "type": "buy",
            "time": 1470302860316,
            "lastTxTime": "2016-08-04T09:27:47.527Z",
            "lastTx": "22347950",
            "pos": null,
            "user": "userId",
            "status": "cd",
            "symbol1": "BTC",
            "symbol2": "USD",
            "amount": "1.00000000",
            "price": "564",
            "fa:USD": "0.00",
            "ta:USD": "359.72",
            "remains": "0.36219371",
            "a:BTC:cds": "0.63780629",
            "a:USD:cds": "565.13",
            "f:USD:cds": "0.00",
            "tradingFeeMaker": "0",
            "tradingFeeTaker": "0.2",
            "tradingFeeStrategy": "Promo000Maker",
            "orderId": "22347874"
        }
        """
        url = BASE_URL + "/get_order/"
        params = {
            'id': order_id
        }
        resp = self.__post(url=url, params=params)
        return dict_to_order_detail(resp)

    def cancel_all_orders(self, symbol):
        url = BASE_URL + "/cancel_orders/%s" % symbol
        resp = self.__post(url=url)
        if resp is not None:
            return resp[u'ok'] == 'ok'

    def cancel_order(self, order_id):
        url = BASE_URL + "/cancel_order/"
        params = {
            'id': order_id
        }
        resp = self.__post(url=url, params=params)
        if resp is not None:
            return resp is True


def dict_to_account(resp):
    ac = account.Account()
    if u'BTC' in resp:
        resp = resp[u'BTC']

        available_balance = Decimal(resp[u'available'])
        frozen_balance = Decimal(resp[u'orders'])
        balance = available_balance + frozen_balance

        btc_item = account.Item(currency='btc', balance=balance, available_balance=available_balance,
                                frozen_balance=frozen_balance)
        ac.append(btc_item)
    return ac


def dict_to_order(resp):
    """返回order和error"""
    if resp is not None:
        if u'error' in resp and resp[u'error'] is not None:
            return None, error.HttpError(message=resp[u'error'])

        order_id = resp[u'id']
        order_type = resp[u'type']
        price = Decimal(str(resp[u'price']))
        amount = Decimal(str(resp[u'amount']))
        pending_amount = Decimal(str(resp[u'pending']))
        deal_amount = amount - pending_amount

        is_completed = (deal_amount == amount)
        order_status = constant.ORDER_STATE_CLOSED if is_completed else constant.ORDER_STATE_PENDING

        return order.Order(order_id=order_id, price=price, status=order_status, order_type=order_type,
                           amount=amount, deal_amount=deal_amount), None
    else:
        return None, error.HttpError()


def dict_to_order_detail(resp):
    """
    get_order接口返回数据转换，和place order返回的格式不一样，需要单独转换
    status – "d" — done (fully executed), "c" — canceled (not executed), "cd" — cancel-done (partially executed)
    """

    if resp is not None:
        order_id = resp[u'id']
        order_type = resp[u'type']
        price = Decimal(str(resp[u'price']))
        amount = Decimal(str(resp[u'amount']))
        pending_amount = Decimal(str(resp[u'remains']))
        deal_amount = amount - pending_amount

        status = resp[u'status']

        # is_completed = (deal_amount == amount)

        if status == 'd':
            order_status = constant.ORDER_STATE_CLOSED
        elif status == 'c':
            order_status = constant.ORDER_STATE_CANCELED
        else:
            order_status = constant.ORDER_STATE_PENDING
        return order.Order(order_id=order_id, price=price, status=order_status, order_type=order_type,
                           amount=amount, deal_amount=deal_amount), None
    else:
        return None, error.HttpError()
