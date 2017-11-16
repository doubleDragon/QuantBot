#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import division

from .t_bithumb import T_Bithumb


class T_Bithumb_BCH(T_Bithumb):
    """
    bch:
    ./venv/bin/python -m quant.cli -mBithumb_BCH_KRW,Bitfinex_BCH_BTC,Bithumb_BTC_KRW -o=T_Bithumb_BCH -f=bithumb_bch -v

    目前的限制:
    bithumb:    bch_krw=0.01
    bitfinex:   bch_btc: 0.02
    bithumb:    btc_krw=0.001

    """

    def __init__(self):
        base_pair = "Bithumb_BCH_KRW"
        pair_1 = "Bitfinex_BCH_BTC"
        pair_2 = "Bithumb_BTC_KRW"

        kwargs = {
            'monitor_only': False,
            'precision': 2,
            'fee_base': 0.0015,
            'fee_pair1': 0.002,
            'fee_pair2': 0.0015,
            'min_stock_base': 0.01,
            'min_stock_pair1': 0.02,
            'min_stock_pair2': 0.001,
            'max_trade_amount': 1,
            'min_trade_amount': 0.02
        }
        super(T_Bithumb_BCH, self).__init__(base_pair, pair_1, pair_2, **kwargs)
