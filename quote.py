from commandbot import *
import logging
import sqlite3
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
    def __init__(self, bot, module_name='Quotes', log_level = logging.DEBUG):
        self.commands = [
                bot.command(r"!quote (?P<id>\d+) *$", self.quote_by_id),
                bot.command(r"!quotes for (?P<nick>\S+)", self.quotes_for_name),
                bot.command(r"^!quote (?P<quote>.+) by (?P<nick>\S+)", self.add_quote),
                bot.command(r"^!quote (?:\d{2}:\d{2} )?<.?(?P<nick>\S+)> +(?P<quote>.+)", self.add_quote),
                bot.command(r"^!quotedel (?P<id>\d+)$", self.delete_quote, auth_level=30),
                ]
        self.events = []
        self.db = bot.db
        
        self.module_name = module_name
        self.bot = bot
        self.log = logging.getLogger("{0}.{1}".format(bot.log_name, module_name))
        self.log.setLevel(log_level)
        bot.add_module(module_name, self)
        self.module_name = module_name
        
        #I know that there could possibly be sql injection here, but if they have module name control they are trusted anyway
        self.db.execute('CREATE TABLE IF NOT EXISTS {0} (id INTEGER PRIMARY KEY, quote TEXT, nick TEXT)'.format(module_name))
        self.db.execute('CREATE INDEX IF NOT EXISTs quote_nick_index ON {0} (quote, nick)'.format(module_name))
        self.db.execute('CREATE INDEX IF NOT EXISTS nick_index ON {0} (nick)'.format(module_name))
        self.db.commit()
        self.log.info('Finished intialising {0}'.format(module_name))
        
    def quote_by_id(self, nick, nickhost, action, targets, message, m):
        '''
        Find a quote with the given id
        '''
        id = int(m.group('id'))
        self.log.debug("Finding quote with id {0}".format(id))
        try:
            result = self.db.execute('SELECT * FROM {0} WHERE id=?'.format(self.module_name), [id]).fetchone()
            if result:
                self.bot.msg_all("<{0}> {1}".format(result[1], result[2]), targets)
            
            else:
                self.bot.msg_all('No quote with that id'.format(id), targets)
         
        except sqlite3.Error as e:
            self.log.exception('Unable to get quote with id {0}'.format(id))
            self.bot.msg_all('Unable to retrieve quote from database'.format(id))
        
    def quotes_for_name(self, nick, nickhost, action, targets, message, m):
        '''
        Find all quotes with given nick
        '''
        given_nick = m.group('nick')
        self.log.debug("Finding all quotes by nick {0}".format(given_nick))
        try:
            result = self.db.execute('SELECT * FROM {0} WHERE nick = ?'.format(self.module_name), [given_nick]).fetchall()
            if result:
                result = ",".join(map(self.print_result, result))
                self.bot.msg_all(result, targets)
            
            else:
                self.bot.msg_all('User {0} has no quotes in quote database'.format(given_nick), targets)
        
        except sqlite3.Error as e:
            self.log.exception('Unable to get quotes for {0} due to database error'.format(given_nick))
            self.bot.msg_all('Unable to retrieve quotes for user {0}'.format(given_nick), targets)
    
    def add_quote(self, nick, nickhost, action, targets, message, m):
        '''
        Add a quote for a given user
        '''
        given_nick = m.group('nick')
        quote = m.group('quote')
        self.log.debug("Adding quote by {0}, {1}".format(given_nick, quote))
        try:
            self.db.execute('INSERT INTO {0} (quote, nick) VALUES (?, ?)'.format(self.module_name), [quote, given_nick])
            self.db.commit()
            result = self.db.execute('SELECT id FROM {0} WHERE quote=? AND nick=?'.format(self.module_name), [quote, given_nick]).fetchone()
            if not result:
                self.log.warning('Could not find quote {0} for nick {1} after adding it'.format(quote, given_nick))
                self.bot.msg_all('Could not find quote after adding it')
                return
            
            id = result[0]
            self.bot.msg_all("Added quote successfully, its id is {0}".format(id), targets)
        
        except sqlite3.Error as e:
            self.db.rollback()
            self.log.exception("Unable to add quote '{0}' for nick {1}, requested by {2}".format(quote, given_nick, nick))
            self.bot.msg_all('Unable to add quote due to database error', targets)
    
    def delete_quote(self, nick, nickhost, action, targets, message, m):
        '''
        Remove quote with given id
        '''
        id = int(m.group('id'))
        try:
            result = self.db.execute('SELECT * FROM {0} WHERE id = ?'.format(self.module_name), [id]).fetchone()
            if not result:
                self.log.debug('No quote with id {0} to delete'.format(id))
                self.bot.msg_all("There is no quote with that id", targets)
            else:
                self.db.execute('DELETE FROM {0} WHERE id = ?'.format(self.module_name), [id])
                self.db.commit()
                self.bot.msg_all('Quote deleted', targets)
                
        except sqlite3.Error as e:
            self.db.rollback()
            self.log.exception("Unable to delete quote with id {0}".format(id))
            self.bot.msg_all("Unable to delete quote due to database error", targets)
            
    def print_result(self, result):
        return '\"{0}\" -{1}'.format(result[1], result[0])
    
    def syntax(self):
        return '''
               Quote modules supports
               !quotes for {user}
               !quote with id {some id}
               !quote {some string quote} by {some nick}
               !quote 16:40 <{nick}> definitely time for a syntax command
               '''

    def close(self):
        self.log.info("Finished cleaning up {0}".format(self.module_name))
        #no cleanup necessary
        pass
        
if __name__ == '__main__':
    #basic stream handler
    h = logging.StreamHandler()
    h.setLevel(logging.DEBUG)
    #format to use
    f = logging.Formatter("%(name)s %(levelname)s %(message)s")
    h.setFormatter(f)
    bot = CommandBot('quotebot', 'irc.segfault.net.nz', 6667, log_handlers=[h])
    #add the quote module
    mod = QuoteBot(bot, log_level = logging.DEBUG)
    bot.join('#bots')
    bot.loop()
