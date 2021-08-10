import logging

#from modules.commands.helper import *
#from modules.commands import *

#import core.command_buffer as cmd_buffer

from config.strings import strings

class MessageProcessor():

    def __init__(self, bot):
        self.bot = bot
        self.connMgr = bot.connMgr

        self.session_running = False

        self.msghooks = []

    def add_custom_command(self, command, message):
        pass

    def remove_custom_command(self, command):
        pass

    def parse_command(self, msg):
        pass


    def parse_message(self, msg): #, sender, perms, emotes):
        # Do any normal message parsing we need here, e.g. spam/banned word checks

        for f in self.msghooks:
            f(self, msg)

    def register_hook(self, func):
        logging.debug("Registering hook: " + func.__name__)
        self.msghooks.append(func)



# -----[ Command Functions ]----------------------------------------------------

    def run_command(self, cmd, data = {}):
        pass

