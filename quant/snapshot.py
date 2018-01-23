import os
import time


class Snapshot(object):
    """docstring for ClassName"""

    def __init__(self):
        super(Snapshot, self).__init__()

    @classmethod
    def _snapshot(cls, filename, header, body):
        _path = './snapshot' + filename
        need_header = False

        if not os.path.exists(_path):
            need_header = True

        fp = open(_path, 'a+')

        if need_header:
            fp.write(header)

        fp.write(body)
        fp.close()

    def snapshot_balance(self, market, total_btc, total_bch, total_eth, total_zrx):
        filename = 'snapshot_%s_balance.csv' % market
        header = "localtime, timestamp, total_btc, total_bch, total_eth, total_zrx\n"

        localtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        timestamp = time.time()

        body = "%s, %s, %.4f, %.2f, %.2f, %.2f\n" % (localtime, timestamp, total_btc, total_bch, total_eth, total_zrx)

        self._snapshot(filename, header, body)

        # if market == "ALL":
        #     body = ("localtime=%s, total_btc=%0.4f, total_bch=%0.4f") % (localtime, total_btc, total_bch)
        #     send_email('xrypto balance snapshot', body)
