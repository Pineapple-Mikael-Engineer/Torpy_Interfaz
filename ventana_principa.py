import sys
import os
import traceback
import signal

# Manejador de señales
def signal_handler(sig, frame):
    print('\n🛑 Cerrando aplicación...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# ========== IMPORTACIONES ==========
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, 
    QHBoxLayout, QVBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy, QoSDurabilityPolicy

# Importar interfaces
import interfaces
from interfaces import Widget_lidar, Widgets_cameraCV
import interfaces.Modulo_velocidad

# Importar splash screen
from pantalla_de_carga.splash_screen import SplashScreen

import cv2
import numpy as np


# ========== NODO DE CÁMARA ==========
class CameraSubscriberNode(Node):
    """Nodo ROS2 para suscribirse a imágenes comprimidas"""
    
    def __init__(self):
        super().__init__('camera_gui_node')
        from sensor_msgs.msg import CompressedImage
        
        self.last_frame = None
        self.frame_count = 0
        
        # QoS optimizado para video streaming
        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1
        )
        
        # Suscripción al topic de cámara
        self.subscription = self.create_subscription(
            CompressedImage,
            '/image_raw/compressed',
            self.callback,
            qos_profile
        )
        
        self.get_logger().info("📹 CameraSubscriberNode iniciado - Escuchando /image_raw/compressed")
    
    def callback(self, msg):
        """Callback para imágenes comprimidas"""
        try:
            # Decodificar imagen comprimida (JPEG)
            np_arr = np.frombuffer(msg.data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if frame is None:
                self.get_logger().error("❌ Error al decodificar imagen")
                return
            
            # Convertir BGR (OpenCV) a RGB (Qt)
            self.last_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.frame_count += 1
            
            # Log cada 30 frames (~4 segundos a 7.5 FPS)
            if self.frame_count % 30 == 0:
                self.get_logger().info(f"📹 Frames recibidos: {self.frame_count}")
                
        except Exception as e:
            self.get_logger().error(f"❌ Error en callback: {e}")


# ========== HILO ROS UNIFICADO ==========
class UnifiedRosSpinThread(QThread):
    """Hilo para procesar todos los nodos ROS2 sin bloquear GUI"""
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.executor = None
        
        if rclpy.ok():
            try:
                self.executor = MultiThreadedExecutor()
                print("✅ Executor ROS2 creado")
            except Exception as e:
                print(f"❌ Error creando executor: {e}")
    
    def add_node(self, node):
        """Agregar un nodo al executor"""
        if not self.executor:
            print(f"⚠️  No hay executor disponible")
            return False
        
        if not isinstance(node, Node):
            print(f"⚠️  {node} no es un nodo ROS2 válido")
            return False
        
        try:
            self.executor.add_node(node)
            print(f"✅ Nodo agregado: {node.get_name()}")
            return True
        except Exception as e:
            print(f"❌ Error agregando nodo {node.get_name()}: {e}")
            return False
    
    def run(self):
        """Loop principal del hilo"""
        if not self.executor:
            print("⚠️  Sin executor - hilo ROS inactivo")
            return
        
        print("🔄 Hilo ROS iniciado")
        while self.running:
            try:
                self.executor.spin_once(timeout_sec=0.01)
            except Exception as e:
                print(f"❌ Error en spin: {e}")
                break
        print("🛑 Hilo ROS detenido")
    
    def stop(self):
        """Detener el hilo"""
        self.running = False
        if self.executor:
            try:
                self.executor.shutdown()
            except:
                pass


# ========== HILO DE INICIALIZACIÓN ==========
class InitThread(QThread):
    """Inicializa componentes pesados en segundo plano"""
    
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)
    
    def __init__(self, window):
        super().__init__()
        self.window = window
    
    def run(self):
        try:
            print("🔄 Inicializando componentes...")
            
            # Dar tiempo para que el hilo ROS esté listo
            import time
            time.sleep(0.1)
            
            # ✅ CREAR NODO DE CÁMARA
            print("  📹 Creando nodo de cámara...")
            self.window.camera_node = CameraSubscriberNode()
            
            # ✅ CONECTAR NODO AL WIDGET
            print("  🔗 Conectando nodo al widget de cámara...")
            self.window.Widget_camera.conectar_nodo_ros(self.window.camera_node)
            
            # ✅ AGREGAR NODO AL EXECUTOR
            print("  ➕ Agregando nodo de cámara al executor...")
            self.window.ros_spin_thread.add_node(self.window.camera_node)
            
            # ✅ ACTIVAR MODO CÁMARA REAL
            print("  ▶️  Activando modo cámara real...")
            self.window.Widget_camera.iniciar_camara_real()
            
            self.finished_signal.emit()
            
        except Exception as e:
            error_msg = f"Error en inicialización: {e}\n{traceback.format_exc()}"
            self.error_signal.emit(error_msg)


