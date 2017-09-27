import logging

from quant.common import constant
from ._bitfinex import Bitfinex
from ._kkex import Kkex
from ._liqui import Liqui
from ._hitbtc import Hitbtc
from ._cex import Cex
from ._bittrex import Bittrex


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
        elif name == "%s_ZEC_USD" % constant.EX_BFX:
            ex = Bitfinex('zecusd')
        elif name == "%s_BCH_BTC" % constant.EX_BFX:
            ex = Bitfinex('bchbtc')
        elif name == "%s_BTC_USD" % constant.EX_BFX:
            ex = Bitfinex('btcusd')
        elif name == "%s_EOS_USD" % constant.EX_BFX:
            ex = Bitfinex('eosusd')
        elif name == "%s_EOS_BTC" % constant.EX_BFX:
            ex = Bitfinex('eosbtc')
        elif name == "%s_BCC_BTC" % constant.EX_KKEX:
            ex = Kkex('bccbtc')
        elif name == "%s_BCC_BTC" % constant.EX_LQ:
            ex = Liqui('bccbtc')
        elif name == "%s_EOS_BTC" % constant.EX_LQ:
            ex = Liqui('eosbtc')
        elif name == "%s_BCC_BTC" % constant.EX_HITBITC:
            ex = Hitbtc('bccbtc')
        elif name == "%s_BCC_BTC" % constant.EX_CEX:
            ex = Cex('bccbtc')
        elif name == "%s_ZEC_BTC" % constant.EX_BITTREX:
            ex = Bittrex('BTC-ZEC')
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
