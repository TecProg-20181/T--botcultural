import sqlalchemy
import db
import datetime
import constants
from urlhandler import UrlHandler
from db import Task


class MessageException(Exception):
    """Just to specify a kind of Exception"""
    pass


class TaskManager:
    def __init__(self):
        self.url_handler = UrlHandler()

    def deps_text(self, task, chat, preceed=''):
        """list tasks in a tree view"""
        text = ''

        for i in range(len(task.dependencies.split(',')[:-1])):
            line = preceed
            query = (db.SESSION
                     .query(Task)
                     .filter_by(id=int(task
                                       .dependencies
                                       .split(',')[:-1][i]), chat=chat))
            dep = query.one()

            icon = constants.NEW_ICON
            if dep.status == 'DOING':
                icon = constants.DOING_ICON
            elif dep.status == 'DONE':
                icon = constants.DONE_ICON

            if i + 1 == len(task.dependencies.split(',')[:-1]):
                line += '└── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
                line += self.deps_text(dep, chat, preceed + '    ')
            else:
                line += '├── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
                line += self.deps_text(dep, chat, preceed + '│   ')

            text += line

        return text

    def get_task(self, msg, chat):
        """send message acusing missing id in the command"""
        if not msg.isdigit():
            self.url_handler.send_message("You must inform the task id {}".format(constants.THINKING_EMOJI), chat)
            raise MessageException('id not provided')
        task_id = int(msg)
        query = db.SESSION.query(Task).filter_by(id=task_id, chat=chat)
        try:
            task = query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            self.url_handler.send_message("Sorry, I didn't find task {} {}.".format(task_id, constants.CONFUSED_EMOJI), chat)
            raise MessageException('task not found')
        return task

    def new_task(self, name, chat):
        """Create and returns a new task named by the user"""
        task = Task(chat=chat,
                    name=name,
                    status='TODO',
                    dependencies='',
                    parents='',
                    priority='2')
        db.SESSION.add(task)
        db.SESSION.commit()
        self.url_handler.send_message("Okay, I'll write this {}.\nThe ID is [[{}]]\n{}".format(constants.WRITING_EMOJI,
                                                                                       task.id,
                                                                                       task.name),
                                      chat)
        return task

    def rename_task(self, msg, chat):
        """rename a task by id"""
        msg, text = self.split_message(msg)
        try:
            task = self.get_task(msg, chat)
        except MessageException:
            return

        if self.validate_rename_task(task, chat, text) is True:

            old_text = task.name
            task.name = text
            db.SESSION.commit()
            self.url_handler.send_message("""
                          Task {} redefined from {} to {}
                         """.format(task.id, old_text, text), chat)
        else:
            # NOTHING TO DO
            pass

    def validate_rename_task(self, task, chat, text):
        """validate if it is possible to rename a task"""
        if text == '':
            self.url_handler.send_message("""
                          You want to modify task {},
                          but you didn't provide any new text
                         """.format(task.id), chat)
            return False
        return True

    def duplicate_task(self, msg, chat):
        """copy a task by id"""
        for id in msg.split():
            try:
                task = self.get_task(id, chat)
            except MessageException:
                continue

            dtask = self.new_task(task.name, chat)

            for item in task.dependencies.split(',')[:-1]:
                querry = db.SESSION.query(Task).filter_by(id=int(item), chat=chat)
                item = querry.one()
                item.parents += '{},'.format(dtask.id)

    def delete_task(self, msg, chat):
        """delete a task by id"""
        for id in msg.split():
            try:
                task = self.get_task(id, chat)
            except MessageException:
                continue
            dependencies = []
            for item in task.dependencies.split(',')[:-1]:
                dependencies.append(item)
            for item in task.parents.split(',')[:-1]:
                querry = db.SESSION.query(Task).filter_by(id=int(item), chat=chat)
                item = querry.one()
                item.dependencies = item.dependencies.replace('{},'.format(task.id), '')
            for item in dependencies:
                querry = db.SESSION.query(Task).filter_by(id=int(item), chat=chat)
                item = querry.one()
                item.parents = item.parents.replace('{},'.format(task.id), '')
            db.SESSION.delete(task)
            db.SESSION.commit()
            self.url_handler.send_message("Task [[{}]] deleted".format(task.id), chat)

    def set_task_status(self, msg, chat, status):
        """set status of task to TODO"""
        for id in msg.split():
            try:
                task = self.get_task(id, chat)
            except MessageException:
                continue
            task.status = status
            db.SESSION.commit()
            self.url_handler.send_message("*{}* task [[{}]] {}".format(status, task.id, task.name), chat)

    def list_tasks(self, chat, order):
        """lists all the tasks"""
        msg = ''

        msg += '\U0001F4CB Task List\n'
        query = (db.SESSION
                 .query(Task)
                 .filter_by(parents='', chat=chat)
                 .order_by(Task.id))
        for task in query.all():
            icon = constants.NEW_ICON
            if task.status == 'DOING':
                icon = constants.DOING_ICON
            elif task.status == 'DONE':
                icon = constants.DONE_ICON

            msg += '[[{}]] {} {}\n'.format(task.id, icon, task.name)
            msg += self.deps_text(task, chat)

        self.url_handler.send_message(msg, chat)

        msg = ''

        msg += constants.STATUS_ICON + '_Status_\n'

        for status, status_icon in zip(['TODO', 'DOING', 'DONE'],
                                       [constants.NEW_ICON, constants.DOING_ICON, constants.DONE_ICON]):

            query_result = self.query(status, chat, order)
            msg += '\n'+ status_icon + '*' + status + '*\n'
            for task in query_result.all():
                msg += '[[{}]] {} {} {}\n'.format(task.id,
                                                  constants.PRIORITY[self.dict_priority(task.priority)],
                                                  task.name,
                                                  task.duedate)

        self.url_handler.send_message(msg, chat)

    def query(self, status, chat, order):
        """makes a query with those parameters"""
        query = (db.SESSION
                 .query(Task)
                 .filter_by(status=status, chat=chat)
                 .order_by(order))
        return query

    def circular_dependency(self, task_id, depid, chat):
        """checks if link the task with a circular dependency
           will cause some circular dependency deadlock"""
        try:
            task = self.get_task(str(task_id), chat)
        except MessageException:
            return True
        if str(depid) in task.parents.split(',')[:-1]:
            return True
        for i in task.parents.split(',')[:-1]:
            if self.circular_dependency(i, depid, chat):
                return True
        return False

    def depend_on_task(self, msg, chat):
        """set dependencies of the task"""
        msg, text = self.split_message(msg)


        try:
            task = self.get_task(msg, chat)
        except MessageException:
            return

        if text == '':
            for i in task.dependencies.split(',')[:-1]:
                i = int(i)
                querry = db.SESSION.query(Task).filter_by(id=i, chat=chat)
                item = querry.one()
                item.parents = item.parents.replace('{},'.format(task.id), '')

            task.dependencies = ''
            self.url_handler.send_message("Task {} doesn't have any dependencies anymore".format(task.id),
                         chat)
        else:
            for depid in text.split(' '):
                if task.id == int(depid):
                    self.url_handler.send_message("Invalid task: {}".format(depid), chat)
                elif self.circular_dependency(task.id, depid, chat):
                    self.url_handler.send_message("Circular dependency, task {} depends on a task {}"
                                 .format(depid, task.id), chat)
                    continue
                else:
                    try:
                        taskdep = self.get_task(depid, chat)
                    except MessageException:
                        continue

                    aux_parents = taskdep.parents.split(',')
                    if str(task.id) not in aux_parents:
                        taskdep.parents += str(task.id) + ','
                    
                    deplist = task.dependencies.split(',')
                    if str(depid) not in deplist:
                        task.dependencies += str(depid) + ','

        db.SESSION.commit()
        self.url_handler.send_message("Task {} dependencies up to date".format(task.id), chat)

    def split_message(self, msg):
        """split a message"""
        text = ''
        if msg != '':
            if len(msg.split(' ', 1)) > 1:
                text = msg.split(' ', 1)[1]
            msg = msg.split(' ', 1)[0]
        return msg, text

    def split_list(self, msg):
        """split a list of parameters and a comand as
        first parameter"""
        if len(msg.split()) > 1:
            ids = msg.split()[1:]
        text = msg.split()[0]
        return text, ids

    def prioritize_task(self, msg, chat):
        """set the priority of given task"""
        text, ids = self.split_list(msg)

        for id in ids:
            try:
                task = self.get_task(id, chat)
            except MessageException:
                continue

            if text == '':
                task.priority = ''
                self.url_handler.send_message("_Cleared_ all priorities from task {}"
                             .format(task.id), chat)
            else:
                if text.lower() not in ['high', 'medium', 'low']:
                    self.url_handler.send_message("""
                                    I'm not so smart, sorry. {}
Please, tell me 'high', 'medium', or 'low'
                                """.format(constants.ZANY_EMOJI), chat)
                else:
                    task.priority = self.dict_priority(text.lower())
                    self.url_handler.send_message("*Task {}* priority has priority *{}*"
                                 .format(task.id, text.lower()), chat)
                db.SESSION.commit()

    def duedate_task(self, msg, chat):
        """set the priority of given task"""
        text, ids = self.split_list(msg)

        for id in ids:
            try:
                task = self.get_task(id, chat)
            except MessageException:
                continue

            if text == '':
                task.duedate = ''
                self.url_handler.send_message("_Cleared_ duedate from task {}"
                             .format(task.name), chat)
            else:
                if self.validate_date(text, chat) is True:
                    task.duedate = text
                    self.url_handler.send_message("*Task {}* duedate is *{}*"
                                 .format(task.id, text), chat)
            db.SESSION.commit()

    def validate_date(self, text, chat):
        """cheks if input is a valid date"""
        try:
            datetime.datetime.strptime(text, '%Y-%m-%d')
        except ValueError:
            self.url_handler.send_message("""
                                     Incorrect data format, should be YYYY-MM-DD
                                 """, chat)
            return

        if datetime.datetime.strptime(text, '%Y-%m-%d') < datetime.datetime.now():
            self.url_handler.send_message("""
            You can't travel to the past {}
            If you can please tell us how :)""".format(constants.MONOCLE_EMOJI), chat)
            return False
        return True

    def dict_priority(self, priority):
        """translate priority by the following dictionary"""
        return {
            'high': '1',
            'medium': '2',
            'low': '3',
            '1': 'high',
            '2': 'medium',
            '3': 'low',
        }[priority]
