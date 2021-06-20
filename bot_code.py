import conf
from conf import *
import telebot
import requests
import pandas as pd
import time
import flask
from pymorphy2 import MorphAnalyzer
from nltk import WordNetLemmatizer
from telebot import types
from random import choice
from bs4 import BeautifulSoup

WEBHOOK_URL_BASE = "https://{}:{}".format(conf.WEBHOOK_HOST, conf.WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/{}/".format(conf.TOKEN)

def find_meme():
    img_srcs = []
    url_redd = "https://www.reddit.com/r/PrequelMemes/top/?t=month"
    while True:
        time.sleep(2)
        response = requests.get(url_redd)
        soup = BeautifulSoup(response.content, 'html.parser')
        images = soup.find_all("img", {"alt": "Post image"})
        img_srcs = [image["src"] for image in images]
        if len(img_srcs) != 0:
            meme = choice(img_srcs)
            return meme
            break

def clean_quote(quotes):
    quotes_words = []
    for quote in quotes:
        quote = quote.replace('.', '')
        quote = quote.replace(',', '')
        quote = quote.replace('!', '')
        quote = quote.replace(',', '')
        quote = quote.replace('?', '')
        quote = quote.replace('[', '')
        quote = quote.replace(']', '')
        if "bi-" not in quote:
            quote = quote.replace('-', '')
        else:
            pass
        spl_quote = quote.split()
        spl_quote = [word.lower() for word in spl_quote]
        quotes_words.append(spl_quote)
    return quotes_words

xl = pd.ExcelFile("static/SW_quotes_app.xlsx")
df = xl.parse("All memes")
cleaned_quotes = clean_quote(df['quote'])
df["Words from quote"] = cleaned_quotes

wnl = WordNetLemmatizer()

lems = []
for spl_quote in cleaned_quotes:
    quote_lems = []
    for word in spl_quote:
        if word.endswith("ing"):
            a = wnl.lemmatize(word, 'v')
            quote_lems.append(a)
        elif word == "is" or word == "am" or word == "are" or word == "were" or word == "was":
            a = wnl.lemmatize(word, 'v')
            quote_lems.append(a)
        else:
            a = wnl.lemmatize(word)
            quote_lems.append(a)
    lems.append(quote_lems)

for lems_line in lems:
    for ind, word in enumerate(lems_line):
        lems_line[ind] = word.replace("doe", "do")
        lems_line[ind] = word.replace("le", "less")
        lems_line[ind] = word.replace("ha", "have")
        if word == "wanna":
            lems_line.append("want")
        if "'s" in word:
            if "an's" not in word:
                lems_line[ind] = word.replace("'s", " is")
                lems_line[ind] = lems_line[ind].split()
            else:
                pass
        if "'re" in word:
            lems_line[ind] = word.replace("'re", " are")
            lems_line[ind] = lems_line[ind].split()
        if "n't" in word:
            if "can't" in word:
                lems_line[ind] = word.replace("can't", "can not")
                lems_line[ind] = lems_line[ind].split()
            else:
                lems_line[ind] = word.replace("n't", " not")
                lems_line[ind] = lems_line[ind].split()
        if "'ll" in word:
            lems_line[ind] = word.replace("'ll", " will")
            lems_line[ind] = lems_line[ind].split()
        if "'ve" in word:
            lems_line[ind] = word.replace("'ve", " have")
            lems_line[ind] = lems_line[ind].split()
        if "'m" in word:
            lems_line[ind] = word.replace("'m", " am")
            lems_line[ind] = lems_line[ind].split()
        if word == "whattaya":
            lems_line[ind] = word.replace("whattaya", "what do you")
            lems_line[ind] = lems_line[ind].split()

for lems_line in lems:
    for elem in lems_line:
        if type(elem) == list:
            for word in elem:
                lems_line.append(word)
            lems_line.remove(elem)

for lems_line in lems: #в одном месте remove не сработал, надо запустить еще раз...
    for elem in lems_line:
        if type(elem) == list:
            lems_line.remove(elem)

df["Lemmas"] = lems

words_and_lems = []
for i, quote in enumerate(df["Words from quote"]):
    two_lists = quote + df["Lemmas"][i]
    no_dup = list(set(two_lists))
    words_and_lems.append(no_dup)

df["words_and_lems"] = words_and_lems

bot = telebot.TeleBot(TOKEN, threaded=False)

bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL_BASE+WEBHOOK_URL_PATH)

app = flask.Flask(__name__)

