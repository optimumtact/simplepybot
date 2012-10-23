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
    def process(source, action, targets, message):
        m = guard.match(message)
        if not m:
            return False
        func(source, action, targets, message, m)
        return True
    return process

class CommandBot(IrcSocket):
    '''
    A base IRC bot with a simple framework and helpers in place for command processing.

    Override the commands variable in instances or subclasses.

    See the command helper for constructing commands.
    '''
    commands = []

    def __init__(self, nick, network, port, max_log_len = 100):
        super(CommandBot, self).__init__()
        assert network and port
        self.modules = dict()
        self.connect((network, port), nick, "bot@"+network, network, nick)
        self.nick = nick
        self.server = network
        self.port = port
        self.logs = deque(maxlen = max_log_len)

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

    def log_message(self, source, action, targets, message, m):
        """
        Log messages in order with a queue, these can be searched by search_logs(regex, name)
        takes standard input from self.get_messages() and does cleaning on it, specifically
        splitting the nick out of the irc senders representation (nick!username@server)
        """
        senders_name = source.split('!')[0]
        #store as a new log entry!
        self.logs.append(LogEntry(senders_name, message, targets))

    def search_logs(self, regex, name=None, match = True):
        """
        Search the stored logs for a message matching the regex given
        Parameters:
            regex:the regex to search with
        Optional:
            nick: if specified attempts to match the given value to the nick as well
            match: controls wether the regex matcher uses a .search or a .match as per  python re specs
        
        Returns a tuple in the format (senders nick, message receivers, message) if a match is found, otherwise
        it returns None

        This method does not capture any errors, so as to allow the bot calling to define what happens when
        the regex compile fails (a re.error is thrown, so catch that)
        """
        for entry in self.logs:

            if match:
                result = re.match(regex, entry.message)
            
            else:
                result = re.search(regex, entry.message)

            if result:
                if name:
                    if entry.name == name:
                        return entry

                    else:
                        return None

                else:
                    return entry

        return None

    def search_logs_greedy(self, regex, name = None, match = True):
        """
        Search the stored logs for a message matching the regex given, on a match keeps matching
        and returns a list of all matching logs
        Parameters:
            regex: the regex to search the logs with
        Optional:
            nick: if specified attempts to match the given value to the nick as well
            match: controls whether the regex matcher uses a .search or a .match as per python re specs
        
        Returns a tuple in the format (senders nick, message receivers, message) if a match is found, otherwise
        it returns None

        This method does not capture any errors, so as to allow the bot calling to define error handling
        """
        all_matches = []
        for entry in self.logs:

            if match:
                result = re.match(regex, entry.message)
            
            else:
                result = re.search(regex, entry.message)

            if result:
                if name:
                    if entry.name == name:
                        all_matches.append(entry)

                    else:
                        continue

                else:
                    all_matches.append(entry)

        return all_matches

    def logic(self):
        '''
        Simple logic processing.

        Examines all messages received, then attempts to match commands against any messages, in order.
        '''
        for m in self.get_messages():
            was_command = False
            source, action, targets, message = m
            print(m)
            if message and action == "PRIVMSG":
                for module in modules:
                    for c in module.commands:
                        if c(source, action, targets, message):
                            was_command = True
                            break

                if not was_command:
                    #if the message wasn't a command we log it
                    self.log_message(source, action, targets, message, m)

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
        self.send('JOIN ' + channel)

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
        XXX: The message should probably be the PART message
        '''
        if message:
            self.msg(message, channel)
        self.send('PART ' + channel)

class LogEntry:
    """
    simple storage class representing a logged channel message
    """
    def __init__(self, name, message, channel):
        self.channel = channel
        self.name = name
        self.message = message
        self.timestamp = datetime.datetime.utcnow()

    def __str__(self):
        return "<{0}> {1}".format(self.name, self.message)

    def __repr__(self):
        return "name:{0}, message:{1}, channel:{2}, timestamp{3}".format(self.name, self.message, self.channel, self.timestamp)

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
