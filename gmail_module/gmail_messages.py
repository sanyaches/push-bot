"""
GMAIL POLLING MESSAGES
Class polling
"""

import manage
import pickle
import datetime

from threading import Thread
from time import sleep
from googleapiclient.discovery import build


class GmailPolling(Thread):

    def __init__(self, account):
        Thread.__init__(self)
        self.chat_id = account.chat_id
        self.credentials = pickle.loads(account.gm_credentials)

    def run(self):
        service = build('gmail', 'v1', credentials=self.credentials)

        polling_gmail(service, self.chat_id)


def polling_gmail(service, bot_chat_id):
    old_messages = get_messages(service)

    while True:
        sleep(5)

        new_messages = get_messages(service)

        diff = search_diff_messages(old_messages, new_messages)
        if len(diff) != 0:
            for msg in diff:
                date = datetime.datetime.fromtimestamp(int(msg['internalDate']) / 1000.0)
                manage.bot.send_message(bot_chat_id,
                                        f'{date} Получено новое письмо: {msg["snippet"]} '
                                        f' от { msg["payload"]["headers"][16]["value"]}')

        old_messages = new_messages


def get_messages(service, user_id='me'):
    """
    Try to get first 20 messages
    :param service: GMAIL client API service
    :param user_id: client_id
    :return: list of messages
    """
    messages = []
    threads = service.users().threads().list(userId=user_id).execute().get('threads', [])
    for thread in threads:
        thread_data = service.users().threads().get(userId=user_id, id=thread['id']).execute()
        for msg in reversed(thread_data['messages']):
            messages.append(msg)
            if len(messages) == 20:
                return messages
    return messages


def search_diff_messages(old_messages, new_messages):
    diff = []

    for index, new_message in enumerate(new_messages):
        for old_message in old_messages:
            if new_message['id'] == old_message['id']:
                return new_messages[:index]

    return new_messages
