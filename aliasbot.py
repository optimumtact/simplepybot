from commandbot import *
import sys


class AliasBot(CommandBot):
    '''
    An IRC Bot that can store, retrieve, and delete items.
    This bot stands as an example to all and sundry
    Coded by TrueshiftBlue

    Contains a simple easter egg - HONK.
    '''
    honk = "HONK"
    nick = "gamzee"
    def __init__(self, network, port):
        self.commands = [
                command(r"^%s: quit" % self.nick, self.end),
                command(r"^%s:" % self.nick, self.honk),
                command(r"^!learn (?P<abbr>\S+) as (?P<long>\S.*)$", self.learn),
                command(r"^!forget (?P<abbr>\S+)", self.forget),
                command(r"^!list_abbr$", self.list_abbrievations),
                command(r"^!(?P<abbr>\S+)$", self.retrieve)
                ]
        super(AliasBot, self).__init__(self.nick, network, port)
        self.honk = "HONK"

    def alternate_honk(self):
        '''
        Alternate between HONK and honk.
        '''
        self.honk = self.honk.swapcase()
        return self.honk

    def honk(self, source, action, targets, message, m):
        '''
        Honk at anyone that highlighted us.
        '''
        self.msg_all(self.alternate_honk(), targets)

    def learn(self, source, action, targets, message, m):
        '''
        Learn a new abbreviation.
        '''
        self.msg_all('Remembering %s as %s' % (m.group('abbr'), m.group('long')), targets)
        self.quotes[m.group('abbr')] = m.group('long')

    def forget(self, source, action, targets, message, m):
        '''
        Forget about an abbreviation.
        '''
        command = m.group('abbr')
        if command in self.quotes:
            del(self.quotes[command])
            self.msg_all("Hrm. I used to remember %s. Now I don't." % command, targets)
        else:
            self.msg_all("Sorry, I don't know about %s." % command, targets)

    def retrieve(self, source, action, targets, message, m):
        '''
        Retrieves a command.
        '''
        command = m.group('abbr')
        if command in self.quotes:
            self.msg_all("%s: %s" % (command, self.quotes[command].decode()), targets)
        else:
            self.msg_all("Sorry, I don't know about %s." % command, targets)

    def end(self, source, action, targets, message, m):
        """
        Quits the server
        """
        self.quit("I can code something!")
        sys.exit(0)

    def list_abbrievations(self, source, action, targets, message, m):
        """
        List all known abbrievation commands
        """
        keys = ", ".join(self.quotes.keys())
        self.msg_all(keys, targets)

    def loop(self):
        with BotDB('alias') as self.quotes:
            super(AliasBot, self).loop()

qb = AliasBot("irc.segfault.net.nz", 6667)
qb.join("#bots")
qb.loop()
