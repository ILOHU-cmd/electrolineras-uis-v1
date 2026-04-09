"""
=============================================================
PROYECTO DE AULA - SEMESTRE 2026-1
Universidad Industrial de Santander (UIS)
Asignaturas: Algoritmos y Programación | Matemáticas Discretas
--------------------------------------------------------------
Sistema para la infraestructura y modelo predictivo de puntos
de carga (Electrolineras) para vehículos eléctricos en el
área metropolitana de Bucaramanga.
=============================================================
"""

from src.ui.menu import Menu
from src.utils.validacion import limpiar_pantalla


def main():
    """Punto de entrada principal del sistema."""
    limpiar_pantalla()
    menu = Menu()
    menu.ejecutar()


if __name__ == "__main__":
    main()
