# coding=utf-8

"""
ORDER_STATE_PENDING	:未完成
ORDER_STATE_CLOSED	:已关闭
ORDER_STATE_CANCELED:已取消


ticker数据结构如下:
{
    sell: 0.5,
    buy: 0.5,
    last: 0.5
}
"""

ORDER_STATE_PENDING = 1
ORDER_STATE_CLOSED = 2
ORDER_STATE_CANCELED = 4
ORDER_STATE_UNKNOWN = 8

EX_OKEX = 'Okex'
EX_BFX = 'Bitfinex'
EX_LQ = 'Liqui'
EX_GDAX = 'Gdax'
EX_BINANCE = 'Binance'
EX_CEX = 'Cex'
EX_EXMO = 'Exmo'
EX_KKEX = 'Kkex'
EX_HITBITC = 'Hitbtc'
EX_BITTREX = 'Bittrex'
EX_GATE = 'Gate'
EX_BITFLYER = 'Bitflyer'
EX_KRAKEN = 'Kraken'
EX_COINEGG = 'Coinegg'
EX_BITHUMB = 'Bithumb'
EX_HUOBI = 'Huobi'


EX_SET = (
    EX_OKEX,
    EX_BFX,
    EX_LQ,
    EX_GDAX,
    EX_BINANCE,
    EX_CEX,
    EX_EXMO,
    EX_BITTREX,
    EX_BITFLYER,
    EX_KRAKEN,
    EX_COINEGG,
    EX_BITHUMB
)

"""
lq 要用到的错误码
832: 卖的时候币不够了
831: 买的时候btc不够了
"""
CODE_LQ_SELL_NOT_ENOUGH = 832
CODE_LQ_BUY_NOT_ENOUGH = 831
