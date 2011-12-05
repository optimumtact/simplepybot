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

#handle reporting of matching quotes
  def reportMatches(self, pattern):
    for line in self.linebuf:
      print line

# React to channel messages
  def on_pubmsg ( self, connection, event ):
    print event.arguments()
    print event.target()
    print event.eventtype()
    print event.source()

# Check for a !quotes command
    if self.listquotes.match(event.arguments()[0])!=None:
     result=event.arguments()[0].split(' ')
     connection.privmsg(channel, 'Im quotes')
    elif self.quote.match(event.arguments()[0]):
       self.reportMatches(event.arguments()[0].split(' ')[1])
#check for a quit command 
    elif self.quitreg.match(event.arguments()[0]):
      self.die('Remote User Kill');
#check for a this (Super secret function here)
    elif self.spartareg.match(event.arguments()[0]) and self.spartamode:
      connection.privmsg(channel, 'IS')
      connection.privmsg(channel, 'SPARTA')
      connection.privmsg(channel, '\001ACTION kicks '+event.source().split('!')[ 0 ]+' into a pit\001')
    else:
      self.linebuf.insert(self.counter, event.arguments()[0])
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
