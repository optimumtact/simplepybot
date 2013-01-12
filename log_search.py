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



bot = CommandBot('LumberJack', 'irc.segfault.net.nz', 6667)
bot.join('#bots')
hb = LogModule(bot)
bot.add_module('Logging', hb)
bot.loop()

