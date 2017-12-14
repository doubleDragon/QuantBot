#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from email.mime.text import MIMEText
from quant import config
import smtplib

mail_to = ["aiai373824745_wy@163.com"]
mail_host = "smtp.163.com"
mail_user = "aiai373824745_wy@163.com"
'''163邮箱smtp生成的密码'''
mail_pass = config.EMAIL_PASSWORD_163
mail_subject = 'logging'


def send_mail(content):
    pass
    # me = "QuantBot" + "<" + mail_user + ">"
    # msg = MIMEText(_text=content, _subtype='plain', _charset='utf-8')
    # msg['Subject'] = mail_subject
    # msg['From'] = me
    # msg['To'] = ";".join(mail_to)
    # try:
    #     server = smtplib.SMTP()
    #     server.connect(mail_host)
    #     server.login(mail_user, mail_pass)
    #     server.sendmail(me, mail_to, msg.as_string())
    #     server.close()
    #     return True
    # except Exception as e:
    #     print (e)
    #     return False


if __name__ == '__main__':
    # for test
    send_mail('content')
