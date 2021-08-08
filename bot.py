import json
import telebot
import requests
from telebot import types
from typing import Type
import google_auth_oauthlib.flow
import datetime
from dateutil.parser import *
import os.path
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import pyshorteners
import utils

f = open('credentials.json')
credentials = json.load(f)["web"]
client_id = credentials["client_id"]
client_secret = credentials["client_secret"]
f.close()
f = open('settings.json')
settings = json.load(f)
bot_token = settings["bot_token"]
redirect_url = settings["redirect_url"]
app_name = settings["app_name"]
f.close()

message_containers = {}  # словарь сообщений
comment_message_ids = {}  # словарь id

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
bot = telebot.TeleBot(bot_token)


class MessageChainNode:
    def __init__(self):
        self.message = Type[telebot.types.Message]  # атрибут message получает атрибуты класса Message
        self.previous_node = Type[MessageChainNode]  # рекурсивный атрибут предыдущего узла


@bot.message_handler(commands=['start'])
def start(message):
    keyboard_login = types.InlineKeyboardMarkup()
    auth_url = get_google_auth_url()
    auth_url_update = 'https://beetzung.com/login?user={}&auth_link={}'.format(message.chat.id, auth_url)
    short = pyshorteners.Shortener()
    short_url = short.tinyurl.short(auth_url_update)
    url_button = types.InlineKeyboardButton(text="Google", url=short_url)
    keyboard_login.row(url_button)
    bot.send_message(message.chat.id, "Войдите через Google аккаунт.", reply_markup=keyboard_login)
    # \nЗатем войдите через Trello аккаунт, скопируйте токен и вставьте его с командой /token [токен]


def notify_success_google_auth(chat_id, success):
    if success:
        keyboard_login = types.InlineKeyboardMarkup()
        auth_url_update_trello = 'https://trello.com/1/authorize?' \
                                 'key=224f6adae2e797aa48a9caee49f30868&' \
                                 'expiration=never&' \
                                 'name=CalendarTrello&' \
                                 'scope=read,write&' \
                                 'response_type=token'

        short_trello = pyshorteners.Shortener()
        short_url_trello = short_trello.tinyurl.short(auth_url_update_trello)
        url_button_trello = types.InlineKeyboardButton(text="Trello",
                                                       url=short_url_trello)
        keyboard_login.row(url_button_trello)
        bot.send_message(chat_id, 'Ура, авторизация через Google произошла успешно. Теперь войдите через Trello '
                                  'аккаунт, скопируйте токен и вставьте его с командой /token [токен]',
                         reply_markup=keyboard_login)
    else:
        msg = "похоже, вы уже логинились. если хотите перелогиниться в этот аккаунт, " \
              + "запретите доступ приложению CalendarTrello по ссылке https://myaccount.google.com/u/0/permissions и " \
              + "попробуйте еще раз: /start"
        bot.send_message(chat_id, msg)


@bot.message_handler(commands=['help'])
def help(message):
    if not os.path.exists(utils.get_google_token_path(message.chat.id)):
        start(message)
        return
    if not os.path.exists(utils.get_trello_token_path(message.chat.id)):
        notify_success_google_auth(message.chat.id, True)
        return
    keyboard_week = telebot.types.ReplyKeyboardMarkup(True).row("Текущая неделя", "Следующая неделя")
    bot.send_message(message.chat.id, "Введите /get или Текущая неделя для получения событий этой недели.\n"
                     + "Для получения событий следующей недели введите /get_next или Следующая неделя",
                     reply_markup=keyboard_week)


@bot.message_handler(commands=['token'])
def token(message):
    token_trello = (utils.find_after(message.text, '/token '))
    j = {
        "token": token_trello
    }
    json.dump(j, utils.get_trello_token_path(message.chat.id))
    bot.send_message(message.chat.id, "Токен получен, все ок")
    help(message)


@bot.message_handler(func=lambda m: True)
def handle_message(message):
    if not os.path.exists(utils.get_google_token_path(message.chat.id)):
        start(message)
        return
    if not os.path.exists(utils.get_trello_token_path(message.chat.id)):
        notify_success_google_auth(message.chat.id, True)
        return
    global message_containers
    global comment_message_ids
    container = MessageChainNode()  # создание объекта класса MessageChainNode
    container.message = message  # пришедшее сообщение
    container.previous_node = message_containers.get(
        message.chat.id)  # из словаря записывается чат айди в предыдущий узел контейнера
    message_container = container  # создание объекта  класса MessageChainNode с атрибутами container полученныеми из message
    message_containers[message.chat.id] = message_container  # ???

    def detect_comment(m: MessageChainNode):
        if m.previous_node is not None:
            this_message = m.message
            previous_message = m.previous_node.message
            if previous_message.date == this_message.date:
                if previous_message.forward_from is not None:
                    return detect_comment(m.previous_node)
                else:
                    return previous_message
        else:
            return None

    comment_message = detect_comment(message_container)
    if comment_message is not None:
        comment_message_id = comment_message_ids.get(message.chat.id)
        print("checking comment: last commented - {}, this - {}".format(comment_message_id,
                                                                        comment_message.message_id))
        if comment_message_id != comment_message.message_id:
            comment_message_ids[message.chat.id] = comment_message.id
            print("found message [{}] that is a comment to forwarder message with id [{}]!".format(
                comment_message.text, message.message_id))
            handle_comment(message, comment_message)
        else:
            print("this message forwarded message's comment already was answered")
    else:
        if message.forward_from is None:
            get_calendar(message)
            # if message.reply_to_message:
            #     bot.send_message(message.chat.id, "[{}] – {}!".format(message.reply_to_message.text, message.text),
            #                      reply_markup=keyboard_trello) TODO что это?
        else:
            print("this is a forwarded message without comment")
        pass


