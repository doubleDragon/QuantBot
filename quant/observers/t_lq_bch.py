#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import division

from .t_lq import T_Lq


class T_Lq_BCH(T_Lq):
    """
    bch:
    python -m quant.cli -mBitfinex_BCH_USD,Liqui_BCC_BTC,Bitfinex_BTC_USD -o=T_Lq_BCH -f=liqui_bch -v

    目前的限制:
    """

    def __init__(self):
        base_pair = "Bitfinex_BCH_USD"
        pair_1 = "Liqui_BCC_BTC"
        pair_2 = "Bitfinex_BTC_USD"

        kwargs = {
            'monitor_only': True,
            'precision': 2,
            'fee_base': 0.002,
            'fee_pair1': 0.0025,
            'fee_pair2': 0.002,
            'min_amount_market': 0.04,
            'min_amount_mid': 0.004,
            'max_trade_amount': 1,
            'min_trade_amount': 0.04
        }
        super(T_Lq_BCH, self).__init__(base_pair, pair_1, pair_2, **kwargs)
