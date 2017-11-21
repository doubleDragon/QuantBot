# 说明
避免每次都去observer copy执行参数，建一个脚本比较方便



# screen方式
screen执行一个bash脚本，bash脚本要给执行权限
```
screen -L -S bithumb bithumb_bch.sh
```

-L参数比较重要，加了后生成screenlog.x日志，
再配合traceback可以输出出错时具体的堆栈信息
```
traceback.print_exc()
```
