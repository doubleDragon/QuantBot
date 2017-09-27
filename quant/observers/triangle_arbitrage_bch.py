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

        self.update_balance()

    def is_depths_available(self, depths):
        return self.base_pair in depths and self.pair_1 in depths and self.pair_2 in depths

    def tick(self, depths):
        if not self.is_depths_available(depths):
            # logging.debug("depths is not available")
            return
        self.forward(depths)
        self.reverse(depths)

    def forward(self, depths):
        logging.info("==============正循环, base买 合成卖==============")
        base_pair_ask_amount = depths[self.base_pair]['asks'][0]['amount']
        base_pair_ask_price = depths[self.base_pair]['asks'][0]['price']

        logging.info("base_pair: %s ask_price:%s" % (self.base_pair, base_pair_ask_price))

        pair1_bid_amount = depths[self.pair_1]['bids'][0]['amount']
        pair1_bid_price = depths[self.pair_1]['bids'][0]['price']

        pair2_bid_amount = depths[self.pair_2]['bids'][0]['amount']
        pair2_bid_price = depths[self.pair_2]['bids'][0]['price']

        logging.info(
            "%s bid_price: %s,  %s bid_price: %s" % (self.pair_1, pair1_bid_price, self.pair_2, pair2_bid_price))

        if pair1_bid_price == 0:
            return

        pair_2to1_bch_amount = pair2_bid_amount / pair1_bid_price

        max_trade_amount = config.bch_max_tx_volume
        hedge_bch_amount = min(base_pair_ask_amount, pair1_bid_amount)
        hedge_bch_amount = min(hedge_bch_amount, pair_2to1_bch_amount)
        hedge_bch_amount = min(max_trade_amount, hedge_bch_amount)

        if hedge_bch_amount < self.min_amount_bch:
            """bitfinex限制bch_usd最小可交易的bch order size为0.001"""
            logging.info('hedge_bch_amount is too small! %s' % hedge_bch_amount)
            return

        hedge_btc_amount = hedge_bch_amount * pair1_bid_price
        if hedge_btc_amount < self.min_amount_btc:
            """bitfinex限制btc_usd最小可交易amount为0.005, liqui限制单次交易btc的amount为0.0001, 所以这里取0.005"""
            logging.info('hedge_btc_amount is too small! %s' % hedge_btc_amount)
            return

        """合成后的价格对标bch_usd, 以目前的bfx的价格设置小数位保留2位比较合适"""
        synthetic_bid_price = round(pair1_bid_price * pair2_bid_price, self.precision)

        t_price = round(base_pair_ask_price * config.TFEE * config.Diff, self.precision)
        logging.info("synthetic_bid_price: %s t_price:%s" % (synthetic_bid_price, t_price))

        """bch_usd买，合成价格卖, 所以p_diff为合成价-base价"""
        p_diff = synthetic_bid_price - t_price
        profit = p_diff * hedge_bch_amount
        logging.info('profit=%s' % profit)
        if profit > 0:
            logging.info("find t!!!: p_diff:%s synthetic_bid_price: %s  base_pair_ask_price: %s t_price: %s" % (
                p_diff,
                synthetic_bid_price,
                base_pair_ask_price,
                t_price))

            logging.info(
                'r--buy %s BCH @%s, sell BTC @synthetic: %s' % (self.base_pair, hedge_bch_amount, hedge_btc_amount))
            if profit < 10:
                logging.warn('profit should >= 10 CNY')
                return

            current_time = time.time()
            if current_time - self.last_trade < 5:
                logging.warn("Can't automate this trade, last trade " +
                             "occured %.2f seconds ago" %
                             (current_time - self.last_trade))
                return

            if not self.monitor_only:
                self.brokers[self.base_pair].buy_limit(hedge_bch_amount, base_pair_ask_price)
                self.brokers[self.pair_1].sell_limit(hedge_bch_amount, pair1_bid_price)
                self.brokers[self.pair_2].sell_limit(hedge_btc_amount, pair2_bid_price)

            self.last_trade = time.time()

    def reverse(self, depths):
        logging.info("==============逆循环, base卖 合成买==============")
        base_pair_bid_amount = depths[self.base_pair]['bids'][0]['amount']
        base_pair_bid_price = depths[self.base_pair]['bids'][0]['price']

        logging.info("base_pair: %s bid_price:%s" % (self.base_pair, base_pair_bid_price))

        pair1_ask_amount = depths[self.pair_1]['asks'][0]['amount']
        pair1_ask_price = depths[self.pair_1]['asks'][0]['price']

        pair2_ask_amount = depths[self.pair_2]['asks'][0]['amount']
        pair2_ask_price = depths[self.pair_2]['asks'][0]['price']

        logging.info(
            "%s ask_price: %s,  %s ask_price: %s" % (self.pair_1, pair1_ask_price, self.pair_2, pair2_ask_price))
        if pair1_ask_price == 0 or pair2_ask_price == 0:
            return

        pair_2to1_bch_amount = pair2_ask_amount / pair1_ask_price
        # print(pair2_bid_amount, pair1_bid_price, pair_2to1_bch_amount)

        max_trade_amount = config.bch_max_tx_volume
        hedge_bch_amount = min(base_pair_bid_amount, pair1_ask_amount)
        hedge_bch_amount = min(hedge_bch_amount, pair_2to1_bch_amount)
        hedge_bch_amount = min(max_trade_amount, hedge_bch_amount)

        if hedge_bch_amount < self.min_amount_bch:
            """bfx限制bch最小订单数量为0.001"""
            logging.info('hedge_bch_amount is too small! %s' % hedge_bch_amount)
            return

        hedge_btc_amount = hedge_bch_amount * pair1_ask_price
        if hedge_btc_amount < self.min_amount_btc:
            """lq限制最小btc的total为0.0001, bfx的bch_usd交易订单限制amount为0.005"""
            logging.info('hedge_btc_amount is too small! %s' % hedge_btc_amount)
            return

        synthetic_ask_price = round(pair1_ask_price * pair2_ask_price, self.precision)

        t_price = round(base_pair_bid_price * config.TFEE * config.Diff, self.precision)
        logging.info("synthetic_ask_price: %s t_price:%s" % (synthetic_ask_price, t_price))

        """bch_usd卖，合成价格买, 所以p_diff=base价-合成价"""
        p_diff = t_price - synthetic_ask_price

        profit = round(p_diff * hedge_bch_amount, self.precision)
        logging.info('profit=%s' % profit)

        if profit > 0:
            logging.info("find t!!!: p_diff:%s synthetic_ask_price: %s  base_pair_bid_price: %s t_price: %s" % (
                p_diff,
                synthetic_ask_price,
                base_pair_bid_price,
                t_price))

            logging.info(
                'r--sell %s BCH @%s, buy @synthetic: %s' % (self.base_pair, hedge_bch_amount, hedge_btc_amount))

            if profit < 10:
                logging.warn('profit should >= 10 CNY')
                return

            current_time = time.time()
            if current_time - self.last_trade < 10:
                logging.warn("Can't automate this trade, last trade " +
                             "occured %.2f seconds ago" %
                             (current_time - self.last_trade))
                return
            if not self.monitor_only:
                self.brokers[self.base_pair].sell_limit(hedge_bch_amount, base_pair_bid_price)
                self.brokers[self.pair_2].buy_limit(hedge_btc_amount, pair2_ask_price)
                self.brokers[self.pair_1].buy_limit(hedge_bch_amount, pair1_ask_price)

            self.last_trade = time.time()

    def update_balance(self):
        super(TriangleArbitrage, self).update_balance()
        for name in self.brokers:
            broker = self.brokers[name]
            logging.info("%s btc balance: %s" % (broker.name, broker.btc_available))
            logging.info("%s bch balance: %s" % (broker.name, broker.bch_available))
