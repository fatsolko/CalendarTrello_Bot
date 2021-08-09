import json
import datetime
import telebot

keyboard_week = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True,
                                                  resize_keyboard=True,
                                                  input_field_placeholder='/get or /get_now ').row("Текущая неделя", "Следующая неделя")



def find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""


def find_after(s, first):
    try:
        start = s.index(first) + len(first)
        return s[start:]
    except ValueError:
        return ""


def get_google_token_path(chat_id):
    return 'users/{}_google_token.json'.format(chat_id)


def get_trello_token_path(chat_id):
    return 'users/{}_trello_token.json'.format(chat_id)

def get_trello_token(chat_id):
    return json.load(open(get_trello_token_path(chat_id)))["token"]


def get_user_data(chat_id):
    return json.load(open('users/{}.json'.format(chat_id)))


def save_user_data(chat_id, data):
    with open("users/{}.json".format(chat_id), "w") as outfile:
        json.dump(data, outfile)

def start_end_week():
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
