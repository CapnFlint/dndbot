import logging
import socket
import re
import sys

from config.config import config
from config.strings import strings

import utils.dndbeyond as dnd

class ConnectionManager():

    def __init__(self, bot, channel):
        self.bot = bot
        self.HOST = "irc.chat.twitch.tv"
        self.PORT = 6667
        self.CHAN = "#" + channel.lower()
        self.sock = None
        self.bot.running = False

# -----[ Initialization Functions ]---------------------------------------------

# -----[ Message Function ]-----------------------------------------------------

    def send_message(self, msg):
            self._send_emote(msg)

# -----[ Utility Functions ]----------------------------------------------------



# -----[ IRC message functions ]------------------------------------------------

    def _connect(self):
        self.sock = socket.socket()
        self.sock.connect((config['irc']['HOST'], config['irc']['PORT']))
        self.sock.sendall(('PASS %s\r\n' % config['irc']['PASS']).encode('utf-8'))
        self.sock.sendall(('NICK %s\r\n' % config['irc']['NICK']).encode('utf-8'))
        self.sock.sendall(('JOIN %s\r\n' % self.CHAN).encode('utf-8'))

        logging.info("Connected!")

    def _request_capabilities(self):
        # Request capabilities
        self.sock.sendall('CAP REQ :twitch.tv/membership\r\n'.encode('utf-8'))
        self.sock.sendall('CAP REQ :twitch.tv/tags\r\n'.encode('utf-8'))
        self.sock.sendall('CAP REQ :twitch.tv/commands\r\n'.encode('utf-8'))

    def _send_pong(self, msg):
        self.sock.sendall(('PONG %s\r\n' % msg).encode('utf-8'))

    def _send_message(self, msg, chan=None):
        if not chan:
            chan = self.CHAN
        logging.debug('PRIVMSG %s :%s\r\n' % (chan, msg))
        self.sock.sendall(('PRIVMSG %s :%s\r\n' % (chan, msg)).encode('utf-8'))

    def _send_emote(self, msg, chan=None):
        if not chan:
            chan = self.CHAN
        emote = '\001ACTION ' + msg + '\001'
        self._send_message(emote, chan)

    def _part_channel(self, chan=None):
        if not chan:
            chan = self.CHAN
        self.sock.sendall(('PART %s\r\n' % chan).encode('utf-8'))

    def _set_color(self):
        self._send_message('DnD Beyond Bot Initialized...')
        self._send_message('.color GoldenRod')

#-------------------------------------------------------------------------------

# -----[ Handle Joins/Parts/Modes ]---------------------------------------------

    def _handle_join(self, user):
        pass

    def _handle_part(self, user):
        pass

    def _handle_mode(self, user):
        logging.debug(user + " is a mod!")

    def _handle_notify(self, msg):
        pass

    def _handle_usernotice(self, tags):
        pass
# ------------------------------------------------------------------------------

# -----[ IRC Utility Functions ]------------------------------------------------

    def _parse_message(self, message):
        msg = {}

        msg["sender"] = re.match(':(.*)!', message[1]).group(1).encode('utf-8')
        msg["text"] = " ".join(message[4:]).lstrip(":")
        msg['channel'] = message[3]
        msg['tags'] = self._get_tags(message[0])
        msg["sender_id"] = msg['tags']['user-id']
        msg['emotes'] = self._get_emotes(msg['tags'])
        msg['perms'] = self._get_perms(msg['tags'])

        if msg['sender'] == 'capn_flint':
            msg['perms']['mod'] = True

        return msg

    def _get_sender(self, msg):
        result = ""
        for char in msg:
            if char == "!":
                break
            if char != ":":
                result += char
        result = result.encode('utf-8')
        return result

    def _get_tags(self, data):
        data = data.split(';')
        tagmap = {}
        for d in data:
            (key, val) = d.split('=')
            tagmap[key] = val
        return tagmap

    def _get_perms(self, tags):
        '''
        '@color=#5F9EA0;display-name=mr_5ka;emotes=81530:0-7,9-16,18-25;mod=0;room-id=91580306;subscriber=1;turbo=0;user-id=69442368;user-type='
        '''

        perm = {}
        perm['mod'] = bool(int(tags['mod']))
        perm['sub'] = bool(int(tags['subscriber']))

        return perm

    def _get_emotes(self, tags):
        '''
        '@color=#5F9EA0;display-name=mr_5ka;emotes=81530:0-7,9-16,18-25;mod=0;room-id=91580306;subscriber=1;turbo=0;user-id=69442368;user-type='
        data[3] = emotes

        link: https://static-cdn.jtvnw.net/emoticons/v1/81530/2.0

        TODO: Make this more generic (search for the mod and subscriber parameters)
        '''

        emotes = {}
        emotelist = tags['emotes']
        if emotelist:
            data = emotelist.split('/')
            for block in data:
                tmp = block.split(':')
                em_id = tmp[0]
                em_cnt = len(tmp[1].split(','))
                emotes[em_id] = em_cnt

        return emotes

# ------------------------------------------------------------------------------

    def connect(self):
        self._connect()
        self._request_capabilities()

        self._set_color()

        logging.info("Connected...")

        data = ""

        self.bot.running = True

        try:
            while self.bot.running:
                try:
                    data = data + self.sock.recv(1024).decode('utf-8')
                    data_split = re.split("[\r\n]+", data)
                    data = data_split.pop()

                    for line in data_split:
                        line = str.rstrip(line)
                        line = str.split(line)

                        if len(line) >= 1:
                            if line[0] == 'PING':
                                self._send_pong(line[1])

                            elif line[2] == 'PRIVMSG':
                                msg = self._parse_message(line)

                                if msg['emotes']:
                                    emoteList = []
                                    for emote in msg['emotes'].keys():
                                        for i in range(msg['emotes'][emote]):
                                            emoteList.append(emote)

                                if msg['channel'] == self.CHAN:
                                    if msg['text'].startswith('!'):
                                        self.bot.msgProc.parse_command(msg)
                                    else:
                                        self.bot.msgProc.parse_message(msg)
                                else:
                                    logging.error("This shouldn't happen! (Raid?)")

                            elif line[2] == 'USERNOTICE':
                                self._handle_usernotice(self._get_tags(line[0]))

                            elif line[2] == 'CLEARCHAT':
                                '''
                                @ban-duration=10;ban-reason=Links,\sautomated\sby\sMoobot.;room-id=22552479;target-user-id=46084149;tmi-sent-ts=1511037298789 :tmi.twitch.tv CLEARCHAT #giantwaffle :jimjerejim
                                '''
                                pass

                            elif line[1] == 'JOIN':
                                joiner = self._get_sender(line[0])
                                if(joiner):
                                    self._handle_join(joiner)

                            elif line[1] == 'PART':
                                leaver = self._get_sender(line[0])
                                if(leaver):
                                    self._handle_part(leaver)

                            elif line[1] == 'MODE':
                                self._handle_mode(line[4])

                            else:
                                logging.warning(" ".join(["Unhandled:"]+line))

                except socket.error:
                    logging.error("Socket died: ", sys.exc_info()[0])
                    self.bot.running = False

                except socket.timeout:
                    logging.error("Socket timeout")
                    self.bot.running = False
        except:
            logging.error("Unhandled Error: ", sys.exc_info()[0])
            self.bot.running = False
            self.bot.restart = False
        # Clean up
        #self._part_channel(self.CHAN)
