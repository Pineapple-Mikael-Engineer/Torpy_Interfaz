import sys
import traceback
import signal

# Manejador de señales para debug
def signal_handler(sig, frame):
    print('\n🛑 Señal recibida, cerrando limpiamente...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# ========== IMPORTACIONES PYQT6 ==========
try:
    from PyQt6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, 
        QHBoxLayout, QLabel, QApplication
    )
    from PyQt6.QtCore import QThread, pyqtSignal, QTimer
except ImportError as e:
    print(f"❌ ERROR: PyQt6 no instalado: {e}")
    sys.exit(1)

# ========== IMPORTACIONES ROS2 ==========
try:
    import rclpy
    from rclpy.node import Node
    from rclpy.executors import MultiThreadedExecutor
    from rclpy.qos import (
        QoSProfile, QoSReliabilityPolicy, 
        QoSHistoryPolicy, QoSDurabilityPolicy
    )
    from sensor_msgs.msg import CompressedImage
    import numpy as np
    import cv2
    ROS_DISPONIBLE = True
    print("✅ ROS2 disponible")
except ImportError as e:
    print(f"⚠️  ROS2 no disponible: {e}")
    ROS_DISPONIBLE = False

# ========== IMPORTACIONES LOCALES ==========
try:
    from interfaces import Widget_lidar, Widgets_cameraCV, Modulo_velocidad
    INTERFACES_OK = True
    print("✅ Interfaces importadas correctamente")
except ImportError as e:
    print(f"⚠️  Error importando interfaces: {e}")
    traceback.print_exc()
    INTERFACES_OK = False


# ========== NODO DE CÁMARA ==========
if ROS_DISPONIBLE:
    class CameraSubscriberNode(Node):
        """Nodo ROS2 para recibir imágenes comprimidas"""
        
        def __init__(self):
            super().__init__('camera_gui_node')
            self.last_frame = None
            self.frame_count = 0
            
            qos_profile = QoSProfile(
                reliability=QoSReliabilityPolicy.BEST_EFFORT,
                durability=QoSDurabilityPolicy.VOLATILE,
                history=QoSHistoryPolicy.KEEP_LAST,
                depth=1
            )
            
            self.subscription = self.create_subscription(
                CompressedImage,
                '/image_raw/compressed',
                self.callback,
                qos_profile
            )
            
            self.get_logger().info("✅ CameraNode: /image_raw/compressed")
        
        def callback(self, msg):
            try:
                np_arr = np.frombuffer(msg.data, np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                
                if frame is not None:
                    self.last_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    self.frame_count += 1
                    
                    if self.frame_count % 30 == 0:
                        self.get_logger().info(f"📹 Frames: {self.frame_count}")
            except Exception as e:
                self.get_logger().error(f"Error: {e}")
else:
    class CameraSubscriberNode:
        def __init__(self):
            self.last_frame = None
            print("⚠️  CameraNode dummy (ROS2 no disponible)")
        def destroy_node(self):
            pass
        def get_name(self):
            return "camera_node_dummy"


# ========== HILO ROS UNIFICADO ==========
class UnifiedRosSpinThread(QThread):
    """Hilo para procesar ROS2 sin bloquear GUI"""
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.executor = None
        
        if ROS_DISPONIBLE and rclpy.ok():
            try:
                self.executor = MultiThreadedExecutor()
                print("✅ MultiThreadedExecutor creado")
            except Exception as e:
                print(f"⚠️  Error creando executor: {e}")
        else:
            print("⚠️  No se creará executor (ROS2 no disponible o no inicializado)")
    
    def add_node(self, node):
        """Agregar nodo al executor"""
        if not self.executor:
            print(f"⚠️  Sin executor - no se puede agregar nodo")
            return False
        
        if not hasattr(node, 'context'):
            print(f"⚠️  {node} no es un nodo ROS válido")
            return False
        
        try:
            self.executor.add_node(node)
            print(f"✅ Nodo agregado: {node.get_name()}")
            return True
        except Exception as e:
            print(f"⚠️  Error agregando nodo {node.get_name()}: {e}")
            return False
    
    def run(self):
        """Loop principal"""
        if not self.executor:
            print("⚠️  Sin executor - hilo ROS inactivo")
            return
        
        print("🔄 Hilo ROS iniciado")
        while self.running:
            try:
                self.executor.spin_once(timeout_sec=0.01)
            except Exception as e:
                print(f"⚠️  Error en spin: {e}")
                break
        print("🛑 Hilo ROS detenido")
    
    def stop(self):
        """Detener hilo"""
        self.running = False
        if self.executor:
            try:
                self.executor.shutdown()
            except:
                pass


# ========== HILO DE INICIALIZACIÓN ==========
class InitThread(QThread):
    """Inicializa componentes ROS en segundo plano"""
    
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)
    
    def __init__(self, window):
        super().__init__()
        self.window = window
    
    def run(self):
        try:
            if not ROS_DISPONIBLE:
                print("⚠️  ROS2 no disponible - sin inicialización")
                self.finished_signal.emit()
                return
            
            print("🔄 Inicializando componentes ROS...")
            
            # Crear nodo de cámara
            self.window.camera_node = CameraSubscriberNode()
            
            # Conectar a widget
            if hasattr(self.window, 'Widget_camera'):
                if hasattr(self.window.Widget_camera, 'conectar_nodo_ros'):
                    self.window.Widget_camera.conectar_nodo_ros(self.window.camera_node)
                    self.window.Widget_camera.iniciar_camara_real()
                    print("  ✅ Cámara conectada")
            
            # Agregar nodo de cámara
            if self.window.ros_spin_thread.add_node(self.window.camera_node):
                print("  ✅ Nodo cámara agregado al executor")
            
            # Agregar nodo de LiDAR (solo si es un nodo ROS válido)
            if hasattr(self.window, 'Widget_derecho_total'):
                if hasattr(self.window.Widget_derecho_total, 'context'):
                    if self.window.ros_spin_thread.add_node(self.window.Widget_derecho_total):
                        print("  ✅ Nodo LiDAR agregado al executor")
            
            self.finished_signal.emit()
            
        except Exception as e:
            error_msg = f"{e}\n{traceback.format_exc()}"
            self.error_signal.emit(error_msg)


