Simplepybot is an attempt at a dead simple python irc bot

Right now it's written in python 2.7 but plans are in the works to port it to 3.x

Most of the modules are not up to date with the latest master and only the aliasbot is likely to work with it, as thats what I've been using for testing. Porting them shouldn't prove a huge hassle however. It's mainly making them use the bot.irc interface instead of the bot.x interface

You can check out the v0.1 tag for a reasonably stable version that most of the modules work with. It does lack some features though (threading, identity mappings)

In terms of a todo
* Write a script that will autogenerate irc.py event_util.py and numerics.py from a json/txt file. This is all simply code that provides a wrapper over the event system simplepybot uses, it's entirely plausible that the bindings at each level can be programtically generated, preventing you having to write the same method basically twice

* Hook authentication module into the new identity map, so you can always refer to users by nick and have it use their hostname transparently

* Clean up logging, right now it's extremely spammy and I want to fix that by leaving most modules set on INFO and above level and only turn on DEBUG on modules that I am programming on explicitly

* Clean up the modules to be in line with the new formats for bot work

* Perhaps provide some worker thread system for long running module commands that don't need to reference the main bot or data

* Other stuff I have written down but not included here
