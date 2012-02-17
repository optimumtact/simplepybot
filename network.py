#!/usr/bin/env python
import socket
import select
import io
import message
socket
bufsize=4096
incomplete_buffer=""
def recv():
  global socket
  global bufsize
  d = socket.recv(bufsize)
  data=d.decode('utf-8', 'replace')
  if data:
    process_data(data)

def process_data(data):
  global incomplete_buffer
  if incomplete_buffer: #if there is incomplete data
    data=incomplete_buffer+data #add it to the data we just recieved (in the recv method)
  if data[-2:]== '\r\n':
    split_data=data.split('\r\n')#this will split the data into the proper messages(assuming they are all full messages
                                 #i.e the last message is not incomplete
  else:
    split_data=data.split('\r\n')#this handles the case where the last message in data may be incomplete
    incomplete_buffer=split_data.pop(-1)
  for line in split_data:
    if line:
      if line.startswith('PING'):#automatically respond to pings
        parameters= line.split()
        pong='PONG '+parameters[1]
        send(pong)
        return
      message.parseMessage(line)

def send(line, encode="utf-8"):
  global socket
  line = line.replace('\r', '')
  line = line.replace('\n', '')
  line = line.replace('\r\n', '') + '\r\n'
  socket.send(line.encode(encode))

def join (channels):
  global socket
  for channel in channels:
    socket.send('JOIN #'+channel)

def connect(address, nick, ident, server, realname):
  global socket
  socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
  socket.connect(address)
  send('NICK '+nick)
  send('USER '+nick+' '+ident+' '+server+' '+' :'+realname)
  return server
