from commandbot import *
import shelve

#TODO implement delete command for quotes, clean up quote command syntax
#TODO add a quit command
class QuoteBot(CommandBot):
    """
    A bot that provides quote services to a channel

    Supported commands:
        !quote some string: search the backlog for any message matching some string and store that as a quote
        !quote some string by user: search the backlog for any message matching some string and made by user and store that as a quote
        !quotes for user: return list of quotes for user
        !quote id: return quote with given id

    """
    nick = "quotebot"
    def __init__(self, network, port):
        self.commands = [
                command(r"!quote (?P<id>\d+) by (?P<nick>\S+)", self.quote_by_id),
                command(r"^!quote (?P<match>[\w\s]+) by (?P<nick>\S+)", self.find_and_remember_quote_by_name),
                command(r"!quotes for (?P<nick>\S+)", self.quote_ids_for_name),
                command(r"^!quote (?P<match>[\w\s]+)", self.find_and_remember_quote),
                ]
        self.network = network
        self.port = port
        super(QuoteBot, self).__init__(self.nick, self.network, self.port)
    
    def quote_by_id(self, source, action, targets, message, m):
        """
        Determine if the id given by m.group("id") is assigned for m.group("nick")
        and then return the quote stored under that combination
        """
        nick = str(m.group("nick"))
        quote_id = int(m.group("id"))
        if nick in self.quotedb:
            quote_ids = self.quotedb[nick].get_all_ids()
            if quote_id in quote_ids:
                index = str((nick, quote_id))
                for key in self.quotedb:
                    print(key, self.quotedb[key])

                print('index', index)
                if index in self.quotedb:
                    self.msg_all(str(self.quotedb[index]), targets)

                else:
                    self.msg_all('error', targets)

            else:
                self.msg_all("There is no quote with that id for this user", targets)

        else:
            self.msg_all("There are no quotes for that user", targets)

    def quote_ids_for_name(self, source, action, targets, message, m):
        """
        Determine if the name stored in m.group("nick") has quotes stored in the quotedb
        and is so return a list of them to the channel for display
        """
        nick = str(m.group("nick"))
        if nick in self.quotedb:
            ids = self.quotedb[nick].get_all_ids()
            strids = list()
            for x in ids:
                strids.append(str(x))
            self.msg_all(",".join(strids), targets)

        else:
            self.msg_all("No ID's for nickname:"+nick)

    def find_and_remember_quote_by_name(self, source, action, targets, message, m):
        '''
        Search the channel and find the quote to store
        '''
        try:
            results = self.search_logs_greedy(m.group('match'), name = m.group('nick'))
            if results:
                if len(results) > 1:
                    self.msg_all('Too many matches found, please refine your search', targets)

                else:
                    entry = self.store_quote(source, results[0])
                    self.msg_all('Stored:'+str(entry), targets)

            else:
                self.msg_all('No match found, please try another query', targets)

        except re.error:
            self.msg_all('Not a valid regex, please try another query', targets)


    def find_and_remember_quote(self, source, action, targets, message, m):
        """
        Searches the channel backlog with the given regex, if it finds more than one
        match it warns you and displays them, if it finds one match it stores that as a
        quote. If no match is found it tells you so

        regex is given by m.group("match")
        """
        try:
            results = self.search_logs_greedy(m.group("match"))
            if results:
                if len(results) > 1:
                    self.msg_all("Too many matches found, please refine your search", targets)

                else:
                    #if only one match store the quote along with some supporting info
                    #reminder: results[0] is a log entry instance, see commandbot for source of this
                    entry = self.store_quote(source, results[0])
                    self.msg_all("Stored:"+str(entry), targets)

            else:
                self.msg_all('No match found, please try another query', targets)

        except re.error:
            self.msg_all('Not a valid regex, please try another query', targets)

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
        quote_id = 0
        #convert to string as shelve+dbm doesn't support unicode
        name = str(entry.name)
        if name in self.quotedb:
            quote_data = self.quotedb[name]
            quote_id = quote_data.get_next_id()
            self.quotedb[name] = quote_data
        
        else:
            #initialise this new users necessary data
            self.quotedb[name] = QuoteData(name)
        
        #convert the combo of entry name + quote_id into a string to use as the index
        index = str((name, quote_id))
        #If this user and id combination already exists we have a serious problem
        if index in self.quotedb:
            #TODO raise a nicer exception here
            raise Exception("User and ID combination already exists")
        
        else:
            self.quotedb[index] = entry
            return entry

    def loop(self):
        with BotShelf('stored_quotes') as self.quotedb:
            super(QuoteBot, self).loop()



class QuoteData:
    """
    This class handles the id management for each nick in the database
    it provide support methods for freeing an id, getting the next id
    to use and providing a list of all id's.
    """

    def __init__(self, nick):
        self.current_id = 0
        self.nick = nick
        self.freed = list()
        self.in_use = list()
        self.in_use.append(self.current_id)

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
            self.current_id = quote_id
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
        return self.in_use

    def __str__(self):
        return self.nick+":"+str(self.current_id)

class BotShelf:
    '''
    Wrapper class over shelve to allow it to be used
    in with statements
    '''

    def __init__(self, name):
        '''
        Set up new BotShelf
        '''
        self.name = name

    def __enter__(self):
        '''
        Open shelve instance with self.name as filename
        creating it if it doesn't already exist
        '''
        self._internal = shelve.open(self.name, 'c')
        return self._internal

    def __exit__(self, type, value, traceback):
        '''
        On exit close internal db instance
        '''
        self._internal.close()

# run bot
qb = QuoteBot("irc.segfault.net.nz", 6667)
qb.join("#bots")
qb.loop()
