#!/usr/bin/env python
import logging
import socket
import io
import select
import re
import shelve
import datetime
import sys

#nickname of bot
nick="quotebot"

#ident server response (could probably set this up in script as well)
ident="botherd"

#email address of owner
realname="mailto:optimumtact.junk@gmail.com"

#address of server
address=("irc.segfault.net.nz", 6667)

#comma seperated list of channels, # are added automatically
channels={"bots"}

#network params
#socket for all sending and receiving
socket

#size of the buffer
bufsize=1024

#buffer to hold incomplete messages
incomplete_buffer=""

#message params
#irc regex to break message down in [prefix] command params* [prefix]
ircmsg=re.compile(r"(?P<prefix>:\S+ )?(?P<command>(\w+|d{3}))(?P<params>( [^ :]\S*)*)(?P<endprefix> :.*)?")

#replace this with propper logger
debug=True

linebuf=[] #stores the last bufSize messages from the channel

autorejoin=True #autorejoin on kick

#check for !quotes followed by an irc nick and an optional id
listquotes=re.compile('^!quotes [A-Za-z_]+ *[0-9]*$')
quote=re.compile('^!quote [\w+\s?]+$') #check for a !quote followed by a number of words and spaces 
quitreg=re.compile(nick+':? quit') #check for my nickname followed by a optional colon and then quit
counter=0 #current number of messages remembered
bufSize=100 #sets the maximum size of the bots channel memory (number of messages remembered)

#open dict storing id's with a single quote attached to each id from file, creating this file if it does not
#exist
quoteDict=shelve.open('id_quote_dict', flag='c') 
#open dict storing names with a list of ids associated to each name (where each id is a entry in the quoteDict
#corresponding to a quote from that name) from file, creating the file if it does not exist
nameDict=shelve.open('name_id_dict', flag='c') 
 
#if we already have quotes then we restore the current id from file
#otherwise we generate one and store it
if '0' in quoteDict:
  quoteID=quoteDict['0']
else:
  quoteID=1
  quoteDict['0']=quoteID

#BOT METHODS
#what to do on server welcome
def on_welcome():
  global channels
  join(channels)

#respond to privmsg containing message and from channel/users contained in params
def on_privmsg(params, message, source):
  global listquotes
  global quote
  global quitreg
  global rejoin_toggle
  global quoteID
  global counter
  channel=params[0]
  # Check for a !quotes command
  if listquotes.match(message):
   result=message.strip(' ').split(' ')
   msg(channel, lookupQuote(result))
  
  #check for a !quote user command
  elif quote.match(message):
    match=findMatches(message.split(' ')[1], channel)
    if match:
      msg(channel, addQuote(quoteID, match,  source.split('!')[0]))
  
  #check for a quit command 
  elif quitreg.match(message):
    die('Remote User Kill');
  elif message.startswith('!'):
   message=None
  #otherwise put the line into the linebuf and increment counter
  else:
    linebuf.insert(counter, (params, message, source))
    counter=counter+1
    if counter>=bufSize:
      counter=0
  
#parse a given irc message with the irc regex and pass it off to handleMessage
def parseMessage(message):
  global ircmsg
  global debug
  m=ircmsg.match(message)
  if m:
    prefix=m.group('prefix')
    if prefix:
      prefix=prefix.lstrip(' ')
      prefix=prefix.lstrip(':')

    command=m.group('command')

    params=m.group('params')
    if params:
      params=params.lstrip(' ')
      params=params.split(' ')
    
    endprefix=m.group('endprefix')
    if endprefix:
      endprefix=endprefix.lstrip(' ')
      endprefix=endprefix.lstrip(':')
    handleMessage(prefix, command, params, endprefix)
    

#respond to a given irc message and depatch it to the correct method based on its command/event number
def handleMessage(prefix, command, params, endprefix):
  global events
  if command  in events:
    event=events[command]
    if event=='welcome':
      on_welcome()
    
    if event=='privmsg':
      on_privmsg(params, endprefix, prefix)
    


def formatForDisplay(source, message):
  displaystring=str(datetime.time.strftime('%H:%M')+' <'+source.split('!')[0]+'> '+message
  return displaystring

#handle reporting of matching quotes
def findMatches(pattern, channel):
  global linebuf
  matchbuf=[]
  for event in linebuf:
    print(event)#TODO change over to debugger
    if re.search(pattern, event[1]):
      matchbuf.append(formatForDisplay(event[2], event[1]))
  
  if (len(matchbuf)>1):
    msg(channel, 'Too many matches, please refine your search')
    return None
  elif (len(matchbuf)>0):
    return matchbuf[0]#in the case we want to return the match it's always the first one
  else:
    msg(channel, 'No matches found')
    return None


#handle insertion of new quote, as well as placing it into the appropriate name and date dicts
def addQuote(idnum, quote, name):
  global quoteDict
  global quoteID
  quoteDict[str(idnum)]=quote
  quoteID=quoteID+1
  return quote

def lookupQuote(id1, id2): 
  result=[]
  temp=id1
  while not temp==id2:
    if quoteDict.haskey(str(id1)):
      result.append(quoteDict[str(id1)])
    temp+=1
  
  if len(result)<1:
    if id1==1d2:
      print('I have no quote for the id:'+str(id1))
    else:
      print('I have no in the range '+str(id1)+'-'+str(id2))
    return None
  else:
    return results


#dict of the needed irc events and commands
events = {
  "001": "welcome",
  "PRIVMSG": "privmsg",
}

#IRC METHODS
#send a priv msg to the given channel (where channel can be an irc channel or a user
def msg(channel, message):
  send('PRIVMSG '+channel+' :'+str(message))

#join all given channels
def join (channels):
  global socket
  for channel in channels:
    if channel:
      channel=channel.lstrip('#')
    send('JOIN #'+channel)

def die (message):
  global quoteDict
  global nameDict
  global quoteID
  quoteDict['0']=quoteID
  quoteDict.close()
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
  if data:
    process_data(data)

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
  for line in split_data:
    if line:
      if line.startswith('PING'):#automatically respond to pings
        parameters= line.split()
        pong='PONG '+parameters[1]
        send(pong)
        return
      parseMessage(line)

#encode a line from utf-8 into bytes and strip all linebreaks
#add linebreaks as required by rfc 1459
def send(line, encode="utf-8"):
  global socket
  line = line.replace('\r', '')
  line = line.replace('\n', '')
  line = line.replace('\r\n', '') + '\r\n'
  socket.send(line.encode(encode))


#dict of irc events and commands
events = {
  "001": "welcome",
  "PRIVMSG": "privmsg",
  "KICK": "kick"
}

connect(address, nick, ident, address[0], realname)
while True:
    recv()
