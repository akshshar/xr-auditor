#!/usr/bin/env python

import logging
from logging.handlers import RotatingFileHandler
import time

log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

logFile = '/misc/app_host/dummy_log'

my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=1024*1024, 
                                 backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.INFO)

app_log = logging.getLogger('compliance')
app_log.setLevel(logging.INFO)

app_log.addHandler(my_handler)

app_log.info("Hello World")
