from commandbot import *
import datetime

class LogModule():
    '''
    An IRC module that offers log searching services
    Written as a runup to a quote module and to test 
    the frameworks logging features
    '''

    def __init__(self, bot, module_name = "Logging"):
        self.commands = [
                bot.command(r"^!find all (?P<match>[\w| ]+) by (?P<name>\w+)", self.harvest_many_by_name),
                bot.command(r"^!find all (?P<match>[\w| ]+)", self.harvest_many),
                bot.command(r"^!find (?P<direction>last|first) (?P<match>[\w| ]+)", self.harvest)
                
                ]
        self.events = [
                bot.event('PRIVMSG', self.log_message)
                ]

        self.module_name = module_name
        self.bot = bot
        self.bot.add_module(module_name, self)
        self.logs = []

    
    def harvest_many_by_name(self, nick, nickhost, action, targets, message, m):
        '''
        Sarch the logs for every item that has m.group("match") as a substring
        and was said by nick m.group("name")
        '''
        messages = []
        results = self.search_logs(m.group("match"), name=m.group("name"))
        if results:
            for result in results:
                messages.append(str(result))
            self.bot.msg_all(', '.join(messages), targets)

        else:
            self.bot.msg_all("No matches found", targets)
            
    def harvest_many(self, nick, nickhost, actions, targets, message, m):
        '''
        Search the logs for every item that has  the m.group("match")
        value as a substring
        '''
        messages = []
        results = self.search_logs(m.group("match"))
        if results:
            for result in results:
                messages.append(str(result))
            self.bot.msg_all(', '.join(messages), targets)

        else:
            self.bot.msg_all("No matches found", targets)


    def harvest(self, nick, nickhost, actions, targets, message, m):
        """
        Search the logs for any message containing the m.group("match") value
        as a substring
        """
        direction = m.group("direction")
        match = m.group("match")
        if direction == "last":
            results = self.search_logs(match, reverse=True)
        
        else:
            results = self.search_logs(match)
        
        if results:
            message = str(results[0])
            self.bot.msg_all(message, targets)

        else:
            self.bot.msg_all("No match found", targets)


    def log_message(self, source, action, args, message):
        """
        Log messages in order with a queue, these can be searched by search_logs(regex, name)
        takes standard input from self.get_messages() and does cleaning on it, specifically
        splitting the nick out of the irc senders representation (nick!username@server)

        is triggered by any event with a PRIVMSG command, note that privmsgs that are valid commands
        are not logged, as they are given a new event type of COMMAND, if you want you could extend
        the logger to log this
        """
        nick, nickhost = source.split('!')
        #store as a new log entry!
        self.logs.append(LogEntry(nick, nickhost, message, args))

    def search_logs(self, string, reverse = False, name = None):
        """
        search the logs, returning all messages that contain the string as a substring
        """
        searchlist = []
        
        if reverse:
            searchlist = self.logs[::-1]
            
        else:
            searchlist = self.logs
            
        all_matches = []
        for entry in searchlist:
            if string in entry.message:
                if name:
                    if entry.nick == name:
                        all_matches.append(entry)

                    else:
                        continue

                else:
                    all_matches.append(entry)

        return all_matches
    
    def syntax(self):
        return '''
            Log Search Module supports
            !find all {some string}
            !find all {some string} by {some name}
            !find [list|first] {some string}
            '''
        
    def close(self):
        #we don't do anything special
        pass
        
class LogEntry:
    """
    simple storage class representing a logged channel message
    """
    def __init__(self, nick, nickhost, message, channel):
        self.channel = channel
        self.nick = nick
        self.nickhost = nickhost
        self.message = message
        self.timestamp = datetime.datetime.utcnow()

    def __str__(self):
        return "<{0}> {1}".format(self.nick, self.message)

    def __repr__(self):
        return "nick:{0}, nickhost:{4} message:{1}, channel:{2}, timestamp{3}".format(self.nick, self.message, self.channel, self.timestamp, self.nickhost)

if __name__ == '__main__':
    bot = CommandBot('LumberJack', 'irc.segfault.net.nz', 6667)
    LogModule(bot)
    bot.join('#bots')
    bot.loop()

