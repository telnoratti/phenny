#!/usr/bin/env python
"""
irc.py - A Utility IRC Bot
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

Rewritten to use twisted by mutantmonkey
on 2011-09-21.

http://inamidst.com/phenny/
"""

import sys, re, time, traceback

from twisted.words.protocols import irc
from twisted.internet import ssl, reactor, protocol


class Origin(object):
    source = re.compile(r'([^!]*)!?([^@]*)@?(.*)')

    def __init__(self, bot, source, args):
        match = Origin.source.match(source or '')
        self.nick, self.user, self.host = match.groups()

        if len(args) > 1: 
            target = args[1]
        else:
            target = None

        mappings = {bot.nick: self.nick, None: None}
        self.sender = mappings.get(target, target)


class TwistedBot(irc.IRCClient): 
    def __init__(self, nick, user, name, channels, password=None):
        self.nickname = nick
        self.username = user
        self.realname = name
        self.password = password
        self.channels = channels or []

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

    def connectionLost(self):
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        for channel in self.channels:
            self.join(channel)


class BotFactory(protocol.ClientFactory):
    def __init__(self, nick, user, name, channels, password=None):
        self.nick = nick
        self.user = user
        self.name = name
        self.password = password
        self.channels = channels or []

    def clientConnectionLost(self, connector, reason):
        """Reconnect to server if we get disconnected."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        reactor.stop()


class Bot(irc.IRCClient):
    def __init__(self, nick, name, channels, password=None):
        self.nickname = nick
        self.username = nick
        self.realname = name
        self.password = password
        self.channels = channels or []

        self.nick = nick
        self.user = nick
        self.name = name
        self.verbose = True
        self.stack = []

        import threading
        self.sending = threading.RLock()

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        for channel in self.channels:
            self.join(channel)

    def privmsg(self, user, channel, text):
        args = ['PRIVMSG', channel]
        origin = Origin(self, user, args)
        self.dispatch(origin, tuple([text] + args))

    def dispatch(self, origin, args):
        pass

    def channel_output(self, method, recipient, text):
        self.sending.acquire()

        # Cf. http://swhack.com/logs/2006-03-01#T19-43-25
        if isinstance(text, unicode): 
            try:
                text = text.encode('utf-8')
            except UnicodeEncodeError, e: 
                text = e.__class__ + ': ' + str(e)
        if isinstance(recipient, unicode): 
            try:
                recipient = recipient.encode('utf-8')
            except UnicodeEncodeError, e: 
                return

        # No messages within the last 3 seconds? Go ahead!
        # Otherwise, wait so it's been at least 0.8 seconds + penalty
        if self.stack: 
            elapsed = time.time() - self.stack[-1][0]
            if elapsed < 3: 
                penalty = float(max(0, len(text) - 50)) / 70
                wait = 0.8 + penalty
                if elapsed < wait: 
                    time.sleep(wait - elapsed)

        # Loop detection
        messages = [m[1] for m in self.stack[-8:]]
        if messages.count(text) >= 5: 
            text = '...'
            if messages.count('...') >= 3: 
                self.sending.release()
                return

        def safe(input): 
            input = input.replace('\n', '')
            return input.replace('\r', '')
        method(safe(recipient), safe(text)[:512])
        self.stack.append((time.time(), text))
        self.stack = self.stack[-10:]

        self.sending.release()

    def msg(self, recipient, text): 
        self.channel_output(self.sendmsg, recipient, text)

    def sendmsg(self, recipient, text):
        return irc.IRCClient.msg(self, recipient, text)

    def action(self, recipient, text, data=None):
        # deal with twisted method conflict
        if data:
            args = ['ACTION', text]
            origin = Origin(self, recipient, args)
            self.dispatch(origin, tuple([data] + args))
        else:
            self.channel_output(self.describe, recipient, text)

    def error(self, origin): 
        try: 
            import traceback
            trace = traceback.format_exc()
            print trace
            lines = list(reversed(trace.splitlines()))

            report = [lines[0].strip()]
            for line in lines: 
                line = line.strip()
                if line.startswith('File "/'): 
                    report.append(line[0].lower() + line[1:])
                    break
            else:
                report.append('source unknown')

            self.msg(origin.sender, report[0] + ' (' + report[1] + ')')
        except:
            self.msg(origin.sender, "Got an error.")


class TestBot(Bot): 
    def f_ping(self, origin, match, args): 
        delay = m.group(1)
        if delay is not None: 
            import time
            time.sleep(int(delay))
            self.msg(origin.sender, 'pong (%s)' % delay)
        else:
            self.msg(origin.sender, 'pong')
    f_ping.rule = r'^\.ping(?:[ \t]+(\d+))?$'


def main(): 
    print __doc__

if __name__ == "__main__": 
    main()
