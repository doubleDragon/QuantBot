#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from quant.api.liqui import PublicClient

import market_util

from .market import Market


class Liqui(Market):
    def __init__(self, pair_code):
        base_currency, market_currency = self.get_available_pairs(pair_code)
        super(Liqui, self).__init__(base_currency, market_currency, pair_code, 0.002)
        self.client = PublicClient()

    @classmethod
    def get_available_pairs(cls, pair_code):
        if pair_code == 'bcc_btc':
            base_currency = 'BTC'
            market_currency = 'BCC'
        elif pair_code == 'eos_btc':
            base_currency = 'BTC'
            market_currency = 'EOS'
        else:
            assert False
        return base_currency, market_currency

    def update_depth(self):
        depth_raw = self.client.depth(self.pair_code)
        if depth_raw and self.pair_code in depth_raw:
            self.depth = self.format_depth(depth_raw[self.pair_code])

    @classmethod
    def format_depth(cls, depth):
        bids = market_util.sort_and_format_list(depth['bids'], True)
        asks = market_util.sort_and_format_list(depth['asks'], False)
        return {'asks': asks, 'bids': bids}
