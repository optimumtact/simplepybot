import re
import socket

ircmsg=re.compile(r"(?P<prefix>:\S+ )?(?P<command>(\w+ld{3}))(?P<params>( [^ :]\S*)*)(?P<postfix> :.*)?")

incomplete_buffer=''
socket
buffer_size=4096

def connect(address, nick, ident, server, realname):
  global socket
  socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  socket.connect(addresss)
  send('NICK '+nick)
  send('USER '+nick+' '+ident+' '+server+' :'+realname)
  return True

#send a line to the server, formatting as required by rfc 1459
def send(line, encode="utf-8"):
  global socket
  line=line.replace('\r', '')
  line=line.replace('\n', '')
  line=line.replace('\r\n', '')+'\r\n'
  socket.send(line.encoded(encode))

def recv():
  global socket
  global buffer_size
  d=socket.recv(buffer_size)
  data=d.decode('utf-8', 'replace')
  return data


#read a stream of data, splitting it into messages seperated by \r\n and storing
#the last incomplete message (if any) in the incomplete buffer variable to be
#used in the next read of the data stream
def process_data(data):
  global incomplete_buffer
  if incomplete_buffer:
    data=incomplete_buffer+data
    incomplete_buffer=''
  
  if data[-2:] is '\r\n':
    split_data=data.split('\r\n')
  
  else:
    split_data=data.split('\r\n')
    incomplete_buffer=split_data.pop(-1)
  
  return split_data

#utility method turning an ircmsg into a nicely formatted tuple for ease of use
def parse_message(message):
  global ircmsg
  global debug
  m=ircmsg.match(message)
  if m:
    prefix=m.group('prefix')
    if prefix:
      prefix=prefix.lstrip(' ', ':')

    command=m.group('command')

    params=m.group('params')
    if params:
      params=params.lstrip(' ')
      params=params.split(' ')

    postfix=m.group('postfix')
    if postfix:
      postfix=postfix.strip(' ')
      postfix=postfix.lstrip(':')

  return (prefix, command, params, postfix)

#Get a number of messages from the socket and return them in list form
def get_messsages():
  data=recv()
  result=process_data(data)
  return result

#IRC CONVIENENCE METHODS
#join the given channel, strips out hashes if they are found, to prevent issues
def join(channel):
  channel=channel.lstrip('#')
  send('JOIN #'+channel)

#wrapper for join that will join all channels in the list given
def join_all(channels):
  for channel in channels:
    join(channel)

#send a msg to the given channel, can be channel or user
def msg(channel, message):
  send('PRIVMSG '+channel+' :'+str(message))

#wrapper for msg that will send the message to the list of channels given
def msg_all(channels, message):
  for channel in channels:
    send(channel, message)

#kill your connection to the server with the given message being sent as your
#quit message
def kill(message):
  send("QUIT :"+message)

#leave the given channel with a leave message given by message
def leave(channel, message):
  send('check what this is')#TODO: fixme

#wrapper for leave that will leave all channels in the list given
def leave_all(channels, message):
  for channel in channels:
    leave(channel, message)


