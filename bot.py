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
rejoin_toggle=re.compile(nick+':? autojoin')
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
  
  #check for a rejoin toggle command
  elif rejoin_toggle.match(message):
    global autojoin
    if autojoin:
      autojoin=False
    else:
      autojoin=True

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
  

#on a kick determine if I am the one who has been kicked, if so I need to check if autojoin is true
#and return to the channel
def on_kick(params, reason, admin):
  global autorejoin
  global nick
  if params[0]==nick:
    admin=admin.split('!')[0]
    print('Kicked by admin %s', admin)#TODO replace with logger
    if autorejoin:
      #rejoin channel
      join(params[1])

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
    
    if debug:
      print ('----Full Message----')
      print (message)
      print ('----Regex----')
      print (prefix)
      print (command)
      print (params)
      print (endprefix)
      print('---------------------')
  else:
    if debug:
      print (message)
    print('ERROR, unknown message passed')

#respond to a given irc message and depatch it to the correct method based on its command/event number
def handleMessage(prefix, command, params, endprefix):
  global events
  if command  in events:
    event=events[command]
    if event=='welcome':
      on_welcome()
    
    if event=='privmsg':
      on_privmsg(params, endprefix, prefix)
    
    if event=='kick':
      on_kick(params, endprefix, prefix)

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

#connect to the server
def connect(address, nick, ident, server, realname):
  global socket
  socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
  socket.connect(address)
  send('NICK '+nick)
  send('USER '+nick+' '+ident+' '+server+' '+' :'+realname)
  return server

# Bot Methods below

def formatForDisplay(source, message):
  displaystring=str(datetime.date.today())+' <'+source.split('!')[0]+'> '+message
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

def die (message):
  global quoteDict
  global nameDict
  global quoteID
  quoteDict['0']=quoteID
  quoteDict.close()
  nameDict.close()
  global address
  send("QUIT :"+message) 
  sys.exit(0)


#handle insertion of new quote, as well as placing it into the appropriate name and date dicts
def addQuote(idnum, quote, name):
  global quoteDict
  global nameDict
  global quoteID
  quoteDict[str(idnum)]=quote
  
  if name in nameDict:
    temp=nameDict[name]
    temp.append(str(idnum))
    nameDict[name]=temp
  else:
    nameDict[name]=[str(idnum)]
  print('---addquote---')
  print (quote)
  print (name)
  print (str(idnum))
  quoteID=quoteID+1
  return quote

def lookupQuote(reference):
  global quoteDict
  global nameDict
  quotes=''
  
  if len(reference)==3:
    if reference[2] in quoteDict:
      return quoteDict[reference[2]]
    else:
      return 'I do not have a quote with id:'+reference[2]
  else:
    if reference[1] not in nameDict :
      return 'I do not have a user with the name:'+reference[1]+' in the database'
    ids=nameDict[reference[1]]
    for quoteid in ids:
      quotes+=' '+quoteDict[quoteid]
    return quotes


