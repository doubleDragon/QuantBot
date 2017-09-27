# coding=utf-8
# Copyright (C) 2017, Philsong <songbohr@gmail.com>
from quant import config
from .broker import Broker
from quant.api.liqui import PrivateClient as LqClient
import logging


# python3 xrypto/cli.py -m Bitfinex_BCH_BTC get-balance

class Liqui(Broker):
    def __init__(self, pair_code, api_key=None, api_secret=None):
        base_currency, market_currency = self.get_available_pairs(pair_code)

        super(Liqui, self).__init__(base_currency, market_currency, pair_code)

        self.client = LqClient(
            api_key if api_key else config.Bitfinex_API_KEY,
            api_secret if api_secret else config.Bitfinex_SECRET_TOKEN)

        # self.get_balances()

    def symbol(self):
        return "%s%s" % (self.market_currency, self.base_currency)

    @classmethod
    def get_available_pairs(cls, pair_code):
        """可交易的pair"""
        if pair_code == 'bccbtc':
            base_currency = 'btc'
            market_currency = 'bcc'
        else:
            assert False
        return base_currency, market_currency

    def _buy_limit(self, amount, price):
        """
        Create a buy limit order,
        order_id == 0表示已全部成交
        """
        resp = self.client.buy(symbol=self.symbol(), price=str(price), amount=str(amount))
        if resp and 'return' in resp and 'order_id' in resp['return']:
            return resp['return']['order_id']

    def _sell_limit(self, amount, price):
        """Create a sell limit order"""
        resp = self.client.sell(symbol=self.symbol(), price=str(price), amount=str(amount))
        if resp and 'return' in resp and 'order_id' in resp['return']:
            return resp['return']['order_id']

    @classmethod
    def _order_status(cls, res, order_id):
        """avg_price equal price"""
        resp = {
            'order_id': order_id,
            'amount': float(res['start_amount']),
            'price': float(res['rate']),
            'deal_amount': float(res['start_amount']) - float(res['amount']),
            'avg_price': float(res['rate'])}

        if res['status'] == 1:
            resp['status'] = 'CLOSE'
        if res['status'] == 0:
            resp['status'] = 'OPEN'
        else:
            resp['status'] = 'CANCELED'

        return resp

    def _get_order(self, order_id):
        res = self.client.get_order(str(order_id))
        logging.info('get_order: %s' % res)

        r_id = None
        r_order = None
        if res and 'return' in res:
            res = res['res']
            r_id = res.keys()[0]
            r_order = res[r_id]

        assert str(r_id) == str(order_id)
        return self._order_status(r_order, r_id)

    def _cancel_order(self, order_id):
        res = self.client.cancel_order(int(order_id))
        assert str(res['return']['order_id']) == str(order_id)

        if res and res['success'] == 1:
            return True
        else:
            return False

    def _get_balances(self):
        """Get balance"""
        res = self.client.balance()
        res = res['return']['funds']

        # logging.debug("liqui get_balances response: %s" % res)

        for key, value in res.items():
            currency = key
            if currency not in (
                    'btc', 'bcc'):
                continue

            if currency == 'bcc':
                self.bch_available = float(value)
                self.bch_balance = float(value)

            elif currency == 'btc':
                self.btc_available = float(value)
                self.btc_balance = float(value)
        return res
