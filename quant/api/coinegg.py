import requests


class PublicClient(object):
    """
    https://www.coinegg.com/explain.api.html#three-one
    """

    def __init__(self):
        self.public_url = "https://www.coinegg.com/api/v1"

    def url_for(self, path):
        url = "%s/%s" % (self.public_url, path)
        return url

    @classmethod
    def _get(cls, url, params=None):
        try:
            response = requests.get(url, timeout=5, params=params)
        except requests.exceptions.RequestException as e:
            print('coinegg get' + url + ' failed: ' + str(e))
        else:
            if response.status_code == requests.codes.ok:
                return response.json()

    def depth(self, currency):
        """
        https://www.coinegg.com/api/v1/depth?coin=eth
        """
        params = {
            'coin': currency
        }
        return self._get(self.url_for('depth'), params)

    def ticker(self, currency):
        """
        https://www.coinegg.com/api/v1/ticker?coin=eth
        """
        params = {
            'coin': currency
        }
        return self._get(self.url_for('ticker'), params)