#dict of irc events and commands
events = {
  "001": "welcome",
  "002": "yourhost",
  "003": "created",
  "004": "myinfo",
  "005": "protocols",
  "006": "map?",
  "007": "endmap",
  "008": "snomask",
  "010": "?",
  "200": "tracelink",
  "201": "traceconnecting",
  "202": "tracehandshake",
  "203": "traceunknown",
  "204": "traceoperator",
  "205": "traceuser",
  "206": "traceserver",
  "207": "traceservice",
  "208": "tracenewtype",
  "209": "traceclass",
  "210": "tracereconnect",
  "211": "statslinkinfo",
  "212": "statscommands",
  "213": "statscline",
  "214": "statsnline",
  "215": "statsiline",
  "216": "statskline",
  "217": "statsqline",
  "218": "statsyline",
  "219": "endofstats",
  "221": "umodeis",
  "231": "serviceinfo",
  "232": "endofservices",
  "233": "service",
  "234": "servlist",
  "235": "servlistend",
  "241": "statslline",
  "242": "statsuptime",
  "243": "statsoline",
  "244": "statshline",
  "250": "luserconns",
  "251": "luserclient",
  "252": "luserop",
  "253": "luserunknown",
  "254": "luserchannels",
  "255": "luserme",
  "256": "adminme",
  "257": "adminloc1",
  "258": "adminloc2",
  "259": "adminemail",
  "261": "tracelog",
  "262": "endoftrace",
  "263": "tryagain",
  "265": "n_local",
  "266": "n_global",
  "300": "none",
  "301": "away",
  "302": "userhost",
  "303": "ison",
  "305": "unaway",
  "306": "nowaway",
  "311": "whoisuser",
  "312": "whoisserver",
  "313": "whoisoperator",
  "314": "whowasuser",
  "315": "endofwho",
  "316": "whoischanop",
  "317": "whoisidle",
  "318": "endofwhois",
  "319": "whoischannels",
  "321": "liststart",
  "322": "list",
  "323": "listend",
  "324": "channelmodeis",
  "329": "channelcreate",
  "331": "notopic",
  "332": "currenttopic",
  "333": "topicinfo",
  "341": "inviting",
  "342": "summoning",
  "346": "invitelist",
  "347": "endofinvitelist",
  "348": "exceptlist",
  "349": "endofexceptlist",
  "351": "version",
  "352": "whoreply",
  "353": "namreply",
  "361": "killdone",
  "362": "closing",
  "363": "closeend",
  "364": "links",
  "365": "endoflinks",
  "366": "endofnames",
  "367": "banlist",
  "368": "endofbanlist",
  "369": "endofwhowas",
  "371": "info",
  "372": "motd",
  "373": "infostart",
  "374": "endofinfo",
  "375": "motdstart",
  "376": "endofmotd",
  "377": "motd2", 
  "381": "youreoper",
  "382": "rehashing",
  "384": "myportis",
  "391": "time",
  "392": "usersstart",
  "393": "users",
  "394": "endofusers",
  "395": "nousers",
  "401": "nosuchnick",
  "402": "nosuchserver",
  "403": "nosuchchannel",
  "404": "cannotsendtochan",
  "405": "toomanychannels",
  "406": "wasnosuchnick",
  "407": "toomanytargets",
  "409": "noorigin",
  "411": "norecipient",
  "412": "notexttosend",
  "413": "notoplevel",
  "414": "wildtoplevel",
  "421": "unknowncommand",
  "422": "nomotd",
  "423": "noadmininfo",
  "424": "fileerror",
  "431": "nonicknamegiven",
  "432": "erroneusnickname",
  "433": "nickinuse",
  "436": "nickcollision",
  "437": "unavailresource", # "Nick is temporarily unavailable
  "439": "toofast",
  "441": "usernotinchannel",
  "442": "notonchannel",
  "443": "useronchannel",
  "444": "nologin",
  "445": "summondisabled",
  "446": "usersdisabled",
  "451": "notregistered",
  "461": "needmoreparams",
  "462": "alreadyregistered",
  "463": "nopermforhost",
  "464": "passwdmismatch",
  "465": "banned",
  "466": "youwillbebanned",
  "467": "keyset",
  "471": "channelisfull",
  "472": "unknownmode",
  "473": "inviteonlychan",
  "474": "bannedfromchan",
  "475": "badchannelkey",
  "476": "badchanmask",
  "477": "nochanmodes", # "Channel doesn't support modes"
  "478": "banlistfull",
  "481": "noprivileges",
  "482": "chanoprivsneeded",
  "483": "cantkillserver",
  "484": "restricted", # Connection is restricted
  "485": "uniqopprivsneeded",
  "486": "needtoidentify",
  "491": "nooperhost",
  "492": "noservicehost",
  "501": "umodeunknownflag",
  "502": "usersdontmatch",
  "PRIVMSG": "privmsg",
  "KICK": "kick"
}
connect(address, nick, ident, address[0], realname)
while True:
    recv()
