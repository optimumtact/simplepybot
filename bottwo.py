import sys
import socket
import string

HOST="irc.segfault.net.nz"
PORT=6667
NICK="swarm"
IDENT="botherd"
REALNAME="This is a python bot"
readbuffer=""
chan='#cave'
amount=2
def sendMessage(bot, msg, channel):
  bot.send("PRIVMSG "+channel+" :"+msg+"\r\n")

def join(bot,channel):
  bot.send("JOIN "+channel+"\r\n")

def quit(msg):
  sendMessage(msg, chan)
  s.send("QUIT\r\n")

def connect(server, port, nick):
  s=socket.socket( )
  s.connect((server, port))
  s.send("NICK %s\r\n" %nick)
  s.send("USER %s %s bla :%s\r\n" % (IDENT, HOST, REALNAME))
  return s

botlist=[]
count=0
while count!=amount:
  count+=1
  bot=(connect(HOST, PORT, NICK+str(count)))
  botlist.append(bot)
   


for bot in botlist:
  join(bot, chan)
  sendMessage(bot, "SWARM HIM", chan)
  


while 1:
  input=raw_input("Enter Message: ")
  for bot in botlist:
    sendMessage(bot,input,chan)

