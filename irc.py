from network import IrcSocket
class IrcConnection(IrcSocket):
    """
    Represents a wrapper for the network class, provides convienience methods
    for irc such as msg and join/leave channels
    """
    def __init__(self, name, server, port):
        assert server and port
        super(IrcConnection, self).__init__()
        self.connect((server, port), name, "bot@"+server, server, name)

        self.name = name
        self.server = server
        self.port = port

    def msgs_all(self, msgs, channels):
        """
        Accepts a list of msgs to send to a list of channels
        """
        for channel in channels:
            for message in msgs:
                self.msg(message, channel)

    def msg_all(self, message, channels):
        """
        Accepts a message to send to a list of channels
        """
        for channel in channels:
            self.msg(message, channel)

    def msg(self, message, channel):
        '''
        Send a message to a specific target.
        '''
        self.send('PRIVMSG ' + channel + ' :' + message)

    def join(self, channel):
        '''
        Join a channel.

        The channel should contain one or more # symbols as needed.
        '''
        self.send('JOIN ' + channel)

    def quit(self, message):
        '''
        Disconnects from a server with a given QUIT message.
        '''
        self.send('QUIT :' + message)

    def leave(self, channel, message):
        '''
        Leaves a channel, optionally sending a message to the channel first.

        XXX: The message should probably be the PART message
        '''
        if message:
            self.msg(message, channel)
        self.send('PART ' + channel)

