from .market import Market
from quant.api.bitfinex import PublicClient as Client
import market_util


class Bitfinex(Market):
    def __init__(self, pair_code):
        base_currency, market_currency = self.get_available_pairs(pair_code)
        super(Bitfinex, self).__init__(base_currency, market_currency, pair_code, 0.002)
        self.client = Client()

    def update_depth(self):
        depth_raw = self.client.depth(self.pair_code)

        if depth_raw:
            self.depth = self.format_depth(depth_raw)

    @classmethod
    def format_depth(cls, depth):
        bids = market_util.sort_and_format_dict(depth['bids'], True)
        asks = market_util.sort_and_format_dict(depth['asks'], False)
        return {'asks': asks, 'bids': bids}

    @classmethod
    def get_available_pairs(cls, pair_code):
        if pair_code == 'ethusd':
            base_currency = 'USD'
            market_currency = 'ETH'
        elif pair_code == 'ethbtc':
            base_currency = 'BTC'
            market_currency = 'ETH'
        elif pair_code == 'bchbtc':
            base_currency = 'BTC'
            market_currency = 'BCH'
        elif pair_code == 'btcusd':
            base_currency = 'USD'
            market_currency = 'BTC'
        elif pair_code == 'bchusd':
            base_currency = 'USD'
            market_currency = 'BCH'
        elif pair_code == 'eosusd':
            base_currency = 'USD'
            market_currency = 'EOS'
        elif pair_code == 'zecusd':
            base_currency = 'USD'
            market_currency = 'ZEC'
        elif pair_code == 'neousd':
            base_currency = 'USD'
            market_currency = 'NEO'
        elif pair_code == 'neobtc':
            base_currency = 'BTC'
            market_currency = 'NEO'
        elif pair_code == 'neoeth':
            base_currency = 'ETH'
            market_currency = 'NEO'
        elif pair_code == 'iotusd':
            base_currency = 'USD'
            market_currency = 'IOT'
        elif pair_code == 'iotbtc':
            base_currency = 'BTC'
            market_currency = 'IOT'
        else:
            assert False
        return base_currency, market_currency
