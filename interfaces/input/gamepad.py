from PyQt6.QtCore import QThread, pyqtSignal
from inputs import get_gamepad

class GamepadFullReader(QThread):
    """
    Lee todos los ejes y botones del gamepad en tiempo real.
    Emite señales para joystick y botones.
    """

    # Señales de joystick (x, y)
    left_stick_moved = pyqtSignal(float, float)
    right_stick_moved = pyqtSignal(float, float)

    # Señales de botones (True = presionado, False = liberado)
    button_changed = pyqtSignal(str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True

        # === Estado del mando ===
        # Joysticks
        self.left_x = 0.0
        self.left_y = 0.0
        self.right_x = 0.0
        self.right_y = 0.0

        # Botones
        self.buttons = {
            # Frontales
            "A": False,
            "B": False,
            "X": False,
            "Y": False,

            # Gatillos / bumpers
            "L1": False,
            "R1": False,
            "L2": False,
            "R2": False,

            # Opcionales
            "START": False,
            "SELECT": False,
            "L3": False,  # Pulsar joystick izquierdo
            "R3": False,  # Pulsar joystick derecho
        }

    def run(self):
        print("🎮 GamepadFullReader iniciado.")
        while self._running:
            try:
                events = get_gamepad()
                for e in events:
                    code = e.code
                    state = e.state

                    # === JOYSTICKS ===
                    if code == "ABS_X":
                        self.left_x = self._normalize(state)
                        self.left_stick_moved.emit(self.left_x, self.left_y)

                    elif code == "ABS_Y":
                        self.left_y = self._normalize(state)
                        self.left_stick_moved.emit(self.left_x, self.left_y)

                    elif code == "ABS_RX" or code == "ABS_Z":
                        self.right_x = self._normalize(state)
                        self.right_stick_moved.emit(self.right_x, self.right_y)

                    elif code == "ABS_RY" or code == "ABS_RZ":
                        self.right_y = self._normalize(state)
                        self.right_stick_moved.emit(self.right_x, self.right_y)

                    # === BOTONES ===
                    elif code == "BTN_SOUTH":  # A
                        self._update_button("A", state)
                    elif code == "BTN_EAST":   # B
                        self._update_button("B", state)
                    elif code == "BTN_NORTH":  # Y
                        self._update_button("Y", state)
                    elif code == "BTN_WEST":   # X
                        self._update_button("X", state)
                    elif code == "BTN_TL":     # L1
                        self._update_button("L1", state)
                    elif code == "BTN_TR":     # R1
                        self._update_button("R1", state)
                    elif code == "BTN_TL2":    # L2 (analógico → presionado si >0)
                        self._update_button("L2", state > 0)
                    elif code == "BTN_TR2":    # R2
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
                continue

        print("🎮 GamepadFullReader detenido.")

    # ---------------------------
    # 🔧 MÉTODOS AUXILIARES
    # ---------------------------
    def _normalize(self, value):
        """Convierte rango 0–255 (centro 128) a [-1, 1]."""
        value = max(0, min(255, value))
        return (value - 128) / 127.0

    def _update_button(self, name, pressed):
        """Actualiza estado del botón y emite señal solo si cambia."""
        pressed = bool(pressed)
        if self.buttons.get(name) != pressed:
            self.buttons[name] = pressed
            self.button_changed.emit(name, pressed)

    def stop(self):
        self._running = False
        self.quit()
        self.wait()
