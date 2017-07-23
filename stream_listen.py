# -*-coding:utf-8-*-



import requests
import json
import websocket
import _thread
import time
import random
import threading
import datetime
import telebot
from telebot import types
import logging



logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.DEBUG, filename=u'mylog.log')



TELEGRAM_API_TOKEN = ''
my_servise_token = ""
bot = telebot.TeleBot(TELEGRAM_API_TOKEN)


# If need get VK API action
# my_user_token = ""
# import vk
# get token
# https://oauth.vk.com/authorize?client_id=ID_APP&scope=streaming,offline&redirect_uri=http://api.vk.com/blank.html&display=page&response_type=token
# http://api.vk.com/blank.html#access_token=&expires_in=0&user_id=




def _send_post(msg):
    bot.send_message(chatID, msg)


def _send(msg):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add('Мои интересы', 'Очистить список интересов', 'Добавить')

    msg = bot.send_message(chatID, msg, reply_markup=markup)
    bot.register_next_step_handler(msg, process_step)


@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    global chatID
    chatID = message.chat.id
    hello_test = 'Привет, %s! Я бот использующий VK Streaming API!' % message.from_user.first_name
    _send(hello_test)


def process_step(message):
    if message.text == 'Мои интересы':
        _send(get_rules_list())

    if message.text == 'Очистить список интересов':
        _send(clear_rules_list())

    if message.text == 'Добавить':
        msg = bot.send_message(chatID, "Что добавить?")
        bot.register_next_step_handler(msg, add_rule_handler)



def add_rule_handler(message):
    new_rule = set_my_rules(message.text)
    if new_rule:
        _send("Successful")
    else:
        logging.debug("Error add rules")
        _send("Error")


def get_streaming_server_key(token):
    request_url = "https://api.vk.com/method/streaming.getServerUrl?access_token={}&v=5.64".format(token)

    logging.debug(">>>> request url:"+request_url)

    r = requests.get(request_url)
    data = r.json()

    return {"server":data["response"]["endpoint"],"key":data["response"]["key"]}


def get_my_rules():
    r = requests.get("https://{}/rules?key={}".format(stream["server"], stream["key"]))
    data = r.json()
    if data['code'] != 200:
        return False

    return data['rules']

def del_my_rules(tag):
    headers = {'content-type': 'application/json'}
    rule_params = {"tag":tag}
    r = requests.delete("https://{}/rules?key={}".format(stream["server"], stream["key"]), data=json.dumps(rule_params), headers=headers)
    data = r.json()

    return data['code'] == 200

def set_my_rules(value):
    rule_params = {"rule":{"value":value,"tag":'tag_'+str(random.randint(11111, 99999))}}

    headers = {'content-type': 'application/json'}

    r = requests.post("https://{}/rules?key={}".format(stream["server"], stream["key"]), data=json.dumps(rule_params), headers=headers)
    data = r.json()
    return data['code'] == 200


def listen_stream():
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://{}/stream?key={} ".format(stream["server"], stream["key"]),
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    #ws.run_forever()

    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()



def on_message(ws, message):
    print(">>>> receive message:", message)

    message = json.loads(message)

    if not message['code']:
        return

    if not message['event']['event_type'] or message['event']['event_type'] != 'post':
        return

    post = message['event']['event_type'] +"\n"+message['event']['text'].replace("<br>", "\n") +"\n\n"+ message['event']['event_url']

    # if need send photo
    # if message['event']['attachments']:
    #     if message['event']['attachments'][0]['type'] == 'photo':
    #         print(message['event']['attachments'][0]['photo']['photo_604'])
    #         local_image_file = save_image(message['event']['attachments'][0]['photo']['photo_604'])
    #         photo = open(local_image_file, 'rb')
    #         bot.send_photo(chatID, photo, post)



    _send_post(post)


def on_error(ws, error):
    print(">>>> error thead:",error)

def on_close(ws):
    print(">>>> close thead")

def on_open(ws):
    print(">>>> open thead")




def get_rules_list():
    rules = get_my_rules()
    if rules:
        return "\n".join([str(rule['value']) for rule in rules])
    else:
        logging.debug("Error get rules list")
        return 'Error'


def clear_rules_list():
    rules = get_my_rules()
    if rules:
        for rule in rules:
            del_my_rules(rule['tag'])

        return "Successful"

    else:
        logging.debug("Error clear rules list")
        return 'Error'




if __name__ == '__main__':
    try:

        chatID = 0
        stream = get_streaming_server_key(my_servise_token)
        listen_stream()

        bot.polling(none_stop=True)


    except Exception as e:
        logging.exception("error start")

