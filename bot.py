#!/usr/bin/env python2
import ircbot
import re
# Connection information
network = 'segfault.net.nz'
port = 6667
channel = '#bots'
nick = 'quotebot'
name = 'BotHerd'

# Create our bot class
class QuoteBot ( ircbot.SingleServerIRCBot ):
  def __init__(self, network, nick, name):
    self.spartamode=False
    self.linebuf=[]
    self.listquotes=re.compile('^!quotes .*')
    self.quote=re.compile('^!quote [\w+\s?]+')
    self.quitreg=re.compile(nick+':? quit')
    self.spartareg=re.compile('this')
    self.counter=0
    self.bufSize=100
    ircbot.SingleServerIRCBot.__init__(self, network, nick, name)

# Join the channel when welcomed
  def on_welcome ( self, connection, event ):
    connection.join ( channel )
  
#turn event objects into nicely formatted strings
  def formatForDisplay(self, event):
    displaystring='<'+event.source().split('!')[0]+'> '+event.arguments()[0]
    return displaystring

#handle reporting of matching quotes
  def reportMatches(self, pattern, connection):
      matchbuf=[]
      for event in self.linebuf:
        if re.search(pattern, event.arguments()[0])!=None:
          matchbuf.append(self.formatForDisplay(event))
      if (len(matchbuf)>6):
        connection.privmsg(channel, 'To many matches, please refine your search')
      else:
        for line in matchbuf:
          connection.privmsg(channel, line)

# React to channel messages
  def on_pubmsg ( self, connection, event ):

# Check for a !quotes command
    if self.listquotes.match(event.arguments()[0])!=None:
     result=event.arguments()[0].split(' ')
     connection.privmsg(channel, 'Im quotes')
    elif self.quote.match(event.arguments()[0]):
       self.reportMatches(event.arguments()[0].split(' ')[1], connection)

#check for a quit command 
    elif self.quitreg.match(event.arguments()[0]):
      self.die('Remote User Kill');

#check for a this (Super secret function here)
    elif self.spartareg.match(event.arguments()[0]) and self.spartamode:
      connection.privmsg(channel, 'IS')
      connection.privmsg(channel, 'SPARTA')
      connection.privmsg(channel, '\001ACTION kicks '+event.source().split('!')[ 0 ]+' into a pit\001')

#otherwise put the line into the linebuf and increment counter
    else:
      self.linebuf.insert(self.counter, event)
      self.counter=self.counter+1
      if self.counter>=self.bufSize:
        self.counter=0
#handle private msg commands
  def on_privmsg(self, connection, event):
    if(spartamode==True):
      spartamode=False
    else:
      spartamode=True
bot = QuoteBot ([(network, port)], nick, name )
bot.start()
