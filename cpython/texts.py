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
/html shows extra help information regarding advanced text formatting options using html-like syntax

If you have any feature ideas or bug reports pls send a text to @LinhTran, or better yet, send them to the printer!
""")

html_text = (
""" Set text properties by sending them to the printer
It's possible to set text properties using a html-like formatting.
Format options can be set using opening tags: <option value>, and unset (set to default) by using a closing tag: </option>. Tags are reset to default after every message. The text that is printed after a tag will be printed using that option.

For example:
<f b>this prints in an alternative font
but font a is nicer </f>
<bold>text from now on will be in bold
<ul 1>this text has a line below</ul>
<a center><ul 2>the line is now denser, and the text is centered</ul></a></bold>
<cs><w 3><h 3>this text is bigger, no more bold!</w></h></cs>
<i>this text prints white on black</i>
<fl>and this one is upside down!</fl>

Tags can be called using their full name <font a> or by using a shorthand notation <f a>, either notion has the same effect. Keep in mind that opening and closing tags need to be set using the same hand-ness in notation i.e. if you enable an option using shorthand notation tags you can't close it using the longhand notation. You can mix handness for different tags however. For example:
<bold><f a> hello </f></bold>     # this is valid
<bold><f a> hello </font></bold>  # this will throw an error

Some options need to be called while specifying a value, others are simply enabled by calling the opening tag and disabled by calling the closing tag as can be seen in the example above. The following options and values are available:

underline: underline mode for text, integer value defines density
double_height: doubles the height of the text
double_width: doubles the width of the text
custom_size: uses custom size specified by width and height parameters. Cannot be used with double_width or double_height.
width: text width multiplier when custom_size is used
height: text height multiplier when custom_size is used
density: print density, value from 0-8
invert: True enables white on black printing
flip: True enables upside-down printing

<f>  <font>          a, b                  default: a
<a>  <align>         left, center, right   default: left
<w>  <width>         1-8                   default: 1
<h>  <height>        1-8                   default: 1
<d>  <density>       0-8                   default: 8
<u>  <underline>     0-2                   default: 0
<i>  <invert>        bool                  default: off
<b>  <bold>          bool                  default: off
<s>  <smooth>        bool                  default: off
<fl> <flip>          bool                  default: off
<cs> <custom_size>   bool                  default: off 
<dw> <double_width>  bool                  default: off 
<dh> <double_height> bool                  default: off 

Lastly, it's also possible to print qr codes using:
<qr src=some_data>

p.s. will fix formatting of the above 'table' in the future!
"""
)

printing_text = (
  """Bonnetjesprinter doet brrrr"""
)

