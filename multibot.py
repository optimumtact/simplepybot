from commandbot import *
import logging
import logging.handlers as handlers

#timed file handler
file_handler = handlers.TimedRotatingFileHandler('bot.log', when='midnight')
file_handler.setLevel(logging.DEBUG)
#basic stream handler
h = logging.StreamHandler()
h.setLevel(logging.INFO)
#format to use
f = logging.Formatter("%(name)s %(levelname)s %(message)s")
h.setFormatter(f)
file_handler.setFormatter(f)

#create bot instance
bot = CommandBot('Test', 'irc.segfault.net.nz', 6667, log_level=logging.DEBUG, log_handlers=[h, file_handler])
bot.join('#bots')
#add modules
bot.loop()
