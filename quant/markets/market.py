#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging
import time

from quant import config


class Market(object):
    def __init__(self, base_currency, market_currency, pair_code, fee_rate):
        self._name = None
        self.base_currency = base_currency
        self.market_currency = market_currency
        self.pair_code = pair_code
        self.fee_rate = fee_rate

        self.depth_updated = 0
        self.update_rate = 3

        self.is_terminated = False
        self.request_timeout = 5  # 5s
        self.depth = {'asks': [{'price': 0, 'amount': 0}], 'bids': [
            {'price': 0, 'amount': 0}]}

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
            # logging.warn('Market: %s order book is expired(%s>%s)', self.name, timediff,
            # config.market_expiration_time)
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

    def sort_and_format(self, l, reverse=False):
        l.sort(key=lambda x: float(x[0]), reverse=reverse)
        r = []
        for i in l:
            r.append({'price': float(i[0]), 'amount': float(i[1])})
        return r

    def format_depth(self, depth):
        bids = self.sort_and_format(depth['bids'], True)
        asks = self.sort_and_format(depth['asks'], False)
        return {'asks': asks, 'bids': bids}

    # Abstract methods
    def update_depth(self):
        pass
