#handle insertion of new quote, as well as placing it into the appropriate name and date dicts
def add_quote(idnum, quote, name):
  bot.quote_dict[str(idnum)]=quote
  bot.quote_id+=1
  return quote

def remove_quote(idnum):
  quote_dict=bot.quote_dict
  quote_dict[str(idnum)]=None
  

def lookup_quote_by_user(name):
  result=[]
  for event in quoteDict:
    if name in event:
      result.append(event)
  if len(result)<1:
    return 'I have no quotes by user:'+name
  return result

def lookup_quote(id1, id2):
  quote_dict=bot.quote_dict
  max_search_range=bot.max_search_range
  result=[]
  start=int(id1)
  finish=int(id2)
  print (start)
  print (finish)
  if start > finish:
    return 'Please dont be retarded'
  
  if finish-start>maxsearchrange:
    return 'Maximum range size is:'+max_search_range

  while not start==finish:
    if str(start) in quote_dict:
      result.append(quote_dict[str(start)])
    start+=1
  
  if len(result)<1:
    if int(id1)==int(id2):
      return 'I have no quote for the id:'+id1
    else:
      return 'I have no quotes in the range '+id1+'-'+id2
  else:
    return result
