# splash_screen.py

import sys
from PyQt6.QtWidgets import (
    QLabel, QProgressBar, QVBoxLayout, QWidget, QApplication, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QFont, QColor, QLinearGradient, QPainter, QMovie

from pantalla_de_carga.Windows_Cargas import Window_Carga



# splash_screen.py
class SplashScreen(QWidget):
    def __init__(self,main_window):
        super().__init__()
        self.main_window = main_window
        self.setFixedSize(650, 520)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Centrar en pantalla
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )

        self.setWindowOpacity(0.0)

        # Mensajes de carga
        self.messages = [
            "Despertando caparazón del sistema…",
            "Acomodando su caparazón digital…",
            "Sintonizando sensores al paso tortuga…",
            "Cargando sabiduría tortuguil de IA…",
            "Calibrando caminata lenta pero segura…",
            "Puliento su caparazón gráfico…",
            "Listo para avanzar con paso tortuga!",
        ]
        self.current_message_index = 0

        # Fondo
        self.bg_gradient = QLinearGradient(0, 0, 0, self.height())
        self.bg_gradient.setColorAt(0, QColor("#0d2b4a"))
        self.bg_gradient.setColorAt(1, QColor("#1e5c7a"))

        # Sombra
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)

        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.setSpacing(20)

        # Logo
        self.logo_label = QLabel()
        try:
            pixmap = QPixmap("logo.png").scaled(140, 140, Qt.AspectRatioMode.KeepAspectRatio,
                                                Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
        except:
            self.logo_label.setText("🐢")
            self.logo_label.setFont(QFont("Arial", 60))
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Título y crédito
        self.title_label = QLabel("Tortoise Bot")
        self.title_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: white;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.credit_label = QLabel("Design by GMIDEI")
        self.credit_label.setFont(QFont("Segoe UI", 12))
        self.credit_label.setStyleSheet("color: #a0d0ff;")
        self.credit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedWidth(450)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2ecc71;
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #0d2b4a, stop:1 #1e5c7a);
                color: white;
                font-weight: bold;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #2ecc71, stop:1 #3498db);
                border-radius: 10px;
            }
        """)

        # Mensaje dinámico
        self.message_label = QLabel(self.messages[0])
        self.message_label.setFont(QFont("Segoe UI", 11))
        self.message_label.setStyleSheet("color: #ecf0f1;")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # GIF
        self.gif_label = QLabel(self)
        self.gif_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.gif_label.setFixedSize(100, 70)
        self.gif_label.raise_()

        try:
            self.movie = QMovie("splash_animation.gif")
            self.movie.setScaledSize(self.gif_label.size())
            self.gif_label.setMovie(self.movie)
            self.movie.start()
        except:
            self.gif_label.setText("🎬")
            self.gif_label.setFont(QFont("Arial", 24))
            self.gif_label.setStyleSheet("color: #3498db; background: transparent;")
            self.gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Añadir widgets
        self.layout.addWidget(self.logo_label)
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.credit_label)
        self.layout.addSpacing(25)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.message_label)

        # Temporizadores
        self.fade_in_timer = QTimer()
        self.fade_in_timer.timeout.connect(self.fade_in)
        self.fade_in_timer.start(30)
        self.fade_step = 0.0

        self.load_timer = QTimer()
        self.load_timer.timeout.connect(self.simulate_loading)
        self.load_timer.setSingleShot(True)

    def fade_in(self):
        self.fade_step += 0.03
        self.setWindowOpacity(self.fade_step)
        if self.fade_step >= 1.0:
            self.fade_in_timer.stop()
            self.load_timer.start(500)

    def simulate_loading(self):
        self.progress = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(50)

    def update_progress(self):
        self.progress += 1
        self.progress_bar.setValue(self.progress)

        # Actualizar mensaje
        new_index = min(self.progress // 15, len(self.messages) - 1)
        if new_index != self.current_message_index:
            self.current_message_index = new_index
            self.message_label.setText(self.messages[new_index])

        if self.progress >= 100:
            self.timer.stop()
            QTimer.singleShot(800, self.open_main_window)

    # splash_screen.py (solo cambios importantes)
    def open_main_window(self):
        self.close()
        self.main_window.init_ui()
        self.main_window.show()


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self.bg_gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 22, 22)
        super().paintEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    splash = SplashScreen()
    splash.show()
    sys.exit(app.exec())
