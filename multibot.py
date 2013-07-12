from commandbot import *
from reminder import *
from ltmfgy import *
from log_search import *
from aliasbot import *
from quote import *
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
bot = CommandBot('FullTest', 'irc.segfault.net.nz', 6667, log_handlers=[h, file_handler])
bot.join('#bots')
#add modules
AliasBot(bot)
QuoteBot(bot)
ReminderModule(bot)
GoogleModule(bot)
LogModule(bot)
bot.loop()
