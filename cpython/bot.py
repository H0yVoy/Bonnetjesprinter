
# Cpython bot implementation
# make sure to grab the latest version from:
# https://github.com/python-escpos/python-escpos
from escpos.printer import Serial
import logging
from telegram import Update, File, PhotoSize
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

import datetime
import time
from time import sleep
from pytz import timezone  # get message timezones correct
from PIL import Image  # resizing incoming images
from sympy import preview  # latex compiling
import os  # downloaded file handling
import ujson  # for database stuff


start_text = (
    """You don't have print access yet, so I've requested it for you. You'll get a confirmation message once access has been granted"""
)

welcome_text = (
"""You now have access to print!
Type /help for a more elaborate guide
""")

help_text = (
"""Info:
With this bot you can send physical texts to Ties!
Most European character sets are supported now: Latin, Cyrillic, Hungarian, Greek etc. as well as Thai, Arabic and Katakana.
You can send images as well, they will be printed in black and white but other than that will look mighty fine and very high-res!
Emojis, media, stickers, as well as exotic characters (i.e. Indic) are not supported (yet), they will be ignored or a ? will be printed instead.
This all used to run on an ESP, but was moved to a raspberry pi since image and extended character set support were added. If anyone knows how to dynamically interpret and switch character sets, as well as doing image manipulation with the limited resources of an ESP pls let me know.
If the bot is offline (maybe I'm asleep) dont worry, all messages are retained on a server and will be printed in the end!

Howto:
Any text message or image that is not a command (starts with /) will be printed alongside your first name and a timestamp
/help shows this info
/start shows welcome text and requests access
/anonymous [message] prints an anonymous message (without first name)
/info shows debug info about your chat
/stats shows printer statistics
/latex prints a latex equation (ex: \\frac{\partial\mathcal{D}}{\partial t} \\nabla\\times\mathcal{H})

If you have any feature ideas or bug reports pls send a text to @LinhTran, or better yet, send them to the printer!
""")

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

with open("config.json", "r") as f:
    config = ujson.load(f)
logger.info("Config loaded")

fmt = '%d-%m-%Y %H:%M:%S'
tzone = timezone('Europe/Amsterdam')

p = Serial(devfile='/dev/ttyUSB0',
           baudrate=38400,
           bytesize=8,
           parity='N',
           stopbits=1,
           timeout=1.00,
           dsrdtr=False,
           profile="TM-T88II")

try:
    with open("bonbotdata.json", "r") as f:
        bonbotdata = ujson.load(f)
        logger.info("Database was loaded:")
        for entry in bonbotdata:
            logger.info(entry,":", bonbotdata[entry])
except OSError:  # no database yet
    bonbotdata = {}


def user_exists(id):
    for entry in bonbotdata:
        if int(entry) == id:
            return True
    return False


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    message = update.message
    if user_exists(message.chat.id):
        message.reply_text("You already have print access. Type /help if you want to know how this thing works")
    else:
        message.reply_text(start_text)
        user_name = '@' + message.chat.username if message.chat.username is not None else message.chat.first_name
        context.bot.send_message(chat_id=config['admin_chat_id'], text=f"User id {message.chat.id} with name {user_name} has requested access to the bonnetjesprinter, moog det? typ /adduser [id] om t te doon")


def helper(update, context):
    """Send a message when the command /help is issued."""
    message = update.message
    message.reply_text(help_text)

def cut(update, context):
    cut()

def info(update, context):
    update.message.reply_text(str(update))

def printbon(update, context):
    """print the user message."""
    message = update.message

    if user_exists(message.chat.id):
        message.reply_text("Bonnetjesprinter doet brrrr")
        # update stats
        bonbotdata[str(message.chat.id)]['messages'] += 1
        bonbotdata[str(message.chat.id)]['characters'] += len(message.text)
        with open("bonbotdata.json", "w") as f:
            ujson.dump(bonbotdata, f)

        timestring = message.date.astimezone(tzone).strftime(fmt)
        p.text(f"Om {timestring} zei {message.chat.first_name}:\n{message.text}")
        p.text("\n------------------------------------------\n")
        cut()

def shell(update, context):
    message = update.message
    try:
        cmd = message.text[7:]
        output = exec(cmd)
        logger.info(output)
        message.reply_text(output)
    except:
        message.reply_text("caused exception")

def approve_user(update, context):
    global bonbotdata
    message = update.message

    user_id = message.text.split(" ")[1]

    if user_exists(user_id):
        message.reply_text("The user you tried to approve is already in the database. Ignoring request")
        return
    new_user = {user_id: {"messages": 0, "characters": 0}}
    bonbotdata.update(new_user)
    with open("bonbotdata.json", "w") as f:
        ujson.dump(bonbotdata, f)
    context.bot.send_message(chat_id=user_id, text=welcome_text)
    context.bot.send_message(chat_id=config['admin_chat_id'], text=f"Access granted for user {user_id}")

def anonymous(update, context):
    message = update.message
    user_name = '@' + message.chat.username if message.chat.username is not None else message.chat.first_name
    context.bot.send_message(chat_id=config['admin_chat_id'], text=f"User {user_name} sent an anonymous message!")

    update.message.chat.first_name = "anonymous"
    update.message.text = message.text[11:]
    printbon(update, context)

