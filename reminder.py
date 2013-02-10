from commandbot import CommandBot
from commandbot import command, event
from datetime import datetime, timedelta

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

    def __init__(self, bot):
        self.bot = bot
        self.commands = [
                command(r'!remind me in (?P<num>\d+) (?P<unit>hours?|minutes?|seconds?) (?P<string>(\w+| )+)', self.remind_user)
                ]

        self.events = []


    def remind_user(self, source, action, targets, message, m):
        '''
        Create a time event that will send a message when
        the elapsed time has passed
        '''

        number = m.group('num')
        number = int(number)

        unit = m.group('unit')
        string = m.group('string')

        '''
        The start date is now
        the end date is now + num*units
        the interval is num*units
        '''
        start_date = datetime.now()
        #use the units arg to build the correct timedelta type
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
        bot.add_timed_event(start_date, end_date, interval, self.send_reminder, func_args=(string, targets))


    def send_reminder(self, string, targets):
        bot.msg_all(string, targets)


if __name__ == '__main__':
    bot = CommandBot('TimeTester', 'irc.segfault.net.nz', 6667)
    bot.join('#bots')
    mod = ReminderModule(bot)
    bot.add_module('Reminders', mod)
    bot.loop()
