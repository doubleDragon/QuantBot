#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging
import time
from quant import config


class Market(object):
    """
    eth_btc
        base_currency :btc
        quote_currency:eth
    """

    def __init__(self, base_currency, market_currency, pair_code, fee_rate):
        self._name = None
        self.base_currency = base_currency
        self.market_currency = market_currency
        self.pair_code = pair_code
        self.fee_rate = fee_rate

        self.depth_updated = 0
        self.update_rate = 1

        self.is_terminated = False
        self.request_timeout = 5  # 5s
        self.depth = {'asks': [{'price': 0, 'amount': 0}], 'bids': [{'price': 0, 'amount': 0}]}

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    def terminate(self):
        self.is_terminated = True

    def get_depth(self):
        time_diff = time.time() - self.depth_updated
        # logging.warn('Market: %s order book1:(%s>%s)', self.name, time_diff, self.depth_updated)
        if time_diff > self.update_rate:
            logging.debug('%s should update...', self.name)
            if not self.ask_update_depth():
                return None

        time_diff = time.time() - self.depth_updated
        # logging.warn('Market: %s order book2:(%s>%s)', self.name, time_diff, self.depth_updated)

        if time_diff > config.market_expiration_time:
            # logging.warn('Market: %s order book is expired(%s>%s)', self.name, time_diff,
            #              config.market_expiration_time)
            return None
        return self.depth

    def ask_update_depth(self):
        try:
            self.update_depth()
            # self.convert_to_usd()
            self.depth_updated = time.time()
            return True
        except Exception as e:
            logging.error("Can't update market: %s - err:%s" % (self.name, str(e)))
            # log_exception(logging.DEBUG)
            return False
            # traceback.print_exc()

    def get_ticker(self):
        depth = self.get_depth()
        if not depth:
            return None

        res = {'ask': {'price': 0, 'amount': 0}, 'bid': {'price': 0, 'amount': 0}}

        if len(depth['asks']) > 0:
            res['ask'] = depth['asks'][0]
        if len(depth['bids']) > 0:
            res['bid'] = depth['bids'][0]
        return res

    def update_depth(self):
        """子类重写该方法，每个market的数据不一样"""
        pass
