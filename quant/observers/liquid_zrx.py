#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import division

import logging
import random

import time

from quant import config
from quant.brokers import broker_factory
from quant.common import constant
from quant.tool import email_box
from .basicbot import BasicBot


class Liquid_ZRX(BasicBot):
    """
    ./venv/bin/python -m quant.cli -mBitfinex_ZRX_ETH,Binance_ZRX_ETH -oLiquid_ZRX -f=liquid_zrx -v
    """

    def __init__(self):
        super(Liquid_ZRX, self).__init__()
        self.mm_market = 'Binance_ZRX_ETH'
        self.refer_markets = ['Bitfinex_ZRX_ETH']
        self.hedge_market = 'Bitfinex_ZRX_ETH'

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

        self.LIQUID_HEDGE_MIN_AMOUNT = 6
        self.LIQUID_MAX_ZRX_AMOUNT = 100
        self.LIQUID_BUY_ORDER_PAIRS = 5
        self.LIQUID_SELL_ORDER_PAIRS = 5
        self.LIQUID_INIT_DIFF = 0.015  # 1%

        self.fee_hedge_market = 0.002
        self.fee_mm_market = 0.002

        self.tick_count = 0

        self.cancel_orders(self.mm_market)
        self.cancel_orders(self.hedge_market)

        self.last_update_min_stock = 0.0

        logging.info('Liquid_ZRX Setup complete')

    def terminate(self):
        super(Liquid_ZRX, self).terminate()
        self.cancel_orders(self.mm_market)
        self.cancel_orders(self.hedge_market)

        logging.info('Liquid_ZRX terminate complete')

    def update_min_stock(self):
        # 更新bfx的最小交易量, 1个小时更新一次
        now = time.time()
        diff = now - self.last_update_min_stock
        if diff > 3600:
            min_stock = self.hedge_broker.get_min_stock()
            if min_stock:
                self.LIQUID_HEDGE_MIN_AMOUNT = min_stock
            self.last_update_min_stock = now

    def update_other(self):
        self.update_min_stock()

    def risk_protect(self):
        self.data_lost_count += 1
        if self.data_lost_count > self.risk_protect_count:
            logging.warn('Liquid_ZRX======>risk protect~stop liquid supply. %s' % self.data_lost_count)

            self.cancel_orders(self.mm_market)
            self.data_lost_count = 0

    def tick(self, depths):
        logging.info("Liquid_ZRX======>tick:%s begin" % self.tick_count)
        refer_market = None
        refer_bid_price = 0
        refer_ask_price = 0

        for m in self.refer_markets:
            try:
                refer_bid_price, refer_ask_price = self.get_ticker(depths, m)
                refer_market = m
                break
            except Exception as e:
                logging.warn('Liquid_ZRX======>%s exception when get_ticker:%s' % (m, e))
                continue

        if (refer_ask_price == 0) or (refer_bid_price == 0):
            logging.warn('Liquid_ZRX======>no available market depths')
            self.risk_protect()
            return

        if not refer_market:
            logging.warn('Liquid_ZRX======>no available market depths')
            self.risk_protect()
            return

        try:
            self.hedge_bid_price, self.hedge_ask_price = self.get_ticker(depths, self.hedge_market)
        except Exception as e:
            logging.warn('Liquid_ZRX======>%s exception when get_ticker:%s' % (self.hedge_market, e))
            self.risk_protect()
            return

        try:
            mm_bid_price, mm_ask_price = self.get_ticker(depths, self.mm_market)
        except Exception as e:
            logging.warn('Liquid_ZRX======>%s exception when get_ticker:%s' % (self.mm_market, e))
            return

        self.check_orders(refer_bid_price, refer_ask_price)

        self.place_orders(refer_bid_price, refer_ask_price, mm_bid_price, mm_ask_price)
        logging.info("Liquid_ZRX======>tick: %s end\n\n" % self.tick_count)
        self.tick_count += 1

    def check_orders(self, refer_bid_price, refer_ask_price):
        max_buy_price = refer_bid_price * (1 - self.LIQUID_MIN_DIFF)
        min_buy_price = refer_bid_price * (1 - self.LIQUID_MAX_DIFF)

        min_sell_price = refer_ask_price * (1 + self.LIQUID_MIN_DIFF)
        max_sell_price = refer_ask_price * (1 + self.LIQUID_MAX_DIFF)

        order_ids = self.get_order_ids()
        if not order_ids:
            logging.warn("Liquid_ZRX======>local orders ids is empty")
            return
        logging.info("Liquid_ZRX======>local orders ids %s" % order_ids)

        remote_orders = self.mm_broker.get_orders_history()
        if remote_orders:
            for order in remote_orders:
                local_order = self.get_order(order['order_id'])
                if not local_order:
                    # local order not exist, just continue
                    continue
                self.hedge_order(local_order, order)
                time_diff = int(time.time() - local_order['time'])
                timeout_adjust = random.randint(36000, 86400)

                if order['status'] == constant.ORDER_STATE_CLOSED or order['status'] == constant.ORDER_STATE_CANCELED:
                    self.remove_order(order['order_id'])
                    logging.info("Liquid_ZRX======>local orders remove %s, because closed or canceled, order=%s" %
                                 (order['order_id'], order))
                    return
                """
                cancel订单条件:
                1, 订单超过10小时则cancel掉
                2, 当前bfx的价格变化，相对于kkex委托的历史订单，如果出现了对冲亏损则cancel掉该订单
                """
                if order['type'] == 'buy':
                    if order['price'] > max_buy_price or time_diff > timeout_adjust:
                        logging.info("Liquid_ZRX======>\
                            [TraderBot] cancel BUY  order #%s ['price'] = %s NOT IN [%s, %s] or timeout[%s>%s]" % (
                            order['order_id'], order['price'], min_buy_price, max_buy_price, time_diff,
                            timeout_adjust))

                        self.cancel_order(self.mm_market, 'buy', order['order_id'])
                elif order['type'] == 'sell':
                    if order['price'] < min_sell_price or time_diff > timeout_adjust:
                        logging.info("Liquid_ZRX======>\
                            [TraderBot] cancel SELL order #%s ['price'] = %s NOT IN [%s, %s] or timeout[%s>%s]" % (
                            order['order_id'], order['price'], min_sell_price, max_sell_price, time_diff,
                            timeout_adjust))

                        self.cancel_order(self.mm_market, 'sell', order['order_id'])

    def hedge_order(self, order, remote_order):
        if remote_order['deal_amount'] <= self.LIQUID_HEDGE_MIN_AMOUNT:
            return

        amount = remote_order['deal_amount'] - order['deal_amount']
        if amount <= self.LIQUID_HEDGE_MIN_AMOUNT:
            logging.debug("Liquid_ZRX======>[hedger]deal nothing while. v:%s <= min:%s", amount,
                          self.LIQUID_HEDGE_MIN_AMOUNT)
            return

        order_id = remote_order['order_id']
        deal_amount = remote_order['deal_amount']
        # price = remote_order['avg_price']

        client_id = str(order_id) + '-' + str(order['deal_index'])

        logging.info("Liquid_ZRX======>local order #%s new deal: %s", order_id, remote_order)
        hedge_side = 'sell' if order['type'] == 'buy' else 'buy'

        if hedge_side == 'sell':
            hedge_price = self.hedge_bid_price * (1 - self.slappage)
            logging.info('Liquid_ZRX======>hedge [%s] to %s: %s %s %s', client_id, self.hedge_market, hedge_side,
                         amount,
                         hedge_price)
            self.hedge_order_sell(amount=amount, price=hedge_price)
        else:
            hedge_price = self.hedge_ask_price * (1 + self.slappage)
            logging.info('Liquid_ZRX======>hedge [%s] to %s: %s %s %s', client_id, self.hedge_market, hedge_side,
                         amount,
                         hedge_price)
            self.hedge_order_buy(amount=amount * (1 + self.fee_hedge_market),
                                 price=hedge_price)
        # update the deal_amount of local order
        self.remove_order(order_id)
        order['deal_amount'] = deal_amount
        order['deal_index'] += 1
        self.orders.append(order)

    def hedge_order_sell(self, amount, price):
        """confirm hedge order all executed"""
        hedge_index = 0
        hedge_total_amount = 0

        can_sell_max = self.hedge_broker.zrx_available
        if can_sell_max < amount:
            # post email
            if can_sell_max < self.LIQUID_HEDGE_MIN_AMOUNT:
                logging.error('Liquid_ZRX======>hedge sell order failed, because can_sell_max: %s < %s' %
                              (can_sell_max, self.LIQUID_HEDGE_MIN_AMOUNT))
                raise Exception('hedge sell order failed, because can_sell_max: %s < %s' %
                                (can_sell_max, self.LIQUID_HEDGE_MIN_AMOUNT))
            sell_amount = can_sell_max
        else:
            sell_amount = amount
        sell_price = price
        while True:
            # sell_limit_c confirm sell_limit success, order_id must exist
            try:
                order_id = self.brokers[self.hedge_market].sell_limit_c(amount=sell_amount, price=sell_price)
            except Exception as e:
                logging.error('Liquid_ZRX======>hedge sell order failed when sell_limit_c, error=%s' % e)
                raise Exception('hedge sell order failed when sell_limit_c, error=%s' % e)

            time.sleep(config.INTERVAL_API)
            deal_amount, avg_price = self.get_deal_amount(self.hedge_market, order_id)
            hedge_total_amount += deal_amount
            logging.info("Liquid_ZRX======>hedge sell %s, order_id=%s, amount=%s, price=%s, deal_amount=%s" %
                         (hedge_index, order_id, sell_amount, avg_price, deal_amount))

            diff_amount = round(sell_amount - deal_amount, 8)
            if diff_amount < self.LIQUID_HEDGE_MIN_AMOUNT:
                logging.info('Liquid_ZRX======>hedge sell order success, target=%s, total=%s, left=%s' %
                             (amount, hedge_total_amount, diff_amount))
                email_box.send_mail('hedge sell order success, target=%s, total=%s, left=%s' %
                                    (amount, hedge_total_amount, diff_amount))
                break
            time.sleep(config.INTERVAL_API)
            ticker = self.get_latest_ticker(self.hedge_market)
            sell_amount = diff_amount
            sell_price = ticker['bid']
            hedge_index += 1

    def hedge_order_buy(self, amount, price):
        """confirm hedge order all executed"""
        buy_price = price
        buy_amount_target = amount
        hedge_index = 0
        hedge_total_amount = 0
        while True:
            can_buy_max = self.hedge_broker.eth_available / buy_price
            if can_buy_max < buy_amount_target:
                if can_buy_max < self.LIQUID_HEDGE_MIN_AMOUNT:
                    logging.error('Liquid_ZRX======>hedge buy order failed, because can_buy_max: %s < %s' %
                                  (can_buy_max, self.LIQUID_HEDGE_MIN_AMOUNT))
                    raise Exception('hedge buy order failed, because can_buy_max: %s < %s' %
                                    (can_buy_max, self.LIQUID_HEDGE_MIN_AMOUNT))
                buy_amount = can_buy_max
            else:
                buy_amount = buy_amount_target

            # sell_limit_c confirm sell_limit success, order_id must exist
            try:
                order_id = self.brokers[self.hedge_market].buy_limit_c(amount=buy_amount, price=buy_price)
            except Exception as e:
                logging.error('Liquid_ZRX======>hedge buy order failed when buy_limit_c, error=%s' % e)
                raise Exception('hedge buy order failed when buy_limit_c, error=%s' % e)

            time.sleep(config.INTERVAL_API)
            deal_amount, avg_price = self.get_deal_amount(self.hedge_market, order_id)
            hedge_total_amount += deal_amount
            logging.info("Liquid_ZRX======>hedge buy %s, order_id=%s, amount=%s, price=%s, deal_amount=%s" %
                         (hedge_index, order_id, buy_amount, avg_price, deal_amount))

            diff_amount = round(buy_amount - deal_amount, 8)
            if diff_amount < self.LIQUID_HEDGE_MIN_AMOUNT:
                logging.info('Liquid_ZRX======>hedge buy order success, target=%s, total=%s, left=%s' %
                             (amount, hedge_total_amount, diff_amount))
                email_box.send_mail('hedge buy order success, target=%s, total=%s, left=%s' %
                                    (amount, hedge_total_amount, diff_amount))
                break
            time.sleep(config.INTERVAL_API)
            ticker = self.get_latest_ticker(self.hedge_market)
            buy_amount_target = diff_amount
            buy_price = ticker['ask']
            hedge_index += 1

    def place_orders(self, refer_bid_price, refer_ask_price, mm_bid_price, mm_ask_price):
        max_trade_amount = self.LIQUID_MAX_ZRX_AMOUNT

        liquid_max_diff = self.LIQUID_MAX_DIFF

        # execute trade
        if self.buying_len() < 2 * self.LIQUID_BUY_ORDER_PAIRS:
            buy_price = refer_bid_price * (1 - self.LIQUID_INIT_DIFF)

            amount = round(max_trade_amount * random.random(), 0)
            # -10% random price base on buy_price
            price = round(buy_price * (1 - liquid_max_diff * random.random()), 5)

            min_amount_balance = round(min(self.mm_broker.eth_available / price, self.hedge_broker.zrx_available), 8)

            min_trade_amount = self.cal_min_amount_trade_bn(mm_bid_price)
            if min_amount_balance < amount or amount < min_trade_amount:
                logging.info("Liquid_ZRX======>\
                    BUY amount (%s) not IN (%s, %s)" % (amount, min_trade_amount, min_amount_balance))
            else:
                if 0 < mm_ask_price < buy_price:
                    price = buy_price

                len_buy_over = (self.buying_len() < self.LIQUID_BUY_ORDER_PAIRS)
                if (0 < mm_ask_price < buy_price) or len_buy_over:
                    order = self.new_order(market=self.mm_market, order_type='buy', amount=amount, price=price)
                    if order:
                        logging.info("Liquid_ZRX======>local orders add new buy order:%s" % order['order_id'])

        if self.selling_len() < 2 * self.LIQUID_SELL_ORDER_PAIRS:
            sell_price = refer_ask_price * (1 + self.LIQUID_INIT_DIFF)

            amount = round(max_trade_amount * random.random(), 0)
            # +10% random price base on sell_price
            price = round(sell_price * (1 + liquid_max_diff * random.random()), 5)

            min_amount_balance = round(min(self.mm_broker.zrx_available, self.hedge_broker.eth_available / price), 8)
            min_trade_amount = self.cal_min_amount_trade_bn(mm_ask_price)
            if min_amount_balance < amount or amount < min_trade_amount:
                logging.info("Liquid_ZRX======>\
                    SELL amount (%s) not IN (%s, %s)" % (amount, min_trade_amount, min_amount_balance))
            else:
                if mm_bid_price > 0 and mm_bid_price > sell_price:
                    price = sell_price

                len_sell_over = (self.selling_len() < self.LIQUID_SELL_ORDER_PAIRS)
                if (mm_bid_price > 0 and mm_bid_price > sell_price) or len_sell_over:
                    order = self.new_order(market=self.mm_market, order_type='sell', amount=amount, price=price)
                    if order:
                        logging.info("Liquid_ZRX======>local orders add new buy order:%s" % order['order_id'])

        return

    @classmethod
    def cal_min_amount_trade_bn(cls, price):
        return 0.01 / price

    @classmethod
    def get_ticker(cls, depths, market):
        bid_price = depths[market]["bids"][0]['price']
        ask_price = depths[market]["asks"][0]['price']
        return bid_price, ask_price

    def update_balance(self):
        self.mm_broker.get_balances_c()
        self.hedge_broker.get_balances_c()

    def cancel_orders(self, market):
        # just for bfx
        self.brokers[market].cancel_orders()
