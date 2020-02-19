import config
import telebot
import urllib.parse
from telebot import apihelper
from sqlalchemy import exists
from models import User, session

bot = telebot.TeleBot(config.token)
apihelper.proxy = config.proxy


@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = """В данный момент к вашему Telegram аккаунту не подключен какой-либо аккаунт
ВКонтакте.️ Предоставьте мне доступ к сообщениям во ВКонтакте. Для этого пришлите
токен доступа любого приложения во ВКонтакте, имеющего доступ к сообщениям.
https://oauth.vk.com/authorize?client_id=2685278&scope=friends,messages,photos,video,offline&redirect_uri=https://api.vk.com/blank.html&response_type=token"""
    bot.send_message(message.chat.id, text)


@bot.message_handler(regexp=r'(www\.)?(vk.com\/)')
def parsing_vk_url(message):
    chat_id = message.chat.id
    (resualt,) = session.query(exists().where(User.chat_id == chat_id))
    if resualt[0]:
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
    bot.send_message(message.chat.id, 'Вы успешно зарегистрированы')


bot.polling(none_stop=True)
