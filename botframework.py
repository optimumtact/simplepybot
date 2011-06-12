import sys
import socket
import string

def sendMessage(msg, channel, sender):
  sender.send("PRIVMSG "+channel+" :"+msg+"\r\n")

def quit(msg, channel, sender):
  sender.send("QUIT :"+msg+"\r\n")

def cleanPrivMessage(msg):
  clean=msg.lstrip()
  clean=clean.split(" ", 3)
  clean[3]=clean[3].lstrip(":")
  return clean

def connect(server, port, nick, ident, host, realname):
  s=socket.socket()
  s.connect((server, port))
  s.send("NICK %s\r\r" %nick)
  s.send("USER %s %s bla :%s\r\n" % (ident, host, realname))
  return s

def isPrivMessage(msg):
  if "PRIVMSG" in msg:
    return 1 
  else:
    return 0


msglist={"francis PRIVMSG #bots :this is","this is not"}
for msg in msglist:
  if (isPrivMessage(msg)):
    print cleanPrivMessage(msg)
  else:
    print msg+" is not a PRIVMSG"
