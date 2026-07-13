# input_emulator.py
import asyncio
import string
import time
import logging

logger = logging.getLogger("input_emulator")

try:
    import evdev
    from evdev import UInput, ecodes as e
    EVDEV_AVAILABLE = True
except ImportError:
    logger.warning("evdev not found. Virtual input disabled. (Only supported on Linux)")
    EVDEV_AVAILABLE = False

ALLOWED_KEYS = frozenset({
    "KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT", "KEY_ENTER", "KEY_ESC",
    "KEY_BACKSPACE", "KEY_TAB", "KEY_LEFTSHIFT", "KEY_SPACE",
    "KEY_PLAYPAUSE", "KEY_PLAY", "KEY_PAUSE", "KEY_STOP",
    "KEY_NEXTSONG", "KEY_PREVIOUSSONG", "KEY_FASTFORWARD", "KEY_REWIND",
    "KEY_VOLUMEUP", "KEY_VOLUMEDOWN", "KEY_MUTE", "KEY_LEFTMETA"
})


def _build_char_keys():
    """Map characters -> (evdev key name, needs_shift) for a given layout."""
    import os
    layout = os.getenv("KEYBOARD_LAYOUT", "us").lower()
    
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
    
    # Inmediato y universal para slash (funciona en todos los layouts vía numpad)
    m["/"] = ("KEY_KPSLASH", False)

    # Diferencias es/latam
    if layout in ("es", "latam"):
        es_pairs = {
            "-": ("KEY_SLASH", False), "_": ("KEY_SLASH", True),
            ";": ("KEY_COMMA", True), ":": ("KEY_DOT", True),
            "'": ("KEY_MINUS", False), '"': ("KEY_2", True),
            "=": ("KEY_0", True), "?": ("KEY_MINUS", True)
        }
        m.update(es_pairs)
        
    return m


CHAR_KEYS = _build_char_keys()


class VirtualGamepad:
    """Virtual keyboard: navigation keys, media keys, and free text typing."""

    def __init__(self):
        self.ui = None
        self._last_init_attempt = 0
        if not EVDEV_AVAILABLE:
            return
        self._try_init()

    def _try_init(self):
        keys = list(range(1, 100)) + [
            e.BTN_A, e.BTN_B, e.BTN_X, e.BTN_Y, e.BTN_START, e.BTN_SELECT,
            e.BTN_DPAD_UP, e.BTN_DPAD_DOWN, e.BTN_DPAD_LEFT, e.BTN_DPAD_RIGHT,
            e.KEY_UP, e.KEY_DOWN, e.KEY_LEFT, e.KEY_RIGHT, e.KEY_ENTER, e.KEY_ESC,
            e.KEY_BACKSPACE, e.KEY_TAB, e.KEY_LEFTSHIFT,
            e.KEY_PLAYPAUSE, e.KEY_PLAY, e.KEY_PAUSE, e.KEY_STOP,
            e.KEY_NEXTSONG, e.KEY_PREVIOUSSONG, e.KEY_FASTFORWARD, e.KEY_REWIND,
            e.KEY_VOLUMEUP, e.KEY_VOLUMEDOWN, e.KEY_MUTE, e.KEY_LEFTMETA,
            e.KEY_LEFTALT, e.KEY_F4
        ]
        try:
            self.ui = UInput({e.EV_KEY: keys}, name='LinuxRemotePlayer Virtual Keyboard', version=0x3)
            logger.info("UInput keyboard device created successfully.")
            
            # Startup guard
            caps = self.ui.capabilities()
            if e.EV_KEY in caps:
                device_keys = set(caps[e.EV_KEY])
                required_names = set(ALLOWED_KEYS) | {"KEY_LEFTALT", "KEY_F4"}
                missing = []
                for k in required_names:
                    code = getattr(e, k, None)
                    if code is not None and code not in device_keys:
                        missing.append(k)
                if missing:
                    logger.error(f"UInput device missing required capabilities for keys: {missing}")

        except Exception as ex:
            logger.warning(f"Could not init keyboard UInput (needs Linux + uinput perms). {ex}")

    def _ensure_ui(self):
        if self.ui is not None or not EVDEV_AVAILABLE:
            return
        now = time.time()
        if now - self._last_init_attempt < 5.0:
            return
        self._last_init_attempt = now
        logger.info("Retrying UInput keyboard device creation (late init)...")
        self._try_init()

    async def press_button(self, btn_code):
        if btn_code not in ALLOWED_KEYS:
            logger.warning(f"Key press rejected (not in whitelist): {btn_code}")
            return
        self._ensure_ui()
        if not self.ui or not EVDEV_AVAILABLE:
            logger.debug(f"[Mock] Key: {btn_code}")
            return
        try:
            btn = getattr(e, btn_code)
        except AttributeError:
            logger.error(f"Invalid key code: {btn_code}")
            return
        self.ui.write(e.EV_KEY, btn, 1)
        self.ui.syn()
        await asyncio.sleep(0.04)
        self.ui.write(e.EV_KEY, btn, 0)
        self.ui.syn()

    async def type_text(self, text):
        self._ensure_ui()
        if not self.ui or not EVDEV_AVAILABLE:
            logger.debug(f"[Mock] type: {text}")
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

    async def press_combo(self, combo_name):
        self._ensure_ui()
        if not self.ui or not EVDEV_AVAILABLE:
            logger.debug(f"[Mock] combo: {combo_name}")
            return
            
        COMBOS = {
            "browser_back": ["KEY_LEFTALT", "KEY_LEFT"],
            "close_window": ["KEY_LEFTALT", "KEY_F4"],
        }
        
        if combo_name not in COMBOS:
            logger.warning(f"Combo rejected (not in whitelist): {combo_name}")
            return
            
        keys = COMBOS[combo_name]
        try:
            btn_codes = [getattr(e, k) for k in keys]
        except AttributeError as ex:
            logger.error(f"Invalid combo keys: {ex}")
            return
            
        # Press all down
        for code in btn_codes:
            self.ui.write(e.EV_KEY, code, 1)
        self.ui.syn()
        
        await asyncio.sleep(0.04)
        
        # Release all up in reverse order
        for code in reversed(btn_codes):
            self.ui.write(e.EV_KEY, code, 0)
        self.ui.syn()


