def get_google_token_path(chat_id):
    return 'users/{}_google_token.json'.format(chat_id)


def find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""



