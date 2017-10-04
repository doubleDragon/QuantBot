# Copyright (C) 2017, Philsong <songbohr@gmail.com>

from quant.api.binance import Client
from quant.markets import market_util
from .market import Market


class Binance(Market):
    def __init__(self, pair_code):
        base_currency, market_currency = self.get_available_pairs(pair_code)
        super(Binance, self).__init__(base_currency, market_currency, pair_code, 0.001)

        self.client = Client(None, None)

    def update_depth(self):
        raw_depth = self.client.get_order_book(symbol=self.pair_code, limit=5)
        if raw_depth:
            self.depth = self.format_depth(raw_depth)

    @classmethod
    def get_available_pairs(cls, pair_code):
        if pair_code == 'BCCBTC':
            base_currency = 'BTC'
            market_currency = 'BCC'
        elif pair_code == 'ETHBTC':
            base_currency = 'BTC'
            market_currency = 'ETH'
        elif pair_code == 'BNBBTC':
            base_currency = 'BTC'
            market_currency = 'BNB'
        elif pair_code == 'BNBETH':
            base_currency = 'ETH'
            market_currency = 'BNB'
        elif pair_code == 'MCOBTC':
            base_currency = 'BTC'
            market_currency = 'MCO'
        elif pair_code == 'MCOETH':
            base_currency = 'ETH'
            market_currency = 'MCO'
        elif pair_code == 'QTUMBTC':
            base_currency = 'BTC'
            market_currency = 'QTUMBCH'
        elif pair_code == 'QTUMETH':
            base_currency = 'ETH'
            market_currency = 'QTUM'
        elif pair_code == 'WTCBTC':
            base_currency = 'BTC'
            market_currency = 'WTC'
        elif pair_code == 'WTCETH':
            base_currency = 'ETH'
            market_currency = 'WTC'
        elif pair_code == 'NEOBTC':
            base_currency = 'BTC'
            market_currency = 'NEO'
        elif pair_code == 'NEOETH':
            base_currency = 'ETH'
            market_currency = 'NEO'
        elif pair_code == 'IOTAETH':
            base_currency = 'ETH'
            market_currency = 'IOTA'
        elif pair_code == 'IOTABTC':
            base_currency = 'BTC'
            market_currency = 'IOTA'
        else:
            assert False
        return base_currency, market_currency

    @classmethod
    def format_depth(cls, depth):
        bids = market_util.sort_and_format_list(depth['bids'], True)
        asks = market_util.sort_and_format_list(depth['asks'], False)
        return {'asks': asks, 'bids': bids}
