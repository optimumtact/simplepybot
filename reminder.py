from commandbot import CommandBot
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

    def __init__(self, bot, module_name='Reminder'):
        self.bot = bot
        self.bot.add_module(module_name, self)
        self.commands = [
                bot.command(r'!remind me in (?P<num>\d+) (?P<unit>hours?|minutes?|seconds?) (?P<string>(\w+| )+)', self.remind_user)
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
        self.bot.add_timed_event(start_date, end_date, interval, self.send_reminder, func_args=(string, targets))
        
        #let the user know!
        self.bot.msg_all("Copy that", targets)


    def send_reminder(self, string, targets):
        self.bot.msg_all(string, targets)
    
    def syntax(self):
        return  '''
                Reminder module supports
                !remind me in {x} [minutes|seconds|hours] {some reminder string}
                '''
                
    def close(self):
        #we don't need to clean up anything special
        pass

if __name__ == '__main__':
    bot = CommandBot('TimeTester', 'irc.segfault.net.nz', 6667)
    bot.join('#bots')
    ReminderModule(bot)
    bot.loop()
