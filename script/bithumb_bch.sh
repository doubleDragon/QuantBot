#!/bin/bash

base_dir=/Users/wsl/workspace/python/QuantBot
cd $base_dir/log
rm -rf *.log

cd $base_dir
rm -rf screenlog.*
./venv/bin/python -m quant.cli -mBithumb_BCH_KRW,Bitfinex_BCH_BTC,Bithumb_BTC_KRW -o=T_Bithumb_BCH -f=bithumb_bch -v
