import logging
from collections import defaultdict
import numerics as nu


class IdentHost:

    def __init__(self, bot, module_name='identhost', log_level=logging.INFO):
        self.bot = bot
        self.log = logging.getLogger(u'{0}.{1}'.format(bot.log_name, module_name))
        self.log.setLevel(log_level)
        self.irc = bot.irc
        self.module_name = module_name
        self.channels = []
        self.nickmap = defaultdict(str)
        self.hostmap = defaultdict(str)
        self.channel2user = defaultdict(list)
        self.user2channel = defaultdict(list)
        self.commands = []
        self.events = [
            bot.event(nu.BOT_JOIN, self.user_join),
            bot.event(nu.BOT_PART, self.user_part),
            bot.event(nu.RPL_WHOREPLY, self.users_who),
            bot.event(nu.BOT_QUIT, self.user_quit),
            bot.event(nu.BOT_NICK, self.user_changed_nick),
            bot.event(nu.BOT_ERR, self.reconnect),
            bot.event(nu.BOT_KILL, self.reconnect),
        ]
        self.bot.add_module(module_name, self)

    def is_user(self, user):
        '''
        return true if there are mappings already present for this nickhost
        otherwise false
        '''
        self.log.debug(u'Checked if user {0} is in my identity map'.format(user))
        return self.hostmap[user] != ''

    def add_user(self, nick, user, channel):
        '''
        Add user and first channel mapping
        '''
        # store mapping between nick and user
        self.nickmap[nick] = user
        self.hostmap[user] = nick
        self.log.debug(u'Adding user mapping {1}=>{0}'.format(user, nick, channel))
        if not self.is_user_in_channel(user, channel):
            self.log.debug(u'Adding user {0} to channel {1}'.format(user, channel))
            self.channel2user[channel].append(user)
            self.user2channel[user].append(channel)

    def delete_user(self, user):
        '''
        Remove all channel and nick mappings
        for this user
        '''
        # remove appropriate mappings
        del self.nickmap[nick]
        del self.hostmap[user]
        self.log.debug('Removing user mapping {1}=>{0}'.format(user, nick))
        for channel in self.user2channel[user]:
            self.log.debug(u'Removing {0} from channel {1}'.format(user, channel))
            self.channel2user[channel].remove(user)

        del self.user2channel[user]

    def change_user_nick(self, user, newnick):
        oldnick = self.nick_of_user(user)
        self.log.debug(u'Changing {0}=>{1} to {2}=>{1}'.format(oldnick, user, newnick))
        self.hostmap[user] = newnick
        del self.nickmap[oldnick]
        self.nickmap[newnick] = user

    def remove_user_from_channel(self, user, channel):
        '''
        Unmap user from this channel
        '''
        self.log.debug('Removing {0} from {1}'.format(user, channel))
        self.channel2user[channel].remove(user)
        self.user2channel[user].remove(channel)

    def add_user_to_channel(self, user, channel):
        '''
        Map user to this channel
        '''
        if not self.is_user_in_channel(user, channel):
            self.log.debug(u'Adding user {0} to {1}'.format(user, channel))
            self.channel2user[channel].append(user)
            self.user2channel[user].append(channel)

    def is_user_in_channel(self, user, channel):
        '''
        Returns true if the user is in that channel
        '''
        return channel in self.user2channel[user]

    def channels_user_in(self, user):
        '''
        Return list of all channels this user is in
        '''
        return self.user2channel[user]

    def users_in_channel(self, channel):
        '''
        Return list of all users in a channel
        '''
        return self.channel2user[channel]

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
        self.log.debug(u'Adding {0} to list of channels im in'.format(channel))
        self.channels.append(channel)

    def remove_channel(self, channel):
        '''
        Remove channel from list of channels bot is in
        '''
        self.log.debug(u'Removing {0} from list of channels im in'.format(channel))
        self.channels.remove[channel]

    def nick_of_user(self, user):
        '''
        return the nick this user is using right now
        '''
        return self.hostmap[user]

    def user_of_nick(self, nick):
        '''
        Return the person using this nick
        '''
        return self.nickmap[nick]

    '''
    Event handlers past this point
    '''

    def user_changed_nick(self, command, prefix, params, postfix):
        '''
        User changed their nick, update the mapping
        '''
        nick, nickhost = prefix.split('!')
        newnick = postfix
        self.log.debug(u'User {0} changed nick to {1}'.format(nickhost, newnick))
        self.change_user_nick(nickhost, newnick)

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
            # no need to update
            pass
        else:
            self.add_user(nick, nickhost, channel)
            self.log.warning(u'User {0} talked in channel {1} as {2} but was not mapped'.format(nickhost, channel, nick))

    def part_channel(self, channel):
        '''
        we just left this channel, nuke the mappings
        '''
        if self.in_channel(channel):
            self.log.debug(u'Parting channel {0}'.format(channel))
            self.remove_channel(channel)
            for user in self.channel2user:
                self.remove_user_from_channel(user, channel)
            del (self.channel2user[channel])
        else:
            self.log.warning(u'Just left channel {0} but was never marked as in it'.format(channel))

    def join_channel(self, channel):
        '''
        We just joined a channel, deal with the list of users we are getting
        '''
        self.log.debug(u'Joined channel {0}'.format(channel))
        self.add_channel(channel)
        self.irc.who(channel)
        pass

    def users_who(self, command, prefix, params, postfix):
        '''
        Deal with the results of a WHO message to a channel we just joined
        This is because users with +i will not show up when joining a channel
        only when you send an explicit who
        '''
        nick = params[2]
        channel = params[1]
        nickhost = '{0}@{1}'.format(params[2], params[3])
        self.log.debug(u'Who response from {0}=>{1}'.format(nick, nickhost))
        if not self.is_user(nickhost):
            self.add_user(nick, nickhost, channel)
        else:
            self.add_user_to_channel(nickhost, channel)

    def reconnect(self, command, prefix, params, postfix):
        '''
        Bot has disconnected, clear all mappings we previously
        knew about
        '''
        self.channels = []
        self.nickmap = defaultdict(str)
        self.hostmap = defaultdict(str)
        self.channel2user = defaultdict(list)
        self.user2channel = defaultdict(list)
