import sys
import socket
import string

HOST="irc.segfault.net.nz"
PORT=6667
NICK="dunnobot"
IDENT="botherd"
REALNAME="This is a python bot"
readbuffer=""
chan='#cave'

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
  return "not implemented yet"

def getQuotes (username):
  return "not implemented yet either"

def setQuote (username, quote):
  return "fail not implemented yet"

s=socket.socket( )
s.connect((HOST, PORT))
s.send("NICK %s\r\n" % NICK)
s.send("USER %s %s bla :%s\r\n" % (IDENT, HOST, REALNAME))

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
     
