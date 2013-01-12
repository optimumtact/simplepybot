from commandbot import *
from irc_module import IrcModule
import sys

class GoogleModule():
    """
    An IRC module that can return a link that will search
    google for the asked terms, greatly improves ability 
    to sarcastically answer peoples questions
    """

    def __init__(self, bot):
        self.bot = bot
        self.irc = bot.get_module('IRC')
        self.commands = [
                command(r"!help (?P<searchterms>[\w\s]+)", self.return_search_link)
                ]

        self.events = []

    def return_search_link(self, source, action, targets, message, m):
        search_terms = m.group("searchterms").replace(" ", "+")
        self.irc.msg_all("http://lmgtfy.com/?q="+m.group("searchterms"), targets)

if __name__ == '__main__':
    bot = CommandBot("HelpBot", "irc.segfault.net.nz", 6667)
    irc = IrcModule(bot)
    bot.add_module('IRC', irc)
    gb = GoogleModule(bot)
    bot.add_module("Helper", gb)
    irc.join('#bots')
    bot.loop()