def del_user(update, context):
    global bonbotdata
    message = update.message
    user_id = message.text.split(" ")[1]
    if user_id in bonbotdata:
        del bonbotdata[user_id]
        with open("bonbotdata.json", "w") as f:
            ujson.dump(bonbotdata, f)
        message.reply_text(f"user {user_id} succesfully deleted")
    else:
        message.reply_text(f"user {user_id} not found in table")

def sendto(update, context):
    message = update.message
    user_id = message.text.split(" ")[1]
    text = " ".join(message.text.split(" ")[2:])
    context.bot.send_message(chat_id=user_id, text=text)
    context.bot.send_message(chat_id=config['admin_chat_id'], text=f"Sent user {user_id} sent the message:\n{text}")
    pass

def stats(update, context):
    tot_mes = 0
    tot_char = 0
    message = update.message
    for entry in bonbotdata:
        tot_mes = tot_mes + bonbotdata[entry]['messages']
        tot_char = tot_char + bonbotdata[entry]['characters']
    totstats = f"Total # of messages printed: {tot_mes}\nTotal # of characters printed: {tot_char}"
    message.reply_text(totstats)
    if (message.chat.id == config['admin_chat_id']):
        pretty = ""
        for entry in bonbotdata:
            pretty += (f"{entry}: {bonbotdata[entry]}\n")
        message.reply_text(pretty)


def spam(update, context):
    for entry in bonbotdata:
        context.bot.send_message(chat_id=entry, text=update.message.text[6:])
    update.message.reply_text("Spammed everyone in the database")

def printimage(photo):
    im = Image.open(photo)
    width, height = im.size

    maxwidth = p.profile.media['width']['pixels']
    resizeratio = maxwidth/width
    print(width, height, resizeratio, maxwidth)
    print(int(height * resizeratio))
    photo = im.resize((maxwidth, int(height * resizeratio)))
    p.image(photo, impl='bitImageRaster')

def cut(update=0, context=0):
    if config['auto_cut'] is True:
        p.cut(mode='FULL', feed=True)

def imagemes(update, context):
    message = update.message

    if user_exists(message.chat.id):
        newFile = context.bot.getFile(file_id=message.photo[-1].file_id)
        photo = newFile.download("temp.png")
        # update stats
        bonbotdata[str(message.chat.id)]['messages'] += 1
        with open("bonbotdata.json", "w") as f:
            ujson.dump(bonbotdata, f)

        message.reply_text("Bonnetjesprinter doet brrrr")
        timestring = message.date.astimezone(tzone).strftime(fmt)
        p.text(f"Om {timestring} zei {message.chat.first_name}:\n")
        printimage(photo)
        os.remove("temp.png")
        p.text("\n------------------------------------------\n")
        cut()

def russian(context):
    text = "Доброе утро. Хорошего дня!"
    p.text(f"Daily Russian:\n{text}")
    p.text("\n------------------------------------------\n")
    cut()

def latex(update, context):
    message = update.message
    if user_exists(message.chat.id):
        try:
            expr = f"r'$${message.text[7:]}$$'"
            preview(expr, viewer='file', filename='temp.png')
        except:
            message.reply_text("Only simple and correct equations are supported. Pls try again")
            return
        # update stats
        bonbotdata[str(message.chat.id)]['messages'] += 1
        with open("bonbotdata.json", "w") as f:
            ujson.dump(bonbotdata, f)
        timestring = message.date.astimezone(tzone).strftime(fmt)
        message.reply_text("Bonnetjesprinter doet brrrr")
        p.text(f"Om {timestring} zei {message.chat.first_name}:\n")
        printimage("temp.png")
        os.remove("temp.png")
        p.text("\n------------------------------------------\n")
        cut()


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(config['token'])

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    admin_filter = Filters.chat(config['admin_chat_id'])
    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", helper))
    dispatcher.add_handler(CommandHandler("info", info))
    dispatcher.add_handler(CommandHandler("stats", stats))
    dispatcher.add_handler(CommandHandler("cut", cut))
    dispatcher.add_handler(CommandHandler("anonymous", anonymous))
    dispatcher.add_handler(CommandHandler("latex", latex))


    dispatcher.add_handler(CommandHandler("adduser", approve_user, filters=admin_filter))
    dispatcher.add_handler(CommandHandler("deluser", del_user, filters=admin_filter))
    dispatcher.add_handler(CommandHandler("shell", shell, filters=admin_filter))
    dispatcher.add_handler(CommandHandler("sendto", sendto, filters=admin_filter))
    dispatcher.add_handler(CommandHandler("spam", spam, filters=admin_filter))

    # on noncommand i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, printbon))
    dispatcher.add_handler(MessageHandler(Filters.photo & ~Filters.command, imagemes))

    # scheduled tasks that run in UTC
    job = updater.job_queue
    job.run_daily(russian,datetime.time(6, 30, 00, 000000),days=(0, 1, 2, 3, 4, 5, 6))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
