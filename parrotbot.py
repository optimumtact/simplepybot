import irc
from time import sleep
import dbm
import re

def command(expr, func):
    guard = re.compile(expr)
    def process(source, action, targets, message):
        m = guard.match(message)
        if not m:
            return False
        func(source, action, targets, message, m)
        return True
    return process

class QuoteDB:
    def __enter__(self):
        self._internal = dbm.open('quotes', 'c')
        return self._internal
    def __exit__(self, type, value, traceback):
        self._internal.close()

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

class QuoteBot(CommandBot):
    honk = "HONK"
    nick = "gamzee"
    def __init__(self, network, port):
        self.commands = [
            command(r"^%s:" % self.nick, self.honk),
            command(r"^!learn (?P<abbr>\S+) as (?P<long>\S.*)$", self.learn),
            command(r"^!forget (?P<abbr>\S+)", self.forget),
            command(r"^!(?P<abbr>\S+)$", self.retrieve)
        ]
        super(QuoteBot, self).__init__(self.nick, network, port)
        self.honk = "HONK"

    def alternate_honk(self):
        self.honk = self.honk.swapcase()
        return self.honk

    def honk(self, source, action, targets, message, m):
        self.msg_all(self.alternate_honk(), targets)

    def learn(self, source, action, targets, message, m):
        print('remembering %s as %s' % (m.group('abbr'), m.group('long')))
        self.quotes[m.group('abbr')] = m.group('long')

    def forget(self, source, action, targets, message, m):
        command = m.group('abbr')
        if command in self.quotes:
            del(self.quotes[command])
            print('deleting %s' % command)
            self.msg_all("Hrm. I used to remember %s. Now I don't." % command, targets)

    def retrieve(self, source, action, targets, message, m):
        command = m.group('abbr')
        if command in self.quotes:
            self.msg_all("%s: %s" % (command, self.quotes[command].decode()), targets)

    def loop(self):
        with QuoteDB() as self.quotes:
            super(QuoteBot, self).loop()

qb = QuoteBot("irc.segfault.net.nz", 6667)
qb.join("#bots")
qb.loop()
