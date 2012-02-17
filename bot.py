#!/usr/bin/env python
import logging
import socket
import io
import select
import re
nick="qoutebot"
ident="botherd"
realname="mailto:optimumtact.junk@gmail.com"
address=("irc.segfault.net.nz", 6667)
#comma seperated list of channels, # are added automatically
channels={"bots"}

#network params
socket
bufsize=1024
incomplete_buffer=""

#message params
ircmsg=re.compile(r"(?P<prefix>:\S+ )?(?P<command>(\w+|d{3}))(?P<params>( [^ :]\S*)*)(?P<endprefix> :.*)?")
debug=False


def on_welcome():
  global channels
  join(channels)

def on_privmsg(params, message):
  print ("privmsg")
  print (message)
  print (params)

def parseMessage(message):
  global ircmsg
  global debug
  m=ircmsg.match(message)
  if m:
    handleMessage(m)
    if debug:
      print ('----Full Message----')
      print (message)
      print ('----Regex----')
      print (m.group('prefix'))
      print (m.group('command'))
      print (m.group('params'))
      print (m.group('endprefix'))
      print('---------------------')
  else:
    if debug:
      print (message)
    print('ERROR, unknown message passed')


def handleMessage(m):
  global numeric_events
  if m.group('command') in events:
    event=events[m.group('command')]
    if event=='welcome':
      on_welcome()
    if event=='privmsg':
      on_privmsg(m.group('params'), m.group('endprefix'))

def recv():
  global socket
  global bufsize
  d = socket.recv(bufsize)
  data=d.decode('utf-8', 'replace')
  if data:
    process_data(data)

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

def send(line, encode="utf-8"):
  global socket
  line = line.replace('\r', '')
  line = line.replace('\n', '')
  line = line.replace('\r\n', '') + '\r\n'
  socket.send(line.encode(encode))

def join (channels):
  global socket
  for channel in channels:
    send('JOIN #'+channel)

def connect(address, nick, ident, server, realname):
  global socket
  socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
  socket.connect(address)
  send('NICK '+nick)
  send('USER '+nick+' '+ident+' '+server+' '+' :'+realname)
  return server

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
  "PRIVMSG": "privmsg"
}


connect(address, nick, ident, address[0], realname)
while True:
    recv()
