#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging

from quant.observers.basicbot import BasicBot

"""
./venv/bin/python -m quant.cli -mBinance_ETH_USDT,Binance_BTC_USDT,Huobi_ETH_USDT,Huobi_BTC_USDT -oC_USDT -f=c_usdt -v
"""


class C_USDT(BasicBot):

    def __init__(self):
        super(C_USDT, self).__init__()
        self.market_eth_bn = "Binance_ETH_USDT"
        self.market_eth_hb = "Huobi_ETH_USDT"
        self.market_btc_bn = "Binance_BTC_USDT"
        self.market_btc_hb = "Huobi_BTC_USDT"
        self.profit_count = 0
        self.profit_total = 0
        self.percent_total = 0

        self.fee_hb = 0.002
        self.fee_bn = 0.001

        logging.info('C_USDT Setup complete')

    def is_depths_available(self, depths):
        if not depths:
            return False
        res = self.market_eth_hb in depths and self.market_eth_bn in depths

        if not res:
            logging.debug("eth market not exist in depths")
            return False

        res = self.market_btc_hb in depths and self.market_btc_bn in depths
        if not res:
            logging.debug("btc market not exist in depths")
            return False

        if not depths[self.market_eth_hb]['bids'] or not depths[self.market_eth_hb]['asks']:
            logging.debug("market_eth_hb invalid")
            return False

        if not depths[self.market_btc_hb]['bids'] or not depths[self.market_btc_hb]['asks']:
            logging.debug("market_btc_hb invalid")
            return False

        if not depths[self.market_eth_bn]['bids'] or not depths[self.market_eth_bn]['asks']:
            logging.debug("market_eth_bn invalid")
            return False

        if not depths[self.market_btc_bn]['bids'] or not depths[self.market_btc_bn]['asks']:
            logging.debug("market_btc_bn invalid")
            return False

        bfx_bid_price = depths[self.market_eth_hb]['bids'][0]['price']
        bfx_ask_price = depths[self.market_eth_hb]['asks'][0]['price']
        if bfx_bid_price <= 0 or bfx_ask_price <= 0:
            return False

        bn_bid_price = depths[self.market_eth_bn]['bids'][0]['price']
        bn_ask_price = depths[self.market_eth_bn]['asks'][0]['price']
        if bn_bid_price <= 0 or bn_ask_price <= 0:
            return False
        return True

    def handle_eth(self, depths):
        hb_bid_price, hb_ask_price = self.get_ticker(depths, self.market_eth_hb)
        hb_bid_price = round(hb_bid_price * (1 - self.fee_hb), 2)
        hb_ask_price = round(hb_ask_price * (1 + self.fee_hb), 2)
        hb_bid_amount, hb_ask_amount = self.get_amount(depths, self.market_eth_hb)

        bn_bid_price, bn_ask_price = self.get_ticker(depths, self.market_eth_bn)
        bn_bid_price = round(bn_bid_price * (1 - self.fee_bn), 2)
        bn_ask_price = round(bn_ask_price * (1 + self.fee_bn), 2)
        bn_bid_amount, bn_ask_amount = self.get_amount(depths, self.market_eth_bn)

        if hb_bid_price > bn_ask_price:
            sell_price = hb_bid_price
            sell_amount = hb_bid_amount
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
            logging.info("huobi and binance eth_usdt profit total: %s, av percent:%s, count: %s" %
                         (self.profit_total, av_percent, self.profit_count))
        elif hb_ask_price < bn_bid_price:
            sell_price = bn_bid_price
            sell_amount = bn_bid_amount
            buy_price = hb_ask_price
            buy_amount = hb_ask_amount

            diff_price = sell_price - buy_price
            percent = round(diff_price / buy_price * 100, 3)
            diff_amount = min(sell_amount, buy_amount)
            profit = round(diff_price * diff_amount, 8)
            self.profit_count += 1
            self.profit_total += profit
            self.percent_total = self.percent_total + percent
            av_percent = round(self.percent_total / self.profit_count, 3)
            logging.info("huobi and binance eth_usdt profit total: %s, av percent:%s, count: %s" %
                         (self.profit_total, av_percent, self.profit_count))
        else:
            logging.info("huobi and binance eth_usdt no chance to profit")

    def handle_btc(self, depths):
        hb_bid_price, hb_ask_price = self.get_ticker(depths, self.market_btc_hb)
        hb_bid_price = round(hb_bid_price * (1 - self.fee_hb), 2)
        hb_ask_price = round(hb_ask_price * (1 + self.fee_hb), 2)
        hb_bid_amount, hb_ask_amount = self.get_amount(depths, self.market_btc_hb)

        bn_bid_price, bn_ask_price = self.get_ticker(depths, self.market_btc_bn)
        bn_bid_price = round(bn_bid_price * (1 - self.fee_bn), 2)
        bn_ask_price = round(bn_ask_price * (1 + self.fee_bn), 2)
        bn_bid_amount, bn_ask_amount = self.get_amount(depths, self.market_btc_bn)

        if hb_bid_price > bn_ask_price:
            sell_price = hb_bid_price
            sell_amount = hb_bid_amount
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
            logging.info("huobi and binance btc_usdt profit total: %s, av percent:%s, count: %s" %
                         (self.profit_total, av_percent, self.profit_count))
        elif hb_ask_price < bn_bid_price:
            sell_price = bn_bid_price
            sell_amount = bn_bid_amount
            buy_price = hb_ask_price
            buy_amount = hb_ask_amount

            diff_price = sell_price - buy_price
            percent = round(diff_price / buy_price * 100, 3)
            diff_amount = min(sell_amount, buy_amount)
            profit = round(diff_price * diff_amount, 8)
            self.profit_count += 1
            self.profit_total += profit
            self.percent_total = self.percent_total + percent
            av_percent = round(self.percent_total / self.profit_count, 3)
            logging.info("huobi and binance btc_usdt profit total: %s, av percent:%s, count: %s" %
                         (self.profit_total, av_percent, self.profit_count))
        else:
            logging.info("huobi and binance btc_usdt no chance to profit")

    def tick(self, depths):
        if not self.is_depths_available(depths):
            return
        self.handle_eth(depths)
        self.handle_btc(depths)

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
