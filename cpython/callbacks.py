# make sure to grab the latest escpos version from:
# https://github.com/python-escpos/python-escpos
from escpos.printer import Serial

import datetime
import time
from time import sleep
from pytz import timezone  # get message timezones correct
from PIL import Image  # resizing incoming images
from sympy import preview  # latex compiling
import os  # downloaded file handling
import ujson  # for database stuff

from texts import start_text, welcome_text, help_text, printing_text


class handler:
    def __init__(self, config, db):
        self.config = config
        self.db = db
        self.fmt = self.config['dtfmt']
        self.tzone = timezone(self.config['tzone'])
        self.p = Serial(devfile='/dev/ttyUSB0',
                        baudrate=38400,
                        bytesize=8,
                        parity='N',
                        stopbits=1,
                        timeout=1.00,
                        dsrdtr=False,
                        profile="TM-T88II")

    def write_db(self):
        # TODO: substitue with sqlite or smth
        with open("bonbotdata.json", "w") as f:
            ujson.dump(self.db, f)

    def check_user(self,id):
        for entry in self.db:
            if int(entry) == id:
                return True
        return False

    def cut(self):
        if self.config['auto_cut'] is True:
            self.p.cut(mode='FULL', feed=True)

    ## command handlers
    def start(self, update, context):
        """Send a message when the command /start is issued."""
        message = update.message
        if self.check_user(message.chat.id):
            message.reply_text("You already have print access. Type /help if you want to know how this thing works")
        else:
            message.reply_text(start_text)
            user_name = '@' + message.chat.username if message.chat.username is not None else message.chat.first_name
            context.bot.send_message(chat_id=self.config['admin_chat_id'],
                                     text=f"User id {message.chat.id} with name {user_name} has requested access to the bonnetjesprinter, moog det? typ /adduser [id] om t te doon")


    def helper(self, update, context):
        """Send a message when the command /help is issued."""
        update.message.reply_text(help_text)

    def info(self, update, context):
        update.message.reply_text(str(update))

    def txtbon(self, update, context):
        """print the user message."""
        message = update.message
        if self.check_user(message.chat.id):
            message.reply_text(printing_text)
            # update stats
            self.db[str(message.chat.id)]['messages'] += 1
            self.db[str(message.chat.id)]['characters'] += len(message.text)
            self.write_db()

            timestring = message.date.astimezone(self.tzone).strftime(self.fmt)
            self.p.text(f"Om {timestring} zei {message.chat.first_name}:\n{message.text}")
            self.p.text("\n------------------------------------------\n")
            self.cut()

    def imgbon(self, update, context):
        message = update.message
        if self.check_user(message.chat.id):
            newFile = context.bot.getFile(file_id=message.photo[-1].file_id)
            photo = newFile.download("temp.png")
            # update stats
            self.db[str(message.chat.id)]['messages'] += 1
            self.write_db()

            message.reply_text(printing_text)
            timestring = message.date.astimezone(self.tzone).strftime(self.fmt)
            self.p.text(f"Om {timestring} zei {message.chat.first_name}:\n")
            self.printimage(photo)
            os.remove("temp.png")
            self.p.text("\n------------------------------------------\n")
            self.cut()

    def printimage(self, photo):
        im = Image.open(photo)
        width, height = im.size

        maxwidth = self.p.profile.media['width']['pixels']
        resizeratio = maxwidth/width
        photo = im.resize((maxwidth, int(height * resizeratio)))
        self.p.image(photo, impl='bitImageRaster')

    def anonymous(self, update, context):
        message = update.message
        user_name = '@' + message.chat.username if message.chat.username is not None else message.chat.first_name
        context.bot.send_message(chat_id=self.config['admin_chat_id'], text=f"User {user_name} sent an anonymous message!")

        update.message.chat.first_name = "anonymous"
        update.message.text = message.text[11:]
        self.txtbon(update, context)

    def stats(self, update, context):
        tot_mes = 0
        tot_char = 0
        message = update.message
        for entry in self.db:
            tot_mes = tot_mes + self.db[entry]['messages']
            tot_char = tot_char + self.db[entry]['characters']
        totstats = f"Total # of messages printed: {tot_mes}\nTotal # of characters printed: {tot_char}"
        message.reply_text(totstats)
        if (message.chat.id == self.config['admin_chat_id']):
            pretty = ""
            for entry in self.db:
                pretty += (f"{entry}: {self.db[entry]}\n")
            message.reply_text(pretty)

    def latex(self, update, context):
        message = update.message
        if self.check_user(message.chat.id):
            try:
                expr = f"r'$${message.text[7:]}$$'"
                preview(expr, viewer='file', filename='temp.png')
            except:
                message.reply_text("Only simple and correct equations are supported. Pls try again")
                return
            # update stats
            self.db[str(message.chat.id)]['messages'] += 1
            self.write_db()
            timestring = message.date.astimezone(self.tzone).strftime(self.fmt)
            message.reply_text(printing_text)
            self.p.text(f"Om {timestring} zei {message.chat.first_name}:\n")
            self.printimage("temp.png")
            self.p.text("\n------------------------------------------\n")
            self.cut()
            os.remove("temp.png")

    ## admin command handlers
    def approve_user(self, update, context):
        message = update.message
        user_id = message.text.split(" ")[1]
        if self.check_user(user_id):
            message.reply_text("The user you tried to approve is already in the database. Ignoring request")
        else:
            new_user = {user_id: {"messages": 0, "characters": 0}}
            self.db.update(new_user)
            self.write_db()
            context.bot.send_message(chat_id=user_id, text=welcome_text)
            context.bot.send_message(chat_id=self.config['admin_chat_id'], text=f"Access granted for user {user_id}")

    def deluser(self, update, context):
        message = update.message
        user_id = message.text.split(" ")[1]
        if user_id in self.db:
            del self.db[user_id]
            self.write_db()
            message.reply_text(f"user {user_id} succesfully deleted")
        else:
            message.reply_text(f"user {user_id} not found in table")

    def sendto(self, update, context):
        message = update.message
        user_id = message.text.split(" ")[1]
        text = " ".join(message.text.split(" ")[2:])
        context.bot.send_message(chat_id=user_id, text=text)
        context.bot.send_message(chat_id=self.config['admin_chat_id'], text=f"Sent user {user_id} sent the message:\n{text}")

    def shell(self, update, context):
        message = update.message
        try:
            cmd = message.text[7:]
            output = exec(cmd)
            message.reply_text(output)
        except:
            message.reply_text("caused exception")

    def spam(self, update, context):
        for entry in self.db:
            context.bot.send_message(chat_id=entry, text=update.message.text[6:])
        update.message.reply_text("Spammed everyone in the database")

    def russian(self, context):
        text = "Доброе утро. Хорошего дня!"
        p.text(f"Daily Russian:\n{text}")
        p.text("\n------------------------------------------\n")
        cut()

