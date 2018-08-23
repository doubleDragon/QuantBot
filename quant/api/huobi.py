#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import base64
import hashlib
import hmac
import urllib
import urlparse

import requests
import json
import datetime

MARKET_URL = TRADE_URL = "https://api.huobi.pro"
TIMEOUT = 5

EXTRA_PUBLIC_HEADERS = {
    "Content-type": "application/x-www-form-urlencoded",
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'
}

# for private get
EXTRA_POST_HEADERS = {
    "Accept": "application/json",
    'Content-Type': 'application/json',
    "User-Agent": "Chrome/39.0.2171.71",
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'
}


class PublicClient(object):
    """
    https://github.com/huobiapi/API_Docs/wiki/REST_api_reference
    https://www.huobi.pro/zh-cn/about/fee/
    """

    def __init__(self):
        super(PublicClient, self).__init__()

    def symbols(self):
        """
        /* GET /v1/common/symbols */
        {
          "status": "ok",
          "data": [
            {
              "base-currency": "eth",
              "quote-currency": "usdt",
              "symbol": "ethusdt"
            }
            {
              "base-currency": "etc",
              "quote-currency": "usdt",
              "symbol": "etcusdt"
            }
          ]
        }
        """
        url = MARKET_URL + '/v1/common/symbols'
        params = {}
        return self._get(url, params)

    def depth(self, symbol, p_type='step1'):
        """
        :param symbol: ethbtc
        :param p_type: 可选值：{ percent10, step0, step1, step2, step3, step4, step5 }
        :return: resp
        """
        params = {'symbol': symbol,
                  'type': p_type}

        url = MARKET_URL + '/market/depth'
        return self._get(url, params)

    @classmethod
    def _get(cls, url, params, headers=None):
        if headers:
            headers.update(EXTRA_PUBLIC_HEADERS)
        else:
            headers = EXTRA_PUBLIC_HEADERS
        data = urllib.urlencode(params)
        try:
            resp = requests.get(url, data, headers=headers, timeout=TIMEOUT)
        except Exception as e:
            raise e
        else:
            return resp.json()


class PrivateClient(PublicClient):

    def __init__(self, access_key, access_secret):
        super(PrivateClient, self).__init__()
        self.access_key = access_key
        self.access_secret = access_secret

    @classmethod
    def _post(cls, url, params, headers=None):
        if headers:
            headers.update(EXTRA_POST_HEADERS)
        else:
            headers = EXTRA_POST_HEADERS
        data = json.dumps(params)
        try:
            resp = requests.post(url, data, headers=headers, timeout=TIMEOUT)
        except Exception as e:
            raise e
        else:
            return resp.json()

    def private_get(self, params, request_path):
        method = 'GET'

        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        params.update({'AccessKeyId': self.access_key,
                       'SignatureMethod': 'HmacSHA256',
                       'SignatureVersion': '2',
                       'Timestamp': timestamp})

        host_url = TRADE_URL
        host_name = urlparse.urlparse(host_url).hostname
        host_name = host_name.lower()

        params['Signature'] = self.create_sign(params, method, host_name, request_path, self.access_secret)
        url = host_url + request_path
        return self._get(url, params)

    @classmethod
    def create_sign(cls, p_params, method, host_url, request_path, secret_key):
        sorted_params = sorted(p_params.items(), key=lambda d: d[0], reverse=False)
        encode_params = urllib.urlencode(sorted_params)
        payload = [method, host_url, request_path, encode_params]
        payload = '\n'.join(payload)
        payload = payload.encode(encoding='UTF8')
        secret_key = secret_key.encode(encoding='UTF8')
        digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(digest)
        signature = signature.decode()
        return signature

    def get_accounts(self):
        """
        :return:
        """
        path = "/v1/account/accounts"
        params = {}
        return self.private_get(params, path)

    def get_balance(self, account_id):
        """
        account_id通过上面的get_accounts获取
        """
        url = "/v1/account/accounts/{0}/balance".format(account_id)
        params = {"account-id": account_id}
        return self.private_get(params, url)
