#!/usr/bin/env python
# -*- coding: UTF-8 -*-


import requests


class PublicClient(object):

    """
    https://www.bithumb.com/u1/US127
    """

    def __init__(self):
        super(PublicClient, self).__init__()
        self.public_url = 'https://api.bithumb.com/public'

    def _build_public(self, path):
        return "%s/%s" % (self.public_url, path)

    @classmethod
    def _get(cls, url, params=None):
        try:
            response = requests.get(url, timeout=5, params=params)
        except requests.exceptions.RequestException as e:
            print('bithumb get' + url + ' failed: ' + str(e))
        else:
            if response.status_code == requests.codes.ok:
                return response.json()

    def ticker(self, currency):
        """
        https://api.bithumb.com/public/ticker/eth
        """
        path = "ticker/%s" % currency
        url = self._build_public(path)

        return self._get(url)

    def depth(self, currency):
        """
        这里的currency指的是market_currency, base_currency为krw
        https://api.bithumb.com/public/orderbook/eth
        :param currency: eth
        "data": {
            "timestamp": "1510145644014",
            "payment_currency": "KRW",
            "order_currency": "ETH",
            "bids": [
                {
                "quantity": "81.46910000",
                "price": "336500"
                },
                {
                "quantity": "9.45210000",
                "price": "336450"
                }
            ],
            "asks": [
                {
                "quantity": "10.04779881",
                "price": "336750"
                },
                {
                "quantity": "50.00000000",
                "price": "336800"
                }
            ]
        }
        """
        path = "orderbook/%s" % currency
        url = self._build_public(path)

        params = {
            'count': 5
        }
        return self._get(url, params)

