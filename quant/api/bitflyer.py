import requests


class PublicClient(object):
    """
    document: https://lightning.bitflyer.jp/docs
    """

    def __init__(self):
        self.public_url = "https://api.bitflyer.com/v1"

    def url_for(self, path):
        url = "%s/%s" % (self.public_url, path)
        return url

    @classmethod
    def _get(cls, url, params=None):
        try:
            response = requests.get(url, timeout=5, params=params)
        except requests.exceptions.RequestException as e:
            print('bitflyer get' + url + ' failed: ' + str(e))
        else:
            if response.status_code == requests.codes.ok:
                return response.json()

    def depth(self, symbol):
        """
        https://api.bitflyer.com/v1/getboard?product_code=eth_btc
        """
        params = {
            'product_code': symbol
        }
        return self._get(self.url_for('getboard'), params)

    def ticker(self, symbol):
        """
        https://api.bitflyer.com/v1/getticker?product_code=eth_btc
        """
        params = {
            'product_code': symbol
        }
        return self._get(self.url_for('getticker'), params)
