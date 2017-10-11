from quant import config
from ._bitfinex import Bitfinex
from ._liqui import Liqui
from ._bittrex import Bittrex
from ._binance import Binance
from ._gate import Gate
import logging


def create_brokers(exchange_names):
    brokers = {}
    for name in exchange_names:
        if name == 'Bitfinex_BCH_USD':
            chg = Bitfinex('bchusd', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif name == 'Bitfinex_ETH_USD':
            chg = Bitfinex('ethusd', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif name == 'Bitfinex_ETH_BTC':
            chg = Bitfinex('ethbtc', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif name == 'Bitfinex_ZEC_USD':
            chg = Bitfinex('zecusd', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif name == 'Bitfinex_BCH_BTC':
            chg = Bitfinex('bchbtc', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif name == 'Bitfinex_BTC_USD':
            chg = Bitfinex('btcusd', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif name == 'Bitfinex_BT1_USD':
            chg = Bitfinex('bt1usd', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif name == 'Bitfinex_BT2_USD':
            chg = Bitfinex('bt2usd', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif name == 'Bitfinex_BT1_BTC':
            chg = Bitfinex('bt1btc', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif name == 'Bitfinex_BT2_BTC':
            chg = Bitfinex('bt2btc', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif name == 'Bitfinex_NEO_USD':
            chg = Bitfinex('neousd', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif name == 'Bitfinex_NEO_BTC':
            chg = Bitfinex('neobtc', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif name == 'Bitfinex_NEO_ETH':
            chg = Bitfinex('neoeth', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif name == 'Bitfinex_IOT_ETH':
            chg = Bitfinex('ioteth', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif name == 'Bitfinex_IOT_BTC':
            chg = Bitfinex('iotbtc', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif name == 'Bitfinex_IOT_USD':
            chg = Bitfinex('iotusd', config.Bitfinex_API_KEY, config.Bitfinex_SECRET_TOKEN)
        elif name == 'Liqui_BCC_BTC':
            chg = Liqui('bcc_btc', config.Liqui_API_KEY, config.Liqui_SECRET_TOKEN)
        elif name == 'Liqui_BCC_ETH':
            chg = Liqui('bcc_eth', config.Liqui_API_KEY, config.Liqui_SECRET_TOKEN)
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
        elif name == 'Binance_NEO_BTC':
            chg = Binance('NEOBTC', config.Binance_API_KEY, config.Binance_SECRET_TOKEN)
        elif name == 'Binance_NEO_ETH':
            chg = Binance('NEOETH', config.Binance_API_KEY, config.Binance_SECRET_TOKEN)
        elif name == 'Binance_IOTA_ETH':
            chg = Binance('IOTAETH', config.Binance_API_KEY, config.Binance_SECRET_TOKEN)
        elif name == 'Binance_IOTA_BTC':
            chg = Binance('IOTABTC', config.Binance_API_KEY, config.Binance_SECRET_TOKEN)
        elif name == 'Gate_BCC_BTC':
            chg = Gate('bcc_btc', config.Gate_API_KEY, config.Gate_SECRET_TOKEN)
        else:
            logging.warn('Exchange ' + name + ' not supported!')
            assert False
        logging.info('%s broker initialized' % chg.name)

        brokers[name] = chg
    return brokers
