import irc
from time import sleep
import dbm
import re

nick = 'gamzee'

s = irc.IrcConnect(nick, "irc.segfault.net.nz", 6667)

#s.connect((, ), "parrot", "wolololol", "homeland.net.nz",
#        "francis is a francis is a francis")

s.join("#bots")

honk = "HONK"

def alternate_honk():
    global honk
    honk = honk.swapcase()
    return honk

learnre = re.compile(r"^!learn (?P<abbr>\S+) as (?P<long>\S.*)$")
forgetre = re.compile(r"^!forget (?P<abbr>\S+)")
commandre = re.compile(r"^!(?P<abbr>\S+)$")

class QuoteDB:
    def __enter__(self):
        self._internal = dbm.open('quotes', 'c')
        return self._internal
    def __exit__(self, type, value, traceback):
        self._internal.close()

with QuoteDB() as quotes:
    while True:
        for m in s.get_messages():
            source, action, targets, message = m
            print(m)
            if message and action == "PRIVMSG":
                if message.startswith("%s:" % nick):
                    s.msgs_all([alternate_honk()], targets)
                else:
                    m = learnre.match(message)
                    if m:
                        print('remembering %s as %s' % (m.group('abbr'), m.group('long')))
                        quotes[m.group('abbr')] = m.group('long')
                    else:
                        m = forgetre.match(message)
                        if m:
                            command = m.group('abbr')
                            if command in quotes:
                                del(quotes[command])
                                print('deleting %s' % command)
                                s.msg_all("Hrm. I used to remember %s. Now I don't." % command, targets)
                        else:
                            m = commandre.match(message)
                            if m:
                                command = m.group('abbr')
                                if command in quotes:
                                    s.msg_all("%s: %s" % (command, quotes[command].decode()), targets)
        sleep(.1)
