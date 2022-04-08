import requests
from telebot import types
import google_auth_oauthlib.flow
from dateutil.parser import *
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from utils_bot import *
from pymongo_utils import *
from dotenv import load_dotenv

load_dotenv()

CREDENTIALS = os.getenv('CREDENTIALS')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
CLIENT_ID = os.getenv('CLIENT_ID')
PROJECT_ID = os.getenv('PROJECT_ID')
AUTH_URI = os.getenv('AUTH_URI')
TOKEN_URI = os.getenv('TOKEN_URI')
AUTH_PROVIDER_X509_CERT_URL = os.getenv('AUTH_PROVIDER_X509_CERT_URL')
REDIRECT_URIS = os.getenv('REDIRECT_URIS')

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

BOT_TOKEN = os.getenv('BOT_TOKEN')
TRELLO_KEY = os.getenv('TRELLO_KEY')
REDIRECT_URI = os.getenv('REDIRECT_URI')
REDIRECT_URI_LOCALHOST = os.getenv('REDIRECT_URI_LOCALHOST')
IP = os.getenv('IP')
PORT = os.getenv('PORT')

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
print(BOT_TOKEN)
bot = telebot.TeleBot(BOT_TOKEN)
# HOST = f"{IP}:{PORT}"
HOST = "https://fatsolko.xyz"
keyboard_login_trello = get_logging_trello_keyboard()


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    keyboard_login = types.InlineKeyboardMarkup()
    auth_url = get_google_auth_url()
    auth_url_update = f'{HOST}/login?user={chat_id}&auth_link={auth_url}'
    short = pyshorteners.Shortener()
    short_url = short.tinyurl.short(auth_url_update)
    url_button = types.InlineKeyboardButton(text="Страница Google авторизации",
                                            url=short_url)
    keyboard_login.row(url_button)
    bot.send_message(chat_id,
                     "Перейдите по ссылке ниже для входа через Google аккаунт.",
                     reply_markup=keyboard_login)


def notify_success_google_auth(chat_id, success):
    if success:
        bot.send_message(chat_id,
                         'Авторизация через Google произошла успешно.\n\nВойдите через Trello '
                         'аккаунт по ссылке ниже, скопируйте оттуда код-токен'
                         ' и напишите боту вставив код с командой через пробел. '
                         'Пример:\n/token 132fv6asd7da849ff',
                         reply_markup=keyboard_login_trello)

    else:
        msg = "Похоже, вы уже логинились. Если хотите перелогиниться в этот аккаунт, " \
              + "запретите доступ приложению CalendarTrello по ссылке" \
                " https://myaccount.google.com/u/0/permissions и попробуйте еще раз: /start"
        bot.send_message(chat_id, msg, reply_markup=hideBoard)


@bot.message_handler(commands=['trello_login'])
def login(message):
    chat_id = message.chat.id
    bot.send_message(chat_id,
                     'Войдите через Trello '
                     'аккаунт по ссылке ниже, скопируйте оттуда код-токен'
                     ' и напишите боту вставив код с командой через пробел. '
                     'Пример:\n/token 132fv6asd7da849ff',
                     reply_markup=keyboard_login_trello)


@bot.message_handler(commands=['help'])
def help_msg(message):
    chat_id = message.chat.id
    bot.send_message(chat_id,
                     "Введите /get или Текущая неделя для получения событий этой недели.\n"
                     + "Для получения событий следующей недели введите /get_next или Следующая неделя",
                     reply_markup=keyboard_week)


@bot.message_handler(commands=['token'])
def token(message):
    chat_id = message.chat.id
    token_trello = (find_after(message.text, '/token '))
    j = {
        "trello_token": token_trello
    }
    set_user_db_data(chat_id, j)
    if token_trello == "":
        bot.send_message(chat_id,
                         "Скопируйте и вставьте токен со страницы авторизации"
                         " Trello по примеру:\n"
                         "/token 132fvse6asd7af",
                         reply_markup=keyboard_token)

    else:
        bot.send_message(chat_id,
                         "Токен получен.\n"
                         "/set_board чтобы выбрать доску\n"
                         "/set_list чтобы выбрать лист",
                         reply_markup=hideBoard)


