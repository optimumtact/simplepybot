from commandbot import *
import sys
import logging

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
        
        self.log = logger.getLogger('{0}.{1]'.format(bot.log_name, module_name))
        self.events = []
        self.log.info('Finished intialising {0}'.format(module_name))

    def return_search_link(self, nick, nickhost, action, targets, message, m):
        search_terms = m.group("searchterms").replace(" ", "+")
        self.log.debug('Created lmgtfy link http://lmgtfy.com/?q={0}'.format(search_terms))
        self.bot.msg_all("http://lmgtfy.com/?q={0}".format(search_terms), targets)
        
    def close(self):
        #we do nothing
        pass
    
    def syntax(self):
        return 'Helper module supports\n!help {some help terms}'
        
if __name__ == '__main__':
    bot = CommandBot("HelpBot", "irc.segfault.net.nz", 6667)
    gb = GoogleModule(bot)
    bot.join('#bots')
    bot.loop()
