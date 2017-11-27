#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import division

import logging

from quant import config
from quant.common import constant
from .broker import Broker
from quant.api.bithumb import PrivateClient as BtbClient


class Bithumb(Broker):
    """
    cancel_all方法未实现，因为在observer里保存订单id和type，更容易实现
    获取未完成的买单和卖单，由于必须提供order_type所以要分开获取和cancel
    """

    def __init__(self, pair_code, api_key=None, api_secret=None):
        base_currency, market_currency = self.get_available_pairs(pair_code)

        super(Bithumb, self).__init__(base_currency, market_currency, pair_code)

        self.client = BtbClient(
            api_key if api_key else config.Bithumb_API_KEY,
            api_secret if api_secret else config.Bithumb_SECRET_TOKEN)

        self.krw_available = 0.0
        self.krw_balance = 0.0

    @classmethod
    def _handle_market_place(cls, res, amount):
        order = {}
        error_message = ''
        if res:
            if 'message' in res:
                error_message = res['message']
                return order, error_message

            if 'order_id' not in res:
                error_message = 'unknown error, order success but not exist order id'
                return order, error_message
            order['order_id'] = res['order_id']
            '''却要确认是否成交'''
            if 'data' in res and len(res['data']) > 0:
                deal_amount = 0.0
                price_total = 0.0
                r_len = 0
                for item in res['data']:
                    deal_amount = float(item['units']) + deal_amount
                    price_total = float(item['price']) + price_total
                    r_len += 1

                avg_price = float(price_total / r_len)

                order.update({
                    'amount': float(amount),
                    'price': avg_price,
                    'deal_amount': deal_amount,
                    'avg_price': avg_price,
                    'status': constant.ORDER_STATE_CLOSED
                })
        return order, error_message

    @classmethod
    def _handle_limit_place(cls, res, amount, price):
        order = {}
        error_message = ''
        if res:
            if 'message' in res:
                error_message = res['message']
                return order, error_message

            if 'order_id' not in res:
                error_message = 'unknown error, order success but not exist order id'
                return order, error_message
            order['order_id'] = res['order_id']
            '''却要确认是否成交'''
            if 'data' in res and len(res['data']) > 0:
                deal_amount = 0.0
                price_total = 0.0
                r_len = 0
                for item in res['data']:
                    deal_amount = float(item['units']) + deal_amount
                    price_total = float(item['price']) + price_total
                    r_len += 1

                avg_price = float(price_total / r_len)

                order.update({
                    'amount': float(amount),
                    'price': float(price),
                    'deal_amount': deal_amount,
                    'avg_price': avg_price,
                    'status': constant.ORDER_STATE_CLOSED
                })
        return order, error_message

    def _buy_limit(self, amount, price):
        """
        Create a buy limit order, 需要返回的不只是order id, 还要成交的订单信息
        只要data里面带东西，认定该订单已成交, 但是observer依然需要未成交量diff, 所以该status不可信

        maker为成交:
        {u'status': u'0000', u'order_id': u'1510629534985', u'data': []}

        taker已成交:
        {"status":"0000","order_id":"1510630163876","data":[{"cont_id":"10725417","units":"0.001","price":"7593000","total":7593,"fee":11}]}

        """
        res = self.client.buy_limit(currency=self.pair_code, price=price, amount=amount)
        return self._handle_limit_place(res=res, amount=amount, price=price)

    def _sell_limit(self, amount, price):
        """
        Create a sell limit order,
        if order and error all is empty, is network failed
        """
        res = self.client.sell_limit(currency=self.pair_code, price=price, amount=amount)
        return self._handle_limit_place(res=res, amount=amount, price=price)

    def buy_market(self, amount):
        res = self.client.buy_market(currency=self.pair_code, amount=amount)
        return self._handle_market_place(res=res, amount=amount)

    def sell_market(self, amount):
        res = self.client.sell_market(currency=self.pair_code, amount=amount)
        return self._handle_market_place(res=res, amount=amount)

    @classmethod
    def _order_status(cls, res):
        """
        如果是已成交的订单， 应该是进不来该方法，所以status简单处理了一下，f
        :param res:
        :return:
        """
        origin_amount = float(res['units'])
        remain_amount = float(res['units_remaining'])
        deal_amount = origin_amount - remain_amount

        price = float(res['price'])

        resp = {
            'order_id': res['order_id'],
            'amount': origin_amount,
            'price': price,
            'deal_amount': deal_amount,
            'avg_price': price
        }

        if res['status'] == 'placed':
            resp['status'] = constant.ORDER_STATE_PENDING
        else:
            if origin_amount == deal_amount:
                resp['status'] = constant.ORDER_STATE_CLOSED
            else:
                resp['status'] = constant.ORDER_STATE_UNKNOWN
                assert False

        return resp

    def order_detail(self, order_id, order_type):
        return self.client.order_detail(self.pair_code, order_id=order_id, order_type=order_type)

    def get_deal_amount(self, order_id, order_type):
        """
        bithumb success order
        """
        res = self.client.order_detail(self.pair_code, order_id=order_id, order_type=order_type)
        deal_amount = 0.0
        if res:
            if 'message' in res:
                return deal_amount, res['message']
            if 'data' not in res:
                return deal_amount, 'unknown error, order_detail success but not exist data'
            if len(res['data']) <= 0:
                return deal_amount, 'unknown error, order_detail success but data len is 0'

            for item in res['data']:
                deal_amount = deal_amount + float(item['units_traded'])

            return deal_amount, None
        else:
            return None, None

    def _get_order(self, order_id, order_type=None):
        res = self.client.get_order(currency=self.pair_code, order_id=order_id, order_type=order_type)
        error_message = None
        if res:
            if 'message' in res:
                error_message = res['message']
                return None, error_message
            if 'data' not in res:
                error_message = 'unknown error, get order success but data is empty'
                return None, error_message
            res = res['data']
            if len(res) <= 0:
                error_message = 'unknown error, get order success but data len is 0'
                return None, error_message
            res = res[0]
            assert str(res['order_id']) == str(order_id)

            return self._order_status(res), error_message
        else:
            return None, error_message

    def _cancel_order(self, order_id, order_type=None):
        logging.debug("bithumb cancel order : %s that type is %s" % (order_id, order_type))
        res = self.client.cancel_order(order_id, self.pair_code, order_type)
        error_msg = ''
        if res:
            if 'message' in res:
                error_msg = res['message']
                return False, error_msg
            if res['status'] != '0000':
                error_msg = 'unknown error, has no message but status code is not 0000'
                return False, error_msg
            return True, error_msg
        else:
            return False, error_msg

    def get_balances(self):
        """Get balance"""
        res = self.client.balances(self.pair_code)

        logging.debug("bithumb get_balances response: %s" % res)
        if not res or ('data' not in res):
            return
        res = res['data']

        if 'total_krw' in res:
            self.krw_available = float(res['available_krw'])
            self.krw_balance = float(res['total_krw'])

        if 'total_bch' in res:
            self.bch_available = float(res['available_bch'])
            self.bch_balance = float(res['total_bch'])

        if 'total_btc' in res:
            self.btc_available = float(res['available_btc'])
            self.btc_balance = float(res['total_btc'])

        return res

    def _ticker(self):
        resp = self.client.ticker(self.pair_code)
        if resp and 'data' in resp:
            resp = resp['data']
            return {
                'bid': float(resp['buy_price']),
                'ask': float(resp['sell_price'])
            }

    @classmethod
    def get_available_pairs(cls, pair_code):
        """可交易的pair"""
        if pair_code == 'eth':
            base_currency = 'KRW'
            market_currency = 'ETH'
        elif pair_code == 'btc':
            base_currency = 'KRW'
            market_currency = 'btc'
        elif pair_code == 'bch':
            base_currency = 'KRW'
            market_currency = 'BCH'
        else:
            assert False
        return base_currency, market_currency
