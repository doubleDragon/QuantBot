#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import time

from quant import config
from quant.api.bitfinex import PrivateClient
from quant.brokers.broker_factory import create_brokers

'''test client'''
# client = PrivateClient(key=config.Bitfinex_SUB_API_KEY, secret=config.Bitfinex_SUB_SECRET_TOKEN)
# client = PrivateClient(key=config.Bitfinex_API_KEY, secret=config.Bitfinex_SECRET_TOKEN)

'''test ticker'''
# print(client.ticker('eosbtc'))


'''test balance'''
# print(client.balances())

'''test buy'''
# symbol = 'bchbtc'
# amount = '0.5'
# price = '0.092'
# resp = client.buy(symbol=symbol, amount=amount, price=price)
# print(resp)

'''test sell'''
# symbol = 'datbtc'
# amount = '136'
# price = '0.000015'
# resp = client.sell(symbol=symbol, amount=amount, price=price)
# if resp:
#     print('make sell order success: ' + str(resp))
# else:
#     print('make sell order failed')

'''test get order'''
# order_id = '5951670653'
# resp = client.get_order(order_id=order_id)
# print(resp)

'''test cancel order'''
# order_id = '5951670653'
# resp = client.cancel_order(order_id)
# print(resp)

'''test cancel all orders'''
# print(client.cancel_all_orders())

'''test orders'''
# resp = client.orders_history(1)
# if resp:
#     print('orders history : ' + str(resp))
# else:
#     print('orders history failed')


'''test broker'''
pair_code = 'Bitfinex_ZRX_ETH'
brokers = create_brokers([pair_code])
broker = brokers[pair_code]

'''test sell order'''
# price = 0.0019
# amount = 6
# order = broker.sell_limit(price=price, amount=amount)
# if order:
#     print('sell order: %s' % str(order))
# else:
#     print('sell order failed')


'''test get order 7361152886'''
order_id = 7361152886
order = broker.get_order(order_id=order_id)
if order:
    print('get order: %s' % str(order))
else:
    print('get order failed')

'''test cancel order 7361152886'''
# order_id = 7361152886
# res = broker.cancel_order(order_id=order_id)
# if res:
#     print('cancel order: %s' % res)
# else:
#     print('cancel order failed')
