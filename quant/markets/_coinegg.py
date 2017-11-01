#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from quant.api.coinegg import PublicClient

import market_util

from .market import Market


class Coinegg(Market):
    """XBT就是BTC"""
    def __init__(self, pair_code):
        base_currency, market_currency = self.get_available_pairs(pair_code)
        super(Coinegg, self).__init__(base_currency, market_currency, pair_code, 0.001)
        self.client = PublicClient()

    @classmethod
    def get_available_pairs(cls, pair_code):
        if pair_code == 'bcc':
            base_currency = 'BTC'
            market_currency = 'BCC'
        elif pair_code == 'eth':
            base_currency = 'BTC'
            market_currency = 'ETH'
        elif pair_code == 'neo':
            base_currency = 'BTC'
            market_currency = 'NEO'
        elif pair_code == 'etc':
            base_currency = 'BTC'
            market_currency = 'ETC'
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
