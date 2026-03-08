from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore import Qt, QPointF, pyqtSignal, QTimer, QElapsedTimer
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QPixmap, QRadialGradient
from interfaces.input import gamepad
import math

def square_to_circle(x: float, y: float) -> tuple[float, float]:
    if x == 0 and y == 0:
        return 0.0, 0.0
    X = x * math.sqrt(1 - (y ** 2) / 2)
    Y = y * math.sqrt(1 - (x ** 2) / 2)
    return X, Y

class QJoystickControl(QWidget):
    movimiento = pyqtSignal(float, float)
    movimiento_raw = pyqtSignal(float, float)
    activado = pyqtSignal()
    desactivado = pyqtSignal()

    def __init__(self, parent=None, radio=100, color_joystick=QColor(70, 130, 180),
                 color_borde=QColor(50, 50, 50), color_fondo = QColor(50, 50, 50), tamaño_joystick=20, icono_path=None,
                 usar_gamepad=False):
        super().__init__(parent)
        self.radio = radio
        self.tamaño_joystick = tamaño_joystick
        self.color_joystick = color_joystick
        self.color_borde = color_borde
        self.color_fondo = color_fondo
        self.posicion = QPointF(0, 0)
        self.pulsado = False
        self.sensibilidad = 1.0
        self.icono = QPixmap(icono_path) if icono_path else None

        # Variables de optimización
        self._ultima_posicion = QPointF(0, 0)
        self._necesita_repintado = True  # Inicialmente necesita repintado
        self._timer_repintado = QElapsedTimer()
        self._timer_repintado.start()
        self._repintado_en_progreso = False  # Prevenir repintados múltiples

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(radio, radio)

        # Buffer para fondo estático
        self._background = None
        self._needs_update_bg = True

        # Timer optimizado para actualización
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_ui)
        self._timer.start(16)  # ~60 FPS

        # Gamepad
        self.gamepad_thread = None
        if usar_gamepad:
            self.iniciar_gamepad_izquierdo()

    def iniciar_gamepad_izquierdo(self):
        self.gamepad_thread = gamepad.GamepadFullReader()
        self.gamepad_thread.left_stick_moved.connect(self.actualizar_desde_gamepad)
        self.gamepad_thread.start()

    def actualizar_desde_gamepad(self, x_norm, y_norm):
        x_c, y_c = square_to_circle(x_norm, y_norm)
        x = x_c * self.radio
        y = y_c * self.radio
        
        # Optimización: Solo actualizar si hay cambio significativo (> 0.1% del radio)
        umbral_cambio = self.radio * 0.001
        if (abs(x - self.posicion.x()) < umbral_cambio and 
            abs(y - self.posicion.y()) < umbral_cambio):
            return
            
        self.posicion = QPointF(x, y)
        self.movimiento.emit(x_c, y_c)
        self.movimiento_raw.emit(x, y)
        self._necesita_repintado = True

    def _update_ui(self):
        """Actualización optimizada: solo repinta si es necesario"""
        if self._necesita_repintado and not self._repintado_en_progreso:
            # Limitar FPS máximo a 60 para evitar sobrecarga
            if self._timer_repintado.hasExpired(16):  # ~60 FPS
                self._necesita_repintado = False
                self.update()
                self._timer_repintado.restart()

    def resizeEvent(self, event):
        tamaño = min(self.width(), self.height())
        self.radio = tamaño / 2
        self._needs_update_bg = True
        self._necesita_repintado = True
        super().resizeEvent(event)

    def _render_background(self):
        """Renderiza fondo estático optimizado"""
        if self.width() <= 0 or self.height() <= 0:
            return
            
        self._background = QPixmap(self.size())
        # Fondo sólido en lugar de transparente
        self._background.fill(self.color_fondo)  # Color de fondo sólido
        
        painter = QPainter(self._background)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width()/2, self.height()/2

        # Fondo circular
        painter.setBrush(QBrush(QColor(240, 240, 240)))  # Mismo color que el fondo
        painter.setPen(QPen(self.color_borde, 4))
        painter.drawEllipse(QPointF(cx, cy), self.radio, self.radio)

        # Sombra interior simplificada
        painter.setBrush(QBrush(QColor(0, 0, 0, 30)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), self.radio-2, self.radio-2)

        # Ejes guía (solo si el radio es suficientemente grande)
        if self.radio > 50:
            painter.setPen(QPen(QColor(180, 180, 180), 1, Qt.PenStyle.DashLine))
            painter.drawLine(QPointF(cx, cy - self.radio), QPointF(cx, cy + self.radio))
            painter.drawLine(QPointF(cx - self.radio, cy), QPointF(cx + self.radio, cy))

        # Anillos decorativos (solo si hay espacio)
        if self.radio > 80:
            painter.setPen(QPen(QColor(200, 200, 200, 100), 2))
            for r in [self.radio*0.5, self.radio*0.75]:
                painter.drawEllipse(QPointF(cx, cy), r, r)

        # Icono optimizado
        if self.icono and not self.icono.isNull():
            tamaño_icono = min(self.radio * 1.2, self.width(), self.height())
            if tamaño_icono > 10:  # Solo dibujar si es visible
                icono_escalado = self.icono.scaled(
                    int(tamaño_icono), int(tamaño_icono), 
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                painter.setOpacity(0.25)
                painter.drawPixmap(
                    int(cx - tamaño_icono/2), 
                    int(cy - tamaño_icono/2), 
                    icono_escalado
                )
                painter.setOpacity(1.0)
        painter.end()
        self._needs_update_bg = False

    def paintEvent(self, event):
        """Paint event optimizado y corregido"""
        if self._repintado_en_progreso:
            return
            
        self._repintado_en_progreso = True
        
        try:
            if self._needs_update_bg or self._background is None or self._background.size() != self.size():
                self._render_background()
            
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Dibujar fondo completo desde buffer
            if self._background:
                painter.drawPixmap(0, 0, self._background)
            
            # Dibujar joystick (siempre, pero optimizado)
            self._dibujar_joystick(painter)
            
        finally:
            self._repintado_en_progreso = False

    def _dibujar_joystick(self, painter):
        """Dibuja el joystick de forma optimizada"""
        x = self.width()/2 + self.posicion.x()
        y = self.height()/2 + self.posicion.y()
        
        # Solo dibujar si está dentro de los límites visibles
        if (x < -self.tamaño_joystick or x > self.width() + self.tamaño_joystick or
            y < -self.tamaño_joystick or y > self.height() + self.tamaño_joystick):
            return
            
        # Gradiente optimizado
        grad_joystick = QRadialGradient(
            x - self.tamaño_joystick / 3.0,
            y - self.tamaño_joystick / 3.0,
            self.tamaño_joystick * 1.5
        )
        grad_joystick.setColorAt(0.0, QColor(255, 255, 255, 230))
        grad_joystick.setColorAt(0.4, self.color_joystick.lighter(120))
        grad_joystick.setColorAt(1.0, self.color_joystick.darker(150))

        painter.setPen(QPen(self.color_borde, 2))
        painter.setBrush(QBrush(grad_joystick))
        painter.drawEllipse(
            QPointF(x, y),
            float(self.tamaño_joystick),
            float(self.tamaño_joystick)
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.pulsado = True
            self.actualizar_posicion(event)
            self.activado.emit()
            self._necesita_repintado = True

    def mouseMoveEvent(self, event):
        if self.pulsado and event.buttons() & Qt.MouseButton.LeftButton:
            self.actualizar_posicion(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.pulsado = False
            old_pos = self.posicion
            self.posicion = QPointF(0,0)
            
            # Solo emitir si había un cambio real
            if old_pos != QPointF(0,0):
                self.movimiento.emit(0,0)
                self.movimiento_raw.emit(0,0)
                
            self.desactivado.emit()
            self._necesita_repintado = True

    def actualizar_posicion(self, event):
        """Actualización de posición optimizada"""
        centro = QPointF(self.width()/2, self.height()/2)
        x = event.position().x() - centro.x()
        y = event.position().y() - centro.y()
        
        distancia = math.hypot(x, y)
        if distancia > self.radio:
            # Optimización: usar división directa
            factor = self.radio / distancia
            x *= factor
            y *= factor
            
        x *= self.sensibilidad
        y *= self.sensibilidad
        
        nueva_posicion = QPointF(x, y)
        
        # Solo actualizar si hay cambio significativo
        umbral = self.radio * 0.01
        if (abs(nueva_posicion.x() - self.posicion.x()) > umbral or 
            abs(nueva_posicion.y() - self.posicion.y()) > umbral):
            
            self.posicion = nueva_posicion
            self.movimiento.emit(x/self.radio, y/self.radio)
            self.movimiento_raw.emit(x, y)
            self._necesita_repintado = True

    # Métodos de ayuda (mantenidos igual)
    def get_posicion_normalizada(self):
        return self.posicion.x()/self.radio, self.posicion.y()/self.radio

    def get_posicion_normalizada_cartesiana(self):
        return self.posicion.x()/self.radio, -self.posicion.y()/self.radio

    def get_posicion_raw(self):
        return self.posicion.x(), self.posicion.y()

    def get_angulo(self):
        x, y = self.get_posicion_normalizada()
        return math.atan2(y, x)

    def get_magnitud(self):
        x, y = self.get_posicion_normalizada()
        return math.sqrt(x*x + y*y)

    def set_sensibilidad(self, valor):
        self.sensibilidad = max(0.1, min(2.0, valor))

    def reset(self):
        old_pos = self.posicion
        self.posicion = QPointF(0,0)
        
        # Solo emitir si había un cambio real
        if old_pos != QPointF(0,0):
            self.movimiento.emit(0,0)
            self.movimiento_raw.emit(0,0)
            
        self._necesita_repintado = True