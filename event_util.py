import collections
from functools import total_ordering
import numerics as nu
from datetime import datetime
import re


@total_ordering
class M_ordering(object):
    """
    A mixin that orders the namedtuple it's mixed with
    credit http://stackoverflow.com/questions/12614213/custom-sorting-on-a-namedtuple-class
    for the solution
    """

    def __lt__(self, other):
        return self.priority < other.priority


class Message(M_ordering, collections.namedtuple('Message', 'type data priority')):
    """
    Our data type
    """
    pass


def event(event_id, func):
    """
    This function will take a function and an event_id, when an inbound message"s action
    matches the event_id it will call the function with the data argument and return True
    it returns False if they don"t match
    """
    event_id = event_id

    def process(message):
        if not event_id == message.type:
            return False
        func(*message.data)
        return True

    return process

def command(bot, expr, func, direct=False, can_mute=True, private=False,
            auth_level=100):
    '''
    Helper function that constructs a command handler function suitable for being called
    in the priv messager handler of a command bot instance 

    Essentially an extension of the EVENT concept that match a regex against a PRIVMSG
    to identify commands

    args:
        expr - regex string to be matched against user message
        func - function to be called upon a match

    kwargs:
        direct - this message eust start with the bots nickname i.e botname
                    quit or botname: quit
        can_mute - Can this message be muted?
        private - Is this message always going to a private channel?
        auth_level - Level of auth this command requires (users who do not have
                        this level will be ignored

    These are intended to be evaluated against user messages and when a match is found
    it calls the associated function, passing through the match object to allow you to
    extract information from the command
    '''
    guard = re.compile(expr)

    def process(source, action, args, message):
        # grab nick and nick host
        nick, nickhost = source.split("!")

        # unfortunately there is weirdness in irc and when you get addressed in
        # a privmsg you see your own name as the channel instead of theirs
        # It would be nice if both sides saw the other persons name
        # I guess they weren"t thinking of bots when they wrote the spec
        # so we replace any instance of our nick with their nick
        for i, channel in enumerate(args[:]):
            if channel == bot.nick:
                args[i] = nick

        # make sure this message was prefixed with our bot username
        if direct:
            if not message.startswith(bot.nick):
                return False

            # strip nick from message
            message = message[len(bot.nick):]
            # strip away any syntax left over from addressing
            # this may or may not be there
            message = message.lstrip(": ")

        else:
            if not message.startswith(bot.commandprefix):
                return False
            message = message[len(bot.commandprefix):]

        # If muted, or message private, send it to user not channel
        if (bot.is_mute or private) and can_mute:
            # replace args with usernick stripped from source
            args = [nick]

        # check it matches regex and grab the matcher object so the function can
        # pull stuff out of it
        m = guard.match(message)
        if not m:
            return False

        '''
        auth_level < 0 means do no auth check at all!, this differs from the default
        which gives most things an auth_level of 100. The only thing that currently uses
        it is the auth module itself, for bootstrapping authentication. Not recommended for
        normal use as people may want ignore people who are not in the auth db, and they
        will change how level 100 checks are managed
        '''
        if auth_level:
            if auth_level > 0 and not bot.auth.is_allowed(nick, nickhost, auth_level):
                return True  # Auth failed but this was a command

        # call the function
        func(nick, nickhost, action, args, message, m)
        return True

    return process


class TimedEvent:
    """
    Represents a timed event,
    the should_trigger method will return true if the
    function should be triggered at the current time

    the is_expired method will return true if the timedevent
    has expired (gone past it"s end_date)
    """

    def __init__(self, start_date, end_date, interval, func, func_args, func_kwargs):
        """
        set up a new timed event object
        """
        self.sd = start_date
        self.ed = end_date
        self.interval = interval
        self.func = func
        self.func_args = func_args
        self.func_kwargs = func_kwargs
        self.next_timeout = self.sd + self.interval

    def should_trigger(self):
        """
        Returns true if the timed event interval has elapsed and we need
        to trigger the function. It also updates when the next timeout
        should occur
        """
        current_time = datetime.now()
        if current_time > self.next_timeout:
            self.next_timeout = current_time + self.interval
            return True
        else:
            return False

    def is_expired(self):
        """
        Returns true if the current time is greater than the end_time for
        this event
        """
        if datetime.now() > self.ed:
            return True
        else:
            return False


class RepeatingEvent(TimedEvent):

    def __init__(self, start_date, repeat_count, interval, func, func_args, func_kwargs):
        """
        set up a new timed event object
        """
        self.sd = start_date
        self.rc = repeat_count
        self.cc = 0  # number of times ticked
        self.interval = interval
        self.func = func
        self.func_args = func_args
        self.func_kwargs = func_kwargs
        self.next_timeout = self.sd + self.interval

    def should_trigger(self):
        """
        Returns true if the timed event interval has elapsed and we need
        to trigger the function. It also updates when the next timeout
        should occur
        """
        current_time = datetime.now()
        if current_time > self.next_timeout:
            self.next_timeout = current_time + self.interval
            self.cc += 1
            return True
        else:
            return False

    def is_expired(self):
        """
        Returns true if the current time is greater than the end_time for
        this event
        """
        if self.cc >= self.rc:
            return True
        else:
            return False


'''
Really boring bunch of definitions of event types,
ircmodule.py wraps this to provide a slightly nicer interface
again, where you don't need to explicitly insert the returned
events.
'''


def irc_msg(command, data, priority=3):
    '''
    Network uses this to store the inbound events
    from the server on the in queue of the main bot
    '''
    return Message(command, data, priority)


def join(channel, priority=3):
    return Message(nu.BOT_JOIN_CHAN, (channel,), priority)


def nick(nick, priority=2):
    return Message(nu.BOT_NICK, (nick,), priority)


def user(nick, realname, priority=2):
    return Message(nu.BOT_USER, (nick, realname), priority)


def connect(server, port, priority=1):
    return Message(nu.BOT_CONN, (server, port), priority)


def error(message, priority=3):
    return Message(nu.BOT_ERR, (message,), priority)


def msg_all(msg, channels, priority=3):
    return Message(nu.BOT_MSG_ALL, (msg, channels), priority)


def msg(msg, channel, priority=3):
    return Message(nu.BOT_MSG, (msg, channel), priority)


def msgs(msgs, channel, priority=3):
    return Message(nu.BOT_MSGS, (msgs, channel), priority)


def msgs_all(msgs, channels, priority=3):
    return Message(nu.BOT_MSGS_ALL, (msgs, channels), priority)



def notice(msg, channel, priority=3):
    return Message(nu.BOT_NOTICE, (msg, channel), priority)

def notice_all(msg, channels, priority=3):
    return Message(nu.BOT_NOTICE_ALL, (msg, channels), priority)


def quit(msg, priority=3):
    return Message(nu.BOT_QUIT, (msg,), priority)


def kill(priority=0):
    return Message(nu.BOT_KILL, (), priority)


def pong(msg, priority=1):
    return Message(nu.BOT_PONG, (msg,), priority)


def error(msg, priority=1):
    return Message(nu.BOT_ERROR, (msg,), priority)


def name(channel, priority):
    return Message(nu.BOT_NAMES, (channel,), priority)


def who(param, priority=3):
    return Message(nu.BOT_WHO, (param,), priority)
