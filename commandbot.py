from network import IrcSocket
import dbm
import sys
import re
from time import sleep
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

    def __init__(self, nick, network, port):
        super(CommandBot, self).__init__()
        assert network and port
        self.connect((network, port), nick, "bot@"+network, network, nick)
        self.nick = nick
        self.server = network
        self.port = port
        self.logs = deque(maxlen=100)


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
        self.logs.append((senders_name, targets, message))

    def search_logs(self, regex, name=None, match = True):
        """
        Search the stored logs for a message matching the regex given
        Parameters:

        Optional:
            nick: if specified attempts to match the given value to the nick as well
            match: controls wether the regex matcher uses a .search or a .match as per  python re specs
        
        Returns a tuple in the format (senders nick, message receivers, message) if a match is found, otherwise
        it returns None

        This method does not capture any errors, so as to allow the bot calling to define what happens when
        the regex compile fails (a re.error is throw, so catch that)
        """
        for entry in self.logs:

            if match:
                result = re.match(regex, entry[2])
            
            else:
                result = re.search(regex, entry[2])

            if result:
                if name:
                    if entry[0] == name:
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

        Optional:
            nick: if specified attempts to match the given value to the nick as well
            match: controls wether the regex matcher uses a .search or a .match as per  python re specs
        
        Returns a tuple in the format (senders nick, message receivers, message) if a match is found, otherwise
        it returns None

        This method does not capture any errors, so as to allow the bot calling to define error handling
        """
        all_matches = []
        for entry in self.logs:

            if match:
                result = re.match(regex, entry[2])
            
            else:
                result = re.search(regex, entry[2])

            if result:
                if name:
                    if entry[0] == name:
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
            source, action, targets, message = m
            print(m)
            if message and action == "PRIVMSG":
                for c in self.commands:
                    if c(source, action, targets, message):
                        break

                #if we reach this point it matches no known command and
                #therefore can be logged 
                self.log_message(source, action, targets, message, m)

        return


    def msgs_all(self, msgs, channels):
        """
        Accepts a list of msgs to send to a list of channels
        """
        for channel in channels:
            for message in msgs:
                self.msg(message, channel)

    def msg_all(self, message, channels):
        """
        Accepts a message to send to a list of channels
        """
        for channel in channels:
            self.msg(message, channel)

    def msg(self, message, channel):
        '''
        Send a message to a specific target.
        '''
        self.send('PRIVMSG ' + channel + ' :' + message)

    def join(self, channel):
        '''
        Join a channel.

        The channel should contain one or more # symbols as needed.
        '''
        self.send('JOIN ' + channel)

    def quit(self, message):
        '''
        Disconnects from a server with a given QUIT message.
        '''
        self.send('QUIT :' + message)

    def leave(self, channel, message):
        '''
        Leaves a channel, optionally sending a message to the channel first.

        XXX: The message should probably be the PART message
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
