import config
import telebot
import urllib.parse
from vk_module import vk_messages
from gmail_module import gmail_messages
from telebot import apihelper, types
from sqlalchemy import exists
from models import User, session
from google_auth_oauthlib.flow import InstalledAppFlow
import json
from vk_module.vk_statistics import VkStatistics

bot = telebot.TeleBot(config.token)
apihelper.proxy = config.proxy

# If modifying these scopes, delete the file token.user.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def create_thread_vk(user):
    polling_vk = vk_messages.VkPolling(account=user)
    polling_vk.start()


def create_thread_gmail(user):
    polling_gmail = gmail_messages.GmailPolling(account=user)
    polling_gmail.start()


def create_thread(user):
    create_thread_vk(user)
    create_thread_gmail(user)


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
    vk_statistics = VkStatistics(user.vk_token).by_date(message.text)
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

    new_user = User(chat_id, token, '')
    session.add(new_user)
    session.commit()
    create_thread(new_user)

    bot.send_message(message.chat.id, 'Вы успешно зарегистрированы', reply_markup=statistics_markup())


@bot.message_handler(func=lambda message: 'Статистика ВК')
def statistics_vk(message):
    msg = bot.reply_to(message, 'Введите дату в виде (22.02.2020 13:22)')
    bot.register_next_step_handler(msg, process_vk_statistics)


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
    create_thread(new_user)

    # finally => success message :)
    bot.send_message(message.chat.id, 'Вы успешно зарегистрированы')


if __name__ == '__main__':
    start_threads()
    bot.polling(none_stop=True)
