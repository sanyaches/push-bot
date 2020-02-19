import config
from models import User, session
from vk_api import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from bot import bot
class VkPolling(object):

    def __init__(self, chat_id, vk_token):
        self.chat_id = chat_id
        self.vk_token = vk_token

    def longpoll_listener(self):
        vk_session = vk_api.VkApi(app_id=config.vk_app_id, token=self.vk_token)
        vk = vk_session.get_api()
        longpoll = VkLongPoll(vk_session)
        global user
        for event in longpoll.listen():

            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    user = vk.users.get(user_ids=event.user_id)[0]

                return f'Новое сообщение {event.message} от: {user["first_name"]} {user["last_name"]},' \
                       f' {event.datetime.hour}:{event.datetime.minute}'


