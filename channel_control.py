from commandbot import event, command

class ChannelControlModule():

    def __init__(self, bot):
        self.bot = bot
        print(bot.nick)
        self.commands = [
                command(bot.nick+':? join (?P<channel>[#|\w]+)', self.join),
                command(bot.nick+':? leave (?P<channel>[#\w]+)', self.leave),
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
