#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import division
import logging

import time

from quant import config
from quant.common import constant
from .basicbot import BasicBot
from quant.brokers import broker_factory


class Arbitrage(BasicBot):
    """
    btc和bt1 bt2的合成与分解套利
    兑换比例1btc=1bt1+1bt2
    python -m quant.cli -mBitfinex_BTC_USD,Bitfinex_BT1_BTC,Bitfinex_BT2_BTC t-watch-bfx-btc2 -v
    """

    def __init__(self, monitor_only=False):
        super(Arbitrage, self).__init__()
        self.base_pair = "Bitfinex_BTC_USD"
        self.pair_1 = "Bitfinex_BT1_BTC"
        self.pair_2 = "Bitfinex_BT2_BTC"

        self.monitor_only = monitor_only
        self.precision = 8

        self.fee_base = 0.002
        self.fee_pair1 = 0.002
        self.fee_pair2 = 0.002
        """交易所限制的最小交易量，由交易所和币种共同决定"""
        self.min_amount_market = 0.02
        """单次交易的最大量和最小量"""
        self.max_trade_amount = 0.1
        self.min_trade_amount = 0.02

        # 赢利触发点，差价，百分比更靠谱?
        self.profit_trigger = 1.5
        self.last_trade = 0
        self.skip = False
        self.brokers = broker_factory.create_brokers([self.base_pair, self.pair_1, self.pair_2])

        self.error_count = 0

    def is_depths_available(self, depths):
        res = self.base_pair in depths and self.pair_1 in depths and self.pair_2 in depths
        if not res:
            return False
        pair1_bid_price = depths[self.pair_1]['bids'][0]['price']
        pair1_ask_price = depths[self.pair_1]['asks'][0]['price']
        if pair1_ask_price <= 0 or pair1_bid_price <= 0:
            return False

        pair2_bid_price = depths[self.pair_2]['bids'][0]['price']
        pair2_ask_price = depths[self.pair_2]['asks'][0]['price']
        if pair2_ask_price <= 0 or pair2_bid_price <= 0:
            return False

        return True

    def tick(self, depths):
        if not self.monitor_only:
            self.update_balance()
            self.risk_protect()
            self.cancel_all_orders(self.base_pair)

        if not self.is_depths_available(depths):
            return

        self.skip = False
        self.forward(depths)
        self.reverse(depths)

    def forward(self, depths):
        logging.info("==============正循环, 卖bt1 bt2==============")
        """所有的real都是带手续费的价格"""
        pair1_bid_amount = depths[self.pair_1]['bids'][0]['amount']
        pair1_bid_price = depths[self.pair_1]['bids'][0]['price']
        pair1_bid_price_real = pair1_bid_price * (1 - self.fee_pair1)

        pair2_bid_amount = depths[self.pair_2]['bids'][0]['amount']
        pair2_bid_price = depths[self.pair_2]['bids'][0]['price']
        pair2_bid_price_real = pair2_bid_price * (1 - self.fee_pair2)

        synthetic_bid_price = round(pair1_bid_price + pair2_bid_price, self.precision)
        synthetic_bid_price_real = round(pair1_bid_price_real + pair2_bid_price_real, self.precision)

        """价差， diff=卖－买"""
        p_diff = round(synthetic_bid_price - 1, self.precision)
        logging.info("forward======>%s bid_price: %s,  %s bid_price: %s" %
                     (self.pair_1, pair1_bid_price, self.pair_2, pair2_bid_price))
        logging.info("forward======>synthetic_bid_price: %s,   p_diff: %s" % (synthetic_bid_price, p_diff))

        """数量限制"""
        hedge_btc_amount_market = min(pair1_bid_amount, pair2_bid_amount)
        hedge_btc_amount_market = min(self.max_trade_amount, hedge_btc_amount_market)
        hedge_btc_amount_market = hedge_btc_amount_market / 2

        if self.monitor_only:
            hedge_btc_amount = hedge_btc_amount_market
            if hedge_btc_amount < self.min_amount_market:
                logging.info("forward======>hedge_btc_amount is too small! %s" % hedge_btc_amount)
                return
        else:
            hedge_btc_amount_balance = round(min(self.brokers[self.base_pair].bt1_available,
                                                 self.brokers[self.base_pair].bt2_available), 8)
            hedge_btc_amount = min(hedge_btc_amount_market, hedge_btc_amount_balance, self.min_trade_amount)
            logging.info("forward======>balance allow btc: %s, market allow btc: %s " %
                         (hedge_btc_amount_balance, hedge_btc_amount_market))
            if hedge_btc_amount < self.min_amount_market:
                logging.info("forward======>hedge_btc_amount is too small! %s" % hedge_btc_amount)
                return

        logging.info("forward======>synthetic_bid_price_real: %s, [%s, %s]" %
                     (synthetic_bid_price_real, pair1_bid_price_real, pair2_bid_price_real))
        t_price = round(synthetic_bid_price_real - 1, self.precision)
        profit = round(t_price * hedge_btc_amount, self.precision)
        logging.info("forward======>t_price: %s, profit: %s" % (t_price, profit))
        if profit > 0:
            logging.info("forward======>find profit!!!: profit:%s,  quote amount: %s,  t_price: %s" %
                         (profit, hedge_btc_amount, t_price))

            current_time = time.time()
            if current_time - self.last_trade < 1:
                logging.warn("forward======>Can't automate this trade, last trade " +
                             "occured %.2f seconds ago" %
                             (current_time - self.last_trade))
                return

            if not self.monitor_only:
                sell_amount_1 = hedge_btc_amount
                sell_price_1 = pair1_bid_price
                logging.info("forward=====>%s place sell order, price=%s, amount=%s" %
                             (self.pair_1, sell_price_1, sell_amount_1))
                r_sell1 = self.new_order(market=self.pair_1, order_type='sell', amount=sell_amount_1,
                                         price=sell_price_1)
                if not r_sell1 or ('order_id' not in r_sell1):
                    # bt1 place order failed
                    logging.warn("forward======>%s place sell order failed, give up and return" % self.pair_1)
                    return

                order_id_1 = r_sell1['order_id']
                time.sleep(config.INTERVAL_API)

                # 计算bt1的成交额度
                deal_amount_1 = self.get_deal_amount(market=self.pair_1, order_id=order_id_1)
                logging.info("forward======>%s order %s deal amount %s, origin amount %s" %
                             (self.pair_1, order_id_1, deal_amount_1, sell_amount_1))

                if deal_amount_1 < self.min_trade_amount:
                    logging.warn("forward======>%s order %s deal amount %s < %s, give up and return" %
                                 (self.pair_1, order_id_1, deal_amount_1, self.min_trade_amount))
                    return

                sell_amount_2 = deal_amount_1
                sell_price_2 = pair2_bid_price
                while True:
                    logging.info("forward=====>%s place sell order, price=%s, amount=%s" %
                                 (self.pair_2, sell_price_2, sell_amount_2))
                    r_sell2 = self.new_order(market=self.pair_2, order_type='sell', amount=sell_amount_2,
                                             price=sell_price_2)
                    if not r_sell2 or ('order_id' not in r_sell2):
                        logging.warn("forward======>%s place sell order failed, %s seconds later retry" %
                                     (self.pair_2, config.INTERVAL_API))
                        time.sleep(config.INTERVAL_API)
                        continue

                    order_id_2 = r_sell2['order_id']
                    time.sleep(config.INTERVAL_API)
                    deal_amount_2 = self.get_deal_amount(market=self.pair_2, order_id=order_id_2)
                    logging.info("forward======>%s order %s deal amount %s, origin amount %s" %
                                 (self.pair_2, order_id_2, deal_amount_2, sell_amount_2))

                    diff_amount = sell_amount_2 - deal_amount_2
                    if diff_amount < self.min_trade_amount:
                        logging.info("forward======>trade circle complete, and %s deal amount: %s" %
                                     (self.pair_2, deal_amount_2))
                        break

                    ticker_2 = self.get_new_ticker(self.pair_2)
                    sell_price_2 = ticker_2['bid']
                    sell_amount_2 = diff_amount
                    time.sleep(config.INTERVAL_API)

                self.skip = True

            self.last_trade = time.time()

    def reverse(self, depths):
        if self.skip and (not self.monitor_only):
            return
        logging.info("==============逆循环, 买bt1 bt2==============")
        pair1_ask_amount = depths[self.pair_1]['asks'][0]['amount']
        pair1_ask_price = depths[self.pair_1]['asks'][0]['price']
        pair1_ask_price_real = pair1_ask_price * (1 + self.fee_pair1)

        pair2_ask_amount = depths[self.pair_2]['asks'][0]['amount']
        pair2_ask_price = depths[self.pair_2]['asks'][0]['price']
        pair2_ask_price_real = pair2_ask_price * (1 + self.fee_pair2)

        synthetic_ask_price = round(pair1_ask_price + pair2_ask_price, self.precision)
        synthetic_ask_price_real = round(pair1_ask_price_real + pair2_ask_price_real, self.precision)
        p_diff = round(1 - synthetic_ask_price, self.precision)

        logging.info("reverse======>%s ask_price: %s,  %s ask_price: %s" %
                     (self.pair_1, pair1_ask_price, self.pair_2, pair2_ask_price))
        logging.info("reverse======>synthetic_ask_price: %s,   p_diff: %s" % (synthetic_ask_price, p_diff))

        """数量限制"""
        hedge_btc_amount_market = min(pair2_ask_amount, pair1_ask_amount)
        hedge_btc_amount_market = min(self.max_trade_amount, hedge_btc_amount_market)
        hedge_btc_amount_market = hedge_btc_amount_market / 2

        if self.monitor_only:
            hedge_btc_amount = hedge_btc_amount_market
            if hedge_btc_amount < self.min_amount_market:
                logging.info("reverse======>hedge_btc_amount is too small! %s" % hedge_btc_amount)
                return
        else:
            btc_amount_balance = round(self.brokers[self.base_pair].btc_available, 8)

            hedge_bt1_amount_balance = round(btc_amount_balance / pair1_ask_price_real, 8)
            hedge_bt2_amount_balance = round(btc_amount_balance / pair2_ask_price_real, 8)
            hedge_btc_amount_balance = round(min(hedge_bt1_amount_balance, hedge_bt2_amount_balance), 8)

            hedge_btc_amount = min(hedge_btc_amount_market, hedge_btc_amount_balance, self.min_trade_amount)
            logging.info("reverse======>balance allow btc: %s, market allow btc: %s " %
                         (hedge_btc_amount_balance, hedge_btc_amount_market))
            hedge_btc_amount_total = round(hedge_btc_amount * 2, 8)
            if (hedge_btc_amount < self.min_amount_market) or (hedge_btc_amount_total > btc_amount_balance):
                logging.warn("reverse======>hedge_btc_amount is too small! %s, or btc total %s large than balance %s" %
                             (hedge_btc_amount, hedge_btc_amount_total, btc_amount_balance))
                return
        logging.info("reverse======>synthetic_ask_price_real: %s, [%s, %s]" %
                     (synthetic_ask_price_real, pair1_ask_price_real, pair2_ask_price_real))
        t_price = round(1 - synthetic_ask_price_real, self.precision)
        profit = round(t_price * hedge_btc_amount, self.precision)
        logging.info("reverse======>t_price: %s, profit: %s" % (t_price, profit))
        if profit > 0:
            logging.info("reverse======>find profit!!!: profit:%s,  quote amount: %s ,  t_price: %s" %
                         (profit, hedge_btc_amount, t_price))

            current_time = time.time()
            if current_time - self.last_trade < 1:
                logging.warn("reverse======>Can't automate this trade, last trade " +
                             "occured %.2f seconds ago" %
                             (current_time - self.last_trade))
                return

            if not self.monitor_only:
                buy_amount_1 = hedge_btc_amount
                buy_price_1 = pair1_ask_price
                logging.info("reverse=====>%s place buy order, price=%s, amount=%s" %
                             (self.pair_1, buy_price_1, buy_amount_1))
                r_buy1 = self.new_order(market=self.pair_1, order_type='buy', amount=buy_amount_1,
                                        price=buy_price_1)
                if not r_buy1 or ('order_id' not in r_buy1):
                    # bt1 place order failed
                    logging.warn("reverse======>%s place buy order failed, give up and return" % self.pair_1)
                    return

                order_id_1 = r_buy1['order_id']
                time.sleep(config.INTERVAL_API)

                # 计算bt1的成交额度
                deal_amount_1 = self.get_deal_amount(market=self.pair_1, order_id=order_id_1)
                logging.info("reverse======>%s order %s deal amount %s, origin amount %s" %
                             (self.pair_1, order_id_1, deal_amount_1, buy_amount_1))

                if deal_amount_1 < self.min_trade_amount:
                    logging.warn("reverse======>%s order %s deal amount %s < %s, give up and return" %
                                 (self.pair_1, order_id_1, deal_amount_1, self.min_trade_amount))
                    return

                buy_amount_2 = deal_amount_1
                buy_price_2 = pair2_ask_price
                while True:
                    logging.info("reverse=====>%s place buy order, price=%s, amount=%s" %
                                 (self.pair_2, buy_price_2, buy_amount_2))
                    r_buy2 = self.new_order(market=self.pair_2, order_type='buy', amount=buy_amount_2,
                                            price=buy_price_2)
                    if not r_buy2 or ('order_id' not in r_buy2):
                        logging.warn("reverse======>%s place buy order failed, %s seconds later retry" %
                                     (self.pair_2, config.INTERVAL_API))
                        time.sleep(config.INTERVAL_API)
                        continue

                    order_id_2 = r_buy2['order_id']
                    time.sleep(config.INTERVAL_API)
                    deal_amount_2 = self.get_deal_amount(market=self.pair_2, order_id=order_id_2)
                    logging.info("reverse======>%s order %s deal amount %s, origin amount %s" %
                                 (self.pair_2, order_id_2, deal_amount_2, buy_amount_2))

                    diff_amount = buy_amount_2 - deal_amount_2
                    if diff_amount < self.min_trade_amount:
                        logging.info("reverse======>trade circle complete, and %s deal amount: %s" %
                                     (self.pair_2, deal_amount_2))
                        break

                    ticker_2 = self.get_new_ticker(self.pair_2)
                    buy_price_2 = ticker_2['ask']
                    buy_amount_2 = diff_amount
                    time.sleep(config.INTERVAL_API)

                self.skip = True

            self.last_trade = time.time()

    def get_deal_amount(self, market, order_id):
        while True:
            order_status = self.brokers[market].get_order(order_id)
            if not order_status:
                time.sleep(config.INTERVAL_API)
                continue
            break

        if order_status['status'] == constant.ORDER_STATE_PENDING:
            self.brokers[market].cancel_order(order_id)
            time.sleep(config.INTERVAL_RETRY)
            return self.get_deal_amount(market, order_id)
        else:
            return order_status['deal_amount']

    def cancel_all_orders(self, market):
        self.brokers[market].cancel_all()

    def get_new_ticker(self, market):
        while True:
            ticker = self.brokers[market].get_ticker()
            if ticker:
                break
            time.sleep(config.INTERVAL_API)

        return ticker

    def update_balance(self):
        self.brokers[self.base_pair].get_balances()

    def risk_protect(self):
        bt1_bal = self.brokers[self.base_pair].bt1_available
        bt2_bal = self.brokers[self.base_pair].bt2_available
        diff = abs(bt1_bal - bt2_bal)
        logging.info("risk======>bt1: %s, bt2: %s, diff: %s" % (bt1_bal, bt2_bal, diff))
        if diff >= self.min_trade_amount:
            self.error_count += 1
            logging.warn("risk======>bt1 balance:%s not equal to bt2 balance:%s, error_count:%s" %
                         (bt1_bal, bt2_bal, self.error_count))

        if self.error_count > 3:
            logging.warn("risk======>error_count > 3, so raise exception")
            assert False
