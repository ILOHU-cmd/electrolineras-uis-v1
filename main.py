"""
Programa principal del proyecto de aula.
"""

from src.ui.menu import ejecutar_menu
from src.utils.validacion import limpiar_pantalla


def main():
    limpiar_pantalla()
    ejecutar_menu()


if __name__ == "__main__":
    main()