@bot.message_handler(commands=["start", "help"])
def say_hello(message):
    bot.send_message(message.chat.id, "Ну привет! Здесь вы можете искать любые шаблоны мемов 'приквелов' — I, II и III эпизодов франшизы 'Звёздные Войны' — на английском.\nВ этом боте есть несколько команд, которые могут понадобиться для поиска:\n/word_search — поиск шаблона мема по одному слову \n/name_search — поиск всех мемов, фразы из которых принадлежат определенному персонажу\n/characters — список персонажей, фразы которых разошлись по цитат.\n/find_meme — данная команда пришлет тебе какой-нибудь мем по Звёздным Войнам с Реддита.")
    hello_there = open("static/3/HT.PNG", "rb")
    bot.send_photo(message.chat.id, hello_there)

@bot.message_handler(commands=["word_search"])
def w_s(message):
    bot.send_message(message.chat.id, "Введите одно слово: ")
    bot.register_next_step_handler(message, w_suggest);

def w_suggest(message):
    ent_word = message.text.lower()
    bot.send_message(message.from_user.id, f"Отлично! Поищем '{ent_word}' в наших архивах...")
    times = 0
    for index, line in enumerate(df["words_and_lems"]):
        for word in line:
            if ent_word == word:
                photo = open(f'{df["image_path_local"][index]}', 'rb')
                bot.send_photo(message.chat.id, photo)
                times += 1
    if times == 0:
        arc_nan = open("static/2/exist_meme.PNG", "rb")
        bot.send_photo(message.chat.id, arc_nan)
        bot.send_message(message.chat.id, "Мне очень жаль, но похоже, мема, который вы ищете, не существует. Возможно, наши данные неполные или же такого мема еще нет...")
    bot.send_message(message.chat.id, "Да пребудет с вами сила!\nЕсли хотите попробовать еще, просто запустите /word_search. \nТакже вы можете посмотреть на другие команды, запустив /start.")

@bot.message_handler(commands=["name_search"])
def n_s(message):
    bot.send_message(message.chat.id, "Введите имя: ")
    bot.register_next_step_handler(message, n_suggest);

def n_suggest(message):
    ent_name = message.text.title()
    if ent_name == "Obiwan" or ent_name == "Obi-wan":
        ent_name = ent_name.replace("Obiwan", "Obi-Wan")
        ent_name = ent_name.replace("Obi-wan", "Obi-Wan")
    elif ent_name == "Padmé":
        ent_name = ent_name.replace("Padmé", "Padme")
    if "Kenobi" in ent_name:
        ent_name = ent_name.replace("Kenobi", "Obi-Wan")
    elif "Skywalker" in ent_name:
        ent_name = ent_name.replace("Skywalker", "Anakin")
    elif "Amidala" in ent_name:
        ent_name = ent_name.replace("Amidala", "Padme")
    ntimes = 0
    bot.send_message(message.from_user.id, f"Отлично! Поищем мемы с цитатами этого персонажа: {ent_name}")
    for index, name in enumerate(df["character"]):
        if ent_name in name:
            photo = open(f'{df["image_path_local"][index]}', 'rb')
            bot.send_photo(message.chat.id, photo)
            ntimes += 1
    if ntimes == 0:
        bot.send_message(message.chat.id, "Возможно, вы ввели имя не совсем корректно или же цитаты этого персонажа не считаются достаточно мемными. А может быть, наши данные неполные... Посмотрите список персонажей, цитаты которых точно можно встретить в мемах: /characters")
    bot.send_message(message.chat.id, "Да пребудет с вами сила!\nЕсли хотите попробовать еще, просто запусти /name_search.\nТакже ты можешь посмотреть на другие команды, запустив /start.")

@bot.message_handler(commands=["characters"])
def meme(message):
    chars = '\n'.join(sorted(list(set(list(df['character'])))))
    print(chars)
    bot.send_message(message.chat.id, chars)

@bot.message_handler(commands=["find_meme"])
def meme(message):
    bot.send_message(message.chat.id, "Ищем мем...")
    link = find_meme()
    bot.send_message(message.chat.id, link)
    bot.send_message(message.chat.id, "Да пребудет с тобой сила!\nЕсли хочешь еще, нажми на /find_meme. Другие команды ты можешь найти в /start.")

@app.route('/', methods=['GET', 'HEAD'])
def index():
    return 'ok'

@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)

if __name__ == "__main__":
    bot.polling(none_stop=True)
