#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from quant import config
from quant.brokers import broker_factory
from .basicbot import BasicBot


class Arbitrage(BasicBot):
    def __init__(self, base_pair, pair1, pair2, monitor_only=False):
        super(Arbitrage, self).__init__()
        self.base_pair = base_pair
        self.pair_1 = pair1
        self.pair_2 = pair2
        self.monitor_only = monitor_only
