# Copyright (C) 2017, Philsong <songbohr@gmail.com>
from quant import config
from quant.api import bittrex
from .broker import Broker
import logging


# python3 xrypto/cli.py -m Bittrex_BCH_BTC get-balance

class Bittrex(Broker):
    def __init__(self, pair_code, api_key=None, api_secret=None):
        base_currency, market_currency = self.get_available_pairs(pair_code)

        super(Bittrex, self).__init__(base_currency, market_currency, pair_code)

        self.client = bittrex.Bittrex(
            api_key if api_key else config.Bittrex_API_KEY,
            api_secret if api_secret else config.Bittrex_SECRET_TOKEN)

        # self.get_balances()

    @classmethod
    def get_available_pairs(cls, pair_code):
        if pair_code == 'BTC-BCC':
            base_currency = 'BTC'
            market_currency = 'BCH'
        elif pair_code == 'BTC-ZEC':
            base_currency = 'BTC'
            market_currency = 'ZEC'
        else:
            assert False
        return base_currency, market_currency

    def _buy_limit(self, amount, price):
        """Create a buy limit order"""
        res = self.client.buy_limit(self.pair_code,
                                    amount,
                                    price)
        return res['result']['uuid']

    def _sell_limit(self, amount, price):
        """Create a sell limit order"""
        res = self.client.sell_limit(self.pair_code,
                                     amount,
                                     price)
        return res['result']['uuid']

    def _order_status(self, res):
        resp = {
            'order_id': res['OrderUuid'],
            'amount': float(res['Quantity']),
            'price': float(res['Limit']),
            'deal_amount': float(res['Quantity']) - float(res['QuantityRemaining']),
            'avg_price': float(res['Price'])
        }

        if res['IsOpen']:
            resp['status'] = 'OPEN'
        else:
            resp['status'] = 'CLOSE'

        return resp

    def _get_order(self, order_id):
        res = self.client.get_order(order_id)
        logging.info('get_order: %s' % res)
        assert str(res['result']['OrderUuid']) == str(order_id)
        return self._order_status(res['result'])

    def _cancel_order(self, order_id):
        res = self.client.cancel(order_id)
        if res['success'] is True:
            return True
        else:
            return False

    def _get_balances(self):
        """Get balance"""
        res = self.client.get_balances()
        logging.debug("bittrex get_balances response: %s" % res)

        for entry in res['result']:
            currency = entry['Currency']
            if currency not in (
                    'BTC', 'BCC'):
                continue

            if currency == 'BCC':
                self.bch_available = float(entry['Available'])
                self.bch_balance = float(entry['Balance'])

            elif currency == 'BTC':
                self.btc_available = float(entry['Available'])
                self.btc_balance = float(entry['Balance'])
            elif currency == 'ZEC':
                self.zec_available = float(entry['Available'])
                self.zec_balance = float(entry['Balance'])

        return res

    def test(self):
        order_id = self.buy_limit(0.11, 0.02)
        print(order_id)
        order_status = self.get_order(order_id)
        print(order_status)
        balance = self.get_balances()
        # print(balance)
        cancel_status = self.cancel_order(order_id)
        print(cancel_status)
        order_status = self.get_order(order_id)
        print(order_status)

        order_id = self.sell_limit(0.12, 0.15)
        print(order_id)
        order_status = self.get_order(order_id)
        print(order_status)

        balance = self.get_balances()
        # print(balance)

        cancel_status = self.cancel_order(order_id)
        print(cancel_status)
        order_status = self.get_order(order_id)
        print(order_status)
