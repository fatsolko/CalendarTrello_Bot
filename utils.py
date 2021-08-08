import json


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
