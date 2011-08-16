
import ircbot
import re
# Connection information
network = 'segfault.net.nz'
port = 6667
channel = '#bots'
nick = 'quotebot'
name = 'BotHerd'

# Create a dictionary to store statistics in
statistics = {}
lineBuff={}


# Create our bot class
class QuoteBot ( ircbot.SingleServerIRCBot ):

# Join the channel when welcomed
  def on_welcome ( self, connection, event ):
    connection.join ( channel )

# React to channel messages
  def on_pubmsg ( self, connection, event ):
    source = event.source().split ( '!' ) [ 0 ]

# compile the regex matchin the quotes command
    reg=re.compile('^!quotes? \w')

# Check for a !quotes command
    if reg.match(event.arguments()[0])!=None:
     print event.arguments()
     
#check for a quit command 
    elif event.arguments()[ 0 ]==nick+' quit':
      self.die('Remote User Kill');
    elif event.arguments()[ 0 ]=='this':
      connection.privmsg(channel, "IS")
      connection.privmsg(channel, "SPARTA")
      connection.privmsg(channel, "/me kicks name into pit")
    else:
      print event.arguments()
# Create the bot
bot = QuoteBot ( [( network, port )], nick, name )
bot.start()

