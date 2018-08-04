#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging

from quant.observers.basicbot import BasicBot

"""
./venv/bin/python -m quant.cli -mBitfinex_ETH_BTC,Binance_ETH_BTC -oC_Diff_ETH -f=c_diff_eth -v
"""


class C_Diff_ETH(BasicBot):

    def __init__(self):
        super(C_Diff_ETH, self).__init__()
        self.market_bfx = 'Bitfinex_ETH_BTC'
        self.market_bn = 'Binance_ETH_BTC'

    def tick(self, depths):
        price_ask_bfx = depths[self.market_bfx]['asks'][0]['amount']
        price_bid_bfx = depths[self.market_bfx]['bids'][0]['amount']

        logging.info("bfx bid: %s, ask: %s" % (price_bid_bfx, price_ask_bfx))
