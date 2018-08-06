#!/usr/bin/env python
# -*- coding: UTF-8 -*-


"""
./venv/bin/python -m quant.cli -mBitfinex_ETH_BTC,Binance_ETH_BTC,Bittrex_ETH_BTC,Gate_ETH_BTC -oC_Diff_ETH -f=mc_diff_eth -v
./venv/bin/python -m quant.cli -mBitfinex_ETH_BTC,Binance_ETH_BTC -oC_Diff_ETH -f=c_diff_eth -v
"""
import logging

from quant.observers.basicbot import BasicBot


class C_Diff_ETH(BasicBot):

    def __init__(self):
        super(C_Diff_ETH, self).__init__()
        self.market_bfx = "Bitfinex_ETH_BTC"
        self.market_bn = "Binance_ETH_BTC"
        self.profit_count = 0
        self.profit_total = 0
        self.percent_total = 0
        # self.market_brx = "Bittrex_ETH_BTC"
        # self.market_gate = "Gate_ETH_BTC"

        logging.info('C_Diff_ETH Setup complete')

    def is_depths_available(self, depths):
        if not depths:
            return False
        res = self.market_bfx in depths and self.market_bn in depths
        if not res:
            return False

        if not depths[self.market_bfx]['bids'] or not depths[self.market_bfx]['asks']:
            return False

        if not depths[self.market_bn]['bids'] or not depths[self.market_bn]['asks']:
            return False

        bfx_bid_price = depths[self.market_bfx]['bids'][0]['price']
        bfx_ask_price = depths[self.market_bfx]['asks'][0]['price']
        if bfx_bid_price <= 0 or bfx_ask_price <= 0:
            return False

        bn_bid_price = depths[self.market_bn]['bids'][0]['price']
        bn_ask_price = depths[self.market_bn]['asks'][0]['price']
        if bn_bid_price <= 0 or bn_ask_price <= 0:
            return False
        return True

    def tick(self, depths):
        if not self.is_depths_available(depths):
            return
        bfx_bid_price, bfx_ask_price = self.get_ticker(depths, self.market_bfx)
        bfx_bid_amount, bfx_ask_amount = self.get_amount(depths, self.market_bfx)
        bn_bid_price, bn_ask_price = self.get_ticker(depths, self.market_bn)
        bn_bid_amount, bn_ask_amount = self.get_amount(depths, self.market_bn)

        if bfx_bid_price > bn_ask_price:
            sell_price = bfx_bid_price
            sell_amount = bfx_bid_amount
            buy_price = bn_ask_price
            buy_amount = bn_ask_amount

            diff_price = sell_price - buy_price
            percent = round(diff_price / buy_price * 100, 3)
            diff_amount = min(sell_amount, buy_amount)
            profit = round(diff_price * diff_amount, 8)
            self.profit_count += 1
            self.profit_total += profit
            self.percent_total = self.percent_total + percent
            av_percent = round(self.percent_total / self.profit_count, 3)
            logging.info("bitfinex and binance eth_btc profit total: %s, av percent:%s, count: %s" %
                         (self.profit_total, av_percent, self.profit_count))
            pass
        elif bfx_ask_price < bn_bid_price:
            sell_price = bn_bid_price
            sell_amount = bn_bid_amount
            buy_price = bfx_ask_price
            buy_amount = bfx_ask_amount

            diff_price = sell_price - buy_price
            percent = round(diff_price / buy_price * 100, 3)
            diff_amount = min(sell_amount, buy_amount)
            profit = round(diff_price * diff_amount, 8)
            self.profit_count += 1
            self.profit_total += profit
            self.percent_total = self.percent_total + percent
            av_percent = round(self.percent_total / self.profit_count, 3)
            logging.info("bitfinex and binance eth_btc profit total: %s, av percent:%s, count: %s" %
                         (self.profit_total, av_percent, self.profit_count))
        else:
            logging.info("bitfinex and binance eth_btc no chance to profit")

    @classmethod
    def get_ticker(cls, depths, market):
        bid_price = depths[market]["bids"][0]['price']
        ask_price = depths[market]["asks"][0]['price']
        return bid_price, ask_price

    @classmethod
    def get_amount(cls, depths, market):
        bid_amount = depths[market]["bids"][0]['amount']
        ask_amount = depths[market]["asks"][0]['amount']
        return bid_amount, ask_amount
