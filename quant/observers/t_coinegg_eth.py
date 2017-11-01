#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from .t_coinegg import T_CoinEgg


class T_CoinEgg_ETH(T_CoinEgg):
    """
    bch:
    python -m quant.cli -mBitfinex_ETH_USD,Coinegg_ETH_BTC,Bitfinex_BTC_USD -o=T_CoinEgg_ETH -f=coinegg_eth -v

    目前的限制:
    """

    def __init__(self):
        base_pair = "Bitfinex_ETH_USD"
        pair_1 = "Coinegg_ETH_BTC"
        pair_2 = "Bitfinex_BTC_USD"

        kwargs = {
            'monitor_only': True,
            'precision': 2,
            'fee_base': 0.002,
            'fee_pair1': 0.001,
            'fee_pair2': 0.002,
            'min_amount_market': 0.04,
            'min_amount_mid': 0.004,
            'max_trade_amount': 1,
            'min_trade_amount': 0.04
        }
        super(T_CoinEgg_ETH, self).__init__(base_pair, pair_1, pair_2, **kwargs)
