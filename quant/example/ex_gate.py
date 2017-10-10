#!/usr/bin/env python
# -*- coding: UTF-8 -*-


from quant.api.gate import PublicClient

client = PublicClient()
print(client.depth('eth_btc'))
