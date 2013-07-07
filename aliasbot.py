from commandbot import *
import sys


class AliasBot():
    '''
    An IRC Bot that can store, retrieve, and delete items.
    This bot stands as the simplest example of how to use
    the framework
    Contains a simple easter egg - HONK.
    '''
    def __init__(self, bot, module_name ='Alias', log_level = logging.INFO):
        #set up logging
        self.log = logging.getLogger(bot.log_name+'.'+module_name)
        self.log.setLevel(log_level)
        
        self.commands = [
                bot.command(r"^\w*", self.honk, direct=True),
                bot.command(r"^!learn (?P<abbr>\S+) as (?P<long>\S.*)$", self.learn),
                bot.command(r"^!forget (?P<abbr>\S+)", self.forget),
                bot.command(r"^!list_abbr$", self.list_abbrievations),
                bot.command(r"^!(?P<abbr>\S+)$", self.retrieve)
                ]
        
        self.events = []
        
        self.module_name = module_name
        self.bot = bot
        self.honk = "HONK"
        
        #get a reference to the bot database
        self.db = bot.db
        #set up a table for the module
        self.db.execute('''CREATE TABLE IF NOT EXISTS alias_module (short text UNIQUE NOT NULL, long text NOT NULL)''')
        
        
        
        #register as a module
        bot.add_module(module_name, self)
        
      
        
        self.log.info('Finished intialising {0}'.format(module_name))
        
    def alternate_honk(self):
        '''
        Alternate between HONK and honk.
        '''
        self.honk = self.honk.swapcase()
        return self.honk

    def honk(self, nick, nickhost, action, targets, message, m):
        '''
        Honk at anyone that highlighted us.
        '''
        self.log.debug('Honking at users on channels {0}'.format(targets))
        self.bot.msg_all(self.alternate_honk(), targets)

    def learn(self, nick, nickhost, action, targets, message, m):
        '''
        Learn a new abbreviation.
        '''
        abbr = m.group('abbr')
        long = m.group('long')
        try:
            self.db.execute('INSERT OR REPLACE INTO alias_module VALUES (?, ?)', [abbr, long])
            self.db.commit()
            self.log.info('Remembering {0} as {1}'.format(abbr, long))
            self.bot.msg_all('Remembering {0} as {1}'.format(abbr, long), targets)
        
        except sqlite3.Error as e:
            self.log.exception('Could not change/add {0} as {1}'.format(abbr, long))
            self.db.rollback()
            self.bot.msg_all('Could not change/add {0} as {1}'.format(abbr, long), targets)
            
            
    def forget(self, nick, nickhost, action, targets, message, m):
        '''
        Forget about an abbreviation.
        '''
        abbr = m.group('abbr')
        try:        
            if self.does_exist(abbr):
                self.db.execute('DELETE FROM alias_module WHERE short = ?', [abbr])
                self.db.commit()
                self.log.info('Successfully deleted {0} from database'.format(abbr))
                self.bot.msg_all('Successfully deleted {0} from database'.format(abbr), targets)
            
            else:
                self.log.warning('Abbr {0} does not exist'.format(abbr))
                self.bot.msg_all('{0} is not in the database'.format(abbr), targets)
            
        except sqlite3.Error as e:
            self.log.exception('Unable to delete {0}'.format(abbr))
            self.bot.msg_all('Unable to delete {0}'.format(abbr), targets)
            
    def retrieve(self, nick, nickhost, action, targets, message, m):
        '''
        Retrieves a long version of an abbrievated nick
        '''
        abbr = m.group('abbr')
        
        try:
            result = self.db.execute('SELECT long FROM alias_module WHERE short = ?', [abbr]).fetchone()
            if result:
                result = result[0]
                self.log.info('Retrieved {1} for {0}'.format(abbr, result))
                self.bot.msg_all(str(result), targets)
            
            else:
                self.log.warning('No result found for abbrievation {0}'.format(abbr))
                self.bot.msg_all('No result for abbrievation {0}'.format(abbr), targets)
        
        except sqlite3.Error as e:
            self.log.exception("Unable to retrieve {0}".format(abbr))
            self.bot.msg_all('Unable to retrieve {0}'.format(abbr), targets)
        

    def list_abbrievations(self, nick, nickhost, action, targets, message, m):
        """
        List all known abbrievation commands
        """
        try:
            results = self.db.execute('SELECT * FROM alias_module').fetchall()
            if results:
                self.log.info('Returning stored abbrievations, there are {0} abbrievations stored'.format(len(results)))
                self.bot.msg_all(",".join(map(str, results)), targets)
            
            else:
                self.log.debug('No stored abbrievations to return')
                self.bot.msg_all('No stored abbrievations yet', targets)
         
        except sqlite3.Error as e:
            self.log.exception("Unable to retrieve abbrievations")
            self.bot.msg_all("Unable to retrieve abbrievations", targets)
            
    def does_exist(self, abbr):
        '''
        Returns true if the item with abbr exist in the database
        If it does not it returns false
        '''
        try:
            result = self.db.execute('SELECT * FROM alias_module WHERE short = ?', [abbr]).fetchone()
            if result:
                return True
                
            else:
                return False
        
        except sqlite3.Error as e:
            self.log.error('Could not verify {0} exists'.format(abbr))
            return False
            
    def close(self):
        #we don't do anything special
        pass

if __name__ == '__main__':
    bot = CommandBot('Gamzee', 'irc.segfault.net.nz', 6667)
    mod = AliasBot(bot)
    bot.join('#bots')
    bot.loop()
