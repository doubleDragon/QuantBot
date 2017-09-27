# coding=utf-8
# Copyright (C) 2017, Philsong <songbohr@gmail.com>
from quant import config
from .broker import Broker
from quant.api.bitfinex import PrivateClient as BfxClient
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

    @classmethod
    def get_available_pairs(cls, pair_code):
        """可交易的pair"""
        if pair_code == 'bchusd':
            base_currency = 'USD'
            market_currency = 'BCH'
        elif pair_code == 'bchbtc':
            base_currency = 'BTC'
            market_currency = 'BCH'
        elif pair_code == 'btcusd':
            base_currency = 'USD'
            market_currency = 'USD'
        else:
            assert False
        return base_currency, market_currency

    def _buy_limit(self, amount, price):
        """Create a buy limit order"""
        res = self.client.place_order(
            str(amount),
            str(price),
            'buy',
            'exchange limit',
            symbol=self.pair_code)
        return res['order_id']

    def _sell_limit(self, amount, price):
        """Create a sell limit order"""
        res = self.client.place_order(
            str(amount),
            str(price),
            'sell',
            'exchange limit',
            symbol=self.pair_code)
        return res['order_id']

    @classmethod
    def _order_status(cls, res):
        resp = {
            'order_id': res['id'],
            'amount': float(res['original_amount']),
            'price': float(res['price']),
            'deal_amount': float(res['executed_amount']),
            'avg_price': float(res['avg_execution_price'])
        }

        if res['is_live']:
            resp['status'] = 'OPEN'
        else:
            resp['status'] = 'CLOSE'

        return resp

    def _get_order(self, order_id):
        res = self.client.get_order(int(order_id))
        logging.info('get_order: %s' % res)

        assert str(res['id']) == str(order_id)
        return self._order_status(res)

    def _cancel_order(self, order_id):
        res = self.client.cancel_order(int(order_id))
        assert str(res['id']) == str(order_id)

        resp = self._order_status(res)
        if resp:
            return True
        else:
            return False

    def get_balances(self):
        """Get balance"""
        res = self.client.balances()

        # logging.debug("bitfinex get_balances response: %s" % res)

        for entry in res:
            if entry['type'] != 'exchange':
                continue

            currency = entry['currency'].upper()
            if currency not in (
                    'BTC', 'BCH'):
                continue

            if currency == 'BCH':
                self.bch_available = float(entry['available'])
                self.bch_balance = float(entry['amount'])

            elif currency == 'BTC':
                self.btc_available = float(entry['available'])
                self.btc_balance = float(entry['amount'])
        return res