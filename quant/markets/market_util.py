#!/usr/bin/env python
# -*- coding: UTF-8 -*-


def sort_and_format_list(l, reverse=False):
    """
    {
        'asks': [
            [
                'price': 0,
                'amount': 0,
            ]
        ],
        'bids': [
            [
                'price': 0,
                'amount': 0,
            ]
        ]
    }
    """
    l.sort(key=lambda x: float(x[0]), reverse=reverse)
    r = []
    for i in l:
        r.append({'price': float(i[0]), 'amount': float(i[1])})
    return r


def sort_and_format_dict(l, reverse=False):
    """
    {
        'asks': [
            {
                'price': 0,
                'amount': 0,
            }
        ],
        'bids': [
            {
                'price': 0,
                'amount': 0,
            }
        ]
    }
    """
    l.sort(key=lambda x: float(x['price']), reverse=reverse)
    r = []
    for i in l:
        r.append({'price': float(i['price']), 'amount': float(i['amount'])})
    return r
