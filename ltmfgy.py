from commandbot import *
import sys

class GoogleModule():
    """
    An IRC module that can return a link that will search
    google for the asked terms, greatly improves ability 
    to sarcastically answer peoples questions
    """

    def __init__(self, bot, module_name='Helper'):
        self.bot = bot
        bot.add_module(module_name, self)
        self.commands = [
                bot.command(r"!help (?P<searchterms>[\w\s]+)", self.return_search_link)
                ]

        self.events = []

    def return_search_link(self, source, action, targets, message, m):
        search_terms = m.group("searchterms").replace(" ", "+")
        self.bot.msg_all("http://lmgtfy.com/?q="+search_terms, targets)
        
    def close(self):
        #we do nothing
        pass

if __name__ == '__main__':
    bot = CommandBot("HelpBot", "irc.segfault.net.nz", 6667)
    gb = GoogleModule(bot)
    bot.add_module("Helper", gb)
    bot.join('#cave')
    bot.loop()
