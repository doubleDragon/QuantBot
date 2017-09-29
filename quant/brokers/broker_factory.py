from quant import config
from ._bitfinex import Bitfinex
from ._liqui import Liqui
from ._bittrex import Bittrex
from ._binance import Binance
import logging


def create_brokers(exchange_names):
    brokers = {}
    for name in exchange_names:
        if name == 'Bitfinex_BCH_USD':
            chg = Bitfinex('bchusd', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif name == 'Bitfinex_ZEC_USD':
            chg = Bitfinex('zecusd', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif name == 'Bitfinex_BCH_BTC':
            chg = Bitfinex('bchbtc', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif name == 'Bitfinex_BTC_USD':
            chg = Bitfinex('btcusd', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif name == 'Liqui_BCC_BTC':
            chg = Liqui('bcc_btc', config.Liqui_API_KEY, config.Liqui_SECRET_TOKEN)
        elif name == 'Bittrex_ZEC_BTC':
            chg = Bittrex('BTC-ZEC', config.Bittrex_API_KEY, config.Bittrex_SECRET_TOKEN)
        elif name == 'Binance_ETH_BTC':
            chg = Binance('ETHBTC', config.Binance_API_KEY, config.Binance_SECRET_TOKEN)
        elif name == 'Binance_BNB_BTC':
            chg = Binance('BNBBTC', config.Binance_API_KEY, config.Binance_SECRET_TOKEN)
        elif name == 'Binance_BNB_ETH':
            chg = Binance('BNBETH', config.Binance_API_KEY, config.Binance_SECRET_TOKEN)
        elif name == 'Binance_MCO_BTC':
            chg = Binance('MCOBTC', config.Binance_API_KEY, config.Binance_SECRET_TOKEN)
        elif name == 'Binance_MCO_ETH':
            chg = Binance('MCOETH', config.Binance_API_KEY, config.Binance_SECRET_TOKEN)
        elif name == 'Binance_QTUM_BTC':
            chg = Binance('QTUMBTC', config.Binance_API_KEY, config.Binance_SECRET_TOKEN)
        elif name == 'Binance_QTUM_ETH':
            chg = Binance('QTUMETH', config.Binance_API_KEY, config.Binance_SECRET_TOKEN)
        elif name == 'Binance_WTC_BTC':
            chg = Binance('WTCBTC', config.Binance_API_KEY, config.Binance_SECRET_TOKEN)
        elif name == 'Binance_WTC_ETH':
            chg = Binance('WTCETH', config.Binance_API_KEY, config.Binance_SECRET_TOKEN)
        elif name == 'Binance_BCC_BTC':
            chg = Binance('BCCBTC', config.Binance_API_KEY, config.Binance_SECRET_TOKEN)
        else:
            logging.warn('Exchange ' + name + ' not supported!')
            assert False
        logging.info('%s broker initialized' % chg.name)

        brokers[name] = chg
    return brokers
