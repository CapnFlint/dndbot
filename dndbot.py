#!/usr/bin/env python3
import logging

logging.basicConfig(
    format='%(filename)s:%(lineno)d::%(levelname)s:: %(message)s',
    handlers=[
        logging.FileHandler("dndbot.log"),
        logging.StreamHandler()
    ],
    level=logging.DEBUG)

from core.connection_manager import ConnectionManager
from core.message_processor import MessageProcessor

from core.monitors.pubsub import pubsub

from config.config import config

class DnDBot():
    def __init__(self, channel):
        self.channel = channel
        self.running = False
        self.restart = True
        self.connMgr = ConnectionManager(self, channel)
        self.msgProc = MessageProcessor(self)

        self.pubsub = pubsub(self)

    def run(self):
        logging.info("starting up!")
        self.pubsub.start()
        self.connMgr.connect()

def main():
    bot = DnDBot(config['twitch']['channel'])
    bot.run()

if __name__ == "__main__":
    main()