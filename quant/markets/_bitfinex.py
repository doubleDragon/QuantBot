from .market import Market
from quant.api.bitfinex import PublicClient as Client
import market_util


class Bitfinex(Market):
    def __init__(self, pair_code):
        base_currency, market_currency = self.get_available_pairs(pair_code)
        super(Bitfinex, self).__init__(base_currency, market_currency, pair_code, 0.002)
        self.client = Client()

    def symbol(self):
        return "%s%s" % (self.market_currency.lower(), self.base_currency.lower())

    def update_depth(self):
        depth_raw = self.client.depth(self.symbol())

        if depth_raw:
            self.depth = self.format_depth(depth_raw)

    @classmethod
    def format_depth(cls, depth):
        bids = market_util.sort_and_format_dict(depth['bids'], True)
        asks = market_util.sort_and_format_dict(depth['asks'], False)
        return {'asks': asks, 'bids': bids}

    @classmethod
    def get_available_pairs(cls, pair_code):
        if pair_code == 'bchbtc':
            base_currency = 'BTC'
            market_currency = 'BCH'
        elif pair_code == 'btcusd':
            base_currency = 'USD'
            market_currency = 'BTC'
        elif pair_code == 'bchusd':
            base_currency = 'USD'
            market_currency = 'BCH'
        else:
            assert False
        return base_currency, market_currency
