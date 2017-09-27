# Copyright (C) 2017, Philsong <songbohr@gmail.com>
from quant.api import bittrex
from .market import Market


class Bittrex(Market):
    def __init__(self, pair_code):
        base_currency, market_currency = self.get_available_pairs(pair_code)

        super(Bittrex, self).__init__(base_currency, market_currency, pair_code, 0.0025)

        self.client = bittrex.Bittrex(None, None)

    def update_depth(self):
        raw_depth = self.client.get_orderbook(self.pair_code, 'both')
        self.depth = self.format_depth(raw_depth)

    # override method
    def sort_and_format(self, l, reverse=False):
        l.sort(key=lambda x: float(x['Rate']), reverse=reverse)
        r = []
        for i in l:
            r.append({'price': float(i['Rate']), 'amount': float(i['Quantity'])})
        return r

    # override method
    def format_depth(self, depth):
        bids = self.sort_and_format(depth['result']['buy'], True)
        asks = self.sort_and_format(depth['result']['sell'], False)
        return {'asks': asks, 'bids': bids}

    @classmethod
    def get_available_pairs(cls, pair_code):
        if pair_code == 'BTC-BCC':
            base_currency = 'BTC'
            market_currency = 'BCH'
        elif pair_code == 'BTC-ZEC':
            base_currency = 'BTC'
            market_currency = 'ZEC'
        else:
            assert False
        return base_currency, market_currency
