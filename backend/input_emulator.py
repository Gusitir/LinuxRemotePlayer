# input_emulator.py
import asyncio
try:
    import evdev
    from evdev import UInput, ecodes as e
    EVDEV_AVAILABLE = True
except ImportError:
    print("Warning: evdev not found. Virtual gamepad will be disabled. (Only supported on Linux)")
    EVDEV_AVAILABLE = False

class VirtualGamepad:
    def __init__(self):
        self.ui = None
        if not EVDEV_AVAILABLE:
            return
            
        cap = {
            e.EV_KEY: [e.BTN_A, e.BTN_B, e.BTN_X, e.BTN_Y, e.BTN_START, e.BTN_SELECT, e.BTN_DPAD_UP, e.BTN_DPAD_DOWN, e.BTN_DPAD_LEFT, e.BTN_DPAD_RIGHT]
        }
        try:
            self.ui = UInput(cap, name='LinuxRemotePlayer Virtual Pad', version=0x3)
        except Exception as ex:
            print(f"Warning: Could not init UInput (requires Linux + uinput permissions). {ex}")

    async def press_button(self, btn_code):
        if not self.ui or not EVDEV_AVAILABLE:
            print(f"[Mock] Button pressed: {btn_code}")
            return
            
        try:
            btn = getattr(e, btn_code)
            self.ui.write(e.EV_KEY, btn, 1)
            self.ui.syn()
            await asyncio.sleep(0.05)
            self.ui.write(e.EV_KEY, btn, 0)
            self.ui.syn()
        except AttributeError:
            print(f"Invalid button code: {btn_code}")

gamepad = VirtualGamepad()
