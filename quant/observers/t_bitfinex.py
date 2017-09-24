# Copyright (C) 2017, Phil Song <songbohr@gmail.com>

# python3 xrypto/cli.py -m Viabtc_BCH_CNY,Viabtc_BCH_BTC,Viabtc_BTC_CNY t-watch -v
import logging
import time

from quant import config
from quant.brokers import broker_factory
from .basicbot import BasicBot


class TrigangularArbitrer_Bitfinex(BasicBot):
    """
    base_pair='Viabtc_BCH_CNY',
    pair1='Viabtc_BCH_BTC',
    pair2='Viabtc_BTC_CNY'
    """

    def __init__(self, base_pair, pair1, pair2, monitor_only=False):
        super(TrigangularArbitrer_Bitfinex, self).__init__()
        self.base_pair = base_pair or 'Bitfinex_BCH_USD'
        self.pair_1 = pair1 or 'Bitfinex_BCH_BTC'
        self.pair_2 = pair2 or 'Bitfinex_BTC_USD'

        self.monitor_only = monitor_only

        self.brokers = broker_factory.create_brokers([self.base_pair, self.pair_1, self.pair_2])

        self.last_trade = 0

    def update_balance(self):
        self.brokers[self.base_pair].get_balances()

    def tick(self, depths):
        self.forward(depths)
        self.reverse(depths)

    @classmethod
    def is_depths_available(cls, depths):
        return len(depths) < 3

    def forward(self, depths):
        if not self.is_depths_available(depths):
            # logging.debug("depths is not available")
            return
        base_pair_ask_amount = depths[self.base_pair]['asks'][0]['amount']
        base_pair_ask_price = depths[self.base_pair]['asks'][0]['price']

        logging.info("base_pair: %s ask_price:%s" % (self.base_pair, base_pair_ask_price))

        pair1_bid_amount = depths[self.pair_1]['bids'][0]['amount']
        pair1_bid_price = depths[self.pair_1]['bids'][0]['price']

        pair2_bid_amount = depths[self.pair_2]['bids'][0]['amount']
        pair2_bid_price = depths[self.pair_2]['bids'][0]['price']

        if pair1_bid_price == 0:
            return

        pair_2to1_bch_amount = pair2_bid_amount / pair1_bid_price
        # print(pair2_bid_amount, pair1_bid_price, pair_2to1_bch_amount)

        max_trade_amount = config.bch_max_tx_volume
        hedge_bch_amount = min(base_pair_ask_amount, pair1_bid_amount)
        hedge_bch_amount = min(hedge_bch_amount, pair_2to1_bch_amount)
        hedge_bch_amount = min(max_trade_amount, hedge_bch_amount)

        if hedge_bch_amount < 0.05:
            logging.info('hedge_ bch _amount is too small! %s' % hedge_bch_amount)
            return

        hedge_btc_amount = hedge_bch_amount * pair1_bid_price
        if hedge_btc_amount < 0.01:
            logging.info('hedge_ btc _amount is too small! %s' % hedge_btc_amount)
            return

        synthetic_bid_price = round(pair1_bid_price * pair2_bid_price, 2)

        t_price = round(base_pair_ask_price * config.TFEE * config.Diff, 2)
        logging.info("synthetic_bid_price: %s t_price:%s" % (synthetic_bid_price, t_price))

        p_diff = synthetic_bid_price - t_price
        profit = p_diff * hedge_bch_amount

        if profit > 0:
            logging.info('profit=%0.4f, p_diff=%0.4f, bch=%s' % (profit, p_diff, hedge_bch_amount))
            logging.info("synthetic_bid_price: %s  base_pair_ask_price: %s t_price: %s" % (
                synthetic_bid_price,
                base_pair_ask_price,
                t_price))

            logging.info(
                'buy %s BCH @%s, sell BTC @synthetic: %s' % (self.base_pair, hedge_bch_amount, hedge_btc_amount))
            if profit < 10:
                logging.warn('profit should >= 10 CNY')
                return

            current_time = time.time()
            if current_time - self.last_trade < 5:
                logging.warn("Can't automate this trade, last trade " +
                             "occured %.2f seconds ago" %
                             (current_time - self.last_trade))
                return

            if not self.monitor_only:
                self.brokers[self.base_pair].buy_limit(hedge_bch_amount, base_pair_ask_price)
                self.brokers[self.pair_1].sell_limit(hedge_bch_amount, pair1_bid_price)
                self.brokers[self.pair_2].sell_limit(hedge_btc_amount, pair2_bid_price)

            self.last_trade = time.time()

    def reverse(self, depths):
        base_pair_bid_amount = depths[self.base_pair]['bids'][0]['amount']
        base_pair_bid_price = depths[self.base_pair]['bids'][0]['price']

        logging.info("base_pair: %s bid_price:%s" % (self.base_pair, base_pair_bid_price))

        pair1_ask_amount = depths[self.pair_1]['asks'][0]['amount']
        pair1_ask_price = depths[self.pair_1]['asks'][0]['price']

        pair2_ask_amount = depths[self.pair_2]['asks'][0]['amount']
        pair2_ask_price = depths[self.pair_2]['asks'][0]['price']

        if pair1_ask_price == 0 or pair2_ask_price == 0:
            return

        pair_2to1_bch_amount = pair2_ask_amount / pair1_ask_price
        # print(pair2_bid_amount, pair1_bid_price, pair_2to1_bch_amount)

        max_trade_amount = 0.1
        hedge_bch_amount = min(base_pair_bid_amount, pair1_ask_amount)
        hedge_bch_amount = min(hedge_bch_amount, pair_2to1_bch_amount)
        hedge_bch_amount = min(max_trade_amount, hedge_bch_amount)

        if hedge_bch_amount < 0.05:
            logging.info('hedge_ bch _amount is too small! %s' % hedge_bch_amount)
            return

        hedge_btc_amount = hedge_bch_amount * pair1_ask_price
        if hedge_btc_amount < 0.01:
            logging.info('hedge_ btc _amount is too small! %s' % hedge_btc_amount)
            return

        synthetic_ask_price = round(pair1_ask_price * pair2_ask_price, 2)

        t_price = round(base_pair_bid_price * config.TFEE * config.Diff, 2)
        logging.info("synthetic_ask_price: %s t_price:%s" % (synthetic_ask_price, t_price))

        p_diff = synthetic_ask_price - t_price

        profit = round(p_diff * hedge_bch_amount, 2)
        logging.info('profit=%s' % profit)

        if p_diff > 0:
            logging.info("find t!!!: p_diff:%s synthetic_ask_price: %s  base_pair_bid_price: %s t_price: %s" % (
                p_diff,
                synthetic_ask_price,
                base_pair_bid_price,
                t_price))

            logging.info(
                'r--sell %s BCH @%s, buy @synthetic: %s' % (self.base_pair, hedge_bch_amount, hedge_btc_amount))

            current_time = time.time()
            if current_time - self.last_trade < 10:
                logging.warn("Can't automate this trade, last trade " +
                             "occured %.2f seconds ago" %
                             (current_time - self.last_trade))
                return

            self.brokers[self.base_pair].sell_limit(hedge_bch_amount, base_pair_bid_price)
            self.brokers[self.pair_2].buy_limit(hedge_btc_amount, pair2_ask_price)
            self.brokers[self.pair_1].buy_limit(hedge_bch_amount, pair1_ask_price)

            self.last_trade = time.time()
