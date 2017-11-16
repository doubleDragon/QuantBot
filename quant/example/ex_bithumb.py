#!/usr/bin/env python
# -*- coding: UTF-8 -*-


from quant import config
from quant.api.bithumb import PrivateClient
from quant.brokers._bithumb import Bithumb

"""test api client"""
# client = PrivateClient(config.Bithumb_API_KEY, config.Bithumb_SECRET_TOKEN)

# print(client.account())
# res = client.balances('bch')
# if res:
#     print(str(res))
# else:
#     print('balance failed')


'''test sell order'''
# res = client.sell(currency='btc', price=1500000, amount=0.0001)
# if res:
#     print('place order success======>' + str(res))
# else:
#     print('place order failed')


'''test get orders'''
# 1510642305378, 1510642337397, 1510642076674
# order_id = '1510646372110'
# currency = 'btc'
# order_type = 'ask'
# res = client.get_order(order_id=order_id, currency=currency, order_type=order_type)
# if res:
#     print('get orders success======>' + str(res))
# else:
#     print('get orders failed')

# 获取已成交订单信息
# order_id = '1510646372110'
# currency = 'btc'
# order_type = 'ask'
# res = client.order_detail(currency=currency, order_id=order_id, order_type=order_type)
# if res:
#     print('order detail success======>' + str(res))
# else:
#     print('order detail failed')


"""test broker"""
# broker = Bithumb(pair_code='btc', api_key=config.Bithumb_API_KEY, api_secret=config.Bithumb_SECRET_TOKEN)
'''test buy order'''
# price = 8200000.000000
# amount = 0.0029
# order_id, order = broker.buy_limit(amount=amount, price=price)
# if order_id:
#     print('broker buy order id: %s' % order_id)
#     if order:
#         print('broker buy order info: ' + str(order))
# else:
#     print('broker buy order failed')

'''test sell order'''
# price = 8500000
# amount = 0.001
# order_id, order = broker.sell_limit(amount=amount, price=price)
# if order_id:
#     print('broker sell order id: %s' % order_id)
#     if order:
#         print('broker sell order info: ' + str(order))
# else:
#     print('broker sell order failed')


'''test cancel order'''
# order_id = '1510819655981'
# order_type = 'ask'
# res = broker.cancel_order(order_id=order_id, order_type=order_type)
# print('broker cancel res: ' + str(res))

'''test get order'''
# order_id = '1510819655981'
# order_type = 'ask'
# res = broker.get_order(order_id=order_id, order_type=order_type)
# if res:
#     print('broker get order: ' + str(res))
# else:
#     print('broker get order failed')

'''test balance, 注意切换pair_code'''
# broker.get_balances()

'''test order detail'''
# order_id = '1510819655981'
# order_type = 'ask'
# res = broker.order_detail(order_id=order_id, order_type=order_type)
# if res:
#     print('broker order detail success: ' + str(res))
# else:
#     print('broker order detail failed')

'''test order detail'''
# order_id = '1510819181758'
# order_type = 'ask'
# print(broker.get_deal_amount(order_id=order_id, order_type=order_type))
