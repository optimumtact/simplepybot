import logging
import sqlite3

class dht_bootstrap:
    def __init__(self, bot, module_name='dht_bootstrap', log_level=logging.DEBUG):
        '''
        Initialise the DHT module
        '''
        
        #remember some pertinent args
        self.bot = bot
        self.db = bot.db
        self.module_name = module_name
        
        self.log = logging.getLogger(bot.log_name+'.'+module_name)
        self.log.setLevel(log_level)
        #set up our db table
        c = self.db.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS {0} (ip TEXT UNIQUE NOT NULL, key INTEGER NOT NULL)".format(self.module_name))
        self.db.commit()
        
        #register ourselves
        self.bot.add_module(module_name, self)
        
        self.commands = [
                bot.command(r'!add server (?P<ip>\d{0,3}.\d{0,3}.\d{0,3}.\d{0,3}) (?P<key>\S+)', self.add_dht),
                bot.command(r"!del server (?P<ip>\d{0,3}.\d{0,3}.\d{0,3}.\d{0,3}) (?P<key>\S+)", self.del_dht, auth_level=30),
                bot.command(r"!list servers", self.list_dht),
                ]

        self.events = []
        self.log.info('Finished intialising {0}'.format(module_name))
    
    def add_dht(self, nick, nickhost, command, targets, message, m):
        ip = m.group('ip')
        key = m.group('key')
        try:
            self.db.execute("INSERT OR REPLACE INTO {0} (ip, key) VALUES (?, ?)".format(self.module_name), [ip, key])
            self.db.commit()
            result = self.db.execute("SELECT * FROM {0} WHERE ip=? AND key=?".format(self.module_name), [ip, key]).fetchone()
            if not result:
                self.log.warning("Couldn't find ip {0} and key {1} after adding them".format(ip, key))
                self.bot.msg_all("Unable to complete request due to db error", targets)
            
            else:
                self.log.debug("Added dht entry {0}:{1}".format(ip, key))
                self.bot.msg_all("Successful", targets)
        
        except sqlite3.Error as e:
            self.db.rollback()
            self.log.exception("Unable to add dht {0}:{1}".format(ip, key))
            self.bot.msg_all("Unable to add entry due to database error")
    
    def del_dht(self, nick, nickhost, command, targets, message, m):
        ip = m.group('ip')
        key = m.group('key')
        try:
            result = self.db.execute("SELECT * FROM {0} WHERE ip=? AND key=?".format(self.module_name), [ip, key]).fetchone()
            if not result:
                self.log.warning("Tried to delete not existent dht {0}:{key}")
                self.bot.msg_all("This bootstrap server is not in my database")
            
            else:
                self.db.execute("DELETE FROM {0} WHERE ip=? and key=?".format(self.module_name), [ip, key])
                self.db.commit()
                self.log.debug("deleted dht entry {0}:{1}".format(ip, key))
                self.bot.msg_all("Successful", targets)
        
        except sqlite3.Error as e:
            self.db.rollback()
            self.log.exception("Unable to del dht {0}:{1}".format(ip, key))
            self.bot.msg_all("Unable to delete entry due to database error")
    
    def list_dht(self, nick, nickhost, command, targets, message, m):
        try:
            results = self.db.execute("SELECT * FROM {0}".format(self.module_name)).fetchall()
            if not results:
                self.log.debug("No bootstrap servers in database")
                self.bot.msg_all("There are no bootstrap servers in my database")
            
            else:
                string = ", ".join(map(self.print_server, results))
                self.bot.msg_all(string, targets)
        
        except sqlite3.Error as e:
            self.log.exception("Unable to list bootstrap servers")
            self.bot.msg_all("Unable to list bootstrap servers due to database error")
            
    def print_server(self, result):
        return "{0}:{1}".format(result[0], result[1])
    
    def syntax(self):
        return "!add server {ip} {pubkey} - adds this server to the list\n!del server {ip} {pubkey} - requires auth\n!list servers - list all bootstrap server"
    
    def close(self):
        pass