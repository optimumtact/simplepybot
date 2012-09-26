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

    It's about time I got around to this, the general plan is to have the quotes stored in a db
    """
    nick = "quotebot"
    def __init__(self, network, port):
        self.commands = [
                command(r"^!quote (?P<match>[\w\s]+) by (?P<nickname>\s+)", self.find_and_remember_quote)
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
            if m.group("nickname"):
                results = self.search_logs_greedy(m.group("match", match=False, name = m.group("nickname")))

            else:
                results = self.search_logs_greedy(m.group("match"), match=False)

            if results:
                if len(results) > 1:
                    self.msg_all("Too many matches found, please refine your search", targets)

                else:
                    #if only one match store the quote along with some supporting info
                    self.store_quote(source, results[0])

            else:
                self.msg_all("No matches found", targets)

        except re.error:
            self.msg_all("Not a valid regex, please try a new query", targets)

    def store_quote(self, source, entry):
        """
        Takes a log entry and stores it in the quote database quotedb. They are indexed by a tuple of (nick, id) where
        id is an number, furthermore under the key nick there is a QuoteData object which is responsible for managing
        the id's for the user who's nick it is stored under, it supports getting a new id and freeing old ones, as well
        as returning a copy of all the id's that that user has quotes stored under

            source: user who requested the quote be stored
            entry: a log entry in the form of (senders_name, targets, message, timestamp)
        """
        #check to see if this user exists and get the id if he does
        #otherwise we store this new user and the current id
        quote_id = 1
        if entry.name in self.quotedb:
            quote_id = self.quotedb[entry.name].get_next_id()
        
        else:
            #initialise this new users necessary data
            self.quotedb[entry.name] = QuoteData()
        
        #If this user and id combination already exists we have a serious problem
        if (entry.name, quote_id) in self.quotedb:
            #TODO raise a nicer exception here
            raise Exception("User and ID combination already exists")
        
        else:
            self.quotedb[(entry.name, quote_id)] = entry
            self.quotedb[entry.name] = quote_id + 1
            return "Quoted: "+ entry

    def loop(self):
        with BotDB('stored_quotes') as self.quotedb:
            super(QuoteBot, self).loop()

# run bot
qb = QuoteBot("irc.segfault.net.nz", 6667)
qb.join("#bots")
qb.loop()


class QuoteData:
    """
    This class handles the id management for each nick in the database
    it provide support methods for freeing an id, getting the next id
    to use and providing a list of all id's.
    """

    def __init__(self):
        self.current_id = 0
        self.freed = list()
        self.in_use = list()

    def get_next_id(self):
        """
        Return the next id for use as part of the (nick, id) tuple
        As well as rememebering that it is in use
        """
        quote_id = 0

        #if there are any freed id's floating around we should use them
        #over advancing the current_id counter, this helps decrease the
        #chances of eventually running out of id's
        if len(self.freed):
            quote_id = self.freed.pop()
            self.in_use.append(quote_id)
            return quote_id
        
        #we use the current id + 1 and increment the current id counter
        else:
            quote_id = self.current_id + 1
            self.current_id += 1
            self.in_use.append(quote_id)
            return quote_id

    def free_id(self, quote_id):
        if quote_id not in self.in_use:
            return False

        else:
            self.in_use.remove(quote_id)
            self.freed.append(quote_id)
            return True

    def get_all_ids(self):
        #TODO perhaps make this a copy of the list? I guess if anyone is
        #mad enough to remove and add id's externally they probably
        #have a good reason
        return self.in_use
