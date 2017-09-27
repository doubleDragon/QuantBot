from quant import config
from ._bitfinex import Bitfinex
from ._liqui import Liqui
from ._bittrex import Bittrex
import logging


def create_brokers(exchange_names):
    brokers = {}
    for name in exchange_names:
        # if (name == 'KKEX_BCH_BTC'):
        #     xchg = KKEX('BCCBTC', config.KKEX_API_KEY, config.KKEX_SECRET_TOKEN)
        # elif (name == 'KKEX_ETH_BTC'):
        #     xchg = KKEX('ETHBTC', config.KKEX_API_KEY, config.KKEX_SECRET_TOKEN)
        # elif (name == 'Bitfinex_BCH_BTC'):
        #     xchg = Bitfinex('bchbtc', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        # elif (name == 'Bittrex_BCH_BTC'):
        #     xchg = Bittrex('BTC-BCC', config.Bittrex_API_KEY, config.Bittrex_SECRET_TOKEN)
        # elif (name == 'Viabtc_BCH_BTC'):
        #     xchg = Viabtc('bccbtc', config.Viabtc_API_KEY, config.Viabtc_SECRET_TOKEN)
        # elif (name == 'Viabtc_BCH_CNY'):
        #     xchg = Viabtc('bcccny', config.Viabtc_API_KEY, config.Viabtc_SECRET_TOKEN)
        # elif (name == 'Viabtc_BTC_CNY'):
        #     xchg = Viabtc('btccny', config.Viabtc_API_KEY, config.Viabtc_SECRET_TOKEN)
        # else:
        #     logging.warn('Exchange ' + name + ' not supported!')
        #     assert False
        if name == 'Bitfinex_BCH_USD':
            chg = Bitfinex('bchusd', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif name == 'Bitfinex_ZEC_USD':
            chg = Bitfinex('zecusd', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif name == 'Bitfinex_BCH_BTC':
            chg = Bitfinex('bchbtc', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif name == 'Bitfinex_BTC_USD':
            chg = Bitfinex('btcusd', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif name == 'Liqui_BCC_BTC':
            chg = Liqui('bccbtc', config.Liqui_API_KEY, config.Liqui_SECRET_TOKEN)
        elif name == 'Bittrex_ZEC_BTC':
            chg = Bittrex('BTC-ZEC', config.Bittrex_API_KEY, config.Bittrex_SECRET_TOKEN)
        else:
            logging.warn('Exchange ' + name + ' not supported!')
            assert False
        logging.info('%s broker initialized' % chg.name)

        brokers[name] = chg
    return brokers
