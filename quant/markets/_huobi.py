#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from .market import Market
from quant.api.huobi import PublicClient as Client
import market_util


class Huobi(Market):
    def __init__(self, pair_code):
        base_currency, market_currency = self.get_available_pairs(pair_code)
        super(Huobi, self).__init__(base_currency, market_currency, pair_code, 0.002)
        self.client = Client()

    def update_depth(self):
        try:
            depth_raw = self.client.depth(self.pair_code)
            if depth_raw:
                if 'status' not in depth_raw and depth_raw['status'] != 'ok':
                    raise Exception('status not exist in raw response or is not ok')
                if 'tick' not in depth_raw:
                    raise Exception('tick not exist in raw response')
                self.depth = self.format_depth(depth_raw['tick'])
            else:
                raise Exception('response is None')
        except Exception as e:
            raise e

    @classmethod
    def format_depth(cls, depth):
        bids = market_util.sort_and_format_list(depth['bids'], True)
        asks = market_util.sort_and_format_list(depth['asks'], False)
        return {'asks': asks, 'bids': bids}

    @classmethod
    def get_available_pairs(cls, pair_code):
        if pair_code == 'ethusdt':
            base_currency = 'USDT'
            market_currency = 'ETH'
        elif pair_code == 'ethbtc':
            base_currency = 'BTC'
            market_currency = 'ETH'
        elif pair_code == 'etcbtc':
            base_currency = 'BTC'
            market_currency = 'ETC'
        elif pair_code == 'etcusdt':
            base_currency = 'USDT'
            market_currency = 'ETC'
        elif pair_code == 'bchbtc':
            base_currency = 'BTC'
            market_currency = 'BCH'
        elif pair_code == 'btcusdt':
            base_currency = 'USDT'
            market_currency = 'BTC'
        else:
            assert False
        return base_currency, market_currency
