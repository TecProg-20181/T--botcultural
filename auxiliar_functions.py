import json
import requests
import time
import urllib

import sqlalchemy

import db
from db import Task

import config


class BotCultural():
    def __init__(self):
        self.URL = "https://api.telegram.org/bot{}/".format(config.TOKEN)
        self.HELP = (
                "/new NOME\n"
                "/todo ID\n"
                "/doing ID\n"
                "/done ID\n"
                "/delete ID\n"
                "/rename ID NOME\n"
                "/dependson ID ID...\n"
                "/duplicate ID\n"
                "/priority ID PRIORITY{low, medium, high}\n"
                "/duedate ID DATE{dd/mm/aaaa}\n"
                "/list\n"
                "/help\n"
            )
    def get_url(self, url):
        """
        Return the especific url
        """
        response = requests.get(url)
        content = response.content.decode("utf8")
        return content

    def get_json_from_url(self, url):
        """
        Return json from especific url
        """
        content = self.get_url(url)
        js = json.loads(content)
        return js

    def get_updates(self, offset=None):
        """
        Return updates from bot with timeout of 100ms
        """
        url = self.URL + "getUpdates?timeout=100"
        if offset:
            url += "&offset={}".format(offset)
        js = self.get_json_from_url(url)
        return js

    def send_message(self, text, chat_id, reply_markup=None):
        """
        Return messages that shows to user
        """
        text = urllib.parse.quote_plus(text)
        url = self.URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
        if reply_markup:
            url += "&reply_markup={}".format(reply_markup)
        self.get_url(url)

    def get_last_update_id(self, updates):
        """
        Get the last id of update
        """
        update_ids = []
        for update in updates["result"]:
            update_ids.append(int(update["update_id"]))

        return max(update_ids)

    def deps_text(self, task, chat, preceed=''):
        """
        Return texts to taks with deppendecies
        """
        text = ''

        for i in range(len(task.dependencies.split(',')[:-1])):
            line = preceed
            query = db.session.query(Task).filter_by(id=int(task.dependencies.split(',')[:-1][i]), chat=chat)
            dep = query.one()

            icon = '\U0001F195'
            if dep.status == 'DOING':
                icon = '\U000023FA'
            elif dep.status == 'DONE':
                icon = '\U00002611'

            if i + 1 == len(task.dependencies.split(',')[:-1]):
                line += '└── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
                line += self.deps_text(dep, chat, preceed + '    ')
            else:
                line += '├── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
                line += self.deps_text(dep, chat, preceed + '│   ')

            text += line

        return text
