# main_window.py
from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont, QLinearGradient, QPainter, QColor

class Window_Carga(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tortoise Bot - Principal")
        self.setGeometry(0, 0, 1000, 700)
        self.center_window()

        # Fondo con gradiente
        self.bg_gradient = QLinearGradient(0, 0, 0, self.height())
        self.bg_gradient.setColorAt(0, QColor("#0d2b4a"))
        self.bg_gradient.setColorAt(1, QColor("#1e5c7a"))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)

        # Logo en ventana principal
        logo_label = QLabel()
        try:
            pixmap = QPixmap("logo.png").scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        except:
            logo_label.setText("🐢")
            logo_label.setFont(QFont("Arial", 60))
        layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Título
        title = QLabel("Bienvenido a Tortoise Bot")
        title.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        # Crédito
        credit = QLabel("Elaborado por GMIDEI")
        credit.setFont(QFont("Segoe UI", 18))
        credit.setStyleSheet("color: #a0d0ff;")
        layout.addWidget(credit, alignment=Qt.AlignmentFlag.AlignCenter)

        # Botón de ejemplo
        self.btn = QPushButton("Iniciar")
        self.btn.setFont(QFont("Segoe UI", 16))
        self.btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #2ecc71, stop:1 #3498db);
                color: white;
                border-radius: 12px;
                padding: 12px 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #27ae60, stop:1 #2980b9);
            }
        """)
        layout.addWidget(self.btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def center_window(self):
        screen = self.screen().geometry()
        window_width = self.width()
        window_height = self.height()
        x = (screen.width() - window_width) // 2
        y = (screen.height() - window_height) // 2
        self.move(x, y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), self.bg_gradient)
        super().paintEvent(event)