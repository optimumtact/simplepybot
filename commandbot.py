from network import IrcSocket
import shelve
import sys
import re

from datetime import datetime, timedelta
from time import sleep
from collections import deque
import logging



class CommandBot(IrcSocket):
    '''
    A simple IRC bot with command processing, event processing and timed event functionalities
    A framework for adding more modules to do more complex stuff
    '''

    def __init__(self, nick, network, port, max_log_len = 100, authmodule=None):
        super(CommandBot, self).__init__()
        assert network and port and nick
        self.modules = dict()
        self.connect((network, port), nick, "bot@"+network, network, nick)
        self.nick = nick
        self.server = network
        self.port = port
        
        #if no authmodule is passed through, use the default host/ident module
        #if not authmodule:
        #    authmodule = new IdentAuth()
        
        #variables for determining when the bot is registered
        self.registered = False
        self.channels = []

        #variables for bot functionality
        self.is_mute = False

        self.commands = [
                self.command('list modules', self.list_modules, direct=True),
                self.command('quit', self.end, direct=True),
                self.command('mute', self.mute, direct=True, can_mute=False),
                ]
        #TODO I need to catch 441 or 436 and handle changing bot name by adding
        #a number or an underscore

        self.events = [
#               self.event('441', self.change_nick),
#               self.event('436', self.change_nick),
                self.event('001', self.registered_event),
                ]

        self.timed_events = []


    def command(self, expr, func, direct=False, can_mute=True, private=False):
        '''
        Helper function that constructs a command handler suitable for CommandBot.

        Takes a regex source string and a function.
        there are two flag values, direct and private. direct sets it up so the
        bot will only respond to the command if it has had it's nickname 
        prefixed to the command i.e botname: quit or botname quit, private
        determines if the command will still be sent to the common channel if
        the bot has been muted (results sent via privmsg)
        #TODO - implemented the mute framework :p

        These are intended to be evaluated against user messages and when a match is found
        it calls the associated function, passing through the match object to allow you to
        extract information from the command
        '''
        guard = re.compile(expr)
        bot = self
        def process(source, action, args, message):
            #grab nick and nick host
            nick, nickhost = source.split('!')
            
            #unfortunately the irc spec is not sane and when you get addressed in
            #a privmsg you see your own name as the channel (why not theirs? who knows)
            #so we have to change it ourselves
            for i, channel in enumerate(args[:]):
                if channel == bot.nick:
                    args[i] = nick
                    
            #make sure this message was directly addressed
            if direct:
                if not message.startswith(bot.nick):
                    return False

                #strip nick from bot
                message = message[len(bot.nick):]
                #strip away any syntax left over from addressing
                message = message.lstrip(': ')
            
            #If muted, or message private, send it to user not channel
            if (self.is_mute or private) and can_mute:
                #replace args with name stripped from source
                args = [nick]

            #check it matches our command regex
            m = guard.match(message)
            if not m:
                return False

            #call the function
            func(nick, nickhost, action, args, message, m)
            return True

        return process

    def event(self, event_id, func):
        '''
        Helper function that constructs an event handler suitable for CommandBot.
        These are intended to capture events from IRC servers, such as the 001 event 
        you receive for correctly registering, or errors such as nick in use
        '''
        event_id = event_id
        def process(source, action, args, message):
            if not event_id == action:
                return False

            #grab nick and nick host
            nick, nickhost = source.split('!')
            func(nick, nickhost, action, args, message)
            return True
        return process

    def add_module(self, name, module):
        '''
        Add the given module to the modules dictionary under the given name
        Raises a key error if the name is already in use
        '''
        if name in self.modules:
            raise KeyError("Module name:{0} already in use".format(name))
        self.modules[name] = module

    def get_module(self, name):
        '''
        Returns the module stored in module dict under the key given by name
        Raises a key error if there is no module with that name
        '''
        if name not in self.modules:
            raise KeyError("No module with the name:{0}".format(name))

        return self.modules[name]

    def has_module(self, name):
        '''
        Returns true if the bot has this module or false otherwise
        '''
        if name not in self.modules:
            return False

        else:
            return True
    
    def run_event_in(self, seconds, func, func_args=(), func_kwargs={}):
        '''
        Helper function that runs an event x seconds in the future, where seconds
        is how many seconds from now to run it
        '''
        start_time = datetime.now()
        interval = timedelta(seconds=seconds)
        end_time = start_time + interval
        self.add_timed_event(start_time, end_time, interval, func, func_args, func_kwargs)
        
    def add_timed_event(self, start_time, end_time, interval, func, func_args=(), func_kwargs={}):
        '''
        Add an event that will trigger once at start_time and then every time
        interval amount of time has elapsed it will trigger again until end_time
        has passed

        Start time and end time are datetime objects
        and interval is a timedelta object
        '''
        self.timed_events.append(TimedEvent(start_time, end_time, interval, func, func_args, func_kwargs))


    def loop(self):
        '''
        Primary loop.

        You'll need to transfer control to this function before execution begins.

        Sets up the dbm instance
        '''
        with BotDB('BOTDB') as self.storage:
            while True:
                self.logic()
                sleep(.1)

    def logic(self):
        '''
        Simple logic processing.

        Examines all messages received, then attempts to match commands against any messages, in 
        the following order

        if a privmsg
            commands local to commandbot
            commands in modules loaded

        all messages(including privmsgs)
        events local to commandbot
        events in modules loaded

        It also evaluates all timed events and triggers them appropriately
        '''
        for m in self.get_messages():
            was_command = False
            source, action, args, message = m
            print(m)

            #if a priv message we first pass it through the command handlers
            if message and action == "PRIVMSG":
                #TODO try catch block for errors
                for command in self.commands:
                    if command(source, action, args, message):
                        action ='COMMAND' #we set the action to command so valid commands can be identified by modules
                        break

                for module in self.modules:
                    module = self.modules[module]
                    for command in module.commands:
                        if command(source, action, args, message):
                            action = 'COMMAND'
                            break

            #check it against the event commands
            #TODO try catch blocks for errors
            for event in self.events:
                event(source, action, args, message)

            for module in self.modules:
                module = self.modules[module]
                for event in module.events:
                    event(source, action, args, message)

        #clone timed events list and go through the clone
        for event in self.timed_events[:]:
            if event.should_trigger():
                #TODO try catch block for errors
                event.func(*event.func_args, **event.func_kwargs)

            if event.is_expired():
                #remove from the original list
                self.timed_events.remove(event)

        return

    def list_modules(self, nick, nickhost, action, targets, message, m):
        '''
        Send a list of all loaded modules
        '''
        self.msg_all(', '.join(self.modules.keys()), targets)

    def end(self, nick, nickhost, action, targets, message, m):
        for module in self.modules:
            module = self.modules[module]
            module.close()

        self.quit('Goodbye for now')
        sys.exit()

    def mute(self, nick, nickhost, action, targets, message, m):
        '''
        Mute/unmute the bot
        '''
        self.is_mute = not self.is_mute

        if self.is_mute:
            message = 'Bot is now muted'
        
        else:
            message= 'Bot is now unmuted'

        self.msg_all(message, targets)

    def msgs_all(self, msgs, channels):
        """
        Accepts a list of messages to send to a list of channels
        msgs: A list of messages to send
        channels: A list of targets to send it to
        """
        for channel in channels:
            for message in msgs:
                self.msg(message, channel)

    def msg_all(self, message, channels):
        """
        Accepts a message to send to a list of channels
        message: the message to send
        channels: A list of targets to send it to
        """
        for channel in channels:
            self.msg(message, channel)

    def msg(self, message, channel):
        '''
        Send a message to a specific target.
        message: the message to send
        channel: the target to send it to
        '''
        self.send('PRIVMSG ' + channel + ' :' + message)

    def join(self, channel):
        '''
        Join a channel.
        channel: the channel to join
        The channel should contain one or more # symbols as needed.

        '''
        if self.registered:
            self.send('JOIN ' + channel)

        else:
            self.channels.append(channel)

    def registered_event(self, nick, nickhost, action, args, message):
        '''
        this is called when a 001 welcome message gets received
        any actions that require you to be registered with
        name and nick first are cached and then called when
        this event is fired
        '''
        self.registered = True
        for channel in self.channels:
            self.join(channel)

    def quit(self, message):
        '''
        Disconnects from a server with a given QUIT message.
        message: message to display with quit
        '''
        self.send('QUIT :' + message)

    def leave(self, channel, message=None):
        '''
        Leaves a channel, optionally sending a message to the channel first.
        channel: Channel to leave
        message: optional message to send first
        '''
        if message:
            self.msg(message, channel)
        self.send('PART ' + channel)


