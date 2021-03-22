from sympy import preview  # latex compiling
from tinydb import Query
from datetime import datetime
import tinydb.operations as tdbop

from texts import start_text, welcome_text, help_text, html_text


class commandhandler:
    def __init__(self, level, handler):
        self.level = level
        self.handler = handler

    def handlecmd(self, update, context):
        if self.handler.get_level(update.message.chat.id) >= self.level:
            self.callback(update, context)


class start(commandhandler):
    def callback(self, update, context):
        message = update.message
        if self.handler.get_level(message.chat.id) > 0:
            message.reply_text("You already have print access. Type /help if you want to know how to use it")
        elif self.handler.get_level(message.chat.id) == 0:
            message.reply_text("Access has already been requested, be patient for approval")
        else:
            message.reply_text(start_text)
            user_name = '@' + message.chat.username if message.chat.username is not None else message.chat.first_name
            context.bot.send_message(chat_id=self.handler.cf['admin_id'], text=f"User id {message.chat.id} with name {user_name} has requested access to the bonnetjesprinter, moog det? Do a copy pasta")
            context.bot.send_message(chat_id=self.handler.cf['admin_id'], text=f"/grant {message.chat.id}")
            self.handler.users.insert({"name": message.chat.first_name + " " + message.chat.last_name,
                                       "uname": user_name,
                                       "id": message.chat.id,
                                       "added": str(datetime.now()),
                                       "level": 0,
                                       "messages": 0,
                                       "characters": 0,
                                       "images": 0})

class help(commandhandler):
    def callback(self, update, context):
        update.message.reply_text(help_text)

class html(commandhandler):
    def callback(self, update, context):
        update.message.reply_text(html_text)

class info(commandhandler):
    def callback(self, update, context):
        update.message.reply_text(str(update))

class anon(commandhandler):
    def callback(self, update, context):
        message = update.message
        update.message.text = update.message.text[11:]
        user = '@' + message.chat.username if message.chat.username is not None else message.chat.first_name
        context.bot.send_message(chat_id=self.handler.cf['admin_id'], text=f"User {user} sent an anonymous message!")
        self.handler.message(update, context, anon=True)

class latex(commandhandler):
    def callback(self, update, context):
        message = update.message
        try:
            expr = f"\\Large ${message.text[7:]}$"
            preview(expr, viewer='file', filename='latex.png')
        except:
            message.reply_text("Only simple and correct equations are supported. Pls try again")
            return
        time = message.date.astimezone(self.handler.tzone).strftime(self.handler.fmt)

        text = None
        if self.handler.get_level(message.chat.id) < 2:  # don't print additional info for admins
            text = f"Om {time} zei {message.chat.first_name}:\n"
        self.handler.printq.insert({"name": message.chat.first_name,
                                    "id": message.chat.id,
                                    "date": time,
                                    "text": text,
                                    "image": "latex.png",
                                    "printed": False})
        if self.handler.sleep:
            message.reply_text("The printer is currently asleep, your receipt was queued")
        else:
            self.handler.bprinter.brrr(context)

class stats(commandhandler):
    def callback(self, update, context):
        tot_mes = 0
        tot_char = 0
        tot_img = 0
        message = update.message
        for entry in self.handler.users:
            tot_mes = tot_mes + entry['messages']
            tot_char = tot_char + entry['characters']
            tot_img = tot_img + entry['images']
        totstats = f"Total # of messages printed: {tot_mes}\nTotal # of characters printed: {tot_char}\nTotal # of images printed: {tot_img}"
        message.reply_text(totstats)

class shell(commandhandler):
    def callback(self, update, context):
        message = update.message
        cmd = message.text[7:]
        output = exec(cmd)
        message.reply_text(output)

class grant(commandhandler):
    def callback(self, update, context):
        message = update.message
        user_id = int(message.text.split(" ")[1])
        user_name = '@' + message.chat.username if message.chat.username is not None else message.chat.first_name
        if self.handler.get_level(user_id) > 0:
            message.reply_text("The user you tried to grant access to already has access. Ignoring request")
        else:
            self.handler.users.update(tdbop.set("level", 1), Query().id == user_id)
            context.bot.send_message(chat_id=user_id, text=welcome_text)
            context.bot.send_message(chat_id=self.handler.cf['admin_id'], text=f"Access granted for user {user_id}")

class revoke(commandhandler):
    def callback(self, update, context):
        message = update.message
        user_id = int(message.text.split(" ")[1])
        if self.handler.get_level(user_id) != -1:
            self.handler.users.remove(Query().id == user_id)
            message.reply_text(f"Access for user {user_id} revoked")
        else:
            message.reply_text(f"User {user_id} not found in database")

class sendto(commandhandler):
    def callback(self, update, context):
        message = update.message
        user_id = message.text.split(" ")[1]
        text = " ".join(message.text.split(" ")[2:])
        context.bot.send_message(chat_id=user_id, text=text)
        context.bot.send_message(chat_id=self.handler.cf['admin_id'], text=f"Sent user {user_id} sent the message:\n{text}")

class spam(commandhandler):
    def callback(self, update, context):
        for entry in self.db:
            context.bot.send_message(chat_id=entry, text=update.message.text[6:])
        update.message.reply_text("Spammed everyone in the database")

class database(commandhandler):
    def callback(self, update, context):
        total = ""
        for item in self.handler.users:
            total = total + f"{item}\n"
        update.message.reply_text(str(total))

class printq(commandhandler):
    def callback(self, update, context):
        total = ""
        for item in self.handler.printq:
            if item['printed'] is False:
                total = total + f"{item}\n"
        if total:
            update.message.reply_text(str(total))
        else:
            update.message.reply_text("Queue is empty")

class purge(commandhandler):
    def callback(self, update, context):
        num = 0
        for item in self.handler.printq:
            if item['printed'] is False:
                self.handler.printq.update(tdbop.set("printed", True), Query().date == item['date'])
                num += 1
        update.message.reply_text(f"Purged {num} message(s) from the queue")


class sleep(commandhandler):
    def callback(self, update, context):
        self.handler.sleep = not self.handler.sleep
        update.message.reply_text(f"sleep state was toggled. Sleep: {self.handler.sleep}")
        if not self.handler.sleep:
            self.handler.bprinter.brrr(context)

class brrr(commandhandler):
    def callback(self, update, context):
        self.handler.bprinter.brrr(context)
        update.message.reply_text(f"printing print queue")
