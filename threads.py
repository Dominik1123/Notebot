import threading


class Responder(threading.Thread):
    def __init__(self, bot, queue):
        super(Responder, self).__init__()

        self.bot = bot
        self.queue = queue

    def run(self):
        while True:
            message_tuple = self.queue.get()
            self.bot.sendMessage(message_tuple[0], message_tuple[1])


class ScheduleRunner(threading.Thread):
    def __init__(self, schedule_queue):
        super(ScheduleRunner, self).__init__()

        self.schedule_queue = schedule_queue

    def run(self):
        while True:
            self.schedule_queue.run()
