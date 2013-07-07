import re
import socket
#import logging

class IrcSocket(object):
    '''
    Base IrcSocket class.

    Consists of a few basic functions aside from sending/receiving.
    Sending NICK, USER, message parsing, and sending PONG responses.
    '''
    #Really long regex to match and split most irc messages correctly (No guarantees though as I haven't fully roadtested it)
    ircmsg = re.compile(r"(?P<prefix>:\S+ )?(?P<command>(\w+|\d{3}))(?P<params>( [^:]\S+)*)(?P<postfix> :.*)?")

    def __init__(self, b_size = 1024):
        self.socket = None
        self.incomplete_buffer = ''
        self.buffer_size = b_size

    def connect(self, address, nick, ident, server, realname):
        '''
        Connect to a server.

        Sends NICK and USER messages.
        '''
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(address)
        self.socket.settimeout(0.1)
        self.send('NICK %s' % nick)
        self.send('USER %s %s %s :%s' % (nick, ident, server, realname))

    def send(self, line, encoding="utf-8"):
        '''
        Send a line to the server.

        Formatted as required by rfc 1459
        '''
        #logging.debug("Sending data: %s" % line)
        line = line.replace('\r', '').replace('\n', '') + '\r\n'
        totalsent = 0
        while totalsent < len(line):
            sent = self.socket.send(line[totalsent:].encode(encoding))
            if sent is 0 :
                raise RuntimeError('Socket connection broken')
            totalsent = totalsent + sent
        #self.socket.send(line.encode(encoding))

    def recv(self):
        '''
        Receives data from the server.
        '''
        buffer_size = self.buffer_size
        try:
            d = self.socket.recv(buffer_size)

        except socket.timeout as e:
            #nothing recv, no new messages
            return []
        data = d.decode('utf-8', 'replace')

        '''
        Read a stream of data, splitting it into messages seperated by \r\n.

        The last incomplete message (if any) will be stored in the incomplete
        buffer variable to be used in the next read of the data stream
        '''
        if self.incomplete_buffer:
            data = self.incomplete_buffer + data
            incomplete_buffer = ''

        if data[-2:] is '\r\n':
            split_data = data.split('\r\n')

        else:
            split_data = data.split('\r\n')
            self.incomplete_buffer = split_data.pop(-1)

        return split_data

    def parse_message(self, message):
        '''
        Utility method turning an ircmsg into a nicely formatted tuple for ease of use.
        '''
        #logging.debug(message)
        m = self.ircmsg.match(message)
        if not m:
            logging.warn('Couldn\'t match message {0}'.format(message))
            return None

        postfix = m.group('postfix')
        if postfix:
            postfix = postfix.lstrip(' ')
            postfix = postfix.lstrip(':')

        command = m.group('command')

        if command == 'PING':
            self.send('PONG %s' % postfix)
            return None

        prefix = m.group('prefix')
        if prefix:
            prefix = prefix.lstrip(' ')
            prefix = prefix.lstrip(':')

        params = m.group('params')
        if params:
            params = params.lstrip(' ')
            params = params.split(' ')

        #logging.debug('Cleaned message, prefix = {0}, command = {1}, params = {2}, postfix = {3}'.format(prefix, command, params, postfix))
        return (prefix, command, params, postfix)

    def get_messages(self):
        '''
        Get a number of messages from the socket and return them in list form
        '''
        result = self.recv()
        clean = []
        for line in result:
            cleaned_message = self.parse_message(line)
            if cleaned_message:
                yield cleaned_message
