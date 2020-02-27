# GMAIL POLING MESSAGES #
import manage
from vk_api import vk_api
from threading import Thread
from vk_api.longpoll import VkLongPoll, VkEventType


class GmailPolling(Thread):

    def __init__(self, account):
        Thread.__init__(self)
        self.chat_id = account.chat_id
        self.vk_token = account.vk_token

    def run(self):
        vk_session = vk_api.VkApi(token=self.vk_token)
        vk = vk_session.get_api()
        long_poll = VkLongPoll(vk_session)
        for event in long_poll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    user_message = vk.users.get(user_ids=event.user_id)[0]
                    manage.bot.send_message(self.chat_id,
                                            f'Новое сообщение {event.message} от: {user_message["first_name"]} '
                                            f'{user_message["last_name"]}')
