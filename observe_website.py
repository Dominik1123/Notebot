import datetime
import requests
import threading
import time

from config import config


class Observer(threading.Thread):
    def __init__(self, bot, chat_ids):
        super(Observer, self).__init__()

        self.bot = bot
        self.chat_ids = chat_ids

    def run(self):
        year, month = datetime.datetime.now().year, datetime.datetime.now().month
        day = datetime.datetime.now().day
        not_avail_content = config['website.content.not_available']

        while day <= 31:
            # Skip Saturdays and Sundays.
            if datetime.datetime(year, month, day).weekday() in (5, 6):
                day += 1
                continue
            url = config['website.url.template'] % day
            print 'Trying %s' % url
            response = requests.get(url, verify=False)
            while not_avail_content in response.text:
                time.sleep(30)
                response = requests.get(url, verify=False)
            self.notify(url)
            day += 1

    def notify(self, url):
        message = 'Website content is now available :)\n%s' % url
        for chat_id in self.chat_ids:
            self.bot.sendMessage(chat_id, message)
