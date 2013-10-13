import event_util as eu
import logging
import logging.handlers as handlers
import commandbot as cb

ALL = eu.ALL
class IRC_Wrapper:
    
    def __init__(self, bot, module_name = "irc", log_level = logging.DEBUG):

        self.commands = [                
                ]
        self.events = [
                ]

        self.module_name = module_name
        self.log = logging.getLogger("{0}.{1}".format(bot.log_name, self.module_name))
        self.log.setLevel(log_level)
        self.bot = bot
        self.bot.add_module(self.module_name, self)
        self.log.info("Finished initialising {0}".format(module_name)) 

    #useful methods
    def join(self, channel, priority=3):
        self.bot.out_event(eu.join(channel, priority))

    def nick(self, nick, priority=2):
        self.bot.out_event(eu.nick(nick, priority))

    def user(self, nick, realname, priority=2):
        self.bot.out_event(eu.user(nick, realname, priority))

    def connect(self, server, port, priority=1):
        self.bot.out_event(eu.connect(server, port, priority))

    def error(self, message, priority=3):
        self.bot.out_event(eu.error(message, priority))
        
    def irc_msg(self, action, data, priority=3):
        self.bot.out_event(eu.irc_msg(action, data, priority))

    def msg_all(self, msg, channels, priority=3):
        self.bot.out_event(eu.msg_all(msg, channels, priority))

    def msg(self, msg, channel, priority=3):
        self.bot.out_event(eu.msg(msg, channel, priority))

    def msgs(self, msgs, channel, priority=3):
        self.bot.out_event(eu.msgs(msgs, channel, priority))

    def msgs_all(self, msgs, channels, priority=3):
        self.bot.out_event(eu.msgs_all(msgs, channels, priority))

    def quit(self, msg, priority=3):
        self.bot.out_event(eu.quit(msg, priority))

    def kill(self, priority=3):
        self.bot.out_event(eu.kill(priority))

    def pong(self, msg, priority=1):
        self.bot.out_event(eu.pong(msg, priority))
    
    def error(self, msg, priority=1):
        self.bout.out_event(eu.error(msg, priority))