from network import IrcSocket
class IrcConnect(IrcSocket):
    """
    Represents a wrapper for the network class, provides convienience methods
    for irc such as msg and join/leave channels
    """
    def __init__(self, name, server, port):
        assert server and port
        super(IrcConnect, self).__init__()
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
        self.send('PRIVMSG ' + channel + ' :' + message)

    def join(self, channel):
        self.send('JOIN ' + channel)

    def quit(self, message):
        self.send('QUIT :' + message)

    def leave(self, channel, message):
        if message:
            self.msg(message, channel)
        self.send('PART ' + channel)

    def leave_all(self, channels, message):
        for channel in channels:
            self.leave(channel, message)
