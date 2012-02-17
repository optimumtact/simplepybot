#!/usr/bin/env python2
import ircbot
import re
import shelve
# Connection information
network = 'segfault.net.nz'
port = 6667
channel = '#bots'
nick = 'quotebot'
name = 'BotHerd'

# Create our bot class
   
spartamode=False #enable/disable spartamode?
  
linebuf=[] #stores the last bufSize messages from the channel
    
#check for !quotes followed by an irc nick and an optional id
listquotes=re.compile('^!quotes [A-Za-z_]+ *[0-9]*$')
    
quote=re.compile('^!quote [\w+\s?]+$') #check for a !quote followed by a number of words and spaces 

quitreg=re.compile(nick+':? quit') #check for my nickname followed by a optional colon and then quit
    
spartareg=re.compile('this') #check for a single this
    
counter=0 #current number of messages remembered
    
bufSize=100 #sets the maximum size of the bots channel memory (number of messages remembered)
   
#Quote id num
quoteID=1
#open dict storing id's with a single quote attached to each id from file, creating this file if it does not
#exist
quoteDict=shelve.open('ircquotes', flag='c') 
#open dict storing names with a list of ids associated to each name (where each id is a entry in the quoteDict
#corresponding to a quote from that name) from file, creating the file if it does not exist
nameDict=shelve.open('nameDict', flag='c') 
    
  
  # Bot Methods below
  # Join the channel when connected
  def on_welcome (  connection, event ):
    connection.join ( channel )
  

  # React to channel messages
  def on_pubmsg ( self, connection, event ):
    #store the actual message from the event
    message=getMsg(event)
    
    # Check for a !quotes command
    if listquotes.match(message)!=None:
     result=message.strip(' ').split(' ')
     connection.privmsg(channel, lookupQuote(result))
    
    #check for a !quote user command
    elif quote.match(message):
      match=findMatches(message.split(' ')[1], connection)
      if match == None:
        connection.privmsg(channel, 'test')
      else:
        connection.privmsg(channel, addQuote(self.quoteID, message.split(' ', 1)[1],  event.source().split('!')[0]))
        quoteID=self.quoteID+1
    #check for a quit command 
    elif quitreg.match(message):
      die('Remote User Kill');

    #check for a this (Super secret function here)
    elif spartareg.match(message) and self.spartamode:
      connection.privmsg(channel, 'IS')
      connection.privmsg(channel, 'SPARTA')
      connection.privmsg(channel, '\001ACTION kicks '+event.source().split('!')[ 0 ]+' into a pit\001')

#otherwise put the line into the linebuf and increment counter
    else:
      print event.arguments()
      print event.source()
      print event.target()
      print event.eventtype()
      linebuf.insert(self.counter, event)
      counter=self.counter+1
      if counter>=self.bufSize:
        counter=0
  

  def formatForDisplay(self, event):
    displaystring='<'+event.source().split('!')[0]+'> '+event.arguments()[0]
    return displaystring

  #handle reporting of matching quotes
  def findMatches(self, pattern, connection):
      matchbuf=[]
      for event in linebuf:
        if re.search(pattern, event.arguments()[0])!=None:
          matchbuf.append(formatForDisplay(event))
      if (len(matchbuf)>1):
        connection.privmsg(channel, 'Too many matches, please refine your search')
      else:
        return matchbuf

  #handle insertion of new quote, as well as placing it into the appropriate name and date dicts
  def addQuote(self, idnum, quote, name):
    quoteDict[idnum]=quote
    if name in nameDict:
      temp=nameDict[name]
      temp.append(idnum)
      nameDict[name]=temp
    else:
      nameDict[name]=[idnum]
    
    print quote
    print name
    print idnum
    return 'q'

  def lookupQuote(self, reference):
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
        quotes+' '+quoteDict[quoteid]
      return quotes

