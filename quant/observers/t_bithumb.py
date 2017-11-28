#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import division

import logging
import time

from quant import config
from quant.brokers import broker_factory
from .basicbot import BasicBot
from quant.common import log

MESSAGE_TRY_AGAIN = 'Please try again'


class T_Bithumb(BasicBot):
    """
    bch:
    python -m quant.cli -mBithumb_BCH_KRW,Bitfinex_BCH_BTC,Bithumb_BTC_KRW -o=T_Bithumb_BCH -f=bithumb_bch -v

    目前的限制:
    """

    def __init__(self, base_pair, pair_1, pair_2, **kwargs):
        super(T_Bithumb, self).__init__()
        self.base_pair = base_pair
        self.pair_1 = pair_1
        self.pair_2 = pair_2
        self.monitor_only = kwargs['monitor_only']
        """小数位进度，krw定价为2, btc定价为8"""
        self.precision = kwargs['precision']
        """交易所和币种对应的手续费, 一般为1%, 2%, 2.5%"""
        self.fee_base = kwargs['fee_base']
        self.fee_pair1 = kwargs['fee_pair1']
        self.fee_pair2 = kwargs['fee_pair2']

        """交易所限制的最小交易量，由交易所和币种共同决定"""
        self.min_stock_base = kwargs['min_stock_base']
        self.min_stock_1 = kwargs['min_stock_pair1']
        self.min_stock_2 = kwargs['min_stock_pair2']

        self.min_amount_market = max(self.min_stock_base, self.min_stock_1)
        self.min_amount_mid = self.min_stock_2
        self.last_update_min_stock = 0.0

        """单次交易的最大量和最小量"""
        self.max_trade_amount = kwargs['max_trade_amount']
        self.min_trade_amount = kwargs['min_trade_amount']

        # 赢利触发点，差价，百分比更靠谱?
        self.trigger_percent = 0.7
        self.last_trade = 0
        self.skip = False

        # just for count for chance profit
        self.count_forward = 0
        self.count_reverse = 0

        self.origin_assets = {}
        self.risk_count = 0
        self.logging_balance = True

        if not self.monitor_only:
            self.brokers = broker_factory.create_brokers([self.base_pair, self.pair_1, self.pair_2])
            self.update_min_stock()
            self.update_balance()

        self.logger_other = log.get_logger('log/bithumb_other.log')
        logging.debug("T_Bithumb params: " + str(kwargs))

    def is_depths_available(self, depths):
        if not depths:
            return False
        res = self.base_pair in depths and self.pair_1 in depths and self.pair_2 in depths
        if not res:
            return False

        if not depths[self.base_pair]['bids'] or not depths[self.base_pair]['asks']:
            return False

        if not depths[self.pair_1]['bids'] or not depths[self.pair_1]['asks']:
            return False

        if not depths[self.pair_2]['bids'] or not depths[self.pair_2]['asks']:
            return False

        base_bid_price = depths[self.base_pair]['bids'][0]['price']
        base_ask_price = depths[self.base_pair]['asks'][0]['price']
        if base_ask_price <= 0 or base_bid_price <= 0:
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

    def terminate(self):
        super(T_Bithumb, self).terminate()
        self.brokers[self.pair_1].cancel_all()

    def update_min_stock(self):
        # 更新bfx的最小交易量, 1个小时更新一次
        now = time.time()
        diff = now - self.last_update_min_stock
        if diff > 3600:
            min_stock = self.brokers[self.pair_1].get_min_stock()
            if min_stock:
                self.min_stock_1 = min_stock
                self.min_amount_market = max(self.min_stock_base, self.min_stock_1)
                logging.debug('update %s min stock: %s' % (self.pair_1, min_stock))
            self.last_update_min_stock = now

    def update_other(self):
        if not self.monitor_only:
            self.update_min_stock()

    def tick(self, depths):
        if not self.is_depths_available(depths):
            return
        self.skip = False
        self.forward(depths)
        self.reverse(depths)

    def forward(self, depths):
        logging.debug("==============正循环, base买 合成卖==============")
        base_pair_ask_amount = depths[self.base_pair]['asks'][0]['amount']
        base_pair_ask_price = depths[self.base_pair]['asks'][0]['price']
        base_pair_ask_price_real = base_pair_ask_price * (1 + self.fee_base)

        logging.debug("forward======>base_pair: %s ask_price:%s" % (self.base_pair, base_pair_ask_price))

        """所有的real都是带手续费的价格"""
        pair1_bid_amount = depths[self.pair_1]['bids'][0]['amount']
        pair1_bid_price = depths[self.pair_1]['bids'][0]['price']
        pair1_bid_price_real = pair1_bid_price * (1 - self.fee_pair1)

        pair2_bid_amount = depths[self.pair_2]['bids'][0]['amount']
        pair2_bid_price = depths[self.pair_2]['bids'][0]['price']
        pair2_bid_price_real = pair2_bid_price * (1 - self.fee_pair2)

        synthetic_bid_price = round(pair1_bid_price * pair2_bid_price, self.precision)
        synthetic_bid_price_real = round(pair1_bid_price_real * pair2_bid_price_real, self.precision)
        """价差， diff=卖－买"""
        p_diff = round(synthetic_bid_price - base_pair_ask_price, self.precision)

        logging.debug("forward======>%s bid_price: %s,  %s bid_price: %s" %
                      (self.pair_1, pair1_bid_price, self.pair_2, pair2_bid_price))
        logging.debug("forward======>synthetic_bid_price: %s,   p_diff: %s" % (synthetic_bid_price, p_diff))

        if pair1_bid_price == 0:
            return

        pair_2to1_quote_amount = round(pair2_bid_amount / pair1_bid_price, 8)

        """市场限制base最多能买多少个bch, pair1 最多能卖多少个bch, 并且在上线和下线范围内[5, 0.05]"""
        """吃单50%, 两个目的：1，增加成交几率； 2，在🈷️余额充足的前提下，委单的手续费部分可能不能成交(极端)"""
        hedge_quote_amount_market = min(base_pair_ask_amount, pair1_bid_amount)
        hedge_quote_amount_market = min(hedge_quote_amount_market, pair_2to1_quote_amount)
        hedge_quote_amount_market = min(self.max_trade_amount, hedge_quote_amount_market)
        hedge_quote_amount_market = hedge_quote_amount_market / 2
        hedge_mid_amount_market = round(hedge_quote_amount_market * pair1_bid_price, 8)

        if self.monitor_only:
            hedge_quote_amount = hedge_quote_amount_market
            hedge_mid_amount = round(hedge_quote_amount * pair1_bid_price, 8)
            if hedge_quote_amount < self.min_amount_market:
                """bitfinex限制bch_krw最小可交易的bch order size为0.001"""
                logging.debug("forward======>hedge_quote_amount is too small! %s" % hedge_quote_amount)
                return

            if hedge_mid_amount < self.min_amount_mid:
                """bitfinex限制btc_krw最小可交易amount为0.005, liqui限制单次交易btc的amount为0.0001, 所以这里取0.005"""
                logging.debug("forward======>hedge_mid_amount is too small! %s" % hedge_mid_amount)
                return
        else:
            """余额限制base最多能买多少个bch, pair1 最多能卖多少个bch, 要带上手续费"""
            hedge_quote_amount_balance = round(min(self.brokers[self.pair_1].bch_available,
                                                   self.brokers[
                                                       self.base_pair].krw_available / base_pair_ask_price_real),
                                               8)
            hedge_mid_amount_balance = round(min(self.brokers[self.pair_2].btc_available,
                                                 self.brokers[self.pair_1].bch_available * pair1_bid_price_real), 8)

            """取市场和余额共同限制的amount"""
            hedge_quote_amount = min(hedge_quote_amount_market, hedge_quote_amount_balance, self.min_trade_amount)
            hedge_mid_amount = hedge_quote_amount * pair1_bid_price

            logging.debug("forward======>balance allow quote: %s and mid: %s, market allow quote: %s and btc: %s " %
                          (hedge_quote_amount_balance, hedge_mid_amount_balance,
                           hedge_quote_amount_market, hedge_mid_amount_market))

            if hedge_quote_amount < self.min_amount_market:
                """bitfinex限制bch_krw最小可交易的bch order size为0.001"""
                logging.debug("forward======>hedge_quote_amount is too small! Because %s < %s" %
                              (hedge_quote_amount, self.min_amount_market))
                return

            if hedge_mid_amount < self.min_amount_mid or hedge_mid_amount > hedge_mid_amount_balance:
                """bitfinex限制btc_krw最小可交易amount为0.005, liqui限制单次交易btc的amount为0.0001, 所以这里取0.005"""
                """btc余额不足也不行"""
                logging.debug("forward======>hedge_mid_amount is too small! Because %s < %s or > %s" %
                              (hedge_mid_amount, self.min_amount_mid, hedge_mid_amount_balance))
                return

        logging.debug("forward======>hedge_quote_amount: %s, hedge_mid_amount:%s" %
                      (hedge_quote_amount, hedge_mid_amount))

        """
        计算的关键点在于bcc和btc的买卖amount除去手续费后是相同的，也就是进行一个循环交易后bcc和btc的总量是不变的, 变的是krw
        profit=去除交易手续费后交易hedge_quote_amount的赢利
        """
        logging.debug("forward======>base_pair_ask_price_real: %s,  synthetic_bid_price_real: %s, [%s, %s]" %
                      (base_pair_ask_price_real, synthetic_bid_price_real, pair1_bid_price_real,
                       pair2_bid_price_real))
        t_price = round(synthetic_bid_price_real - base_pair_ask_price_real, self.precision)
        """差价百分比"""
        t_price_percent = round(t_price / base_pair_ask_price_real * 100, 2)
        profit = round(t_price * hedge_quote_amount, self.precision)
        logging.debug(
            "forward======>t_price: %s, t_price_percent: %s, profit: %s" % (t_price, t_price_percent, profit))
        if profit > 0:
            if t_price_percent < self.trigger_percent:
                logging.debug("forward======>profit percent should >= %s" % self.trigger_percent)
                return
            self.count_forward += 1
            self.logger_other.info("count_forward: %s, count_reverse: %s" % (self.count_forward, self.count_reverse))
            logging.debug(
                "forward======>find profit!!!: profit:%s,  quote amount: %s and mid amount: %s,  t_price: %s" %
                (profit, hedge_quote_amount, hedge_mid_amount, t_price))

            current_time = time.time()
            if current_time - self.last_trade < 1:
                logging.debug("forward======>Can't automate this trade, last trade " +
                              "occured %.2f seconds ago" %
                              (current_time - self.last_trade))
                return

            if not self.monitor_only:
                # bch_btc sell first, bch_krw btc_krw second, bch_btc起连接作用，所以先交易
                sell_amount_1 = hedge_quote_amount
                sell_price_1 = pair1_bid_price

                logging.info("forward=====>%s place sell order, price=%s, amount=%s" %
                             (self.pair_1, sell_price_1, sell_amount_1))

                order_id_1 = self.brokers[self.pair_1].sell_limit(amount=sell_amount_1, price=sell_price_1)

                if not order_id_1 or order_id_1 < 0:
                    logging.info("forward======>%s place sell order failed, give up and return" % self.pair_1)
                    return

                # time.sleep(config.INTERVAL_API)
                deal_amount_1, deal_avg_price_1 = self.get_deal_amount(market=self.pair_1, order_id=order_id_1)
                if deal_amount_1 < self.min_stock_1:
                    '''
                    理论上不会出现0.0<deal_amount_1<self.min_stock_1这种情况, 经过实盘测试确实不会出现这种情况
                    '''
                    logging.error("forward======>%s order %s deal amount %s < %s, give up and return" %
                                  (self.pair_1, order_id_1, deal_amount_1, self.min_stock_1))
                    return
                else:
                    logging.info("forward======>%s make sell order that id=%s, price= %s, amount=%s, deal_amount=%s" %
                                 (self.pair_1, order_id_1, sell_price_1, sell_amount_1, deal_amount_1))

                if not deal_avg_price_1:
                    logging.error("forward======>%s order %s avg price must not be empty" % (self.pair_1, order_id_1))
                    assert False

                '''bithumb 限制委单小数位最多为4'''
                # 这个地方注意要用平均成交价来计算pair2的amount
                sell_amount_2 = round(deal_amount_1 * deal_avg_price_1, 4)
                sell_price_2 = pair2_bid_price
                if sell_amount_2 < self.min_stock_2:
                    # must not happen, 理论上不该出现这种场景，因为交易之前已经限定了条件
                    logging.error('forward======>pair2下单量小于最小限制, 即%s < %s' % (sell_amount_2, self.min_stock_2))
                    assert False

                buy_amount_base = round(deal_amount_1 * (1 + self.fee_base), 4)
                buy_price_base = base_pair_ask_price

                done_2 = False
                done_base = False
                while True:
                    order_id_2 = None
                    order_2 = None
                    order_id_base = None
                    order_base = None

                    if not done_2:
                        logging.info("forward=====>%s place sell order, price=%s, amount=%s" %
                                     (self.pair_2, sell_price_2, sell_amount_2))
                        order_2, order_2_error = self.brokers[self.pair_2].sell_limit(amount=sell_amount_2,
                                                                                      price=sell_price_2)
                        if self.has_error(order_2, order_2_error):
                            logging.error("forward======>%s place sell order failed: %s" % (self.pair_2, order_2_error))
                        else:
                            order_id_2 = order_2['order_id']
                            if not order_id_2:
                                logging.error("forward======>%s order_id_2 is None shouldn't happen" % self.pair_2)
                                assert False

                    if not done_base:
                        logging.info("forward=====>%s place buy order, price=%s, amount=%s" %
                                     (self.base_pair, buy_price_base, buy_amount_base))
                        order_base, order_base_error = self.brokers[self.base_pair].buy_limit(amount=buy_amount_base,
                                                                                              price=buy_price_base)
                        if self.has_error(order_base, order_base_error):
                            logging.error("forward======>%s place buy order failed: %s" % (self.base_pair,
                                                                                           order_base_error))
                        else:
                            order_id_base = order_base['order_id']
                            if not order_id_base:
                                logging.error("forward======>%s order_id_base is None shouldn't happen" %
                                              self.base_pair)
                                assert False

                    time.sleep(config.INTERVAL_API)
                    if not done_2 and order_2 and order_id_2 and order_id_2 >= 0:
                        deal_amount_2 = self.get_btb_deal_amount(self.pair_2, order_id_2, order_2, 'ask')
                        diff_amount_2 = round(sell_amount_2 - deal_amount_2, 4)
                        logging.info("forward======>%s sell order that id=%s, price=%s, amount=%s, deal_amount=%s\
                                      diff_amount=%s" % (self.pair_2, order_id_2, sell_price_2, sell_amount_2,
                                                         deal_amount_2, diff_amount_2))
                        if diff_amount_2 < self.min_stock_2:
                            logging.info("forward======>%s trade complete" % self.pair_2)
                            done_2 = True
                        else:
                            # 后续用market_buy搞定, 减少一次ticker的读取
                            ticker2 = self.get_latest_ticker(self.pair_2)
                            sell_price_2 = ticker2['bid']
                            sell_amount_2 = diff_amount_2

                    if not done_base and order_base and order_id_base and order_id_base >= 0:
                        deal_amount_base = self.get_btb_deal_amount(self.base_pair, order_id_base, order_base, 'bid')
                        diff_amount_base = round(buy_amount_base - deal_amount_base, 4)
                        logging.info("forward======>%s buy order that id=%s, price=%s, amount=%s, deal_amount=%s\
                                      diff_amount=%s" % (self.base_pair, order_id_base, buy_price_base, buy_amount_base,
                                                         deal_amount_base, diff_amount_base))
                        if diff_amount_base < self.min_stock_base:
                            logging.info("forward======>%s trade complete" % self.base_pair)
                            done_base = True
                        else:
                            # 后续用market_buy搞定, 减少一次ticker的读取
                            ticker_base = self.get_latest_ticker(self.base_pair)
                            buy_price_base = ticker_base['ask']
                            buy_amount_base = diff_amount_base

                    if done_2 and done_base:
                        self.logging_balance = True
                        logging.info("forward======>trade all complete, at count %s" % self.count_forward)
                        break
                    time.sleep(config.INTERVAL_API)

                self.skip = True

            self.last_trade = time.time()

    def reverse(self, depths):
        if self.skip and (not self.monitor_only):
            return
        logging.debug("==============逆循环, base卖 合成买==============")
        base_pair_bid_amount = depths[self.base_pair]['bids'][0]['amount']
        base_pair_bid_price = depths[self.base_pair]['bids'][0]['price']
        base_pair_bid_price_real = base_pair_bid_price * (1 - self.fee_base)

        logging.debug("reverse======>base_pair: %s bid_price:%s" % (self.base_pair, base_pair_bid_price))

        pair1_ask_amount = depths[self.pair_1]['asks'][0]['amount']
        pair1_ask_price = depths[self.pair_1]['asks'][0]['price']
        pair1_ask_price_real = pair1_ask_price * (1 + self.fee_pair1)

        pair2_ask_amount = depths[self.pair_2]['asks'][0]['amount']
        pair2_ask_price = depths[self.pair_2]['asks'][0]['price']
        pair2_ask_price_real = pair2_ask_price * (1 + self.fee_pair2)

        synthetic_ask_price = round(pair1_ask_price * pair2_ask_price, self.precision)
        synthetic_ask_price_real = round(pair1_ask_price_real * pair2_ask_price_real, self.precision)
        p_diff = round(base_pair_bid_price - synthetic_ask_price, self.precision)

        logging.debug("reverse======>%s ask_price: %s,  %s ask_price: %s" %
                      (self.pair_1, pair1_ask_price, self.pair_2, pair2_ask_price))
        logging.debug("reverse======>synthetic_ask_price: %s,   p_diff: %s" % (synthetic_ask_price, p_diff))
        if pair1_ask_price == 0 or pair2_ask_price == 0:
            return

        pair_2to1_quote_amount = round(pair2_ask_amount / pair1_ask_price, 8)

        """市场限制base最多能卖多少个bch, pair1 最多能买多少个bch, 并且在上线和下线范围内[5, 0.05]"""
        """吃单50%, 两个目的：1，增加成交几率； 2，在🈷️余额充足的前提下，委单的手续费部分可能不能成交(极端)"""
        hedge_quote_amount_market = min(base_pair_bid_amount, pair1_ask_amount)
        hedge_quote_amount_market = min(hedge_quote_amount_market, pair_2to1_quote_amount)
        hedge_quote_amount_market = min(self.max_trade_amount, hedge_quote_amount_market)
        hedge_quote_amount_market = hedge_quote_amount_market / 2
        hedge_mid_amount_market = round(hedge_quote_amount_market * pair1_ask_price, 8)

        if self.monitor_only:
            hedge_quote_amount = hedge_quote_amount_market
            hedge_mid_amount = round(hedge_quote_amount * pair1_ask_price, 8)
            if hedge_quote_amount < self.min_amount_market:
                """bfx限制bch最小订单数量为0.001"""
                logging.debug("reverse======>hedge_quote_amount is too small! %s" % hedge_quote_amount)
                return

            if hedge_mid_amount < self.min_amount_mid:
                """lq限制最小btc的total为0.0001, bfx的bch_krw交易订单限制amount为0.005"""
                logging.debug("reverse======>hedge_mid_amount is too small! %s" % hedge_mid_amount)
                return
        else:
            """余额限制base最多能卖多少个bch, pair1 最多能买多少个bch, 要带上手续费"""
            hedge_quote_amount_balance = round(min(self.brokers[self.base_pair].bch_available,
                                                   self.brokers[self.pair_1].btc_available / pair1_ask_price_real), 8)
            hedge_mid_amount_balance = round(min(self.brokers[self.pair_2].krw_available / pair2_ask_price_real,
                                                 self.brokers[self.pair_1].btc_available), 8)

            hedge_quote_amount = min(hedge_quote_amount_market, hedge_quote_amount_balance, self.min_trade_amount)
            hedge_mid_amount = hedge_quote_amount * pair1_ask_price

            logging.debug("reverse======>balance allow bch: %s and btc: %s, market allow bch: %s and btc: %s " %
                          (hedge_quote_amount_balance, hedge_mid_amount_balance,
                           hedge_quote_amount_market, hedge_mid_amount_market))

            if hedge_quote_amount < self.min_amount_market:
                """bfx限制bch最小订单数量为0.001"""
                logging.debug("reverse======>hedge_quote_amount is too small! %s" % hedge_quote_amount)
                return

            if hedge_mid_amount < self.min_amount_mid or hedge_mid_amount > hedge_mid_amount_balance:
                """lq限制最小btc的total为0.0001, bfx的bch_btc交易订单限制amount为0.005"""
                """并且不能大于余额的限制"""
                logging.debug("reverse======>hedge_mid_amount is too small! %s" % hedge_mid_amount)
                return

        logging.debug("reverse======>hedge_quote_amount: %s, hedge_mid_amount:%s" %
                      (hedge_quote_amount, hedge_mid_amount))

        """
        计算的关键点在于bcc和btc的买卖amount除去手续费后是相同的，也就是进行一个循环交易后bcc和btc的总量是不变的, 变的是krw
        profit=去除交易手续费后交易hedge_quote_amount的赢利
        """
        logging.debug("reverse======>base_pair_bid_price_real: %s,  synthetic_ask_price_real: %s, [%s, %s]" %
                      (base_pair_bid_price_real, synthetic_ask_price_real, pair1_ask_price_real,
                       pair2_ask_price_real))
        t_price = round(base_pair_bid_price_real - synthetic_ask_price_real, self.precision)
        t_price_percent = round(t_price / synthetic_ask_price_real * 100, 2)
        profit = round(t_price * hedge_quote_amount, self.precision)
        logging.debug(
            "reverse======>t_price: %s, t_price_percent: %s, profit: %s" % (t_price, t_price_percent, profit))
        if profit > 0:
            if t_price_percent < self.trigger_percent:
                logging.debug("forward======>profit percent should >= %s krw" % self.trigger_percent)
                return
            self.count_reverse += 1
            self.logger_other.info("count_forward: %s, count_reverse: %s" % (self.count_forward, self.count_reverse))
            logging.debug(
                "reverse======>find profit!!!: profit:%s,  quote amount: %s and mid amount: %s, t_price: %s" %
                (profit, hedge_quote_amount, hedge_mid_amount, t_price))

            current_time = time.time()
            if current_time - self.last_trade < 1:
                logging.debug("reverse======>Can't automate this trade, last trade " +
                              "occured %.2f seconds ago" %
                              (current_time - self.last_trade))
                return
            if not self.monitor_only:
                # bch_btc buy first, bch_krw btc_krw second, bch_btc起连接作用，所以先交易
                buy_amount_1 = round(hedge_quote_amount * (1 + self.fee_pair1), 8)
                buy_price_1 = pair1_ask_price
                logging.info("reverse=====>%s place buy order, price=%s, amount=%s" %
                             (self.pair_1, buy_price_1, buy_amount_1))
                order_id_1 = self.brokers[self.pair_1].buy_limit(amount=buy_amount_1, price=buy_price_1)

                if not order_id_1 or order_id_1 < 0:
                    logging.error("reverse======>%s place buy order failed, give up and return" % self.pair_1)
                    return

                time.sleep(config.INTERVAL_API)
                deal_amount_1, deal_avg_price_1 = self.get_deal_amount(market=self.pair_1, order_id=order_id_1)
                if deal_amount_1 < self.min_stock_1:
                    logging.error("reverse======>%s order %s deal amount %s < %s, give up and return" %
                                  (self.pair_1, order_id_1, deal_amount_1, self.min_stock_1))
                    return
                else:
                    logging.info("reverse======>%s make buy order that id=%s, price=%s, amount=%s, deal_amount=%s" %
                                 (self.pair_1, order_id_1, buy_price_1, buy_amount_1, deal_amount_1))
                if not deal_avg_price_1:
                    logging.error("reverse======>%s order %s avg price must not be empty" % (self.pair_1, order_id_1))
                    assert False
                '''bithumb限制amount小数位最多为4'''
                sell_amount_base = round(deal_amount_1 * (1 - self.fee_pair1), 4)
                # 这个地方用平均成交价来计算pair2的amount
                buy_amount_2 = round(deal_amount_1 * deal_avg_price_1, 4)

                sell_price_base = base_pair_bid_price
                buy_price_2 = pair2_ask_price

                done_base = False
                done_2 = False
                while True:
                    order_id_base = None
                    order_base = None
                    order_id_2 = None
                    order_2 = None

                    if not done_base:
                        logging.info("reverse=====>%s place sell order, price=%s, amount=%s" %
                                     (self.base_pair, sell_amount_base, sell_amount_base))
                        order_base, order_base_error = self.brokers[self.base_pair].sell_limit(
                            amount=sell_amount_base, price=sell_price_base)
                        if self.has_error(order_base, order_base_error):
                            logging.error("reverse======>%s place sell order failed: %s" % (self.base_pair,
                                                                                            order_base_error))
                        else:
                            order_id_base = order_base['order_id']
                            if not order_id_base:
                                logging.error("reverse======>%s order_id_base is None shouldn't happen"
                                              % self.base_pair)
                                assert False

                    if not done_2:
                        logging.info("reverse=====>%s place buy order, price=%s, amount=%s" %
                                     (self.pair_2, buy_price_2, buy_amount_2))
                        order_2, order_2_error = self.brokers[self.pair_2].buy_limit(
                            amount=buy_amount_2, price=buy_price_2)

                        if self.has_error(order_2, order_2_error):
                            logging.error("reverse======>%s place buy order failed: %s" % (self.pair_2, order_2_error))
                        else:
                            order_id_2 = order_2['order_id']
                            if not order_id_2:
                                logging.error("reverse======>%s order_id_2 is None shouldn't happen"
                                              % self.pair_2)
                                assert False

                    time.sleep(config.INTERVAL_API)
                    if not done_base and order_base and order_id_base and order_id_base >= 0:
                        deal_amount_base = self.get_btb_deal_amount(self.base_pair, order_id_base, order_base, 'ask')
                        diff_amount_base = round(sell_amount_base - deal_amount_base, 4)
                        logging.info("reverse======>%s make sell order that id=%s, price=%s, amount=%s, \
                                      deal_amount=%s, diff_amount=%s " %
                                     (self.base_pair, order_id_base, sell_price_base, sell_amount_base,
                                      deal_amount_base, diff_amount_base))
                        if diff_amount_base < self.min_stock_base:
                            logging.info("reverse======>%s trade complete" % self.base_pair)
                            done_base = True
                        else:
                            # 后续调整为market_sell, 减少ticker调用?
                            ticker_base = self.get_latest_ticker(self.base_pair)
                            sell_price_base = ticker_base['bid']
                            sell_amount_base = diff_amount_base

                    if not done_2 and order_2 and order_id_2 and order_id_2 >= 0:
                        deal_amount_2 = self.get_btb_deal_amount(self.pair_2, order_id_2, order_2, 'bid')
                        diff_amount_2 = round(buy_amount_2 - deal_amount_2, 4)
                        logging.info("reverse======>%s make buy order that id=%s, price=%s, amount=%s, deal_amount=%s\
                                      ,diff_amount=%s" % (self.pair_2, order_id_2, buy_price_2, buy_amount_2,
                                                          deal_amount_2, diff_amount_2))
                        if diff_amount_2 < self.min_stock_2:
                            logging.info("reverse======>%s trade complete" % self.pair_2)
                            done_2 = True
                        else:
                            ticker2 = self.get_latest_ticker(self.pair_2)
                            buy_price_2 = ticker2['ask']
                            buy_amount_2 = diff_amount_2

                    if done_base and done_2:
                        self.logging_balance = True
                        logging.info("reverse======>trade all complete at count %s" % self.count_reverse)
                        break
                    time.sleep(config.INTERVAL_API)

                self.skip = True

            self.last_trade = time.time()

    def get_btb_deal_amount(self, market, order_id, order, order_type):
        if order and 'deal_amount' in order:
            return order['deal_amount']
        else:
            # 未完成的订单才能查询到
            while True:
                resp, resp_error = self.brokers[market].get_order(order_id=order_id, order_type=order_type)
                # 两种情况需要continue
                # 1,resp 和error_msg都为空表示网络问题无response
                # 2,error_msg如果是try again, 如果是非try again表示该订单已成交所以查询不到

                # resp 可能为空，因为订单可能成交了,所以会有2个种情况break
                # 1, resp不为空 error为空，订单未成交且查询成功
                # 2, resp为空，error不为空且不是Please try again, 则订单已成交
                if not resp and not resp_error:
                    time.sleep(config.INTERVAL_RETRY)
                    continue
                if resp_error and 'message' in resp_error:
                    if self.is_needed_try_again(resp_error['message']):
                        time.sleep(config.INTERVAL_RETRY)
                        continue
                    else:
                        logging.info("%s get order %s failed: %s" % (market, order_id, resp_error))
                break
            if resp:
                while True:
                    cancel_done, error_cancel = self.brokers[market].cancel_order(order_id=order_id,
                                                                                  order_type=order_type)
                    if not cancel_done and not error_cancel:
                        # network invalid, try again
                        time.sleep(config.INTERVAL_RETRY)
                        continue
                    if error_cancel and 'message' in error_cancel:
                        if self.is_needed_try_again(error_cancel['message']):
                            time.sleep(config.INTERVAL_RETRY)
                            continue
                        else:
                            logging.info("%s cancel %s order %s failed: %s" % (market, order_type, order_id,
                                                                               error_cancel))
                    break

                if cancel_done:
                    # 大部分是这种场景, cancel未完成的部分
                    logging.info("%s cancel %s order %s success" % (market, order_type, order_id))
                    return resp['deal_amount']
                else:
                    # get_order成功，但是两次cancel失败了，当作已成功处理
                    # time.sleep(config.INTERVAL_RETRY)
                    logging.info("%s cancel %s order %s failed, maybe has filled" % (market, order_type, order_id))
                    return self.get_filled_deal_amount_c(market, order_id, order_type)
            else:
                # get_order两次失败，当作已成交处理
                # time.sleep(config.INTERVAL_RETRY)
                logging.info("%s get %s order %s failed, maybe has filled" % (market, order_type, order_id))
                return self.get_filled_deal_amount_c(market, order_id, order_type)

    def get_filled_deal_amount_c(self, market, order_id, order_type):
        """
        已成交订单的deal_amount, get_order查询不到
        这里的逻辑是只有error和order都为None，即网络错误才进行重试
        """
        while True:
            deal_amount, error_obj = self.brokers[market].get_deal_amount(order_id=order_id, order_type=order_type)
            if not error_obj and deal_amount is None:
                # 这个地方不要用not deal_amount判断，因为要确定是网络原因
                time.sleep(config.INTERVAL_RETRY)
                continue
            else:
                if error_obj and 'message' in error_obj:
                    if self.is_needed_try_again(error_obj['message']):
                        # bithumb 提示 Please try again
                        time.sleep(config.INTERVAL_RETRY)
                        continue
                    else:
                        logging.info("%s get order %s filled deal amount failed: %s" % (market, order_id, error_obj))
                break
        return deal_amount

    @classmethod
    def is_needed_try_again(cls, error_msg):
        if error_msg:
            res = error_msg.find(MESSAGE_TRY_AGAIN)
            # -1表示找不到Please try again, 就不用重试接口直接 return false
            return res != -1

        return False

    @classmethod
    def has_error(cls, resp, error_obj):
        # 无错的情况如下:
        # 1, resp error_obj都不为空
        # 2, error_obj code为'0000'

        if resp and error_obj:
            if 'message' in error_obj:
                return True
            if 'code' in error_obj:
                return error_obj['status'] != '0000'

        return True

    def update_balance(self):
        if self.monitor_only:
            return

        res_base = self.brokers[self.base_pair].get_balances_c()
        res_1 = self.brokers[self.pair_1].get_balances_c()
        res_2 = self.brokers[self.pair_2].get_balances_c()
        if not res_base or not res_1 or not res_2:
            logging.error("balance must be success, but failed")
            assert False

        bch_base = self.brokers[self.base_pair].bch_available
        krw_base = self.brokers[self.base_pair].krw_available

        bch_1 = self.brokers[self.pair_1].bch_available
        btc_1 = self.brokers[self.pair_1].btc_available

        btc_2 = self.brokers[self.pair_2].btc_available
        krw_2 = self.brokers[self.pair_2].krw_available

        btc_total = btc_1 + btc_2
        bch_total = bch_base + bch_1
        krw_total = min(krw_base, krw_2)

        if not self.origin_assets:
            self.origin_assets[self.base_pair] = {
                'bch_available': bch_base,
                'krw_available': krw_base
            }
            self.origin_assets[self.pair_1] = {
                'bch_available': bch_1,
                'btc_available': btc_1
            }

            self.origin_assets[self.pair_2] = {
                'btc_available': btc_2,
                'krw_available': krw_2
            }

            self.origin_assets['btc_total'] = btc_total
            self.origin_assets['bch_total'] = bch_total
            self.origin_assets['krw_total'] = krw_total

        current_assets = {
            self.base_pair: {
                'bch_available': bch_base,
                'krw_available': krw_base
            },
            self.pair_1: {
                'bch_available': bch_1,
                'btc_available': btc_1
            },
            self.pair_2: {
                'btc_available': btc_2,
                'krw_available': krw_2
            },
            'btc_total': btc_total,
            'bch_total': bch_total,
            'krw_total': krw_total
        }

        if self.logging_balance:
            logging.info('origin assets: ' + str(self.origin_assets))
            logging.info('current assets: ' + str(current_assets))
            self.logging_balance = False

        self.risk_protect(current_assets)

    def risk_protect(self, current_assets):
        btc_diff = abs(self.origin_assets['btc_total'] - current_assets['btc_total'])
        bch_diff = abs(self.origin_assets['bch_total'] - current_assets['bch_total'])
        if bch_diff >= self.min_amount_market or btc_diff >= self.min_amount_mid:
            self.risk_count += 1
            logging.info('risk======>risk_count: %s' % self.risk_count)
            # if self.risk_count > 25:
            #     logging.error("Stop quant bot, because risk protect")
            #     assert False
        else:
            self.risk_count = 0
