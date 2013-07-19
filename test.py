import logging
import tox_dht as t
import commandbot as cb

#basic stream handler
h = logging.StreamHandler()
h.setLevel(logging.DEBUG)
#format to use
f = logging.Formatter("%(name)s %(levelname)s %(message)s")
h.setFormatter(f)
bot = cb.CommandBot("dht_bootstrap", "irc.freenode.net", 6667, log_handlers=[h])
gb = t.dht_bootstrap(bot)
bot.join('#InsertProjectNameHere')
bot.loop()
