#!/usr/bin/env python
# -*- coding: UTF-8 -*-


from quant.api.kkex import PublicClient

client = PublicClient()
print(client.depth('BCCBTC'))