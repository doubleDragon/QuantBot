#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import division

import logging
import random

import time

from quant.brokers import broker_factory
from quant.common import constant
from .basicbot import BasicBot


class Liquid(BasicBot):
    """
    ./venv/bin/python -m quant.cli -mKkex_BCH_BTC,Bitfinex_BCH_BTC -oLiquid -f=liquid -v
    """

    def __init__(self):
        super(Liquid, self).__init__()
        self.mm_market = 'Kkex_BCH_BTC'
        self.refer_markets = ['Bitfinex_BCH_BTC']
        self.hedge_market = 'Bitfinex_BCH_BTC'

        self.data_lost_count = 0
        self.risk_protect_count = 10

        self.slappage = 0.005

        self.brokers = broker_factory.create_brokers([self.mm_market, self.hedge_market])
        self.mm_broker = self.brokers[self.mm_market]
        self.hedge_broker = self.brokers[self.hedge_market]

        self.hedge_bid_price = 0.0
        self.hedge_ask_price = 0.0

        self.LIQUID_MIN_DIFF = 0.01
        # self.LIQUID_MAX_DIFF = 0.05
        self.LIQUID_MAX_DIFF = 0.03

        # bfx bch min trade amount = 0.02
        self.LIQUID_HEDGE_MIN_AMOUNT = 0.02
        self.LIQUID_MAX_BCH_AMOUNT = 1
        self.LIQUID_MIN_BCH_AMOUNT = 0.1
        self.LIQUID_BUY_ORDER_PAIRS = 5
        self.LIQUID_SELL_ORDER_PAIRS = 5
        # self.LIQUID_INIT_DIFF = 0.015  # 1%
        self.LIQUID_INIT_DIFF = 0.01  # 1%

        self.cancel_all_orders(self.mm_market)
        self.cancel_all_orders(self.hedge_market)

        self.fee_hedge_market = 0.002
        self.fee_mm_market = 0.002

        self.tick_count = 0

        logging.info('Liquid Setup complete')

    def terminate(self):
        super(Liquid, self).terminate()
        self.cancel_all_orders(self.mm_market)
        self.cancel_all_orders(self.hedge_market)

        logging.info('Liquid terminate complete')

    def risk_protect(self):
        self.data_lost_count += 1
        if self.data_lost_count > self.risk_protect_count:
            logging.warn('liquid======>risk protect~stop liquid supply. %s' % self.data_lost_count)

            self.cancel_all_orders(self.mm_market)
            self.data_lost_count = 0

    def tick(self, depths):
        logging.info("liquid======>tick:%s begin" % self.tick_count)
        refer_market = None
        refer_bid_price = 0
        refer_ask_price = 0

        for m in self.refer_markets:
            try:
                refer_bid_price, refer_ask_price = self.get_ticker(depths, m)
                refer_market = m
                break
            except Exception as e:
                logging.warn('liquid======>%s exception 000 when get_ticker:%s' % (m, e))
                continue

        if (refer_ask_price == 0) or (refer_bid_price == 0):
            logging.warn('liquid======>no available market depths 000')
            self.risk_protect()
            return

        if not refer_market:
            logging.warn('liquid======>no available market depths 111')
            self.risk_protect()
            return

        try:
            self.hedge_bid_price, self.hedge_ask_price = self.get_ticker(depths, self.hedge_market)
        except Exception as e:
            logging.warn('liquid======>%s exception 111 when get_ticker:%s' % (self.hedge_market, e))
            self.risk_protect()
            return

        try:
            mm_bid_price, mm_ask_price = self.get_ticker(depths, self.mm_market)
        except Exception as e:
            logging.warn('liquid======>%s exception 222 when get_ticker:%s' % (self.mm_market, e))
            return

        self.check_orders(refer_bid_price, refer_ask_price)

        self.place_orders(refer_bid_price, refer_ask_price, mm_bid_price, mm_ask_price)
        logging.info("liquid======>tick: %s end\n\n" % self.tick_count)
        self.tick_count += 1

    def check_orders(self, refer_bid_price, refer_ask_price):
        max_buy_price = refer_bid_price * (1 - self.LIQUID_MIN_DIFF)
        min_buy_price = refer_bid_price * (1 - self.LIQUID_MAX_DIFF)

        min_sell_price = refer_ask_price * (1 + self.LIQUID_MIN_DIFF)
        max_sell_price = refer_ask_price * (1 + self.LIQUID_MAX_DIFF)

        order_ids = self.get_order_ids()
        if not order_ids:
            logging.warn("liquid======>local orders ids is empty")
            return
        logging.info("liquid======>local orders ids %s" % order_ids)

        orders = self.mm_broker.get_orders(order_ids)
        if orders:
            for order in orders:
                local_order = self.get_order(order['order_id'])
                self.hedge_order(local_order, order)
                time_diff = int(time.time() - local_order['time'])
                timeout_adjust = random.randint(36000, 86400)

                if order['status'] == constant.ORDER_STATE_CLOSED or order['status'] == constant.ORDER_STATE_CANCELED:
                    self.remove_order(order['order_id'])
                    logging.info("liquid======>local orders remove %s, because closed or canceled, order=%s" %
                                 (order['order_id'], order))
                    return
                """
                cancel订单条件:
                1, 订单超过10小时则cancel掉
                2, 当前bfx的价格变化，相对于kkex委托的历史订单，如果出现了对冲亏损则cancel掉该订单
                """
                if order['type'] == 'buy':
                    if order['price'] > max_buy_price or time_diff > timeout_adjust:
                        logging.info("liquid======>\
                            [TraderBot] cancel BUY  order #%s ['price'] = %s NOT IN [%s, %s] or timeout[%s>%s]" % (
                            order['order_id'], order['price'], min_buy_price, max_buy_price, time_diff,
                            timeout_adjust))

                        self.cancel_order(self.mm_market, 'buy', order['order_id'])
                elif order['type'] == 'sell':
                    if order['price'] < min_sell_price or time_diff > timeout_adjust:
                        logging.info("liquid======>\
                            [TraderBot] cancel SELL order #%s ['price'] = %s NOT IN [%s, %s] or timeout[%s>%s]" % (
                            order['order_id'], order['price'], min_sell_price, max_sell_price, time_diff,
                            timeout_adjust))

                        self.cancel_order(self.mm_market, 'sell', order['order_id'])

    def hedge_order(self, order, remote_order):
        if remote_order['deal_amount'] <= self.LIQUID_HEDGE_MIN_AMOUNT:
            return

        amount = remote_order['deal_amount'] - order['deal_amount']
        if amount <= self.LIQUID_HEDGE_MIN_AMOUNT:
            logging.debug("liquid======>[hedger]deal nothing while. v:%s <= min:%s", amount,
                          self.LIQUID_HEDGE_MIN_AMOUNT)
            return

        order_id = remote_order['order_id']
        deal_amount = remote_order['deal_amount']
        price = remote_order['avg_price']

        client_id = str(order_id) + '-' + str(order['deal_index'])

        logging.info("liquid======>local order #%s new deal: %s", order_id, remote_order)
        hedge_side = 'sell' if order['type'] == 'buy' else 'buy'
        logging.info('liquid======>hedge [%s] to %s: %s %s %s', client_id, self.hedge_market, hedge_side, amount, price)

        if hedge_side == 'sell':
            self.hedge_order_sell(amount=amount, price=self.hedge_bid_price * (1 - self.slappage))
        else:
            self.hedge_order_buy(amount=amount * (1 + self.fee_hedge_market),
                                 price=self.hedge_ask_price * (1 + self.slappage))
        # update the deal_amount of local order
        self.remove_order(order_id)
        order['deal_amount'] = deal_amount
        order['deal_index'] += 1
        self.orders.append(order)

    def hedge_order_sell(self, amount, price):
        """confirm hedge order all executed"""
        can_sell_max = self.hedge_broker.bch_available
        if can_sell_max < amount:
            # post email
            if can_sell_max < self.LIQUID_HEDGE_MIN_AMOUNT:
                logging.error('liquid======>hedge sell order failed, because can_sell_max: %s < %s' %
                              (can_sell_max, self.LIQUID_HEDGE_MIN_AMOUNT))
                assert False
            sell_amount = can_sell_max
        else:
            sell_amount = amount
        sell_price = price
        while True:
            # sell_limit_c confirm sell_limit success, order_id must exist
            order_id = self.brokers[self.hedge_market].sell_limit_c(amount=sell_amount, price=sell_price)
            deal_amount, avg_price = self.get_deal_amount(self.hedge_market, order_id)
            diff_amount = round(sell_amount - deal_amount, 8)
            if diff_amount < self.LIQUID_HEDGE_MIN_AMOUNT:
                break
            ticker = self.get_latest_ticker(self.hedge_market)
            sell_amount = diff_amount
            sell_price = ticker['bid']

    def hedge_order_buy(self, amount, price):
        """confirm hedge order all executed"""
        buy_price = price
        buy_amount_target = amount
        while True:
            can_buy_max = self.hedge_broker.btc_available / buy_price
            if can_buy_max < buy_amount_target:
                if can_buy_max < self.LIQUID_HEDGE_MIN_AMOUNT:
                    logging.error('liquid======>hedge buy order failed, because can_buy_max: %s < %s' %
                                  (can_buy_max, self.LIQUID_HEDGE_MIN_AMOUNT))
                    assert False
                buy_amount = can_buy_max
            else:
                buy_amount = buy_amount_target

            # sell_limit_c confirm sell_limit success, order_id must exist
            order_id = self.brokers[self.hedge_market].buy_limit_c(amount=buy_amount, price=buy_price)
            deal_amount, avg_price = self.get_deal_amount(self.hedge_market, order_id)
            diff_amount = round(buy_amount - deal_amount, 8)
            if diff_amount < self.LIQUID_HEDGE_MIN_AMOUNT:
                break
            ticker = self.get_latest_ticker(self.hedge_market)
            buy_amount_target = diff_amount
            buy_price = ticker['ask']

    def place_orders(self, refer_bid_price, refer_ask_price, mm_bid_price, mm_ask_price):
        max_bch_trade_amount = self.LIQUID_MAX_BCH_AMOUNT
        min_bch_trade_amount = self.LIQUID_MIN_BCH_AMOUNT

        liquid_max_diff = self.LIQUID_MAX_DIFF

        # execute trade
        if self.buying_len() < 2 * self.LIQUID_BUY_ORDER_PAIRS:
            buy_price = refer_bid_price * (1 - self.LIQUID_INIT_DIFF)

            amount = round(max_bch_trade_amount * random.random(), 2)
            # -10% random price base on buy_price
            price = round(buy_price * (1 - liquid_max_diff * random.random()), 5)

            min_bch_amount_balance = round(min(self.mm_broker.btc_balance / price, self.hedge_broker.bch_available), 8)

            if min_bch_amount_balance < amount or amount < min_bch_trade_amount:
                logging.info("liquid======>\
                    BUY amount (%s) not IN (%s, %s)" % (amount, min_bch_trade_amount, min_bch_amount_balance))
            else:
                if 0 < mm_ask_price < buy_price:
                    price = buy_price

                len_buy_over = (self.buying_len() < self.LIQUID_BUY_ORDER_PAIRS)
                if (0 < mm_ask_price < buy_price) or len_buy_over:
                    order = self.new_order(market=self.mm_market, order_type='buy', amount=amount, price=price)
                    if order:
                        logging.info("liquid======>local orders add new buy order:%s" % order['order_id'])

        if self.selling_len() < 2 * self.LIQUID_SELL_ORDER_PAIRS:
            sell_price = refer_ask_price * (1 + self.LIQUID_INIT_DIFF)

            amount = round(max_bch_trade_amount * random.random(), 2)
            # +10% random price base on sell_price
            price = round(sell_price * (1 + liquid_max_diff * random.random()), 5)

            min_bch_amount_balance = round(min(self.mm_broker.bch_available, self.hedge_broker.btc_available / price),
                                           8)

            if min_bch_amount_balance < amount or amount < min_bch_trade_amount:
                logging.info("liquid======>\
                    SELL amount (%s) not IN (%s, %s)" % (amount, min_bch_trade_amount, min_bch_amount_balance))
            else:
                if mm_bid_price > 0 and mm_bid_price > sell_price:
                    price = sell_price

                len_sell_over = (self.selling_len() < self.LIQUID_SELL_ORDER_PAIRS)
                if (mm_bid_price > 0 and mm_bid_price > sell_price) or len_sell_over:
                    order = self.new_order(market=self.mm_market, order_type='sell', amount=amount, price=price)
                    if order:
                        logging.info("liquid======>local orders add new buy order:%s" % order['order_id'])

        return

    @classmethod
    def get_ticker(cls, depths, market):
        bid_price = depths[market]["bids"][0]['price']
        ask_price = depths[market]["asks"][0]['price']
        return bid_price, ask_price

    def update_balance(self):
        self.mm_broker.get_balances_c()
        self.hedge_broker.get_balances_c()

    def cancel_all_orders(self, market):
        self.brokers[market].cancel_all()
