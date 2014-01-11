import logging
from collections import defaultdict
import numerics as nu
import event_util as eu

class IdentHost:
    def __init__(self, bot, module_name='identhost', log_level = logging.INFO):
        self.bot = bot
        self.log = logging.getLogger('{0}.{1}'.format(bot.log_name, module_name))
        self.log.setLevel(log_level)
        self.irc = bot.irc
        self.module_name = module_name
        self.channels = []
        self.nickmap = defaultdict(list)
        self.hostmap = defaultdict(list)
        self.channel2nick = defaultdict(list)
        self.nick2channel = defaultdict(list)
        self.commands = [
                        self.bot.command('!nick (?P<nick>.*)', self.find_nick),
                        self.bot.command('!nickhost (?P<nickhost>.*)', self.find_nick_host),
                        self.bot.command('!users (?P<chan>.*)', self.find_users_in_channel),
                        self.bot.command('!channels (?P<nick>.*)', self.find_channels_user_in),
                        ]
        self.events =   [
                        eu.event(nu.BOT_JOIN, self.user_join),
                        eu.event(nu.BOT_PART, self.user_part),
                        eu.event(nu.RPL_WHOREPLY, self.users_who),
                        eu.event(nu.BOT_QUIT, self.user_quit),
                        ]
        self.bot.add_module(module_name, self)
    
    def find_nick(self, nick, nickhost, action, targets, message, m):
        nick = m.group('nick')
        result = self.user_of_nick(nick)
        if self.is_user_in_channel(result, targets[0]):
            self.irc.msg_all(result, targets)
        else:
            self.irc.msg_all('user not in this channel', targets)

    def find_nick_host(self, nick, nickhost, action, targets, message, m):
        nickhost = m.group('nickhost')
        result = self.user_of_nick(nickhost)
        self.irc_msg_all(result, targets)

    def find_users_in_channel(self, nick, nickhost, action, targets, message, m):
        chan = m.group('chan')
        result = self.users_in_channel(chan)
        self.irc.msg_all(','.join(result), targets)
    
    def find_channels_user_in(self, nick, nickhost, action, targets, message, m):
        nick = m.group('nick')
        user = self.user_of_nick(nick)
        channels = self.channels_user_in(user)
        self.irc.msg_all(','.join(channels), targets)

    def is_user(self, user):
        '''
        return true if there are mappings already present for this nickhost
        otherwise false
        '''
        return self.hostmap[user]

    def add_user(self, nick, user, channel):
        '''
        Add user and first channel mapping
        '''
        #store mapping between nick and user
        self.nickmap[nick] = user
        self.hostmap[user] = nick
        if not self.is_user_in_channel(user, channel):
            self.channel2nick[channel].append(user)
            self.nick2channel[user].append(channel)

    def delete_user(self, user):
        '''
        Remove all channel and nick mappings
        for this user
        '''
        #remove appropriate mappings
        del self.nickmap[nick]
        del self.hostmap[user]
        for channel in self.nick2channel[user]:
            self.channel2nick[channel].remove(user)
        
        del self.nick2channel[user]

    def remove_user_from_channel(self, user, channel):
        '''
        Unmap user from this channel
        '''
        self.channel2nick[channel].remove(user)
        self.nick2channel[user].remove(channel)

    def add_user_to_channel(self, user, channel):
        '''
        Map user to this channel
        '''
        if not self.is_user_in_channel(user, channel):
            self.channel2nick[channel].append(user)
            self.nick2channel[user].append(channel)

    def is_user_in_channel(self, user, channel):
        '''
        Returns true if the user is in that channel
        '''
        return channel in self.nick2channel[user]

    def channels_user_in(self, user):
        '''
        Return list of all channels this user is in
        '''
        return self.nick2channel[user]

    def users_in_channel(self, channel):
        '''
        Return list of all users in a channel
        '''
        return self.channel2nick[channel]

    def in_channel(self, channel):
        '''
        Return true if the bot is in this channel
        '''
        return channel in self.channels

    def channels_bot_in(self, channels):
        '''
        Return list of channels the bot is in
        '''
        return self.channels

    def add_channel(self, channel):
        '''
        Add channel to list of channels bot is in
        '''
        self.channels.append(channel)

    def remove_channel(self, channel):
        '''
        Remove channel from list of channels bot is in
        '''
        self.channels.remove[channel]

    def user_nick(self, user):
        '''
        return the nick this user is using right now
        '''
        return self.hostmap[user]

    def user_of_nick(self, nick):
        '''
        Return the person using this nick
        '''
        return self.nickmap[nick]

    def user_join(self, command, prefix, params, postfix):
        '''
        A new user has joined a channel, store their hostname - nick mapping in the appropriate location
        '''
        nick, nickhost = prefix.split('!')
        channel = postfix
        self.log.debug(u'User {0} joined channel {1} with nick {2}'.format(nickhost, channel, nick))
        if self.is_user(nickhost):
            self.add_user_to_channel(nickhost, channel)
        else:
            self.add_user(nick, nickhost, channel)

    def user_quit(self, command, prefix, params, postfix):
        '''
        User quit server, remove all mappings
        '''
        nick, nickhost = prefix.split('!')
        self.log.debug(u'User {0} quit, deleted all mappings'.format(nickhost))
        self.delete_user(nickhost)

    def user_part(self, command, prefix, params, postfix):
        '''
        User parted a channel, remove that channel from their channel list
        '''
        nick, nickhost = prefix.split('!')
        channel = params[0]
        self.log.debug(u'User {0} left channel {1}'.format(nickhost, channel))

        if self.is_user_in_channel(nickhost, channel):
            self.remove_user_from_channel(nickhost, channel)
        else:
            self.log.warning(u'User {0} left channel {1} but was not mapped'.format(nickhost, channel))

    def user_msg(self, command, prefix, params, postfix):
        '''
        A user sent the channel a message, use this to help keep our mappings up to date
        '''
        nick, nickhost = prefix.split('!')
        channel = params[0]
        if self.is_user_in_channel(nickhost, channel):
            #no need to update
            pass
        else:
            self.add_user(nick, nickhost, channel)
            self.log.warning(u'User {0} talked in channel {1} as {2} but was not mapped'.format(nickhost, channel, nick))

    def part_channel(self, channel):
        '''
        we just left this channel, nuke the mappings
        '''
        if self.in_channel(channel):
            self.remove_channel(channel)
        else:
            self.log.warning(u'Just left channel {0} but was never marked as in it'.format(channel))

    def join_channel(self, channel):
        '''
        We just joined a channel, deal with the list of users we are getting
        '''
        self.add_channel(channel)
        self.irc.who(channel)#WE'RE GETTING THE NAMES MAN
        pass

    def users_who(self, command, prefix, params, postfix):
        '''
        Deal with the results of a WHO message to a channel we just joined
        This is because users with +i will not show up when joining a channel
        only when you send an explicit who
        '''
        nick = params[5]
        channel = params[1]
        nickhost = '{0}@{1}'.format(params[2], params[3])
        if not self.is_user(nickhost):
            self.add_user(nick, nickhost, channel)
        else:
            self.add_user_to_channel(nickhost, channel)