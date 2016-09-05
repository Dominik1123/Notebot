import datetime
from Queue import Queue
import re
import subprocess
import time
import threading

import sched

import config

outgoing_queue = Queue()
schedule_queue = sched.scheduler(time.time, time.sleep)


def create_outgoing_error(original_message, error_text):
    outgoing_queue.put((original_message['chat']['id'], error_text))


def create_personal_outgoing_error(original_message, error_text):
    outgoing_queue.put((original_message['chat']['id'], error_text % original_message['from']['first_name']))


def trigger_by_command(command):
    def wrapper(func):
        setattr(func, 'command', command)
        return func

    return wrapper


@trigger_by_command('/reminder')
def new_reminder(msg):
    """Create a new reminder.

    Reminders must use the following format:
        /reminder <when> <what>
        where <when> can use one of the following formats:
            1. +<number><unit>
            where <unit> can be one of:
                s: seconds
                m: minutes
                h: hours
                d: days
            2. @<date>t<time>
            where <date> can use one of the following formats:
                1. <year>-<month>-<day>: complete date
                2.        <month>-<day>: same year is assumed
                3.                <day>: same year and same month are assumed
                4.                     : same year, month and day are assumed
                where <year>, <month>, <day> are integer numbers
            and <time> must be the following format:
                <hour>:<minute>
        and <what> is a string containing letters, numbers and whitespaces.

    :param msg:
    :return:
    """

    def compute_delay(groupdict):
        seconds_per_unit = {
            's': 1,
            'm': 60,
            'h': 60 * 60,
            'd': 24 * 60 * 60,
        }
        if groupdict['mode'] == '+':
            return int(groupdict['delay']) * seconds_per_unit[groupdict['unit']]
        elif groupdict['mode'] == '@':
            datetime_string = '%04d-%02d-%02d %02d:%02d:00' % (
                int(groupdict['year']) or datetime.datetime.now().year,
                int(groupdict['month']) or datetime.datetime.now().month,
                int(groupdict['day']) or datetime.datetime.now().day,
                int(groupdict['hour']) or datetime.datetime.now().hour,
                int(groupdict['minute']) or datetime.datetime.now().minute
            )
            print datetime_string
            return max(
                time.mktime(datetime.datetime.strptime(datetime_string, '%Y-%m-%d %H:%M:%S').timetuple()) - time.time(),
                0)

    date_pattern = '(?P<year>[2-9][0-9][0-9][0-9])-(?P<month>[0-1][0-9])-(?P<day>[0-3][0-9])\.'
    time_pattern = '(?P<hour>[0-2][0-9]):(?P<minute>[0-5][0-9])'
    when_pattern = '(?P<mode>\+|@)((?P<delay>[0-9]+)(?P<unit>s|m|h|d)|%s%s)' % (date_pattern, time_pattern)
    what_pattern = '(?P<what>[a-zA-Z0-9\s]+)'
    pattern = r'%s %s %s' % (new_reminder.command, when_pattern, what_pattern)
    match = re.match(pattern, msg['text'])
    if match is None:
        create_outgoing_error(msg, 'Regex did not match')
        return
    print match.groupdict()
    outgoing_queue.put((msg['chat']['id'], "Ok, I'll remind you in %d seconds." % compute_delay(match.groupdict())))

    def put_reminder_to_outgoing_queue(reminder_text):
        text = "Hey %s, don't forget to %s!" % (msg['from']['first_name'], reminder_text)
        outgoing_queue.put((msg['chat']['id'], text))

    timer = threading.Timer(compute_delay(match.groupdict()), put_reminder_to_outgoing_queue,
                            [match.groupdict()['what']])
    timer.start()


@trigger_by_command('/update')
def software_update(msg):
    """Update the software via git pull and restart of systemd service.

    :param msg:
    :return:
    """
    subprocess.call(['git', '--git-dir=%s' % config.config['git.git-dir'],
                     '--work-tree=%s' % config.config['git.work-tree'], 'pull'])
    subprocess.call(['systemctl', 'restart', config.config['systemd.service']])


command_reactions = {
    getattr(reaction, 'command'): reaction for reaction in [new_reminder, software_update]
    }

error_messages = {
    'command_without_text': 'Cannot extract command from message without text',
    'invalid_command_format': 'Invalid format for command. Commands must start with "/" and contain only letters.',
    'unknown_command': 'Unknown command. Valid commands are: ' + ' '.join(sorted(command_reactions.keys())),
}

personal_error_messages = {
    'wrong_chat': "Sorry %s, I'm really busy being the secretary of Mr Bond. Maybe Q has some time for you?"
}


def extract_command_from_message(msg):
    if 'text' not in msg:
        raise TypeError(error_messages['command_without_text'])
    command_pattern = r'^(?P<command>/[a-zA-Z]+)'
    match = re.match(command_pattern, msg['text'])
    if match is None:
        raise ValueError(error_messages['invalid_command_format'])
    return match.groupdict()['command']


def process_message(msg):
    if msg['chat']['id'] != config.config['telegram.chat.id']:
        create_personal_outgoing_error(msg, personal_error_messages['wrong_chat'])
        return
    try:
        command = extract_command_from_message(msg)
        print command
    except TypeError as err:
        create_outgoing_error(msg, err.message)
        return
    except ValueError as err:
        create_outgoing_error(msg, err.message)
        return

    try:
        command_reactions[command](msg)
    except KeyError:
        create_outgoing_error(msg, error_messages['unknown_command'])
        return
