from commandbot import CommandBot

class ControlModule():

    def __init__(self, bot, module_name="Chan_Control"):
        self.bot = bot
        bot.add_module(module_name, self)
        self.commands = [
                bot.command('join channel (?P<channel>[#|\w]+)', self.join, direct=True),
                bot.command('leave channel (?P<channel>[#|\w]+)', self.leave, direct=True),
                bot.command('annoy user (?P<user>\w+) (?P<message>.+)', self.msg_user, direct=True),
                ]
        self.events = []
        self.channels = []
        self.registered = False


    def join(self, nick, nickhost, action, targets, message, m):
        '''
        Join a channel live
        '''
        channel = m.group('channel')
        if not channel.startswith('#'):
            channel = '#'+channel

        if channel not in self.channels:
            self.bot.join(channel)
            self.channels.append(channel)
            
        else:
            self.bot.msg_all("I am in that channel already", targets)

    def leave(self, nick, nickhost, action, targets, message, m):
        '''
        leave a channel live
        '''
        channel = m.group('channel')
        if not channel.startswith('#'):
            channel = '#'+channel

        if channel in self.channels:
            self.bot.leave(channel)
            self.channels.remove(channel)
            self.bot.msg_all("Left that channel", targets)
        
        else:
            self.bot.msg_all("I am not in that channel", targets)

    def msg_user(self, nick, nickhost, action, targets, message, m):
        '''
        Send the user a message from the bot
        '''
        self.bot.msg(m.group('message'), m.group('user'))
    
    def quit():
        pass #Nothing special

if __name__ == '__main__':
    bot = CommandBot('Testing', 'irc.segfault.net.nz', 6667)
    bot.join('#bots')
    mod = ControlModule(bot)
    bot.loop()
