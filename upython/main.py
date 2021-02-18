
import utelegram
import network
import escpos
import ujson
import micropython
from utime import sleep, localtime
from machine import UART

debug = True
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


def init():
    global p, uart, bonbotdata, config
    uart = UART(2, 38400)
    uart.init(38400, bits=8, parity=None, stop=1)
    p = escpos.SerialEscPos(uart, profile="TM-T88II")
    print("UART initialized")

    with open("config.json", "r") as f:
        config = ujson.load(f)
    print("Config loaded")

    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print("Connecting to network", end="")
        sta_if.active(True)
        sta_if.connect(config['ssid'], config['password'])
        while not sta_if.isconnected():
            print(".", end="")
            sleep(.5)
            pass
    print("\nNetwork Connection Established:")
    print(sta_if.ifconfig())

    try:
        with open("bonbotdata.json", "r") as f:
            bonbotdata = ujson.load(f)
            print("Database was loaded:")
            for entry in bonbotdata:
                print(entry,":", bonbotdata[entry])
    except OSError:  # no database yet
        bonbotdata = {}
    gc.collect()

def user_exists(id):
    for entry in bonbotdata:
        if int(entry) == id:
            return True
    return False        
        
def start(message):
    # print("received start:", message)
    if user_exists(message['message']['chat']['id']):
        bot.send(message['message']['chat']['id'], "You already have print access. Type /help if you want to know how this thing works")
    else:
        bot.send(message['message']['chat']['id'], "You don't have print access yet, so I've requested it for you. You'll get a confirmation message once access has been granted")
        user_name = '@' + message['message']['from']['username'] if 'username' in message['message']['from'] else message['message']['from']['first_name']
        bot.send(config['admin_chat_id'], "User id {} with name {} has requested access to the bonnetjesprinter, moog det? typ /jejoa [id] om t te doon".format(message['message']['chat']['id'], user_name))
        print(message['message']['chat']['id'], config['admin_chat_id'])
        print(config['admin_chat_id'], "User id {} with name {} has requested access to the bonnetjesprinter, moog det? typ /jejoa [id] om t te doon".format(message['message']['chat']['id'], user_name))


def info(message):
    bot.send(message['message']['chat']['id'], "{}\nPrint access: {}".format(message, user_exists(message['message']['chat']['id'])))

def cut(message):
    p.cut()

def shell(message):
    if (message['message']['chat']['id'] == config['admin_chat_id']):
        try:
            cmd = message['message']['text'][7:]
            output = exec(cmd)
            print(output)
            bot.send(message['message']['chat']['id'], output)
        except:
            bot.send(message['message']['chat']['id'], "caused exception")

def die(message):
    if (message['message']['chat']['id'] == config['admin_chat_id']):
        raise KeyboardInterrupt

def approve_user(message):
    global bonbotdata
    if (message['message']['chat']['id'] == config['admin_chat_id']):
        user_id = message['message']['text'].split(" ")[1]

        if user_exists(user_id):
            bot.send(message['message']['chat']['id'], "The user you tried to approve is already in the database. Ignoring request")
            return
        new_user = {user_id: {"messages": 0, "characters": 0}}
        bonbotdata.update(new_user)
        with open("bonbotdata.json", "w") as f:
            ujson.dump(bonbotdata, f)
        bot.send(user_id, welcome_text)
        bot.send(message['message']['chat']['id'], "Access granted for user {}".format(user_id))
    else:
        bot.send(config['admin_chat_id'], "User {} tried to approve himself lmao".format(message['message']['chat']['id']))

def default(message):
    global bonbotdata
    # check if user is allowed
    if user_exists(message['message']['chat']['id']):
        bot.send(message['message']['chat']['id'], 'Bonnetjesprinter doet brrrr')
        tt = localtime(message['message']['date'])
        timestring = "{}-{}-{} {}:{}:{}".format(tt[2], tt[1], tt[0]-30, tt[3]+1, tt[4], tt[5])
        p.text("Om {} zei {}:\n{}".format(timestring, message['message']['from']['first_name'], message['message']['text']))
        output = str(message['message']['text'])
        p.text("".format(output))
        p.text("\n------------------------------------------\n")

        # update stats
        bonbotdata[str(message['message']['chat']['id'])]['messages'] += 1
        bonbotdata[str(message['message']['chat']['id'])]['characters'] += len(message['message']['text'])
        with open("bonbotdata.json", "w") as f:
            ujson.dump(bonbotdata, f)

        if config['auto_cut'] is True:
            p.cut()
    # id was not found, do nothing

def anonymous(message):
    user_name = '@' + message['message']['from']['username'] if 'username' in message['message']['from'] else message['message']['from']['first_name']
    bot.send(config['admin_chat_id'], "User {} sent an anonymous message!".format(user_name))

    message['message']['from']['first_name'] = "anonymous"
    message['message']['text'] = message['message']['text'][11:]
    default(message)

def helper(message):
    bot.send(message['message']['chat']['id'], help_text)

def stats(message):
    global bonbotdata
    tot_mes = 0
    tot_char = 0
    for entry in bonbotdata:
        tot_mes = tot_mes + bonbotdata[entry]['messages']
        tot_char = tot_char + bonbotdata[entry]['characters']
    totstats = "Total # of messages printed: {}\nTotal # of characters printed: {}".format(tot_mes, tot_char)
    bot.send(message['message']['chat']['id'], totstats)
    if (message['message']['chat']['id'] == config['admin_chat_id']):
        bot.send(message['message']['chat']['id'], bonbotdata)

def del_user(message):
    global bonbotdata
    if (message['message']['chat']['id'] == config['admin_chat_id']):
        user_id = message['message']['text'].split(" ")[1]
        if user_id in bonbotdata:
            del bonbotdata[user_id]
            with open("bonbotdata.json", "w") as f:
                ujson.dump(bonbotdata, f)
            bot.send(message['message']['chat']['id'], "user {} succesfully deleted".format(user_id))
        else:
            bot.send(message['message']['chat']['id'], "user {} not found in table".format(user_id))

def sendto(message):
    if (message['message']['chat']['id'] == config['admin_chat_id']):
        user_id = message['message']['text'].split(" ")[1]
        text = " ".join(message['message']['text'].split(" ")[2:])
        bot.send(user_id, text)
        bot.send(message['message']['chat']['id'], "Sent user {} the following message:\n{}".format(user_id, text))

if __name__ == "__main__":
    init()
    micropython.mem_info()
    print('registering bot...')
    bot = utelegram.ubot(config['token'])
    bot.register('/start', start)
    bot.register('/info', info)
    bot.register('/help', helper)
    bot.register('/anonymous', anonymous)
    bot.register('/stats', stats)

    bot.register('/jejoa', approve_user)
    bot.register('/deluser', del_user)
    bot.register('/cut', cut)
    bot.register('/shell', shell)
    bot.register('/quit', die)
    bot.register('/sendto', sendto)
    bot.set_default_handler(default)

    bot.send(config['admin_chat_id'], "Bot came online :D")
    print('Bot is now listening for commands')
    bot.listen()
    exit()