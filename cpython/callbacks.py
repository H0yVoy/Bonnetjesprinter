from time import sleep
from datetime import datetime

# make sure to grab the latest escpos version from:
# https://github.com/python-escpos/python-escpos
from escpos.printer import Serial
from pytz import timezone  # get message timezones correct
from PIL import Image  # resizing incoming images
from tinydb import Query
import tinydb.operations as tdbop
import emoji

from texts import start_text, welcome_text, help_text, printing_text


class bonprinter:
    def __init__(self, logger, config, printq):
        self.logger = logger
        self.cf = config
        self.printq = printq
        #self.p = None
        self.p = Serial(devfile='/dev/ttyUSB0',
                        baudrate=38400,
                        bytesize=8,
                        parity='N',
                        stopbits=1,
                        timeout=1.00,
                        dsrdtr=False,
                        profile="TM-T88II")

    def brrr(self, context):
        for item in self.printq:
            if item['printed'] is False:
                context.bot.send_message(chat_id=item['id'], text=printing_text)
                if item['text'] is not None:
                    text = emoji.demojize(item['text'])
                    print(text)
                    self.p.text(text)
                if item['image'] is not None:
                    self.p.image(item['image'], impl='bitImageRaster')
                self.p.text("\n------------------------------------------\n")
                if self.cf['auto_cut'] is True:
                    self.p.cut(mode='FULL', feed=True, lines=4)
                self.printq.update(tdbop.set("printed", True), Query().date == item['date'])
                if item['image'] is not None:
                    sleep(2)  # timeout so printer can cool down

    def fancy_parser(self):
        pass


class mhandler:
    def __init__(self, logger, config, db):
        self.logger = logger
        self.cf = config
        self.db = db
        self.fmt = self.cf['dtfmt']
        self.tzone = timezone(self.cf['tzone'])
        self.sleep = False

        self.printq = self.db.table("printq")
        self.users = self.db.table("users")
        self.bprinter = bonprinter(self.logger,
                                   self.cf,
                                   self.printq)

        if not "users" in db.tables():
             self.users.insert({"name": "admin",
                                "uname": "admin",
                                "id": self.cf["admin_id"],
                                "added": str(datetime.now()),
                                "level": 2,
                                "messages": 0,
                                "characters": 0,
                                "images": 0})

    def get_level(self, id):
        user = Query()
        result = self.users.search(user.id == id)
        try:
            level = result[0]['level']
        except IndexError:
            level = -1
        return level

    def message(self, update, context, anon=False):
        message = update.message
        level = self.get_level(message.chat.id)
        if anon:
            message.chat.first_name = "anonymous"
        if level > 0:
            text = message.text
            time = message.date.astimezone(self.tzone).strftime(self.fmt)
            image = None

            try:
                if message.document != None:  # image is document
                    imageFile = context.bot.get_file(message.document.file_id)
                elif message.sticker != None:
                    if (message.sticker.is_animated):
                        message.reply_text("Cannot print animated stickers...")
                        self.logger.error("Cannot print animated stickers")
                    # Get sticker
                    imageFile = context.bot.get_file(message.sticker.file_id)
                elif message.photo != None:
                    imageFile = context.bot.get_file(message.photo[-1].file_id)
                image = imageFile.download(f"./fcache/{imageFile.file_unique_id}.jpeg")
                text = message.caption

                img = Image.open(image)
                width, height = img.size
                maxwidth = self.bprinter.p.profile.media['width']['pixels']
                resizeratio = maxwidth/width
                img = img.resize((maxwidth, int(height * resizeratio)))
                img.save(f"./fcache/{imageFile.file_unique_id}.jpeg", 'JPEG')
                self.users.update(tdbop.increment("images"), Query().id == message.chat.id)
            except (IndexError, AttributeError):
                pass

            self.users.update(tdbop.increment("messages"), Query().id == message.chat.id)
            if text is not None:
                newvalue = self.users.search(Query().id == message.chat.id)[0]['characters'] + len(text)
                self.users.update(tdbop.set("characters", newvalue), Query().id == message.chat.id)

            if level < 2:  # don't print additional info for admins
                text = f"Om {time} zei {message.chat.first_name}\n------------------------------------------\n{text}"

            self.printq.insert({"name": message.chat.first_name,
                                "id": message.chat.id,
                                "date": time,
                                "text": text,
                                "image": image,
                                "printed": False})

            if self.sleep:
                message.reply_text("The printer is currently asleep, your receipt was queued and will be printed when the printer wakes up")
            else:
                # trigger printer
                self.bprinter.brrr(context)

    def russian(self, context):
        text = "Доброе утро. Хорошего дня!"
        body = text
        #self.printbon(title, text)

    def go_sleep(self, context):
        context.bot.send_message(chat_id=self.cf['admin_id'], text=f"Going to sleep...")
        self.sleep = True

    def wake(self, context):
        context.bot.send_message(chat_id=self.cf['admin_id'], text=f"Waking up!")
        self.sleep = False
        self.bprinter.brrr(context)

    def exception(self, update, context):
        context.bot.send_message(chat_id=self.cf['admin_id'], text=f"An Exception Occured: {context.error}!")

    def parser(self, text):
        # todo
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
    cffile = "config.json"
    dbfile = "bonbotdata.json"
    cf = ujson.load(open(cffile, "r"))
    db = ujson.load(open(dbfile, "r"))

    handler = handler(cf, db)
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
