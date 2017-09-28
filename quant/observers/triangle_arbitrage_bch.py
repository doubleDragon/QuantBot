#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import logging

import time

from quant import config
from quant.brokers import broker_factory
from .basicbot import BasicBot


class TriangleArbitrage(BasicBot):
    """
    python -m quant.cli -mBitfinex_BCH_USD,Liqui_BCC_BTC,Bitfinex_BTC_USD t-watch-triangle-arbitrage-bch -d
    每个交易所的min_price和min_stocks不一致，限定条件需要查询文档
    限制条件:
        1, 交易所的min_price和min_stocks限制, 每个交易所可能不一样，需要动态的改
        2, 余额限制，即当前能买卖的币数量合理
    pair_1可选参数:
        1, Kkex_BCC_BTC
        2, Hitbtc_BCC_BTC
        3, Cex_BCC_BTC
    待调整参数:
        profit>10 ? 大于多少合适
    """

    def __init__(self, monitor_only=False):
        super(TriangleArbitrage, self).__init__()

        self.base_pair = 'Bitfinex_BCH_USD'
        self.pair_1 = 'Liqui_BCC_BTC'
        self.pair_2 = 'Bitfinex_BTC_USD'
        self.monitor_only = monitor_only

        self.brokers = broker_factory.create_brokers([self.base_pair, self.pair_1, self.pair_2])

        self.last_trade = 0
        self.min_amount_bch = 0.001
        self.min_amount_btc = 0.005
        # 保留的小树位精度
        self.precision = 2
        # 赢利触发点
        self.profit_trigger = 1.5
        self.skip = False

    def is_depths_available(self, depths):
        return self.base_pair in depths and self.pair_1 in depths and self.pair_2 in depths

    def tick(self, depths):
        self.update_balance()
        if not self.is_depths_available(depths):
            # logging.debug("depths is not available")
            return
        self.skip = False
        self.forward(depths)
        self.reverse(depths)

    def forward(self, depths):
        logging.info("==============正循环, base买 合成卖==============")
        base_pair_ask_amount = depths[self.base_pair]['asks'][0]['amount']
        base_pair_ask_price = depths[self.base_pair]['asks'][0]['price']

        logging.info("forward======>base_pair: %s ask_price:%s" % (self.base_pair, base_pair_ask_price))

        pair1_bid_amount = depths[self.pair_1]['bids'][0]['amount']
        pair1_bid_price = depths[self.pair_1]['bids'][0]['price']

        pair2_bid_amount = depths[self.pair_2]['bids'][0]['amount']
        pair2_bid_price = depths[self.pair_2]['bids'][0]['price']

        """合成后的价格对标bch_usd, 以目前的bfx的价格设置小数位保留2位比较合适"""
        synthetic_bid_price = round(pair1_bid_price * pair2_bid_price, self.precision)
        """价差， diff=卖－买, 对标的是usd， 小数位保留2"""
        p_diff = synthetic_bid_price - base_pair_ask_price

        logging.info("forward======>%s bid_price: %s,  %s bid_price: %s" %
                     (self.pair_1, pair1_bid_price, self.pair_2, pair2_bid_price))
        logging.info("forward======>synthetic_bid_price: %s,   p_diff: %s" % (synthetic_bid_price, p_diff))

        if pair1_bid_price == 0:
            return

        pair_2to1_bch_amount = round(pair2_bid_amount / pair1_bid_price, 8)

        """市场限制base最多能买多少个bch, pair1 最多能卖多少个bch, 并且在上线和下线范围内[5, 0.05]"""
        max_trade_amount = config.bch_max_tx_volume
        min_trade_amount = config.bch_min_tx_volume
        hedge_bch_amount_market = min(base_pair_ask_amount, pair1_bid_amount)
        hedge_bch_amount_market = min(hedge_bch_amount_market, pair_2to1_bch_amount)
        hedge_bch_amount_market = min(max_trade_amount, hedge_bch_amount_market)
        hedge_btc_amount_market = round(hedge_bch_amount_market * pair1_bid_price, 8)

        """余额限制base最多能买多少个bch, pair1 最多能卖多少个bch"""
        hedge_bch_amount_balance = round(min(self.brokers[self.pair_1].bch_available,
                                             self.brokers[self.base_pair].usd_available * base_pair_ask_price), 8)
        hedge_btc_amount_balance = round(min(self.brokers[self.pair_2].btc_available,
                                             self.brokers[self.pair_1].bch_available * pair1_bid_price), 8)
        """取市场和余额共同限制的amount"""
        hedge_bch_amount = min(hedge_bch_amount_market, hedge_bch_amount_balance, min_trade_amount)
        hedge_btc_amount = hedge_bch_amount * pair1_bid_price

        logging.info("forward======>balance allow bch: %s and btc: %s, market allow bch: %s and btc: %s " %
                     (hedge_bch_amount_balance, hedge_btc_amount_balance,
                      hedge_bch_amount_market, hedge_btc_amount_market))

        if hedge_bch_amount < self.min_amount_bch:
            """bitfinex限制bch_usd最小可交易的bch order size为0.001"""
            logging.info("forward======>hedge_bch_amount is too small! %s" % hedge_bch_amount)
            return

        if hedge_btc_amount < self.min_amount_btc or hedge_btc_amount > hedge_btc_amount_balance:
            """bitfinex限制btc_usd最小可交易amount为0.005, liqui限制单次交易btc的amount为0.0001, 所以这里取0.005"""
            """btc余额不足也不行"""
            logging.info("forward======>hedge_btc_amount is too small! %s" % hedge_btc_amount)
            return

        profit = p_diff * hedge_bch_amount
        if profit > 0:
            logging.info("forward======>find profit!!!: profit:%s,  bch amount: %s and btc amount: %s" %
                         (profit, hedge_bch_amount, hedge_btc_amount))
            if profit < self.profit_trigger:
                logging.warn("forward profit should >= %s usd" % self.profit_trigger)
                return

            current_time = time.time()
            if current_time - self.last_trade < 5:
                logging.warn("forward======>Can't automate this trade, last trade " +
                             "occured %.2f seconds ago" %
                             (current_time - self.last_trade))
                return

            if not self.monitor_only:
                logging.info("forward======>Ready to trade")
                self.new_order(market=self.base_pair, order_type='buy', amount=hedge_bch_amount,
                               price=base_pair_ask_price)
                self.new_order(market=self.pair_1, order_type='sell', amount=hedge_bch_amount, price=pair1_bid_price)
                self.new_order(market=self.pair_2, order_type='sell', amount=hedge_bch_amount, price=pair2_bid_price)
                self.skip = True

            self.last_trade = time.time()

    def reverse(self, depths):
        if self.skip and (not self.monitor_only):
            return
        logging.info("==============逆循环, base卖 合成买==============")
        base_pair_bid_amount = depths[self.base_pair]['bids'][0]['amount']
        base_pair_bid_price = depths[self.base_pair]['bids'][0]['price']

        logging.info("reverse======>base_pair: %s bid_price:%s" % (self.base_pair, base_pair_bid_price))

        pair1_ask_amount = depths[self.pair_1]['asks'][0]['amount']
        pair1_ask_price = depths[self.pair_1]['asks'][0]['price']

        pair2_ask_amount = depths[self.pair_2]['asks'][0]['amount']
        pair2_ask_price = depths[self.pair_2]['asks'][0]['price']

        synthetic_ask_price = round(pair1_ask_price * pair2_ask_price, self.precision)
        p_diff = base_pair_bid_price - synthetic_ask_price

        logging.info("reverse======>%s ask_price: %s,  %s ask_price: %s" %
                     (self.pair_1, pair1_ask_price, self.pair_2, pair2_ask_price))
        logging.info("reverse======>synthetic_ask_price: %s,   p_diff: %s" % (synthetic_ask_price, p_diff))
        if pair1_ask_price == 0 or pair2_ask_price == 0:
            return

        pair_2to1_bch_amount = round(pair2_ask_amount / pair1_ask_price, 8)

        """市场限制base最多能卖多少个bch, pair1 最多能买多少个bch, 并且在上线和下线范围内[5, 0.05]"""
        max_trade_amount = config.bch_max_tx_volume
        min_trade_amount = config.bch_min_tx_volume
        hedge_bch_amount_market = min(base_pair_bid_amount, pair1_ask_amount)
        hedge_bch_amount_market = min(hedge_bch_amount_market, pair_2to1_bch_amount)
        hedge_bch_amount_market = min(max_trade_amount, hedge_bch_amount_market)
        hedge_btc_amount_market = round(hedge_bch_amount_market * pair1_ask_price, 8)

        """余额限制base最多能卖多少个bch, pair1 最多能买多少个bch"""
        hedge_bch_amount_balance = min(self.brokers[self.base_pair].bch_available,
                                       self.brokers[self.pair_1].btc_available * pair1_ask_price)
        hedge_btc_amount_balance = min(self.brokers[self.pair_2].usd_available * pair2_ask_price,
                                       self.brokers[self.pair_1].btc_available)

        hedge_bch_amount = min(hedge_bch_amount_market, hedge_bch_amount_balance, min_trade_amount)
        hedge_btc_amount = hedge_bch_amount * pair1_ask_price

        logging.info("reverse======>balance allow bch: %s and btc: %s, market allow bch: %s and btc: %s " %
                     (hedge_bch_amount_balance, hedge_btc_amount_balance,
                      hedge_bch_amount_market, hedge_btc_amount_market))

        if hedge_bch_amount < self.min_amount_bch:
            """bfx限制bch最小订单数量为0.001"""
            logging.info("reverse======>hedge_bch_amount is too small! %s" % hedge_bch_amount)
            return

        if hedge_btc_amount < self.min_amount_btc or hedge_btc_amount > hedge_btc_amount_balance:
            """lq限制最小btc的total为0.0001, bfx的bch_usd交易订单限制amount为0.005"""
            """并且不能大于余额的限制"""
            logging.info("reverse======>hedge_btc_amount is too small! %s" % hedge_btc_amount)
            return

        profit = round(p_diff * hedge_bch_amount, self.precision)
        logging.info('profit=%s' % profit)
        if profit > 0:
            logging.info("reverse======>find profit!!!: profit:%s,  bch amount: %s and btc amount: %s" %
                         (profit, hedge_bch_amount, hedge_btc_amount))
            if profit < self.profit_trigger:
                logging.warn("reverse======>profit should >= %s usd" % self.profit_trigger)
                return

            current_time = time.time()
            if current_time - self.last_trade < 10:
                logging.warn("reverse======>Can't automate this trade, last trade " +
                             "occured %.2f seconds ago" %
                             (current_time - self.last_trade))
                return
            if not self.monitor_only:
                logging.info("reverse======>Ready to trade")
                self.new_order(market=self.base_pair, order_type='sell', amount=hedge_bch_amount,
                               price=base_pair_bid_price)
                self.new_order(market=self.pair_1, order_type='buy', amount=hedge_bch_amount, price=pair1_ask_price)
                self.new_order(market=self.pair_2, order_type='buy', amount=hedge_bch_amount, price=pair2_ask_price)
                self.skip = True

            self.last_trade = time.time()

    def update_balance(self):
        super(TriangleArbitrage, self).update_balance()
        for name in self.brokers:
            broker = self.brokers[name]
            logging.info("%s btc balance: %s" % (broker.name, broker.btc_available))
            logging.info("%s bch balance: %s" % (broker.name, broker.bch_available))
