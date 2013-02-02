from network import IrcSocket
import dbm
import sys
import re

from datetime import datetime, timedelta
from time import sleep
from collections import deque

def command(expr, func):
    '''
    Helper function that constructs a command handler suitable for CommandBot.

    Takes a regex source string and a function.
    '''
    guard = re.compile(expr)
    def process(source, action, args, message):
        m = guard.match(message)
        if not m:
            return False
        func(source, action, args, message, m)
        return True
    return process

def event(event_id, func):
    '''
    Helper function that constructs an event handler suitable for CommandBot.

    Takes an id and a function
    '''
    event_id = event_id
    def process(source, action, args, message):
        if not event_id == action:
            return False

        func(source, action, args, message)
        return True
    return process

class CommandBot(IrcSocket):
    '''
    A base IRC bot with a simple framework and helpers in place for command processing.

    Override the commands variable in instances or subclasses.

    See the command helper for constructing commands.
    '''

    def __init__(self, nick, network, port, max_log_len = 100):
        super(CommandBot, self).__init__()
        assert network and port
        self.modules = dict()
        self.connect((network, port), nick, "bot@"+network, network, nick)
        self.nick = nick
        self.server = network
        self.port = port

        self.registered = False
        self.channels = []

        self.commands = []
        self.events = [
                event('001', self.registered_event),
                ]

    def add_module(self, name, module):
        '''
        Add the given module to the modules dictionary under the given name
        Raises a key error if the name is already in use
        '''
        if name in self.modules:
            raise KeyError("Module name:{0} already in use".format(name))
        self.modules[name] = module

    def get_module(self, name):
        '''
        Returns the module stored in module dict under the key given by name
        Raises a key error if there is no module with that name
        '''
        if name not in self.modules:
            raise KeyError("No module with the name:{0}".format(name))

        return self.modules[name]

    def has_module(self, name):
        '''
        Returns true if the bot has this module or false otherwise
        '''
        if name not in self.modules:
            return False

        else:
            return True

    def add_timed_event(start_time, end_time, interval, func, args=None, kwargs=None):
        '''
        Add an event that will trigger once at start_time and then every time
        interval amount of time has elapsed it will trigger again until end_time
        has passed

        Start time and end time are datetime objects
        and interval is a timedelta object
        '''
        #TODO write the TimedEvent class, with should_trigger and is_expired methods
        #self.timed_events.append(TimedEvent(start_time, end_time, interval, func, args, kwargs))
        pass


    def loop(self):
        '''
        Primary loop.

        You'll need to transfer control to this function before execution begins.
        You may wish to override this to include your own time sensitive features
        '''
        while True:
            self.logic()
            sleep(.1)

    def logic(self):
        '''
        Simple logic processing.

        Examines all messages received, then attempts to match commands against any messages, in 
        the following order

        if a privmsg
            commands local to commandbot
            commands in modules loaded

        all messages(including privmsgs)
        events local to commandbot
        events in modules loaded

        #TODO loop through timed_events array and handle timed events
        I need to write a timedevent class that has two methods, should_trigger()
        which returns true if the function should be run
        and is_expired() which returns true if the timedevent has passed it's end date

        maybe also have trigger() which actually triggers and runs the function
        '''
        for m in self.get_messages():
            was_command = False
            source, action, args, message = m
            print(m)

            #if a priv message we first pass it through the command handlers
            if message and action == "PRIVMSG":
                for command in self.commands:
                    if command(source, action, args, message):
                        action ='COMMAND' #we set the action to command so valid commands can be identified by modules
                        break

                for module in self.modules:
                    module = self.modules[module]
                    for command in module.commands:
                        if command(source, action, args, message):
                            action = 'COMMAND'
                            break

            #check it against the event commands
            for event in self.events:
                event(source, action, args, message)

            for module in self.modules:
                module = self.modules[module]
                for event in module.events:
                    event(source, action, args, message)

        return

    def msgs_all(self, msgs, channels):
        """
        Accepts a list of messages to send to a list of channels
        msgs: A list of messages to send
        channels: A list of targets to send it to
        """
        for channel in channels:
            for message in msgs:
                self.msg(message, channel)

    def msg_all(self, message, channels):
        """
        Accepts a message to send to a list of channels
        message: the message to send
        channels: A list of targets to send it to
        """
        for channel in channels:
            self.msg(message, channel)

    def msg(self, message, channel):
        '''
        Send a message to a specific target.
        message: the message to send
        channel: the target to send it to
        '''
        self.send('PRIVMSG ' + channel + ' :' + message)

    def join(self, channel):
        '''
        Join a channel.
        channel: the channel to join
        The channel should contain one or more # symbols as needed.

        '''
        if self.registered:
            self.send('JOIN ' + channel)

        else:
            self.channels.append(channel)

    def registered_event(self, source, action, args, message):
        '''
        this is called when a 001 welcome message gets received
        any actions that require you to be registered with
        name and nick first are cached and then called when
        this event is fired
        '''
        self.registered = True
        for channel in self.channels:
            self.join(channel)

    def quit(self, message):
        '''
        Disconnects from a server with a given QUIT message.
        message: message to display with quit
        '''
        self.send('QUIT :' + message)

    def leave(self, channel, message=None):
        '''
        Leaves a channel, optionally sending a message to the channel first.
        channel: Channel to leave
        message: optional message to send first
        '''
        if message:
            self.msg(message, channel)
        self.send('PART ' + channel)


class BotDB:
    """
    Trivial wrapper class over dbm to enable use in with statements.
    """
    def __init__(self, name):
        """
        Store the given name to use for this Database
        """
        self.name = name

    def __enter__(self):
        """
        Set up the internal db with the right settings
        """
        self._internal = dbm.open(self.name, 'c')
        return self._internal

    def __exit__(self, type, value, traceback):
        """
        On exit we simply close internal db instance
        """
        self._internal.close()
