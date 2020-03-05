import config
import telebot
import telebot_calendar

import urllib.parse
import datetime
import time
import json

from vk_module import vk_messages
from gmail_module import gmail_messages

from telebot import apihelper
from telebot.types import ReplyKeyboardRemove, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup
from telebot_calendar import CallbackData

from sqlalchemy import exists
from models import User, session
from google_auth_oauthlib.flow import InstalledAppFlow
from vk_module.vk_statistics import VkStatistics

bot = telebot.TeleBot(config.token)
apihelper.proxy = config.proxy

# If modifying these scopes, delete the file token.user.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

threads = []
calendar = CallbackData("calendar_1", "action", "year", "month", "day")


def get_user(message):
    return session.query(User).filter_by(chat_id=message.chat.id).first()

  
def create_thread(accounts):
    for account in accounts:
        threads.append(vk_messages.VkPolling(account=account))
        threads.append(gmail_messages.GmailPolling(account=user))

        
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

    new_user = User(chat_id, token, '')
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


@bot.message_handler(commands=['gmail'])
# function authGmail(message) => add credentials to db
# from response oauth google
def auth_gmail(message):

    # 1) Check registered in gmail => nothing
    chat_id = message.chat.id
    (result,) = session.query(exists().where(User.chat_id == chat_id and User.gm_credentials))

    if result[0]:
        bot.send_message(message.chat.id, 'Вы уже зарегистрированы в gmail')
        return

    # 2) Check registered in vk but not gmail => upgrade user
    (result,) = session.query(exists().where(User.chat_id == chat_id and User.vk_token and not User.gm_credentials))
    if result[0]:
        bot.send_message(message.chat.id, 'Сейчас вас перенаправит в браузер для того чтобы зарегистрироваться в gmail')
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)

        result[0].update({'gm_credentials': json.dumps(creds.__dict__)})
        session.commit()

    # 3) Get the credentials => add new user
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)

    new_user = User(chat_id, '', creds)
    session.add(new_user)
    session.commit()
    
    thread = gmail_messages.GmailPolling(account=new_user)
    thread.start()
    threads.append(thread)

    # finally => success message :)
    bot.send_message(message.chat.id, 'Вы успешно зарегистрированы')


if __name__ == '__main__':
    start_threads()
    bot.polling(none_stop=True)
