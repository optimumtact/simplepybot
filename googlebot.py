from commandbot import *
import sys

class GoogleBot(CommandBot):
    """
    An IRC bot that can when asked, return a link that will search
    google for the asked terms, greatly improves ability to sarcastically
    answer peoples questions
    """

    nick = "SarcasticHelper"
    def __init__(self, network, port):
        self.commands = [
                command(r"^%s: quit" % self.nick, self.end),
                command(r"!help (?P<searchterms>\S+)", self.return_search_link)
                ]
        self.network = network
        self.port = port
        super(GoogleBot, self).__init__(self.nick, self.network, self.port)

    def end(self, source, action, targets, message, m):
        """
        Quits the server!
        """
        self.quit("Goodbye")
        sys.exit(0)

    def return_search_link(self, source, action, targets, message, m):
        search_terms = m.group("searchterms").replace(" ", "+")
        self.msg_all("http://lmgtfy.com/?q="+m.group("searchterms"), targets)

hb = GoogleBot("irc.segfault.net.nz", 6667)
hb.join("#cave")
hb.loop()
