import datetime

import tinydb

import config

db = tinydb.TinyDB(config.config['savemoney.db.path'])


def savemoney(amount):
    db.insert({'timestamp': str(datetime.datetime.now()), 'amount': amount})
