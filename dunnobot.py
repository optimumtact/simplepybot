import sys
import socket
import string

HOST="irc.segfault.net.nz"
PORT=6667
NICK="rachael"
IDENT="botherd"
REALNAME="This is a python bot"
readbuffer=""
chan='#cave'
quoteDict={"404":{1:"No quote found",2:"Seriously, no quotes here at all",3:"No fucking joke man, no quotes, now piss off",4:"Ok Ok, Sun Tzu: Appear strong when you are weak and appear weak when you are strong"},"francis":{1:"There are no trolls here",2:"Okay maybe just one"}}

def sendMessage(msg, channel):
  s.send("PRIVMSG "+channel+" :"+msg+"\r\n")


def quit(msg):
  sendMessage(msg, chan)
  s.send("QUIT\r\n")

def parseMessage(theBuffer):
    readbuffer=theBuffer.recv(1024)
    temp=string.split(readbuffer, "\n")
    readbuffer=temp.pop( )
    for i in temp:
      print i
    return temp

def getQuote (username, id):
  if (quoteDict.has_key(username)):
    quotes=quoteDict.get(username)
    if(quotes.has_key(id)):
          return quotes.get(id)
    return "No quotes for:"+username+"'s "+id
  return "No quotes for:"+username

def getQuotes (username):
  if (quoteDict.has_key(username)):
    return quoteDict.get(username)
  return "No quotes for:"+username 

def setQuote (username, quote):
  return "fail, not implemented yet"

#s=socket.socket( )
#s.connect((HOST, PORT))
#s.send("NICK %s\r\n" % NICK)
#s.send("USER %s %s bla :%s\r\n" % (IDENT, HOST, REALNAME))
while True:
  temp=parseMessage(s)
  for line in temp:
     line=string.rstrip(line)
     line=string.split(line)
     if(line[0]=="PING"):
       s.send("PONG %s\r\n" % line[1])
     if(line[1]=="376"):
       s.send("JOIN "+chan+"\r\n")
     if(line[1]=="353"):
       for name in line:
         if 'chris' in name or 'Chris' in name:
           sendMessage(name+" is retarded", chan)
     if(line[1]=='PRIVMSG' and line[3]==':quit'):
       quit('Look at me, I can quit!')
       break
     if(line[1]=='PRIVMSG' and line[3]=='dunnobot' and line[4]=='quotes'):
       quotes=getQuotes(line[5])
       for quote in quotes.itervalues():
         sendMessage(line[5]+":"+quote, chan)
     if(line[1]=='PRIVMSG' and line[3]=='dunnobot' and line[4]=='quote'):
       sendMessage(line[5]+":"+getQuote(line[5], line[6]), chan)
    
print getQuote("francis", 2)
print getQuote("404", 1)
for quote in quoteDict.get("francis").itervalues():
  print quote
for quote in quoteDict.get("404").itervalues():
  print quote
