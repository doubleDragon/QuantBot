#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import division

import logging
import time

from quant.brokers import broker_factory
from .basicbot import BasicBot


class T_Lq(BasicBot):
    """
    bch:
    python -m quant.cli -mBitfinex_BCH_USD,Liqui_BCC_BTC,Bitfinex_BTC_USD -o=T_Lq_BCH -f=liqui_bch -v

    目前的限制:
    """

    def __init__(self, base_pair, pair_1, pair_2, **kwargs):
        super(T_Lq, self).__init__()
        self.base_pair = base_pair
        self.pair_1 = pair_1
        self.pair_2 = pair_2
        self.monitor_only = kwargs['monitor_only']
        """小数位进度，usd定价为2, btc定价为8"""
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
        self.profit_trigger = 1.5
        self.last_trade = 0
        self.skip = False

        # just for count for chance profit
        self.count_forward = 0
        self.count_reverse = 0
        self.trigger_diff_percent = 0.5

        if not self.monitor_only:
            self.brokers = broker_factory.create_brokers([self.base_pair, self.pair_1, self.pair_2])

        logging.debug("T_Lq params: " + str(kwargs))

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
                """bitfinex限制bch_usd最小可交易的bch order size为0.001"""
                logging.info("forward======>hedge_quote_amount is too small! %s" % hedge_quote_amount)
                return

            if hedge_mid_amount < self.min_amount_mid:
                """bitfinex限制btc_usd最小可交易amount为0.005, liqui限制单次交易btc的amount为0.0001, 所以这里取0.005"""
                logging.info("forward======>hedge_mid_amount is too small! %s" % hedge_mid_amount)
                return
        else:
            """余额限制base最多能买多少个bch, pair1 最多能卖多少个bch, 要带上手续费"""
            hedge_quote_amount_balance = round(min(self.brokers[self.pair_1].bch_available,
                                                   self.brokers[
                                                       self.base_pair].usd_available / base_pair_ask_price_real),
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
                """bitfinex限制bch_usd最小可交易的bch order size为0.001"""
                logging.info("forward======>hedge_quote_amount is too small! %s" % hedge_quote_amount)
                return

            if hedge_mid_amount < self.min_amount_mid or hedge_mid_amount > hedge_mid_amount_balance:
                """bitfinex限制btc_usd最小可交易amount为0.005, liqui限制单次交易btc的amount为0.0001, 所以这里取0.005"""
                """btc余额不足也不行"""
                logging.info("forward======>hedge_mid_amount is too small! %s" % hedge_mid_amount)
                return

        logging.info("forward======>hedge_quote_amount: %s, hedge_mid_amount:%s" %
                     (hedge_quote_amount, hedge_mid_amount))

        """
        计算的关键点在于bcc和btc的买卖amount除去手续费后是相同的，也就是进行一个循环交易后bcc和btc的总量是不变的, 变的是usd
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
            if t_price_percent < self.trigger_diff_percent:
                logging.warn("forward======>profit percent should >= %s usd" % self.trigger_diff_percent)
                return
            self.count_forward += 1
            logging.info(
                "forward======>find profit!!!: profit:%s,  quote amount: %s and mid amount: %s,  t_price: %s" %
                (profit, hedge_quote_amount, hedge_mid_amount, t_price))
            # if profit < self.profit_trigger:
            #     logging.warn("forward======>profit should >= %s usd" % self.profit_trigger)
            #     return

            current_time = time.time()
            if current_time - self.last_trade < 1:
                logging.warn("forward======>Can't automate this trade, last trade " +
                             "occured %.2f seconds ago" %
                             (current_time - self.last_trade))
                return

            # if not self.monitor_only:
            # amount_base = hedge_quote_amount * (1 + self.fee_base)
            # amount_pair2 = hedge_quote_amount * pair1_bid_price * (1 - self.fee_pair1)
            # self.new_order(market=self.base_pair, order_type='buy', amount=amount_base,
            #                price=base_pair_ask_price)
            # self.new_order(market=self.pair_1, order_type='sell',
            #                amount=hedge_quote_amount, price=pair1_bid_price)
            # self.new_order(market=self.pair_2, order_type='sell', amount=amount_pair2,
            #                price=pair2_bid_price)
            # self.skip = True

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
                """lq限制最小btc的total为0.0001, bfx的bch_usd交易订单限制amount为0.005"""
                logging.info("reverse======>hedge_mid_amount is too small! %s" % hedge_mid_amount)
                return
        else:
            """余额限制base最多能卖多少个bch, pair1 最多能买多少个bch, 要带上手续费"""
            hedge_quote_amount_balance = min(self.brokers[self.base_pair].bch_available,
                                             self.brokers[self.pair_1].btc_available * pair1_ask_price_real)
            hedge_mid_amount_balance = min(self.brokers[self.pair_2].usd_available * pair2_ask_price_real,
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
                """lq限制最小btc的total为0.0001, bfx的bch_usd交易订单限制amount为0.005"""
                """并且不能大于余额的限制"""
                logging.info("reverse======>hedge_mid_amount is too small! %s" % hedge_mid_amount)
                return

        logging.info("reverse======>hedge_quote_amount: %s, hedge_mid_amount:%s" %
                     (hedge_quote_amount, hedge_mid_amount))

        """
        计算的关键点在于bcc和btc的买卖amount除去手续费后是相同的，也就是进行一个循环交易后bcc和btc的总量是不变的, 变的是usd
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
            if t_price_percent < self.trigger_diff_percent:
                logging.warn("forward======>profit percent should >= %s usd" % self.trigger_diff_percent)
                return
            self.count_reverse += 1
            logging.info(
                "reverse======>find profit!!!: profit:%s,  quote amount: %s and mid amount: %s, t_price: %s" %
                (profit, hedge_quote_amount, hedge_mid_amount, t_price))
            # if profit < self.profit_trigger:
            #     logging.warn("reverse======>profit should >= %s usd" % self.profit_trigger)
            #     return

            current_time = time.time()
            if current_time - self.last_trade < 1:
                logging.warn("reverse======>Can't automate this trade, last trade " +
                             "occured %.2f seconds ago" %
                             (current_time - self.last_trade))
                return
            # if not self.monitor_only:
            # amount_pair1 = hedge_quote_amount * (1 + self.fee_pair1)
            # amount_pair2 = hedge_quote_amount * pair1_ask_price * (1 + self.fee_pair2) * (1 + self.fee_pair1)
            # self.new_order(market=self.base_pair, order_type='sell', amount=hedge_quote_amount,
            #                price=base_pair_bid_price)
            # self.new_order(market=self.pair_1, order_type='buy', amount=amount_pair1, price=pair1_ask_price)
            # self.new_order(market=self.pair_2, order_type='buy', amount=amount_pair2, price=pair2_ask_price)
            # self.skip = True

            self.last_trade = time.time()

            # def update_balance(self):
            #     super(TriangleArbitrage, self).update_balance()
            #     for name in self.brokers:
            #         broker = self.brokers[name]
            #         logging.info("%s btc balance: %s" % (broker.name, broker.btc_available))
            #         logging.info("%s bch balance: %s" % (broker.name, broker.bch_available))
