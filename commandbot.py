from network import IrcSocket
import dbm
import sys
import re
from time import sleep
import datetime
from collections import deque

def command(expr, func):
    '''
    Helper function that constructs a command suitable for CommandBot.

    Takes an re source string and a function.
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
    Helper function that constructs an event suitable for CommandBot.

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
        self.logs = deque(maxlen = max_log_len)

        self.commands = []
        self.events = []

        #add a handler that captures the 001 event and joins channels added
        #before we registered
        self.registered = False
        self.channels = []
        self.events.append(event('001', self._join))

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

    def loop(self):
        '''
        Primary loop.

        You'll need to transfer control to this function before execution begins.

        You may wish to override this
        '''
        while True:
            self.logic()
            sleep(.1)

    def logic(self):
        '''
        Simple logic processing.

        Examines all messages received, then attempts to match commands against any messages, in order.
        '''
        for m in self.get_messages():
            was_command = False
            source, action, args, message = m
            print(m)
            if message and action == "PRIVMSG":
                for module in self.modules:
                    module = self.modules[module]
                    for c in module.commands:
                        if c(source, action, args, message):
                            was_command = True
                            break

                if not was_command:
                    #if the message wasn't a command we log it
                    self.log_message(source, action, args, message, m)

            else:
                #we are dealing with some kind of event
                #check it against the event commands
                for module in self.modules:
                    module = self.modules[module]
                    for e in module.events:
                        e(source, action, args, message)

        return


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
