#!/usr/bin/env python
import configparser
import network
import linebuffer as lb
import quotestore
nick=None
channels=None

def read_file(filename):
  config=configparser.ConfigParser()
  config.read(filename)
  return config

def start():
  global nick
  global channels

  config_file='example.cfg'
  config=read_file(config_file)
  
  settings = config['Settings']
  nick = settings['nick']
  ident = settings['ident']
  realname = settings['realname']
  quote_file = settings['quote file']

  server = config['Server']
  host = server['host']
  port = int(server['port'])
  channels = server['channels'].split(' ')

  #set up quotestore with a given quote file
  #can be given max quotes parameter
  quotestore.initalise(quote_file)
  
  #set up the linebuffer
  lb.intialise()

  network.connect((host, port), nick, ident, host, realname)

def handle_messages(messsages):
  for message in messages:
    handle_message(message)

def handle_message(prefix, command, params, endprefix):
  global events
  if command in events:
    events=events[command]
    if event is 'welcome':
      on_welcome()
    elif event is 'privmsg':
      on_privmsg(params, endprefix, prefix)

def on_welcome():
  global channels
  network.joinall(channels)

def on_privmsg(params, message, source):
  channel=params[0]
  result=message.split(' ')
  if False:
    print('temporary')

  else:
    lb.add_line(channel, (prefix, command, params, endprefix))




start()
while True:
  messages=network.get_messages()
  handle_messages(messages)

