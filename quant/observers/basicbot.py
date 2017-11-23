#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging

import time

from quant import config
from quant.common import constant
from .observer import Observer


class BasicBot(Observer):
    def __init__(self):
        super(BasicBot, self).__init__()

        self.brokers = {}
        self.orders = []

        logging.info('BasicBot Setup complete')

    def new_order(self, market, order_type, maker_only=False, amount=None, price=None):
        if order_type == 'buy' or order_type == 'sell':
            if not price or not amount:
                print(price)
                print(amount)
                assert False

            if maker_only:
                if order_type == 'buy':
                    order_id = self.brokers[market].buy_maker(amount, price)
                else:
                    order_id = self.brokers[market].sell_maker(amount, price)
            else:
                if order_type == 'buy':
                    order_id = self.brokers[market].buy_limit(amount, price)
                else:
                    order_id = self.brokers[market].sell_limit(amount, price)

            if not order_id or order_id == -1:
                logging.warn("%s @%s %f/%f failed, %s" % (order_type, market, amount, price, order_id))
                return None

            order = {
                'market': market,
                'order_id': order_id,
                'price': price,
                'amount': amount,
                'deal_amount': 0,
                'deal_index': 0,
                'type': order_type,
                'time': time.time()
            }
            self.orders.append(order)
            logging.info("submit order %s" % order)

            return order

        return None

    def remove_order(self, order_id):
        self.orders = [x for x in self.orders if not x['order_id'] == order_id]

    def get_order(self, order_id):
        for x in self.orders:
            if x['order_id'] == order_id:
                return x

    def get_orders(self, order_type):
        orders_snapshot = [x for x in self.orders if x['type'] == order_type]
        return orders_snapshot

    def get_order_ids(self):
        order_ids = [x['order_id'] for x in self.orders]
        return order_ids

    def selling_len(self):
        return len(self.get_orders('sell'))

    def buying_len(self):
        return len(self.get_orders('buy'))

    def is_selling(self):
        return len(self.get_orders('sell')) > 0

    def is_buying(self):
        return len(self.get_orders('buy')) > 0

    # def get_sell_price(self):
    #     return self.sprice
    #
    # def get_buy_price(self):
    #     return self.bprice
    #
    # def get_spread(self):
    #     return self.sprice - self.bprice

    def cancel_order(self, market, order_type, order_id):
        result = self.brokers[market].cancel_order(order_id)
        if not result:
            logging.warn("cancel %s #%s failed" % (order_type, order_id))
            return False
        else:
            logging.info("cancel %s #%s ok" % (order_type, order_id))
            return True

    def cancel_all_orders(self, market):
        orders = self.brokers[market].get_orders_history()
        if not orders:
            return

        for order in orders:
            logging.info("Cancelling: %s %s @ %s" % (order['type'], order['amount'], order['price']))
            while True:
                result = self.cancel_order(market, order['type'], order['order_id'])
                if not result:
                    time.sleep(2)
                else:
                    break

    def update_balance(self):
        for broker in self.brokers:
            self.brokers[broker].get_balances()

    def update_other(self):
        pass

    def get_deal_amount(self, market, order_id):
        """
        平均成交价还是要有的
        """
        while True:
            order_status = self.brokers[market].get_order(order_id)
            if not order_status:
                time.sleep(config.INTERVAL_RETRY)
                continue
            break

        if order_status['status'] == constant.ORDER_STATE_PENDING:
            self.brokers[market].cancel_order(order_id)
            time.sleep(config.INTERVAL_API)
            return self.get_deal_amount(market, order_id)
        else:
            return order_status['deal_amount'], order_status['avg_price']

    def get_latest_ticker(self, market):
        return self.brokers[market].get_ticker_c()
