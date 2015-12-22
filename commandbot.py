from network import Network
import shelve
import sys
import re
import sqlite3
from datetime import datetime, timedelta
import time
import logging
import logging.config
import event_util as eu
import queue as q 
import threading
import numerics as nu
import signal
import configparser
import json
import importlib


class CommandBot():
    '''
    A simple IRC bot with command processing, event processing and timed event functionalities
    A framework for adding more modules to do more complex stuff
    '''

    def __init__(self, config_file='basic.ini', authmodule=None):
        self.module_name = 'core'
        
        #read in config and parse it (this also sets up any submodule config
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

    
        self.modules = {}
        # set up logging from json config file
        with open(self.config[self.module_name]['log_config']) as f:
            logdict = json.load(f)

        logging.config.dictConfig(logdict) 
        self.log_name = 'bot'
        self.log = logging.getLogger(self.log_name)
        
        # variables for determining when the bot is registered
        self.registered = False
        self.channels = []

        # variables for bot functionality
        self.is_mute = False


        self.timed_events = []

        # set up network stuff
        # IO queues
        self.inq = q.PriorityQueue()
        self.outq = q.PriorityQueue()
        # Set up network class
        net = Network(self.inq, self.outq, self.log_name)
        # Dispatch the thread
        self.log.debug("Dispatching network thread")
        thread = threading.Thread(target=net.loop)
        #this is not gonna do much but loop atm
        thread.start()

        #start reading and handling constants
        # params for connection
        self.nick = self.config[self.module_name]['nick']
        self.realname = self.config[self.module_name]['realname']
        self.network = self.config[self.module_name]['network']
        self.port = int(self.config[self.module_name]['port'])
        self.commandprefix = self.config[self.module_name]['commandprefix']

        # network stuff done

        self.max_reconnects = int(self.config[self.module_name]['max_reconnects'])
        self.times_reconnected = 0
        self.is_running = True

        # create a ref to the db connection
        self.db = sqlite3.connect(self.config[self.module_name]['db_file'])
        
        #load core modules (functionality below depends on this
        core_modules = self.config[self.module_name]['core_modules']
        core_modules = core_modules.split(',')
        for core_module in core_modules:
            self.load_module(self.config[core_module])


        #add modules defined by user in the config file
        custom_modules = self.config[self.module_name]['modules']
        custom_modules = custom_modules.split(',')
        for module in custom_modules:
            self.load_module(self.config[module])
        
        
        # register signal handlers (closes bot)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGQUIT, self.signal_handler)

        # events/commands we respond too
        self.commands = [
            self.command("quit", self.end_command_handler, direct=True, auth_level=20),
            self.command("mute", self.mute, direct=True, can_mute=False,
                         auth_level=20),
            self.command(r"syntax ?(?P<module>\S+)?", self.syntax),
        ]
        # TODO I need to catch 441 or 436 and handle changing bot name by adding
        # a number or an underscore
        # catch also a 432 which is a bad uname

        self.events = [
            self.event(nu.RPL_ENDOFMOTD, self.registered_event),
            self.event(nu.ERR_NOMOTD, self.registered_event),
            self.event(nu.BOT_ERR, self.reconnect),
            self.event(nu.BOT_KILL, self.reconnect),
            self.event(nu.BOT_PING, self.ping),
            self.event(nu.BOT_PRIVMSG, self.handle_privmsg),
        ]
        # send out events to connect and send USER and NICK commands
        self.irc.connect(self.network, self.port)
        self.irc.user(self.nick, self.realname)
        self.irc.nick(self.nick)

    def command(self, expr, func, direct=False, can_mute=True, private=False, auth_level=100):
        return eu.command(self, expr, func, direct, can_mute, private, auth_level)
    
    def event(self, event_id, func):
        return eu.event(event_id, func)

    def in_event(self, event):
        self.inq.put(event)

    def out_event(self, event):
        self.outq.put(event)

    def load_module(self, module_config):
        self.log.info('Attempting to load module {0}'.format(module_config['modulename']))
        modpath = 'modules.{0}'.format(module_config['filename'])
        module = importlib.import_module(modpath)
        klass = getattr(module, module_config['class'])
        instance = klass(self, module_config['modulename'])
        if 'core' in module_config:
            setattr(self, module_config['core'], instance)

        self.add_module(module_config['modulename'], instance)

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
        Helper function that runs an event x seconds in the future,
        where seconds is how many seconds from now to run it
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
        '''
        t_event = eu.TimedEvent(start_time, end_time, interval, func, func_args, func_kwargs)
        self.timed_events.append(t_event)

    def add_repeat_event(self, start_time, repeat_count, interval, func, func_args=(), func_kwargs={}):
        r_event = eu.RepeatingEvent(start_time, repeat_count, interval, func, func_args, func_kwargs)
        self.timed_events.append(r_event)

    def loop(self):
        '''
        Primary loop.
        You'll need to transfer control to this function before execution begins.
        This is provided so you can hook in at the loop level and change things here
        in a subclass
        '''
        # TODO - Exception handling that panic kills the IRC network thread
        # so it doesn't just hang when it dies to some bad code thats not inside
        # the more robust module handling code
        while self.is_running:
            self.handle_event()
            time.sleep(.1)

        self.cleanup()
        self.log.info("Bot ending")

    def handle_event(self):
        '''
        try to match the event against events local to commandbot
        then against events in modules loaded. PRIV_MSG are handled at this
        point by the inbuilt priv_msg event handler

        It also evaluates all timed events and triggers them appropriately
        '''
        try:
            # try to grab an event from the inbound queue
            m_event = self.inq.get(False)
            self.log.debug(u"Inbound event {0}".format(m_event))
            was_event = False

            # check it against the event commands
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

        except q.Empty:
            # nothing to do
            pass

        # clone timed events list and go through the clone
        for event in self.timed_events[:]:
            if event.should_trigger():
                try:
                    event.func(*event.func_args, **event.func_kwargs)

                except Exception as e:
                    self.log.exception("Error in timed event handler")

            if event.is_expired():
                # remove from the original list
                self.timed_events.remove(event)

        return

    def handle_privmsg(self, action, source, args, message):
        '''
        We have received a privmsg, loop through the commands in our command handler
        and in the module command handlers trying to find matches
        '''
        try:
            for command in self.commands:
                if command(source, action, args, message):
                    # we set the action to command so valid commands can be identified by modules
                    action = nu.BOT_COMM
                    break

        except Exception as e:
            self.log.exception(u"Error in bot command handler")
            self.irc.msg_all(u"Unable to complete request due to internal error", args)

        try:
            for module_name in self.modules:
                module = self.modules[module_name]
                for command in module.commands:
                    if command(source, action, args, message):
                        action = nu.BOT_COMM
                        break

        except Exception as e:
            self.log.exception("Error in module command handler:{0}".format(module_name))
            self.irc.msg_all("Unable to complete request due to internal error", args)

    def ctcp_version(self, nick, nickhost, action, targets, message, m):
        '''
        We just got a ctcp request, respond with something useful
        '''
        msg = u'\x01VERSION Simplepythonbot github.com/optimumtact/simplepybot\x01'
        self.irc.notice_all(msg, targets)

    def syntax(self, nick, nickhost, action, targets, message, m):
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


    def signal_handler(self, signum, frame):
        self.log.info('Recieived sigint, closing')
        self.close()
    
    def end_command_handler(self, nick, nickhost, action, targets, message, m):
        self.close()

    def close(self):
        '''
        End this bot, closing each module and quitting the server
        '''
        self.log.info("Shutting down bot")
        for name in self.modules:
            module = self.modules[name]
            try:
                module.close()
            except AttributeError as e:
                self.log.warning(u"Module {0} has no close method".format(name))

        self.irc.quit("Goodbye for now")
        self.irc.kill()
        self.is_running = False

    def cleanup(self):
        '''
        Called after all modules are closed and no more events to be processed,
        cleanup any final bits and pieces
        '''
        self.log.info('Cleaning up after myself')
        self.db.close()

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
        # TODO: what else do we need to extend this too?
        # TODO: extend this to a generic framework
        self.registered = True
        for channel in self.channels:
            self.join(channel)

    def join(self, channel):
        if self.registered:
            # send join event
            self.irc.join(channel)
            # tell the ident module we joined this channel
            self.ident.join_channel(channel)
            if not(channel in self.channels):
                self.channels.append(channel)
        else:
            self.channels.append(channel)

    def reconnect(self, source, event, args, message):
        '''
        Handles disconnection by trying to reconnect the configured number of times
        before quitting
        '''
        # if we have been kicked, don"t attempt a reconnect
        # TODO : rejoin channels we were supposed to be in
        if event == nu.BOT_KILL:
            self.log.info("No reconnection attempt due to being killed")
            self.close()

        self.log.error("Lost connection to server:{0}".format(message))
        if self.times_reconnected >= self.max_reconnects:
            self.log.error("Unable to reconnect to server on third attempt")
            self.close()

        else:
            self.log.info(
                u"Sleeping before reconnection attempt, {0} seconds".format((self.times_reconnected + 1) * 60)
            )
            time.sleep((self.times_reconnected + 1) * 60)
            self.registered = False
            self.times_reconnected += 1
            self.log.info(u"Attempting reconnection, attempt no: {0}".format(self.times_reconnected))
            # set up events to connect and send USER and NICK commands
            self.irc.connect(self.network, self.port)
            self.irc.user(self.nick, self.realname)
            self.irc.nick(self.nick)

    def ping(self, source, action, args, message):
        self.irc.pong(message)

if __name__ == '__main__':
    bot = CommandBot()
    bot.join('#bots')
    bot.loop()
