import logging


class IdentControl:

    def __init__(self, bot, module_name='identcontrol', log_level=logging.INFO):
        self.bot = bot
        self.log = logging.getLogger('{0}.{1}'.format(bot.log_name, module_name))
        self.log.setLevel(log_level)
        self.irc = bot.irc
        self.ident = bot.ident
        self.module_name = module_name
        self.commands = [
            self.bot.command('nick (?P<nick>.*)', self.find_nick),
            self.bot.command('nickhost (?P<nickhost>.*)', self.find_nick_host),
            self.bot.command('users (?P<chan>.*)', self.find_users_in_channel),
            self.bot.command('channels (?P<nick>.*)', self.find_channels_user_in),
        ]
        self.events = []
        self.bot.add_module(module_name, self)

    def find_nick(self, nick, nickhost, action, targets, message, m):
        nick = m.group('nick')
        result = self.ident.user_of_nick(nick)
        if result:
            if self.ident.is_user_in_channel(result, targets[0]):
                self.irc.msg_all(result, targets)
            else:
                self.irc.msg_all(u'{0} is not in this channel'.format(nick), targets)

    def find_nick_host(self, nick, nickhost, action, targets, message, m):
        nickhost = m.group('nickhost')
        result = self.ident.nick_of_user(nickhost)
        self.irc.msg_all(result, targets)

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
