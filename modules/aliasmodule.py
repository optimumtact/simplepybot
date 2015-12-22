#/usr/bin/python3
import logging


class AliasModule:
    '''
    An IRC Bot that can store, retrieve, and delete items.
    This bot stands as the simplest example of how to use
    the framework
    Contains a simple easter egg - HONK.
    '''

    def __init__(self, bot, module_name):
        # set up logging
        self.log = logging.getLogger(bot.log_name + '.' + module_name)

        self.commands = [
            bot.command(r"^\w*", self.honk, direct=True),
            bot.command(r"^!learn (?P<abbr>\S+) as (?P<long>.+)$", self.learn, auth_level=20),
            bot.command(r"^!forget (?P<abbr>\S+)", self.forget, auth_level=20),
            bot.command(r"^!list_abbr$", self.list_abbrievations, private=True),
            bot.command(r"^!(?P<abbr>\S+)$", self.retrieve)
        ]

        self.events = []

        self.module_name = module_name
        self.bot = bot
        self.honk = "HONK"
        self.irc = bot.irc
        # get a reference to the bot database
        self.db = bot.db
        # set up a table for the module
        self.db.execute('''CREATE TABLE IF NOT EXISTS alias_module (short text UNIQUE NOT NULL, long text NOT NULL)''')


        self.log.info(u'Finished intialising {0}'.format(module_name))

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
        self.irc.msg_all(self.alternate_honk(), targets)

    def learn(self, nick, nickhost, action, targets, message, m):
        '''
        Learn a new abbreviation.
        '''
        abbr = m.group('abbr')
        replace = m.group('long')
        self.log.debug(u"Remembering {0} as {1}".format(abbr, replace))

        try:
            self.db.execute('INSERT OR REPLACE INTO alias_module VALUES (?, ?)', [abbr, replace])
            self.db.commit()
            self.irc.msg_all(u'Remembering {0} as {1}'.format(abbr, replace), targets)

        except sqlite3.Error as e:
            self.log.exception(u'Could not change/add {0} as {1}'.format(abbr, replace))
            self.db.rollback()
            self.irc.msg_all(u'Could not change/add {0} as {1}'.format(abbr, replace), targets)

    def forget(self, nick, nickhost, action, targets, message, m):
        '''
        Forget about an abbreviation.
        '''
        abbr = m.group('abbr')
        self.log.debug(u"Forgetting {0}".format(abbr))
        try:
            if self.does_exist(abbr):
                self.db.execute('DELETE FROM alias_module WHERE short = ?', [abbr])
                self.db.commit()
                self.irc.msg_all(u'Successfully deleted {0} from database'.format(abbr), targets)

            else:
                self.irc.msg_all(u'{0} is not in the database'.format(abbr), targets)

        except sqlite3.Error as e:
            self.log.exception(u'Unable to delete {0}'.format(abbr))
            self.irc.msg_all(u'Unable to delete {0}'.format(abbr), targets)

    def retrieve(self, nick, nickhost, action, targets, message, m):
        '''
        Retrieves a long version of an abbrievated nick
        '''
        abbr = m.group('abbr')
        self.log.debug(u"Retrieving {0}".format(abbr))
        try:
            result = self.db.execute('SELECT long FROM alias_module WHERE short = ?', [abbr]).fetchone()
            if result:
                result = result[0]
                self.irc.msg_all((result), targets)

            else:
                pass
                #self.irc.msg_all('No result for abbrievation {0}'.format(abbr), targets)

        except sqlite3.Error as e:
            self.log.exception(u"Unable to retrieve {0}".format(abbr))
            self.irc.msg_all(u'Unable to retrieve {0}'.format(abbr), targets)

    def list_abbrievations(self, nick, nickhost, action, targets, message, m):
        """
        List all known abbrievation commands
        """
        try:
            results = self.db.execute('SELECT * FROM alias_module').fetchall()
            if results:
                self.irc.msg_all(u",".join(map(str, results)), targets)

            else:
                self.irc.msg_all(u'No stored abbrievations yet', targets)

        except sqlite3.Error as e:
            self.log.exception(u"Unable to retrieve abbrievations")
            self.irc.msg_all(u"Unable to retrieve abbrievations", targets)

    def does_exist(self, abbr):
        '''
        Returns true if the item with abbr exist in the database
        If it does not it returns false
        '''
        self.log.debug(u"Testing if {0} exists".format(abbr))
        try:
            result = self.db.execute('SELECT * FROM alias_module WHERE short = ?', [abbr]).fetchone()
            if result:
                self.log.debug(u"It Does")
                return True

            else:
                self.log.debug(u"It doesn't")
                return False

        except sqlite3.Error as e:
            self.log.exception(u'Could not verify {0} exists'.format(abbr))
            return False

    def syntax(self):
        return  '''
                Alias module supports
                !learn {x} as {y}
                !{x}
                !forget {x}
                !list_abbr
                '''

    def close(self):
        # we don't do anything special
        pass
