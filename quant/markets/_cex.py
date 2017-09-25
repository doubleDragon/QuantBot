#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from quant.api.cex import PublicClient

import market_util

from .market import Market


class Cex(Market):
    def __init__(self, pair_code):
        base_currency, market_currency = self.get_available_pairs(pair_code)
        super(Cex, self).__init__(base_currency, market_currency, pair_code, 0.002)
        self.client = PublicClient()

    @classmethod
    def get_available_pairs(cls, pair_code):
        if pair_code == 'bccbtc':
            base_currency = 'BTC'
            market_currency = 'BCH'
        else:
            assert False
        return base_currency, market_currency

    def symbol(self):
        return "%s/%s" % (self.market_currency.upper(), self.base_currency.upper())

    def update_depth(self):
        depth_raw = self.client.depth(self.symbol())
        if depth_raw:
            self.depth = self.format_depth(depth_raw)

    @classmethod
    def format_depth(cls, depth):
        bids = market_util.sort_and_format_list(depth['bids'], True)
        asks = market_util.sort_and_format_list(depth['asks'], False)
        return {'asks': asks, 'bids': bids}
