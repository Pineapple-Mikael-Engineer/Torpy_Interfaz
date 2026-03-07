#!/usr/bin/env python3
"""
Script de diagnóstico para verificar recepción de imágenes de la cámara
"""

import sys
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from sensor_msgs.msg import CompressedImage
import cv2
import numpy as np

class CameraDiagnosticNode(Node):
    def __init__(self):
        super().__init__('camera_diagnostic')
        
        self.frame_count = 0
        self.first_frame_received = False
        
        # ========== PRUEBA 1: QoS RELIABLE ==========
        print("\n" + "="*60)
        print("📹 TEST 1: Intentando con QoS RELIABLE")
        print("="*60)
        
        qos_reliable = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        self.sub_reliable = self.create_subscription(
            CompressedImage,
            '/image_raw/compressed',
            self.callback_reliable,
            qos_reliable
        )
        
        # ========== PRUEBA 2: QoS BEST_EFFORT ==========
        print("\n📹 TEST 2: Intentando con QoS BEST_EFFORT")
        
        qos_best_effort = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        self.sub_best_effort = self.create_subscription(
            CompressedImage,
            '/image_raw/compressed',
            self.callback_best_effort,
            qos_best_effort
        )
        
        # Timer para verificar estado
        self.timer = self.create_timer(3.0, self.check_status)
        self.start_time = self.get_clock().now()
        
        print("\n✅ Nodo iniciado - Esperando frames...\n")
    
    def callback_reliable(self, msg):
        """Callback para suscripción RELIABLE"""
        if not self.first_frame_received:
            print("\n" + "="*60)
            print("✅ ÉXITO: Frames recibidos con QoS RELIABLE")
            print("="*60)
            self.first_frame_received = True
            self.process_frame(msg, "RELIABLE")
        
        self.frame_count += 1
        if self.frame_count % 10 == 0:
            print(f"📊 RELIABLE: {self.frame_count} frames recibidos")
    
    def callback_best_effort(self, msg):
        """Callback para suscripción BEST_EFFORT"""
        if not self.first_frame_received:
            print("\n" + "="*60)
            print("✅ ÉXITO: Frames recibidos con QoS BEST_EFFORT")
            print("="*60)
            self.first_frame_received = True
            self.process_frame(msg, "BEST_EFFORT")
        
        self.frame_count += 1
        if self.frame_count % 10 == 0:
            print(f"📊 BEST_EFFORT: {self.frame_count} frames recibidos")
    
    def process_frame(self, msg, qos_type):
        """Procesa y valida un frame"""
        try:
            print(f"\n📦 Información del mensaje ({qos_type}):")
            print(f"   • Tamaño datos: {len(msg.data)} bytes")
            print(f"   • Formato: {msg.format}")
            
            # Decodificar
            np_arr = np.frombuffer(msg.data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if frame is not None:
                h, w, c = frame.shape
                print(f"   • Resolución: {w}x{h}")
                print(f"   • Canales: {c}")
                print(f"   • Tipo: {frame.dtype}")
                print("\n✅ Frame decodificado correctamente")
                
                # Intentar mostrar con OpenCV (opcional)
                try:
                    cv2.imshow(f'Camera Test - {qos_type}', frame)
                    cv2.waitKey(1)
                    print("   • Ventana OpenCV creada (presiona 'q' para cerrar)")
                except:
                    print("   • No se pudo crear ventana (sin display)")
            else:
                print("❌ Error: cv2.imdecode retornó None")
                
        except Exception as e:
            print(f"❌ Error procesando frame: {e}")
            import traceback
            traceback.print_exc()
    
    def check_status(self):
        """Verifica el estado de conexión cada 3 segundos"""
        elapsed = (self.get_clock().now() - self.start_time).nanoseconds / 1e9
        
        if not self.first_frame_received:
            print(f"\n⏳ Esperando frames... ({elapsed:.1f}s)")
            
            # Verificar publishers
            num_pubs = self.count_publishers('/image_raw/compressed')
            print(f"   • Publishers detectados: {num_pubs}")
            
            if num_pubs == 0:
                print("\n⚠️  PROBLEMA DETECTADO:")
                print("   No hay publicadores en /image_raw/compressed")
                print("\n🔧 Soluciones:")
                print("   1. Verifica que la Raspberry esté conectada")
                print("   2. Ejecuta en otra terminal:")
                print("      ros2 topic list | grep image")
                print("      ros2 topic hz /image_raw/compressed")
                print("      ros2 node list")
            
            if elapsed > 15:
                print("\n❌ TIMEOUT: No se recibieron frames en 15 segundos")
                print("\n🔧 Diagnóstico recomendado:")
                print("   1. ros2 topic info /image_raw/compressed -v")
                print("   2. ros2 node info /v4l2_camera")
                print("   3. Verifica configuración DDS (ROS_DOMAIN_ID)")

def main():
    print("\n" + "="*60)
    print("🔍 DIAGNÓSTICO DE CÁMARA TURTLEBOT")
    print("="*60)
    
    # Verificar ROS2
    if not rclpy.ok():
        rclpy.init()
    
    print("\n📌 Información del sistema:")
    print(f"   • ROS2 inicializado: {rclpy.ok()}")
    
    import os
    domain_id = os.environ.get('ROS_DOMAIN_ID', '0')
    print(f"   • ROS_DOMAIN_ID: {domain_id}")
    
    print("\n🎯 Este script intentará:")
    print("   1. Conectarse con QoS RELIABLE")
    print("   2. Conectarse con QoS BEST_EFFORT")
    print("   3. Detectar qué configuración funciona")
    print("   4. Mostrar información detallada del primer frame")
    
    try:
        node = CameraDiagnosticNode()
        
        print("\n🔄 Ejecutando... (Ctrl+C para salir)")
        rclpy.spin(node)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Detenido por usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if rclpy.ok():
            rclpy.shutdown()
        cv2.destroyAllWindows()
        
        print("\n" + "="*60)
        print("📊 RESUMEN")
        print("="*60)
        if hasattr(node, 'frame_count'):
            print(f"   • Total frames recibidos: {node.frame_count}")
            if node.frame_count > 0:
                print("   • ✅ Conexión exitosa")
            else:
                print("   • ❌ No se recibieron frames")
        print("="*60 + "\n")

if __name__ == '__main__':
    main()