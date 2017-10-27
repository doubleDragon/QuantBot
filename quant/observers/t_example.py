#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import logging

from quant.observers.basicbot import BasicBot


class T_Example(BasicBot):

    """
    python -m quant.cli -mBitfinex_BCH_USD,Liqui_BCC_BTC,Bitfinex_BTC_USD -oT_Example -f=example -d
    """

    def __init__(self):
        super(T_Example, self).__init__()

    def tick(self, depths):
        logging.debug("t_test tick invoke")
