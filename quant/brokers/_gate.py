# coding=utf-8
# Copyright (C) 2017, Philsong <songbohr@gmail.com>
from quant import config
from .broker import Broker
from quant.api.gate import PrivateClient as GateClient
import logging


# python -m quant.cli -m Bitfinex_BCH_BTC get-balance

class Gate(Broker):
    def __init__(self, pair_code, api_key=None, api_secret=None):
        base_currency, market_currency = self.get_available_pairs(pair_code)

        super(Gate, self).__init__(base_currency, market_currency, pair_code)

        self.client = GateClient(
            api_key if api_key else config.Gate_API_KEY,
            api_secret if api_secret else config.Gate_SECRET_TOKEN)

        # self.get_balances()

    @classmethod
    def get_available_pairs(cls, pair_code):
        """可交易的pair"""
        if pair_code == 'bcc_btc':
            base_currency = 'btc'
            market_currency = 'bcc'
        elif pair_code == 'bcc_eth':
            base_currency = 'eth'
            market_currency = 'bcc'
        else:
            assert False
        return base_currency, market_currency

    def _buy_limit(self, amount, price):
        """
        Create a buy limit order,
        order_id == 0表示已全部成交
        """
        resp = self.client.buy(symbol=self.pair_code, price=str(price), amount=str(amount))
        if resp and 'orderNumber' in resp:
            return resp['orderNumber']

    def _sell_limit(self, amount, price):
        """Create a sell limit order"""
        resp = self.client.sell(symbol=self.pair_code, price=str(price), amount=str(amount))
        if resp and 'orderNumber' in resp:
            return resp['orderNumber']

    @classmethod
    def _order_status(cls, res, order_id):
        """avg_price equal price"""
        resp = {
            'order_id': order_id,
            'amount': float(res['initialAmount']),
            'price': float(res['initialRate']),
            'deal_amount': float(res['initialAmount']) - float(res['amount']),
            'avg_price': float(res['rate'])}

        if res['status'] == 'done':
            resp['status'] = 'CLOSE'
        elif res['status'] == 'cancelled':
            resp['status'] = 'CANCELED'
        else:
            resp['status'] = 'OPEN'

        return resp

    def _get_order(self, order_id):
        res = self.client.get_order(order_id, self.pair_code)
        logging.info('get_order: %s' % res)

        r_id = None
        r_order = None
        if res and 'order' in res:
            r_order = res['order']
            r_id = r_order['id']

        assert str(r_id) == str(order_id)
        return self._order_status(r_order, r_id)

    def _cancel_order(self, order_id):
        res = self.client.cancel_order(order_id, self.pair_code)

        if res and res['result'] is True:
            return True
        else:
            return False

    def _get_balances(self):
        """Get balance"""
        res = self.client.balance()
        # logging.debug("gate get_balances response: %s" % res)
        if not res:
            return None

        if 'available' in res:
            res0 = res['available']
            if 'BTC' in res0:
                self.btc_available = float(res0['BTC'])
            if 'ETH' in res0:
                self.eth_available = float(res0['ETH'])

        if 'locked' in res:
            res1 = res['locked']
            if 'BTC' in res1:
                self.btc_balance = float(res1['BTC']) + self.btc_available
            if 'BTC' in res1:
                self.eth_available = float(res1['BTC']) + self.eth_available

        return res

    def _ticker(self):
        pass
