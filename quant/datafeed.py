#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import config
import time
import logging
from concurrent.futures import ThreadPoolExecutor, wait
import traceback

import sys
import signal

from quant.tool import email_box

from markets.market_factory import create_markets

is_sigint_up = False


def sigint_handler(signum, frame):
    global is_sigint_up
    is_sigint_up = True
    print ('catched interrupt signal!')


class DataFeed(object):
    def __init__(self):
        self.markets = []
        self.market_names = []
        self.observers = []
        self.observer_names = []
        self.depths = {}
        self.init_markets(config.markets)
        self.init_observers(config.observers)
        self.thread_pool = ThreadPoolExecutor(max_workers=10)

    def init_markets(self, _markets):
        logging.debug("init_markets:%s" % _markets)
        self.market_names = _markets
        markets_dict = create_markets(_markets)

        for market_name, market in markets_dict.items():
            if self.get_market(market_name):
                continue
            self.markets.append(market)

    def init_observers(self, _observers):
        logging.debug("init_observers:%s" % _observers)

        self.observer_names = _observers
        for observer_name in _observers:
            try:
                exec ('import observers.' + observer_name.lower())
                observer = eval('observers.' + observer_name.lower() + '.' +
                                observer_name + '()')
                self.observers.append(observer)
            except (ImportError, AttributeError) as e:
                print("%s observer name is invalid: Ignored (you should check your config file)" % observer_name)
                print(e)

    def register_observer(self, _observer):
        logging.debug("register_observer:%s" % _observer)
        self.observers.append(_observer)

    def get_market(self, market_name):
        for market in self.markets:
            if market.name == market_name:
                return market

        return None

    def observer_tick(self):
        for observer in self.observers:
            observer.tick(self.depths)

    def tick(self):
        self.print_tickers()

        self.observer_tick()

    @classmethod
    def __get_market_depth(cls, market, depths):
        depth = market.get_depth()
        if depth:
            depths[market.name] = depth

    def update_depths(self):
        # depths = {}
        depths = {}
        futures = []

        for market in self.markets:
            futures.append(self.thread_pool.submit(self.__get_market_depth, market, depths))
        # wait(futures, timeout=20)
        wait(futures, timeout=3)
        return depths

    def print_tickers(self):
        for market in self.markets:
            logging.debug("ticker: " + market.name + " - " + str(market.get_ticker()))

    def replay_history(self, directory):
        import os
        import json
        files = os.listdir(directory)
        files.sort()
        for f in files:
            depths = json.load(open(directory + '/' + f, 'r'))
            self.depths = {}
            for market in self.market_names:
                if market in depths:
                    self.depths[market] = depths[market]
            self.tick()

    def update_balance(self):
        for observer in self.observers:
            observer.update_balance()

    def update_other(self):
        for observer in self.observers:
            observer.update_other()

    def terminate(self):
        for observer in self.observers:
            observer.terminate()

        for market in self.markets:
            market.terminate()

    def run_loop(self):
        if len(self.markets) == 0:
            print('empty markets')
            return

        if len(self.observers) == 0:
            print('empty observers')
            return
        #
        signal.signal(signal.SIGINT, sigint_handler)
        # 以下那句在windows python2.4不通过,但在freebsd下通过
        signal.signal(signal.SIGHUP, sigint_handler)
        signal.signal(signal.SIGTERM, sigint_handler)

        while True:
            self.update_balance()

            self.update_other()
            self.depths = self.update_depths()

            try:

                self.tick()
            except Exception as ex:
                logging.warn("datafeed exception:%s" % ex)
                traceback.print_exc()
                email_box.send_mail("datafeed exception:%s" % ex)
                self.terminate()
                return

            if is_sigint_up:
                # 中断时需要处理的代码
                logging.info("APP Exit")
                self.terminate()
                break
            sys.stdout.write(".\n\n")
            sys.stdout.flush()
            time.sleep(config.refresh_rate)
