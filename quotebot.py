from commandbot import *

class QuoteBot(CommandBot):
    """
    A bot that provides quote services to a channel

    Supported commands:
        !quote some string: search the backlog for any message matching some string and store that as a quote
        !quote some string by user: search the backlog for any message matching some string and made by user and store that as a quote
        !last quotes: last 5 quotes
        !quotes for user: return list of quotes for user
        !quote id: return quote with given id

    It's about time I got around to this, the general plan is to have the quotes stored in a dbm instance by username, there will hopefully
    be some secondary indexes, such as ID and Message to also be able to search by, depends on how much effort I put in after getting the basics
    up
    """
    nick = "quotebot"
    def __init__(self, network, port):
        self.commands = [
        command(r"^!quote (?P<match>[\w\s]+)", self.find_and_remember_quote)
        ]
        self.network = network
        self.port = port
        super(QuoteBot, self).__init__(self.nick, self.network, self.port)

    def find_and_remember_quote(self, source, action, targets, message, m):
        """
        Searches the channel backlog with the given regex, if it finds more than one
        match it warns you and displays them, if it finds one match it stores that as a
        quote. If no match is found it tells you so
        """
        if m.group("match"):
            try:
                results = self.search_logs_greedy(m.group("match"), match=False)
                if results:
                    if len(results) > 1:
                        self.msg_all("Too many matches found, please refine your search", targets)

                    else:
                        #if only one match store the quote along with some supporting info
                        message = self.store_quote(source, results[0])
                        self.msg_all(message, targets)


                else:
                    self.msg_all("No matches found", targets)

            except re.error:
                self.msg_all("Not a valid regex, you shouldn't be able to trigger this, if you did, well, good job", targets)
        else:
            self.msg_all("You didn't even match the regex, this should be super impossible, seeing this means something is very wrong", targets)

    def store_quote(self, source, logged_message):
        #not yet doing anything
        return "Quote not stored, but at least it works (sort of)"

    def loop(self):
        with BotDB('stored_quotes') as self.quotedb:
            super(QuoteBot, self).loop()

# run bot
qb = QuoteBot("irc.segfault.net.nz", 6667)
qb.join("#bots")
qb.loop()
