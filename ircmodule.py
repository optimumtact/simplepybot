import event_util as eu
import logging
import logging.handlers as handlers
import commandbot as cb


class IRC_Wrapper:
    '''
    This class provides a clean wrapper around the event queue system
    that is used to talk to the network thread, basically it abstracts
    out the queue calls to provide a less verbose method of calling
    the irc methods
    '''

    def __init__(self, bot, module_name="irc", log_level=logging.DEBUG):
        self.commands = [
        ]
        self.events = [
        ]

        self.module_name = module_name
        self.log = logging.getLogger("{0}.{1}".format(bot.log_name, self.module_name))
        self.log.setLevel(log_level)
        self.bot = bot
        self.bot.add_module(self.module_name, self)
        self.log.info("Finished initialising {0}".format(module_name))

    # useful methods
    def join(self, channel, priority=3):
        '''
        Join a channel
        args:
            channel = The channel to join
        kwargs:
            priority = how quickly to process the event
        '''
        self.bot.out_event(eu.join(channel, priority))

    def nick(self, nick, priority=2):
        '''
        Send a NICk to the server
        args:
            nick = the nick to use
        kwargs:
            priority = how quickly to process the event
        '''
        self.bot.out_event(eu.nick(nick, priority))

    def user(self, nick, realname, priority=2):
        '''
        Send a USER to the server
        args:
            nick = nick
            realname = ident name
        kwargs:
            priority = how quickly to process the event
        '''
        self.bot.out_event(eu.user(nick, realname, priority))

    def connect(self, server, port, priority=1):
        '''
        Connect to a given server on a given port
        args:
            server = hostname of server to join
            port = port of server to join
        kwargs:
            priority = how quickly to process the event
        '''
        self.bot.out_event(eu.connect(server, port, priority))

    def error(self, message, priority=3):
        '''
        Send an error event to the network thread
        args:
            message = message about the error
        kwargs:
            priority = how quickly to process the event
        '''
        self.bot.out_event(eu.error(message, priority))

    def msg(self, msg, channel, priority=3):
        '''
        Send an irc msg to the given channel
        args:
            msg = the message to send
            channel = The channel to send it to
        kwargs:
            priority = how quickly to process the event
        '''
        self.bot.out_event(eu.irc_msg(action, data, priority))

    def msg_all(self, msg, channels, priority=3):
        '''
        Send an irc msg to the given channels
        args:
            msg = the message to send
            channels = The channels to send it to
        kwargs:
            priority = how quickly to process the event
        '''
        self.bot.out_event(eu.msg_all(msg, channels, priority))
    def msgs(self, msgs, channel, priority=3):
        '''
        Send a list of messages to the given channel
        args:
            msgs = the messages to send
            channel = The channel to send it to
        kwargs:
            priority = how quickly to process the event
        '''
        self.bot.out_event(eu.msgs(msgs, channel, priority))

    def msgs_all(self, msgs, channels, priority=3):
        '''
        Send a list of msgs to the given channels
        args:
            msgs = the messages to send
            channels = The channels to send it to
        kwargs:
            priority = how quickly to process the event
        '''
        self.bot.out_event(eu.msgs_all(msgs, channels, priority))

    def notice(self, msg, channel, priority=3):
        '''
        Send an irc notice to the given channel
        args:
            msg = the message to send
            channel = The channel to send it to
        kwargs:
            priority = how quickly to process the event
        '''
        self.bot.out_event(eu.notice_msg(action, data, priority))

    def notice_all(self, msg, channels, priority=3):
        '''
        Send an irc msg to the given channels
        args:
            msg = the message to send
            channels = The channels to send it to
        kwargs:
            priority = how quickly to process the event
        '''
        self.bot.out_event(eu.notice_all(msg, channels, priority))


    def quit(self, msg, priority=3):
        '''
        Send a quit command to the server
        args:
            msg = the message to send with the quit
        kwargs:
            priority = how quickly to process the event
        '''
        self.bot.out_event(eu.quit(msg, priority))

    def kill(self, priority=3):
        '''
        Used to handle Kill Events from the server
        Network also uses these to send panic events
        that will end the bot (i.e my socket broke)vent

        kwargs:
            priority = how quickly to process the event
        '''
        self.bot.out_event(eu.kill(priority))

    def pong(self, msg, priority=1):
        '''
        Send a pong to the server
        args:
            msg = the ping key
        kwargs:
            priority = how quickly to process the event
        '''
        self.bot.out_event(eu.pong(msg, priority))

    def error(self, msg, priority=1):
        '''
        Used to handle disconnection Events from the network
        thread and the irc server itself. Most bot cores
        will run reconnection logic when they get one
        of these
        kwargs:
            priority = how quickly to process the event
        '''
        self.bot.out_event(eu.error(msg, priority))

    def name(self, channel=None, priority=3):
        '''
        Send the IRC NAME command to the server, passing a
        list of channels if given
        '''
        self.bot.out_event(eu.name(channel, priority))

    def who(self, param=None, priority=3):
        '''
        Send the IRC WHO command with given parameter
        '''
        self.bot.out_event(eu.who(param, priority))
