import requests
from telebot import types
import google_auth_oauthlib.flow
from dateutil.parser import *
import os.path
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from utils_app import *


f = open('../credentials.json')
credentials = json.load(f)["web"]
client_id = credentials["client_id"]
client_secret = credentials["client_secret"]
f.close()

f = open('../settings.json')
settings = json.load(f)
bot_token = settings["bot_token"]
trello_key = settings["trello_key"]
redirect_url = settings["redirect_url_localhost"]  # TODO settings["redirect_url"]
f.close()

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
bot = telebot.TeleBot(bot_token)
site = "http://localhost:5000"
# TODO site = "https://fatsolko.xyz"
keyboard_login_trello = get_logging_trello_keyboard()


@bot.message_handler(commands=['start'])
def start(message):
    keyboard_login = types.InlineKeyboardMarkup()
    auth_url = get_google_auth_url()
    auth_url_update = '{}/login?user={}&auth_link={}'.format(site, message.chat.id, auth_url)
    short = pyshorteners.Shortener()
    short_url = short.tinyurl.short(auth_url_update)
    url_button = types.InlineKeyboardButton(text="Страница Google авторизации", url=short_url)
    keyboard_login.row(url_button)
    bot.send_message(message.chat.id, "Перейдите по ссылке ниже для входа через Google аккаунт.",
                     reply_markup=keyboard_login)


def notify_success_google_auth(chat_id, success):
    if success:
        bot.send_message(chat_id, 'Авторизация через Google произошла успешно.\n\nВойдите через Trello '
                                  'аккаунт по ссылке ниже, скопируйте оттуда код-токен'
                                  ' и напишите боту вставив код с командой через пробел. '
                                  'Пример:\n/token 132fv6asd7da849ff', reply_markup=keyboard_login_trello)

    else:
        msg = "Похоже, вы уже логинились. Если хотите перелогиниться в этот аккаунт, " \
              + "запретите доступ приложению CalendarTrello по ссылке https://myaccount.google.com/u/0/permissions и " \
              + "попробуйте еще раз: /start"
        bot.send_message(chat_id, msg, reply_markup=hideBoard)


@bot.message_handler(commands=['trello_login'])
def login(message):
    bot.send_message(message.chat.id, 'Войдите через Trello '
                                      'аккаунт по ссылке ниже, скопируйте оттуда код-токен'
                                      ' и напишите боту вставив код с командой через пробел. '
                                      'Пример:\n/token 132fv6asd7da849ff',
                     reply_markup=keyboard_login_trello)


@bot.message_handler(commands=['help'])
def help_msg(message):
    if not os.path.exists(get_google_token_path(message.chat.id)):
        start(message)
        return
    if not os.path.exists(get_trello_token_path(message.chat.id)):
        notify_success_google_auth(message.chat.id, True)
        return

    bot.send_message(message.chat.id, "Введите /get или Текущая неделя для получения событий этой недели.\n"
                     + "Для получения событий следующей недели введите /get_next или Следующая неделя",
                     reply_markup=keyboard_week)


@bot.message_handler(commands=['token'])
def token(message):
    token_trello = (find_after(message.text, '/token '))
    j = {
        "token": token_trello
    }
    with open(get_trello_token_path(message.chat.id), "w") as outfile:
        json.dump(j, outfile, sort_keys=True, indent=4)

    data = {}
    save_user_data(message.chat.id, data)
    if token_trello == "":
        bot.send_message(message.chat.id, "Скопируйте и вставьте токен со страницы авторизации"
                                          " Trello по примеру:\n"
                                          "/token 132fvse6asd7af",
                         reply_markup=keyboard_token)

    else:
        bot.send_message(message.chat.id, "Токен получен.\n"
                                          "/set_board чтобы выбрать доску\n"
                                          "/set_list чтобы выбрать лист", reply_markup=hideBoard)


