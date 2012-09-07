




class Quotebot(CommandBot):
    


    def __init__(self, network, port):
        self.commands = [
        command(r"^!quote .*", self.remember_quote)
        ]

    def remember_quote(self, source, action, targets, message, m):
