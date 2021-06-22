import conf
from conf import TOKEN
from conf import WEBHOOK_HOST
from conf import WEBHOOK_PORT
import telebot
import requests
import pandas as pd
import time
import flask
import nltk
nltk.download('wordnet')
from nltk import WordNetLemmatizer
from random import choice
from bs4 import BeautifulSoup

WEBHOOK_URL_BASE = "https://{}:{}".format(WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/{}/".format(conf.TOKEN)

def find_meme():
    img_srcs = []
    url_redd = "https://www.reddit.com/r/PrequelMemes/top/?t=week"
    while True:
        time.sleep(1)
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

df = pd.read_csv('/home/oks110/PM_bot/static/PM_quotes.csv', sep='\t', comment='#')
cleaned_quotes = clean_quote(df['quote'])
df["Words from quote"] = cleaned_quotes

print(df)

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

@bot.message_handler(commands=["start", "hello_there"])
def say_hello(message):
    bot.send_message(message.chat.id, "Ну привет! Здесь вы можете искать любые шаблоны мемов 'приквелов' — I, II и III эпизодов франшизы 'Звёздные Войны' — на английском.\nВ этом боте есть несколько команд, которые могут понадобиться для поиска:\n/word_search — поиск шаблона мема по одному слову\n/name_search — поиск всех мемов, фразы из которых принадлежат определенному персонажу\n/characters — список персонажей, фразы которых разошлись на цитаты.\n/find_meme — данная команда пришлет какой-нибудь мем по Звёздным Войнам с Реддита.")
    bot.send_photo(message.chat.id, photo = open('/home/oks110/PM_bot/static/3/HT.png','rb'))

@bot.message_handler(commands=["word_search"])
def w_s(message):
    bot.send_message(message.chat.id, "Введите одно слово на английском\n(можно ввести как нужную форму слова, так и его лемму): ")
    bot.register_next_step_handler(message, w_suggest);

def w_suggest(message):
    ent_word = message.text.lower()
    bot.send_message(message.from_user.id, f"Отлично! Поищем '{ent_word}' в наших архивах...")
    times = 0
    for index, line in enumerate(df["words_and_lems"]):
        for word in line:
            if ent_word == word:
                photo = open(f'{df["image_path_local"][index]}','rb')
                bot.send_photo(message.chat.id, photo, timeout=10)
                times += 1
    if times == 0:
        with open("/home/oks110/PM_bot/static/2/exist_meme.png","rb") as f:
            bot.send_photo(message.chat.id, photo = f)
            bot.send_message(message.chat.id, "Мне очень жаль, но похоже, мема, который вы ищете, не существует. Возможно, наши данные неполные или же такого мема еще нет...")
    bot.send_message(message.chat.id, "Да пребудет с вами сила!\nЕсли хотите попробовать еще, просто запустите /word_search. \nТакже вы можете посмотреть на другие команды, запустив /hello_there.")

@bot.message_handler(commands=["name_search"])
def n_s(message):
    bot.send_message(message.chat.id, "Введите имя: ")
    bot.register_next_step_handler(message, n_suggest);

def n_suggest(message):
    ent_name = message.text.title()
    if ent_name == "Obiwan" or ent_name == "Obi-wan":
        ent_name = ent_name.replace("Obiwan", "Obi-Wan")
        ent_name = ent_name.replace("Obi-wan", "Obi-Wan")
    elif ent_name == "Quigon" or ent_name == "Qui-gon":
        ent_name = ent_name.replace("Quigon", "Qui-gon")
        ent_name = ent_name.replace("Qui-gon", "Qui-gon")
    elif ent_name == "Padmé":
        ent_name = ent_name.replace("Padmé", "Padme")
    elif ent_name == "Vader":
        ent_name = ent_name.replace("Vader", "Darth Vader")
    elif ent_name == "Sidious":
        ent_name = ent_name.replace("Sidious", "Darth Sidious")
    elif ent_name == "Boba":
        ent_name = ent_name.replace("Boba", "Boba Fett")
    elif ent_name == "Jango":
        ent_name = ent_name.replace("Jango", "Jango Fett")
    elif ent_name == "Dooku":
        ent_name = ent_name.replace("Dooku", "Count Dooku")
    elif ent_name == "Maul":
        ent_name = ent_name.replace("Maul", "Darth Maul")
    elif ent_name == "Nute":
        ent_name = ent_name.replace("Nute", "Nute Gunray")
    elif ent_name == "Mace" or ent_name == "Windu":
        ent_name = ent_name.replace("Mace", "Mace Windu")
        ent_name = ent_name.replace("Windu", "Mace Windu")
    if "Kenobi" in ent_name:
        ent_name = ent_name.replace("Kenobi", "Obi-Wan")
    elif "Skywalker" in ent_name:
        ent_name = ent_name.replace("Skywalker", "Anakin")
    elif "Amidala" in ent_name:
        ent_name = ent_name.replace("Amidala", "Padme")
    ntimes = 0
    bot.send_message(message.from_user.id, f"Отлично! Поищем мемы с цитатами этого персонажа!")
    for index, name in enumerate(df["character"]):
        if ent_name==name:
            with open(f'{df["image_path_local"][index]}','rb') as f:
                bot.send_photo(message.chat.id, photo = f)
                ntimes += 1
    if ntimes == 0:
        bot.send_message(message.chat.id, "Возможно, вы ввели имя не совсем корректно или же цитаты этого персонажа не считаются достаточно мемными. А может быть, наши данные неполные... Посмотрите список персонажей, цитаты которых точно можно встретить в мемах: /characters")
    bot.send_message(message.chat.id, "Да пребудет с вами сила!\nЕсли хотите попробовать еще, просто запусти /name_search.\nТакже вы можете посмотреть на другие команды, запустив /hello_there.")

@bot.message_handler(commands=["characters"])
def characters(message):
    chars = '\n'.join(sorted(list(set(list(df['character'])))))
    print(chars)
    bot.send_message(message.chat.id, chars)

@bot.message_handler(commands=["find_meme"])
def meme(message):
    bot.send_message(message.chat.id, "Ищем мем, это может занять некоторое время...")
    link = find_meme()
    bot.send_message(message.chat.id, link)
    bot.send_message(message.chat.id, "Да пребудет с вами сила!\nЕсли хотите еще, нажмите на /find_meme. Другие команды вы можете найти в /hello_there.")

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
