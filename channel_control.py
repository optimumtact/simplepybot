from commandbot import event, command, CommandBot

class ControlModule():

    def __init__(self, bot):
        self.bot = bot
        self.commands = [
                command(bot.nick+':? join channel (?P<channel>[#|\w]+)', self.join),
                command(bot.nick+':? leave channel (?P<channel>[#|\w]+)', self.leave),
                command(bot.nick+':? msg user (?P<user>\w+) (?P<message>[ |\w]+', self.msg_user),
                ]
        self.events = []
        self.channels = []
        self.registered = False


    def join(self, source, action, targets, message, m):
        '''
        Join a channel live
        '''
        channel = m.group('channel')
        if not channel.startswith('#'):
            channel = '#'+channel

        if channel not in self.channels:
            self.bot.join(channel)
            self.channels.append(channel)

    def leave(self, source, action, targets, message, m):
        '''
        leave a channel live
        '''
        channel = m.group('channel')
        if not channel.startswith('#'):
            channel = '#'+channel

        if channel in self.channels:
            self.bot.leave(channel)
            self.channels.remove(channel)

    def msg_user(self, source, action, targets, message, m):
        '''
        Send the user a message from the bot
        '''
        self.bot.msg(m.group('message'), m.group('user'))

if __name__ == '__main__':
    bot = CommandBot('Annoy', 'irc.segfault.net.nz', 6667)
    bot.join('#bots')
    mod = ControlModule('Command', bot)
    bot.loop()
