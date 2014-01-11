from network import Network
import shelve
import sys
import re
import sqlite3
from datetime import datetime, timedelta
import time
import logging
import event_util as eu
import Queue
import threading
from authentication import IdentAuth
from ircmodule import IRC_Wrapper
import numerics as nu
from ident import IdentHost

class CommandBot():
    '''
    A simple IRC bot with command processing, event processing and timed event functionalities
    A framework for adding more modules to do more complex stuff
    '''

    def __init__(self, nick, network, port, max_log_len = 100, authmodule=None, ircmodule=None,
                 db_file = "bot.db", module_name="core", log_name="core", log_level=logging.DEBUG,
                 log_handlers = None):

        self.modules = {}
        #set up logging stuff
        self.log_name = log_name
        self.module_name = module_name
        self.log = logging.getLogger(self.log_name)
        self.log.setLevel(log_level)
        
        #if handlers were given we need to add them
        if log_handlers:
            for handler in log_handlers:
                self.log.addHandler(handler)
                
        #set up network stuff
        #IO queues
        self.inq = Queue.PriorityQueue()
        self.outq = Queue.PriorityQueue()
        #Set up network class
        net = Network(self.inq, self.outq, self.log_name, log_level = log_level)
        #Despatch the thread
        self.log.debug("Dispatching network thread")
        thread = threading.Thread(target=net.loop)
        thread.start()
        #params for connection
        self.nick = nick
        self.network = network
        self.port = port
       
        #network stuff done

        #TODO a lot of these need to be made into config options, along with most of the
        #kwarg params
        self.max_reconnects = 3
        self.times_reconnected = 0
        self.is_running=True

        #create a ref to the db connection
        self.db = sqlite3.connect(db_file)

        #irc module bootstrapped before auth and ident, as auth uses it
        if not ircmodule:
            self.irc = IRC_Wrapper(self, log_level=log_level)
        
        else:
            self.irc = ircmodule
        
        self.ident = IdentHost(self, log_level=log_level)#set up ident
        #if no authmodule is passed through, use the default host/ident module
        if not authmodule:
            self.auth = IdentAuth(self, log_level=log_level)
        
        else:
            self.auth = authmodule

        
        #variables for determining when the bot is registered
        self.registered = False
        self.channels = []

        #variables for bot functionality
        self.is_mute = False

        self.commands = [
                self.command("quit", self.end, direct=True, auth_level=20),
                self.command("mute", self.mute, direct=True, can_mute=False,
                             auth_level=20),
                self.command(r"!syntax ?(?P<module>\S+)?", self.syntax)
                ]
        #TODO I need to catch 441 or 436 and handle changing bot name by adding
        #a number or an underscore
        #catch also a 432 which is a bad uname

        self.events = [
                eu.event(nu.RPL_ENDOFMOTD, self.registered_event),
                eu.event(nu.ERR_NOMOTD, self.registered_event),
                eu.event(nu.BOT_ERR, self.reconnect),
                eu.event(nu.BOT_KILL, self.reconnect),
                eu.event(nu.BOT_PING, self.ping),
                #TODO: can get privmsg handling as an event?
                #self.event("PRIVMSG", self.handle_priv),
                ]

        self.timed_events = []

        #send out events to connect and send USER and NICK commands
        self.irc.connect(self.network, self.port)
        self.irc.user(self.nick, "Python Robot")
        self.irc.nick(self.nick)

    def command(self, expr, func, direct=False, can_mute=True, private=False,
                auth_level=100):
        '''
        Helper function that constructs a command handler suitable for CommandBot.
        Theres are essentially an extension of the EVENT concept from message_util.py
        with extra arguments and working only on PRIVMSGS

        args:
            expr - regex string to be matched against user message
            func - function to be called upon a match

        kwargs:
            direct - this message eust start with the bots nickname i.e botname
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
            nick, nickhost = source.split("!")
            
            #unfortunately there is weirdness in irc and when you get addressed in
            #a privmsg you see your own name as the channel instead of theirs
            #It would be nice if both sides saw the other persons name
            #I guess they weren"t thinking of bots when they wrote the spec
            #so we replace any instance of our nick with their nick
            for i, channel in enumerate(args[:]):
                if channel == self.nick:
                    args[i] = nick
                    
            #make sure this message was prefixed with our bot username
            if direct:
                if not message.startswith(bot.nick):
                    return False

                #strip nick from message
                message = message[len(bot.nick):]
                #strip away any syntax left over from addressing
                #this may or may not be there
                message = message.lstrip(": ")
            
            #If muted, or message private, send it to user not channel
            if (self.is_mute or private) and can_mute:
                #replace args with usernick stripped from source
                args = [nick]
            

            #check it matches regex and grab the matcher object so the function can
            #pull stuff out of it
            m = guard.match(message)
            if not m:
                return False

            '''
            auth_level < 0 means do no auth check at all!, this differs from the default
            which gives most things an auth_level of 100. The only thing that currently uses
            it is the auth module itself, for bootstrapping authentication. Not recommened for
            normal use as people may want ignore people who are not in the auth db, and they
            will change how level 100 checks are managed
            '''
            if auth_level:
                if auth_level > 0 and not bot.auth.is_allowed(nick, nickhost, auth_level):
                    return True #Auth failed but was command

            #call the function
            func(nick, nickhost, action, args, message, m)
            return True

        return process
    
    def in_event(self, event):
        self.inq.put(event)
    
    def out_event(self, event):
        self.outq.put(event)

    def add_module(self, name, module):
        '''
        Add the given module to the modules dictionary under the given name
        Raises a key error if the name is already in use
        '''
        if name in self.modules:
            raise KeyError(u"Module name:{0} already in use".format(name))
        self.modules[name] = module

    def get_module(self, name):
        '''
        Returns the module stored in module dict under the key given by name
        Raises a key error if there is no module with that name
        '''
        if name not in self.modules:
            raise KeyError(u"No module with the name:{0}".format(name))
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
        t_event = eu.TimedEvent(start_time, end_time, interval, func, func_args, func_kwargs)
        self.timed_events.append(t_event)

    def loop(self):
        '''
        Primary loop.
        You'll need to transfer control to this function before execution begins.
        This is provided so you can hook in at the loop level and change things here
        in a subclass
        '''
        while self.is_running:
            self.logic()
            time.sleep(.1)
        self.log.info("Bot ending")

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
        try:
            #try to grab an event from the inbound queue
            m_event = self.inq.get(False)
            self.log.debug(u"Inbound event {0}".format(m_event))
            was_event = False
            #this is the cleaned data from an irc msg
            #i.e PRIVMSG francis!francis@localhost [#bots] "hey all"
            #if a priv message we first pass it through the command handlers
            if m_event.type == nu.BOT_PRIVMSG:
                was_event=True
                #unpack the data!
                action, source, args, message = m_event.data
                for command in self.commands:
                    try:
                        if command(source, action, args, message):
                            action = nu.BOT_COMM #we set the action to command so valid commands can be identified by modules
                            break #TODO, should we break, needs a lot more thought

                    except Exception as e:
                        self.log.exception(u"Error in bot command handler")
                        self.irc.msg_all(u"Unable to complete request due to internal error", args)
                        

                for module_name in self.modules:
                    module = self.modules[module_name]
                    for command in module.commands:
                        try:
                            if command(source, action, args, message):
                                action = nu.BOT_COMM
                                break

                        except Exception as e:
                            self.log.exception("Error in module command handler:{0}".format(module_name))
                            self.irc.msg_all("Unable to complete request due to internal error", args)

            #check it against the event commands
            for event in self.events:
                try:
                    if event(m_event):
                        was_event = True

                except Exception as e:
                    self.log.exception("Error in bot event handler")

            for module_name in self.modules:
                module = self.modules[module_name]
                for event in module.events:
                    try:
                        if event(m_event):
                            was_event = True

                    except Exception as e:
                        self.log.exception(u"Error in module event handler: {0}".format(module_name))

            if not was_event:
                self.log.debug(u"Unhandled event {0}".format(m_event))

        except Queue.Empty:
            #nothing to do
            pass

        #clone timed events list and go through the clone
        for event in self.timed_events[:]:
            if event.should_trigger():
                try:
                    event.func(*event.func_args, **event.func_kwargs)

                except Exception as e:
                    self.log.exception("Error in timed event handler")

            if event.is_expired():
                #remove from the original list
                self.timed_events.remove(event)

        return

    def syntax (self, nick, nickhost, action, targets, message, m):
        '''
        either lists all module names or if a modulename is provided
        calls that modules syntax method
        '''
        if m.group("module"):
            module = m.group("module")
            if self.has_module(module):
                try:
                    self.get_module(module).syntax()

                except AttributeError as e:
                    self.log.warn(u"Module {0} has no syntax method".format(module))
        
        else:
            msg = ", ".join(self.modules.keys())
            self.irc.msg_all(msg, targets)

    def end(self, nick, nickhost, action, targets, message, m):
        '''
        End this bot, closing each module and quitting the server
        '''
        self.log.info("Shutting down bot")
        self.db.close()
        for name in self.modules:
            module = self.modules[name]
            try:
                module.close()
            except AttributeError as e:
                self.log.warning(u"Module {0} has no close method".format(name))

        self.irc.quit("Goodbye for now")
        self.irc.kill()
        self.is_running=False

    def mute(self, nick, nickhost, action, targets, message, m):
        '''
        mute/unmute the bot
        '''
        self.is_mute = not self.is_mute

        if self.is_mute:
            message = "Bot is now muted"
        
        else:
            message = "Bot is now unmuted"

        self.irc.msg_all(message, targets)

    def registered_event(self, source, action, args, message):
        '''
        this is called when a 001 welcome message gets received
        any actions that require you to be registered with
        name and nick first are cached and then called when
        this event is fired, for example, joining channels
        '''
        #TODO: what else do we need to extend this too?
        #messages/privmsgs
        self.registered = True
        for channel in self.channels:
            self.join(channel)

    def join(self, channel):
        if self.registered:
            #send join event
            self.irc.join(channel)
            #tell the ident module we joined this channel
            self.ident.join_channel(channel)
            if not(channel in self.channels):
                self.channels.append(channel)
        else:
            self.channels.append(channel)

    def reconnect(self, source, event, args, message):
        '''
        Handles disconnection by trying to reconnect 3 times
        before quitting
        '''
        #if we have been kicked, don"t attempt a reconnect
        if  event == "KILL":
            self.log.info("No reconnection attempt due to being killed")
            self.close()
            
        self.log.error("Lost connection to server:{0}".format(message))
        if self.times_reconnected >= self.max_reconnects:
            self.log.error("Unable to reconnect to server on third attempt")
            self.close()
        
        else:
            self.log.info(u"Sleeping before reconnection attempt, {0} seconds".format(self.times_reconnected*60))
            time.sleep((self.times_reconnected+1)*60)
            self.registered = False
            self.log.info(u"Attempting reconnection, attempt no: {0}".format(self.times_reconnected))
            self.times_reconnected += 1
            #set up events to connect and send USER and NICK commands
            self.irc.connect(self.network, self.port)
            self.irc.user(self.nick, "Python Robot")
            self.irc.nick(self.nick)
    
    def ping(self, source, action, args, message):
        '''
        Called on a ping and responds with a PONG
        Module authors can also hook the PING event for a low resolution timer
        if you didn"t want to use the timed events system for some reason
        '''
        self.irc.pong(message)
