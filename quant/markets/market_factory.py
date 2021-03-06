#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging

from quant.common import constant
from ._bitfinex import Bitfinex
from ._kkex import Kkex
from ._liqui import Liqui
from ._hitbtc import Hitbtc
from ._cex import Cex
from ._bittrex import Bittrex
from ._binance import Binance
from ._gate import Gate
from ._bitflyer import Bitflyer
from ._kraken import Kraken
from ._coinegg import Coinegg
from ._bithumb import Bithumb
from ._huobi import Huobi


def create_markets(exchange_names):
    """
    [
        'Bitfinex_BCH_BTC'
        ...
    ]
    """
    markets = {}
    for name in exchange_names:
        if name == "%s_ETH_USD" % constant.EX_BFX:
            ex = Bitfinex('ethusd')
        elif name == "%s_ETC_BTC" % constant.EX_BFX:
            ex = Bitfinex('etcbtc')
        elif name == "%s_ETC_USD" % constant.EX_BFX:
            ex = Bitfinex('etcusd')
        elif name == "%s_ETH_BTC" % constant.EX_BFX:
            ex = Bitfinex('ethbtc')
        elif name == "%s_BCH_USD" % constant.EX_BFX:
            ex = Bitfinex('bchusd')
        elif name == "%s_ZEC_USD" % constant.EX_BFX:
            ex = Bitfinex('zecusd')
        elif name == "%s_BCH_BTC" % constant.EX_BFX:
            ex = Bitfinex('bchbtc')
        elif name == "%s_BTC_USD" % constant.EX_BFX:
            ex = Bitfinex('btcusd')
        elif name == "%s_BT1_USD" % constant.EX_BFX:
            ex = Bitfinex('bt1usd')
        elif name == "%s_BT2_USD" % constant.EX_BFX:
            ex = Bitfinex('bt2usd')
        elif name == "%s_BT1_BTC" % constant.EX_BFX:
            ex = Bitfinex('bt1btc')
        elif name == "%s_BT2_BTC" % constant.EX_BFX:
            ex = Bitfinex('bt2btc')
        elif name == "%s_EOS_USD" % constant.EX_BFX:
            ex = Bitfinex('eosusd')
        elif name == "%s_EOS_BTC" % constant.EX_BFX:
            ex = Bitfinex('eosbtc')
        elif name == "%s_EOS_ETH" % constant.EX_BFX:
            ex = Bitfinex('eoseth')
        elif name == "%s_NEO_BTC" % constant.EX_BFX:
            ex = Bitfinex('neobtc')
        elif name == "%s_NEO_ETH" % constant.EX_BFX:
            ex = Bitfinex('neoeth')
        elif name == "%s_NEO_USD" % constant.EX_BFX:
            ex = Bitfinex('neousd')
        elif name == "%s_IOT_USD" % constant.EX_BFX:
            ex = Bitfinex('iotusd')
        elif name == "%s_IOT_BTC" % constant.EX_BFX:
            ex = Bitfinex('iotbtc')
        elif name == "%s_ZRX_ETH" % constant.EX_BFX:
            ex = Bitfinex('zrxeth')
        elif name == "%s_ZRX_BTC" % constant.EX_BFX:
            ex = Bitfinex('zrxbtc')
        elif name == "%s_BCH_BTC" % constant.EX_KKEX:
            ex = Kkex('BCHBTC')
        elif name == "%s_BCC_BTC" % constant.EX_LQ:
            ex = Liqui('bcc_btc')
        elif name == "%s_BCC_ETH" % constant.EX_LQ:
            ex = Liqui('bcc_eth')
        elif name == "%s_EOS_BTC" % constant.EX_LQ:
            ex = Liqui('eos_btc')
        elif name == "%s_BCC_BTC" % constant.EX_HITBITC:
            ex = Hitbtc('bccbtc')
        elif name == "%s_BCC_BTC" % constant.EX_CEX:
            ex = Cex('bccbtc')
        elif name == "%s_ZEC_BTC" % constant.EX_BITTREX:
            ex = Bittrex('BTC-ZEC')
        elif name == "%s_BTC_USDT" % constant.EX_BINANCE:
            ex = Binance('BTCUSDT')
        elif name == "%s_BCC_BTC" % constant.EX_BINANCE:
            ex = Binance('BCCBTC')
        elif name == "%s_ETH_BTC" % constant.EX_BINANCE:
            ex = Binance('ETHBTC')
        elif name == "%s_ETH_USDT" % constant.EX_BINANCE:
            ex = Binance('ETHUSDT')
        elif name == "%s_BNB_BTC" % constant.EX_BINANCE:
            ex = Binance('BNBBTC')
        elif name == "%s_BNB_ETH" % constant.EX_BINANCE:
            ex = Binance('BNBETH')
        elif name == "%s_MCO_BTC" % constant.EX_BINANCE:
            ex = Binance('MCOBTC')
        elif name == "%s_MCO_ETH" % constant.EX_BINANCE:
            ex = Binance('MCOETH')
        elif name == "%s_QTUM_BTC" % constant.EX_BINANCE:
            ex = Binance('QTUMBTC')
        elif name == "%s_QTUM_ETH" % constant.EX_BINANCE:
            ex = Binance('QTUMETH')
        elif name == "%s_WTC_BTC" % constant.EX_BINANCE:
            ex = Binance('WTCBTC')
        elif name == "%s_WTC_ETH" % constant.EX_BINANCE:
            ex = Binance('WTCETH')
        elif name == "%s_NEO_BTC" % constant.EX_BINANCE:
            ex = Binance('NEOBTC')
        elif name == "%s_NEO_ETH" % constant.EX_BINANCE:
            ex = Binance('NEOETH')
        elif name == "%s_IOTA_ETH" % constant.EX_BINANCE:
            ex = Binance('IOTAETH')
        elif name == "%s_IOTA_BTC" % constant.EX_BINANCE:
            ex = Binance('IOTABTC')
        elif name == "%s_ZRX_BTC" % constant.EX_BINANCE:
            ex = Binance('ZRXBTC')
        elif name == "%s_ZRX_ETH" % constant.EX_BINANCE:
            ex = Binance('ZRXETH')
        elif name == "%s_ETH_BTC" % constant.EX_GATE:
            ex = Gate('eth_btc')
        elif name == "%s_BCC_BTC" % constant.EX_GATE:
            ex = Gate('bcc_btc')
        elif name == "%s_BTC_JPY" % constant.EX_BITFLYER:
            ex = Bitflyer('btc_jpy')
        elif name == "%s_ETH_BTC" % constant.EX_BITFLYER:
            ex = Bitflyer('eth_btc')
        elif name == "%s_BCH_BTC" % constant.EX_BITFLYER:
            ex = Bitflyer('bch_btc')
        elif name == "%s_ETH_EUR" % constant.EX_KRAKEN:
            ex = Kraken('etheur')
        elif name == "%s_ETH_USD" % constant.EX_KRAKEN:
            ex = Kraken('ethusd')
        elif name == "%s_BCH_EUR" % constant.EX_KRAKEN:
            ex = Kraken('bcheur')
        elif name == "%s_BCH_USD" % constant.EX_KRAKEN:
            ex = Kraken('bchusd')
        elif name == "%s_XBT_EUR" % constant.EX_KRAKEN:
            ex = Kraken('xbteur')
        elif name == "%s_XBT_USD" % constant.EX_KRAKEN:
            ex = Kraken('xbtusd')
        elif name == "%s_EOS_EUR" % constant.EX_KRAKEN:
            ex = Kraken('eoseur')
        elif name == "%s_EOS_USD" % constant.EX_KRAKEN:
            ex = Kraken('eosusd')
        elif name == "%s_BCC_BTC" % constant.EX_COINEGG:
            ex = Coinegg('bcc')
        elif name == "%s_ETH_BTC" % constant.EX_COINEGG:
            ex = Coinegg('eth')
        elif name == "%s_NEO_BTC" % constant.EX_COINEGG:
            ex = Coinegg('neo')
        elif name == "%s_ETC_BTC" % constant.EX_COINEGG:
            ex = Coinegg('etc')
        elif name == "%s_BTC_KRW" % constant.EX_BITHUMB:
            ex = Bithumb('btc')
        elif name == "%s_ETH_KRW" % constant.EX_BITHUMB:
            ex = Bithumb('eth')
        elif name == "%s_BCH_KRW" % constant.EX_BITHUMB:
            ex = Bithumb('bch')
        elif name == "%s_ETH_USDT" % constant.EX_HUOBI:
            ex = Huobi('ethusdt')
        elif name == "%s_BTC_USDT" % constant.EX_HUOBI:
            ex = Huobi('btcusdt')
        else:
            logging.warn('Exchange ' + name + ' not supported!')
            assert False
        ex.name = name

        logging.info('%s market initialized' % ex.name)

        markets[name] = ex
    return markets
