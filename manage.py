import config
import telebot
import urllib.parse
import vk_messages
from telebot import apihelper
from sqlalchemy import exists
from models import User, session

bot = telebot.TeleBot(config.token)
apihelper.proxy = config.proxy


def create_thread(account):
    polling = vk_messages.VkPolling(account=account)
    polling.start()


def start_threads():
    users = session.query(User).all()
    for user in users:
        create_thread(user)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    (result,) = session.query(exists().where(User.chat_id == chat_id))
    if result[0]:
        bot.send_message(message.chat.id, 'Вы уже зарегистрированы')
        return
    url_text = '[ссылке](https://oauth.vk.com/authorize?client_id=2685278&scope=friends,messages,photos,video,' \
               'offline&redirect_uri=https://api.vk.com/blank.html&response_type=token'
    text = f'В данный момент к вашему Telegram аккаунту не подключен какой-либо аккаунт ВКонтакте.️ ' \
           f'Предоставьте мне ' \
           f'доступ к сообщениям во ВКонтакте. Для этого отправьте полученный URL после перехода по {url_text}' \
           f'отправьте полученный URL'
    bot.send_message(message.chat.id, text, parse_mode='Markdown')


@bot.message_handler(regexp=r'(www\.)?(vk.com\/)')
def parsing_vk_url(message):
    chat_id = message.chat.id
    (result,) = session.query(exists().where(User.chat_id == chat_id))
    if result[0]:
        bot.send_message(message.chat.id, 'Вы уже зарегистрированы')
        return
    fragment = urllib.parse.urlparse(message.text).fragment
    dict_parameters = dict(urllib.parse.parse_qsl(fragment))
    if 'access_token' not in dict_parameters:
        bot.send_message(message.chat.id, 'Отсуствует access_token в URL')
        return
    token = dict_parameters['access_token']
    new_user = User(chat_id, token)
    session.add(new_user)
    session.commit()
    create_thread(new_user)
    bot.send_message(message.chat.id, 'Вы успешно зарегистрированы')


if __name__ == '__main__':
    start_threads()
    bot.polling(none_stop=True)
