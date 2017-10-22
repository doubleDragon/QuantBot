#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import requests


class PublicClient(object):
    def __init__(self):
        super(PublicClient, self).__init__()
        self.base_url = "https://api.kraken.com/0/public"

    def _url_for(self, path):
        return "%s/%s" % (self.base_url, path)

    @classmethod
    def _get(cls, url, params=None):
        try:
            response = requests.get(url, timeout=5, params=params)
        except requests.exceptions.RequestException as e:
            print('kraken get' + url + ' failed: ' + str(e))
        else:
            if response.status_code == requests.codes.ok:
                return response.json()

    def depth(self, symbol, count=5):
        path = "Depth"
        params = {
            'count': count,
            'pair': symbol
        }
        url = self._url_for(path)
        return self._get(url, params)
