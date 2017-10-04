#!/usr/bin/env python
# -*- coding: UTF-8 -*-


def convert_currency_bfx(currency):
    currency = currency.lower()
    if currency == "dash":
        currency = "dsh"
    if currency == "bcc":
        currency = "bch"
    if currency == "iota":
        currency = 'iot'
    return currency.upper()
