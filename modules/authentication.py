import sqlite3
import logging
import event_util as eu
import numerics as nu


class BasicAuthEngine:

    def __init__(self, bot, module_name):
        self.bot = bot
        self.ident = bot.ident
        self.log = logging.getLogger(bot.log_name + '.' + module_name)
        self.db = bot.db
        self.irc = bot.irc
        self.module_name = module_name
        # set up our db table
        c = self.db.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS {0} (name TEXT UNIQUE NOT NULL, level INTEGER NOT NULL)".format(self.module_name))
        self.db.commit()
        self.commands = [
            bot.command(r'add user (?P<nick>\S+) (?P<level>\d+)', self.add_user_c, auth_level=20),
            bot.command(r'update user (?P<nick>\S+) (?P<level>\d+)', self.update_user_c, auth_level=20),
            bot.command(r'delete user (?P<nick>\S+)', self.del_user_c, auth_level=20),
            bot.command(r'user level (?P<nick>\S+)', self.show_user_c),
            bot.command(r'ignore user (?P<nick>\S+)', self.ignore_user_c, auth_level=20),
            bot.command(r'unignore user (?P<nick>\S+)', self.unignore_user_c, auth_level=20),
            # Negative auth means, no check at all. This should be the only place it's ever needed!
            bot.command(r'bootstrap auth', self.bootstrap, auth_level=-1),
        ]

        self.events = []
        self.bootstrapped = False
        # Check we are bootstrapped
        if self.has_users():
            self.bootstrapped = True

        self.log.info(u'Finished intialising {0}'.format(module_name))

    def add_user_c(self, nick, nickhost, action, targets, message, m):
        nick = m.group('nick')
        nickhost = self.ident.user_of_nick(nick)
        if(nickhost):
            level = int(m.group('level'))
            result = self.add_user(nickhost, level)
            self.irc.msg_all(result, targets)
        else:
            self.irc.msg_all(u'No known user by the nick {0}'.format(nick), targets)
            self.log.debug(u'host mapping not found for nickname {0}'.format(nick))

    def update_user_c(self, nick, nickhost, action, targets, message, m):
        nick = m.group('nick')
        nickhost = self.ident.user_of_nick(nick)
        if(nickhost):
            level = int(m.group('level'))
            result = self.update_user(nickhost, level)
            self.irc.msg_all(result, targets)
        else:
            self.irc.msg_all(u'No known user by the nick {0}'.format(nick), targets)
            self.log.debug(u'host mapping not found for nickname {0}'.format(nick))

    def del_user_c(self, nick, nickhost, action, targets, message, m):
        nick = m.group('nick')
        nickhost = self.ident.user_of_nick(nick)
        if(nickhost):
            result = self.delete_user(nickhost)
            self.irc.msg_all(result, targets)
        else:
            self.irc.msg_all(u'No known user by the nick {0}'.format(nick), targets)
            self.log.debug(u'host mapping not found for nickname {0}'.format(nick))

    def show_user_c(self, nick, nickhost, action, targets, message, m):
        nick = m.group('nick')
        nickhost = self.ident.user_of_nick(nick)
        if(nickhost):
            level = 100
            level = self.get_level(nickhost)
            self.irc.msg_all(level, targets)
        else:
            self.irc.msg_all(u'No known user by the nick {0}'.format(nick), targets)
            self.log.debug(u'host mapping not found for nickname {0}'.format(nick))

    def ignore_user_c(self, nick, nickhost, action, targets, message, m):
        nick = m.group('nick')
        nickhost = self.ident.user_of_nick(nick)
        if(nickhost):
            level = 101  # Higher than currently max, so will be ignored
            if(self.is_user(nickhost)):
                result = self.update_user(nickhost, level)
                self.irc.msg_all(u'User {0} is now being ignored'.format(nick), targets)
            else:
                result = self.add_user(nickhost, level)
                self.irc.msg_all(u'User {0} is now being ignored'.format(nick), targets)

        else:
            self.irc.msg_all(u'No known user by the nick {0}'.format(nick), targets)
            self.log.debug(u'host mapping not found for nickname {0}'.format(nick))

    def unignore_user_c(self, nick, nickhost, action, targets, message, m):
        nick = m.group('nick')
        nickhost = self.ident.user_of_nick(nick)
        if(nickhost):
            result = self.delete_user(nickhost)
            self.irc.msg_all(u'User {0} is now being unignored'.format(nick), targets)

        else:
            self.irc.msg_all(u'No known user by the nick {0}'.format(nick), targets)
            self.log.debug(u'host mapping not found for nickname {0}'.format(nick))

    def bootstrap(self, nick, nickhost, action, targets, message, m):
        try:

            if self.has_users():
                self.log.warning(u'Attempted to bootstrap when module was already boostrapped')
                self.irc.msg_all(u"The authentication is already bootstrapped", targets)

            else:
                self.log.info(u'Bootstrap by user {0} successfull'.format(nick))
                self.irc.msg_all(self.add_user(nickhost, 0), targets)
                self.bootstrapped = True

        except sqlite3.Error as e:
            self.log.exception(u"Unable to boostrap auth")
            result = u'Unable to bootstrap due to database error {0}'.format(e.args[0])
            self.irc.msg_all(result, targets)

    def is_allowed(self, nick, nickhost, level):
        if not self.bootstrapped:
            self.log.debug(u'auth check when not bootstrapped')
            return False

        try:
            c = self.db.cursor()
            c.execute('SELECT level FROM {0} WHERE name=?'.format(self.module_name), [nickhost])
            result = c.fetchone()
            if result:
                users_level = result[0]
            else:
                users_level = 100
                self.log.debug(u'User auth check, but user {0} not in db - set to 100'.format(nickhost))

            self.log.debug(u'auth check for {0} requires <= {1} and has {2}'.format(nick, level, users_level))
            return users_level <= level

        except sqlite3.Error as e:
            self.db.rollback()
            self.log.exception(u'Unable to check users auth')
            return False

    def is_user(self, nickhost):
        # search the db for our user to check if they exist before updating
        result = self.db.execute('SELECT level FROM {0} WHERE name=?'.format(self.module_name), [nickhost]).fetchall()
        if not result:
            self.log.debug(u'User {0} doesnt exist in db'.format(nickhost))
            return False

        else:
            self.log.debug(u'User {0} does exist in db'.format(nickhost))
            return True

    def has_users(self):
        try:
            result = self.db.execute('SELECT * FROM {0}'.format(self.module_name)).fetchall()
            return len(result)

        except sqlite3.Error as e:
            self.log.exception(u'Unable to check if we have users')
            return 0

    def update_user(self, nickhost, level):
        try:
            if not self.is_user(nickhost):
                self.log.warning(u"Can't update a user that doesn't exist: {0}".format(nickhost))
                return u"Unable to update user {0} as it doesn't exist in the database".format(nickhost)

            else:
                self.db.execute('UPDATE OR ABORT {0} SET level=? WHERE name=?'.format(self.module_name), [level, nickhost])
                self.db.commit()
                self.log.info(u'Successfully updated user {0}, with level {1}'.format(nickhost, level))
                return u'Successfully updated user {0}'.format(nickhost)

        except sqlite3.Error as e:
            self.db.rollback()
            self.log.error(u'Unable to update user {0} due to database error{1}'.format(nickhost,
                                                                                        e.args[0]))
            return u'Unable to update user {0} due to database error{1}'.format(nickhost,
                                                                                e.args[0])

    def add_user(self, nickhost, level):
        try:
            if self.is_user(nickhost):
                self.log.warning(u'Unable to add user who already exists {0}'.format(nickhost))
                return u'Unable to add user who already exists {0}'.format(nickhost)

            else:
                self.db.execute('INSERT INTO {0} VALUES(?, ?)'.format(self.module_name), [nickhost, level])
                self.db.commit()
                self.log.info(u'Successfully added user {0} with level {1}'.format(nickhost, level))
                return u'Successfully added user {0}'.format(nickhost)

        except sqlite3.Error as e:
            self.db.rollback()
            self.log.error(u'Unable to add user {0} due to database error{1}'.format(nickhost,
                                                                                     e.args[0]))
            return u'Unable to add user {0} due to a database error{1}'.format(nickhost,
                                                                               e.args[0])

    def delete_user(self, nickhost):
        try:
            if self.is_user(nickhost):
                self.db.execute('DELETE FROM {0} WHERE name=?'.format(self.module_name), [nickhost])
                self.db.commit()
                self.log.info(u'Succesfully deleted user {0}'.format(nickhost))
                return u'Succesfully deleted user {0}'.format(nickhost)

            else:
                self.log.warning(u'Unable to delete user {0}, they do not exist in the database'.format(nickhost))
                return u'Unable to delete user {0}, they do not exist in the database'.format(nickhost)

        except sqlite3.Error as e:
            self.db.rollback()
            self.log.error(u'Unable to delete user {0} due to database error{1}'.format(nickhost,
                                                                                        e.args[0]))
            return u'Unable to delete user {0} due to a database error {1}'.format(nickhost,
                                                                                   e.args[0])

    def get_level(self, nickhost):
        try:
            if self.is_user(nickhost):
                result = self.db.execute('SELECT level FROM {0} WHERE name=?'.format(self.module_name), [nickhost]).fetchone()
                if result:
                    result = result[0]
                    self.log.debug(u'{0} level is {1}'.format(nickhost, result))
                    return u'{0} level is {1}'.format(nickhost, result)

                else:
                    self.log.warning(u'User {0} could not be found but should exist'.format(nickhost))
                    return u'User {0} could not be retrieved'.format(nickhost)

            else:
                self.log.debug(u'User {0} does not exist'.format(nickhost))
                return u'User {0} does not exist'.format(nickhost)

        except sqlite3.Error as e:
            self.log.exception(u'Could not get level for {0}'.format(nickhost))
            return u'Could not get level for {0}'.format(nickhost)


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
    print( auth.add_user('oranges', 20) )
    print( auth.is_allowed('oranges', 'oranges', 20) ) 
    print( auth.is_allowed('oranges', 'oranges', 10) )
    print( auth.is_allowed('richard', 'richard', 20) )
    print( auth.add_user('oranges', 10) )
    print( auth.add_user('house', 10) )
    print( auth.is_allowed('house', 'house', 10) )
    print( auth.update_user('notauser', 20) )
    print( auth.update_user('oranges', 10) )
    print( auth.is_allowed('oranges', 'oranges', 10) ) 
    print( auth.is_allowed('notauser', 'notauser', 25) )
    print( auth.delete_user('house') )
    print( auth.is_allowed('house', 'house', 100) )
    print( auth.delete_user('notauser') )
