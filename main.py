# Necessary imports
from picolink import Link, Button, Led

link = Link("B")
button = Button(14)
led = Led(15)

while True:
    press = button.get_press()
    if press == "single":
        link.send("BLINK")
    elif press == "double" and led.is_blinking():
        led.stop_blinking()
        link.send("STOPPED")

    message = link.receive()
    if message == "BLINK":
        led.start_blinking()
    elif message == "STOPPED":
        print("The other Pico stopped blinking")
