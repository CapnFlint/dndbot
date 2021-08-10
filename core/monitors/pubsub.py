import logging
import websocket
import threading
import time
import json
import ssl
import requests

from config.config import config

import utils.dndbeyond as dnd_utils


class pubsub():

    def __init__(self, bot=None, host=""):
        self.bot = bot
        self.HOST = host
        self.ws = None
        self.ping_ok = True

    # send PING
    def _ping(self):
        # Send a ping Message
        logging.debug("PING!!!")
        self.ping_ok = False
        msg = {
            "data":"ping"
        }
        self.ws.send(json.dumps(msg))

    def _pong(self):
        # Handle pong response
        logging.debug("PONG!!!")
        self.ping_ok = True


    # handle RESPONSE
    def _response(self, msg):
        logging.debug("Handling RESPONSE")
        if(msg["error"] != ""):
            logging.error("Error found: '%s'" % msg["error"])

    # handle RECONNECT
    def _reconnect(self):
        # Handle reconnect Messages
        self.ws.close()
        time.sleep(2)
        self.start()

    # handle Message
    def on_message(self, wsapp, message):
        if message == "pong":
            self._pong()
        else:
            msg = json.loads(message)
            data = {}
            if ('rolls' in msg['data']):
                roll = msg['data']['rolls'][0]
                if('result' in roll):
                    data['char'] = msg['data']['context']['name']
                    data['type'] = roll['rollType']
                    data['item'] = msg['data']['action']
                    data['result'] = roll['result']['total']
                    data['detail'] = roll['result']['text']
                    data['values'] = roll['result']['values']
                    logging.debug(data)
                    self.show_message(data)
            
    def show_message(self, data):
        msg = ""
        stats = {
            'int': 'Intelligence',
            'str': 'Strength',
            'dex': 'Dexterity',
            'con': 'Constitution',
            'wis': 'Wisdom',
            'cha': 'Charisma'
        }
        if data["type"] == "roll":
            msg = "{char} makes a {item} roll, and gets {result}! ({detail})"
        if data["type"] == "check":
            if data['item'] in stats:
                data['item'] = stats[data['item']]
            msg = "{char} attempts a {item} check, and rolls {result}! ({detail})"
        if data["type"] == "save":
            msg = "{char} attempts a {item} save, and gets {result}! ({detail})"
        if data["type"] == "to hit":
            if 20 in data['values']:
                msg = "{char} attacks with their {item}, and rolls {result}. It is a CRITICAL HIT!!! ({detail})"
            else:
                msg = "{char} attacks with their {item}, and rolls {result}! ({detail})"
        if data["type"] == "damage":
            msg = "{char}'s {item} hits for {result} damage! ({detail})"
        self.bot.connMgr.send_message(msg.format(**data))
        pass

    def on_error(self, wsapp, error):
        logging.error(error)
        self._reconnect()

    def on_close(self, wsapp, close_status_code, close_msg):
        logging.debug("### closed ### ")
        self._reconnect()

    def on_open(self, wsapp):
        logging.debug("on_open called")
        def run(*args):
            # ping!
            try:
                while(1):
                    self._ping()
                    time.sleep(10)
                    if(self.ping_ok == False):
                        logging.error("Ping failed, reconnecting!")
                        self._reconnect()
                    time.sleep(230)
            except WebSocketConnectionClosedException:
                logging.debug("Socket closed, restarting!")
                self._reconnect()
        threading.Thread(target=run).start()

    def _connect(self):
        logging.info("Connecting...")
        #websocket.enableTrace(True)
        auth_token = self._get_token()
        self.ws = websocket.WebSocketApp(config['dndbeyond']['websocket_url'] + auth_token,
                                    on_message = self.on_message,
                                    on_error = self.on_error,
                                    on_close = self.on_close)
        self.ws.on_open = self.on_open
        self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    def _get_token(self):
        url = config['dndbeyond']['token_url']
        cookie = {"CobaltSession": config['dndbeyond']['cobalt_cookie']}
        result = requests.post(url, cookies=cookie)
        token = json.loads(result.text)['token']
        return token

    def start(self):
        threading.Thread(target=self._connect).start()
