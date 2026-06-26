# input_emulator.py
import asyncio
import string

try:
    import evdev
    from evdev import UInput, ecodes as e
    EVDEV_AVAILABLE = True
except ImportError:
    print("Warning: evdev not found. Virtual input disabled. (Only supported on Linux)")
    EVDEV_AVAILABLE = False


def _build_char_keys():
    """Map characters -> (evdev key name, needs_shift) for a US layout."""
    m = {}
    for c in string.ascii_lowercase:
        m[c] = (f"KEY_{c.upper()}", False)
    for c in string.ascii_uppercase:
        m[c] = (f"KEY_{c}", True)
    for d in "0123456789":
        m[d] = (f"KEY_{d}", False)
    m[" "] = ("KEY_SPACE", False)
    m["\n"] = ("KEY_ENTER", False)
    m["\t"] = ("KEY_TAB", False)
    pairs = {
        "-": ("KEY_MINUS", False), "_": ("KEY_MINUS", True),
        "=": ("KEY_EQUAL", False), "+": ("KEY_EQUAL", True),
        "[": ("KEY_LEFTBRACE", False), "{": ("KEY_LEFTBRACE", True),
        "]": ("KEY_RIGHTBRACE", False), "}": ("KEY_RIGHTBRACE", True),
        ";": ("KEY_SEMICOLON", False), ":": ("KEY_SEMICOLON", True),
        "'": ("KEY_APOSTROPHE", False), '"': ("KEY_APOSTROPHE", True),
        "`": ("KEY_GRAVE", False), "~": ("KEY_GRAVE", True),
        "\\": ("KEY_BACKSLASH", False), "|": ("KEY_BACKSLASH", True),
        ",": ("KEY_COMMA", False), "<": ("KEY_COMMA", True),
        ".": ("KEY_DOT", False), ">": ("KEY_DOT", True),
        "/": ("KEY_SLASH", False), "?": ("KEY_SLASH", True),
        "!": ("KEY_1", True), "@": ("KEY_2", True), "#": ("KEY_3", True),
        "$": ("KEY_4", True), "%": ("KEY_5", True), "^": ("KEY_6", True),
        "&": ("KEY_7", True), "*": ("KEY_8", True), "(": ("KEY_9", True),
        ")": ("KEY_0", True),
    }
    m.update(pairs)
    return m


CHAR_KEYS = _build_char_keys()


class VirtualGamepad:
    """Virtual keyboard: navigation keys, media keys, and free text typing."""

    def __init__(self):
        self.ui = None
        if not EVDEV_AVAILABLE:
            return
        # Codes 1..99 cover the standard typing keys; the named ones add the rest.
        keys = list(range(1, 100)) + [
            e.BTN_A, e.BTN_B, e.BTN_X, e.BTN_Y, e.BTN_START, e.BTN_SELECT,
            e.BTN_DPAD_UP, e.BTN_DPAD_DOWN, e.BTN_DPAD_LEFT, e.BTN_DPAD_RIGHT,
            e.KEY_UP, e.KEY_DOWN, e.KEY_LEFT, e.KEY_RIGHT, e.KEY_ENTER, e.KEY_ESC,
            e.KEY_BACKSPACE, e.KEY_TAB, e.KEY_LEFTSHIFT,
            e.KEY_PLAYPAUSE, e.KEY_PLAY, e.KEY_PAUSE, e.KEY_STOP,
            e.KEY_NEXTSONG, e.KEY_PREVIOUSSONG, e.KEY_FASTFORWARD, e.KEY_REWIND,
            e.KEY_VOLUMEUP, e.KEY_VOLUMEDOWN, e.KEY_MUTE,
        ]
        try:
            self.ui = UInput({e.EV_KEY: keys}, name='LinuxRemotePlayer Virtual Keyboard', version=0x3)
        except Exception as ex:
            print(f"Warning: Could not init keyboard UInput (needs Linux + uinput perms). {ex}")

    async def press_button(self, btn_code):
        if not self.ui or not EVDEV_AVAILABLE:
            print(f"[Mock] Key: {btn_code}")
            return
        try:
            btn = getattr(e, btn_code)
        except AttributeError:
            print(f"Invalid key code: {btn_code}")
            return
        self.ui.write(e.EV_KEY, btn, 1)
        self.ui.syn()
        await asyncio.sleep(0.04)
        self.ui.write(e.EV_KEY, btn, 0)
        self.ui.syn()

    async def type_text(self, text):
        if not self.ui or not EVDEV_AVAILABLE:
            print(f"[Mock] type: {text}")
            return
        for ch in text:
            entry = CHAR_KEYS.get(ch)
            if not entry:
                continue
            keyname, shift = entry
            code = getattr(e, keyname, None)
            if code is None:
                continue
            if shift:
                self.ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 1)
                self.ui.syn()
            self.ui.write(e.EV_KEY, code, 1)
            self.ui.syn()
            self.ui.write(e.EV_KEY, code, 0)
            self.ui.syn()
            if shift:
                self.ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 0)
                self.ui.syn()
            await asyncio.sleep(0.005)


class VirtualMouse:
    """Virtual relative-pointer mouse for the on-screen touchpad."""

    def __init__(self):
        self.ui = None
        if not EVDEV_AVAILABLE:
            return
        cap = {
            e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT],
            e.EV_REL: [e.REL_X, e.REL_Y, e.REL_WHEEL],
        }
        try:
            self.ui = UInput(cap, name='LinuxRemotePlayer Virtual Mouse', version=0x3)
        except Exception as ex:
            print(f"Warning: Could not init mouse UInput (needs Linux + uinput perms). {ex}")

    async def move(self, dx, dy):
        if not self.ui or not EVDEV_AVAILABLE:
            return
        try:
            self.ui.write(e.EV_REL, e.REL_X, int(dx))
            self.ui.write(e.EV_REL, e.REL_Y, int(dy))
            self.ui.syn()
        except Exception as ex:
            print(f"Mouse move error: {ex}")

    async def click(self, button="left"):
        if not self.ui or not EVDEV_AVAILABLE:
            print(f"[Mock] click: {button}")
            return
        code = e.BTN_RIGHT if button == "right" else e.BTN_LEFT
        self.ui.write(e.EV_KEY, code, 1)
        self.ui.syn()
        await asyncio.sleep(0.02)
        self.ui.write(e.EV_KEY, code, 0)
        self.ui.syn()

    async def scroll(self, amount):
        if not self.ui or not EVDEV_AVAILABLE:
            return
        self.ui.write(e.EV_REL, e.REL_WHEEL, 1 if amount > 0 else -1)
        self.ui.syn()


gamepad = VirtualGamepad()
mouse = VirtualMouse()