def handle_comment(message, comment_message):
    keyboard_week = telebot.types.ReplyKeyboardMarkup(True).row("Текущая неделя", "Следующая неделя")
    bot.send_message(message.chat.id, 'Выберите неделю', reply_markup=keyboard_week)
    keyboard_trello = types.InlineKeyboardMarkup()
    trello_send_button = types.InlineKeyboardButton(text="Отправить в Trello", url='https://trello.com')
    keyboard_trello.add(trello_send_button)
    bot.send_message(message.chat.id, "[{}] – {}!".format(message.text, comment_message.text),
                     reply_markup=keyboard_trello)


def get_calendar(message):
    token_path = utils.get_google_token_path(message.chat.id)
    if not os.path.exists(token_path):
        bot.answer_callback_query(message.chat.id, 'вы не авторизовались. используйте /start для авторизации')
        return
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    try:
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                bot.send_message(message.chat.id, 'вы не авторизовались. используйте /start для авторизации')
                return

        service = build('calendar', 'v3', credentials=creds)
        day_start_week, day_end_week, now = start_end_week()

        if message.text.lower() == '/get' or message.text.lower() == "текущая неделя":
            events_result = service.events().list(calendarId='primary', timeMin=now,
                                                  timeMax=day_start_week, singleEvents=True,
                                                  orderBy='startTime').execute()
            events = events_result.get('items', [])
            if not events:
                bot.send_message(message.chat.id, 'No upcoming events found.')
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                start_format = parse(start).date().strftime("%d.%m.%Y") + ' ' + parse(start).strftime("%H:%M")
                bot.send_message(message.chat.id, start_format + " – " + event['summary'])
        elif message.text.lower() == '/get_next' or message.text.lower() == "следующая неделя":
            events_result = service.events().list(calendarId='primary', timeMin=day_start_week,
                                                  timeMax=day_end_week, singleEvents=True,
                                                  orderBy='startTime').execute()
            events = events_result.get('items', [])
            if not events:
                bot.send_message(message.chat.id, 'No upcoming events found.')
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                start_format = parse(start).date().strftime("%d.%m.%Y") + ' ' + parse(start).strftime("%H:%M")
                bot.send_message(message.chat.id, start_format + " – " + event['summary'])
        # else:
        #     bot.send_message(message.chat.id, "Выберите неделю.\nТекущая /get .\n" \
        #                      + "Следующая /get_next ", \
        #                      reply_markup=keyboard_week)

    except Exception as e:
        bot.send_message(message.chat.id, "Войдите в Google аккаунт")
        print(str(e))


def get_google_auth_url():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES)
    flow.redirect_uri = redirect_url
    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')
    return authorization_url


def roundTime(dt=None, roundTo=60):
    """Round a datetime object to any time laps in seconds
   dt : datetime.datetime object, default now.
   roundTo : Closest number of seconds to round to, default 1 minute.
   Author: Thierry Husson 2012 - Use it as you want but don't blame me.
   """
    if dt == None: dt = datetime.datetime.now()
    seconds = (dt.replace(tzinfo=None) - dt.min).seconds
    rounding = (seconds + roundTo / 2) // roundTo * roundTo
    return dt + datetime.timedelta(0, rounding - seconds, -dt.microsecond)


def start_end_week():
    # currentweek
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    my_date = datetime.datetime.utcnow()
    day_number = my_date.weekday()
    delta = 6 - day_number
    day_start_week = my_date + datetime.timedelta(delta + 1)
    day_start_week = roundTime(day_start_week, roundTo=60 * 60)
    day_end_week = day_start_week + datetime.timedelta(delta + 6)
    day_end_week = roundTime(day_end_week, roundTo=60 * 60 * 24 - 1)
    day_end_week = day_end_week.isoformat() + "Z"
    day_start_week = day_start_week.isoformat() + "Z"
    return day_start_week, day_end_week, now


if __name__ == '__main__':
    bot.infinity_polling()
