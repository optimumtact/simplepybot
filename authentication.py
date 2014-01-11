import sqlite3
import logging

class IdentAuth:
    def __init__(self, bot, module_name='identauth', log_level = logging.INFO):
        self.bot = bot
        self.log = logging.getLogger(bot.log_name+'.'+module_name)
        self.log.setLevel(log_level)
        self.db = bot.db
        self.irc = bot.irc
        self.module_name = module_name
        #set up our db table
        c = self.db.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS {0} (name TEXT UNIQUE NOT NULL, level INTEGER NOT NULL)".format(self.module_name))
        self.db.commit()
        self.bot.add_module(module_name, self)
        self.commands = [
                bot.command(r'!add user (?P<nickhost>\S+) (?P<level>\d+)', self.add_user_c, auth_level=20),
                bot.command(r'!update user (?P<nickhost>\S+) (?P<level>\d+)', self.update_user_c, auth_level=20),
                bot.command(r'!delete user (?P<nickhost>\S+)', self.del_user_c, auth_level=20),
                bot.command(r'!user level(?P<nickhost> \S+)?', self.show_user_c),
                #Negative auth means, no check at all. This should be the only place it's ever needed!
                bot.command(r'!bootstrap auth', self.bootstrap, auth_level=-1),
                ]

        self.events = []
        self.bootstrapped = False
        #Check we are bootstrapped
        if self.has_users():
            self.bootstrapped = True

        self.log.info('Finished intialising {0}'.format(module_name))
        
    def add_user_c(self, nick, nickhost, action, targets, message, m):
        nickhost = m.group('nickhost')
        level = int(m.group('level'))
        result = self.add_user(nickhost, level)
        self.irc.msg_all(result, targets)
    
    def update_user_c(self, nick, nickhost, action, targets, message, m):
        nickhost = m.group('nickhost')
        level = int(m.group('level'))
        result = self.update_user(nickhost, level)
        self.irc.msg_all(result, targets)
    
    def del_user_c(self, nick, nickhost, action, targets, message, m):
        nickhost = m.group('nickhost')
        result = self.delete_user(nickhost)
        self.irc.msg_all(result, targets)
    
    def show_user_c(self, nick, nickhost, action, targets, message, m):
        given_nickhost = m.group('nickhost')
        level = 100
        if given_nickhost:
            given_nickhost = given_nickhost.lstrip(' ')
            level = self.get_level(given_nickhost)
            self.irc.msg_all(level, targets)
        
        else:
            level = self.get_level(nickhost)
            self.irc.msg_all(level, targets)
        
    def bootstrap(self, nick, nickhost, action, targets, message, m):
        try:
           
            if self.has_users():
                self.log.warning('Attempted to bootstrap when module was already boostrapped')
                self.irc.msg_all("The authentication is already bootstrapped", targets)
            
            else:
                self.log.info(u'Bootstrap by user {0} successfull'.format(nick))
                self.irc.msg_all(self.add_user(nickhost, 0), targets)
                self.bootstrapped=True
         
        except sqlite3.Error as e:
            self.log.exception(u"Unable to boostrap auth")
            result = u'Unable to bootstrap due to database error {0}'.format(e.args[0])
            self.irc.msg_all(result, targets)
                
        
    def is_allowed(self, nick, nickhost, level):
        if not self.bootstrapped:
            print('not bootstrapped')
            return False

        try:
            c = self.db.cursor()
            c.execute('SELECT level FROM {0} WHERE name=?'.format(self.module_name), [nickhost])
            result = c.fetchone()
            if result:
                if level == 100:
                    return True #level 100 means no auth required
                users_level = result[0]
                self.log.debug('auth check for {0} requires <= {1} and has {2}'.format(nick, level, users_level))
                return users_level <= level
            
            else:
                self.log.warning('User auth check, but user {0} not in db'.format(nickhost))
                if level == 100:
                    return True #level 100 (default) means no auth required
                    
                else:
                    print('fail')
                    return False
        
        except sqlite3.Error as e:
            self.db.rollback()
            self.log.exception('Unable to check users auth')
            return False
    
    def is_user(self, nickhost):
        #search the db for our user to check if they exist before updating
        result = self.db.execute('SELECT level FROM {0} WHERE name=?'.format(self.module_name), [nickhost]).fetchall()
        if not result:
            self.log.debug('User {0} doesnt exist in db'.format(nickhost))
            return False
        
        else:
            self.log.debug('User {0} does exist in db'.format(nickhost))
            return True

    def has_users(self):
        try:
            result  = self.db.execute('SELECT * FROM {0}'.format(self.module_name)).fetchall()
            return len(result)
        
        except sqlite3.Error as e:
            self.log.exception('Unable to check if we have users')
            return 0

    def update_user(self, nickhost, level):
        try:
            if not self.is_user(nickhost):
                self.log.warning("Can't update a user that doesn't exist: {0}".format(nickhost))
                return "Unable to update user {0} as it doesn't exist in the database".format(nickhost)
            
            else:
                self.db.execute('UPDATE OR ABORT {0} SET level=? WHERE name=?'.format(self.module_name), [level, nickhost])
                self.db.commit()
                self.log.info('Successfully updated user {0}, with level {1}'.format(nickhost, level))
                return 'Successfully updated user {0}'.format(nickhost)
            
        except sqlite3.Error as e:
            self.db.rollback()
            self.log.error('Unable to update user {0} due to database error{1}'.format(nickhost,
                                                                                       e.args[0]))
            return 'Unable to update user {0} due to database error{1}'.format(nickhost,
                                                                               e.args[0])
            
    def add_user(self, nickhost, level):
        try:
            if self.is_user(nickhost):
                self.log.warning('Unable to add user who already exists {0}'.format(nickhost))
                return 'Unable to add user who already exists {0}'.format(nickhost)
                
            else:
                self.db.execute('INSERT INTO {0} VALUES(?, ?)'.format(self.module_name),[nickhost, level])
                self.db.commit()
                self.log.info('Successfully added user {0} with level {1}'.format(nickhost, level))
                return 'Successfully added user {0}'.format(nickhost)
        
        except sqlite3.Error as e:
            self.db.rollback()
            self.log.error('Unable to add user {0} due to database error{1}'.format(nickhost,
                                                                                     e.args[0]))
            return 'Unable to add user {0} due to a database error{1}'.format(nickhost,
                                                                               e.args[0])
    
    def delete_user(self, nickhost):
        try:
            if self.is_user(nickhost):
                self.db.execute('DELETE FROM {0} WHERE name=?'.format(self.module_name), [nickhost])
                self.db.commit()
                self.log.info('Succesfully deleted user {0}'.format(nickhost))
                return 'Succesfully deleted user {0}'.format(nickhost)
            
            else:
                self.log.warning('Unable to delete user {0}, they do not exist in the database'.format(nickhost))
                return 'Unable to delete user {0}, they do not exist in the database'.format(nickhost)
                
        except sqlite3.Error as e:
            self.db.rollback()
            self.log.error('Unable to delete user {0} due to database error{1}'.format(nickhost,
                                                                                        e.args[0]))
            return 'Unable to delete user {0} due to a database error {1}'.format(nickhost,
                                                                                   e.args[0])
    
    def get_level(self, nickhost):
        try:
            if self.is_user(nickhost):
                result = self.db.execute('SELECT level FROM {0} WHERE name=?'.format(self.module_name), [nickhost]).fetchone()
                if result:
                    result = result[0]
                    self.log.debug('{0} level is {1}'.format(nickhost, result))
                    return '{0} level is {1}'.format(nickhost, result)
                
                else:
                    self.log.warning('User {0} could not be found but should exist'.format(nickhost))
                    return 'User {0} could not be retrieved'.format(nickhost)
            
            else:
                self.log.debug('User {0} does not exist'.format(nickhost))
                return 'User {0} does not exist'.format(nickhost)
                
        except sqlite3.Error as e:
            self.log.exception('Could not get level for {0}'.format(nickhost))
            return 'Could not get level for {0}'.format(nickhost)


