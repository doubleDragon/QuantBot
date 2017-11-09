#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import division

from .t_bithumb import T_Bithumb


class T_Bithumb_BCH(T_Bithumb):
    """
    bch:
    python -m quant.cli -mBithumb_BCH_KRW,Bitfinex_BCH_BTC,Bithumb_BTC_KRW -o=T_Bithumb_BCH -f=bithumb_bch -v

    目前的限制:
    """

    def __init__(self):
        base_pair = "Bithumb_BCH_KRW"
        pair_1 = "Bitfinex_BCH_BTC"
        pair_2 = "Bithumb_BTC_KRW"

        kwargs = {
            'monitor_only': True,
            'precision': 2,
            'fee_base': 0.0015,
            'fee_pair1': 0.002,
            'fee_pair2': 0.0015,
            'min_amount_market': 0.04,
            'min_amount_mid': 0.004,
            'max_trade_amount': 1,
            'min_trade_amount': 0.04
        }
        super(T_Bithumb_BCH, self).__init__(base_pair, pair_1, pair_2, **kwargs)