@bot.message_handler(commands=['set_board'])
def set_board(message):
    chat_id = message.chat.id
    try:
        trello_token = get_user_db_data(chat_id, "trello_token")
        url = f"https://api.trello.com/1/members/me/boards?fields=name,url&key={TRELLO_KEY}&token={trello_token}"
        print(url)
        boards_list = requests.get(url).json()
        print(boards_list)
        boards_dict = {"boards_list": boards_list}
        keyboard = types.InlineKeyboardMarkup()
        set_user_db_data(chat_id, boards_dict)
        # boards = user_data["boards"]
        for board in boards_list:
            board_id = board["id"]
            board_name = board["name"]
            callback_data = f'id = {board_id}'
            button = types.InlineKeyboardButton(f'{board_name}', callback_data=callback_data)
            keyboard.row(button)
        if len(boards_list) > 0:
            bot.send_message(chat_id,
                             "Выберите доску:",
                             reply_markup=keyboard)
        else:
            bot.send_message(chat_id,
                             "У вас нет досок",
                             reply_markup=hideBoard)
    except KeyError as e:
        if e == 'selected_board':
            bot.send_message(chat_id,
                             "Вы не выбрали доску \n /set_board",
                             reply_markup=hideBoard)
    except ValueError as v:
        bot.send_message(chat_id,
                         "Неверный токен. Скопируйте и вставьте токен со страницы авторизации"
                         " Trello по примеру:\n"
                         "/token 132fvse6asd7af",
                         reply_markup=keyboard_login_trello)
        print(str(v))


@bot.message_handler(commands=['set_list'])
def set_board(message):
    chat_id = message.chat.id
    try:
        selected_board = get_user_db_data(chat_id, "selected_board")
        print(selected_board)
        selected_board_id = selected_board['id']
        trello_token = get_user_db_data(chat_id, "trello_token")
        list_url = f"https://api.trello.com/1/boards/{selected_board_id}/lists?key={TRELLO_KEY}&token={trello_token}"
        lists = requests.get(list_url).json()
        print(lists)
        selected_board["lists"] = lists
        for k, v in selected_board.items():
            print(k, v)
        selected_board = {"selected_board": selected_board}
        set_user_db_data(chat_id, selected_board)
        keyboard = types.InlineKeyboardMarkup()
        for board_list in lists:
            list_id = board_list["id"]
            list_name = board_list["name"]
            callback_data = f'list_id = {list_id}'
            button = types.InlineKeyboardButton(f'{list_name}', callback_data=callback_data)
            keyboard.row(button)
        if len(lists) > 0:
            bot.send_message(chat_id, "Выберите лист:", reply_markup=keyboard)
        else:
            bot.send_message(chat_id, "У вас нет листов", reply_markup=hideBoard)
    except KeyError as e:
        bot.send_message(chat_id, "Вы не выбрали доску \n /set_board", reply_markup=hideBoard)
        print("err" + str(e))


@bot.callback_query_handler(func=lambda call: call.data.startswith('id = '))
def handle_set_board(call):
    board_id = find_after(call.data, 'id = ')
    chat_id = call.message.chat.id
    boards = get_user_db_data(chat_id, "boards_list")
    for board in boards:
        if board["id"] == board_id:
            name = board['name']
            selected_board = {"selected_board": {"id": board_id,
                                                 "name": name}}
            set_user_db_data(chat_id, selected_board)
            bot.answer_callback_query(call.id)
            bot.send_message(chat_id, f"Выберана доска: {name}.\nВыберите лист /set_list")


