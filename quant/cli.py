#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import argparse
import logging
from logging.handlers import RotatingFileHandler

from quant.datafeed import DataFeed
from quant.observers.t_bitfinex import TrigangularArbitrer_Bitfinex
from quant.observers.triangle_arbitrage import TriangleArbitrage


class CLI(object):
    def __init__(self):
        super(CLI, self).__init__()
        self.data_feed = None

    @classmethod
    def init_logger(cls, args):
        level = logging.INFO
        if args.verbose:
            level = logging.INFO
        if args.debug:
            level = logging.DEBUG

        logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',
                            level=level)

        rt_handler = RotatingFileHandler('quant.log', maxBytes=100 * 1024 * 1024, backupCount=10)
        rt_handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)-12s [%(levelname)s] %(message)s')
        rt_handler.setFormatter(formatter)
        logging.getLogger('').addHandler(rt_handler)

        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

    def exec_command(self, args):
        logging.debug('exec_command:%s' % args)

        # if "replay-history" in args.command:
        #     self.create_arbitrer(args)
        #     self.arbitrer.replay_history(args.replay_history)
        #     return
        # if "get-balance" in args.command:
        #     self.get_balance(args)
        #     return
        # if "list-public-markets" in args.command:
        #     self.list_markets()
        #     return
        # if "get-broker-balance" in args.command:
        #     self.get_broker_balance(args)
        #     return
        # if "test_pub" in args.command:
        #     self.test_pub(args)
        #     return
        # if "test_pri" in args.command:
        #     self.test_pri(args)
        #     return

        # if "b-watch" in args.command:
        #     self.create_arbitrer(args)
        # else:
        #     self.create_datafeed(args)
        #
        #     # special tranglar observer
        #     if "t-watch-viabtc-bcc" in args.command:
        #         self.register_t_viabtc_bcc(args)
        #
        #     if "t-watch-binance-wtc" in args.command:
        #         self.register_t_binance_wtc(args)
        #
        #     if "t-watch-binance-bnb" in args.command:
        #         self.register_t_binance_bnb(args)
        #
        #     if "t-watch-binance-mco" in args.command:
        #         self.register_t_binance_mco(args)
        #
        #     if "t-watch-binance-qtum" in args.command:
        #         self.register_t_binance_qtum(args)

        if "b-watch" in args.command:
            pass
        else:
            self.create_data_feed(args)
            if "t-watch-bitfinex-bch" in args.command:
                self.register_t_bitfinex_bcc()
            if "t-watch-triangle-arbitrage" in args.command:
                self.register_t_triangle_arbitrage()

        self.data_feed.run_loop()

    def register_t_triangle_arbitrage(self):
        _observer = TriangleArbitrage(monitor_only=True)
        self.data_feed.register_observer(_observer)

    def register_t_bitfinex_bcc(self):
        _observer = TrigangularArbitrer_Bitfinex(base_pair='Bitfinex_BCH_USD',
                                                 pair1='Bitfinex_BCH_BTC',
                                                 pair2='Bitfinex_BTC_USD',
                                                 monitor_only=True)
        self.data_feed.register_observer(_observer)

    def create_data_feed(self, args):
        self.data_feed = DataFeed()
        self.init_observers_and_markets(args)

    def init_observers_and_markets(self, args):
        if args.observers:
            self.data_feed.init_observers(args.observers.split(","))
        if args.markets:
            self.data_feed.init_markets(args.markets.split(","))

    def main(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-d", "--debug", help="debug verbose mode",
                            action="store_true")
        parser.add_argument("-v", "--verbose", help="info verbose mode",
                            action="store_true")
        parser.add_argument("-o", "--observers", type=str,
                            help="observers, example: -oLogger,Emailer")
        parser.add_argument("-m", "--markets", type=str,
                            help="markets, example: -mHaobtcCNY,Bitstamp")
        parser.add_argument("-s", "--status", help="status", action="store_true")
        parser.add_argument("command", nargs='*', default="watch",
                            help='verb: "watch|replay-history|get-balance|list-public-markets|get-broker-balance"')
        args = parser.parse_args()
        self.init_logger(args)
        self.exec_command(args)
        print('main end')
        exit(-1)


def main():
    cli = CLI()
    cli.main()


if __name__ == "__main__":
    main()
