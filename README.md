# picolink

**Simple Pico W to Pico W messaging, plus easy buttons and LEDs.**

`picolink` lets two Raspberry Pi Pico W boards send text messages to each other over Wi-Fi. No router, no IP addresses and no networking code are needed. It also includes simple `Button` and `Led` classes, so you can focus on what your program should *do*.

---

## Getting started

1. Copy `picolink.py` onto **both** Picos, next to `main.py`.
2. In `main.py`, import the library and set up your hardware:

```python
from picolink import Link, Button, Led

link = Link("A")          # use "B" on the other Pico
button = Button(14)       # button between GP14 and GND
led = Led(15)             # LED (with resistor) between GP15 and GND
```

> **Tip:** One Pico must be `"A"` and the other `"B"`. That is the only difference between the two boards.

---

## What you can do

### Link: talk to the other Pico

| Code | What it does |
|------|--------------|
| `link.send("HELLO")` | Sends a text message to the other Pico |
| `link.receive()` | Returns the next message as text, or `None` if there is none |

### Button

| Code | What it does |
|------|--------------|
| `button.get_press()` | Returns `"single"`, `"double"` or `None` |
| `button.is_pressed()` | Returns `True` while the button is held down |

### Led

| Code | What it does |
|------|--------------|
| `led.on()` | Turns the LED on |
| `led.off()` | Turns the LED off |
| `led.toggle()` | Switches the LED between on and off |
| `led.start_blinking()` | Starts blinking by itself in the background |
| `led.stop_blinking()` | Stops blinking |
| `led.is_blinking()` | Returns `True` or `False` |

---

## How it works (for the curious)

- Pico **A** creates its own small Wi-Fi network, and Pico **B** joins it.
- Messages travel as small **UDP packets**.
- Wi-Fi can lose packets, so each message is **sent a few times**. Duplicates are **filtered out** on arrival, so each message reaches your program only once.
