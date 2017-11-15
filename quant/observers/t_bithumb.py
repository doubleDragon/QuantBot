#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import division

import logging
import time

from quant import config
from quant.brokers import broker_factory
from .basicbot import BasicBot


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
        self.min_amount_market = kwargs['min_amount_market']
        self.min_amount_mid = kwargs['min_amount_mid']
        """单次交易的最大量和最小量"""
        self.max_trade_amount = kwargs['max_trade_amount']
        self.min_trade_amount = kwargs['min_trade_amount']

        # 赢利触发点，差价，百分比更靠谱?
        self.trigger_percent = 1.0
        self.last_trade = 0
        self.skip = False

        # just for count for chance profit
        self.count_forward = 0
        self.count_reverse = 0

        if not self.monitor_only:
            self.brokers = broker_factory.create_brokers([self.base_pair, self.pair_1, self.pair_2])

        logging.debug("T_Bithumb params: " + str(kwargs))

    def is_depths_available(self, depths):
        res = self.base_pair in depths and self.pair_1 in depths and self.pair_2 in depths
        if not res:
            return False
        # base empty
        res = 'asks' in depths[self.base_pair] and 'bids' in depths[self.base_pair]
        if not res:
            return False
        if len(depths[self.base_pair]['asks']) <= 0 or len(depths[self.base_pair]['bids']) <= 0:
            return False

        res = 'asks' in depths[self.pair_1] and 'bids' in depths[self.pair_1]
        if not res:
            return False
        if len(depths[self.pair_1]['asks']) <= 0 or len(depths[self.pair_1]['bids']) <= 0:
            return False

        res = 'asks' in depths[self.pair_2] and 'bids' in depths[self.pair_2]
        if not res:
            return False
        if len(depths[self.pair_2]['asks']) <= 0 or len(depths[self.pair_2]['bids']) <= 0:
            return False

        return True

    def tick(self, depths):
        if not self.monitor_only:
            self.update_balance()
        if not self.is_depths_available(depths):
            # logging.debug("depths is not available")
            return
        logging.info("count_forward: %s, count_reverse: %s" % (self.count_forward, self.count_reverse))
        self.skip = False
        self.forward(depths)
        self.reverse(depths)

    def forward(self, depths):
        logging.info("==============正循环, base买 合成卖==============")
        base_pair_ask_amount = depths[self.base_pair]['asks'][0]['amount']
        base_pair_ask_price = depths[self.base_pair]['asks'][0]['price']
        base_pair_ask_price_real = base_pair_ask_price * (1 + self.fee_base)

        logging.info("forward======>base_pair: %s ask_price:%s" % (self.base_pair, base_pair_ask_price))

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

        logging.info("forward======>%s bid_price: %s,  %s bid_price: %s" %
                     (self.pair_1, pair1_bid_price, self.pair_2, pair2_bid_price))
        logging.info("forward======>synthetic_bid_price: %s,   p_diff: %s" % (synthetic_bid_price, p_diff))

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
                logging.info("forward======>hedge_quote_amount is too small! %s" % hedge_quote_amount)
                return

            if hedge_mid_amount < self.min_amount_mid:
                """bitfinex限制btc_krw最小可交易amount为0.005, liqui限制单次交易btc的amount为0.0001, 所以这里取0.005"""
                logging.info("forward======>hedge_mid_amount is too small! %s" % hedge_mid_amount)
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

            logging.info("forward======>balance allow quote: %s and mid: %s, market allow quote: %s and btc: %s " %
                         (hedge_quote_amount_balance, hedge_mid_amount_balance,
                          hedge_quote_amount_market, hedge_mid_amount_market))

            if hedge_quote_amount < self.min_amount_market:
                """bitfinex限制bch_krw最小可交易的bch order size为0.001"""
                logging.info("forward======>hedge_quote_amount is too small! %s" % hedge_quote_amount)
                return

            if hedge_mid_amount < self.min_amount_mid or hedge_mid_amount > hedge_mid_amount_balance:
                """bitfinex限制btc_krw最小可交易amount为0.005, liqui限制单次交易btc的amount为0.0001, 所以这里取0.005"""
                """btc余额不足也不行"""
                logging.info("forward======>hedge_mid_amount is too small! %s" % hedge_mid_amount)
                return

        logging.info("forward======>hedge_quote_amount: %s, hedge_mid_amount:%s" %
                     (hedge_quote_amount, hedge_mid_amount))

        """
        计算的关键点在于bcc和btc的买卖amount除去手续费后是相同的，也就是进行一个循环交易后bcc和btc的总量是不变的, 变的是krw
        profit=去除交易手续费后交易hedge_quote_amount的赢利
        """
        logging.info("forward======>base_pair_ask_price_real: %s,  synthetic_bid_price_real: %s, [%s, %s]" %
                     (base_pair_ask_price_real, synthetic_bid_price_real, pair1_bid_price_real,
                      pair2_bid_price_real))
        t_price = round(synthetic_bid_price_real - base_pair_ask_price_real, self.precision)
        """差价百分比"""
        t_price_percent = round(t_price / base_pair_ask_price_real * 100, 2)
        profit = round(t_price * hedge_quote_amount, self.precision)
        logging.info(
            "forward======>t_price: %s, t_price_percent: %s, profit: %s" % (t_price, t_price_percent, profit))
        if profit > 0:
            if t_price_percent < self.trigger_percent:
                logging.warn("forward======>profit percent should >= %s krw" % self.trigger_percent)
                return
            self.count_forward += 1
            logging.info(
                "forward======>find profit!!!: profit:%s,  quote amount: %s and mid amount: %s,  t_price: %s" %
                (profit, hedge_quote_amount, hedge_mid_amount, t_price))

            current_time = time.time()
            if current_time - self.last_trade < 1:
                logging.warn("forward======>Can't automate this trade, last trade " +
                             "occured %.2f seconds ago" %
                             (current_time - self.last_trade))
                return

            if not self.monitor_only:
                sell_amount_2 = hedge_quote_amount
                sell_price_2 = pair2_bid_price

                logging.info("forward=====>%s place sell order, price=%s, amount=%s" %
                             (self.pair_2, sell_price_2, sell_amount_2))

                r_sell2 = self.new_order(market=self.pair_2, order_type='sell', amount=sell_amount_2,
                                         price=sell_price_2)

                if not r_sell2 or ('order_id' not in r_sell2):
                    logging.warn("forward======>%s place sell order failed, give up and return" % self.pair_2)
                    return

                order_id_2 = r_sell2['order_id']
                time.sleep(config.INTERVAL_API)
                deal_amount_2 = self.get_deal_amount(market=self.pair_2, order_id=order_id_2)
                if deal_amount_2 < self.min_trade_amount:
                    logging.warn("forward======>%s order %s deal amount %s < %s, give up and return" %
                                 (self.pair_2, order_id_2, deal_amount_2, self.min_trade_amount))
                    return
                logging.warn("forward======>%s order %s deal amount %s > %s, continue" %
                             (self.pair_2, order_id_2, deal_amount_2, self.min_trade_amount))

                sell_amount_1 = deal_amount_2
                sell_price_1 = pair1_bid_price

                buy_amount_base = round(deal_amount_2 * (1 + self.fee_base), 8)
                buy_price_base = base_pair_ask_price

                done_1 = False
                done_base = False
                while True:
                    order_id_1 = -1
                    order_id_base = -1

                    if not done_1:
                        logging.info("forward=====>%s place sell order, price=%s, amount=%s" %
                                     (self.pair_1, sell_price_1, sell_amount_1))
                        r_sell1 = self.new_order(market=self.pair_1, order_type='sell', amount=sell_amount_1,
                                                 price=sell_price_1)
                        if r_sell1 and ('order_id' in r_sell1):
                            order_id_1 = r_sell1['order_id']
                            if order_id_1 < 0:
                                assert False

                    if not done_base:
                        logging.info("forward=====>%s place buy order, price=%s, amount=%s" %
                                     (self.base_pair, buy_price_base, buy_amount_base))
                        r_buy_base = self.new_order(market=self.base_pair, order_type='buy', amount=buy_amount_base,
                                                    price=buy_price_base)
                        if r_buy_base and ('order_id' in r_buy_base):
                            order_id_base = r_buy_base['order_id']
                            if order_id_base < 0:
                                assert False

                    time.sleep(config.INTERVAL_API)
                    if not done_1 and order_id_1 and order_id_1 >= 0:
                        deal_amount_1 = self.get_deal_amount(self.pair_1, order_id_1)
                        logging.info("forward======>%s order %s deal amount %s, origin amount %s" %
                                     (self.pair_1, order_id_1, deal_amount_1, sell_amount_1))
                        diff_amount_1 = sell_amount_1 - deal_amount_1
                        if diff_amount_1 < self.min_trade_amount:
                            logging.info("forward======>%s trade complete" % self.pair_1)
                            done_1 = True
                        else:
                            ticker1 = self.get_latest_ticker(self.pair_1)
                            sell_price_1 = ticker1['bid']
                            sell_amount_1 = diff_amount_1

                    if not done_base and order_id_base and order_id_base >= 0:
                        deal_amount_base = self.get_deal_amount(self.base_pair, order_id_base)
                        logging.info("forward======>%s order %s deal amount %s, origin amount %s" %
                                     (self.base_pair, order_id_base, deal_amount_base, buy_amount_base))
                        diff_amount_base = buy_amount_base - deal_amount_base
                        if diff_amount_base < self.min_trade_amount:
                            logging.info("forward======>%s trade complete" % self.base_pair)
                            done_base = True
                        else:
                            ticker_base = self.get_latest_ticker(self.base_pair)
                            buy_price_base = ticker_base['ask']
                            buy_amount_base = diff_amount_base

                    if done_1 and done_base:
                        logging.info("forward======>trade all complete")
                        break

                self.skip = True

            self.last_trade = time.time()

    def reverse(self, depths):
        if self.skip and (not self.monitor_only):
            return
        logging.info("==============逆循环, base卖 合成买==============")
        base_pair_bid_amount = depths[self.base_pair]['bids'][0]['amount']
        base_pair_bid_price = depths[self.base_pair]['bids'][0]['price']
        base_pair_bid_price_real = base_pair_bid_price * (1 - self.fee_base)

        logging.info("reverse======>base_pair: %s bid_price:%s" % (self.base_pair, base_pair_bid_price))

        pair1_ask_amount = depths[self.pair_1]['asks'][0]['amount']
        pair1_ask_price = depths[self.pair_1]['asks'][0]['price']
        pair1_ask_price_real = pair1_ask_price * (1 + self.fee_pair1)

        pair2_ask_amount = depths[self.pair_2]['asks'][0]['amount']
        pair2_ask_price = depths[self.pair_2]['asks'][0]['price']
        pair2_ask_price_real = pair2_ask_price * (1 + self.fee_pair2)

        synthetic_ask_price = round(pair1_ask_price * pair2_ask_price, self.precision)
        synthetic_ask_price_real = round(pair1_ask_price_real * pair2_ask_price_real, self.precision)
        p_diff = round(base_pair_bid_price - synthetic_ask_price, self.precision)

        logging.info("reverse======>%s ask_price: %s,  %s ask_price: %s" %
                     (self.pair_1, pair1_ask_price, self.pair_2, pair2_ask_price))
        logging.info("reverse======>synthetic_ask_price: %s,   p_diff: %s" % (synthetic_ask_price, p_diff))
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
                logging.info("reverse======>hedge_quote_amount is too small! %s" % hedge_quote_amount)
                return

            if hedge_mid_amount < self.min_amount_mid:
                """lq限制最小btc的total为0.0001, bfx的bch_krw交易订单限制amount为0.005"""
                logging.info("reverse======>hedge_mid_amount is too small! %s" % hedge_mid_amount)
                return
        else:
            """余额限制base最多能卖多少个bch, pair1 最多能买多少个bch, 要带上手续费"""
            hedge_quote_amount_balance = min(self.brokers[self.base_pair].bch_available,
                                             self.brokers[self.pair_1].btc_available * pair1_ask_price_real)
            hedge_mid_amount_balance = min(self.brokers[self.pair_2].krw_available * pair2_ask_price_real,
                                           self.brokers[self.pair_1].btc_available)

            hedge_quote_amount = min(hedge_quote_amount_market, hedge_quote_amount_balance, self.min_trade_amount)
            hedge_mid_amount = hedge_quote_amount * pair1_ask_price

            logging.info("reverse======>balance allow bch: %s and btc: %s, market allow bch: %s and btc: %s " %
                         (hedge_quote_amount_balance, hedge_mid_amount_balance,
                          hedge_quote_amount_market, hedge_mid_amount_market))

            if hedge_quote_amount < self.min_amount_market:
                """bfx限制bch最小订单数量为0.001"""
                logging.info("reverse======>hedge_quote_amount is too small! %s" % hedge_quote_amount)
                return

            if hedge_mid_amount < self.min_amount_mid or hedge_mid_amount > hedge_mid_amount_balance:
                """lq限制最小btc的total为0.0001, bfx的bch_btc交易订单限制amount为0.005"""
                """并且不能大于余额的限制"""
                logging.info("reverse======>hedge_mid_amount is too small! %s" % hedge_mid_amount)
                return

        logging.info("reverse======>hedge_quote_amount: %s, hedge_mid_amount:%s" %
                     (hedge_quote_amount, hedge_mid_amount))

        """
        计算的关键点在于bcc和btc的买卖amount除去手续费后是相同的，也就是进行一个循环交易后bcc和btc的总量是不变的, 变的是krw
        profit=去除交易手续费后交易hedge_quote_amount的赢利
        """
        logging.info("reverse======>base_pair_bid_price_real: %s,  synthetic_ask_price_real: %s, [%s, %s]" %
                     (base_pair_bid_price_real, synthetic_ask_price_real, pair1_ask_price_real,
                      pair2_ask_price_real))
        t_price = round(base_pair_bid_price_real - synthetic_ask_price_real, self.precision)
        t_price_percent = round(t_price / synthetic_ask_price_real * 100, 2)
        profit = round(t_price * hedge_quote_amount, self.precision)
        logging.info(
            "reverse======>t_price: %s, t_price_percent: %s, profit: %s" % (t_price, t_price_percent, profit))
        if profit > 0:
            if t_price_percent < self.trigger_percent:
                logging.warn("forward======>profit percent should >= %s krw" % self.trigger_percent)
                return
            self.count_reverse += 1
            logging.info(
                "reverse======>find profit!!!: profit:%s,  quote amount: %s and mid amount: %s, t_price: %s" %
                (profit, hedge_quote_amount, hedge_mid_amount, t_price))

            current_time = time.time()
            if current_time - self.last_trade < 1:
                logging.warn("reverse======>Can't automate this trade, last trade " +
                             "occured %.2f seconds ago" %
                             (current_time - self.last_trade))
                return
            if not self.monitor_only:
                # sell first, buy second base on deal_amount
                sell_amount = hedge_quote_amount
                sell_price = base_pair_bid_price
                logging.info("reverse=====>%s place sell order, price=%s, amount=%s" %
                             (self.base_pair, sell_price, sell_amount))
                r_sell = self.new_order(market=self.base_pair, order_type='sell', amount=sell_amount,
                                        price=sell_price)

                if not r_sell or ('order_id' not in r_sell):
                    # bt1 place order failed
                    logging.warn("reverse======>%s place sell order failed, give up and return" % self.base_pair)
                    return

                order_id_base = r_sell['order_id']
                time.sleep(config.INTERVAL_API)
                deal_amount_base = self.get_deal_amount(market=self.base_pair, order_id=order_id_base)
                if deal_amount_base < self.min_trade_amount:
                    logging.warn("reverse======>%s order %s deal amount %s < %s, give up and return" %
                                 (self.base_pair, order_id_base, deal_amount_base, self.min_trade_amount))
                    return

                logging.warn("reverse======>%s order %s deal amount %s > %s, continue" %
                             (self.base_pair, order_id_base, deal_amount_base, self.min_trade_amount))

                # bt1 bt2分别买进buy_amount
                buy_amount_1 = deal_amount_base * (1 + self.fee_pair1)
                buy_amount_2 = deal_amount_base * (1 + self.fee_pair2)

                buy_price_1 = pair1_ask_price
                buy_price_2 = pair2_ask_price

                # bt1 bt2 先一起下单，保证都下单成功
                done_1 = False
                done_2 = False
                while True:
                    order_id_1 = None
                    order_id_2 = None

                    if not done_1:
                        logging.info("reverse=====>%s place buy order, price=%s, amount=%s" %
                                     (self.pair_1, buy_price_1, buy_amount_1))
                        r_buy1 = self.new_order(market=self.pair_1, order_type='buy', amount=buy_amount_1,
                                                price=buy_price_1)
                        if r_buy1 and ('order_id' in r_buy1):
                            order_id_1 = r_buy1['order_id']
                            if order_id_1 < 0:
                                assert False

                    if not done_2:
                        logging.info("reverse=====>%s place buy order, price=%s, amount=%s" %
                                     (self.pair_2, buy_price_2, buy_amount_2))
                        r_buy2 = self.new_order(market=self.pair_2, order_type='buy', amount=buy_amount_2,
                                                price=buy_price_2)
                        if r_buy2 and ('order_id' in r_buy2):
                            order_id_2 = r_buy2['order_id']
                            if order_id_2 < 0:
                                assert False

                    time.sleep(config.INTERVAL_API)

                    if not done_1 and order_id_1 and order_id_1 >= 0:
                        deal_amount_1 = self.get_deal_amount(self.pair_1, order_id_1)
                        logging.info("reverse======>%s order %s deal amount %s, origin amount %s" %
                                     (self.pair_1, order_id_1, deal_amount_1, buy_amount_1))
                        diff_amount_1 = buy_amount_1 - deal_amount_1
                        if diff_amount_1 < self.min_trade_amount:
                            logging.info("reverse======>%s trade complete" % self.pair_1)
                            done_1 = True
                        else:
                            ticker1 = self.get_latest_ticker(self.pair_1)
                            buy_price_1 = ticker1['ask']
                            buy_amount_1 = diff_amount_1

                    if not done_2 and order_id_2 and order_id_2 >= 0:
                        deal_amount_2 = self.get_deal_amount(self.pair_2, order_id_2)
                        logging.info("reverse======>%s order %s deal amount %s, origin amount %s" %
                                     (self.pair_2, order_id_2, deal_amount_2, buy_amount_2))
                        diff_amount_2 = buy_amount_2 - deal_amount_2
                        if diff_amount_2 < self.min_trade_amount:
                            logging.info("reverse======>%s trade complete" % self.pair_2)
                            done_2 = True
                        else:
                            ticker2 = self.get_latest_ticker(self.pair_2)
                            buy_price_2 = ticker2['ask']
                            buy_amount_2 = diff_amount_2

                    if done_1 and done_2:
                        logging.info("reverse======>trade all complete")
                        break

                self.skip = True

            self.last_trade = time.time()

    def update_balance(self):
        self.brokers[self.base_pair].get_balances()
        self.brokers[self.pair_1].get_balances()
        self.brokers[self.pair_2].get_balances()