@bot.message_handler(commands=['set_board'])
def set_board(message):
    try:
        url = "https://api.trello.com/1/members/me/boards?fields=name,url&key={}&token={}".format(
            trello_key,
            get_trello_token(message.chat.id))
        print(url)
        boards = requests.get(url).json()
        keyboard = types.InlineKeyboardMarkup()
        user_data = get_user_data(message.chat.id)
        user_data['boards'] = boards
        save_user_data(message.chat.id, user_data)
        boards = user_data["boards"]
        for board in boards:
            board_id = board["id"]
            board_name = board["name"]
            callback_data = 'id = {}'.format(board_id)
            button = types.InlineKeyboardButton('{}'.format(board_name), callback_data=callback_data)
            keyboard.row(button)
        if len(boards) > 0:
            bot.send_message(message.chat.id, "Выберите доску:", reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, "У вас нет досок", reply_markup=hideBoard)
    except KeyError as e:
        if e == 'selected_board':
            bot.send_message(message.chat.id, "Вы не выбрали доску \n /set_board", reply_markup=hideBoard)
    except ValueError as v:
        bot.send_message(message.chat.id, "Неверный токен. Скопируйте и вставьте токен со страницы авторизации"
                                          " Trello по примеру:\n"
                                          "/token 132fvse6asd7af",
                         reply_markup=keyboard_login_trello)
        print(str(v))


@bot.message_handler(commands=['set_list'])
def set_board(message):
    try:
        selected_board = get_user_data(message.chat.id)["selected_board"]
        selected_board_id = selected_board['id']
        trello_token = get_trello_token(message.chat.id)
        list_url = "https://api.trello.com/1/boards/{}/lists?key={}&token={}".format(
            selected_board_id,
            trello_key,
            trello_token
        )
        print(list_url)
        lists = requests.get(list_url).json()
        list_id = lists
        selected_board['lists'] = list_id
        user_data = get_user_data(message.chat.id)
        user_data['selected_board'] = selected_board
        save_user_data(message.chat.id, user_data)
        keyboard = types.InlineKeyboardMarkup()
        user_data['lists'] = lists
        for board_list in lists:
            list_id = board_list["id"]
            list_name = board_list["name"]
            callback_data = 'list_id = {}'.format(list_id)
            button = types.InlineKeyboardButton('{}'.format(list_name), callback_data=callback_data)
            keyboard.row(button)
        if len(lists) > 0:
            bot.send_message(message.chat.id, "Выберите лист:", reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, "У вас нет листов", reply_markup=hideBoard)
    except KeyError as e:
        bot.send_message(message.chat.id, "Вы не выбрали доску \n /set_board", reply_markup=hideBoard)
        print(str(e))


@bot.callback_query_handler(func=lambda call: call.data.startswith('id = '))
def handle_set_board(call):
    board_id = find_after(call.data, 'id = ')
    chat_id = call.message.chat.id
    user_data = get_user_data(chat_id)
    boards = user_data["boards"]
    for board in boards:
        if board["id"] == board_id:
            name = board['name']
            new_data = get_user_data(chat_id)
            new_data["selected_board"] = board
            save_user_data(chat_id, new_data)
            bot.send_message(chat_id, "Выберана доска: {}.\nВыберите лист /set_list".format(name))


@bot.callback_query_handler(func=lambda call: call.data.startswith('list_id = '))
def handle_set_list(call):
    list_id = find_after(call.data, 'list_id = ')
    chat_id = call.message.chat.id
    user_data = get_user_data(chat_id)
    lists = user_data['selected_board']["lists"]
    for list_count in lists:
        if list_count["id"] == list_id:
            name = list_count['name']
            new_data = get_user_data(chat_id)
            new_data["selected_board"]["selected_list"] = list_count
            save_user_data(chat_id, new_data)
            bot.send_message(chat_id, "Выберан лист: {}.\n"
                                      "Ответьте на появившееся событие после нажатия на одну из команд ниже,"
                                      " чтобы добавить к нему комментарий.\n"
                                      "/get показать события текущей недели \n"
                                      "/get_next показать события следующей недели"
                             .format(name),
                             reply_markup=keyboard_week)


