#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import division

import logging

import time

from quant import config
from quant.brokers import broker_factory
from quant.common import constant
from quant.tool import email_box
from .basicbot import BasicBot


class Liquid_zrx(BasicBot):
    """
    ./venv/bin/python -m quant.cli -mBitfinex_ZRX_ETH,Binance_ZRX_ETH -oLiquid_zrx -f=liquid_zrx -v
    """

    def __init__(self):
        super(Liquid_zrx, self).__init__()
        self.mm_market = 'Bitfinex_ZRX_ETH'
        self.hedge_market = 'Binance_ZRX_ETH'

        self.brokers = broker_factory.create_brokers([self.mm_market, self.hedge_market])
        self.mm_broker = self.brokers[self.mm_market]
        self.hedge_broker = self.brokers[self.hedge_market]

        self.local_order = {}

        self.data_lost_count = 0
        self.risk_protect_count = 10

        self.fee_hedge_market = 0.002
        self.fee_mm_market = 0.002

        self.MIN_PRICE_DIFF = 0.02
        self.PLACE_AMOUNT_INIT = 10

        # 滑价
        self.SLID_PRICE = 0.005

        self.tick_count = 0

        self.last_update_min_stock = 0.0
        # Just for bfx
        self.min_amount_trade = 6

        self.cancel_orders(self.mm_market)
        logging.info('liquid_zrx======>Setup complete')

    def terminate(self):
        super(Liquid_zrx, self).terminate()
        self.cancel_orders(self.mm_market)
        logging.info('liquid_zrx======>terminate complete')

    @classmethod
    def cal_hedge_amount_min(cls, price):
        return 0.01 / price

    def cal_mm_buy_price(self, hedge_bid_price, mm_bid_price):
        price = hedge_bid_price * (1 - self.MIN_PRICE_DIFF)
        if price > mm_bid_price:
            price = round(mm_bid_price * (1 + self.SLID_PRICE), 8)
        return price

    def cal_handle_amount(self):
        return self.local_order['deal_amount'] - self.local_order['hedge_amount']

    def risk_protect(self):
        self.data_lost_count += 1
        if self.data_lost_count > self.risk_protect_count:
            logging.warn('liquid_zrx======>risk protect~stop liquid supply. %s' % self.data_lost_count)

            self.cancel_orders(self.mm_market)
            self.data_lost_count = 0

    def update_min_stock(self):
        # 更新bfx的最小交易量, 1个小时更新一次
        now = time.time()
        diff = now - self.last_update_min_stock
        if diff > 3600:
            min_stock = self.brokers[self.mm_market].get_min_stock()
            if min_stock:
                self.min_amount_trade = min_stock
            self.last_update_min_stock = now

    def update_other(self):
        self.update_min_stock()

    def tick(self, depths):
        try:
            mm_bid_price, mm_ask_price = self.get_ticker(depths, self.mm_market)
        except Exception as e:
            logging.debug(e)
            return

        try:
            hedge_bid_price, hedge_ask_price = self.get_ticker(depths, self.hedge_market)
        except Exception as e:
            logging.debug(e)
            self.risk_protect()
            return

        if not self.local_order:
            buy_price = self.cal_mm_buy_price(hedge_bid_price=hedge_bid_price, mm_bid_price=mm_bid_price)
            self.place_order(buy_price, self.PLACE_AMOUNT_INIT)
            return

        # update local order
        self.update_order()

        # all float type
        buy_price = self.cal_mm_buy_price(hedge_bid_price=hedge_bid_price, mm_bid_price=mm_bid_price)

        handle_amount = self.cal_handle_amount()
        hedge_amount_min = self.cal_hedge_amount_min(hedge_bid_price)
        if handle_amount < hedge_amount_min:
            order_price = self.local_order['price']
            if order_price <= buy_price:
                return
            self.cancel_flow(buy_price)
        else:
            self.hedge_order(handle_amount, hedge_bid_price)
            if self.local_order['status'] == constant.ORDER_STATE_PENDING:
                self.cancel_flow(buy_price)

    def cancel_flow(self, buy_price):
        # current order price is not good, so cancel and place again
        cancel_res = self.hedge_broker.cancel_order(order_id=self.local_order['order_id'])
        if not cancel_res:
            # cancel failed, just return
            return
        # delete local order
        self.local_order = {}
        # place new order
        self.place_order(buy_price, self.PLACE_AMOUNT_INIT)

    def update_order(self):
        # update local order
        order_id = self.local_order['order_id']
        error_count = 0
        while True:
            resp = self.mm_broker.get_order(order_id=order_id)
            if resp:
                self.local_order['deal_amount'] = resp['deal_amount']
                self.local_order['avg_price'] = resp['avg_price']
                self.local_order['status'] = resp['status']
                break
            error_count += 1
            if error_count >= 10:
                raise Exception("liquid_zrx======>update_order failed more than 10 times")
            time.sleep(config.INTERVAL_RETRY)

    def place_order(self, buy_price, buy_amount):
        can_buy_max = self.mm_broker.eth_available / buy_price

        buy_amount = min(buy_amount, can_buy_max)

        if buy_amount < self.min_amount_trade:
            raise Exception('liquid_zrx======>buy failed, maybe bfx eth is not enough')

        try:
            order_id = self.mm_broker.buy_limit_c(price=buy_price, amount=buy_amount)
        except Exception as e:
            logging.error("liquid_zrx======>place_order failed, exception: %s" % e)
            email_box.send_mail("liquid_zrx======>place_order failed, exception: %s" % e)
            return
        if not order_id:
            logging.error('liquid_zrx======>place_order failed, because order_id is none,that must not happen')
            raise Exception('liquid_zrx======>place_order failed, because order_id is none,that must not happen')
        self.local_order = {
            'order_id': order_id,
            'price': buy_price,
            'amount': buy_amount,
            'deal_amount': 0,
            'hedge_amount': 0,
            'type': 'buy',
            'status': constant.ORDER_STATE_PENDING,
            'time': time.time()
        }

    def hedge_order(self, hedge_amount, hedge_price):
        # hedge sell in binance
        can_sell_max = self.hedge_broker.zrx_available

        sell_amount_limit = self.cal_hedge_amount_min(hedge_price)
        if can_sell_max < hedge_amount:
            # post email
            if can_sell_max < sell_amount_limit:
                logging.error('liquid_zrx======>hedge_order failed, because can_sell_max: %s < %s' %
                              (can_sell_max, sell_amount_limit))
                raise Exception('liquid_zrx======>hedge_order failed, because can_sell_max: %s < %s' %
                                (can_sell_max, sell_amount_limit))
            sell_amount = can_sell_max
        else:
            sell_amount = hedge_amount

        sell_price = hedge_price
        hedge_index = 0
        while True:
            try:
                order_id = self.hedge_broker.sell_limit_c(amount=sell_amount, price=sell_price)
            except Exception as e:
                logging.error('liquid_zrx======>hedge sell order failed when sell_limit_c, error=%s' % e)
                raise Exception('liquid_zrx======>hedge sell order failed when sell_limit_c, error=%s' % e)
            deal_amount, avg_price = self.get_deal_amount(self.hedge_market, order_id)
            self.local_order['hedge_amount'] += deal_amount
            logging.info("liquid_zrx======>hedge sell %s, order_id=%s, amount=%s, price=%s, deal_amount=%s" %
                         (hedge_index, order_id, sell_amount, avg_price, deal_amount))
            diff_amount = round(sell_amount - deal_amount, 8)

            sell_amount_limit = self.cal_hedge_amount_min(sell_price)
            if diff_amount < sell_amount_limit:
                hedge_amount_current = self.local_order['hedge_amount']
                hedge_amount_target = self.local_order['deal_amount']

                logging.info('liquid_zrx======>hedge sell order success, target=%s, current=%s' %
                             (hedge_amount_target, hedge_amount_current))

                email_box.send_mail('liquid_zrx======>hedge sell order success, target=%s, current=%s' %
                                    (hedge_amount_target, hedge_amount_current))
                break
            ticker = self.get_latest_ticker(self.hedge_market)
            sell_amount = diff_amount
            sell_price = ticker['bid']
            hedge_index += 1

    @classmethod
    def get_ticker(cls, depths, market):
        bid_price = depths[market]["bids"][0]['price']
        ask_price = depths[market]["asks"][0]['price']
        return bid_price, ask_price

    def update_balance(self):
        self.mm_broker.get_balances_c()
        self.hedge_broker.get_balances_c()

    def cancel_orders(self, market):
        logging.info('liquid_zrx======>cancel zrx orders on bitfinex')
        self.brokers[market].cancel_orders()
