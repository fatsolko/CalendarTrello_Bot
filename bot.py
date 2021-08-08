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
trello_key = credentials["trello_key"]
f.close()
f = open('settings.json')
settings = json.load(f)
bot_token = settings["bot_token"]
redirect_url = settings["redirect_url"]
app_name = settings["app_name"]
f.close()

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
bot = telebot.TeleBot(bot_token)


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
                                 'key={}&' \
                                 'expiration=never&' \
                                 'name=CalendarTrello&' \
                                 'scope=read,write&' \
                                 'response_type=token'.format(trello_key)

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
    with open(utils.get_trello_token_path(message.chat.id), "w") as outfile:
        json.dump(j, outfile, sort_keys=True, indent=4)

    data = {}
    utils.save_user_data(message.chat.id, data)
    bot.send_message(message.chat.id, "Токен получен, все ок. /set_board чтобы выбрать доску")


@bot.message_handler(commands=['set_board'])
def set_board(message):
    url = "https://api.trello.com/1/members/me/boards?fields=name,url&key={}&token={}".format(
        trello_key,
        utils.get_trello_token(message.chat.id)
    )
    boards = requests.get(url).json()
    parsed_boards = []
    keyboard = types.InlineKeyboardMarkup()
    for board in boards:
        parsed_boards.append((board["id"], board["name"]))
        button = types.InlineKeyboardButton(board["name"],
                                            callback_data='set_board:{}'.format(board["id"]))
        keyboard.row(button)
    if len(boards) > 0:
        bot.send_message(message.chat.id, "Выберите доску:", reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, "У тебя нет досок")


@bot.callback_query_handler(func=lambda call: call.data.startswith('set_board'))
def handle_set_board(call):
    board_id = utils.find_after(call.data, "set_board:")
    chat_id = call.message.chat.id
    user_data = utils.get_user_data(chat_id)
    user_data["board"] = board_id
    utils.save_user_data(chat_id, user_data)


@bot.message_handler(func=lambda m: True)
def handle_message(message):
    if not os.path.exists(utils.get_google_token_path(message.chat.id)):
        start(message)
        return
    if not os.path.exists(utils.get_trello_token_path(message.chat.id)):
        notify_success_google_auth(message.chat.id, True)
        return

    if message.reply_to_message is not None and message.reply_to_message.from_user.is_bot:
        handle_reply(message)
    else:
        get_calendar(message)


def handle_reply(message):
    board_url = "https://api.trello.com/1/boards/{}/lists?key={}&token={}".format(
        utils.get_user_data(message.chat.id)["board"],
        trello_key,
        utils.get_trello_token(message.chat.id)
    )
    response = requests.get(board_url).json()
    bot.send_message(message.chat.id, str(response))
    url = "https://api.trello.com/1/cards?&key={}&token={}&name={}&".format(
        trello_key,
        utils.get_trello_token(message.chat.id)
    )

    # keyboard_week = telebot.types.ReplyKeyboardMarkup(True).row("Текущая неделя", "Следующая неделя")
    # bot.send_message(message.chat.id, 'Выберите неделю', reply_markup=keyboard_week)
    # keyboard_trello = types.InlineKeyboardMarkup()
    # trello_send_button = types.InlineKeyboardButton(text="Отправить в Trello", url='https://trello.com')
    # keyboard_trello.add(trello_send_button)
    # bot.send_message(message.chat.id, "[{}] – {}!".format(message.text, comment_message.text),
    #                  reply_markup=keyboard_trello)


def get_calendar(message):
    if not message.text.startswith("/get"):
        return
    token_path = utils.get_google_token_path(message.chat.id)
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
    print(bot.get_me())
    bot.infinity_polling()
