import urllib.parse

import telebot
from sqlalchemy import exists
from telebot import apihelper, types

import config
import vk_messages
from models import User, session
from vk_statistics import VkStatistics

bot = telebot.TeleBot(config.token)
apihelper.proxy = config.proxy


def create_thread(account):
    polling = vk_messages.VkPolling(account=account)
    polling.start()


def start_threads():
    users = session.query(User).all()
    for user in users:
        create_thread(user)


def statistics_markup():
    markup = types.ReplyKeyboardMarkup()
    statistics_vk_btn = types.KeyboardButton('Статистика Вконтакте')
    statistics_mail_btn = types.KeyboardButton('Статистика Gmail')
    markup.add(statistics_vk_btn)
    markup.add(statistics_mail_btn)
    return markup


def process_vk_statistics(message):
    chat_id = message.chat.id
    user = session.query(User).filter_by(chat_id=chat_id).first()
    vk_statistics = VkStatistics(vk_token=user.vk_token, chat_id=chat_id).by_date(message.text)
    if vk_statistics is not None:
        bot.send_message(chat_id, vk_statistics)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    (result,) = session.query(exists().where(User.chat_id == chat_id))
    if result[0]:
        bot.send_message(message.chat.id, 'Вы уже зарегистрированы', reply_markup=statistics_markup())
        return
    url_text = '[ссылке](https://oauth.vk.com/authorize?client_id=2685278&scope=friends,messages,photos,video,' \
               'offline&redirect_uri=https://api.vk.com/blank.html&response_type=token'
    text = f'В данный момент к вашему Telegram аккаунту не подключен какой-либо аккаунт ВКонтакте.️ ' \
           f'Предоставьте мне ' \
           f'доступ к сообщениям во ВКонтакте. Для этого отправьте полученный URL после перехода по {url_text}'
    bot.send_message(message.chat.id, text, parse_mode='Markdown')


@bot.message_handler(regexp=r'(www\.)?(vk.com\/)')
def parsing_vk_url(message):
    chat_id = message.chat.id
    (result,) = session.query(exists().where(User.chat_id == chat_id))
    if result[0]:
        bot.send_message(message.chat.id, 'Вы уже зарегистрированы', reply_markup=statistics_markup())
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
    bot.send_message(message.chat.id, 'Вы успешно зарегистрированы', reply_markup=statistics_markup())


@bot.message_handler(regexp='Статистика ВК')
def statistics_vk(message):
    msg = bot.reply_to(message, 'Введите дату в виде (22.02.2020 13:22)')
    bot.register_next_step_handler(msg, process_vk_statistics)


if __name__ == '__main__':
    start_threads()
    bot.polling(none_stop=True)
