import re
import socket
import logging

class Network:
    ircmsg = re.compile(r"(?P<prefix>:\S+ )?(?P<command>(\w+|\d{3}))(?P<params>( [^:]\S+)*)(?P<postfix> :.*)?")

    def __init__(b_size = 1024):
        self.socket
        self.incomplete_buffer = ''
        self.buffer_size = b_size

    def connect(self, address, nick, ident, server, realname):
      socket = self.socket
      socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      socket.connect(address)
      send('NICK ' + nick)
      send('USER ' + nick + ' ' + ident + ' ' + server  +' :' + realname)
      return True
    
    #send a line to the server, formatting as required by rfc 1459
    def send(line, encoding="utf-8"):
      socket = self.socket
      line = line.replace('\r', '')
      line = line.replace('\n', '')
      line = line.replace('\r\n', '')+'\r\n'
      totalsent = 0
      while totalsent < len(line):
        sent = socket.send(line[totalsent:].encode(encoding))
        if sent is 0 :
          raise RuntimeError('Socket connection broken')
        totalsent = totalsent + sent
      socket.send(line.encode(encoding))
    
    def recv():
      socket = self.socket
      buffer_size = self.buffer_size
      d = socket.recv(buffer_size)
      data = d.decode('utf-8', 'replace')
      return data
    
    
    #read a stream of data, splitting it into messages seperated by \r\n and storing
    #the last incomplete message (if any) in the incomplete buffer variable to be
    #used in the next read of the data stream
    def process_data(data):
      incomplete_buffer = self.incomplete_buffer
      if incomplete_buffer:
        data = incomplete_buffer + data
        incomplete_buffer = ''
      
      if data[-2:] is '\r\n':
        split_data = data.split('\r\n')
      
      else:
        split_data = data.split('\r\n')
        incomplete_buffer = split_data.pop(-1)
      
      return split_data
    
    #utility method turning an ircmsg into a nicely formatted tuple for ease of use
    def parse_message(self, message):
      
      logging.debug(message)
      m = self.ircmsg.match(message)
      prefix = None
      postfix = None
      params = None
      command = None
      if m:
        prefix = m.group('prefix')
        if prefix:
          prefix = prefix.lstrip(' ')
          prefix = prefix.lstrip(':')
    
        command = m.group('command')
    
        params = m.group('params')
        if params:
          params = params.lstrip(' ')
          params = params.split(' ')
    
        postfix = m.group('postfix')
        if postfix:
          postfix = postfix.lstrip(' ')
          postfix = postfix.lstrip(':')
      
      if m:
        logging.debug('Cleaned message, prefix = {0}, command = {1}, params = {2}, postfix = {3}'.format(prefix, command, params, postfix))
        return (prefix, command, params, postfix)
    
      else:
        logging.warn('Couldn\'t match message {0}'.format(message))
        return None
    
    #Get a number of messages from the socket and return them in list form
    def get_messages():
      data = recv()
      result = process_data(data)
      clean = []
      for line in result:
        cleaned_message = parse_message(line)
        if cleaned_message:
          clean.append(cleaned_message)
      return clean
    
    #IRC CONVIENENCE METHODS
    #join the given channel, strips out hashes if they are found, to prevent issues
    def join(self, channel):
      channel = channel.lstrip('#')
      self.send('JOIN #' + channel)
    
    #send a msg to the given channel, can be channel or user
    def msg(self, channel, message):
      channel=channel.lstrip('#')
      self.send('PRIVMSG ' + channel + ' :' + str(message))
    
    #kill your connection to the server with the given message being sent as your
    #quit message
    def kill(self, message):
      self.send("QUIT :" + message)
    
    #leave the given channel with a leave message given by message
    def leave(self, channel, message):
      self.send('check what this is')#TODO: fixme
    
