#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# python -m quant.example.ex_coinegg

from quant.api.coinegg import PublicClient

client = PublicClient()
print(client.ticker('bcc'))
# print(client.depth('bcc'))
