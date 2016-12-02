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
        day = datetime.datetime.now().day
        not_avail_content = config['website.content.not_available']

        while day <= 31:
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
