# main.py
import sys
from PyQt6.QtWidgets import QApplication
from .splash_screen import SplashScreen

if __name__ == "__main__":
    app = QApplication(sys.argv)
    splash = SplashScreen()
    splash.show()
    sys.exit(app.exec())