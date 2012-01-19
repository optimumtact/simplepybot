#!/usr/bin/env python
import socket
import select
import io
network='segfault.net.nz'
port=6667
channel=['#bots']
nick='quotebotv2'
name='python3isformal'
bufsize=4096
incomplete_buffer=''
address=(network,port)


def recv(socket):
  d = socket.recv(bufsize)
  data=d.decode('utf-8', 'replace')
  if data:
    process_data(data)

def process_data(data):
  global incomplete_buffer
  if incomplete_buffer:
    data=incomplete_buffer+data
  if data[-2:]== '\r\n':
    split_data=data.split('\r\n')
  else:
    split_data=data.split('\r\n')
    incomplete_buffer=split_data.pop(-1)
  for line in split_data:
    if line:
      if line.startswith('PING'):
        parameters= line.split()
        pong='PONG '+parameters[1]
        send(pong)
        return
      handle_message(line)

def send(line, socket, encode="utf-8"):
  
  line = line.replace('\r', '')
  line = line.replace('\n', '')
  line = line.replace('\r\n', '') + '\r\n'
  socket.send(line.encode(encode))

def handle_message(message):
  print(message)
def connect(message):
  global address
  server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
  server.connect(address)
  send('NICK '+nick, server)
  send('USER francis devines segfault :Francis bot', server)
  return server
server=connect('true')
while True:
  recv(server)
