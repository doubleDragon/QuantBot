#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from .market import Market
from quant.api.kkex import PublicClient as Client
import market_util


class Kkex(Market):
    def __init__(self, pair_code):
        base_currency, market_currency = self.get_available_pairs(pair_code)
        super(Kkex, self).__init__(base_currency, market_currency, pair_code, 0.0025)
        self.client = Client()

    @classmethod
    def get_available_pairs(cls, pair_code):
        if pair_code == 'BCCBTC':
            base_currency = 'BTC'
            market_currency = 'BCC'
        else:
            assert False
        return base_currency, market_currency

    def update_depth(self):
        depth_raw = self.client.depth(self.pair_code)

        if depth_raw:
            self.depth = self.format_depth(depth_raw)

    @classmethod
    def format_depth(cls, depth):
        bids = market_util.sort_and_format_list(depth['bids'], True)
        asks = market_util.sort_and_format_list(depth['asks'], False)
        return {'asks': asks, 'bids': bids}
