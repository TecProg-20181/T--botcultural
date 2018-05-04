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


class HandleTasks(BotCultural):

    def __init__(self):
        BotCultural.__init__(self)

    def handle_updates(self, updates):
        """
        Loop with all the functios of the bot can do
        """
        for update in updates["result"]:
            if 'message' in update:
                message = update['message']
            elif 'edited_message' in update:
                message = update['edited_message']
            else:
                print('Can\'t process! {}'.format(update))
                return

            command = message["text"].split(" ", 1)[0]
            msg = ''
            if len(message["text"].split(" ", 1)) > 1:
                msg = message["text"].split(" ", 1)[1].strip()

            chat = message["chat"]["id"]

            print(command, msg, chat)

            if command == '/new':
                task = Task(chat=chat, name=msg, status='TODO', dependencies='', parents='', priority='')
                db.session.add(task)
                db.session.commit()
                self.send_message("New task *TODO* [[{}]] {}".format(task.id, task.name), chat)

            elif command == '/rename':
                text = ''
                if msg != '':
                    if len(msg.split(' ', 1)) > 1:
                        text = msg.split(' ', 1)[1]
                    msg = msg.split(' ', 1)[0]

                if not msg.isdigit():
                    self.send_message("You must inform the task id", chat)
                else:
                    task_id = int(msg)
                    query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                    try:
                        task = query.one()
                    except sqlalchemy.orm.exc.NoResultFound:
                        self.send_message("_404_ Task {} not found x.x".format(task_id), chat)
                        return

                    if text == '':
                        self.send_message("You want to modify task {}, but you didn't provide any new text".format(task_id), chat)
                        return

                    old_text = task.name
                    task.name = text
                    db.session.commit()
                    self.send_message("Task {} redefined from {} to {}".format(task_id, old_text, text), chat)
            elif command == '/duplicate':
                if not msg.isdigit():
                    self.send_message("You must inform the task id", chat)
                else:
                    task_id = int(msg)
                    query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                    try:
                        task = query.one()
                    except sqlalchemy.orm.exc.NoResultFound:
                        self.send_message("_404_ Task {} not found x.x".format(task_id), chat)
                        return

                    dtask = Task(chat=task.chat, name=task.name, status=task.status, dependencies=task.dependencies,
                                 parents=task.parents, priority=task.priority, duedate=task.duedate)
                    db.session.add(dtask)

                    for t in task.dependencies.split(',')[:-1]:
                        qy = db.session.query(Task).filter_by(id=int(t), chat=chat)
                        t = qy.one()
                        t.parents += '{},'.format(dtask.id)

                    db.session.commit()
                    self.send_message("New task *TODO* [[{}]] {}".format(dtask.id, dtask.name), chat)

            elif command == '/delete':
                if not msg.isdigit():
                    self.send_message("You must inform the task id", chat)
                else:
                    task_id = int(msg)
                    query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                    try:
                        task = query.one()
                    except sqlalchemy.orm.exc.NoResultFound:
                        self.send_message("_404_ Task {} not found x.x".format(task_id), chat)
                        return
                    for t in task.dependencies.split(',')[:-1]:
                        qy = db.session.query(Task).filter_by(id=int(t), chat=chat)
                        t = qy.one()
                        t.parents = t.parents.replace('{},'.format(task.id), '')
                    db.session.delete(task)
                    db.session.commit()
                    self.send_message("Task [[{}]] deleted".format(task_id), chat)

            elif command == '/todo':
                if not msg.isdigit():
                    self.send_message("You must inform the task id", chat)
                else:
                    task_id = int(msg)
                    query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                    try:
                        task = query.one()
                    except sqlalchemy.orm.exc.NoResultFound:
                        self.send_message("_404_ Task {} not found x.x".format(task_id), chat)
                        return
                    task.status = 'TODO'
                    db.session.commit()
                    self.send_message("*TODO* task [[{}]] {}".format(task.id, task.name), chat)

            elif command == '/doing':
                if not msg.isdigit():
                    self.send_message("You must inform the task id", chat)
                else:
                    task_id = int(msg)
                    query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                    try:
                        task = query.one()
                    except sqlalchemy.orm.exc.NoResultFound:
                        self.send_message("_404_ Task {} not found x.x".format(task_id), chat)
                        return
                    task.status = 'DOING'
                    db.session.commit()
                    self.send_message("*DOING* task [[{}]] {}".format(task.id, task.name), chat)

            elif command == '/done':
                if not msg.isdigit():
                    self.send_message("You must inform the task id", chat)
                else:
                    task_id = int(msg)
                    query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                    try:
                        task = query.one()
                    except sqlalchemy.orm.exc.NoResultFound:
                        self.send_message("_404_ Task {} not found x.x".format(task_id), chat)
                        return
                    task.status = 'DONE'
                    db.session.commit()
                    self.send_message("*DONE* task [[{}]] {}".format(task.id, task.name), chat)

            elif command == '/list':
                a = ''

                a += '\U0001F4CB Task List\n'
                query = db.session.query(Task).filter_by(parents='', chat=chat).order_by(Task.id)
                for task in query.all():
                    icon = '\U0001F195'
                    if task.status == 'DOING':
                        icon = '\U000023FA'
                    elif task.status == 'DONE':
                        icon = '\U00002611'

                    a += '[[{}]] {} {} - {}\n'.format(task.id, icon, task.name, task.priority)
                    a += self.deps_text(task, chat)

                self.send_message(a, chat)
                a = ''

                a += '\U0001F4DD _Status_\n'
                query = db.session.query(Task).filter_by(status='TODO', chat=chat).order_by(Task.id)
                a += '\n\U0001F195 *TODO*\n'
                for task in query.all():
                    a += '[[{}]] {}\n'.format(task.id, task.name)
                query = db.session.query(Task).filter_by(status='DOING', chat=chat).order_by(Task.id)
                a += '\n\U000023FA *DOING*\n'
                for task in query.all():
                    a += '[[{}]] {}\n'.format(task.id, task.name)
                query = db.session.query(Task).filter_by(status='DONE', chat=chat).order_by(Task.id)
                a += '\n\U00002611 *DONE*\n'
                for task in query.all():
                    a += '[[{}]] {}\n'.format(task.id, task.name)

                self.send_message(a, chat)
            elif command == '/dependson':
                text = ''
                if msg != '':
                    if len(msg.split(' ', 1)) > 1:
                        text = msg.split(' ', 1)[1]
                    msg = msg.split(' ', 1)[0]

                if not msg.isdigit():
                    self.send_message("You must inform the task id", chat)
                else:
                    task_id = int(msg)
                    query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                    try:
                        task = query.one()
                    except sqlalchemy.orm.exc.NoResultFound:
                        self.send_message("_404_ Task {} not found x.x".format(task_id), chat)
                        return

                    if text == '':
                        for i in task.dependencies.split(',')[:-1]:
                            i = int(i)
                            q = db.session.query(Task).filter_by(id=i, chat=chat)
                            t = q.one()
                            t.parents = t.parents.replace('{},'.format(task.id), '')

                        task.dependencies = ''
                        self.send_message("Dependencies removed from task {}".format(task_id), chat)
                    else:
                        for depid in text.split(' '):
                            if not depid.isdigit():
                                self.send_message("All dependencies ids must be numeric, and not {}".format(depid), chat)
                            else:
                                depid = int(depid)
                                query = db.session.query(Task).filter_by(id=depid, chat=chat)
                                try:
                                    taskdep = query.one()
                                    taskdep.parents += str(task.id) + ','
                                except sqlalchemy.orm.exc.NoResultFound:
                                    self.send_message("_404_ Task {} not found x.x".format(depid), chat)
                                    continue

                                deplist = task.dependencies.split(',')
                                if str(depid) not in deplist:
                                    task.dependencies += str(depid) + ','

                    db.session.commit()
                    self.send_message("Task {} dependencies up to date".format(task_id), chat)
            elif command == '/priority':
                text = ''
                if msg != '':
                    if len(msg.split(' ', 1)) > 1:
                        text = msg.split(' ', 1)[1]
                    msg = msg.split(' ', 1)[0]

                if not msg.isdigit():
                    self.send_message("You must inform the task id", chat)
                else:
                    task_id = int(msg)
                    query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                    try:
                        task = query.one()
                    except sqlalchemy.orm.exc.NoResultFound:
                        self.send_message("_404_ Task {} not found x.x".format(task_id), chat)
                        return

                    if text == '':
                        task.priority = ''
                        self.send_message("_Cleared_ all priorities from task {}".format(task_id), chat)
                    else:
                        if text.lower() not in ['high', 'medium', 'low']:
                            self.send_message("The priority *must be* one of the following: high, medium, low", chat)
                        else:
                            task.priority = text.lower()
                            self.send_message("*Task {}* priority has priority *{}*".format(task_id, text.lower()), chat)
                    db.session.commit()

            elif command == '/showpriority':
                priority_list = ''
                high_list = ''
                medium_list = ''
                low_list = ''
                undefined_priority = '\U0001F914 Tasks whithout priority\n'

                priority_list += '\n\n\U0001F4CB * Task List order by priority *\n'
                query = db.session.query(Task).filter_by(parents='', chat=chat).order_by(Task.priority)
                for task in query.all():
                    icon = '\U0001F195'
                    if task.status == 'DOING':
                        icon = '\U000023FA'
                    elif task.status == 'DONE':
                        icon = '\U00002611'

                    if task.priority == 'high':
                        high_list += '\U0001F4D5 * {} *- {} {}\n'.format(task.priority, task.name, icon)
                    elif task.priority == 'medium':
                        medium_list += '\U0001F4D9 * {} *- {} {}\n'.format(task.priority, task.name, icon)
                    elif task.priority == 'low':
                        low_list += '\U0001F4D7 * {} *- {} {}\n'.format(task.priority, task.name, icon)
                    else:
                        undefined_priority += '\U00002753 {} {}\n'.format(task.name, icon)

                priority_list += high_list + medium_list + low_list + '\n' + undefined_priority
                self.send_message(priority_list, chat)

            elif command == '/start':
                self.send_message("Welcome! Here is a list of things you can do.", chat)
                self.send_message(self.HELP, chat)
            elif command == '/help':
                self.send_message("Here is a list of things you can do.", chat)
                self.send_message(self.HELP, chat)
            else:
                self.send_message("I'm sorry dave. I'm afraid I can't do that.", chat)
