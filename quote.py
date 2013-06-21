from commandbot import *
from log_search import LogModule
import shelve

#TODO implement delete command for quotes, clean up quote command syntax
class QuoteBot():
    """
    A bot that provides quote services to a channel

    Supported commands:
        !quote some string: search the backlog for any message matching some string and store that as a quote
        !quote some string by user: search the backlog for any message matching some string and made by user and store that as a quote
        !quotes for user: return list of quotes for user
        !quote id: return quote with given id

    """
    nick = "quotebot"
    def __init__(self, bot, module_name='Quotes'):
        self.commands = [
                command(r"!quote (?P<id>\d+) by (?P<nick>\S+)", self.quote_by_id),
                command(r"^!quote (?P<match>[\w\s]+) by (?P<nick>\S+)", self.find_and_remember_quote_by_name),
                command(r"!quotes for (?P<nick>\S+)", self.quote_ids_for_name),
                command(r"^!quote (?P<match>[\w\s]+)", self.find_and_remember_quote),
                ]
        self.events = []

        self.module_name = module_name
        self.bot = bot
        self.log_module = bot.get_module('Logging')
        bot.add_module(module_name, self)

    def quote_by_id(self, nick, nickhost, action, targets, message, m):
        """
        Determine if the id given by m.group("id") is assigned for m.group("nick")
        and then return the quote stored under that combination
        """
        nick = str(m.group("nick"))
        quote_id = int(m.group("id"))
        ids_index = str((self.module_name, nick))

        if ids_index in self.bot.storage:
            quote_ids = self.bot.storage[ids_index]
            if quote_id in quote_ids:
                index = str((self.module_name, (nick, quote_id)))
                if index in self.bot.storage:
                    self.bot.msg_all(str(self.bot.storage[index]), targets)

                else:
                    self.bot.msg_all('Missing quote for index:'+index, targets)

            else:
                self.bot.msg_all("There is no quote with that id for this user", targets)

        else:
            self.bot.msg_all("There are no quotes for that user", targets)

    def quote_ids_for_name(self, nick, nickhost, action, targets, message, m):
        """
        Determine if the name stored in m.group("nick") has quotes stored in the quotedb
        and is so return a list of them to the channel for display
        """
        nick = str(m.group("nick"))
        index = str((self.module_name, nick))
        if index in self.bot.storage:
            ids = self.bot.storage[index]
            strids = list()
            for x in ids:
                strids.append(str(x))
            self.bot.msg_all('['+','.join(strids)+']', targets)

        else:
            self.bot.msg_all("No ID's for nickname:"+nick)

    def find_and_remember_quote_by_name(self, nick, nickhost, action, targets, message, m):
        '''
        Search the channel and find the quote to store
        '''
        try:
            results = self.log_module.search_logs_greedy(m.group('match'), name = m.group('nick'))
            if results:
                if len(results) > 1:
                    self.bot.msg_all('Too many matches found, please refine your search', targets)

                else:
                    entry = self.store_quote(nick, results[0])
                    self.bot.msg_all('Stored:'+str(entry), targets)

            else:
                self.bot.msg_all('No match found, please try another query', targets)

        except re.error:
            self.bot.msg_all('Not a valid regex, please try another query', targets)


    def find_and_remember_quote(self, nick, nickhost, action, targets, message, m):
        """
        Searches the channel backlog with the given regex, if it finds more than one
        match it warns you and displays them, if it finds one match it stores that as a
        quote. If no match is found it tells you so

        regex is given by m.group("match")
        """
        try:
            results = self.log_module.search_logs_greedy(m.group("match"))
            if results:
                if len(results) > 1:
                    self.bot.msg_all("Too many matches found, please refine your search", targets)

                else:
                    #if only one match store the quote along with some supporting info
                    #reminder: results[0] is a log entry instance, see commandbot for source of this
                    entry = self.store_quote(nick, results[0])
                    self.bot.msg_all("Stored:"+str(entry), targets)

            else:
                self.bot.msg_all('No match found, please try another query', targets)

        except re.error:
            self.bot.msg_all('Not a valid regex, please try another query', targets)

    def store_quote(self, nick, entry):
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
        #convert to string for indexing
        name = str(entry.name)
        index = str((self.module_name, name))
        if index in self.bot.storage:
            #get the list of used ids
            quote_data = self.bot.storage[index]
            #search through it to find first gap or next value
            quote_id = find_next_id(quote_data)
            #insert the quote_id into the list and store the newly changed list
            #we use insert ast the find_next_id method expects a sorted list
            quote_data.insert(quote_id, quote_id)
            self.bot.storage[index] = quote_data

        else:
            #initialise this new users ids list
            self.bot.storage[index] = [0]

        #convert the combo of entry name + quote_id into a string to use as the index
        index = str((self.module_name,(name, quote_id)))
        #If this user and id combination already exists we have a collision
        if index in self.bot.storage:
            #TODO raise a nicer exception here
            raise Exception("User and ID collision:"+str((name, quote_id)))

        else:
            self.bot.storage[index] = entry
            return entry

def find_next_id(id_list):
    length = len(id_list)
    for index, q_id in enumerate(id_list):
        if index+1 < length:
            #while we still can move along
            next_id = id_list[index+1]
        else:
            #end of list, return q_id + 1
            next_id = q_id + 1
            return q_id + 1

        if q_id + 1 < next_id:
            # we found a gap in id's
            return q_id + 1

if __name__ == '__main__':
    bot = CommandBot('betterthanscorecard', 'irc.segfault.net.nz', 6667)
    #add the log and quote modules
    #note Quotebot relies on log module
    mod = LogModule(bot)
    mod = QuoteBot(bot)
    bot.join('#bots')
    bot.loop()
