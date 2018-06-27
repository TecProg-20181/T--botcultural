import constants
from db import Task
from urlhandler import UrlHandler
from taskmanager import TaskManager
from issuemanager import IssueManager


class MessageException(Exception):
    """Just to specify a kind of Exception"""
    pass


class BotManager:
    def __init__(self):
        self.task_manager = TaskManager()
        self.issue_manager = IssueManager()
        self.url_handler = UrlHandler()

    def handle_updates(self, updates, chat_bot):
        """read the user command and calls the property methods"""
        for update in updates["result"]:
            try:
                message = self.url_handler.get_message(update)
                command = message["text"].split(" ", 1)[0]
            except:
                return
            msg = ''
            if len(message["text"].split(" ", 1)) > 1:
                msg = message["text"].split(" ", 1)[1].strip()

            chat = message["chat"]["id"]

            print('\n\n\n')
            print(command, msg, chat)
            print('\n\n\n')
            
            if command == '/new' or command == '/n':
                self.task_manager.new_task(msg, chat)

            elif command == '/newIssue' or command == '/ni':
                self.issue_manager.new_issue(msg, chat)

            elif command == '/renameIssue' or command == '/ri':
                self.issue_manager.rename_issue(msg, chat)

            elif command == '/rename' or command == '/r':
                self.task_manager.rename_task(msg, chat)

            elif command == '/duplicate' or command == '/dc':
                self.task_manager.duplicate_task(msg, chat)

            elif command == '/delete' or command == '/d':
                self.task_manager.delete_task(msg, chat)

            elif command == '/todo':
                self.task_manager.set_task_status(msg, chat, constants.TODO)

            elif command == '/doing':
                self.task_manager.set_task_status(msg, chat, constants.DOING)

            elif command == '/done':
                self.task_manager.set_task_status(msg, chat, constants.DONE)

            elif command == '/listP' or command == '/lp':
                order = Task.priority
                self.task_manager.list_tasks(chat, order)

            elif command == '/list' or command == '/l':
                order = Task.id
                self.task_manager.list_tasks(chat, order)

            elif command == '/listIssues' or command == '/li':
                self.issue_manager.list_issues(chat)

            elif command == '/dependson' or command == '/dp':
                self.task_manager.depend_on_task(msg, chat)

            elif command == '/priority' or command == '/p':
                self.task_manager.prioritize_task(msg, chat)

            elif command == '/duedate' or command == '/dd':
                self.task_manager.duedate_task(msg, chat)

            elif command == '/start':
                self.url_handler.send_message("Welcome! Here is a list of things you can do.", chat)
                self.url_handler.send_message(constants.HELP, chat)

            elif command == '/help' or command == '/h':
                self.url_handler.send_message("Here is a list of things you can do.", chat)
                self.url_handler.send_message(constants.HELP, chat)

            else:
                response = chat_bot.predict([message['text']])
                print(response)
                print(message['text'])
                response = str(response)
                print(response)
                self.url_handler.send_message(response[2:-2], chat)
