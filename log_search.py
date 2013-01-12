from commandbot import *

class LogModule():
    '''
    An IRC module that offers log searching services
    Written as a runup to a quote module and to test 
    the frameworks logging features
    '''

    def __init__(self, bot):
        self.bot = bot
        self.commands = [
                command(r"^!harvest many (?P<match>.*)", self.harvest_many),
                command(r"^!harvest (?P<match>.*)", self.harvest)
                ]

        self.events = []

    def harvest_many(self, source, actions, targets, message, m):
        '''
        Search the logs for every item that can .search match the m.group("match")
        value
        '''
        print('Calling harvest many')
        messages = []
        try:
            results = self.bot.search_logs_greedy(m.group("match"), match=False)
            print(results)
            if results:
                for result in results:
                    messages.append (" [message:{0}, sender:{1}] ".format(result.message, result.name))
                self.bot.msg_all(''.join(messages), targets)

            else:
                self.bot.msg_all("No matches found", targets)

        except re.error:
            self.bot.msg_all("Not a valid regex", targets)

    def harvest(self, source, actions, targets, message, m):
        """
        Search the logs for anything matching the m.group("match") value
        """
        try:
            result = self.bot.search_logs(m.group("match"), match=False)
            if result:
                message = "Harvested:{0}, sender:{1}".format(result.message, result.name)
                self.bot.msg_all(message, targets)

            else:
                self.bot.msg_all("No match found", targets)

        except re.error:
            self.bot.msg_all("Not a valid regex", targets)

    def log_message(self, source, action, targets, message, m):
        """
        Log messages in order with a queue, these can be searched by search_logs(regex, name)
        takes standard input from self.get_messages() and does cleaning on it, specifically
        splitting the nick out of the irc senders representation (nick!username@server)
        """
        senders_name = source.split('!')[0]
        #store as a new log entry!
        self.logs.append(LogEntry(senders_name, message, targets))

    def search_logs(self, regex, name=None, match = True):
        """
        Search the stored logs for a message matching the regex given
        Parameters:
            regex:the regex to search with
        Optional:
            nick: if specified attempts to match the given value to the nick as well
            match: controls wether the regex matcher uses a .search or a .match as per  python re specs

        Returns a tuple in the format (senders nick, message receivers, message) if a match is found, otherwise
        it returns None

        This method does not capture any errors, so as to allow the bot calling to define what happens when
        the regex compile fails (a re.error is thrown, so catch that)
        """
        for entry in self.logs:

            if match:
                result = re.match(regex, entry.message)

            else:
                result = re.search(regex, entry.message)

            if result:
                if name:
                    if entry.name == name:
                        return entry

                    else:
                        return None

                else:
                    return entry

        return None

    def search_logs_greedy(self, regex, name = None, match = True):
        """
        Search the stored logs for a message matching the regex given, on a match keeps matching
        and returns a list of all matching logs
        Parameters:
            regex: the regex to search the logs with
        Optional:
            nick: if specified attempts to match the given value to the nick as well
            match: controls whether the regex matcher uses a .search or a .match as per python re specs

        Returns a tuple in the format (senders nick, message receivers, message) if a match is found, otherwise
        it returns None

        This method does not capture any errors, so as to allow the bot calling to define error handling
        """
        all_matches = []
        for entry in self.logs:

            if match:
                result = re.match(regex, entry.message)

            else:
                result = re.search(regex, entry.message)

            if result:
                if name:
                    if entry.name == name:
                        all_matches.append(entry)

                    else:
                        continue

                else:
                    all_matches.append(entry)

        return all_matches

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

if __name__ = '__main__':
    bot = CommandBot('LumberJack', 'irc.segfault.net.nz', 6667)
    bot.join('#bots')
    hb = LogModule(bot)
    bot.add_module('Logging', hb)
    bot.loop()

