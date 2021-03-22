#!/usr/bin/env python
__author__ = "Thijs van Gansewinkel"
__version__ = "0.1"

configfile = "config.json"
dbfile = "bonbotdb.json"

import logging
from telegram import Update, File, PhotoSize
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import ujson  # for database stuff
from datetime import time
from tinydb import TinyDB

import callbacks as cbs
import commands as cmd

config = ujson.load(open(configfile, "r"))
db = TinyDB(dbfile)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#           command,    function,       level
commands = {"start":     (cmd.start,     -1),
            "help":      (cmd.help,      0),
            "html":      (cmd.html,      0),
            "info":      (cmd.info,      0),
            "anonymous": (cmd.anon,      1),
            "latex":     (cmd.latex,     1),
            "stats":     (cmd.stats,     1),
            "shell":     (cmd.shell,     2),
            "grant":     (cmd.grant,     2),
            "revoke":    (cmd.revoke,    2),
            "sendto":    (cmd.sendto,    2),
            "spam":      (cmd.spam,      2),
            "database":  (cmd.database,  2),
            "printq":    (cmd.printq,    2),
            "purge":     (cmd.purge,     2),
            "sleep":     (cmd.sleep,     2)}

if __name__ == '__main__':
    mhandler = cbs.mhandler(logger, config, db)

    updater = Updater(config['token'])
    dispatcher = updater.dispatcher

    for command, (handler, level) in commands.items():
        dispatcher.add_handler(CommandHandler(command, handler(level, mhandler).handlecmd))

    for filter in (Filters.sticker, Filters.text, Filters.photo, Filters.document):
        dispatcher.add_handler(MessageHandler(filter, mhandler.message))

    # scheduled tasks that run in UTC so 6:30 in utc is 7:30 here (summer time)
    # will fix later
    job = updater.job_queue
    #job.run_daily(mhandler.russian, time(8, 00, 00, 000000),days=(0, 1, 2, 3, 4, 5, 6))
    job.run_daily(mhandler.go_sleep, time(22, 30, 00, 000000),days=(0, 1, 2, 3, 4, 5, 6))
    job.run_daily(mhandler.wake, time(6, 30, 00, 000000),days=(0, 1, 2, 3, 4, 5, 6))

    # add exception handler
    #dispatcher.add_error_handler(mhandler.exception)

    # start_polling() is non-blocking and will stop the bot gracefully on SIGTERM
    updater.start_polling()
    updater.idle()
