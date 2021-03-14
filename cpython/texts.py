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
This all used to run on an ESP, but was moved to a raspberry pi since image and extended character set support were added. If anyone knows how to dynamically interpret and switch character sets on a per character basis, as well as doing image manipulation with the limited resources of an ESP pls let me know ;p
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

printing_text = (
  """Bonnetjesprinter doet brrrr"""
)
