Simplepybot is an attempt at a dead simple python irc bot

python3 support is in testing on the py3support branch - at this stage things seem to work fine

There is a v0.1 tag that has more modules and works only on python2, it lacks some features such as identity mappings

In terms of a todo
* Add spam control - the bot should avoid sending too many messages (configurable, with sensible defaults) to a channel, and should auto ignore users who abuse it's functions. This will require tracking the "originator" of a command and also keep a count of outgoing messages in the past x minutes and qeueing messages as necessary

* Change permission system to use permissions instead of numbers (i.e) !grant permission [nick] module/permisson

* Introduce idea of a role, which is preconfigured with permission !grant role [nick] rolename

* Write a script that will autogenerate irc.py event_util.py and numerics.py from a json/txt file. This is all simply code that provides a wrapper over the event system simplepybot uses, it's entirely plausible that the bindings at each level can be programtically generated, preventing you having to write the same method basically twice

* Clean up logging, right now it's extremely spammy and I want to fix that by leaving most modules set on INFO and above level and only turn on DEBUG on modules that I am programming on explicitly

* Perhaps provide some worker thread system for long running module commands that don't need to reference the main bot or data

