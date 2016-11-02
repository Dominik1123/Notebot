import datetime

import tinydb

import config

db = tinydb.TinyDB(config.config['savemoney.db.path'])


def savemoney(amount):
    db.insert({'timestamp': str(datetime.datetime.now()), 'amount': amount})


def get_all_records():
    query = tinydb.Query()
    return db.search(query.id >= 0)
