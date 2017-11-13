#!/usr/bin/env python
# -*- coding: UTF-8 -*-


from quant import config
from quant.api.bithumb import PrivateClient

client = PrivateClient(config.Bithumb_API_KEY, config.Bithumb_SECRET_TOKEN)

print(client.account())
print(client.balance('bch'))