class BotDB:
    """
    Trivial wrapper class over shelve to enable use in with statements.
    """
    def __init__(self, name):
        """
        Store the given name to use for this Database
        """
        self.name = name

    def __enter__(self):
        """
        Set up the internal db with the right settings
        """
        self._internal = shelve.open(self.name, 'c')
        return self._internal

    def __exit__(self, type, value, traceback):
        """
        On exit we simply close internal db instance
        """
        self._internal.close()

class TimedEvent():
    '''
    Represents a timed event, 
    the should_trigger method will return true if the 
    function should be triggered at the current time

    the is_expired method will return true if the timedevent
    has expired (gone past it's end_date)
    '''

    def __init__(self, start_date, end_date, interval, func, func_args, func_kwargs):
        '''
        set up a new timed event object 
        '''
        self.sd = start_date
        self.ed = end_date
        self.interval = interval
        self.func = func
        self.func_args = func_args
        self.func_kwargs = func_kwargs

        self.next_timeout = self.sd + self.interval

    def should_trigger(self):
        '''
        Returns true if the timed event interval has elapsed and we need
        to trigger the function. It also updates when the next timeout
        should occur
        '''
        current_time = datetime.now()
        if current_time > self.next_timeout:
            self.next_timeout = current_time + self.interval
            return True

        else:
            return False

    def is_expired(self):
        '''
        Returns true if the current time is greater than the end_time for
        this event
        '''
        if datetime.now() > self.ed:
            return True

        else:
            return False
