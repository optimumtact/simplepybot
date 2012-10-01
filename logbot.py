from commandbot import *

class LogBot(CommandBot):
    """
    An IRC bot that offers log searching services

    Written as a runup to quotebot and to test the frameworks logging features
    """

    nick = "LumberJack"
    def __init__(self, network, port):
        self.commands = [
                command(r"^%s: quit" % self.nick, self.end),
                command(r"^!harvest many (?P<match>.*)", self.harvest_many),
                command(r"^!harvest (?P<match>.*)", self.harvest)
                ]
        super(LogBot, self).__init__(self.nick, network, port)

    def harvest_many(self, source, actions, targets, message, m):
        """
        Search the logs for every item that can .search match the m.group("match")
        value
        """
        messages = []
        try:
            results = self.search_logs_greedy(m.group("match"), match=False)
                if results:
                    for result in results:
                        messages.append (" [message:{0}, sender:{1}] ".format(result.message, result.name))
                    self.msg_all(r"".join(messages), targets)

                else:
                    self.msg_all("No matches found", targets)

        except re.error:
            self.msg_all("Not a valid regex", targets)

    def harvest(self, source, actions, targets, message, m):
        """
        Search the logs for anything matching the m.group("match") value
        """
        try:
            result = self.search_logs(m.group("match"), match=False)
                if result:
                    message = "Harvested:{0}, sender:{1}".format(result.message, result.name)
                    self.msg_all(message, targets)

                else:
                    self.msg_all("No match found", targets)

        except re.error:
            self.msg_all("Not a valid regex", targets)


    def end(self, source, actions, targets, message, m):
        """
        Quit server and kill script
        """
        self.quit("Lunch Break")
        sys.exit(0)

hb = LogBot("irc.segfault.net.nz", 6667)
hb.join("#bots")
hb.loop()

