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
                bot.command(r"^!find all (?P<match>[\w| ]+)", self.harvest_many),
                bot.command(r"^!find last (?P<match>[\w| ]+)", self.harvest)
                ]
        self.events = [
                bot.event('PRIVMSG', self.log_message)
                ]

        self.module_name = module_name
        self.bot = bot
        self.bot.add_module(module_name, self)
        self.logs = []

    def harvest_many(self, nick, nickhost, actions, targets, message, m):
        '''
        Search the logs for every item that has  the m.group("match")
        value as a substring
        '''
        messages = []
        results = self.search_logs_greedy(m.group("match"))
        if results:
            for result in results:
                messages.append ("Message:{0}|Sender:{1}".format(result.message, result.name))
            self.bot.msg_all('Found: '+', '.join(messages), targets)

        else:
            self.bot.msg_all("No matches found", targets)


    def harvest(self, nick, nickhost, actions, targets, message, m):
        """
        Search the logs for any message containing the m.group("match") value
        as a substring
        """
        result = self.search_logs(m.group("match"))
        if result:
            message = "Found:{0}|Sender:{1}".format(result.message, result.name)
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
        senders_name = source
        #store as a new log entry!
        self.logs.append(LogEntry(senders_name, message, args))

    def search_logs(self, string, name=None):
        """
        search the logs, returning the first message that contains string as a substring
        """
        for entry in self.logs:
            if string in entry.message:
                if name:
                    if entry.name == name:
                        return entry

                    else:
                        return None

                else:
                    return entry

        return None

    def search_logs_greedy(self, string, name = None):
        """
        search the logs, returning all messages that contain the string as a substring
        """
        all_matches = []
        for entry in self.logs:
            if string in entry.message:
                if name:
                    if entry.name == name:
                        all_matches.append(entry)

                    else:
                        continue

                else:
                    all_matches.append(entry)

        return all_matches

    def close(self):
        #we don't do anything special
        pass
        
class LogEntry:
    """
    simple storage class representing a logged channel message
    """
    def __init__(self, name, message, channel):
        self.channel = channel
        self.name = name
        self.message = message
        self.timestamp = datetime.datetime.utcnow()

    def __str__(self):
        return "<{0}> {1}".format(self.name, self.message)

    def __repr__(self):
        return "name:{0}, message:{1}, channel:{2}, timestamp{3}".format(self.name, self.message, self.channel, self.timestamp)

if __name__ == '__main__':
    bot = CommandBot('LumberJack', 'irc.segfault.net.nz', 6667)
    LogModule(bot)
    bot.join('#bots')
    bot.loop()

