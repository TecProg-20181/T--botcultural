import os
import time
from urlhandler import UrlHandler
from chatbot import ChatBot
from botmanager import BotManager
import config 

TOKEN = config.TOKEN


def main():
    """get updates continuosly and manage instructions"""
    last_update_id = None
    chat_bot = ChatBot.chat_bot_start()
    url_handler = UrlHandler()
    bot_manager = BotManager()

    while True:
        print("Updates")
        updates = url_handler.get_updates(last_update_id)

        if updates["result"]:
            last_update_id = url_handler.get_last_update_id(updates) + 1
            bot_manager.handle_updates(updates, chat_bot)

        time.sleep(0.5)


if __name__ == '__main__':
    main()
