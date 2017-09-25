#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import requests

BASE_URL = 'https://api.hitbtc.com/api/1'
TIMEOUT = 5


class PublicClient(object):
    def __init__(self):
        super(PublicClient, self).__init__()

    @classmethod
    def _build_parameters(cls, parameters):
        # sort the keys so we can test easily in Python 3.3 (dicts are not
        # ordered)
        keys = list(parameters.keys())
        keys.sort()

        return '&'.join(["%s=%s" % (k, parameters[k]) for k in keys])

    def url_for(self, path, path_arg=None, parameters=None):

        # build the basic url
        url = "%s/%s" % (BASE_URL, path)

        # If there is a path_arh, interpolate it into the URL.
        # In this case the path that was provided will need to have string
        # interpolation characters in it, such as PATH_TICKER
        if path_arg:
            url = url % (path_arg)

        # Append any parameters to the URL.
        if parameters:
            url = "%s?%s" % (url, self._build_parameters(parameters))

        return url

    @classmethod
    def _get(cls, url, params=None):
        try:
            resp = requests.get(url, timeout=TIMEOUT, params=params)
        except requests.exceptions.RequestException as e:
            raise e
        else:
            if resp.status_code == requests.codes.ok:
                return resp.json()

    def depth(self, symbol):
        url = self.url_for("public/%s/orderbook" % symbol)
        return self._get(url)
