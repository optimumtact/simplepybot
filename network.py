import re
import socket
import errno
import select
import logging
import Queue as q
import event_util as eu
import time
import numerics as nu

class Network(object):
    '''
    Handles messages to the socket

    Consists of a few basic functions aside from sending/receiving.
    Sending NICK, USER, message parsing, and sending PONG responses.
    '''
    #Really long regex to match and split most irc messages correctly (No guarantees though as I haven"t fully roadtested it)
    ircmsg = re.compile(r"(?P<prefix>:\S+ )?(?P<command>(\w+|\d{3}))(?P<params>( [^:]\S+)*)(?P<postfix> :.*)?")

    def __init__(self, inqueue, outqueue, botname, module_name="network", b_size = 1024, log_level=logging.INFO):
        self.socket = None
        self.module_name = module_name
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(0)
        self.incomplete_buffer = ""
        self.buffer_size = b_size
        self.log = logging.getLogger(u"{0}.{1}".format(botname, module_name))
        self.log.setLevel(log_level)
        self.is_running = True
        self.connected = False
        #priority queues with data in form of (priority, data)
        self.inq = inqueue
        self.outq = outqueue

        #list of our sockets
        self.inputs = [self.socket]
        self.outputs = [self.socket]

        #Events coming out of the network - unused for now
        self.in_events = []

        #Event coming in from the ircbot core
        self.out_events =   [
                            eu.event(nu.BOT_MSG, self.msg),
                            eu.event(nu.BOT_MSGS_ALL, self.msgs_all),
                            eu.event(nu.BOT_MSGS, self.msgs),
                            eu.event(nu.BOT_MSG_ALL, self.msg_all),
                            eu.event(nu.BOT_CONN, self.connect),
                            eu.event(nu.BOT_USER, self.user),
                            eu.event(nu.BOT_NICK, self.nick),
                            eu.event(nu.BOT_JOIN_CHAN, self.join),
                            eu.event(nu.BOT_QUIT, self.quit),
                            eu.event(nu.BOT_KILL, self.kill),
                            eu.event(nu.BOT_PONG, self.pong),
                            eu.event(nu.BOT_NAMES, self.names),
                            eu.event(nu.BOT_WHO, self.who),
                            ]
        self.log.info('network initialised')

    def loop(self):
        self.log.debug('Looping started')
        while self.is_running:
            if not self.connected:
                try:
                    m_event = self.outq.get(False)
                    if m_event.type == nu.BOT_CONN:
                        self.log.debug('Connection event!')
                        self.connect(*m_event.data)
                    else:
                        pass
                except q.Empty as e:
                    pass
            else:
                self.poll_sockets()
                time.sleep(.1)

        self.log.info('network ending')

    def poll_sockets(self):
        '''
        Uses select to get readable/writable sockets then calls
        read or write on them
        '''
        readable, writable, exceptional = select.select(self.inputs, self.outputs, self.inputs)
        if readable:
            for r in readable:
                #read from r, placing the messages in the given queue 
                self.handle_input(r, self.inq)

        if writable and not self.outq.empty():
            for w in writable:
                #write to w with items pulled from the given queue
                self.handle_output(w, self.outq)

        if exceptional:
            for e in exceptional:
                #TODO can we get the error to log as well?
                self.log.error(u'Exceptional socket {0}'.format(e.getpeername()))
                self.inputs.remove(e)
                self.outputs.remove(e)
        
        #if we lost all our sockets
        if not self.inputs or not self.outputs:
            self.log.error(u'No sockets left to read/write')
            self.connected = False
            #highest priority message that will get client to attempt to reconnect
            self.inq.put(eu.error('No sockets left to read/write from', priority=1))

    def handle_output(self, socket, outqueue):
        '''
        Takes an item from the outbound queue and puts it through our internal
        event handlers
        '''
        try:
            #grab an item from the outbound queue
            m_event = self.outq.get(False)
            self.log.debug(u'Outwards event, {0}, data {1}'.format(m_event.type, m_event.data))
            #put them through our outbound event handlers
            triggered = False
            for e in self.out_events:
                if e(m_event):
                    triggered = True

            if not triggered:
                self.log.debug(u'Unhandled outbound event {0} data:{1}'.format(m_event.type, m_event.data))

        except q.Empty:
            #nothing to write
            pass

    def handle_input(self, socket, inqueue):
        '''
        Pull all possible irc lines from the socket
        parse them and then put them through our internal
        event handling before sending them to the client
        '''
        #pull all current lines from socket
        result = self.recv()
        clean = []
        for line in result:
            cleaned_message = self.parse_message(line)
            clean.append(cleaned_message)
        
        #go through the cleaned messages and put them through our internal
        #event handling before they reach client (normally used to tweak priorities)
        for msg in clean:
            for event in self.in_events:
                event(msg) #TODO do I really need this?

            self.inq.put(msg)

    def send(self, line, encoding='utf-8'):
        #send the message out
        #send takes the form SENDOUT [lines..]
        self.log.info(u'>> {0}'.format(line))
        line = line.replace('\r', ' ').replace('\n', ' ') + '\r\n'
        totalsent = 0
        while totalsent < len(line):
            sent = self.socket.send(line[totalsent:].encode(encoding))
            totalsent = totalsent + sent
                

    def recv(self):
        '''
        Receives data from the server.
        '''
        buffer_size = self.buffer_size
        d = self.socket.recv(buffer_size)

        data = d.decode('utf-8', 'replace')

        '''
        Read a stream of data, splitting it into messages separated by \r\n.

        The last incomplete message (if any) will be stored in the incomplete
        buffer variable to be used in the next read of the data stream
        
        Every time we get new data we put the incomplete buffer at the front then we 
        check if the last 2 chars are the delimiter, in which case we have a full
        irc msg so we can just split the data. Otherwise we have to split the data
        and put the last incomplete item on the buffer
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
        Takes messages from the socket and converts them into internal events
        '''
        m = self.ircmsg.match(message)

        if not m:
            self.log.warn(u'Couldn\'t match message {0}'.format(message))
            return None

        postfix = m.group('postfix')
        if postfix:
            postfix = postfix.strip(' ')
            postfix = postfix.lstrip(':')

        command = m.group('command')

        prefix = m.group('prefix')
        if prefix:
            prefix = prefix.strip(' ')
            prefix = prefix.lstrip(':')

        params = m.group('params')
        if params:
            params = params.strip(' ')
            params = params.split(' ')
        
        self.log.debug(u'Cleaned message, prefix = {0}, command = {1}, params = {2}, postfix = {3}'.format(prefix, command, params, postfix))
        self.log.info(u'<< {0} {1} {2} {3}'.format(prefix, command, params, postfix))
        return eu.irc_msg(command, (command, prefix, params, postfix))

    #Everything below this point are handlers for events from botcore
    def msgs_all(self, msgs, channels):
        '''
        Accepts a list of messages to send to a list of channels
        msgs: A list of messages to send
        channels: A list of targets to send it to
        '''
        for channel in channels:
            for message in msgs:
                self.msg(message, channel)

    def msg_all(self, message, channels):
        '''
        Accepts a message to send to a list of channels
        message: the message to send
        channels: A list of targets to send it to
        '''
        for channel in channels:
            self.msg(message, channel)

    def msg(self, message, channel):
        '''
        Send a message to a specific target.
        message: the message to send
        channel: the target to send it to
        
        This method takes care of enforcing the 512 character limit
        right now it does it very simply by cutting the message at char 510
        (leaving space for the \r\n) and calling msg again with the remainder
        later on it might be improved by finding the nearest space to cut on
        under the limit
        '''
        msg = u'PRIVMSG {0} :{1}'.format(channel, message)
        if len(msg) > 512:
            sending = msg[:510]
            remainder = msg[510:]
            self.send(sending)
            self.msg(remainder, channel)
        
        else:
            self.send(msg)

    def msgs(self, msgs, channel):
        '''
        Send a list of msgs to a channel
        '''
        for msg in msgs:
            self.msg(msg, channel)

    def join(self, channel):
        '''
        Join a channel.
        channel: the channel to join
        '''      
        self.send(u'JOIN {0}'.format(channel))

    def quit(self, message):
        '''
        Disconnects from a server with a optional QUIT message.
        '''
        if message:
            self.send(u'QUIT :{0}'.format(message))
        
        else:
            self.send(u'QUIT')
    
    def kill(self):
        '''
        Die!
        '''
        self.is_running = False

    def leave(self, channel, message):
        '''
        Leaves a channel, optionally sending a message to the channel first.
        channel: Channel to leave
        message: optional message to send first
        '''
        if message:
            self.msg(message, channel)
        self.send(u'PART {0}'.format(channel))

    def connect(self, server, port):
        '''
        Connect to a server.
        data is the args
        '''
        try:
            self.socket.connect((server,port))
        except socket.error as e:
            if e.errno == 115:
                pass
            elif e.errno == 10035:
                pass
            else:
                raise e

        self.connected = True

    def nick(self, nick):
        '''
        Send the nick command with the given nick
        '''
        self.send(u'NICK {0}'.format(nick))

    def user(self, nick, realname):
        '''
        Send the USER command with the given realname and nick
        HOSTNAME and SERVERNAME are given as pybot
        '''
        self.send(u'USER {0} pybot pybot :{1}'.format(nick, realname))
    
    def pong(self, msg):
        self.send(u'PONG {0}'.format(msg))
        
    def names(self, channels):
        '''
        Send the NAMES command with the given set of channels to call
        for
        '''
        if channels:
            self.send(u'NAMES {0}'.format(','.join(channels)))
        else:
            self.send(u'NAMES')
    
    def who(self, param):
        '''
        send the Who message with given param
        '''
        if param:
            self.send(u'WHO {0}'.format(param))
        else:
            self.send(u'WHO')

