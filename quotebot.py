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

    def store_quote(self, source, entry):
        """
        Takes a log entry and stores it in the quote database quotedb. They are indexed by a tuple of (nick, id) where
        id is an number, this number represents the latest id allowed and is stored in the dict under the value of nick
        
        parameters
        source: user who requested the quote be stored
        entry: a log entry in the form of (senders_name, targets, message, timestamp)
        """
        #check to see if this user exists and get the id if he does
        #otherwise we store this new user and the current id
        quote_id = 0
        if entry[0] in self.quotedb:
            quote_id = self.quotedb[entry[0]]
        
        else:
            self.quotedb[entry[0]] = quote_id
        
        #If this user and id combination already exists we have a serious problem
        if (entry[0], quote_id) in self.quotedb:
            raise Exception("User and ID combination already exists")
        
        else:
            self.quotedb[(entry[0], quote_id)] = entry
            return "Quoted: "+ entry

    def loop(self):
        with BotDB('stored_quotes') as self.quotedb:
            super(QuoteBot, self).loop()

# run bot
qb = QuoteBot("irc.segfault.net.nz", 6667)
qb.join("#bots")
qb.loop()
