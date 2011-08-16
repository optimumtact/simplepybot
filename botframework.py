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

def isServerMessage(msg, server):
  if server in msg:
   return 1
  else:
    return 0

def isPing(msg):
  msg=msg.split(" ")
  if msg[1]=="PING":
    return msg[2]
  else:
    return 0

def cleanServerMessage(msg):
  clean=msg.lstrip()
  clean=clean.split(" ", 4)
  print clean
  clean[3]=clean[3].lstrip(":")
  return clean

server="segfault.net.nz"
msglist={"francis PRIVMSG #bots :this is","this is not", ":segfault.net.nz 003 rachel :Your host is gay",
         "PING :segfault.net.nz"}
for msg in msglist:
  if (isPrivMessage(msg)):
    print cleanPrivMessage(msg)
  else:
    print msg+" is not a PRIVMSG"
  if (isServerMessage(msg, server)):
    print cleanServerMessage(msg)
  else:
    print msg+" is not a server message"
  reply=isPing(msg)
  if (reply!=0):
    print reply
  else:
    print msg+" is not a ping"
