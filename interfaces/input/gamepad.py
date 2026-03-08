from PyQt6.QtCore import QThread, pyqtSignal

try:
    from inputs import get_gamepad

    GAMEPAD_BACKEND_OK = True
except ImportError:
    get_gamepad = None
    GAMEPAD_BACKEND_OK = False


class GamepadFullReader(QThread):
    """Lee ejes/botones del gamepad y emite señales normalizadas."""

    left_stick_moved = pyqtSignal(float, float)
    right_stick_moved = pyqtSignal(float, float)
    button_changed = pyqtSignal(str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True
        self._warned_backend = False

        self.left_x = 0.0
        self.left_y = 0.0
        self.right_x = 0.0
        self.right_y = 0.0

        self.buttons = {
            "A": False,
            "B": False,
            "X": False,
            "Y": False,
            "L1": False,
            "R1": False,
            "L2": False,
            "R2": False,
            "START": False,
            "SELECT": False,
            "L3": False,
            "R3": False,
        }

    def run(self):
        print("🎮 GamepadFullReader iniciado.")

        while self._running:
            if not GAMEPAD_BACKEND_OK or get_gamepad is None:
                if not self._warned_backend:
                    print("⚠️ Librería 'inputs' no disponible: gamepad deshabilitado")
                    self._warned_backend = True
                self.msleep(250)
                continue

            try:
                events = get_gamepad()
                for e in events:
                    code = e.code
                    state = e.state

                    if code == "ABS_X":
                        self.left_x = self._normalize(state)
                        self.left_stick_moved.emit(self.left_x, self.left_y)
                    elif code == "ABS_Y":
                        self.left_y = self._normalize(state)
                        self.left_stick_moved.emit(self.left_x, self.left_y)
                    elif code in ("ABS_RX", "ABS_Z"):
                        self.right_x = self._normalize(state)
                        self.right_stick_moved.emit(self.right_x, self.right_y)
                    elif code in ("ABS_RY", "ABS_RZ"):
                        self.right_y = self._normalize(state)
                        self.right_stick_moved.emit(self.right_x, self.right_y)
                    elif code == "BTN_SOUTH":
                        self._update_button("A", state)
                    elif code == "BTN_EAST":
                        self._update_button("B", state)
                    elif code == "BTN_NORTH":
                        self._update_button("Y", state)
                    elif code == "BTN_WEST":
                        self._update_button("X", state)
                    elif code == "BTN_TL":
                        self._update_button("L1", state)
                    elif code == "BTN_TR":
                        self._update_button("R1", state)
                    elif code == "BTN_TL2":
                        self._update_button("L2", state > 0)
                    elif code == "BTN_TR2":
                        self._update_button("R2", state > 0)
                    elif code == "BTN_THUMBL":
                        self._update_button("L3", state)
                    elif code == "BTN_THUMBR":
                        self._update_button("R3", state)
                    elif code == "BTN_START":
                        self._update_button("START", state)
                    elif code == "BTN_SELECT":
                        self._update_button("SELECT", state)

                self.msleep(20)
            except Exception:
                self.msleep(50)

        print("🎮 GamepadFullReader detenido.")

    def _normalize(self, value):
        value = max(0, min(255, value))
        return (value - 128) / 127.0

    def _update_button(self, name, pressed):
        pressed = bool(pressed)
        if self.buttons.get(name) != pressed:
            self.buttons[name] = pressed
            self.button_changed.emit(name, pressed)

    def stop(self):
        self._running = False
        self.quit()
        self.wait()
