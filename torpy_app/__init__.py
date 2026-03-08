"""Paquete principal de la aplicación TurtleBot."""


def run() -> int:
    """Entry-point perezoso para evitar imports pesados al importar el paquete."""
    from .app import run as _run

    return _run()


__all__ = ["run"]