# ========== VENTANA PRINCIPAL ==========
class ventana_Turtlebot(QMainWindow):
    """Ventana principal del TurtleBot"""
    
    def __init__(self):
        super().__init__()
        
        print("\n" + "="*60)
        print("🚀 Iniciando TurtleBot Control Center")
        print("="*60 + "\n")
        
        self.setWindowTitle("🤖 TurtleBot Control Center")
        self.resize(1200, 800)
        
        # Variables
        self.ros_spin_thread = None
        self.init_thread = None
        self.camera_node = None  # ✅ AGREGAR VARIABLE PARA NODO DE CÁMARA
        
        try:
            # PASO 1: Crear hilo ROS (NO iniciarlo aún)
            print("📌 Paso 1: Creando hilo ROS...")
            self.ros_spin_thread = UnifiedRosSpinThread()
            
            # PASO 2: Crear widgets (esto crea los nodos)
            print("📌 Paso 2: Creando widgets...")
            self._crear_widgets()
            
            # PASO 3: Agregar nodos al executor (excepto cámara, se hace después)
            print("📌 Paso 3: Agregando nodos al executor...")
            self._agregar_nodos_a_executor()
            
            # PASO 4: AHORA SÍ iniciar el hilo ROS
            print("📌 Paso 4: Iniciando hilo ROS...")
            self.ros_spin_thread.start()
            
            # PASO 5: Construir interfaz
            print("📌 Paso 5: Construyendo interfaz...")
            self.init_ui()
            
            # PASO 6: Inicializar componentes pesados en segundo plano (CÁMARA)
            print("📌 Paso 6: Inicializando cámara en segundo plano...")
            self.start_initialization()
            
            print("\n✅ Ventana principal lista\n")
            
        except Exception as e:
            print(f"\n❌ ERROR CRÍTICO: {e}")
            traceback.print_exc()
            raise
    
    def _crear_widgets(self):
        """Crea todos los widgets"""
        
        # Widget de velocidad/control
        try:
            self.Wigdet_Velocidad = interfaces.Modulo_velocidad.Widget_Modulo_velocidad()
            print("  ✅ Widget velocidad creado")
        except Exception as e:
            print(f"  ❌ Error creando widget velocidad: {e}")
            traceback.print_exc()
            raise
        
        # Widget de cámara (sin nodo aún)
        try:
            self.Widget_camera = Widgets_cameraCV.CameraDiagramWidget()
            print("  ✅ Widget cámara creado")
        except Exception as e:
            print(f"  ❌ Error creando widget cámara: {e}")
            traceback.print_exc()
            raise
        
        # Widget de LiDAR (es un nodo ROS2)
        try:
            self.Widget_derecho_total = Widget_lidar.LidarWidget(
                topic_name="/Torpy/scan",
                scale=100,
                debug=False  # Cambiar a True para más logs
            )
            print(f"  ✅ Widget LiDAR creado")
            print(f"     - Nombre nodo: {self.Widget_derecho_total.get_name()}")
        except Exception as e:
            print(f"  ❌ Error creando widget LiDAR: {e}")
            traceback.print_exc()
            raise
    
    def _agregar_nodos_a_executor(self):
        """Agrega todos los nodos ROS2 al executor (excepto cámara)"""
        
        # Agregar nodo del widget de velocidad (si existe)
        if hasattr(self.Wigdet_Velocidad, 'ros_node'):
            if isinstance(self.Wigdet_Velocidad.ros_node, Node):
                self.ros_spin_thread.add_node(self.Wigdet_Velocidad.ros_node)
        
        # Agregar nodo del LiDAR
        if isinstance(self.Widget_derecho_total, Node):
            self.ros_spin_thread.add_node(self.Widget_derecho_total)
        
        # La cámara se agrega en InitThread después
    
    def init_ui(self):
        """Construye la interfaz de usuario"""
        
        # Widget central
        Widget_central = QWidget()
        layout_total = QHBoxLayout()
        
        # Panel izquierdo (velocidad + cámara)
        Widget_Izquierdo_total = QWidget()
        layout_izquierdo_total = QVBoxLayout()
        layout_izquierdo_total.addWidget(self.Wigdet_Velocidad, stretch=20)
        layout_izquierdo_total.addWidget(self.Widget_camera, stretch=30)
        Widget_Izquierdo_total.setLayout(layout_izquierdo_total)
        
        # Layout principal
        layout_total.addWidget(Widget_Izquierdo_total, stretch=40)
        layout_total.addWidget(self.Widget_derecho_total, stretch=50)
        
        Widget_central.setLayout(layout_total)
        self.setCentralWidget(Widget_central)
        
        print("  ✅ UI construida")
    
    def start_initialization(self):
        """Inicia la inicialización en segundo plano"""
        self.init_thread = InitThread(self)
        self.init_thread.finished_signal.connect(self.on_init_finished)
        self.init_thread.error_signal.connect(self.on_init_error)
        self.init_thread.start()
    
    def on_init_finished(self):
        print("\n✅ Inicialización completada")
        print("📡 Sistema listo - Esperando datos de cámara...\n")
    
    def on_init_error(self, error_msg):
        print(f"\n❌ Error en inicialización:\n{error_msg}\n")
    
    def closeEvent(self, event):
        """Limpieza al cerrar la aplicación"""
        print("\n" + "="*60)
        print("🛑 Cerrando aplicación")
        print("="*60 + "\n")
        
        # Detener hilo ROS
        if self.ros_spin_thread:
            print("  - Deteniendo hilo ROS...")
            self.ros_spin_thread.stop()
            self.ros_spin_thread.wait(2000)
        
        # Destruir nodos
        try:
            if hasattr(self, 'camera_node') and self.camera_node:
                self.camera_node.destroy_node()
                print("  - Nodo cámara destruido")
        except Exception as e:
            print(f"    Error destruyendo cámara: {e}")
        
        try:
            if hasattr(self, 'Widget_derecho_total'):
                if isinstance(self.Widget_derecho_total, Node):
                    self.Widget_derecho_total.destroy_node()
                    print("  - Nodo LiDAR destruido")
        except Exception as e:
            print(f"    Error destruyendo LiDAR: {e}")
        
        try:
            if hasattr(self, 'Wigdet_Velocidad'):
                if hasattr(self.Wigdet_Velocidad, 'ros_node'):
                    self.Wigdet_Velocidad.ros_node.destroy_node()
                    print("  - Nodo velocidad destruido")
        except Exception as e:
            print(f"    Error destruyendo velocidad: {e}")
        
        # Shutdown ROS2
        if rclpy.ok():
            try:
                rclpy.shutdown()
                print("  - ROS2 shutdown")
            except Exception as e:
                print(f"    Error en shutdown: {e}")
        
        print("\n✅ Limpieza completa\n")
        event.accept()


