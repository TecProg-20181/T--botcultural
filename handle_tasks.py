import json
import requests
import time
from datetime import date
import urllib

import sqlalchemy

import db
from db import Task

import config
import icons
from auxiliar_functions import BotCultural
from handle_issues import HandleIssues
from handle_urls import HandleUrls



class HandleTasks(BotCultural):

    def __init__(self):
        BotCultural.__init__(self)
        self.handle_issues = HandleIssues()
        self.handle_urls = HandleUrls()

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
                task_list = msg.split()
                print('msg: {} chat: {} list: {}'.format(msg, chat, task_list))
                for task in task_list:
                    task = task.strip()
                    task = Task(chat=chat, name=msg, status='TODO', dependencies='', parents='', priority='')
                    db.session.add(task)
                    db.session.commit()
                    self.send_message("New task *TODO* [[{}]] {}".format(task.id, task.name), chat)
            
            elif command == '/newIssue' or command == '/ni':
                self.handle_issues.new_issue(msg, chat)
            
            elif command == '/renameIssue' or command == '/ri':
                self.handle_issues.rename_issue(msg, chat)

            elif command == '/listIssues' or command == '/li':
                self.handle_issues.list_issues(chat)

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
                taskList= msg.split()
                for task in taskList:
                    task = task.strip()
                    if not task.isdigit():
                        self.send_message("You must inform the task id", chat)
                    else:
                        task_id = int(task)
                        query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                        try:
                            task_returned = query.one()
                        except sqlalchemy.orm.exc.NoResultFound:
                            self.send_message("_404_ Task {} not found x.x".format(task_id), chat)
                            return
                        task_returned.status = 'TODO'
                        db.session.commit()
                        self.send_message("*TODO* task [[{}]] {}".format(task_returned.id, task_returned.name), chat)

            elif command == '/doing':
                taskList = msg.split()
                for task in taskList:
                    task = task.strip()
                    if not task.isdigit():
                        self.send_message("You must inform the task id", chat)
                    else:
                        task_id = int(task)
                        query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                        try:
                            task_returned = query.one()
                        except sqlalchemy.orm.exc.NoResultFound:
                            self.send_message("_404_ Task {} not found x.x".format(task_id), chat)
                            return
                        task_returned.status = 'DOING'
                        db.session.commit()
                        self.send_message("*DOING* task [[{}]] {}".format(task_returned.id, task_returned.name), chat)

            elif command == '/done':
                taskList = msg.split()
                for task in taskList:
                    task = task.strip()
                    if not task.isdigit():
                        self.send_message("You must inform the task id", chat)
                    else:
                        task_id = int(task)
                        query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                        try:
                            task_returned = query.one()
                        except sqlalchemy.orm.exc.NoResultFound:
                            self.send_message("_404_ Task {} not found x.x".format(task_id), chat)
                            return
                        task_returned.status = 'DONE'
                        db.session.commit()
                        self.send_message("*DONE* task [[{}]] {}".format(task_returned.id, task_returned.name), chat)


            elif command == '/list':
                a = ''

                a += icons.LIST_ICON + ' Task List\n'
                query = db.session.query(Task).filter_by(parents='', chat=chat).order_by(Task.id)
                for task in query.all():
                    icon = icons.NEW_ICON
                    if task.status == 'DOING':
                        icon = icons.DOING_ICON
                    elif task.status == 'DONE':
                        icon = icons.DONE_ICON

                    a += '[[{}]] {} {} - {}\n'.format(task.id, icon, task.name, task.priority)
                    a += self.deps_text(task, chat)

                self.send_message(a, chat)
                a = ''

                a += icons.STATUS_ICON + ' _Status_\n'
                query = db.session.query(Task).filter_by(status='TODO', chat=chat).order_by(Task.id)
                a += icons.NEW_ICON + '\n *TODO*\n'
                for task in query.all():
                    a += '[[{}]] {} - {}\n'.format(task.id, task.name, task.duedate)
                query = db.session.query(Task).filter_by(status='DOING', chat=chat).order_by(Task.id)
                a += icons.DOING_ICON + '\n *DOING*\n'
                for task in query.all():
                    a += '[[{}]] {} - {}\n'.format(task.id, task.name, task.duedate)
                query = db.session.query(Task).filter_by(status='DONE', chat=chat).order_by(Task.id)
                a += icons.DONE_ICON + '\n *DONE*\n'
                for task in query.all():
                    a += '[[{}]] {} - {}\n'.format(task.id, task.name, task.duedate)

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
                                    parlist = taskdep.dependencies.split(',')
                                    if str(task.id) not in parlist:
                                        taskdep.parents += str(task.id) + ','
                                        deplist = task.dependencies.split(',')
                                        if str(depid) not in deplist:
                                            task.dependencies += str(depid) + ','
                                        self.send_message("Task {} dependencies up to date".format(task_id), chat)
                                    else:
                                        self.send_message("Dependencies can't be circular", chat)
                                except sqlalchemy.orm.exc.NoResultFound:
                                    self.send_message("_404_ Task {} not found x.x".format(depid), chat)
                                    continue

                    db.session.commit()
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
                undefined_priority = icons.WITHOUT_PRIORITY_ICON + ' Tasks whithout priority\n'

                priority_list += icons.LIST_ICON + '\n\n * Task List order by priority *\n'
                query = db.session.query(Task).filter_by(parents='', chat=chat).order_by(Task.priority)
                for task in query.all():
                    icon = icons.NEW_ICON
                    if task.status == 'DOING':
                        icon = icons.DOING_ICON
                    elif task.status == 'DONE':
                        icon = icons.DONE_ICON

                    if task.priority == 'high':
                        high_list += icons.HIGH_ICON + ' * {} *- {} {}\n'.format(task.priority, task.name, icon)
                    elif task.priority == 'medium':
                        medium_list += icons.MEDIUM_ICON + ' * {} *- {} {}\n'.format(task.priority, task.name, icon)
                    elif task.priority == 'low':
                        low_list += icons.LOW_ICON + ' * {} *- {} {}\n'.format(task.priority, task.name, icon)
                    else:
                        undefined_priority += icons.QUESTION_ICON + '{} {}\n'.format(task.name, icon)

                priority_list += high_list + medium_list + low_list + '\n' + undefined_priority
                self.send_message(priority_list, chat)

            elif command == '/duedate':
                text = ''
                duedate = ''
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
                        task.duedate = None
                        self.send_message("_Cleared_ all dates from task {}".format(task_id), chat)
                    else:
                        duedate = ''
                        today = ''

                        # corrigindo erro de pegar a data sem /
                        duedate = text.split('/')
                        duedate = date(int(duedate[2]), int(duedate[1]), int(duedate[0]))
                        today = date.today()
                        # Verificar se a data é maior ou igual que a do dia

                        task.duedate = duedate
                        self.send_message("*Task {}* date is *{}*".format(task_id, text.lower()), chat)
                    db.session.commit()

            elif command == '/start':
                self.send_message("Welcome! Here is a list of things you can do.", chat)
                self.send_message(self.HELP, chat)
            elif command == '/help':
                self.send_message("Here is a list of things you can do.", chat)
                self.send_message(self.HELP, chat)
            else:
                self.send_message("I'm sorry dave. I'm afraid I can't do that.", chat)
