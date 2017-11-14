# Copyright (C) 2017, Philsong <songbohr@gmail.com>
from quant import config
from quant.common import constant
from .broker import Broker
import logging
from quant.api.kkex import PrivateClient


class Kkex(Broker):
    def __init__(self, pair_code, api_key=None, api_secret=None):

        base_currency, market_currency = self.get_available_pairs(pair_code)

        super(Kkex, self).__init__(base_currency, market_currency, pair_code)

        self.client = PrivateClient(
            api_key if api_key else config.KKEX_API_KEY,
            api_secret if api_secret else config.KKEX_SECRET_TOKEN)

    @classmethod
    def get_available_pairs(cls, pair_code):
        if pair_code == 'BCCBTC':
            base_currency = 'BTC'
            market_currency = 'BCH'
        elif pair_code == 'ETHBTC':
            base_currency = 'BTC'
            market_currency = 'ETH'
        else:
            assert False
        return base_currency, market_currency

    def _buy_limit(self, amount, price):
        """Create a buy limit order"""
        res = self.client.buy_limit(symbol=self.pair_code, amount=str(amount), price=str(price))
        logging.info('_buy_limit: %s' % res)
        return res['order_id']

    def _sell_limit(self, amount, price):
        """Create a sell limit order"""
        res = self.client.sell_limit(symbol=self.pair_code, amount=str(amount), price=str(price))
        logging.info('_sell_limit: %s' % res)
        return res['order_id']

    @classmethod
    def _order_status(cls, res):
        resp = {
            'order_id': res['order_id'],
            'amount': float(res['amount']),
            'price': float(res['price']),
            'deal_amount': float(res['deal_amount']),
            'avg_price': float(res['avg_price']),
            'type': res['type']
        }
        if res['status'] == 2:
            resp['status'] = constant.ORDER_STATE_CLOSED
        elif res['status'] == -1:
            resp['status'] = constant.ORDER_STATE_CANCELED
        else:
            # 0 1 4 pending status
            resp['status'] = constant.ORDER_STATE_PENDING

        return resp

    def _get_order(self, order_id, order_type=None):
        res = self.client.order_info(self.pair_code, int(order_id))
        logging.info('get_order: %s' % res)

        assert str(res['order']['order_id']) == str(order_id)
        return self._order_status(res['order'])

    def _get_orders(self, order_ids):
        orders = []
        res = self.client.orders_info(self.pair_code, order_ids)
        for order in res['orders']:
            resp_order = self._order_status(order)
            orders.append(resp_order)

        return orders

    def _cancel_order(self, order_id, currency=None, order_type=None):
        res = self.client.cancel_order(self.pair_code, int(order_id))
        logging.info('cancel_order: %s' % res)

        assert str(res['order_id']) == str(order_id)

        return True

    def _cancel_all(self):
        res = self.client.cancel_all_orders(self.pair_code)
        return res['result']

    def _get_balances(self):
        """Get balance"""
        res = self.client.balance()
        logging.debug("kkex get_balances: %s" % res)

        entry = res['info']['funds']

        self.bch_available = float(entry['free']['BCC'])
        self.bch_balance = float(entry['freezed']['BCC']) + float(entry['free']['BCC'])
        self.btc_available = float(entry['free']['BTC'])
        self.btc_balance = float(entry['freezed']['BTC']) + float(entry['free']['BTC'])

        return res

    def _get_orders_history(self):
        orders = []
        res = self.client.get_orders_history(self.pair_code, pagesize=200)
        if res:
            for order in res['orders']:
                resp_order = self._order_status(order)
                orders.append(resp_order)

            return orders
