import re
import socket
#irc regex to break message down in [prefix] command params* [prefix]
ircmsg=re.compile(r"(?P<prefix>:\S+ )?(?P<command>(\w+|d{3}))(?P<params>( [^ :]\S*)*)(?P<endprefix> :.*)?")

incomplete_buffer=''
socket
bufsize=4096

#dict of irc events and commands

#IRC METHODS
#send a priv msg to the given channel (where channel can be an irc channel or a user
def msg(channel, message):
  send('PRIVMSG '+channel+' :'+str(message))

#send a msg to all channels in list
def msgall(channels, message):
  for channel in channels:
    msg(channel, message)

#join all given channels
def join (channels):
  for channel in channels:
    if channel:
      channel=channel.lstrip('#')
      send('JOIN #'+channel)

def die (message, quote_dict, quote_id):
  quote_dict['0']=quote_id
  quote_dict.close()
  send("QUIT :"+message) 
  sys.exit(0)

#connect to the server
def connect(address, nick, ident, server, realname):
  global socket
  socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
  socket.connect(address)
  send('NICK '+nick)
  send('USER '+nick+' '+ident+' '+server+' '+' :'+realname)
  return server

#network methods
#recv up to bufsize data into the socket
def recv():
  global socket
  global bufsize
  d = socket.recv(bufsize)
  data=d.decode('utf-8', 'replace')
  return data

#process the decoded data from the socket, splitting out complete messages and
#storing any incomplete messages in the incomplete buffer
def process_data(data):
  global incomplete_buffer
  if incomplete_buffer: #if there is incomplete data
    data=incomplete_buffer+data #add it to the data we just recieved (in the recv method)
    incomplete_buffer=''#clear buffer of anything in it

  if data[-2:]== '\r\n':
    split_data=data.split('\r\n')#this will split the data into the proper messages(assuming they are all full messages
    #i.e the last message is not incomplete
  else:
    split_data=data.split('\r\n')#this handles the case where the last message in data may be incomplete
    incomplete_buffer=split_data.pop(-1)
  return split_data

#encode a line from utf-8 into bytes and strip all linebreaks
#add linebreaks as required by rfc 1459
def send(line, encode="utf-8"):
  global socket
  line = line.replace('\r', '')
  line = line.replace('\n', '')
  line = line.replace('\r\n', '') + '\r\n'
  socket.send(line.encode(encode))

#start receiving messages from socket
def getMessages():
  data=recv()
  result=process_data(data)
  return results


def parseMessage(message):
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

    endprefix=m.group('endprefix')
    if endprefix:
      endprefix=endprefix.strip(' ')
      endprefix=endprefix.lstrip(':')

    return (prefix, command, params, endprefix)

  return None


