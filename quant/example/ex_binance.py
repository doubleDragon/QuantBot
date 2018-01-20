#!/usr/bin/env python
# -*- coding: UTF-8 -*-


from __future__ import print_function
from quant.brokers.broker_factory import create_brokers

pair_code = 'Binance_ZRX_ETH'

'''test broker'''
brokers = create_brokers([pair_code])
broker = brokers[pair_code]

'''sell order'''
# amount = 10
# price = 0.0019
# order_id = broker.sell_limit(amount=amount, price=price)
# if order_id:
#     print('sell order success, id = %s' % order_id)
# else:
#     print('sell order failed')

'''buy order'''

'''get order 5863126'''
# order = broker.get_order(order_id=5863126)
# if order:
#     print('get order success, %s' % order)
# else:
#     print('get order failed')

'''cancel order 5957505'''
# order_id = 5957505
# res = broker.cancel_order(order_id=order_id)
# if res:
#     print('cancel order: % success' % order_id)
# else:
#     print('cancel order: % failed' % order_id)
