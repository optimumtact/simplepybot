    def is_user(user):
        '''
        return true if there are mappings already present for this nickhost
        otherwise false
        '''
        return not empty(self.hostmap[user])

    def add_user(nick, user, channel):
        '''
        Add user and first channel mapping
        '''
        #store mapping between nick and user
        self.nickmap[nick] = user
        self.hostmap[user] = nick
              
        self.channel2nick[channel] = self.channel2nick[channel].insert(user)
        self.nick2channel[user] = self.nick2channel[user].insert(channel)

    def delete_user(user):
        '''
        Remove all channel and nick mappings
        for this user
        '''
        #remove appropriate mappings
        del self.nickmap[nick]
        del self.hostmap[user]
        for channel in self.nick2channel[user]:
            self.channel2nick[channel] = self.channel2nick[channel].remove(user)
        
        del self.nick2channel[user]

    def remove_user_from_channel(user, channel):
        '''
        Unmap user from this channel
        '''
        self.channel2nick[channel] = self.channel2nick[channel].remove(user)
        self.nick2channel[user] = self.nick2channel[user].remove(channel)

    def add_user_to_channel(user, channel):
        '''
        Map user to this channel
        '''
        self.channel2nick[channel] = self.channel2nick[channel].insert(user)
        self.nick2channel[user] = self.nick2channel[user].insert(channel)

    def is_user_in_channel(user, channel):
        '''
        Returns true if the user is in that channel
        '''
        return self.nick2channel[user].contains(channel)

    def channels_user_in(user):
        '''
        Return list of all channels this user is in
        '''
        return self.nick2channel[user]

    def users_in_channel(channel):
        '''
        Return list of all users in a channel
        '''
        return self.channel2nick[channel]

    def in_channel(channel):
        '''
        Return true if the bot is in this channel
        '''
        return self.channels.contains[channel]

    def channels_bot_in(channels):
        '''
        Return list of channels the bot is in
        '''
        return self.channels

    def add_channel(channel):
        '''
        Add channel to list of channels bot is in
        '''
        self.channels[channel]

    def remove_channel(channel):
        '''
        Remove channel from list of channels bot is in
        '''
        self.channels.remove[channel]

    def user_nick(user):
        '''
        return the nick this user is using right now
        '''
        return self.hostmap[user]

    def user_of_nick(nick):
        '''
        Return the person using this nick
        '''
        return self.nickmap[nick]

    def user_join(self, command, prefix, params, postfix):
        '''
        A new user has joined a channel, store their hostname - nick mapping in the appropriate location
        '''
        self.log.debug(u'User {0} joined channel {1} with nick {2}'.format(nickhost, channel, nick))
        nick, nickhost = prefix.split('!')
        channel = params[0]
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
        self.remove_user(nickhost)

    def user_part(self, command, prefix, params, postfix):
        '''
        User parted a channel, remove that channel from their channel list
        '''
        self.log.debug(u'User {0} left channel {1}'.format(nickhost, channel))
        nick, nickhost = prefix.split('!')
        channel = params[0]
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

    def join_channel(self, command, prefix, params, postfix):
        '''
        We just joined a channel, deal with the list of users we are getting
        '''
        self.add_channel(channel)
        #TODO get format of what it looks like when joining and parse
        #Plus send a who command to that channel to get users with +i
        pass

    def users_who(self, command, prefix, params, postfix):
        '''
        Deal with the results of a WHO message to a channel we just joined
        This is because users with +i will not show up when joining a channel
        only when you send an explicit who
        '''
        pass