# ========== VENTANA PRINCIPAL ==========
class ventana_Turtlebot(QMainWindow):
    """Ventana principal de control del TurtleBot"""
    
    def __init__(self):
        super().__init__()
        
        print("\n" + "="*50)
        print("🚀 Iniciando TurtleBot Control Center")
        print("="*50 + "\n")
        
        self.setWindowTitle("TurtleBot Control Center 🤖")
        self.resize(1200, 800)
        
        # Variables
        self.camera_node = None
        self.ros_spin_thread = None
        self.init_thread = None
        
        try:
            # PASO 1: Inicializar ROS2 PRIMERO
            self._inicializar_ros2()
            
            # PASO 2: Crear hilo spin (después de inicializar ROS)
            self._crear_hilo_ros()
            
            # PASO 3: Crear widgets
            self._crear_widgets()
            
            # PASO 4: Construir UI
            self._construir_ui()
            
            # PASO 5: Iniciar componentes ROS en segundo plano
            self._iniciar_componentes_ros()
            
            print("\n✅ Ventana principal lista\n")
            
        except Exception as e:
            print(f"\n❌ ERROR CRÍTICO en __init__: {e}")
            traceback.print_exc()
            raise
    
    def _inicializar_ros2(self):
        """Inicializa ROS2 ANTES de crear cualquier nodo"""
        if not ROS_DISPONIBLE:
            print("⚠️  ROS2 no disponible - modo sin ROS\n")
            return
        
        if not rclpy.ok():
            try:
                rclpy.init()
                print("✅ ROS2 inicializado\n")
            except Exception as e:
                print(f"❌ Error inicializando ROS2: {e}\n")
        else:
            print("✅ ROS2 ya estaba inicializado\n")
    
    def _crear_hilo_ros(self):
        """Crea el hilo para procesar ROS2"""
        self.ros_spin_thread = UnifiedRosSpinThread()
        # NO iniciar el hilo hasta que los nodos estén agregados
        print("✅ Hilo ROS creado (aún no iniciado)\n")
    
    def _crear_widgets(self):
        """Crea todos los widgets"""
        
        print("🔄 Creando widgets...")
        
        # Widget de velocidad
        if INTERFACES_OK and Modulo_velocidad:
            try:
                self.speed_widget = Modulo_velocidad.Widget_Modulo_velocidad()
                print("  ✅ Widget velocidad")
            except Exception as e:
                print(f"  ⚠️  Error widget velocidad: {e}")
                traceback.print_exc()
                self.speed_widget = self._crear_widget_placeholder("Velocidad")
        else:
            print("  ⚠️  Modulo_velocidad no disponible")
            self.speed_widget = self._crear_widget_placeholder("Velocidad")
        
        # Widget de cámara
        if INTERFACES_OK and Widgets_cameraCV:
            try:
                self.Widget_camera = Widgets_cameraCV.CameraDiagramWidget()
                print("  ✅ Widget cámara")
            except Exception as e:
                print(f"  ⚠️  Error widget cámara: {e}")
                traceback.print_exc()
                self.Widget_camera = self._crear_widget_placeholder("Cámara")
        else:
            print("  ⚠️  Widgets_cameraCV no disponible")
            self.Widget_camera = self._crear_widget_placeholder("Cámara")
        
        # Widget de LiDAR
        if INTERFACES_OK and Widget_lidar:
            try:
                self.Widget_derecho_total = Widget_lidar.LidarWidget(
                    topic_name="/scan",
                    scale=100,
                    debug=True
                )
                print("  ✅ Widget LiDAR")
            except Exception as e:
                print(f"  ⚠️  Error widget LiDAR: {e}")
                traceback.print_exc()
                self.Widget_derecho_total = self._crear_widget_placeholder("LiDAR")
        else:
            print("  ⚠️  Widget_lidar no disponible")
            self.Widget_derecho_total = self._crear_widget_placeholder("LiDAR")
        
        print()
    
    def _crear_widget_placeholder(self, nombre):
        """Crea un widget placeholder cuando falla la carga"""
        widget = QWidget()
        layout = QVBoxLayout()
        label = QLabel(f"⚠️ {nombre}\nNo disponible")
        label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                color: #888;
                background: #f0f0f0;
                padding: 20px;
                border-radius: 10px;
            }
        """)
        layout.addWidget(label)
        widget.setLayout(layout)
        return widget
    
    def _construir_ui(self):
        """Construye el layout"""
        print("🔄 Construyendo UI...")
        
        central_widget = QWidget()
        layout_total = QHBoxLayout()
        
        # Panel izquierdo
        left_widget = QWidget()
        layout_left = QVBoxLayout()
        layout_left.addWidget(self.speed_widget, stretch=20)
        layout_left.addWidget(self.Widget_camera, stretch=30)
        left_widget.setLayout(layout_left)
        
        # Layout principal
        layout_total.addWidget(left_widget, stretch=40)
        layout_total.addWidget(self.Widget_derecho_total, stretch=50)
        
        central_widget.setLayout(layout_total)
        self.setCentralWidget(central_widget)
        
        print("  ✅ UI construida\n")
    
    def _iniciar_componentes_ros(self):
        """Inicia componentes ROS en segundo plano"""
        if not ROS_DISPONIBLE:
            print("⚠️  Sin ROS2 - no hay componentes que iniciar\n")
            return
        
        print("🔄 Iniciando componentes ROS en segundo plano...\n")
        
        # Iniciar hilo ROS ANTES de crear nodos
        self.ros_spin_thread.start()
        
        # Dar tiempo para que el hilo inicie
        QTimer.singleShot(100, self._iniciar_nodos)
    
    def _iniciar_nodos(self):
        """Inicializa nodos en hilo separado"""
        self.init_thread = InitThread(self)
        self.init_thread.finished_signal.connect(self.on_init_finished)
        self.init_thread.error_signal.connect(self.on_init_error)
        self.init_thread.start()
    
    def on_init_finished(self):
        print("\n✅ Inicialización ROS completa")
        print("📹 Esperando frames de cámara...\n")
    
    def on_init_error(self, error_msg):
        print(f"\n❌ Error en inicialización:\n{error_msg}\n")
    
    def closeEvent(self, event):
        """Limpieza al cerrar"""
        print("\n" + "="*50)
        print("🛑 Cerrando aplicación")
        print("="*50 + "\n")
        
        # Detener hilo ROS
        if self.ros_spin_thread:
            print("  - Deteniendo hilo ROS...")
            self.ros_spin_thread.stop()
            self.ros_spin_thread.wait(1000)
        
        # Destruir nodos
        if self.camera_node:
            try:
                self.camera_node.destroy_node()
                print("  - Nodo cámara destruido")
            except Exception as e:
                print(f"    Error: {e}")
        
        if hasattr(self.Widget_derecho_total, "destroy_node"):
            try:
                self.Widget_derecho_total.destroy_node()
                print("  - Nodo LiDAR destruido")
            except Exception as e:
                print(f"    Error: {e}")
        
        # Shutdown ROS2
        if ROS_DISPONIBLE and rclpy.ok():
            try:
                rclpy.shutdown()
                print("  - ROS2 shutdown")
            except Exception as e:
                print(f"    Error: {e}")
        
        print("\n✅ Limpieza completa\n")
        event.accept()



