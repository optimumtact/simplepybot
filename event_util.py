import collections
from functools import total_ordering

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


class TimedEvent:
    """
    Represents a timed event, 
    the should_trigger method will return true if the 
    function should be triggered at the current time
    
    the is_expired method will return true if the timedevent
    has expired (gone past it"s end_date)
    """

    def __init__(start_date, end_date, interval, func, func_args, func_kwargs):
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

def join(channel, priority = 3):
    return Message('JOIN', (channel,), priority)

def nick(nick, priority = 2):
    return Message('NICK', (nick,), priority)

def user(nick, realname, priority = 2):
    return Message('USER', (nick, realname), priority)

def connect(server, port, priority = 1):
    return Message('CONN', (server, port), priority)

def error(message, priority = 3):
    return Message('ERROR', (message,), priority)

def msg_all(msg, channels, priority = 3):
    return Message('MSG_ALL', (msg, channels), priority)


def msg(msg, channel, priority = 3):
    return Message('MSG', (msg, channel), priority)


def msgs(msgs, channel, priority = 3):
    return Message('MSGS', (msgs, channel), priority)


def msgs_all(msgs, channels, priority = 3):
    return Message('MSGS_ALL', (msgs, channels), priority)


def quit(msg, priority = 3):
    return Message('QUIT', (msg,), priority)


def kill(priority = 0):
    return Message('KILL', (), priority)


def pong(msg, priority = 1):
    return Message('PONG', (msg,), priority)


def error(msg, priority = 1):
    return Message('ERROR', (msg,), priority)


