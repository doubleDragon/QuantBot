#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from quant import config
from quant.api.kkex import PrivateClient

client = PrivateClient(config.KKEX_API_KEY, config.KKEX_SECRET_TOKEN)
print(client.depth('BCCBTC'))

print(client.profile())
