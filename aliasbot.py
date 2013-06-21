from commandbot import *
import sys


class AliasBot():
    '''
    An IRC Bot that can store, retrieve, and delete items.
    This bot stands as the simplest example of how to use
    the framework
    Contains a simple easter egg - HONK.
    '''
    def __init__(self, bot, module_name ='Alias'):
        self.commands = [
                bot.command(r"^\w*", self.honk, direct=True),
                bot.command(r"^!learn (?P<abbr>\S+) as (?P<long>\S.*)$", self.learn),
                bot.command(r"^!forget (?P<abbr>\S+)", self.forget),
                bot.command(r"^!list_abbr$", self.list_abbrievations),
                bot.command(r"^!(?P<abbr>\S+)$", self.retrieve)
                ]
        self.events = []
        self.module_name = module_name
        self.bot = bot
        bot.add_module(module_name, self)
        self.honk = "HONK"

    def alternate_honk(self):
        '''
        Alternate between HONK and honk.
        '''
        self.honk = self.honk.swapcase()
        return self.honk

    def honk(self, nick, nickhost, action, targets, message, m):
        '''
        Honk at anyone that highlighted us.
        '''
        self.bot.msg_all(self.alternate_honk(), targets)

    def learn(self, nick, nickhost, action, targets, message, m):
        '''
        Learn a new abbreviation.
        '''
        self.bot.msg_all('Remembering %s as %s' % (m.group('abbr'), m.group('long')), targets)
        index = str((self.module_name, m.group('abbr')))
        self.bot.storage[index] = m.group('long')

    def forget(self, nick, nickhost, action, targets, message, m):
        '''
        Forget about an abbreviation.
        '''
        abbr = m.group('abbr')
        command = str((self.module_name, abbr))
        if command in self.bot.storage:
            del(self.bot.storage[command])
            self.bot.msg_all("Hrm. I used to remember %s. Now I don't." % abbr, targets)
        else:
            self.bot.msg_all("Sorry, I don't know about %s." % abbr, targets)

    def retrieve(self, nick, nickhost, action, targets, message, m):
        '''
        Retrieves a command.
        '''
        abbr = m.group('abbr')
        command = str((self.module_name, abbr))
        if command in self.bot.storage:
            self.bot.msg_all("%s: %s" % (abbr, self.bot.storage[command]), targets)
        else:
            self.bot.msg_all("Sorry, I don't know about %s." % abbr, targets)

    def list_abbrievations(self, nick, nickhost, action, targets, message, m):
        """
        List all known abbrievation commands
        """
        #look at this functional programming!
        keys = ", ".join(filter(lambda x:self.module_name in x, self.bot.storage.keys()))
        self.bot.msg_all(keys, targets)

    def close(self):
        #we don't do anything special
        pass

if __name__ == '__main__':
    bot = CommandBot('Gamzee', 'irc.segfault.net.nz', 6667)
    mod = AliasBot(bot)
    bot.join('#bots')
    bot.loop()
