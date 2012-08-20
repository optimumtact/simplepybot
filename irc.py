from network import irc_socket
class irc_connection:
    """Represents a wrapper for the network class, provides convienience methods
    for irc such as msg and join/leave channels"""

    def __init__(self, name, server, port):
        self.socket = irc_socket()
        if server and port:
            self.socket.connect((server, port), name, "bot@"+server, server,
                                name)

        self.name = name
        self.server = server
        self.port = port

    def msg_all(self, msgs, channels):
        """Accepts a list of msgs to send to a list of channels"""
        for channel in channels:
            for msg in msgs:
                self._msg(msg, channel)

    def msg(self, msg, channel):
        channel = channel.lstrip('#')
        self.socket.send('PRIVMSG ' + channel + ' :' + message)

    def join(self, channel):
        channel = channel.lstrip('#')
        self.socket.send('JOIN #' + channel)

    def quit(self, message):
        self.send('QUIT :' + message)

    def leave(self, channel, message):
        channel = channel.lstrip('#')
        if message:
            self.msg(message, channel)
        self.send('PART #' + channel)

    def leave_all(self, channels, message):
        for channel in channels:
            self.leave(channel, message)

