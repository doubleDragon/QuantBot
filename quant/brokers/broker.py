# Copyright (C) 2017, Philsong <songbohr@gmail.com>

import logging
import inspect

import time

from quant import config


def get_current_function_name():
    return inspect.stack()[1][3]


class TradeException(Exception):
    pass


class Broker(object):
    def __init__(self, base_currency, market_currency, pair_code):
        self.name = self.__class__.__name__
        self.brief_name = self.name[6:]

        self.base_currency = base_currency
        self.market_currency = market_currency
        self.pair_code = pair_code

        self.cny_balance = 0.
        self.cny_available = 0.

        self.btc_balance = 0.
        self.btc_available = 0.

        self.bch_balance = 0.
        self.bch_available = 0.

        self.zec_balance = 0.
        self.zec_available = 0.

        self.usd_balance = 0.
        self.usd_available = 0.

    def __str__(self):
        return "%s: %s" % (self.brief_name, str({"cny_balance": self.cny_balance,
                                                 "cny_available": self.cny_available,
                                                 "btc_balance": self.btc_balance,
                                                 "btc_available": self.btc_available,
                                                 "bch_balance": self.bch_balance,
                                                 "bch_available": self.bch_available,
                                                 "zec_balance": self.zec_balance,
                                                 "zec_available": self.zec_available,
                                                 "usd_balance": self.usd_balance,
                                                 "usd_available": self.usd_available
                                                 }))

    def buy_limit_c(self, amount, price, client_id=None):
        while True:
            order_id = self.buy_limit(amount, price, client_id)
            if order_id:
                break
            time.sleep(config.INTERVAL_API)
        return order_id

    def buy_limit(self, amount, price, client_id=None):
        if amount > config.RISK_PROTECT_MAX_VOLUMN:
            logging.error('risk alert: amount %s > risk amount:%s' % (amount, config.RISK_PROTECT_MAX_VOLUMN))
            raise

        logging.info("BUY LIMIT %f %s at %f %s @%s" % (amount, self.market_currency,
                                                       price, self.base_currency, self.brief_name))

        try:
            if client_id:
                return self._buy_limit(amount, price, client_id)
            else:
                return self._buy_limit(amount, price)
        except Exception as e:
            logging.error('%s %s except: %s' % (self.name, get_current_function_name(), e))
            return None

    def sell_limit_c(self, amount, price, client_id=None):
        while True:
            order_id = self.sell_limit(amount, price, client_id)
            if order_id:
                break
            time.sleep(config.INTERVAL_API)
        return order_id

    def sell_limit(self, amount, price, client_id=None):
        if amount > config.RISK_PROTECT_MAX_VOLUMN:
            logging.error('risk alert: amount %s > risk amount:%s' % (amount, config.RISK_PROTECT_MAX_VOLUMN))
            raise

        logging.info("SELL LIMIT %f %s at %f %s @%s" % (amount, self.market_currency,
                                                        price, self.base_currency, self.brief_name))

        try:
            if client_id:
                return self._sell_limit(amount, price, client_id)
            else:
                return self._sell_limit(amount, price)
        except Exception as e:
            logging.error('%s %s except: %s' % (self.name, get_current_function_name(), e))
            return None

    def buy_maker(self, amount, price):
        if amount > config.RISK_PROTECT_MAX_VOLUMN:
            logging.error('risk alert: amount %s > risk amount:%s' % (amount, config.RISK_PROTECT_MAX_VOLUMN))
            raise

        logging.info("BUY MAKER %f %s at %f %s @%s" % (amount, self.market_currency,
                                                       price, self.base_currency, self.brief_name))

        try:
            return self._buy_maker(amount, price)
        except Exception as e:
            logging.error('%s %s except: %s' % (self.name, get_current_function_name(), e))
            return None

    def sell_maker(self, amount, price):
        if amount > config.RISK_PROTECT_MAX_VOLUMN:
            logging.error('risk alert: amount %s > risk amount:%s' % (amount, config.RISK_PROTECT_MAX_VOLUMN))
            raise

        logging.info("SELL MAKER %f %s at %f %s @%s" % (amount, self.market_currency,
                                                        price, self.base_currency, self.brief_name))
        try:
            return self._sell_maker(amount, price)
        except Exception as e:
            logging.error('%s %s except: %s' % (self.name, get_current_function_name(), e))
            return None

    def get_order(self, order_id, order_type=None):
        """
        bithumb must exist order_type, bid or ask
        """
        if not order_id:
            return None

        try:
            return self._get_order(order_id, order_type)
        except Exception as e:
            logging.error('%s %s except: %s' % (self.name, get_current_function_name(), e))
            return None

    def cancel_order(self, order_id, currency=None, order_type=None):
        if not order_id:
            return None

        try:
            return self._cancel_order(order_id, currency, order_type)
        except Exception as e:
            logging.error('%s %s except: %s' % (self.name, get_current_function_name(), e))

            return None

    def get_orders(self, order_ids):
        try:
            return self._get_orders(order_ids)
        except Exception as e:
            logging.error('%s %s except: %s' % (self.name, get_current_function_name(), e))
            return None

    def get_orders_history(self):
        try:
            return self._get_orders_history()
        except Exception as e:
            logging.error('%s %s except: %s' % (self.name, get_current_function_name(), e))
            return None

    def get_balances(self):
        try:
            res = self._get_balances()
        except Exception as e:
            logging.error('%s %s except: %s' % (self.name, get_current_function_name(), e))
            return None
        return res

    def cancel_all(self):
        try:
            res = self._cancel_all()
        except Exception as e:
            logging.error('%s %s except: %s' % (self.name, get_current_function_name(), e))
            return None
        return res

    def get_ticker_c(self):
        while True:
            res = self.get_ticker()
            if res:
                break
            time.sleep(config.INTERVAL_API)
        return res

    def get_ticker(self):
        try:
            res = self._ticker()
        except Exception as e:
            logging.error('%s %s except: %s' % (self.name, get_current_function_name(), e))
            return None
        return res

    def _buy_limit(self, amount, price):
        raise NotImplementedError("%s.buy(self, amount, price)" % self.name)

    def _sell_limit(self, amount, price):
        raise NotImplementedError("%s.sell(self, amount, price)" % self.name)

    def _buy_maker(self, amount, price):
        raise NotImplementedError("%s.buy_maker(self, amount, price)" % self.name)

    def _sell_maker(self, amount, price):
        raise NotImplementedError("%s.sell_maker(self, amount, price)" % self.name)

    def _get_order(self, order_id, order_type=None):
        raise NotImplementedError("%s.get_order(self, order_id)" % self.name)

    def _cancel_order(self, order_id, currency=None, order_type=None):
        raise NotImplementedError("%s.cancel_order(self, order_id)" % self.name)

    def _get_orders(self, order_ids):
        raise NotImplementedError("%s.get_orders(self, order_ids)" % self.name)

    def _get_orders_history(self):
        raise NotImplementedError("%s._get_orders_history(self)" % self.name)

    def _cancel_all(self):
        raise NotImplementedError("%s.cancel_all(self)" % self.name)

    def deposit(self):
        raise NotImplementedError("%s.deposit(self)" % self.name)

    def withdraw(self, amount, address):
        raise NotImplementedError("%s.withdraw(self, amount, address)" % self.name)

    def _get_balances(self):
        raise NotImplementedError("%s.get_balances(self)" % self.name)

    def _ticker(self):
        raise NotImplementedError("%s.ticker(self)" % self.name)

    def test(self):
        raise
