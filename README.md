# Torpy Interfaz

Interfaz de control para TurtleBot construida con **PyQt6**, con integración opcional a **ROS2** para visualizar cámara y LiDAR, y enviar comandos de velocidad.

## ¿Qué hace este proyecto?

La app levanta una ventana principal con tres bloques:

- **Control de movimiento** (botones + joystick + slider de velocidad).
- **Vista de cámara/diagrama** (conmutación entre feed de cámara y vista esquemática).
- **Visualización LiDAR** (nube de puntos, rejilla y controles de renderizado).

El sistema está diseñado para funcionar en dos modos:

1. **Con ROS2 disponible**: consume tópicos reales (`/image_raw/compressed`, `/scan`) y publica movimiento.
2. **Sin ROS2**: mantiene la interfaz funcional con placeholders o simulación, útil para desarrollo visual/local.

---

## Arquitectura (visión rápida)

### 1) Entry point

- `main.py` es el lanzador principal y delega en `torpy_app.run()`.
- `torpy_app/app.py` crea `QApplication`, registra manejo de señales y construye la ventana principal.

### 2) Carga dinámica de dependencias

- `torpy_app/config.py` intenta importar ROS2, OpenCV/Numpy y módulos de widgets.
- Expone flags globales:
  - `ROS_DISPONIBLE`
  - `INTERFACES_OK`
- Si algo falla, no se cae todo el programa: se habilita modo degradado.

### 3) Ventana principal

- `torpy_app/ui/main_window.py` compone widgets y administra ciclo de vida.
- Inicializa ROS, crea hilo de `spin`, arranca inicialización en segundo plano y conecta nodos con la UI.
- Si un módulo no está disponible, crea un **placeholder visual** en lugar de romper la app.

### 4) ROS en segundo plano

- `torpy_app/ros/spin_thread.py`: hilo con `MultiThreadedExecutor` para no bloquear la GUI.
- `torpy_app/ros/init_thread.py`: inicializa nodos ROS asíncronamente y los conecta a widgets.
- `torpy_app/ros/camera_node.py`: suscriptor de imágenes comprimidas con fallback dummy cuando ROS2 no está.

### 5) Widgets de interfaz

- `interfaces/widgets/modulo_velocidad.py`: controles de movimiento del robot (botones/joystick/velocidad).
- `interfaces/widgets/camera_widget.py`: modo cámara y modo diagrama del robot.
- `interfaces/widgets/lidar_widget.py`: viewer LiDAR con fallback simulado cuando no hay ROS.

---

## Estructura del repositorio

```text
.
├── main.py                      # Launcher principal
├── torpy_app/
│   ├── app.py                   # Arranque de app
│   ├── config.py                # Detección/carga de dependencias
│   ├── ros/                     # Hilos y nodos ROS2
│   └── ui/main_window.py        # Ventana principal
├── interfaces/
│   ├── widgets/                 # Widgets funcionales (cámara, lidar, velocidad)
│   ├── input/                   # Lectura de joystick/gamepad
│   ├── herramientas/            # utilidades gráficas
│   ├── multimedia/              # iconos
│   └── tests/                   # scripts de prueba manual
├── ui/splash/                   # pantalla de carga/splash (módulo alterno)
├── pantalla_de_carga/           # compatibilidad hacia ui.splash
└── scripts/legacy/              # código legado (referencia)
```

---

## Requisitos recomendados

- Python 3.10+
- PyQt6
- (Opcional, para modo ROS) ROS2 + `rclpy` + mensajes de sensores
- (Opcional, para cámara real) `opencv-python`, `numpy`

> Nota: la app está preparada para arrancar sin todos los paquetes instalados, pero con funcionalidad reducida.

---

## Cómo ejecutar

Desde la raíz del repo:

```bash
python3 main.py
```

Si estás en entorno ROS2, recuerda cargar tu setup antes:

```bash
source /opt/ros/<distro>/setup.bash
python3 main.py
```

---

## Tópicos ROS esperados (por defecto)

- Cámara: `/image_raw/compressed`
- LiDAR: `/scan` (instanciado en ventana principal)

Si tu robot publica en otros tópicos, ajusta los parámetros al crear los widgets/nodos.

---

## Detalles útiles para revisar (checklist rápido)

### A. La app abre pero no hay datos de cámara

1. Verifica que exista tráfico en el tópico:
   - `ros2 topic list`
   - `ros2 topic echo /image_raw/compressed --once`
2. Confirma que OpenCV/Numpy estén instalados.
3. Revisa logs de arranque (`ROS2 disponible`, `CameraNode`, conteo de frames).

### B. El LiDAR no muestra puntos

1. Confirma tópico correcto:
   - `ros2 topic list`
   - `ros2 topic echo /scan --once`
2. Ajusta escala en el panel del widget LiDAR.
3. Verifica QoS y tipo de mensaje (`sensor_msgs/msg/LaserScan`).

### C. Controles de velocidad no mueven el robot

1. Verifica que el publicador de `cmd_vel` esté activo en `modulo_velocidad.py`.
2. Comprueba que el robot/stack de navegación esté escuchando el tópico de velocidad correcto.
3. Si usas gamepad, prueba primero botones para aislar si el problema es de input.

### D. Se congela o cierra al iniciar

1. Ejecuta en terminal para capturar trazas.
2. Observa salida de `config.cargar_dependencias()` para identificar import faltante.
3. Si ROS2 no está listo, valida `source` del entorno antes de iniciar.

---

## Estado del código

- Hay una estructura moderna en `torpy_app/` (entrypoint, UI, ROS threads, fallback).
- Existen módulos **legacy** y wrappers de splash para compatibilidad.
- El proyecto ya está orientado a “degradación elegante” cuando falta ROS o alguna interfaz.

---

## Recomendaciones de mejora (siguientes pasos)

1. Añadir `requirements.txt` o `pyproject.toml` con dependencias mínimas/optativas.
2. Centralizar configuración de tópicos ROS en un archivo único (por entorno/robot).
3. Incorporar pruebas automáticas básicas para widgets y arranque en modo sin ROS.
4. Documentar mapeo exacto de `cmd_vel` y sensibilidad del joystick para operación en campo.

---

## Licencia

Pendiente de definir.
