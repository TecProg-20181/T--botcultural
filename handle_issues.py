import requests
import constants
from handle_url import UrlHandler


class HandleIssues:
    def __init__(self):
        self.url_handler = UrlHandler()

    def split_message(self, msg):
        """split a message"""
        text = ''
        if msg != '':
            if len(msg.split(' ', 1)) > 1:
                text = msg.split(' ', 1)[1]
            msg = msg.split(' ', 1)[0]
        return msg, text

    def new_issue(self, name, chat):
        """Create an Issue"""
        payload = "{\n  \"title\": \""+name+"\",\n  \"labels\": [\n    \"telegram\"\n  ]\n}"
        print(payload)
        headers = {
            'Content-Type': "application/json",
            'Authorization': "token b9b41b4afc288532de694dc776cfffe200926437",
            'Cache-Control': "no-cache",
            'Postman-Token': "971ca199169fa9ad5ae235f7304a6bbf0b5f4faa"
        }

        response = requests.request("POST", constants.URL_GITHUB, data=payload, headers=headers)

        print(response.text)

        return self.url_handler.send_message("New Issue created {}".format(name), chat)

    def rename_issue(self, msg, chat):
        """rename a task by id"""
        msg, text = self.split_message(msg)

        if text == '':
            self.url_handler.send_message("""
                          You want to modify the issue {},
                          but you didn't provide any new text
                         """.format(msg), chat)
            return

        payload = "{\n  \"title\": \""+text+"\",\n  \"labels\": [\n    \"telegram\"\n  ]\n}"
        print(payload)
        headers = {
            'Content-Type': "application/json",
            'Authorization': "token b9b41b4afc288532de694dc776cfffe200926437",
            'Cache-Control': "no-cache",
            'Postman-Token': "971ca199169fa9ad5ae235f7304a6bbf0b5f4faa"
        }
        result = requests.request("GET", constants.URL_GITHUB + '/' + msg)
        result_json = result.json()
        print(result_json)
        try:
            result_json['state']
        except:
            return self.url_handler.send_message("Issue does not exist", chat)

        requests.request("POST", constants.URL_GITHUB+'/'+msg, data=payload, headers=headers)
        return self.url_handler.send_message("Issue renamed {}".format(text), chat)

    def list_issues(self, chat):
        """lists all the issues active in the T--botcultural"""
        issues = self.url_handler.get_json_from_url(constants.URL_GITHUB)
        msg = ''
        msg += '\U0001F4CB Issues List\n\n'
        for aux in issues:
            msg += "[[{}]] - {}\n\n".format(str(aux['number']), aux['title'])

        self.url_handler.send_message(msg, chat)