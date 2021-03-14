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
        self.parser = printerpreter(self.p)

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
            self.p.cut(mode='FULL', feed=True, lines=4)

    ## command handlers
    def start(self, update, context):
        """Send a message when the command /start is issued."""
        message = update.message
        if self.check_user(message.chat.id):
            message.reply_text("You already have print access. Type /help if you want to know how this thing works")
        else:
            message.reply_text(start_text)
            user_name = '@' + message.chat.username if message.chat.username is not None else message.chat.first_name
            context.bot.send_message(chat_id=self.config['admin_chat_id'], text=f"User id {message.chat.id} with name {user_name} has requested access to the bonnetjesprinter, moog det? typ /adduser [id] om t te doon")

    def helper(self, update, context):
        """Send a message when the command /help is issued."""
        update.message.reply_text(help_text)

    def info(self, update, context):
        update.message.reply_text(str(update))

    def message(self, update, context):
        """print the user message."""
        message = update.message
        print(message)
        if self.check_user(message.chat.id):
            message.reply_text(printing_text)
            self.db[str(message.chat.id)]['messages'] += 1

            body = message.text
            user = message.chat.first_name
            image = None
            try:
                newFile = context.bot.getFile(file_id=message.photo[-1].file_id)
                image = newFile.download("temp.png")
                body = message.caption
            except (IndexError, AttributeError):
                pass

            if body:
                self.db[str(message.chat.id)]['characters'] += len(body)
                self.write_db()
            time = message.date.astimezone(self.tzone).strftime(self.fmt)
            title = f"Om {time} zei {user}:"
            if self.config['admin_chat_id'] == message.chat.id:
                title = None
            print(title, body, image)
            self.printbon(title, body, image)
            if image:
                os.remove("temp.png")

    def printbon(self, title=None, body=None, image=None, image_resize=True):
        if title:
            self.p.text(title + "\n")
        if image:
            self.printimage(image, image_resize)
        if body:
            self.p.text(body)
        self.p.text("\n------------------------------------------\n")
        self.cut()
        sleep(2) # timeout else the printing element overheats

    def printimage(self, photo, resize=True):
        im = Image.open(photo)
        width, height = im.size

        maxwidth = self.p.profile.media['width']['pixels']
        if width > maxwidth or resize is True:
            resizeratio = maxwidth/width
            photo = im.resize((maxwidth, int(height * resizeratio)))
        self.p.image(photo, impl='bitImageRaster')

    def anonymous(self, update, context):
        message = update.message
        user = '@' + message.chat.username if message.chat.username is not None else message.chat.first_name
        context.bot.send_message(chat_id=self.config['admin_chat_id'], text=f"User {user} sent an anonymous message!")
        time = message.date.astimezone(self.tzone).strftime(self.fmt)
        title = f"Om {time} zei anonymous:"
        self.printbon(title, update.message.text[11:])

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
                expr = f"\\Large ${message.text[7:]}$"
                preview(expr, viewer='file', filename='temp.png')
            except:
                message.reply_text("Only simple and correct equations are supported. Pls try again")
                return
            # update stats
            self.db[str(message.chat.id)]['messages'] += 1
            self.write_db()
            time = message.date.astimezone(self.tzone).strftime(self.fmt)
            message.reply_text(printing_text)
            title = f"Om {time} zei {message.chat.first_name}:"
            self.printbon(title, None, "temp.png", False)
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
        cmd = message.text[7:]
        output = exec(cmd)
        message.reply_text(output)

    def spam(self, update, context):
        for entry in self.db:
            context.bot.send_message(chat_id=entry, text=update.message.text[6:])
        update.message.reply_text("Spammed everyone in the database")

    def russian(self, context):
        text = "Доброе утро. Хорошего дня!"
        title = f"Daily Russian:"
        body = text
        self.printbon(title, text)

    def exception(self, update, context):
        context.bot.send_message(chat_id=self.config['admin_chat_id'], text=f"An Exception Occured: {context.error}!")

    def parser(self, text):
        parser = printerpreter(self.p)
        parser.feed(text)


