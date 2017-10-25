#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import logging
from logging.handlers import RotatingFileHandler


def get_logger(log_name, level=logging.DEBUG):
    """
    日志的疯转
    :param level: 日志级别
    :param log_name: 日志对象名
    :return: 日志对象名
    """
    logger = logging.getLogger(log_name)

    logger.setLevel(level)

    rt_handler = RotatingFileHandler(log_name, maxBytes=100 * 1024 * 1024, backupCount=10)
    rt_handler.setLevel(level)
    formatter = logging.Formatter('%(asctime)-12s [%(levelname)s] %(message)s')
    rt_handler.setFormatter(formatter)
    logger.addHandler(rt_handler)
    return logger
