import datetime
import time
import urllib.parse

import telebot
import telebot_calendar
from sqlalchemy import exists
from telebot import apihelper
from telebot.types import ReplyKeyboardRemove, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup
from telebot_calendar import CallbackData

import config
from models import User, session
from vk_module import vk_messages
from vk_module.vk_statistics import VkStatistics

bot = telebot.TeleBot(config.token)
apihelper.proxy = config.proxy

threads = []
calendar = CallbackData("calendar_1", "action", "year", "month", "day")


def get_user(message):
    return session.query(User).filter_by(chat_id=message.chat.id).first()


def create_thread(accounts):
    for account in accounts:
        threads.append(vk_messages.VkPolling(account=account))


def start_threads():
    users = session.query(User).all()
    create_thread(users)
    for thread in threads:
        thread.start()


def pause_thread(message):
    for thread in threads:
        if thread.chat_id == message.chat.id:
            thread.stop()


def resume_thread(message):
    for thread in threads:
        if thread.chat_id == message.chat.id:
            thread.resume()


def statistics_markup():
    markup = ReplyKeyboardMarkup()
    statistics_vk_btn = KeyboardButton('Статистика Вконтакте')
    statistics_mail_btn = KeyboardButton('Статистика Gmail')
    pause_btn = KeyboardButton('Приостановить уведомления')
    resume_btn = KeyboardButton('Восстановить уведомления')
    markup.add(pause_btn)
    markup.add(resume_btn)
    markup.add(statistics_vk_btn)
    markup.add(statistics_mail_btn)
    return markup


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


@bot.message_handler(regexp='Приостановить уведомления')
def pause_vk_polling(message):
    pause_thread(message)


@bot.message_handler(regexp='Восстановить уведомления')
def resume_vk_polling(message):
    resume_thread(message)


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
    thread = vk_messages.VkPolling(new_user)
    thread.start()
    threads.append(thread)
    bot.send_message(message.chat.id, 'Вы успешно зарегистрированы', reply_markup=statistics_markup())


@bot.message_handler(regexp='Статистика ВК')
def vk_statistic(message):
    now = datetime.datetime.now()
    bot.send_message(
        message.chat.id,
        "Выберите день",
        reply_markup=telebot_calendar.create_calendar(
            name=calendar.prefix,
            year=now.year,
            month=now.month,
        ),
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith(calendar.prefix))
def callback_inline(call: CallbackQuery):
    name, action, year, month, day = call.data.split(calendar.sep)
    date = telebot_calendar.calendar_query_handler(
        bot=bot, call=call, name=name, action=action, year=year, month=month, day=day
    )
    if action == "DAY":
        bot.send_message(
            chat_id=call.from_user.id,
            text=f"Вы выбрали {date.strftime('%d.%m.%Y')}\nСбор статистики\nПожалуйста подождите",
            reply_markup=ReplyKeyboardRemove(),
        )
        account = session.query(User).filter_by(chat_id=call.from_user.id).first()
        vk_statistics = VkStatistics(account.vk_token, account.chat_id).by_date(time.mktime(date.timetuple()))
        bot.send_message(chat_id=call.from_user.id, text=vk_statistics, reply_markup=statistics_markup())
    elif action == "CANCEL":
        bot.send_message(
            chat_id=call.from_user.id,
            text="Отмена",
            reply_markup=statistics_markup(),
        )
        print(f"{calendar}: Отмена")


if __name__ == '__main__':
    start_threads()
    bot.polling(none_stop=True)
