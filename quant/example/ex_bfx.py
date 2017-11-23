#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import time

from quant import config
from quant.api.bitfinex import PrivateClient

# client = PrivateClient(key=config.Bitfinex_SUB_API_KEY, secret=config.Bitfinex_SUB_SECRET_TOKEN)
client = PrivateClient(key=config.Bitfinex_API_KEY, secret=config.Bitfinex_SECRET_TOKEN)
# print(client.ticker('eosbtc'))
# print(client.balances())


'''test sell'''
# symbol = 'datbtc'
# amount = '158'
# price = '0.00000875'
# resp = client.sell(symbol=symbol, amount=amount, price=price)
# if resp:
#     print('make sell order success: ' + str(resp))
# else:
#     print('make sell order failed')

order_id = '5396170001'
resp = client.get_order(order_id=5396170001)
if resp:
    print('get order success: ' + str(resp))
else:
    print('get order failed')

'''test cancel order'''
# order_id = ''
# client.cancel_order(order_id)

'''test cancel all orders'''
# print(client.cancel_all_orders())

'''test orders'''
# resp = client.orders_history(1)
# if resp:
#     print('orders history : ' + str(resp))
# else:
#     print('orders history failed')
