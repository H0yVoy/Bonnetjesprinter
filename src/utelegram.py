# based on: https://github.com/jordiprats/micropython-utelegram
# but improved so now it _does_ work

from utime import sleep
import gc
import ujson
import urequests_nr as urequests

class ubot:
    def __init__(self, token):
        self.url = 'https://api.telegram.org/bot' + token
        self.commands = {}
        self.default_handler = None
        self.message_offset = 0
        self.sleep_btw_updates = 3

        messages = self.read_messages()
        if messages:
            for message in messages:
                if message['update_id'] > self.message_offset:
                    self.message_offset = message['update_id']


    def send(self, chat_id, text):
        data = {'chat_id': chat_id, 'text': text}
        try:
            headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
            response = urequests.post(self.url + '/sendMessage', json=data, headers=headers)
            response.close()
            return True
        except:
            return False

    def read_messages(self):
        result = []
        query_updates = {
            "offset": self.message_offset,
            "limit": 2,
            "timeout": 15,
            "allowed_updates": ['message']}

        try:
            # print("Getting new messages...")
            gc.collect()  # before action, else it throws away things I need
            update_messages = urequests.post(self.url + '/getUpdates', json=query_updates).json() 
            # print(update_messages)
            if 'result' in update_messages:
                for item in update_messages['result']:
                    # append all messages else it won't get updated, check for contents later
                    result.append(item)
            return result
        except (ValueError):
            return None
        except (OSError):
            print("OSError: request timed out")
            return None

    def listen(self):
        while True:
            self.read_once()
            sleep(self.sleep_btw_updates)


    def read_once(self):
        messages = self.read_messages()
        if messages:
            for message in messages:
                # print("Message:", message)
                if message['update_id'] > self.message_offset:
                    if 'text' in message['message']:
                        self.message_handler(message)
                        print("Message:", message)
                    # only update key after text has been handled
                    self.message_offset = message['update_id']


    def register(self, command, handler):
        self.commands[command] = handler

    def set_default_handler(self, handler):
        self.default_handler = handler

    def set_sleep_btw_updates(self, sleep_time):
        self.sleep_btw_updates = sleep_time

    def message_handler(self, message):
        parts = message['message']['text'].split(' ')
        if parts[0] in self.commands:
            self.commands[parts[0]](message)
        else:
            if self.default_handler:
                self.default_handler(message)
