from commandbot import *
import sys


class AliasBot():
    '''
    An IRC Bot that can store, retrieve, and delete items.
    This bot stands as the simplest example of how to use
    the framework
    Contains a simple easter egg - HONK.
    '''
    def __init__(self, bot):
        self.commands = [
                command(r"^%s: quit" % bot.nick, self.end),
                command(r"^%s:" % self.nick, self.honk),
                command(r"^!learn (?P<abbr>\S+) as (?P<long>\S.*)$", self.learn),
                command(r"^!forget (?P<abbr>\S+)", self.forget),
                command(r"^!list_abbr$", self.list_abbrievations),
                command(r"^!(?P<abbr>\S+)$", self.retrieve)
                ]
        self.bot = bot
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
        self.bot.msg_all(self.alternate_honk(), targets)

    def learn(self, source, action, targets, message, m):
        '''
        Learn a new abbreviation.
        '''
        self.bot.msg_all('Remembering %s as %s' % (m.group('abbr'), m.group('long')), targets)
        self.quotes[m.group('abbr')] = m.group('long')

    def forget(self, source, action, targets, message, m):
        '''
        Forget about an abbreviation.
        '''
        command = m.group('abbr')
        if command in self.quotes:
            del(self.quotes[command])
            self.bot.msg_all("Hrm. I used to remember %s. Now I don't." % command, targets)
        else:
            self.bot.msg_all("Sorry, I don't know about %s." % command, targets)

    def retrieve(self, source, action, targets, message, m):
        '''
        Retrieves a command.
        '''
        command = m.group('abbr')
        if command in self.quotes:
            self.bot.msg_all("%s: %s" % (command, self.quotes[command].decode()), targets)
        else:
            self.bot.msg_all("Sorry, I don't know about %s." % command, targets)

    def end(self, source, action, targets, message, m):
        """
        Quits the server
        """
        self.bot.quit("I can code something!")
        sys.exit(0)

    def list_abbrievations(self, source, action, targets, message, m):
        """
        List all known abbrievation commands
        """
        keys = ", ".join(self.quotes.keys())
        self.msg_all(keys, targets)

if __name__ == '__main__':
    qb = AliasBot("irc.segfault.net.nz", 6667)
    qb.join("#bots")
    qb.loop()
