from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QStackedWidget, QLabel, QGroupBox, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QPainterPath, QImage, QPixmap
import math
try:
    import cv2
    import numpy as np
    CAMERA_LIBS_OK = True
except ImportError:
    cv2 = None
    np = None
    CAMERA_LIBS_OK = False

class CameraDiagramWidget(QWidget):
    """Widget que permite cambiar entre vista de cámara y diagrama del robot"""
    
    # Señal para cuando se cambia de modo
    modo_cambiado = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
        # Estado del robot (simulado por ahora)
        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_orientacion = 0.0  # En radianes
    
        # Nodo ROS que proporcionará frames
        self.ros_camera_node = None
    
        # Configuración de UI
        self.setup_ui()
        self.setup_camera()

    def conectar_nodo_ros(self, nodo):
        """Conecta el nodo ROS de cámara al widget"""
        self.ros_camera_node = nodo
        # Pasar el nodo al widget de cámara
        self.widget_camara.conectar_nodo_ros(nodo)
        print("✅ Nodo ROS conectado al widget de cámara")
        
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        layout_principal = QVBoxLayout(self)
        
        # Botones de selección de modo
        layout_botones = QHBoxLayout()
        
        self.btn_camara = QPushButton("📹 Cámara")
        self.btn_camara.setCheckable(True)
        self.btn_camara.setChecked(True)
        self.btn_camara.clicked.connect(self.cambiar_a_camara)
        
        self.btn_diagrama = QPushButton("🤖 Diagrama Robot")
        self.btn_diagrama.setCheckable(True)
        self.btn_diagrama.clicked.connect(self.cambiar_a_diagrama)
        
        layout_botones.addWidget(self.btn_camara)
        layout_botones.addWidget(self.btn_diagrama)
        layout_botones.addStretch()
        
        # Widget apilado para cambiar entre vistas
        self.stacked_widget = QStackedWidget()
        
        # Widget de cámara
        self.widget_camara = CameraWidget()
        
        # Widget de diagrama del robot
        self.widget_diagrama = RobotDiagramWidget()
        
        self.stacked_widget.addWidget(self.widget_camara)
        self.stacked_widget.addWidget(self.widget_diagrama)
        
        layout_principal.addLayout(layout_botones)
        layout_principal.addWidget(self.stacked_widget)
        
        # Estilo de los botones
        self.actualizar_estilo_botones()
        
    def setup_camera(self):
        """Configuración inicial de la cámara"""
        # Iniciar en modo simulado hasta que lleguen datos reales
        self.widget_camara.iniciar_camara_simulada()
        
    def cambiar_a_camara(self):
        """Cambia a la vista de cámara"""
        self.stacked_widget.setCurrentWidget(self.widget_camara)
        self.btn_camara.setChecked(True)
        self.btn_diagrama.setChecked(False)
        self.actualizar_estilo_botones()
        self.modo_cambiado.emit("camara")
        
    def cambiar_a_diagrama(self):
        """Cambia a la vista de diagrama del robot"""
        self.stacked_widget.setCurrentWidget(self.widget_diagrama)
        self.btn_diagrama.setChecked(True)
        self.btn_camara.setChecked(False)
        self.actualizar_estilo_botones()
        self.modo_cambiado.emit("diagrama")
        
    def actualizar_estilo_botones(self):
        """Actualiza el estilo de los botones según el modo activo"""
        estilo_activo = """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border: 2px solid #45a049;
                padding: 8px 16px;
                border-radius: 4px;
            }
        """
        
        estilo_inactivo = """
            QPushButton {
                background-color: #f0f0f0;
                color: #333;
                border: 2px solid #ccc;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """
        
        self.btn_camara.setStyleSheet(estilo_activo if self.btn_camara.isChecked() else estilo_inactivo)
        self.btn_diagrama.setStyleSheet(estilo_activo if self.btn_diagrama.isChecked() else estilo_inactivo)
    
    # Métodos públicos para control externo
    def actualizar_posicion_robot(self, x, y, orientacion):
        """Actualiza la posición y orientación del robot"""
        self.robot_x = x
        self.robot_y = y
        self.robot_orientacion = orientacion
        self.widget_diagrama.actualizar_robot(x, y, orientacion)
        self.widget_diagrama.update()
        
    def iniciar_camara_real(self):
        """Activa el modo de cámara real"""
        self.widget_camara.iniciar_camara_real()
        print("✅ Modo cámara real activado")
    
    def detener_camara(self):
        """Detiene la cámara"""
        self.widget_camara.detener_camara()
        
    def get_modo_actual(self):
        """Devuelve el modo actual"""
        return "camara" if self.btn_camara.isChecked() else "diagrama"


