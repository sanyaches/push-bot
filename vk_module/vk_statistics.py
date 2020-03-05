import datetime
import time

import vk_api


class VkStatistics:

    def __init__(self, vk_token):
        self.vk_token = vk_token

    def by_date(self, date):
        vk_session = vk_api.VkApi(token=self.vk_token)
        vk = vk_session.get_api()
        time_filter = time.mktime(datetime.datetime.strptime(date, "%d.%m.%Y %H:%M").timetuple())
        conversations = [conversation for conversation in vk.messages.getConversations(extended=1, count=20)[
            'profiles']]
        conversations_statistics = {}
        for conversation in conversations:
            count_history_messages = 0
            user_id = conversation['id']
            messages = vk.messages.getHistory(user_id=user_id, count=200)
            for message in messages['items']:
                if message['date'] >= time_filter:
                    count_history_messages += 1
            name_user_id = conversation['first_name'] + ' ' + conversation['last_name']
            conversations_statistics[name_user_id] = count_history_messages
        return "\n".join("{!s} : {!r}".format(key, val) for (key, val) in conversations_statistics.items())
