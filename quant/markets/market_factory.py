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
        if name == "%s_BCH_BTC" % constant.EX_BFX:
            ex = Bitfinex('bchbtc')
        else:
            logging.warn('Exchange ' + name + ' not supported!')
            assert False

        ex.name = name

        logging.info('%s market initialized' % ex.name)

        markets[name] = ex
    return markets