from html.parser import HTMLParser

class printerpreter(HTMLParser):
    """ interprets text sent to printer, supports a ton of tags and converts links to qr codes"""
    active_tags = {}

    def __init__(self, printer):
        self.p = printer

    def handle_starttag(self, tag, attrs):
        try:
            self.active_tags.update({tag: attrs[0][0]})
        except IndexError:
            self.active_tags.update({tag: True})

    def handle_endtag(self, tag):
        del self.active_tags[tag]

    def handle_data(self, data):
        self.setPrinterSettings(self.active_tags)
        self.p.text(data)

    def setPrinterSettings(self, tags):
        set = ""
        for entry in tags:
            # set = set + f"{entry}={tags[entry]}"
            print(entry)
            tag = tags[entry]
            if entry == "a":
                set = set + f"align={tag}, "
            if entry == "f":
                set = set + f"font='{tag}', "
            if entry == "b":
                set = set + f"bold=True, "
            if entry == "ul":
                set = set + f"underline={tag}, "
            if entry == "dh":
                set = set + f"double_heigt=True, "
            if entry == "dw":
                set = set + f"double_width=True, "
            if entry == "cs":
                set = set + f"custom_size=True, "
            if entry == "w":
                set = set + f"custom_width={tag}, "
            if entry == "h":
                set = set + f"custom_height={tag}, "
            if entry == "d":
                set = set + f"density={tag}, "
            if entry == "i":
                set = set + f"invert=True, "
            if entry == "s":
                set = set + f"smooth=True, "
            if entry == "fl":
                set = set + f"flip=True, "
        print(set)
        exec(f"self.p.set({set})")


        

        # exec(f"self.set.p({entry}={active_tags[entry]}")
        # settings is a dict with attributes, convert them to p.set() commands

if __name__ == "__main__":
    import ujson  # for database stuff
    configfile = "config.json"
    dbfile = "bonbotdata.json"
    config = ujson.load(open(configfile, "r"))
    db = ujson.load(open(dbfile, "r"))

    handler = handler(config, db)
    handler.parser.feed(
        """heyheyhey
        <align left><font a><bold>hey
        <align right>hoeist?
        <align left>goed, mj?
        <font b><bold>HALLO</bold></font>
        <flip>ondersteboven</flip>
        <ul 2>
        <bold>oida</bold>
        """
    )


    """ Set text properties by sending them to the printer
    All tags which are not terminated will be terminated at the end of your text

    :param align: horizontal position for text, possible values are:

        * 'center'
        * 'left'
        * 'right'

        *default*: 'left'

    :param font: font given as an index, a name, or one of the
        special values 'a' or 'b', referring to fonts 0 and 1.
    :param bold: text in bold, *default*: False
    :param underline: underline mode for text, decimal range 0-2,  *default*: 0
    :param double_height: doubles the height of the text
    :param double_width: doubles the width of the text
    :param custom_size: uses custom size specified by width and height
        parameters. Cannot be used with double_width or double_height.
    :param width: text width multiplier when custom_size is used, decimal range 1-8,  *default*: 1
    :param height: text height multiplier when custom_size is used, decimal range 1-8, *default*: 1
    :param density: print density, value from 0-8, if something else is supplied the density remains unchanged
    :param invert: True enables white on black printing, *default*: False
    :param smooth: True enables text smoothing. Effective on 4x4 size text and larger, *default*: False
    :param flip: True enables upside-down printing, *default*: False

    :type font: str
    :type invert: bool
    :type bold: bool
    :type underline: bool
    :type smooth: bool
    :type flip: bool
    :type custom_size: bool
    :type double_width: bool
    :type double_height: bool
    :type align: str
    :type width: int
    :type height: int
    :type density: int

    add barcode, qrcode as well, convert weblinks to qrcodes by default
    """
