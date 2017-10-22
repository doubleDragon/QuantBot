#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from quant.api.kraken import PublicClient

import market_util

from .market import Market


class Kraken(Market):
    """XBT就是BTC"""
    def __init__(self, pair_code):
        base_currency, market_currency = self.get_available_pairs(pair_code)
        super(Kraken, self).__init__(base_currency, market_currency, pair_code, 0.002)
        self.client = PublicClient()

    @classmethod
    def get_available_pairs(cls, pair_code):
        if pair_code == 'xbteur':
            base_currency = 'EUR'
            market_currency = 'XBT'
        elif pair_code == 'xbtusd':
            base_currency = 'USD'
            market_currency = 'XBT'
        elif pair_code == 'etheur':
            base_currency = 'EUR'
            market_currency = 'ETH'
        elif pair_code == 'ethusd':
            base_currency = 'USD'
            market_currency = 'ETH'
        elif pair_code == 'bcheur':
            base_currency = 'EUR'
            market_currency = 'BCH'
        elif pair_code == 'bchusd':
            base_currency = 'USD'
            market_currency = 'BCH'
        elif pair_code == 'eoseur':
            base_currency = 'EUR'
            market_currency = 'EOS'
        elif pair_code == 'eosusd':
            base_currency = 'USD'
            market_currency = 'EOS'
        else:
            assert False
        return base_currency, market_currency

    def update_depth(self):
        depth_raw = self.client.depth(self.pair_code)
        if depth_raw and 'result' in depth_raw:
            depth_raw = depth_raw['result']
            if len(depth_raw) > 0:
                depth_raw = depth_raw.values()[0]
                self.depth = self.format_depth(depth_raw)

    @classmethod
    def format_depth(cls, depth):
        bids = market_util.sort_and_format_list(depth['bids'], True)
        asks = market_util.sort_and_format_list(depth['asks'], False)
        return {'asks': asks, 'bids': bids}
