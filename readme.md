Simplepybot is an attempt at a dead simple python irc bot that got way out of control

It is currently targeting python3 test

#Configuration
configuration is done by editing the basic.ini file, you can define more core and custom modules by adding them.

to allow a module to load the following settings *Must* be defined
```
class=Name of python class
filename = filename class lives in
modulename = what name the module should have
```
If you want to include the module as an accessible attribute on the bot object (much like the ircengine,identengine and authengine modules) then add
```
core = attributename
```
A module should pull all and any configuration from the config file, module creators are advised to do
```
self.config = bot.config[self.module_name]
```
aside from the predefined, class,filename,modulename attributes just about anything can be put in there, see the python configparser docs for more info

#Writing your own module
create a new class with an init that accepts the following
```
__init__(self, bot, module_name)
```
to do logging in your module setup a log like so
```
self.log = logging.getLogger(bot.log_name+'.'+module_name)
```
the end user will configure the log with the logging.json file, you may wish to provide a default/example config

you can get access to an sqlite db connection from bot.db, make sure you prefix the tables with your module_name, this makes it easier for an end user to reuse your module with others

finally, specify a set of command/event handlers on the commands attrib of your class
```
self.commands = [
    bot.command(r'regex expression', self.func),
    ...
]
self.events[
    bot.event(botflag, self.func),
    ...
]
```
see event_util for documentation on the event/command handlers, commands are for responding to user input and events are for hooking into real irc events (TODO write a nice version)

for the event botflags you can use any option from the numerics.py file, get them by adding the following import to your module
```
import numerics as nu
```
you can then reference it with
```
nu.PRIV_MSG
...
```

See modules/aliasmodule.py for a super simple example of a module



