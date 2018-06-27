import urllib
import json
import requests
import constants


class MessageException(Exception):
    """Just to specify a kind of Exception"""
    pass


class UrlHandler:

    def get_url(self, url):
        """get response content of given url"""
        response = requests.get(url)
        content = response.content.decode("utf8")
        return content

    def get_json_from_url(self, url):
        """get json content of the given url"""
        content = self.get_url(url)
        payload = json.loads(content)
        return payload

    def get_updates(self, offset=None):
        """request new information from API"""
        url = constants.URL_TELEGRAM + "getUpdates?timeout=100"
        if offset:
            url += "&offset={}".format(offset)
        payload = self.get_json_from_url(url)
        return payload

    def send_message(self, text, chat_id, reply_markup=None):
        """send message to the user"""
        text = urllib.parse.quote_plus(text)
        url = constants.URL_TELEGRAM + ("sendMessage?text={}&chat_id={}&parse_mode=Markdown"
                     .format(text, chat_id))
        if reply_markup:
            url += "&reply_markup={}".format(reply_markup)
        self.get_url(url)

    def get_last_update_id(self, updates):
        """get the last update"""
        update_ids = []
        for update in updates["result"]:
            update_ids.append(int(update["update_id"]))

        return max(update_ids)

    def get_message(self, update):
        """return the message catched by update"""
        if 'message' in update:
            message = update['message']
        elif 'edited_message' in update:
            message = update['edited_message']
        else:
            print('Can\'t process! {}'.format(update))
            raise MessageException('Not recognizable message')
        return message