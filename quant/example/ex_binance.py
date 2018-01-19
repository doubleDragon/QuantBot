#!/usr/bin/env python
# -*- coding: UTF-8 -*-


from __future__ import print_function
from quant.brokers.broker_factory import create_brokers
from quant.markets.market_factory import create_markets

pair_code = 'Binance_ZRX_ETH'

markets = create_markets([pair_code])
market = markets[pair_code]
depth = market.get_depth()
print(depth)

brokers = create_brokers([pair_code])
broker = brokers[pair_code]
ticker = broker.get_ticker()
print(ticker)
