from network import IrcSocket
import re
from time import sleep

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
        self.name = nick
        self.server = network
        self.port = port

    def loop(self):
        '''
        Primary loop.

        You'll need to transfer control to this function before execution begins.

        You may wish to override this.
        '''
        while True:
            self.logic()
            sleep(.1)

    """
    Log messages inside an internal database for later retrieval	
    """
    def log_message(self, source, action, targets, message, m):
        #not implemented yet
        pass



    def logic(self):
        '''
        Simple logic processing.

        Examines all messages received, then attempts to match commands against any messages, in order.
        '''
        for m in self.get_messages():
            source, action, targets, message = m
            print(m)
            if message and action == "PRIVMSG":
                self.log_message(source, action, targets, message, m)
                for c in self.commands:
                    if c(source, action, targets, message):
                        break
                    

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

