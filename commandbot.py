from network import IrcSocket
import shelve
import sys
import re
import sqlite3
from datetime import datetime, timedelta
import time
from collections import deque
import logging

from authentication import IdentAuth



class CommandBot(IrcSocket):
    '''
    A simple IRC bot with command processing, event processing and timed event functionalities
    A framework for adding more modules to do more complex stuff
    '''

    def __init__(self, nick, network, port, max_log_len = 100, authmodule=None, db_file = 'bot.db', log_name='BotCore', log_level=logging.DEBUG):
        #set up logging stuff
        self.log_name = log_name
        self.log = logging.getLogger(self.log_name)
        self.log.setLevel(logging.DEBUG)
        h = logging.StreamHandler()
        h.setLevel(log_level)
        f = logging.Formatter("%(name)s %(levelname)s %(message)s")
        h.setFormatter(f)
        self.log.addHandler(h)
        
        #set up network stuff
        #TODO I need to refactor this out into it's own thread
        super(CommandBot, self).__init__()
        assert network and port and nick
        self.modules = dict()
        
        self.connect((network, port), nick, "bot@"+network, network, nick)
        self.nick = nick
        self.network = network
        self.port = port
        
        self.times_reconnected = 0
        
        #create a ref to the db connection
        self.db = sqlite3.connect(db_file)
        
        #if no authmodule is passed through, use the default host/ident module
        if not authmodule:
            self.auth = IdentAuth(self)
        
        else:
            self.auth = authmodule

        #variables for determining when the bot is registered
        self.registered = False
        self.channels = []

        #variables for bot functionality
        self.is_mute = False

        self.commands = [
                self.command(r'syntax (?P<module>\S+)', self.syntax, direct=True),
                self.command('list modules', self.list_modules, direct=True),
                self.command('quit', self.end, direct=True, auth_level=20),
                self.command('mute', self.mute, direct=True, can_mute=False,
                             auth_level=20),
                ]
        #TODO I need to catch 441 or 436 and handle changing bot name by adding
        #a number or an underscore

        self.events = [
#               self.event('441', self.change_nick),
#               self.event('436', self.change_nick),
                self.event('001', self.registered_event),
                self.event('ERROR', self.reconnect),
                self.event('NETWORK_MODULE_SOCKET_ERROR', self.reconnect),
                self.event('PING', self.ping),
                ]

        self.timed_events = []


    def command(self, expr, func, direct=False, can_mute=True, private=False,
                auth_level=100):
        '''
        Helper function that constructs a command handler suitable for CommandBot.

        args:
            expr - regex string to be matched against user message
            func - function to be called upon a match

        kwargs:
            direct - this message must start with the bots nickname i.e botname
                     quit or botname: quit
            can_mute - Can this message be muted?
            private - Is this message always going to a private channel?
            auth_level - Level of auth this command requires (users who do not have
                         this level will be ignored

        These are intended to be evaluated against user messages and when a match is found
        it calls the associated function, passing through the match object to allow you to
        extract information from the command
        '''
        guard = re.compile(expr)
        bot = self
        def process(source, action, args, message):
            #grab nick and nick host
            nick, nickhost = source.split('!')
            #we have some whitespace to remove
            nickhost = nickhost.strip(' ')
            
            #unfortunately there is weirdness in irc and when you get addressed in
            #a privmsg you see your own name as the channel instead of theirs
            #It would be nice if both sides saw the other persons name
            #I guess they weren't thinking of bots when they wrote the spec
            for i, channel in enumerate(args[:]):
                if channel == bot.nick:
                    args[i] = nick
                    
            #make sure this message was directly addressed
            if direct:
                if not message.startswith(bot.nick):
                    return False

                #strip nick from message
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

            if auth_level:
                if not bot.auth.is_allowed(nick, nickhost, auth_level):
                    #bot.msg_all('{0} is not authenticated to do that'.format(nick), args)
                    return True

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
                
            func(source, action, args, message)
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
        This is provided so you can hook in at the loop level and change things here
        in a subclass
        '''
        while True:
            self.logic()
            time.sleep(.1)

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
            #self.log.debug('Logic loop event {0}'.format(m))

            #if a priv message we first pass it through the command handlers
            if message and action == "PRIVMSG":
                for command in self.commands:
                    try:
                        if command(source, action, args, message):
                            action ='COMMAND' #we set the action to command so valid commands can be identified by modules
                            break
                    
                    except SystemExit, msg:
                        raise SystemExit, msg
                    
                    except Exception as e:
                        self.log.exception("Error in bot command handler")
                        self.msg_all("Unable to complete request due to internal error", args)
                        
                for module_name in self.modules:
                    module = self.modules[module_name]
                    for command in module.commands:
                        try:
                            if command(source, action, args, message):
                                action = 'COMMAND'
                                break
                        
                        except SystemExit, msg:
                            raise SystemExist, msg
                        
                        except Exception as e:
                            self.log.exception("Error in module command handler:{0}".format(module_name))
                            self.msg_all("Unable to complete request due to internal error", args)

            #check it against the event commands
            for event in self.events:
                try:
                    event(source, action, args, message)
                
                except SystemExit, msg:
                    raise SystemExit, msg
                
                except Exception as e:
                    self.log.exception("Error in bot event handler")

            for module_name in self.modules:
                module = self.modules[module_name]
                for event in module.events:
                    try:
                        event(source, action, args, message)
                
                    except SystemExit, msg:
                        raise SystemExit, msg
                    
                    except Exception as e:
                        self.log.exception("Error in module event handler: {0}".format(module_name))

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
    
    def syntax (self, nick, nickhost, action, targets, message, m):
        module = m.group('module')
        if module in self.modules:
            self.msg_all(self.modules[module].syntax(), targets)
        
        else:
            self.msg_all('No module by that name, try {0}: list modules'.format(self.nick), targets)
            
    def end(self, nick, nickhost, action, targets, message, m):
        '''
        End this bot, closing each module and quitting the server
        '''
        self.quit('Goodbye for now')
        self.close()

    def mute(self, nick, nickhost, action, targets, message, m):
        '''
        Mute/unmute the bot
        '''
        self.is_mute = not self.is_mute

        if self.is_mute:
            message = 'Bot is now muted'
        
        else:
            message = 'Bot is now unmuted'

        self.msg_all(message, targets)

    def registered_event(self, source, action, args, message):
        '''
        this is called when a 001 welcome message gets received
        any actions that require you to be registered with
        name and nick first are cached and then called when
        this event is fired
        '''
        self.registered = True
        for channel in self.channels:
            self.join(channel)
    
    def reconnect(self, source, event, args, message):
        '''
        Handles disconnection by trying to reconnect 3 times
        before quitting
        '''
        if event == 'NETWORK_MODULE_SOCKET_ERROR':
            self.log.error('Closing bot due to fatal socket error')
            self.close()
            
        self.log.error('Lost connection to server:{0}'.format(message))
        if self.times_reconnected >= 3:
            self.log.error('Unable to reconnect to server on third attempt')
            self.close()
        
        else:
            self.log.info('Sleeping before reconnection attempt, {0} seconds'.format(self.times_reconnected*60))
            time.sleep(self.times_reconnected*60)
            self.registered = False
            self.times_reconnected += 1
            self.log.info('Attempting reconnection, attempt no: {0}'.format(self.times_reconnected))
            self.connect((self.network, self.port), self.nick, "bot@"+self.network, self.network, self.nick)
    
    def ping(self, source, action, args, message):
        '''
        Called on a ping, you can hook into this to get a really low resolution timer
        Suggest you use timing events instead
        '''
        self.send('PONG {0}'.format(message))
        
    def close(self):
        '''
        Handle module cleanup, database cleanup and ending script
        '''
        self.log.info("Shutting down bot")
        for module in self.modules:
            module = self.modules[module]
            module.close()
        
        self.db.close()
        sys.exit()

    #Everything below this point is just convienience methods for IRC
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
