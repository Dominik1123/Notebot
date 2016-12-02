import time

import telepot

import config
import messaging
import observe_website
import threads


if __name__ == '__main__':
    bot = telepot.Bot(config.config['telegram.bot.token'])
    bot.message_loop(messaging.process_message)

    responder = threads.Responder(bot, messaging.outgoing_queue)
    responder.start()

    observer = observe_website.Observer(bot, (config.config['telegram.chat.id'],))
    observer.start()

    while True:
        time.sleep(5)
