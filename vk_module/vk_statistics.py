import datetime
import time

import vk_api

import manage


class VkStatistics:

    def __init__(self, vk_token, chat_id):
        self.vk_token = vk_token
        self.chat_id = chat_id

    def by_date(self, date):
        global time_filter
        vk_session = vk_api.VkApi(token=self.vk_token)
        vk = vk_session.get_api()
        try:
            time_filter = time.mktime(datetime.datetime.strptime(date, "%d.%m.%Y %H:%M").timetuple())
        except:
            manage.bot.send_message(chat_id=self.chat_id, text='Неверный формат даты')
            return
        conversations = [conversation for conversation in vk.messages.getConversations(extended=1, count=20)[
            'profiles']]
        conversations_statistics = {}
        manage.bot.send_message(self.chat_id, text='Сбор статистики\nПожалуйста подождите')
        for conversation in conversations:
            count_history_messages = 0
            user_id = conversation['id']
            messages = vk.messages.getHistory(user_id=user_id, count=200)
            for message in messages['items']:
                if message['date'] >= time_filter:
                    count_history_messages += 1
            if count_history_messages == 0:
                continue
            name_user_id = conversation['first_name'] + ' ' + conversation['last_name']
            conversations_statistics[name_user_id] = count_history_messages
        return "\n".join("{!s} : {!r}".format(key, val) for (key, val) in conversations_statistics.items())