@bot.message_handler(func=lambda m: True)
def handle_message(message):
    chat_id = message.chat.id
    if not os.path.exists(get_google_token_path(chat_id)):
        start(message)
        return
    if not os.path.exists(get_trello_token_path(chat_id)):
        notify_success_google_auth(chat_id, True)
        return
    if message.reply_to_message is not None and message.reply_to_message.from_user.is_bot:  # TODO реплай ивента или нет
        handle_reply(message)
    else:
        get_calendar(message)


def handle_reply(message):
    try:
        user_data = get_user_data(message.chat.id)
        if len(user_data) > 0:
            selected_list_id = user_data['selected_board']['selected_list']['id']
            name_event = find_after(message.reply_to_message.text, " – ")
            url = "https://api.trello.com/1/cards?&key={}&token={}&name={}&desc={}&idList={}".format(
                trello_key,
                get_trello_token(message.chat.id),
                name_event,  # TODO get calendar event name
                message.text,
                selected_list_id
            )

            short_url = pyshorteners.Shortener()
            short_post_url = short_url.tinyurl.short(url)
            keyboard_send_trello = types.InlineKeyboardMarkup()
            name_selected_board = user_data['selected_board']["name"]
            name_selected_list = user_data['selected_board']["selected_list"]['name']
            button_text = "Отправить на доску \"{}\" в лист \"{}\"".format(name_selected_board, name_selected_list)
            callback_data = "send={}".format(short_post_url)
            url_button = types.InlineKeyboardButton(text=button_text, callback_data=callback_data)
            keyboard_send_trello.row(url_button)
            bot.send_message(message.chat.id, '{} – {}'.format(message.text, message.reply_to_message.text),
                             reply_markup=keyboard_send_trello)
        else:
            bot.send_message(message.chat.id, "Вы не выбрали доску \n /set_board", reply_markup=hideBoard)
    except KeyError as e:
        if e == 'selected_board':
            bot.send_message(message.chat.id, "Вы не выбрали доску \n /set_board", reply_markup=hideBoard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('send='))
def callback_inline(call):
    url = find_after(call.data, 'send=')
    chat_id = call.message.chat.id
    response = requests.post(url)
    print(url)
    print(str(response))
    if str(response) == '<Response [200]>':
        bot.send_message(chat_id, "Готово", reply_markup=hideBoard)


def get_calendar(message):
    if not message.text.startswith("/get") and not message.text.endswith("неделя"):
        return
    token_path = get_google_token_path(message.chat.id)
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    try:
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                bot.send_message(message.chat.id, 'Вы не авторизовались. Введите /start для авторизации')
                return

        service = build('calendar', 'v3', credentials=creds)
        day_start_week, day_end_week, now = start_end_week()

        if message.text.lower() == '/get' or message.text.lower() == "текущая неделя":
            calendars = service.calendarList().get(calendarId='den2434358@gmail.com').execute()
            print(calendars)

            events_result = service.events().list(calendarId='primary', timeMin=now,
                                                  timeMax=day_start_week, singleEvents=True,
                                                  orderBy='startTime').execute()
            events = events_result.get('items', [])

        elif message.text.lower() == '/get_next' or message.text.lower() == "следующая неделя":
            events_result = service.events().list(calendarId='primary', timeMin=day_start_week,
                                                  timeMax=day_end_week, singleEvents=True,
                                                  orderBy='startTime').execute()
            events = events_result.get('items', [])
        if not events:
            bot.send_message(message.chat.id, 'Нет событий')
        for event in events:
            start_date = event['start'].get('dateTime', event['start'].get('date'))
            start_format = parse(start_date).date().strftime("%d.%m.%Y") + ' ' + parse(start_date).strftime("%H:%M")
            bot.send_message(message.chat.id, start_format + " – " + event['summary'])
    except Exception as e:
        bot.send_message(message.chat.id, "Войдите в Google аккаунт")
        print(str(e))


def get_google_auth_url():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        '../credentials.json',
        scopes=SCOPES)
    flow.redirect_uri = redirect_url
    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')
    return authorization_url


if __name__ == '__main__':
    bot.infinity_polling(timeout=10, long_polling_timeout=5)