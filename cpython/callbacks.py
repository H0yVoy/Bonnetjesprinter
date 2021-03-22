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

from texts import printing_text

from html.parser import HTMLParser


class printerpreter(HTMLParser):
    """ interprets text sent to printer, supports a ton of tags and converts links to qr codes"""
    active_tags = {}

    def __init__(self, printer, *, convert_charrefs=True):
        self.convert_charrefs = convert_charrefs
        self.reset()
        self.p = printer

    def printbon(self, text):
        # TODO: auto detect urls and insert qr tags
        text = emoji.demojize(text)
        print("printbon:", text)  # debug
        self.active_tags = {}  # reset tags on every new print
        self.reset()  # reset instance, necessary to avoid infinite loop exceptions
        self.feed(text)
        self.p.set()  # reset printer settings

    def handle_starttag(self, tag, attrs):
        try:
            if tag == "qr":
                print("QR:", attrs[0][1])
                self.p.qr(str(attrs[0][1]), size=3, center=True)
                self.p.set(align='center')
                self.p.text(attrs[0][1])
            elif tag == "bar":  # TODO: extend support for formats and add to help
                print("BAR:", attrs[0][1])
                self.p.barcode(str(attrs[0][1]), 'EAN13', 64, 2, '', '')             
            else:
                self.active_tags.update({tag: attrs[0][0]})
        except IndexError:
            self.active_tags.update({tag: True})

    def handle_endtag(self, tag):
        del self.active_tags[tag]

    def handle_data(self, data):
        self.setPrinterSettings(self.active_tags)
        print("PRINT:", data)
        self.p.text(data)

    def setPrinterSettings(self, tags):
        args = ""
        print("active tags:", tags)
        for entry in tags:
            # set = set + f"{entry}={tags[entry]}"
            tag = tags[entry]
            if entry == "a" or entry == "align":
                args = args + f"align='{tag}', "
            if entry == "f" or entry == "font":
                args = args + f"font='{tag}', "
            if entry == "b" or entry == "bold":
                args = args + f"bold=True, "
            if entry == "u" or entry == "underline":
                args = args + f"underline={tag}, "
            if entry == "dh" or entry == "double_height":
                args = args + f"double_heigt=True, "
            if entry == "dw" or entry == "double_width":
                args = args + f"double_width=True, "
            if entry == "cs" or entry == "custom_size":
                args = args + f"custom_size=True, "
            if entry == "w" or entry == "width":
                args = args + f"width={tag}, "
            if entry == "h" or entry == "height":
                args = args + f"height={tag}, "
            if entry == "d" or entry == "density":
                args = args + f"density={tag}, "
            if entry == "i" or entry == "invert":
                args = args + f"invert=True, "
            if entry == "s" or entry == "smooth":
                args = args + f"smooth=True, "
            if entry == "fl" or entry == "flip":
                args = args + f"flip=True, "
        print("SET:", args)
        # not sure if there's a code injection possibility here
        exec(f"self.p.set({args})")
        # if so use a dict, but doesn't work yet for now
        # args = args[:-2]  # remove final comma
        # args = dict(a.split('=') for a in args.split(', '))
        # print(args)


class bonprinter:
    def __init__(self, logger, config, printq):
        self.logger = logger
        self.cf = config
        self.printq = printq
        #self.p = None
        self.p = Serial(devfile='/dev/ttyUSB1',
                        baudrate=38400,
                        bytesize=8,
                        parity='N',
                        stopbits=1,
                        timeout=1.00,
                        dsrdtr=False,
                        profile="TM-T88II")
        self.pprint = printerpreter(self.p)  # pretty printer

    def brrr(self, context):
        for item in self.printq:
            if item['printed'] is False:
                context.bot.send_message(chat_id=item['id'], text=printing_text)
                self.printq.update(tdbop.set("printed", True), Query().date == item['date'])
                # mark as printed so errors dont result in infinite loops
                if item['text'] is not None:
                    self.pprint.printbon(item['text'])
                if item['image'] is not None:
                    self.p.image(item['image'], impl='bitImageRaster')
                self.p.text("\n------------------------------------------\n")
                if self.cf['auto_cut'] is True:
                    self.p.cut(mode='FULL', feed=True, lines=4)
                if item['image'] is not None:
                    sleep(2)  # timeout so printer can cool down
                # self.printq.remove(Query().date == item['date'])  # keep the database clean


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
                        return  # don't attempt to download anything
                    else:
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
                img.save(f"./fcache/{imageFile.file_unique_id}.png", 'PNG')
                self.users.update(tdbop.increment("images"), Query().id == message.chat.id)
            except (IndexError, AttributeError):
                pass

            self.users.update(tdbop.increment("messages"), Query().id == message.chat.id)
            if text is not None:
                newvalue = self.users.search(Query().id == message.chat.id)[0]['characters'] + len(text)
                self.users.update(tdbop.set("characters", newvalue), Query().id == message.chat.id)

            if level < 2:  # don't print additional info for admins
                text = f"Om {time} zei {message.chat.first_name}\n{text}"

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
        message = update.message
        user_name = '@' + message.chat.username if message.chat.username is not None else message.chat.first_name
        message.reply_text(f"Your message caused the following error:\n{context.error}\n\nif you feel confused then send a text to Ties")
        context.bot.send_message(chat_id=self.cf['admin_id'], text=f"User {user_name} sent the message:\n{message}\n which caused an exception:\n{context.error}!")


if __name__ == "__main__":
    pprint = printerpreter(None)  # pretty printer
    pprint.print("<qr src=https://thijsvg.nl>thijsvg.nl\n")
    text = ("""hallo
        hoeist? ja goed he
        oke
        heyheyhey
        <align left><font a><bold>hey</bold></font></align>
        <align right>hoeist?</align>
        <align left>goed, mj?</align>
        <font b><bold>HALLO</bold></font>
        <flip>ondersteboven</flip>
        <ul 2>
        <bold>oida</bold>
        <qr src=https://thijsvg.nl>thijsvg.nl
        """
    )


    # <qr src=https://.nl>
