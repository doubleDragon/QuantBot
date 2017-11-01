#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from .t_coinegg import T_CoinEgg


class T_CoinEgg_ETC(T_CoinEgg):
    """
    bch:
    python -m quant.cli -mBitfinex_ETC_USD,Coinegg_ETC_BTC,Bitfinex_BTC_USD -o=T_CoinEgg_ETC -f=coinegg_etc -v

    目前的限制:
    """

    def __init__(self):
        base_pair = "Bitfinex_ETC_USD"
        pair_1 = "Coinegg_ETC_BTC"
        pair_2 = "Bitfinex_BTC_USD"

        kwargs = {
            'monitor_only': True,
            'precision': 2,
            'fee_base': 0.002,
            'fee_pair1': 0.001,
            'fee_pair2': 0.002,
            'min_amount_market': 1.0,
            'min_amount_mid': 0.004,
            'max_trade_amount': 5,
            'min_trade_amount': 2.0
        }
        super(T_CoinEgg_ETC, self).__init__(base_pair, pair_1, pair_2, **kwargs)
