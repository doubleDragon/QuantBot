#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import time

from quant import config
from quant.api.bitfinex import PrivateClient

client = PrivateClient(key=config.Bitfinex_SUB_API_KEY, secret=config.Bitfinex_SUB_SECRET_TOKEN)
# client = PrivateClient(key=config.Bitfinex_API_KEY, secret=config.Bitfinex_SECRET_TOKEN)
# print(client.ticker('eosbtc'))
# print(client.balances())

amount = '20.0'
price = '0.00015'
symbol = 'eosbtc'
r_id = client.buy(symbol=symbol, amount=amount, price=price)
print(r_id)

if r_id:
    time.sleep(1)
    client.cancel_order(r_id)

# print(client.cancel_all_orders())


