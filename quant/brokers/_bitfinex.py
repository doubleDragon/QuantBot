#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import division

from quant import config
from .broker import Broker
from quant.api.bitfinex import PrivateClient as BfxClient
from quant.common import constant
import logging


# python -m quant.cli -m Bitfinex_BCH_BTC get-balance

class Bitfinex(Broker):
    def __init__(self, pair_code, api_key=None, api_secret=None):
        base_currency, market_currency = self.get_available_pairs(pair_code)

        super(Bitfinex, self).__init__(base_currency, market_currency, pair_code)

        self.client = BfxClient(
            api_key if api_key else config.Bitfinex_API_KEY,
            api_secret if api_secret else config.Bitfinex_SECRET_TOKEN)

        # self.get_balances()
        self.bt1_available = 0.0
        self.bt1_balance = 0.0

        self.bt2_available = 0.0
        self.bt2_balance = 0.0

    def _buy_limit(self, amount, price):
        """Create a buy limit order"""
        res = self.client.place_order(
            str(amount),
            str(price),
            'buy',
            'exchange limit',
            symbol=self.pair_code)
        if res:
            if 'order_id' in res:
                return res['order_id']
            else:
                error_msg = 'unknown error, order_id not exists'
                if 'message' in res:
                    error_msg = res['message']
                raise ValueError(error_msg)
        else:
            raise ValueError('response is None')

    def _sell_limit(self, amount, price):
        """Create a sell limit order"""
        res = self.client.place_order(
            str(amount),
            str(price),
            'sell',
            'exchange limit',
            symbol=self.pair_code)
        if res:
            if 'order_id' in res:
                return res['order_id']
            else:
                error_msg = 'unknown error, order_id not exists'
                if 'message' in res:
                    error_msg = res['message']
                raise ValueError(error_msg)
        else:
            raise ValueError('response is None')

    @classmethod
    def _order_status(cls, res):
        resp = {
            'order_id': res['id'],
            'amount': float(res['original_amount']),
            'price': float(res['price']),
            'deal_amount': float(res['executed_amount']),
            'avg_price': float(res['avg_execution_price'])
        }

        is_cancelled = res['is_cancelled']
        is_completed = (resp['amount'] == resp['deal_amount'])
        if is_completed:
            resp['status'] = constant.ORDER_STATE_CLOSED
        else:
            if is_cancelled:
                resp['status'] = constant.ORDER_STATE_CANCELED
            else:
                resp['status'] = constant.ORDER_STATE_PENDING

        return resp

    def _get_order(self, order_id, order_type=None):
        res = self.client.get_order(int(order_id))
        if not res:
            raise ValueError('response is None')
        if 'message' in res:
            raise ValueError(res['message'])
        logging.debug('get_order id: %s, res: %s' % (order_id, res))

        assert str(res['id']) == str(order_id)
        return self._order_status(res)

    def _cancel_order(self, order_id, order_type=None):
        res = self.client.cancel_order(int(order_id))
        if not res:
            raise ValueError('response is None')
        if 'message' in res:
            raise ValueError(res['message'])

        assert str(res['id']) == str(order_id)

        resp = self._order_status(res)
        if resp:
            return True
        else:
            return False

    def _cancel_all(self):
        return self.client.cancel_all_orders()

    def _get_balances(self):
        """Get balance"""
        res = self.client.balances()

        logging.debug("bitfinex get_balances response: %s" % res)
        if not res:
            raise ValueError('response is None')

        if 'message' in res:
            raise ValueError(res['message'])

        for entry in res:
            if entry['type'] != 'exchange':
                continue

            currency = entry['currency']
            if currency not in (
                    'btc', 'bch', 'usd', 'bt1', 'bt2', 'zec'):
                continue

            if currency == 'bch':
                self.bch_available = float(entry['available'])
                self.bch_balance = float(entry['amount'])

            elif currency == 'btc':
                self.btc_available = float(entry['available'])
                self.btc_balance = float(entry['amount'])

            elif currency == 'zec':
                self.zec_available = float(entry['available'])
                self.zec_balance = float(entry['amount'])

            elif currency == 'usd':
                self.usd_available = float(entry['available'])
                self.usd_balance = float(entry['amount'])

            elif currency == 'bt1':
                self.bt1_available = float(entry['available'])
                self.bt1_balance = float(entry['amount'])

            elif currency == 'bt2':
                self.bt2_available = float(entry['available'])
                self.bt2_balance = float(entry['amount'])
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
        if pair_code == 'ethusd':
            base_currency = 'USD'
            market_currency = 'ETH'
        elif pair_code == 'ethbtc':
            base_currency = 'BTC'
            market_currency = 'ETH'
        elif pair_code == 'btcusd':
            base_currency = 'USD'
            market_currency = 'BTC'
        elif pair_code == 'bt1usd':
            base_currency = 'USD'
            market_currency = 'BT1'
        elif pair_code == 'bt2usd':
            base_currency = 'USD'
            market_currency = 'BT2'
        elif pair_code == 'bt1btc':
            base_currency = 'BTC'
            market_currency = 'BT1'
        elif pair_code == 'bt2btc':
            base_currency = 'BTC'
            market_currency = 'BT2'
        elif pair_code == 'bchusd':
            base_currency = 'USD'
            market_currency = 'BCH'
        elif pair_code == 'bchbtc':
            base_currency = 'BTC'
            market_currency = 'BCH'
        elif pair_code == 'zecusd':
            base_currency = 'USD'
            market_currency = 'ZEC'
        elif pair_code == 'neousd':
            base_currency = 'USD'
            market_currency = 'NEO'
        elif pair_code == 'neobtc':
            base_currency = 'BTC'
            market_currency = 'NEO'
        elif pair_code == 'neoeth':
            base_currency = 'ETH'
            market_currency = 'NEO'
        elif pair_code == 'ioteth':
            base_currency = 'ETH'
            market_currency = 'IOT'
        elif pair_code == 'iotbtc':
            base_currency = 'BTC'
            market_currency = 'IOT'
        elif pair_code == 'iotusd':
            base_currency = 'USD'
            market_currency = 'IOT'
        else:
            assert False
        return base_currency, market_currency

    def get_min_stock(self):
        resp = self.client.symbols_details()
        if resp:
            for item in resp:
                if item['pair'] == self.pair_code:
                    return float(item['minimum_order_size'])
