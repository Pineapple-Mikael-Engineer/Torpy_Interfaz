import os

from PyQt6.QtWidgets import QFrame, QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize, QTimer
from PyQt6.QtGui import QColor

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

from interfaces.herramientas.clases import DifferentialDriver
from .QJoyStick import QJoystickControl
from . import Widget_velocidad_botones
from .GamePadClase import GamepadFullReader 


def Redimencionar_QIcon(Widget_guia, Boton, escala):
    size = int(min(Widget_guia.width(), Widget_guia.height()) * escala)
    Boton.setIconSize(QSize(size, size))


class Widget_Modulo_velocidad(QWidget, Widget_velocidad_botones.Ui_Widget_principal):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # ========== INICIALIZAR ROS2 ==========
        if not rclpy.ok():
            rclpy.init()
        
        self.ros_node = rclpy.create_node(
            'interface_controller',
            namespace='Mikael'
        )

        self.publisher = self.ros_node.create_publisher(Twist, 'cmd_vel_raw', 10)
        
        # Timer para procesar ROS2 sin bloquear el GUI
        self.ros_timer = QTimer()
        self.ros_timer.timeout.connect(lambda: rclpy.spin_once(self.ros_node, timeout_sec=0))
        self.ros_timer.start(10)  # cada 10ms
        
        # Variable para guardar velocidad actual del slider
        self.current_speed = 0.5  # Velocidad por defecto (50%)

        self.setObjectName("Modulo Velocidad")
        
        # Clase de driver velocidad (para usar con joystick en el futuro)
        self.velocidad_calculator = DifferentialDriver(speed_factor=1)
        
        # base path del módulo
        base = os.path.dirname(__file__)

        # ===Agregar QJoyStick===
        self.widget_joystick = QJoystickControl(
            parent=None,
            radio=110,
            color_joystick=QColor(96, 125, 139),
            color_borde=QColor(0, 121, 107),
            tamaño_joystick=16,
            icono_path=None,
            usar_gamepad=True
        )
        
        # ==== Conectar JoyStick a Label====
        self.widget_joystick.movimiento.connect(self.actualizar_label_desde_joystick)
        self.widget_joystick.movimiento.connect(self.cuadrante)
        self.widget_joystick.movimiento.connect(self.on_move_general)
        
        # =====Creacion de Frame para QJoyStick=====
        self.LabelPosicion_JoyStick = QLabel("Posición: ...")
        text_label_style = """
        QLabel {
            color: #b3e5fc;
            background-color: #1c313a;
            border: 1.5px solid #0288d1;
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 14px;
            font-family: 'Segoe UI', 'Ubuntu', sans-serif;
            line-height: 1.4;
        }
        """
        self.LabelPosicion_JoyStick.setStyleSheet(text_label_style)
        
        self.frame_JoyStick = QFrame()
        self.layout_JoyStick = QHBoxLayout(self.frame_JoyStick)
        self.layout_JoyStick.setContentsMargins(0, 0, 0, 0)
        self.layout_JoyStick.setSpacing(10)
        self.layout_JoyStick.addWidget(self.widget_joystick, stretch=2)
        self.layout_JoyStick.addWidget(self.LabelPosicion_JoyStick, stretch=5)
        
        # ====Conectar JoyStick derecho con Slider===
        self.conectar_joystick_derecho()
        
        # ========Unir bloques JoyStick y Botones=====
        self.layout_contenedor_general.addWidget(self.frame_JoyStick, stretch=3)
        self.layout_contenedor_general.setStretchFactor(self.layout_contenedor_general_botones, 2)
        
        # ======Estilo QSlider=====
        slider_style = """
            QSlider::groove:horizontal {
                background: #102027;
                border: 1px solid #4dd0e1;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #4dd0e1, stop:1 #80deea);
                border: 2px solid #00acc1;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #80deea, stop:1 #b2ebf2);
                border: 2px solid #4dd0e1;
            }
            QSlider::handle:horizontal:pressed {
                background: #00bcd4;
                border: 2px solid #26c6da;
            }
            QSlider::add-page:horizontal {
                background: #1c313a;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #4dd0e1;
                border-radius: 3px;
            }
        """
        self.slider_velocidad.setStyleSheet(slider_style)
        self.slider_velocidad.setRange(0, 100)
        self.slider_velocidad.setSingleStep(10)
        self.slider_velocidad.setValue(50)  # Valor inicial 50%
        self.slider_velocidad.valueChanged.connect(self.cambiar_velocidad)
        
        # ===Agregar Iconos===
        Icono_avanzar = QIcon(os.path.join(base, "multimedia", "icons8-move-up-liquid-glass", "icons8-move-up-96.png"))
        Icono_retroceder = QIcon(os.path.join(base, "multimedia", "icons8-move-down-liquid-glass", "icons8-move-down-96.png"))
        Icono_rotar_anti = QIcon(os.path.join(base, "multimedia", "icons8-rotate-antih-liquid-glass", "icons8-rotate-96.png"))
        Icono_rotar_hora = QIcon(os.path.join(base, "multimedia", "icons8-rotate-hora-liquid-glass", "icons8-rotate-96.png"))

        self.button_avanzar.setIcon(Icono_avanzar)
        self.button_retroceder.setIcon(Icono_retroceder)
        self.button_giro_antihorario.setIcon(Icono_rotar_anti)
        self.button_giro_horario.setIcon(Icono_rotar_hora)

        # ========== CONECTAR BOTONES A ROS2 ==========
        self.button_avanzar.pressed.connect(self.on_avanzar_pressed)
        self.button_avanzar.released.connect(self.on_stop)
        
        self.button_retroceder.pressed.connect(self.on_retroceder_pressed)
        self.button_retroceder.released.connect(self.on_stop)
        
        self.button_giro_horario.pressed.connect(self.on_giro_derecha_pressed)
        self.button_giro_horario.released.connect(self.on_stop)
        
        self.button_giro_antihorario.pressed.connect(self.on_giro_izquierda_pressed)
        self.button_giro_antihorario.released.connect(self.on_stop)

    # ========== FUNCIONES DE CONTROL DE BOTONES ==========
    def on_avanzar_pressed(self):
        """Avanzar hacia adelante"""
        print("🔵 BOTÓN AVANZAR PRESIONADO")
        self.publicar_twist(1.0, 0.0)
    
    def on_retroceder_pressed(self):
        """Retroceder"""
        print("🔵 BOTÓN RETROCEDER PRESIONADO")
        self.publicar_twist(-1.0, 0.0)
    
    def on_giro_derecha_pressed(self):
        """Girar a la derecha (en el lugar)"""
        print("🔵 BOTÓN GIRO DERECHA PRESIONADO")
        self.publicar_twist(0.0, -1.0)
    
    def on_giro_izquierda_pressed(self):
        """Girar a la izquierda (en el lugar)"""
        print("🔵 BOTÓN GIRO IZQUIERDA PRESIONADO")
        self.publicar_twist(0.0, 1.0)
    
    def on_stop(self):
        """Detener el robot"""
        print("🛑 DETENER")
        self.publicar_twist(0.0, 0.0)

    def on_move_general(self,x,y):
        """Moverlo por JoyStick"""
        print("Moviendo, por JoyStick")
        self.publicar_twist(-y,-x)
        
    # ====Re-Escalar Iconos===
    def resizeEvent(self, event):
        Redimencionar_QIcon(self, self.button_retroceder, 0.25)
        Redimencionar_QIcon(self, self.button_avanzar, 0.25)
        Redimencionar_QIcon(self, self.button_giro_horario, 0.45)
        Redimencionar_QIcon(self, self.button_giro_antihorario, 0.45)
       
    def actualizar_label_desde_joystick(self, x_norm, y_norm):
        """Actualiza el label con la posición del joystick"""
        x = round(x_norm, 2)
        y = -round(y_norm, 2)
        Posicion = f"X: {x:+.2f}  Y: {y:+.2f}"
        self.LabelPosicion_JoyStick.setText(Posicion)
 


    



    
    def cuadrante(self, x_norm, y_norm):
        """Indica visualmente qué botones corresponden al movimiento del joystick"""
        x = round(x_norm, 1)
        y = -round(y_norm, 1)
        
        # Actualizar botones de movimiento lineal
        if y > 0:
            self.button_avanzar.setDown(True)
            self.button_retroceder.setDown(False)
        elif y < 0:
            self.button_avanzar.setDown(False)
            self.button_retroceder.setDown(True) 
        else:
            self.button_avanzar.setDown(False)
            self.button_retroceder.setDown(False)
        
        # Actualizar botones de giro
        if x > 0:
            self.button_giro_horario.setDown(True)
            self.button_giro_antihorario.setDown(False)
        elif x < 0:
            self.button_giro_horario.setDown(False)
            self.button_giro_antihorario.setDown(True)
        else:
            self.button_giro_horario.setDown(False)
            self.button_giro_antihorario.setDown(False)
        
    def conectar_joystick_derecho(self):
        """Conecta el stick derecho del gamepad al slider de velocidad"""
        try:
            self.widget_joystick.gamepad_thread.right_stick_moved.connect(self.actualizar_valor_Slider)
            self.widget_joystick.gamepad_thread.start()
            print("✅ Gamepad conectado al slider")
        except Exception as e:
            print(f"⚠️ No se pudo conectar gamepad: {e}")
        
    def actualizar_valor_Slider(self, x, y):
        """Actualiza el slider desde el stick derecho del gamepad"""
        sensibilidad = 0.4
        velocidad_actual = self.slider_velocidad.value()
        if (y <= -sensibilidad):
            if velocidad_actual <= 90:
                velocidad_actual += 10
            else:
                velocidad_actual = 100
        elif (y >= sensibilidad):
            if velocidad_actual >= 10:
                velocidad_actual -= 10
            else:
                velocidad_actual=0
        self.slider_velocidad.setValue(velocidad_actual)

    def cambiar_velocidad(self, valor):
        """
        Actualiza la velocidad cuando el slider cambia
        valor: 0 a 100 (del slider)
        """
        # Convertir de 0-100 a 0.25-1.0 (25% a 100% de velocidad)
        self.current_speed = 0.25 + (valor / 100) * 0.75
        
        # Actualizar el label
        self.label_Widget_velocidad.setText(f"Velocidad: {valor}%")
        
        # Actualizar el factor en DifferentialDriver (para uso futuro)
        self.velocidad_calculator.set_speed_factor(self.current_speed)
        
        print(f"⚡ Velocidad: {valor}% (factor: {self.current_speed:.2f})")

    def publicar_twist(self, linear_x, angular_z):
        """
        Publica un mensaje Twist a ROS2
        
        Args:
            linear_x: velocidad lineal (-1.0 a 1.0), positivo = adelante
            angular_z: velocidad angular (-1.0 a 1.0), positivo = giro izquierda
        """
        msg = Twist()
        msg.linear.x = float(linear_x * self.current_speed)
        msg.angular.z = float(angular_z * self.current_speed)
        self.publisher.publish(msg)
        print(f"📡 Publicado → linear: {msg.linear.x:.2f}, angular: {msg.angular.z:.2f}")

    def closeEvent(self, event):
        """Se ejecuta cuando se cierra la ventana"""
        print("🔌 Cerrando módulo de velocidad...")
        self.ros_timer.stop()
        self.ros_node.destroy_node()
        # NO hacer rclpy.shutdown() - otros widgets pueden estar usándolo
        event.accept()
    
        
    


    

                
        
        
    
