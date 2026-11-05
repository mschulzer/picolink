import network
import socket
import time
import random
from machine import Pin, Timer

SSID = "pico-link"
PASSWORD = "picopico123"    # must be at least 8 characters
PORT = 5005
A_IP = "192.168.4.1"        # default address of a Pico W acting as access point

_HEARTBEAT_MS = 2000        # how often we say "I'm here" to the other Pico
_REPEATS = 3                # each message is sent this many times


class Link:
    """A connection to the other Pico."""

    def __init__(self, role, ssid=SSID, password=PASSWORD):
        role = role.upper()
        if role not in ("A", "B"):
            raise ValueError('role must be "A" or "B"')
        self.role = role
        self._peer_ip = A_IP if role == "B" else None   # A learns B's address later
        self._next_id = random.getrandbits(16)          # message counter
        self._last_seen_id = None
        self._last_heartbeat = time.ticks_ms()

        self._start_wifi(ssid, password)

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind(("0.0.0.0", PORT))
        self._sock.setblocking(False)
        self._send_raw("PING")
        print("Link ready as Pico", self.role)

    # ----- public -----

    def send(self, message):
        """Send a text message to the other Pico."""
        if self._peer_ip is None:
            print("picolink: the other Pico has not been seen yet - is it on?")
            return
        self._next_id = (self._next_id + 1) % 65536
        packet = "{}|{}".format(self._next_id, message)
        for _ in range(_REPEATS):
            self._send_raw(packet)

    def receive(self):
        """Return the next message from the other Pico, or None if there is none."""
        self._heartbeat()
        while True:
            try:
                data, addr = self._sock.recvfrom(256)
            except OSError:          # nothing waiting
                return None
            self._peer_ip = addr[0]  # remember who is talking to us
            text = data.decode()
            if text == "PING" or "|" not in text:
                continue
            msg_id, message = text.split("|", 1)
            if msg_id == self._last_seen_id:
                continue             # a repeat of a message we already returned
            self._last_seen_id = msg_id
            return message

    def peer_found(self):
        """True once we know where the other Pico is."""
        return self._peer_ip is not None

    # ----- behind the scenes -----

    def _start_wifi(self, ssid, password):
        if self.role == "A":
            ap = network.WLAN(network.AP_IF)
            ap.config(essid=ssid, password=password)
            ap.active(True)
            while not ap.active():
                time.sleep_ms(100)
            print("Wi-Fi network", ssid, "created")
        else:
            sta = network.WLAN(network.STA_IF)
            sta.active(True)
            sta.config(pm=0xa11140)  # power saving off -> faster messages
            sta.connect(ssid, password)
            print("Connecting to", ssid, end="")
            while not sta.isconnected():
                print(".", end="")
                time.sleep_ms(250)
            print(" connected")

    def _send_raw(self, text):
        if self._peer_ip is None:
            return
        try:
            self._sock.sendto(text.encode(), (self._peer_ip, PORT))
        except OSError:
            pass

    def _heartbeat(self):
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_heartbeat) >= _HEARTBEAT_MS:
            self._last_heartbeat = now
            self._send_raw("PING")


class Button:
    """A push button between a GPIO pin and GND."""

    def __init__(self, pin, double_press_ms=400, debounce_ms=30):
        self._pin = Pin(pin, Pin.IN, Pin.PULL_UP)   # reads 0 when pressed
        self._double_ms = double_press_ms
        self._debounce_ms = debounce_ms
        self._raw = 1
        self._stable = 1
        self._changed_at = time.ticks_ms()
        self._clicks = 0
        self._last_release = 0

    def is_pressed(self):
        """True while the button is held down."""
        return self._pin.value() == 0

    def get_press(self):
        """Return "single", "double" or None. Call this often (e.g. in your loop)."""
        now = time.ticks_ms()
        raw = self._pin.value()

        if raw != self._raw:                       # the contact is bouncing
            self._raw = raw
            self._changed_at = now
        elif raw != self._stable and time.ticks_diff(now, self._changed_at) >= self._debounce_ms:
            self._stable = raw                     # the change is real
            if raw == 1:                           # button was released
                self._clicks += 1
                self._last_release = now
                if self._clicks == 2:
                    self._clicks = 0
                    return "double"

        if (self._clicks == 1 and self._stable == 1
                and time.ticks_diff(now, self._last_release) > self._double_ms):
            self._clicks = 0                       # no second press came
            return "single"
        return None


class Led:
    """An LED on a GPIO pin. Use Led("LED") for the Pico W's built-in LED."""

    def __init__(self, pin):
        self._pin = Pin(pin, Pin.OUT, value=0)
        self._timer = None

    def on(self):
        self.stop_blinking()
        self._pin.value(1)

    def off(self):
        self.stop_blinking()
        self._pin.value(0)

    def toggle(self):
        self._pin.toggle()

    def start_blinking(self, interval_ms=250):
        """Blink in the background until stop_blinking() is called."""
        if self._timer is not None:
            return
        self._timer = Timer(period=interval_ms, mode=Timer.PERIODIC,
                            callback=lambda t: self._pin.toggle())

    def stop_blinking(self):
        if self._timer is not None:
            self._timer.deinit()
            self._timer = None
        self._pin.value(0)

    def is_blinking(self):
        return self._timer is not None
