#!/usr/bin/env python
import configparser
import network
import linebuffer as lb
import quotestore
import re
from datetime import datetime
nick = None
channels = None

#Find command regex
find_quote_single=re.compile('^!quotes? find [0-9]+$')
find_quote_range=re.compile('^!quotes? find [0-9]+ [0-9]+$')
find_quote_name=re.compile('^!quotes? find [A-Za-z_]+$')

#add command regex
add_quote_msg=re.compile('^!quote add [\w+\s?]+$')
add_quote_user=re.compile('^!quote add <[@+]?[A-Za-z_]+ [\w+\s?]+$')

def read_file(filename):
  config = configparser.ConfigParser()
  config.read(filename)
  return config

def start():
  global nick
  global channels

  config_file = 'example.cfg'
  config = read_file(config_file)
  
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
    events = events[command]
    if event is 'welcome':
      on_welcome()
    elif event is 'privmsg':
      on_privmsg(params, endprefix, prefix)

def on_welcome():
  global channels
  network.joinall(channels)

def on_privmsg(params, message, source):
  global find_quote_single
  global find_quote_range
  global find_quote_name
  global add_quote_msg
  global add_quote_user
  channel = params[0]
  result = message.split(' ')
  if find_quote_single.match(message):
    print('find single')

  elif find_quote_range.match(message):
    print('find range')
  
  elif find_quote_name.match(message):
    print('find name')
  
  elif add_quote_msg.match(messsage):
    print('add quote message')

  elif add_quote_user.match(message):
    print('add quote by user')

  elif message.starts_with('!'):
    print('ignore malformed commands')

  else:
    now=datetime.today()
    timestamp=now.strftime('[%H:%M]')
    lb.add_line(channel, message, source, timestamp)n




start()
while True:
  messages = network.get_messages()
  handle_messages(messages)

