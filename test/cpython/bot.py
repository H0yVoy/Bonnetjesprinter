
# Cpython bot implementation

configfile = "config.json"
dbfile = "bonbotdata.json"

import logging
from telegram import Update, File, PhotoSize
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import ujson  # for database stuff
import datetime

import callbacks as cbs

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

config = ujson.load(open(configfile, "r"))
db = ujson.load(open(dbfile, "r"))

handler = cbs.handler(config, db)

if __name__ == '__main__':
    updater = Updater(config['token'])
    dispatcher = updater.dispatcher

    admin_filter = Filters.chat(config['admin_chat_id'])

    dispatcher.add_handler(CommandHandler("start",      handler.start))
    dispatcher.add_handler(CommandHandler("help",       handler.helper))
    dispatcher.add_handler(CommandHandler("info",       handler.info))
    dispatcher.add_handler(CommandHandler("stats",      handler.stats))
    dispatcher.add_handler(CommandHandler("cut",        handler.cut))
    dispatcher.add_handler(CommandHandler("anonymous",  handler.anonymous))
    dispatcher.add_handler(CommandHandler("latex",      handler.latex))

    dispatcher.add_handler(CommandHandler("adduser",    handler.approve_user,   filters=admin_filter))
    dispatcher.add_handler(CommandHandler("deluser",    handler.deluser,       filters=admin_filter))
    dispatcher.add_handler(CommandHandler("shell",      handler.shell,          filters=admin_filter))
    dispatcher.add_handler(CommandHandler("sendto",     handler.sendto,         filters=admin_filter))
    dispatcher.add_handler(CommandHandler("spam",       handler.spam,           filters=admin_filter))

    dispatcher.add_handler(MessageHandler(Filters.text  & ~Filters.command, handler.txtbon))
    dispatcher.add_handler(MessageHandler(Filters.photo & ~Filters.command, handler.imgbon))

    # scheduled tasks that run in UTC
    #job = updater.job_queue
    #job.run_daily(handler.russian, datetime.time(6, 30, 00, 000000),days=(0, 1, 2, 3, 4, 5, 6))

    # start_polling() is non-blocking and will stop the bot gracefully on SIGTERM
    updater.start_polling()
    updater.idle()
