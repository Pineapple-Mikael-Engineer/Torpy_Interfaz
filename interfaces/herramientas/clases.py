"""
Control de robot diferencial usando un joystick 2D dentro de un círculo de radio 1.

Entrada:
    (x, y)  => posición del joystick, ambos entre [-1, 1] y dentro de un círculo unitario
    speed_factor ∈ [0.25, 1] => escala de velocidad configurable

Salida:
    (vL, vR)  => velocidades en escala [0, 200]
                 100 = detenido
                 <100 = retroceso
                 >100 = avance

Reglas:
    y controla avance/retroceso (ambas ruedas)
    x controla giro diferencial (una rueda acelera y la otra desacelera)
    Si y = 0 => giro puro (ruedas opuestas)
"""

class DifferentialDriver:
    def __init__(self, speed_factor: float = 1.0):
        self.set_speed_factor(speed_factor)

    def set_speed_factor(self, sf: float):
        """
        Limita el speed_factor al rango permitido y lo guarda.
        sf = 1.0   => rango máximo [0,200]
        sf = 0.25  => rango mínimo [75,125]
        """
        self.speed_factor = max(0.25, min(1.0, sf))

    def compute_velocity(self, x: float, y: float):
        """
        Calcula vL y vR a partir de x,y normalizados dentro del círculo unitario.
        """

        # Limitar joystick al círculo unitario
        if x*x + y*y > 1.0:
            # Proyectar al borde del círculo
            import math
            mag = math.sqrt(x*x + y*y)
            x /= mag
            y /= mag

        # Base neutral
        neutral = 100.0

        # Convertir movimientos a aceleración diferencial
        # y controla avance/retroceso
        # x controla giro (positivo = giro derecha)
        # mezcla diferencial: salida normalizada en [-1,1]
        left_norm  = y + x
        right_norm = y - x

        # Limitar a [-1,1]
        left_norm  = max(-1.0, min(1.0, left_norm))
        right_norm = max(-1.0, min(1.0, right_norm))

        # Aplicar factor de velocidad
        # Mapea [-1,1] según factor: salida en [100 - 100*sf, 100 + 100*sf]
        min_val = 100 - 100 * self.speed_factor
        max_val = 100 + 100 * self.speed_factor

        vL = min_val + (left_norm + 1)  * (max_val - min_val) / 2
        vR = min_val + (right_norm + 1) * (max_val - min_val) / 2

        return round(vL, 2), round(vR, 2)


# ================= PRUEBAS =================
if __name__ == "__main__":
    driver = DifferentialDriver(speed_factor=0.7)

    test_inputs = [
        (0, 0),      # quieto
        (0, 1),      # avanzar recto
        (0, -1),     # retroceder recto
        (1, 0),      # giro puro derecha
        (-1, 0),     # giro puro izquierda
        (0.5, 0.5),  # avanzar girando derecha
        (-0.5, 0.5), # avanzar girando izquierda
    ]

    for x, y in test_inputs:
        vL, vR = driver.compute_velocity(x, y)
        print(f"Joystick({x:>4}, {y:>4}) => vL={vL:>6}, vR={vR:>6}")
