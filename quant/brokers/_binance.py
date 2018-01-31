# coding=utf-8
# Copyright (C) 2017, Philsong <songbohr@gmail.com>
from __future__ import division

import time

import logging
from quant import config
from quant.common import constant
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

    def buy_limit(self, amount, price, client_id=None):
        protected_amount = 600
        if amount > protected_amount:
            logging.error('risk alert: amount %s > risk amount:%s' % (amount, protected_amount))
            raise Exception

        logging.debug("BUY LIMIT %f %s at %f %s @%s" % (amount, self.market_currency,
                                                        price, self.base_currency, self.brief_name))

        try:
            if client_id:
                return self._buy_limit(amount, price, client_id)
            else:
                return self._buy_limit(amount, price)
        except Exception as e:
            logging.error('%s %s except: %s' % (self.name, 'buy_limit', e))
            return None

    def sell_limit(self, amount, price, client_id=None):
        protected_amount = 600
        if amount > protected_amount:
            logging.error('risk alert: amount %s > risk amount:%s' % (amount, protected_amount))
            raise Exception

        logging.debug("SELL LIMIT %f %s at %f %s @%s" % (amount, self.market_currency,
                                                         price, self.base_currency, self.brief_name))

        try:
            if client_id:
                return self._sell_limit(amount, price, client_id)
            else:
                return self._sell_limit(amount, price)
        except Exception as e:
            logging.error('%s %s except: %s' % (self.name, 'sell_limit', e))
            return None

    def _place_order(self, amount, price, side):
        order = self.client.create_order(
            symbol=self.pair_code,
            side=side,
            type=ORDER_TYPE_LIMIT,
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=amount,
            price=str(price),
        )
        logging.debug('_place_order: %s %s' % (side, order))

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
            'avg_price': float(res['price']),
            'symbol': res['symbol'],
            'type': res['side'].lower()
        }

        if res['status'] == ORDER_STATUS_NEW or res['status'] == ORDER_STATUS_PARTIALLY_FILLED:
            resp['status'] = constant.ORDER_STATE_PENDING
        elif res['status'] == ORDER_STATUS_CANCELED:
            resp['status'] = constant.ORDER_STATE_CANCELED
        else:
            resp['status'] = constant.ORDER_STATE_CLOSED

        return resp

    def _get_order(self, order_id, order_type=None):
        res = self.client.get_order(orderId=int(order_id), symbol=self.pair_code)
        logging.debug('get_order: %s' % res)

        assert str(res['symbol']) == str(self.pair_code)
        assert str(res['orderId']) == str(order_id)
        return self._order_status(res)

    def _get_orders_history(self):
        # get orders that symbol is pair before 5 minutes
        timestamp = (int(round(time.time() * 1000))) - 5 * 60 * 1000
        orders = self.client.get_all_orders(symbol=self.pair_code, limit=20, timestamp=timestamp)
        result = []
        for order in orders:
            result.append(self._order_status(order))
        return result

    def _cancel_order(self, order_id, order_type=None):
        res = self.client.cancel_order(orderId=int(order_id), symbol=self.pair_code)
        logging.debug('cancel_order: %s' % res)

        assert str(res['orderId']) == str(order_id)
        return True

    def _get_active_orders(self):
        res = self.client.get_open_orders()
        orders = []
        for item in res:
            orders.append(self._order_status(item))
        return orders

    def _cancel_orders(self):
        try:
            orders = self._get_active_orders()
            if len(orders) == 0:
                return
            for order in orders:
                if order['symbol'] != self.pair_code:
                    continue
                try:
                    self._cancel_order(order_id=order['order_id'])
                    logging.info('_cancel_orders cancel %s success' % order['order_id'])
                except Exception as e:
                    raise Exception('_cancel_orders %s failed : %s' % (order['order_id'], e))
        except Exception as e:
            raise Exception('_cancel_orders failed when get active orders, error: %s' % e)

    def _get_balances(self):
        """Get balance"""
        res = self.client.get_account()
        logging.debug("get_balances: %s" % res)

        balances = res['balances']

        for entry in balances:
            currency = entry['asset'].upper()
            if currency not in (
                    'BTC', 'BCH', 'USD', 'ETH', 'ZRX'):
                continue

            if currency == 'BCH':
                self.bch_available = float(entry['free'])
                self.bch_balance = float(entry['free']) + float(entry['locked'])
            elif currency == 'BTC':
                self.btc_available = float(entry['free'])
                self.btc_balance = float(entry['free']) + float(entry['locked'])
            elif currency == 'ETH':
                self.eth_available = float(entry['free'])
                self.eth_balance = float(entry['free']) + float(entry['locked'])
            elif currency == 'ZRX':
                self.zrx_available = float(entry['free'])
                self.zrx_balance = float(entry['free']) + float(entry['locked'])

        return res

    def _ticker(self):
        return self.client.get_ticker(symbol=self.pair_code)

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
        elif pair_code == 'ZRXBTC':
            base_currency = 'BTC'
            market_currency = 'ZRX'
        elif pair_code == 'ZRXETH':
            base_currency = 'ETH'
            market_currency = 'ZRX'
        else:
            assert False
        return base_currency, market_currency
