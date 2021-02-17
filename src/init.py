wifi_config = {
    'ssid':'',
    'password':''
}

import network
import utime
from machine import UART

debug = True

uart = UART(2, 38400)
uart.init(38400, bits=8, parity=None, stop=1)
print("UART initialized")

sta_if = network.WLAN(network.STA_IF)
if not sta_if.isconnected():
    print("Connecting to network", end="")
    sta_if.active(True)
    sta_if.connect(wifi_config['ssid'], wifi_config['password'])
    while not sta_if.isconnected():
        print(".", end="")
        utime.sleep(.5)
        pass
print("\nNetwork Connection Established:")
print(sta_if.ifconfig())

exec(open('escpos.py').read())
p = SerialEscPos(uart)