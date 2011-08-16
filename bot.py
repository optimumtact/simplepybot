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
    ircbot.SingleServerIRCBot.__init__(self, network, nick, name)
    self.spartamode=False
    self.linebuf={"Francis had a little lamb"}
    self.quotereg=re.compile('^!quotes? \w+')
    self.quitreg=re.complile(nick+':? quit')
    self.spartareg=re.compile('this')
# Join the channel when welcomed
  def on_welcome ( self, connection, event ):
    connection.join ( channel )

# React to channel messages
  def on_pubmsg ( self, connection, event ):
    source = event.source().split ( '!' ) [ 0 ]
# compile the regex matchin the quotes command
# Check for a !quotes command
    if self.quotereg.match(event.arguments()[0])!=None:
     result=event.arguments()[0].split(' ')
     for line in self.linebuf:
       if re.match(result[1], line)!=None:
         connection.privmsg(channel, line)
     
#check for a quit command 
    elif self.quitreg.match(event.arguments()[0]):
      self.die('Remote User Kill');
#check for a this (Super secret function here)
    elif self.spartareg.match(event.arguments()[0] and self.spartamode:
      connection.privmsg(channel, 'IS')
      connection.privmsg(channel, 'SPARTA')
      connection.privmsg(channel, '\001ACTION kicks '+source+' into a pit\001')

#debug printing work
#    print event.source()
#    print event.eventtype()
#    print event.target()
#    print event.arguments()
# Create the bot

  def on_privmsg(self, connection, event):
    if(self.spartamode==True):
      self.spartamode=False
    else:
      self.spartamode=True
bot = QuoteBot ([(network, port)], nick, name )
bot.start()

