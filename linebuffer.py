import re
channel_dictionary=dict()
max_channels=None
buffer_size=20


def intialise( max_buffer_size=-1, max_channel_size=-1):
  global max_channels
  max_channels = max_channel_size
  if max_buffer_size > 0:
    global buffer_size
    buffer_size = max_buffer_size


def add_channel(channel_name):
  global max_channels
  if len(channel_dictionary) >= max_channels:
    return False

  global channel_dictionary
  global buffer_size
  if channel not in channel_dictionary:
    #intialise the channel with it's message count value
    channel_dictionary[channel_name] = [0]
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

def add_line(channel_name, line):
  global channel_dictionary
  #this will add the channel if it does not yet exist
  add_channel(channel_name)

  #get the channel we want to add the line too
  channel = channel_dictionary[channel_name]

  #now we append the line to the channel
  add_line_to_channel(channel, line)


def add_line_to_channel(channel, line):
  global buffer_size
  count = channel[0]

  if count >= buffer_size:
    count = 0

  channel[count + 1] = line
  count = count + 1
  channel[0] = count



def find_lines(channel_name, regex):
  global channel_dictionary
  if channel in channel_dictionary:
    matches = find_lines_in_channel(channel_dictionary[channel])
    return Matches
  else:
    return None


def find_lines_in_channel(channel, regex):
  result = []    
  for line in channel:
    if regex.matches(line):
      result.append(line)

    return result


