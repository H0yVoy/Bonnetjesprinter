import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from time import sleep
import time
from pytz import timezone

# Cpython bot implementation 
# make sure to grab the latest version from:
# https://github.com/python-escpos/python-escpos
from escpos.printer import Serial
import ujson
import pprint

start_text = (
    """You don't have print access yet, so I've requested it for you. You'll get a confirmation message once access has been granted"""
)

welcome_text = (
"""You now have access to print!
Type /help for a more elaborate guide
""")

help_text = (
"""Info:
Only ASCII characters are supported right now, you can type whatever you want but if it's not ASCII (cyrillic, arabic, etc.) it probably won't be printed.
Pics, emojis, media, and stickers are not supported (yet), they will be ignored. 
This all runs on an ESP with limited resources, so sometimes the bot can take several seconds before it responds. The bot might also crash from time to time, and my wifi is buggy af,
I'm also still figuring out how memory allocation works pls don't hate xd
Dont worry, all messages are retained on a server and will be printed in the end!

Howto:
Any message that is not a command (starts with /) will be printed alongside your first name and a timestamp
/help shows this info
/start shows welcome text and requests access
/anonymous [message] prints an anonymous message (without first name)
/info shows debug info about your chat
/stats shows printer statistics

If you have any feature ideas or bug reports pls send a text to @LinhTran, or better yet, send them to the printer!
""")

p = Serial(devfile='/dev/ttyUSB2',
           baudrate=38400,
           bytesize=8,
           parity='N',
           stopbits=1,
           timeout=1.00,
           dsrdtr=True,
           Profile="TM-T88II")

with open("config.json", "r") as f:
    config = ujson.load(f)
logger.info("Config loaded")

fmt = '%d-%m-%Y %H:%M:%S'
tzone = timezone('Europe/Amsterdam')

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

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
    p.cut()

def info(update, context):
    update.message.reply_text(str(update))

def printbon(update, context):
    """print the user message."""
    message = update.message

    if user_exists(message.chat.id):
        message.reply_text("Bonnetjesprinter doet brrrr")
        timestring = message.date.astimezone(tzone).strftime(fmt)
        p.text(f"Om {timestring} zei {message.chat.first_name}:\n{message.text}")
        p.cut()

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
    pass


def printimage(update, context):
    logger.info(update)
    message = 
    p.image()

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

    dispatcher.add_handler(CommandHandler("adduser", approve_user, filters=admin_filter))
    dispatcher.add_handler(CommandHandler("deluser", del_user, filters=admin_filter))
    dispatcher.add_handler(CommandHandler("shell", shell, filters=admin_filter))
    dispatcher.add_handler(CommandHandler("sendto", sendto, filters=admin_filter))
    dispatcher.add_handler(CommandHandler("spam", spam, filters=admin_filter))

    # on noncommand i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, printbon))
    dispatcher.add_handler(MessageHandler(Filters.image & ~Filters.command, printimage))


    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()