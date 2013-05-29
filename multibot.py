from commandbot import *
from reminder import *
from ltmfgy import *
from log_search import *
from aliasbot import *

bot = CommandBot('MultiBot', 'irc.segfault.net.nz', 6667)
bot.join('#bots')
ReminderModule(bot)
GoogleModule(bot)
LogModule(bot)
bot.loop()
