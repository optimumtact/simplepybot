channel_dictionary=dict()
max_supported_channels=None
buffer_size=None


def intialise(max_channels=-1, max_buffer_size=-1):
  global max_supported_channels
  max_supported_channels=max_channels
  global buffer_size
  buffer_size=max_buffer_size


def add_channel(channel_name):
  global channel_dictionary
  if channel not in channel_dictionary:
    channel_dictionary[channel_name]=[]
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
  #now we append the line to the channel
  channel_dictionary[channel_name].append(line)


def find_lines(channel_name, regex):
  global channel_dictionary
  if channel in channel_dictionary:
    matches=find_lines_in_channel(channel_dictionary[channel])
    return Matches
  else:
    return None


def find_lines_in_channel(channel, regex):
  result=[]    
  for line in channel:
    if regex.matches(line):
      result.append(line)

    return result


