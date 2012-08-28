import irc
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

class CommandBot(irc.IrcConnection):
    '''
    A base IRC bot with a simple framework and helpers in place for command processing.

    Override the commands variable in instances or subclasses.

    See the command helper for constructing commands.
    '''
    commands = []
    def __init__(self, nick, network, port):
        super(CommandBot, self).__init__(nick, network, port)

    def loop(self):
        '''
        Primary loop.

        You'll need to transfer control to this function before execution begins.

        You may wish to override this.
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
            source, action, targets, message = m
            print(m)
            if message and action == "PRIVMSG":
                for c in self.commands:
                    if c(source, action, targets, message):
                        break
