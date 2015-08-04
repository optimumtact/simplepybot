from commandbot import CommandBot
from datetime import datetime, timedelta
import logging


class ReminderModule():
    '''
    An irc module that provides a simple reminder
    service

    rough draft of the command form
    !remind me in number [time specifier] that "string"

    after the right number of minutes/hours/seconds has
    elapsed the bot should send them the string they
    requested
    '''

    def __init__(self, bot, module_name='Reminder'):
        self.bot = bot
        self.irc = bot.irc
        self.bot.add_module(module_name, self)
        self.commands = [
            bot.command(r'!remind me in (?P<num>\d+) (?P<unit>hours?|minutes?|seconds?) (?P<string>(\w+| )+)', self.remind_user),
            bot.command(r'!repeat (?P<num>\d+) (?P<string>(\w+| )+)', self.repeat_user),
        ]

        self.events = []

    def remind_user(self, nick, nickhost, action, targets, message, m):
        '''
        Create a time event that will send a message when
        the elapsed time has passed
        '''

        number = m.group('num')
        number = int(number)
        name = nick
        unit = m.group('unit')
        string = m.group('string')
        string = "{0}: {1}".format(name, string)
        '''
        The start date is now
        the end date is now + num*units
        the interval is num*units
        '''
        start_date = datetime.now()
        # use the units arg to build the correct timedelta type
        if unit in ['hour', 'hours']:
            interval = timedelta(hours=number)

        elif unit in ['minute', 'minutes']:
            interval = timedelta(minutes=number)

        else:
            interval = timedelta(seconds=number)

        end_date = start_date + interval
        '''
        Now create a timed event via the add_timed_event
        api call and pass it the send reminder func with
        the string as an arg

        I.E
        bot.add_timed_event(st, et, i, self.send_reminder, [string])
        '''
        self.bot.add_timed_event(start_date, end_date, interval, self.send_reminder, func_args=(string, targets))

        # let the user know!
        self.irc.msg_all("Copy that", targets)

    def repeat_user(self, nick, nickhost, action, targets, message, m):
        '''
        Create an event to repeat a message num number of times
        '''
        number = m.group('num')
        number = int(number)
        name = nick
        string = m.group('string')
        string = "{0}: {1}".format(name, string)
        start_date = datetime.now()
        interval = timedelta(seconds=1)

        self.bot.add_repeat_event(start_date, number, interval, self.send_reminder, func_args=(string, targets))
        # let the user know!
        self.irc.msg_all("Copy that", targets)

    def send_reminder(self, string, targets):
        self.irc.msg_all(string, targets)

    def syntax(self):
        return  '''
                Reminder module supports
                !remind me in {x} [minutes|seconds|hours] {some reminder string}
                '''

    def close(self):
        # we don't need to clean up anything special
        pass

if __name__ == '__main__':
    # basic stream handler
    h = logging.StreamHandler()
    h.setLevel(logging.INFO)
    # format to use
    f = logging.Formatter(u"%(name)s %(levelname)s %(message)s")
    h.setFormatter(f)
    f_h = logging.handlers.TimedRotatingFileHandler("bot.log", when="midnight")
    f_h.setFormatter(f)
    f_h.setLevel(logging.DEBUG)

    bot = CommandBot('TimeTester', 'irc.segfault.net.nz', 6667, log_handlers=[h, f_h])
    ReminderModule(bot)
    bot.join('#bots')
    bot.loop()
