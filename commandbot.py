import irc
import re
from time import sleep

def command(expr, func):
    guard = re.compile(expr)
    def process(source, action, targets, message):
        m = guard.match(message)
        if not m:
            return False
        func(source, action, targets, message, m)
        return True
    return process

class CommandBot(irc.IrcConnection):
    commands = []
    def __init__(self, nick, network, port):
        super(CommandBot, self).__init__(nick, network, port)

    def loop(self):
        while True:
            self.logic()
            sleep(.1)

    def logic(self):
        for m in self.get_messages():
            source, action, targets, message = m
            print(m)
            if message and action == "PRIVMSG":
                for c in self.commands:
                    if c(source, action, targets, message):
                        break
