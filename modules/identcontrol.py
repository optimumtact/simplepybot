import logging


class IdentHostControl:

    def __init__(self, bot, module_name):
        self.bot = bot
        self.log = logging.getLogger('{0}.{1}'.format(bot.log_name, module_name))
        self.irc = bot.irc
        self.ident = bot.ident
        self.module_name = module_name
        self.commands = [
            self.bot.command('nick (?P<ident>.*)', self.find_ident_nick),
            self.bot.command('ident (?P<nick>.*)', self.find_nick_ident),
            self.bot.command('users (?P<chan>.*)', self.find_users_in_channel),
            self.bot.command('channels (?P<nick>.*)', self.find_channels_user_in),
            self.bot.command('dump', self.dump_mappings, auth_level=20),
        ]
        self.events = []

    def find_ident_nick(self, nick, nickhost, action, targets, message, m):
        target_ident = m.group('ident')
        result = self.ident.nick_of_user(target_ident)
        if result:
            self.irc.msg_all(result, targets)
        else:
            self.irc.msg_all(u'No nick mapping for {0}'.format(target_ident), targets)

    def find_nick_ident(self, nick, nickhost, action, targets, message, m):
        target_nick = m.group('nick')
        result = self.ident.user_of_nick(target_nick)
        if result:
            self.irc.msg_all(result, targets)
        else:
            self.irc.msg_all(u'No ident mapping for {0}'.format(target_nick), targets)

    def find_users_in_channel(self, nick, nickhost, action, targets, message, m):
        chan = m.group('chan')
        result = self.ident.users_in_channel(chan)
        if result:
            self.irc.msg_all(u','.join(result), targets)
        else:
            self.irc.msg_all(u'No users in {0}'.format(chan), targets)

    def find_channels_user_in(self, nick, nickhost, action, targets, message, m):
        nick = m.group('nick')
        user = self.ident.user_of_nick(nick)
        if not user:
            return  # ignore invalid nicks

        channels = self.ident.channels_user_in(user)
        if channels:
            self.irc.msg_all(u','.join(channels), targets)
        else:
            self.irc.msg_all(u'I am not in any channels with {0}'.format(nick), targets)

    def dump_mappings(self, nick, nickhost, action, targets, message, m):
        self.ident.dump()
        self.irc.msg_all(u'Dumped mapping data to json file', targets)
