#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import requests


class Rate(object):
    def __init__(self):
        super(Rate, self).__init__()
        self.url = "http://api.fixer.io/latest"

    @classmethod
    def _get(cls, url, params=None):
        try:
            response = requests.get(url, timeout=5, params=params)
        except requests.exceptions.RequestException as e:
            print('quary rate failed: ' + str(e))
        else:
            if response.status_code == requests.codes.ok:
                return response.json()

    def query(self, base, target):
        params = {
            'base': base
        }
        resp = self._get(self.url, params)
        if resp and 'rates' in resp:
            return float(resp['rates'][target])