class VirtualMouse:
    """Virtual relative-pointer mouse for the on-screen touchpad."""

    def __init__(self):
        self.ui = None
        self._last_init_attempt = 0
        if not EVDEV_AVAILABLE:
            return
        self._try_init()

    def _try_init(self):
        cap = {
            e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT],
            e.EV_REL: [e.REL_X, e.REL_Y, e.REL_WHEEL],
        }
        try:
            self.ui = UInput(cap, name='LinuxRemotePlayer Virtual Mouse', version=0x3)
            logger.info("UInput mouse device created successfully.")
        except Exception as ex:
            logger.error(f"Could not init mouse UInput (needs Linux + uinput perms). {ex}")

    def _ensure_ui(self):
        if self.ui is not None or not EVDEV_AVAILABLE:
            return
        now = time.time()
        if now - self._last_init_attempt < 5.0:
            return
        self._last_init_attempt = now
        logger.info("Retrying UInput mouse device creation (late init)...")
        self._try_init()

    async def move(self, dx, dy):
        self._ensure_ui()
        if not self.ui or not EVDEV_AVAILABLE:
            return
        try:
            self.ui.write(e.EV_REL, e.REL_X, int(dx))
            self.ui.write(e.EV_REL, e.REL_Y, int(dy))
            self.ui.syn()
        except Exception as ex:
            logger.error(f"Mouse move error: {ex}")

    async def click(self, button="left"):
        self._ensure_ui()
        if not self.ui or not EVDEV_AVAILABLE:
            logger.debug(f"[Mock] click: {button}")
            return
        code = e.BTN_RIGHT if button == "right" else e.BTN_LEFT
        self.ui.write(e.EV_KEY, code, 1)
        self.ui.syn()
        await asyncio.sleep(0.02)
        self.ui.write(e.EV_KEY, code, 0)
        self.ui.syn()

    async def scroll(self, amount):
        self._ensure_ui()
        if not self.ui or not EVDEV_AVAILABLE:
            return
        try:
            n = int(amount)
        except (TypeError, ValueError):
            return
        step = 1 if n >= 0 else -1
        for _ in range(min(abs(n) or 1, 15)):
            self.ui.write(e.EV_REL, e.REL_WHEEL, step)
            self.ui.syn()


gamepad = VirtualGamepad()
mouse = VirtualMouse()
