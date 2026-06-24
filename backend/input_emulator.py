# input_emulator.py
import evdev
from evdev import UInput, ecodes as e

class VirtualGamepad:
    def __init__(self):
        cap = {
            e.EV_KEY: [e.BTN_A, e.BTN_B, e.BTN_X, e.BTN_Y, e.BTN_START, e.BTN_SELECT, e.BTN_DPAD_UP, e.BTN_DPAD_DOWN, e.BTN_DPAD_LEFT, e.BTN_DPAD_RIGHT]
        }
        try:
            self.ui = UInput(cap, name='LinuxRemotePlayer Virtual Pad', version=0x3)
        except Exception as ex:
            print(f"Warning: Could not init UInput (requires Linux + uinput permissions). {ex}")
            self.ui = None

    def press_button(self, btn_code):
        if not self.ui: return
        try:
            btn = getattr(e, btn_code)
            self.ui.write(e.EV_KEY, btn, 1)
            self.ui.syn()
            self.ui.write(e.EV_KEY, btn, 0)
            self.ui.syn()
        except AttributeError:
            print(f"Invalid button code: {btn_code}")

gamepad = VirtualGamepad()
