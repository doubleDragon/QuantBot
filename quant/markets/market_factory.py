import logging

from quant.common import constant
from ._bitfinex import Bitfinex


def create_markets(exchange_names):
    """
    [
        'Bitfinex_BCH_BTC'
        ...
    ]
    """
    markets = {}
    for name in exchange_names:
        if name == "%s_BCH_USD" % constant.EX_BFX:
            ex = Bitfinex('bchusd')
        elif name == "%s_BCH_BTC" % constant.EX_BFX:
            ex = Bitfinex('bchbtc')
        elif name == "%s_BTC_USD" % constant.EX_BFX:
            ex = Bitfinex('btcusd')
        else:
            logging.warn('Exchange ' + name + ' not supported!')
            assert False
        # if name == "Bitfinex_BCH_USD":
        #     ex = Bitfinex('bchusd')
        # elif name == "Bitfinex_BCH_BTC":
        #     ex = Bitfinex('bchbtc')
        # elif name == "Bitfinex_BTC_USD":
        #     ex = Bitfinex('btcusd')
        # else:
        #     logging.warn('Exchange ' + name + ' not supported!')
        #     assert False

        ex.name = name

        logging.info('%s market initialized' % ex.name)

        markets[name] = ex
    return markets
