#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import division
import logging

from .basicbot import BasicBot
from quant.brokers import broker_factory


class Arbitrage(BasicBot):
    """
    btc和bt1 bt2的合成与分解套利
    兑换比例1btc=1bt1+1bt2
    python -m quant.cli -mBitfinex_BTC_USD,Bitfinex_BT1_USD,Bitfinex_BT2_USD t-watch-bfx-btc -v
    """

    def __init__(self, monitor_only=False):
        super(Arbitrage, self).__init__()
        self.base_pair = "Bitfinex_BTC_USD"
        self.pair_1 = "Bitfinex_BT1_USD"
        self.pair_2 = "Bitfinex_BT2_USD"

        self.monitor_only = monitor_only
        self.precision = 2

        self.fee_base = 0.002
        self.fee_pair1 = 0.002
        self.fee_pair2 = 0.002
        """交易所限制的最小交易量，由交易所和币种共同决定"""
        self.min_amount_market = 0.005
        """单次交易的最大量和最小量"""
        self.max_trade_amount = 1
        self.min_trade_amount = 0.005

        # 赢利触发点，差价，百分比更靠谱?
        self.profit_trigger = 1.5
        self.last_trade = 0
        self.skip = False
        self.brokers = broker_factory.create_brokers([self.base_pair, self.pair_1, self.pair_2])

        # just for count for chance profit
        self.count_forward = 0
        self.count_reverse = 0
        self.trigger_diff_percent = 1.0

    def is_depths_available(self, depths):
        return self.base_pair in depths and self.pair_1 in depths and self.pair_2 in depths

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

        synthetic_bid_price = round(pair1_bid_price + pair2_bid_price, self.precision)
        synthetic_bid_price_real = round(pair1_bid_price_real + pair2_bid_price_real, self.precision)

        """价差， diff=卖－买"""
        p_diff = round(synthetic_bid_price - base_pair_ask_price, self.precision)
        logging.info("forward======>%s bid_price: %s,  %s bid_price: %s" %
                     (self.pair_1, pair1_bid_price, self.pair_2, pair2_bid_price))
        logging.info("forward======>synthetic_bid_price: %s,   p_diff: %s" % (synthetic_bid_price, p_diff))

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

        synthetic_ask_price = round(pair1_ask_price + pair2_ask_price, self.precision)
        synthetic_ask_price_real = round(pair1_ask_price_real + pair2_ask_price_real, self.precision)
        p_diff = round(base_pair_bid_price - synthetic_ask_price, self.precision)

        logging.info("reverse======>%s ask_price: %s,  %s ask_price: %s" %
                     (self.pair_1, pair1_ask_price, self.pair_2, pair2_ask_price))
        logging.info("reverse======>synthetic_ask_price: %s,   p_diff: %s" % (synthetic_ask_price, p_diff))
