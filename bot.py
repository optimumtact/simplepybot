#!/usr/bin/env python
import re
import shelve
import sys
import quotefunctions as qf
import network as net

nick='quotebot'
ident='botherd'
realname='v1.1a'
host='irc.segfault.net.nz'
port='6667'
address=(host, port)
channels=['bots']
max_range=10
counter=0 #current number of messages remembered
line_buffer_size=100 #sets the maximum size of the bots channel memory (number of messages remembered)
line_buffer=[] #stores the last bufSize messages from the channel
#open dict storing quotes
quote_dict=shelve.open('id_quote_dict', flag='c') 

#if we already have quotes then we restore the current id from file
#otherwise we generate one and store it
if '0' in quote_dict:
  quote_id=quote_dict['0']
else:
  quote_id=1
  quote_dict['0']=quote_id

#check for find commands
find_quote_single=re.compile('^!quotes? [0-9]')
find_quote_range=re.compile('^!quote find [0-9]+ [0-9]+$')
find_quote_name=re.compile('^!quote find [A-Za-z_]+$')
#check for a !quote followed by a number of words and spaces 
add_quote_msg=re.compile('^!quote add [\w+\s?]+$')
add_quote_user=re.compile('^!quote add <[A-Za-z_]+> [\w+\s?]+$')
#check for my nickname followed by a optional colon and then quit
quitreg=re.compile(nick+':? quit') 


#what to do on server welcome
def on_welcome():
  net.join(bot.channels)

#respond to privmsg containing message and from channel/users contained in params
def on_privmsg(params, message, source):
  channel=params[0]
  result=message.split(' ')
  if bot.find_quote_single.match(message):
    answer=qf.lookup_quote(results[2], results[2])

  elif bot.find_quote_range.match(message):
    answer=qf.lookup_quote(results[2], results[3])

  elif bot.find_quote_name.match(message):
    answer=qf.lookup_quote_by_user(results[2])

  elif bot.add_quote_user.match(message):
    print('add_quote_user')
  
  else:
    print('no regex match')

  net.msg(channel, answer)

def formatForDisplay(source, message):
  displaystring=' <'+source.split('!')[0]+'> '+message
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

def start():
  net.connect(bot.address, bot.nick, bot.ident, bot.host, bot.realname)
  while True:
    net.getMessages()

start()
