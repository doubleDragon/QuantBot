#!/usr/bin/env python
# -*- coding: UTF-8 -*-


from quant.api import bithumb
from .market import Market


class Bithumb(Market):
    def __init__(self, pair_code):
        base_currency, market_currency = self.get_available_pairs(pair_code)

        super(Bithumb, self).__init__(base_currency, market_currency, pair_code, 0.0025)

        self.client = bithumb.PublicClient()

    def update_depth(self):
        raw_depth = self.client.depth(self.pair_code)
        if raw_depth and 'data' in raw_depth:
            raw_depth = raw_depth['data']
            self.depth = self.format_depth(raw_depth)

    @classmethod
    def sort_and_format(cls, l, reverse=False):
        l.sort(key=lambda x: float(x['price']), reverse=reverse)
        r = []
        for i in l:
            r.append({'price': float(i['price']), 'amount': float(i['quantity'])})
        return r

    def format_depth(self, depth):
        bids = self.sort_and_format(depth['bids'], True)
        asks = self.sort_and_format(depth['asks'], False)
        return {'asks': asks, 'bids': bids}

    @classmethod
    def get_available_pairs(cls, pair_code):
        if pair_code == 'btc':
            base_currency = 'KRW'
            market_currency = 'BTC'
        elif pair_code == 'eth':
            base_currency = 'KRW'
            market_currency = 'ETH'
        elif pair_code == 'bch':
            base_currency = 'KRW'
            market_currency = 'BCH'
        else:
            assert False
        return base_currency, market_currency