class DummyBot:
    def __init__(self):
        self.db = sqlite3.connect(':memory:')
        self.log_name = 'botcore'
        log_level = logging.DEBUG
        self.log = logging.getLogger(self.log_name)
        self.log.setLevel(log_level)
        h = logging.StreamHandler()
        f = logging.Formatter("%(name)s %(levelname)s %(funcName)s %(message)s")
        h.setFormatter(f)
        self.log.addHandler(h)
        
    def command(self, expr, func, direct=False, can_mute=True, private=False, auth_level=0):
        return func
    
    def add_module(self, module, name):
        pass
    
    def msg_all(self, msg, targets):
        pass

if __name__ == '__main__':
    bot = DummyBot()
    auth = IdentAuth(bot)
    print auth.add_user('oranges', 20)
    print auth.is_allowed('oranges', 'oranges', 20)
    print auth.is_allowed('oranges', 'oranges', 10)
    print auth.is_allowed('richard', 'richard', 20)
    print auth.add_user('oranges', 10)
    print auth.add_user('house', 10)
    print auth.is_allowed('house', 'house', 10)
    print auth.update_user('notauser', 20)
    print auth.update_user('oranges', 10)
    print auth.is_allowed('oranges','oranges', 10)
    print auth.is_allowed('notauser', 'notauser', 25)
    print auth.delete_user('house')
    print auth.is_allowed('house','house', 100)
    print auth.delete_user('notauser')
    

        
