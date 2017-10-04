# coding=utf-8
# Copyright (C) 2017, Philsong <songbohr@gmail.com>
import logging
from quant import config
from .broker import Broker
from quant.api.binance import Client
from quant.api.binance_enums import *


class Binance(Broker):
    def __init__(self, pair_code, api_key=None, api_secret=None):
        base_currency, market_currency = self.get_available_pairs(pair_code)
        super(Binance, self).__init__(base_currency, market_currency, pair_code)

        self.client = Client(
            api_key if api_key else config.Binance_API_KEY,
            api_secret if api_secret else config.Binance_SECRET_TOKEN)

    def _place_order(self, amount, price, side):
        order = self.client.create_order(
            symbol=self.pair_code,
            side=side,
            type=ORDER_TYPE_LIMIT,
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=amount,
            price=str(price))
        logging.info('_place_order: %s %s' % (side, order))

        return order['orderId']

    def _buy_limit(self, amount, price):
        """Create a buy limit order"""
        return self._place_order(amount, price, SIDE_BUY)

    def _sell_limit(self, amount, price):
        """Create a sell limit order"""
        return self._place_order(amount, price, SIDE_SELL)

    @classmethod
    def _order_status(cls, res):
        resp = {
            'order_id': res['orderId'],
            'amount': float(res['origQty']),
            'price': float(res['price']),
            'deal_amount': float(res['executedQty']),
            'avg_price': float(res['price'])
        }

        if res['status'] == ORDER_STATUS_NEW or res['status'] == ORDER_STATUS_PARTIALLY_FILLED:
            resp['status'] = 'OPEN'
        else:
            resp['status'] = 'CLOSE'

        return resp

    def _get_order(self, order_id):
        res = self.client.get_order(orderId=int(order_id), symbol=self.pair_code)
        logging.info('get_order: %s' % res)

        assert str(res['symbol']) == str(self.pair_code)
        assert str(res['orderId']) == str(order_id)
        return self._order_status(res['data'])

    def _cancel_order(self, order_id):
        res = self.client.cancel_order(orderId=int(order_id), symbol=self.pair_code)
        logging.info('cancel_order: %s' % res)

        assert str(res['orderId']) == str(order_id)
        return True

    def _get_balances(self):
        """Get balance"""
        res = self.client.get_account()
        logging.debug("get_balances: %s" % res)

        balances = res['balances']

        for entry in balances:
            currency = entry['asset'].upper()
            if currency not in (
                    'BTC', 'BCH', 'USD'):
                continue

            if currency == 'BCH':
                self.bch_available = float(entry['free'])
                self.bch_balance = float(entry['amount']) + float(entry['locked'])

            elif currency == 'BTC':
                self.btc_available = float(entry['free'])
                self.btc_balance = float(entry['amount']) + float(entry['locked'])

        return res

    @classmethod
    def get_available_pairs(cls, pair_code):
        """可交易的pair"""
        if pair_code == 'BCCBTC':
            base_currency = 'BTC'
            market_currency = 'BCC'
        elif pair_code == 'ETHBTC':
            base_currency = 'BTC'
            market_currency = 'ETH'
        elif pair_code == 'BNBBTC':
            base_currency = 'BTC'
            market_currency = 'BNB'
        elif pair_code == 'BNBETH':
            base_currency = 'ETH'
            market_currency = 'BNB'
        elif pair_code == 'MCOBTC':
            base_currency = 'BTC'
            market_currency = 'MCO'
        elif pair_code == 'MCOETH':
            base_currency = 'ETH'
            market_currency = 'MCO'
        elif pair_code == 'QTUMBTC':
            base_currency = 'BTC'
            market_currency = 'QTUM'
        elif pair_code == 'QTUMETH':
            base_currency = 'ETH'
            market_currency = 'QTUM'
        elif pair_code == 'WTCBTC':
            base_currency = 'BTC'
            market_currency = 'WTC'
        elif pair_code == 'WTCETH':
            base_currency = 'ETH'
            market_currency = 'WTC'
        elif pair_code == 'NEOBTC':
            base_currency = 'BTC'
            market_currency = 'NEO'
        elif pair_code == 'NEOETH':
            base_currency = 'ETH'
            market_currency = 'NEO'
        elif pair_code == 'IOTAETH':
            base_currency = 'ETH'
            market_currency = 'IOTA'
        elif pair_code == 'IOTABTC':
            base_currency = 'BTC'
            market_currency = 'IOTA'
        else:
            assert False
        return base_currency, market_currency