@bot.callback_query_handler(func=lambda call: call.data.startswith('list_id = '))
def handle_set_list(call):
    list_id = find_after(call.data, 'list_id = ')
    chat_id = call.message.chat.id
    lists = get_user_db_data(chat_id, "selected_board")['lists']
    for board_list in lists:
        if board_list["id"] == list_id:
            name = board_list['name']
            selected_list = {"selected_list": {"id": list_id,
                                               "name": name}}
            set_user_db_data(chat_id, selected_list)
            bot.answer_callback_query(call.id)
            bot.send_message(chat_id,
                             f"Выберан лист: {name}.\n"
                             "Ответьте на появившееся событие после нажатия на одну из команд ниже,"
                             " чтобы добавить к нему комментарий.\n"
                             "/get показать события текущей недели \n"
                             "/get_next показать события следующей недели",
                             reply_markup=keyboard_week)


@bot.message_handler(func=lambda m: True)
def handle_message(message):
    chat_id = message.chat.id
    creds_collection = db['user creds']
    doc_exist = creds_collection.count_documents({"chat_id": str(chat_id)}) > 0
    if not doc_exist:
        start(message)
        return
    if not doc_exist:
        notify_success_google_auth(chat_id, True)
        return
    if message.reply_to_message is not None and message.reply_to_message.from_user.is_bot:  # TODO реплай ивента или нет
        handle_reply(message)
    else:
        get_calendar(message)


def handle_reply(message):
    chat_id = message.chat.id
    try:
        selected_board = get_user_db_data(chat_id, "selected_board")
        selected_list = get_user_db_data(chat_id, "selected_list")
        trello_token = get_user_db_data(chat_id, "trello_token")
        if len(selected_board) > 0:
            selected_list_id = selected_list["id"]
            name_event = find_after(message.reply_to_message.text, " – ")
            url = f"https://api.trello.com/1/cards?&" \
                  f"key={TRELLO_KEY}&" \
                  f"token={trello_token}&" \
                  f"name={name_event}&" \
                  f"desc={message.text}&" \
                  f"idList={selected_list_id}"
            short_url = pyshorteners.Shortener()
            short_post_url = short_url.tinyurl.short(url)
            keyboard_send_trello = types.InlineKeyboardMarkup()
            name_selected_board = selected_board['name']
            name_selected_list = selected_list['name']
            button_text = f"Отправить на доску \"{name_selected_board}\" в лист \"{name_selected_list}\""
            callback_data = f"send={short_post_url}"
            url_button = types.InlineKeyboardButton(text=button_text, callback_data=callback_data)
            keyboard_send_trello.row(url_button)
            bot.send_message(message.chat.id, f'{message.text} – {message.reply_to_message.text}',
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
    # print(url)
    # print(str(response))
    if str(response) == '<Response [200]>':
        bot.send_message(chat_id, "Готово", reply_markup=hideBoard)
    bot.answer_callback_query(call.id)


def get_calendar(message):
    chat_id = message.chat.id
    if not message.text.startswith("/get") and not message.text.endswith("текущая неделя"):
        return
    user_creds = get_creds_db_data(chat_id, 'creds')
    print(user_creds)
    creds = Credentials.from_authorized_user_info(user_creds, SCOPES)
    try:
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                bot.send_message(chat_id, 'Вы не авторизовались. Введите /start для авторизации')
                return

        service = build('calendar', 'v3', credentials=creds)
        day_start_week, day_end_week, now = start_end_week()

        if message.text.lower() == '/get' or message.text.lower() == "текущая неделя":
            # calendars = service.calendarList().get(calendarId='den2434358@gmail.com').execute()
            # print(calendars)

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
        print("err" + str(e))
        bot.send_message(message.chat.id, "Войдите в Google аккаунт")


def get_google_auth_url():
    user_creds = {"web":
        {
            "client_id": CLIENT_ID,
            "project_id": PROJECT_ID,
            "auth_uri": AUTH_URI,
            "token_uri": TOKEN_URI,
            "auth_provider_x509_cert_url": AUTH_PROVIDER_X509_CERT_URL,
            "client_secret": CLIENT_SECRET,
            "redirect_uris": REDIRECT_URIS
        }
    }
    flow = google_auth_oauthlib.flow.Flow.from_client_config(user_creds, SCOPES)
    # flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
    #     '../credentials.json',
    #     scopes=SCOPES)

    flow.redirect_uri = REDIRECT_URI
    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')
    return authorization_url


if __name__ == '__main__':
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
