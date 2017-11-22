#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import division

from .t_bithumb import T_Bithumb


class T_Bithumb_ETH(T_Bithumb):
    """
    bch:
    ./venv/bin/python -m quant.cli -mBithumb_ETH_KRW,Bitfinex_ETH_BTC,Bithumb_BTC_KRW -o=T_Bithumb_ETH -f=bithumb_eth -v

    目前的限制:
    """

    def __init__(self):
        base_pair = "Bithumb_ETH_KRW"
        pair_1 = "Bitfinex_ETH_BTC"
        pair_2 = "Bithumb_BTC_KRW"

        kwargs = {
            'monitor_only': True,
            'precision': 2,
            'fee_base': 0.0015,
            'fee_pair1': 0.002,
            'fee_pair2': 0.0015,
            'min_stock_base': 0.0,
            'min_stock_pair1': 0.01,
            'min_stock_pair2': 0.001,
            'max_trade_amount': 1,
            'min_trade_amount': 0.04
        }
        super(T_Bithumb_ETH, self).__init__(base_pair, pair_1, pair_2, **kwargs)
