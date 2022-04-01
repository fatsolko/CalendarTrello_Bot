import pyshorteners
import json
import telebot


def get_logging_trello_keyboard():
    f = open('../settings.json')
    settings = json.load(f)
    trello_key = settings["trello_key"]
    f.close()
    keyboard_login_trello = telebot.types.InlineKeyboardMarkup()
    auth_url_update_trello = 'https://trello.com/1/authorize?' \
                             f'key={trello_key}&' \
                             'expiration=never&' \
                             'name=CalendarTrello&' \
                             'scope=read,write&' \
                             'response_type=token'

    short_trello = pyshorteners.Shortener()
    short_url_trello = short_trello.tinyurl.short(auth_url_update_trello)
    url_button_trello = telebot.types.InlineKeyboardButton(text="Страница авторизации Trello", url=short_url_trello)
    keyboard_login_trello.row(url_button_trello)
    return keyboard_login_trello


def get_google_token_path(chat_id):
    return 'users/{}_google_token.json'.format(chat_id)


def find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""



