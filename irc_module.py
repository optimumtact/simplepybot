from commandbot import event, command

class IrcModule():

    def __init__(self, bot):
        self.bot = bot
        self.commands = [
                command(bot.nick+':? join (?P<channel>/s+)', self.live_join),
                command(bot.nick+':? leave (?P<channel>/s+)', self.live_leave),
                ]
        self.events = [
                event('001', self._join),
                ]
        self.channels = []
        self.registered = False

    def msgs_all(self, msgs, channels):
        """
        Accepts a list of messages to send to a list of channels
        msgs: A list of messages to send
        channels: A list of targets to send it to
        """
        for channel in channels:
            for message in msgs:
                self.msg(message, channel)

    def msg_all(self, message, channels):
        """
        Accepts a message to send to a list of channels
        message: the message to send
        channels: A list of targets to send it to
        """
        for channel in channels:
            self.msg(message, channel)

    def msg(self, message, channel):
        '''
        Send a message to a specific target.
        message: the message to send
        channel: the target to send it to
        '''
        self.bot.send('PRIVMSG ' + channel + ' :' + message)

    def join(self, channel):
        '''
        Join a channel.
        channel: the channel to join
        The channel should contain one or more # symbols as needed.

        '''
        if self.registered:
            self.bot.send('JOIN ' + channel)

        else:
            self.channels.append(channel)

    def _join(self, source, action, args, message):
        '''
        Join all channels in the channels variable
        '''
        self.registered = True
        for channel in self.channels:
            self.join(channel)

    def live_join(self, source, action, targets, message, m):
        '''
        Join a channel live
        '''
        self.join(m.group('channel'))

    def live_leave(self, source, action, targets, message, m):
        '''
        leave a channel live
        '''
        self.leave(m.group('channel'))

    def quit(self, message):
        '''
        Disconnects from a server with a given QUIT message.
        message: message to display with quit
        '''
        self.bot.send('QUIT :' + message)

    def leave(self, channel, message=None):
        '''
        Leaves a channel, optionally sending a message to the channel first.
        channel: Channel to leave
        message: optional message to send first
        XXX: The message should probably be the PART message
        '''
        if message:
            self.msg(message, channel)
        self.bot.send('PART ' + channel)

