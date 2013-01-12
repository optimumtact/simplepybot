from commandbot import *
import sys

class GoogleModule():
    """
    An IRC module that can return a link that will search
    google for the asked terms, greatly improves ability 
    to sarcastically answer peoples questions
    """

    def __init__(self, bot):
        self.bot = bot
        self.commands = [
                command(r"!help (?P<searchterms>\S+)", self.return_search_link)
                ]

        self.events = []

    def return_search_link(self, source, action, targets, message, m):
        search_terms = m.group("searchterms").replace(" ", "+")
        self.bot.msg_all("http://lmgtfy.com/?q="+m.group("searchterms"), targets)


bot = CommandBot("HelpBot", "irc.segfault.net.nz", 6667)
bot.join("#bots")
gb = GoogleModule(bot)
bot.add_module("Helper", gb)
bot.loop()
