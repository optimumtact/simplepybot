import re
channel_dictionary=dict()
max_channels=None
buffer_size=20

#allows me to use this class like a Struct and assign it arbitrary values
#using this to store counts associated with each line without having to 
#dick around with storing them somewhere in the list
class Store:
  pass

#this one here is used for storing the message, time  and name associated
#with each line in the buffer
class Line:
  pass

def intialise( max_buffer_size=-1, max_channel_size=-1):
  global max_channels
  max_channels = max_channel_size
  if max_buffer_size > 0:
    global buffer_size
    buffer_size = max_buffer_size


def add_channel(channel_name):
  global max_channels
  global channel_dictionary

  if len(channel_dictionary) >= max_channels:
    return False

  global buffer_size
  if channel not in channel_dictionary:
    #intialise the channel with it's message count value
    temp = Store()
    temp.count =0
    temp.lines = []
    channel_dictionary[channel] = temp
    return True

  else:
    return False


def remove_channel(channel_name):
  global channel_dictionary
  if channel not in channel_dictionary:
    return False

  else:
    del channel_dictionary[channel_name]
    return True

def add_line(channel_name, line, name, time):
  global channel_dictionary
  #this will add the channel if it does not yet exist
  add_channel(channel_name)

  #get the channel we want to add the line too
  channel = channel_dictionary[channel_name]

  #now we append the line to the channel
  add_line_to_channel(channel, line, name, time)


def add_line_to_channel(channel, line, name, time):
  global buffer_size
  count = channel.count
  temp = Line()
  temp.name = name
  temp.time = time
  temp.message = line

  if count >= buffer_size:
    count = 0

  channel.lines[count] = temp
  count = count + 1
  channel.count = count


def find_lines(channel_name, regex):
  global channel_dictionary
  if channel in channel_dictionary:
    matches = find_lines_in_channel(channel_dictionary[channel], regex)
    return Matches
  else:
    return None

def find_lines_by_name(channel, name, regex):
  global channel_dictionary
  if channel in channel_dictionary:
    matches = find_lines_by_name_in_channel(channel_dictionary[channel], name, message)
    return matches
  else:
    return None


def find_lines_in_channel(channel, regex):
  result = []    
  for line in channel.lines:
    if re.matches(line.message, regex):
      result.append(line)

    return result

def find_lines_by_name_in_channel(channel, user_name, user_message):
  result = []
  for line in channel.lines:
    if re.match(user_messsage, line.message) and user_name is line.name:
      result.append(line)

