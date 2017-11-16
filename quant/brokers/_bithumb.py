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

    def _buy_limit(self, amount, price):
        """
        Create a buy limit order, 需要返回的不只是order id, 还要成交的订单信息
        只要data里面带东西，认定该订单已成交, 但是observer依然需要未成交量diff, 所以该status不可信

        maker为成交:
        {u'status': u'0000', u'order_id': u'1510629534985', u'data': []}

        taker已成交:
        {"status":"0000","order_id":"1510630163876","data":[{"cont_id":"10725417","units":"0.001","price":"7593000","total":7593,"fee":11}]}

        """
        res = self.client.buy(currency=self.pair_code, price=price, amount=amount)
        order_id = None
        order = None
        if res and 'order_id' in res:
            order_id = res['order_id']
            '''却要确认是否成交'''
            if 'data' in res and len(res['data']) > 0:
                deal_amount = 0.0
                origin_amount = float(amount)
                for item in res['data']:
                    deal_amount = float(item['units']) + deal_amount
                order = {
                    'order_id': order_id,
                    'amount': origin_amount,
                    'price': float(price),
                    'deal_amount': deal_amount,
                    'avg_price': float(price),
                    'status': constant.ORDER_STATE_CLOSED
                }
        return order_id, order

    def _sell_limit(self, amount, price):
        """Create a sell limit order"""
        res = self.client.sell(currency=self.pair_code, price=price, amount=amount)
        order_id = None
        order = None
        if res and 'order_id' in res:
            order_id = res['order_id']
            '''却要确认是否成交'''
            if 'data' in res and len(res['data']) > 0:
                deal_amount = 0.0
                for item in res['data']:
                    deal_amount = float(item['units']) + deal_amount
                order = {
                    'order_id': order_id,
                    'amount': float(amount),
                    'price': float(price),
                    'deal_amount': deal_amount,
                    'avg_price': float(price),
                    'status': constant.ORDER_STATE_CLOSED
                }
        return order_id, order

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
                print('bithumb _order_status res: ' + str(res))
                assert False

        return resp

    def order_detail(self, order_id, order_type):
        return self.client.order_detail(self.pair_code, order_id=order_id, order_type=order_type)

    def get_deal_amount(self, order_id, order_type):
        res = self.client.order_detail(self.pair_code, order_id=order_id, order_type=order_type)

        deal_amount = 0.0
        if res and 'data' in res:
            for item in res['data']:
                deal_amount = deal_amount + float(item['units_traded'])

        return deal_amount

    def _get_order(self, order_id, order_type=None):
        res = self.client.get_order(currency=self.pair_code, order_id=order_id, order_type=order_type)
        if not res or 'data' not in res:
            return None
        res = res['data']
        if len(res) <= 0:
            return None
        res = res[0]
        logging.debug('get_order id: %s, res: %s' % (order_id, res))
        assert str(res['order_id']) == str(order_id)

        return self._order_status(res)

    def _cancel_order(self, order_id, order_type=None):
        logging.debug("bithumb cancel order : %s that type is %s" % (order_id, order_type))
        res = self.client.cancel_order(order_id, self.pair_code, order_type)
        if not res:
            return False
        if res['status'] == '0000':
            return True
        else:
            return False

    def get_balances(self):
        """Get balance"""
        res = self.client.balances(self.pair_code)

        logging.debug("bithumb get_balances response: %s" % res)
        if not res and 'data' in res:
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
        if resp:
            return {
                'bid': float(resp['bid']),
                'ask': float(resp['ask'])
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
