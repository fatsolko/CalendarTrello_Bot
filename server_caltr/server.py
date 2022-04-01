import os
import ssl
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from requests.structures import CaseInsensitiveDict
from utils_server import *
from pages import *

print('Python %s on %s' % (sys.version, sys.platform))
sys.path.extend(['D:\\Programming\\Python\\CalendarTrelloBot', 'D:\\Programming\\Python\\pyMQ', 'D:/Programming/Python/CalendarTrelloBot'])


f = open('../credentials.json')
credentials = json.load(f)["web"]
client_id = credentials["client_id"]
client_secret = credentials["client_secret"]
f.close()

f = open('../settings.json')
settings = json.load(f)
bot_token = settings["bot_token"]
redirect_url = settings["redirect_url_localhost"] #TODO settings["redirect_url"]
ip = settings["ip"]
port = settings["port"]
bot_link = settings["bot_link"]
f.close()

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

bot = telebot.TeleBot(bot_token)


def send_token_request(code):
    url = "https://oauth2.googleapis.com/token"
    headers = CaseInsensitiveDict()
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    data = "code={}&client_id={}&client_secret={}&redirect_uri={}&grant_type=authorization_code" \
        .format(code, client_id, client_secret, redirect_url)
    response = requests.post(url, headers=headers, data=data)
    j = response.json()
    print(j)
    refresh_token = "no_token"
    access_token = "no_token"
    if "access_token" in j:
        access_token = j["access_token"]
        print(access_token)
    if "refresh_token" in j:
        refresh_token = j["refresh_token"]
        print(refresh_token)
    return access_token, refresh_token


def notify_success_google_auth(chat_id, success):
    keyboard_login_trello = get_logging_trello_keyboard()
    hideBoard = telebot.types.ReplyKeyboardRemove()
    if success:
        bot.send_message(chat_id, 'Авторизация через Google произошла успешно.\n\nВойдите через Trello '
                                  'аккаунт по ссылке ниже, скопируйте оттуда код-токен'
                                  ' и напишите боту вставив код с командой через пробел.\n '
                                  'Пример:\n\n/token 132fv6asd7da849ff',
                         reply_markup=keyboard_login_trello)
    else:
        msg = "Похоже, вы уже логинились. Если хотите перелогиниться в этот аккаунт, " \
              + "запретите доступ приложению CalendarTrello по ссылке https://myaccount.google.com/u/0/permissions и " \
              + "попробуйте еще раз: /start"
        bot.send_message(chat_id, msg, reply_markup=hideBoard)


class RequestHandler(BaseHTTPRequestHandler):
    def do_get(self):
        print('got request for ' + self.path)
        request_ip = self.client_address[0]
        if self.path.startswith("/login"):
            chat_id = int(find_between(self.path, 'user=', '&auth_link'))
            url = self.path.split("&auth_link=", 1)[1]
            j = {"chat_id": chat_id}
            with open("users/{}.json".format(request_ip), "w") as outfile:
                json.dump(j, outfile)
            web_page = first_page.replace("{url1}", url).replace("{url2}", url)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes(web_page, "utf-8"))
            self.wfile.flush()

        elif self.path.startswith("/redirect"):
            user_id_path = 'users/{}.json'.format(request_ip)
            if not os.path.exists(user_id_path):
                pass
            user_id_file = open(user_id_path)
            chat_id = json.load(user_id_file)["chat_id"]
            code = find_between(self.path, "code=", "&scope")
            access_token, refresh_token = send_token_request(code)
            if access_token == 'no_token' or refresh_token == 'no_token':
                notify_success_google_auth(chat_id, False)
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(bytes(redirect_new_page, "utf-8"))
                self.wfile.flush()
                return
            print(access_token)
            print(refresh_token)
            notify_success_google_auth(chat_id, True)
            j = {
                'token': access_token,
                'refresh_token': refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
                "scopes": SCOPES
            }
            with open(get_google_token_path(chat_id), "w") as outfile:
                json.dump(j, outfile, sort_keys=True, indent=4)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes(redirect_new_page, "utf-8"))
            self.wfile.flush()
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes(error_page, "utf-8"))
            self.wfile.flush()

    def do_post(self):
        pass


if __name__ == "__main__":
    HTTPserver = HTTPServer((ip, port), RequestHandler)
    if port == 443:
        HTTPserver.socket = ssl.wrap_socket(HTTPserver.socket, keyfile='/etc/letsencrypt/live/fatsolko.xyz/privkey.pem',
                                            certfile='/etc/letsencrypt/live/fatsolko.xyz/fullchain.pem',
                                            server_side=True)
    HTTPserver.serve_forever()