# ========== MAIN ==========
if __name__ == "__main__":
    
    print("\n" + "="*60)
    print("🎬 Iniciando aplicación TurtleBot")
    print("="*60 + "\n")
    
    # Inicializar ROS2 PRIMERO
    if not rclpy.ok():
        try:
            rclpy.init()
            print("✅ ROS2 inicializado\n")
        except Exception as e:
            print(f"❌ Error inicializando ROS2: {e}\n")
            sys.exit(1)
    else:
        print("✅ ROS2 ya estaba inicializado\n")
    
    # Crear aplicación Qt
    app = QApplication(sys.argv)
    
    # Crear ventana principal
    try:
        mi_ventana = ventana_Turtlebot()
    except Exception as e:
        print(f"\n❌ Error creando ventana: {e}")
        traceback.print_exc()
        rclpy.shutdown()
        sys.exit(1)
    
    # Mostrar con splash screen
    try:
        splash = SplashScreen(mi_ventana)
        splash.show()
        print("✅ Splash screen mostrado\n")
    except Exception as e:
        print(f"⚠️  Error con splash screen: {e}")
        print("   Mostrando ventana directamente...\n")
        mi_ventana.show()
    
    # Ejecutar aplicación
    exit_code = app.exec()
    
    # Limpieza final
    print("\n📌 Aplicación cerrada con código:", exit_code)
    
    if rclpy.ok():
        rclpy.shutdown()
        print("✅ ROS2 finalizado\n")
    
    sys.exit(exit_code)