class CameraWidget(QWidget):
    """Widget para visualización de cámara con soporte ROS2"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.camera_activa = False
        self.camera_simulada = False
        self.frame_count = 0
        self.ros_camera_node = None
        self.ultimo_frame = None
        self.frames_recibidos = 0
        
        # Timer para simulación de cámara
        self.timer_simulacion = QTimer(self)
        self.timer_simulacion.timeout.connect(self.generar_frame_simulado)
        
        # Timer para actualizar frames de ROS
        self.timer_ros = QTimer(self)
        self.timer_ros.timeout.connect(self.actualizar_frame_ros)
        self.timer_ros.start(33)  # ~30 FPS
        
        self.setMinimumSize(640, 480)
        
        # Estilo del widget
        self.setStyleSheet("background-color: #1a1a1a;")
    
    def conectar_nodo_ros(self, nodo):
        """Conecta el nodo ROS de cámara"""
        self.ros_camera_node = nodo
        print(f"✅ CameraWidget: Nodo ROS conectado - {nodo.get_name()}")
        
    def iniciar_camara_simulada(self):
        """Inicia una cámara simulada para pruebas"""
        self.camera_activa = True
        self.camera_simulada = True
        self.timer_simulacion.start(100)  # 10 FPS para simulación
        print("📹 Cámara simulada iniciada")
        self.update()
        
    def iniciar_camara_real(self):
        """Activa el modo de cámara real desde ROS"""
        if not CAMERA_LIBS_OK:
            print("⚠️ OpenCV/Numpy no disponibles, se mantiene cámara simulada")
            self.iniciar_camara_simulada()
            return

        self.camera_activa = True
        self.camera_simulada = False
        if self.timer_simulacion.isActive():
            self.timer_simulacion.stop()
        print("📹 Modo cámara real activado - esperando frames ROS...")
        self.update()
    
    def actualizar_frame_ros(self):
        """Actualiza el frame desde el nodo ROS"""
        if not self.camera_activa or self.camera_simulada:
            return
            
        if self.ros_camera_node is None:
            return

        if not CAMERA_LIBS_OK:
            return

        # Verificar si hay un nuevo frame disponible
        if hasattr(self.ros_camera_node, 'last_frame') and self.ros_camera_node.last_frame is not None:
            try:
                # Obtener el frame del nodo ROS (ya viene en RGB)
                frame = self.ros_camera_node.last_frame
                
                if frame is not None and len(frame.shape) == 3:
                    self.ultimo_frame = frame.copy()
                    self.frames_recibidos += 1
                    
                    # Log cada 30 frames
                    if self.frames_recibidos % 30 == 0:
                        print(f"📹 CameraWidget: {self.frames_recibidos} frames recibidos")
                    
                    self.update()
                    
            except Exception as e:
                print(f"❌ CameraWidget: Error al procesar frame ROS: {e}")
        
    def detener_camara(self):
        """Detiene la cámara"""
        self.camera_activa = False
        if self.timer_simulacion.isActive():
            self.timer_simulacion.stop()
        self.update()
        
    def generar_frame_simulado(self):
        """Genera un frame simulado para la cámara"""
        self.frame_count += 1
        self.update()
        
    def paintEvent(self, event):
        """Dibuja la vista de la cámara"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fondo negro
        painter.fillRect(self.rect(), QColor(20, 20, 30))
        
        if not self.camera_activa:
            # Mostrar mensaje de cámara no disponible
            painter.setPen(QColor(255, 100, 100))
            painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 
                           "❌ CÁMARA NO DISPONIBLE")
            return
        
        if self.camera_simulada:
            # Dibujar simulación de cámara
            self.dibujar_camara_simulada(painter)
        elif self.ultimo_frame is not None:
            # Dibujar frame real de ROS
            self.dibujar_frame_real(painter)
        else:
            # Esperando frames de ROS
            painter.setPen(QColor(255, 255, 0))
            painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            
            mensaje = "📡 ESPERANDO DATOS DE CÁMARA...\n\n"
            if self.ros_camera_node:
                mensaje += f"Nodo conectado: {self.ros_camera_node.get_name()}\n"
                if hasattr(self.ros_camera_node, 'frame_count'):
                    mensaje += f"Frames del nodo: {self.ros_camera_node.frame_count}"
            else:
                mensaje += "⚠️ Nodo no conectado"
            
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, mensaje)
    
    def dibujar_frame_real(self, painter):
        """Dibuja el frame real de la cámara ROS"""
        if self.ultimo_frame is None:
            return
        
        try:
            frame = self.ultimo_frame
            h, w = frame.shape[:2]
            
            # Crear QImage desde el array numpy (ya está en RGB)
            bytes_per_line = 3 * w
            qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
            
            # Convertir a pixmap
            pixmap = QPixmap.fromImage(qimg)
            
            # Escalar manteniendo aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Centrar la imagen
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
            
            # Información overlay
            painter.setPen(QColor(0, 255, 0))
            painter.setFont(QFont("Monospace", 10, QFont.Weight.Bold))
            info_text = f"📹 LIVE | Frames: {self.frames_recibidos} | {w}x{h}"
            
            # Fondo semi-transparente para el texto
            text_rect = painter.fontMetrics().boundingRect(info_text)
            text_rect.adjust(-5, -2, 5, 2)
            text_rect.moveTopLeft(painter.viewport().topLeft() + painter.viewport().topLeft())
            text_rect.translate(10, 10)
            
            painter.fillRect(text_rect, QColor(0, 0, 0, 180))
            painter.drawText(10, 25, info_text)
            
        except Exception as e:
            painter.setPen(QColor(255, 0, 0))
            painter.setFont(QFont("Arial", 12))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 
                           f"❌ Error al renderizar: {str(e)}")
            print(f"❌ Error en dibujar_frame_real: {e}")
            import traceback
            traceback.print_exc()
            
    def dibujar_camara_simulada(self, painter):
        """Dibuja una simulación de video de cámara"""
        ancho = self.width()
        alto = self.height()
        
        # Patrón de fondo móvil para simular video
        for i in range(0, ancho, 20):
            for j in range(0, alto, 20):
                offset = (self.frame_count // 2) % 40
                color_val = 40 + ((i + j + offset) % 80)
                painter.setPen(QColor(color_val, color_val, color_val))
                painter.drawPoint(i, j)
        
        # Cuadrícula
        painter.setPen(QPen(QColor(80, 80, 100), 1))
        for i in range(0, ancho, 50):
            painter.drawLine(i, 0, i, alto)
        for j in range(0, alto, 50):
            painter.drawLine(0, j, ancho, j)
            
        # Círculo móvil simulado
        centro_x = ancho // 2 + int(math.cos(self.frame_count * 0.1) * 100)
        centro_y = alto // 2 + int(math.sin(self.frame_count * 0.08) * 80)
        radio = 30 + int(math.sin(self.frame_count * 0.05) * 10)
        
        painter.setPen(QPen(QColor(0, 255, 0), 2))
        painter.setBrush(QColor(0, 100, 0, 100))
        painter.drawEllipse(centro_x - radio, centro_y - radio, radio * 2, radio * 2)
        
        # Texto informativo
        painter.setPen(QColor(255, 255, 0))
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.drawText(10, 25, "📹 CÁMARA SIMULADA")
        painter.drawText(10, 45, f"Frame: {self.frame_count}")
        painter.drawText(10, 65, "Esperando conexión ROS...")


class RobotDiagramWidget(QWidget):
    """Widget para visualizar el diagrama y posición del robot"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_orientacion = 0.0  # En radianes
        self.setMinimumSize(400, 400)
        
    def actualizar_robot(self, x, y, orientacion):
        """Actualiza la posición y orientación del robot"""
        self.robot_x = x
        self.robot_y = y
        self.robot_orientacion = orientacion
        
    def paintEvent(self, event):
        """Dibuja el diagrama del robot"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fondo
        self.dibujar_fondo(painter)
        
        # Sistema de coordenadas
        self.dibujar_sistema_coordenadas(painter)
        
        # Robot
        self.dibujar_robot(painter)
        
        # Información
        self.dibujar_informacion(painter)
        
    def dibujar_fondo(self, painter):
        """Dibuja el fondo del diagrama"""
        painter.fillRect(self.rect(), QColor(240, 240, 240))
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self.rect().adjusted(1, 1, -1, -1))
        
    def dibujar_sistema_coordenadas(self, painter):
        """Dibuja el sistema de coordenadas"""
        ancho = self.width()
        alto = self.height()
        centro_x = ancho // 2
        centro_y = alto // 2
        escala = min(ancho, alto) * 0.3
        
        # Cuadrícula
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        for i in range(-5, 6):
            x = centro_x + i * escala / 2
            painter.drawLine(int(x), 0, int(x), alto)
            y = centro_y + i * escala / 2
            painter.drawLine(0, int(y), ancho, int(y))
        
        # Ejes
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawLine(0, centro_y, ancho, centro_y)
        painter.drawLine(centro_x, 0, centro_x, alto)
        
        # Etiquetas
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.drawText(ancho - 30, centro_y - 10, "X")
        painter.setPen(QPen(QColor(0, 0, 255), 2))
        painter.drawText(centro_x + 10, 30, "Y")
        
    def dibujar_robot(self, painter):
        """Dibuja el robot"""
        ancho = self.width()
        alto = self.height()
        centro_x = ancho // 2
        centro_y = alto // 2
        escala = min(ancho, alto) * 0.3
        
        x_pantalla = centro_x + self.robot_x * escala
        y_pantalla = centro_y - self.robot_y * escala
        
        tamaño_robot = 20
        
        # Cuerpo
        painter.setPen(QPen(QColor(0, 100, 0), 2))
        painter.setBrush(QColor(0, 200, 0, 150))
        painter.drawEllipse(int(x_pantalla - tamaño_robot), 
                          int(y_pantalla - tamaño_robot), 
                          tamaño_robot * 2, tamaño_robot * 2)
        
        # Dirección
        orientacion_x = x_pantalla + math.cos(self.robot_orientacion) * tamaño_robot * 1.5
        orientacion_y = y_pantalla - math.sin(self.robot_orientacion) * tamaño_robot * 1.5
        
        painter.setPen(QPen(QColor(255, 0, 0), 3))
        painter.drawLine(int(x_pantalla), int(y_pantalla), 
                        int(orientacion_x), int(orientacion_y))
        
    def dibujar_informacion(self, painter):
        """Dibuja la información del robot"""
        info = [
            f"X: {self.robot_x:.2f}",
            f"Y: {self.robot_y:.2f}", 
            f"θ: {math.degrees(self.robot_orientacion):.1f}°"
        ]
        
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        for i, texto in enumerate(info):
            painter.drawText(10, 30 + i * 20, texto)