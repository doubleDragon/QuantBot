#!/usr/bin/env python
# -*- coding: UTF-8 -*-


from quant.api.kraken import PublicClient

client = PublicClient()
print(client.depth('BCHEUR'))
