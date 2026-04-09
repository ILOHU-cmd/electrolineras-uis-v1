"""
validacion.py
-------------
Funciones de validación de entradas del usuario.
Cubre: negativos, fuera de rango, caracteres inválidos.
Requisito explícito de la rúbrica del profesor.
"""

import os
import re


# ─────────────────────────────────────────────────────────────
# LIMPIEZA DE PANTALLA
# ─────────────────────────────────────────────────────────────
def limpiar_pantalla():
    """Limpia la consola según el sistema operativo."""
    os.system("cls" if os.name == "nt" else "clear")


# ─────────────────────────────────────────────────────────────
# VALIDACIÓN DE ENTEROS
# ─────────────────────────────────────────────────────────────
def leer_entero(mensaje: str, minimo: int = None, maximo: int = None) -> int:
    """
    Lee un entero del usuario con validación completa.

    Parámetros
    ----------
    mensaje : str
        Texto que se muestra al usuario.
    minimo : int, opcional
        Valor mínimo permitido (inclusive).
    maximo : int, opcional
        Valor máximo permitido (inclusive).

    Retorna
    -------
    int
        El entero validado.
    """
    while True:
        entrada = input(mensaje).strip()

        # Validar que no esté vacío
        if not entrada:
            print("  ⚠  Entrada vacía. Por favor ingrese un número.\n")
            continue

        # Validar que solo contenga dígitos (y posible signo negativo)
        if not re.fullmatch(r"-?\d+", entrada):
            print("  ⚠  Carácter inválido. Solo se permiten dígitos enteros.\n")
            continue

        valor = int(entrada)

        # Validar rango mínimo
        if minimo is not None and valor < minimo:
            print(f"  ⚠  El valor debe ser mayor o igual a {minimo}.\n")
            continue

        # Validar rango máximo
        if maximo is not None and valor > maximo:
            print(f"  ⚠  El valor debe ser menor o igual a {maximo}.\n")
            continue

        return valor


# ─────────────────────────────────────────────────────────────
# VALIDACIÓN DE FLOTANTES
# ─────────────────────────────────────────────────────────────
def leer_flotante(mensaje: str, minimo: float = None, maximo: float = None) -> float:
    """
    Lee un número flotante con validación de rango y formato.
    """
    while True:
        entrada = input(mensaje).strip()

        if not entrada:
            print("  ⚠  Entrada vacía. Ingrese un número decimal.\n")
            continue

        try:
            valor = float(entrada)
        except ValueError:
            print("  ⚠  Formato inválido. Use punto decimal (ej: 3.14).\n")
            continue

        if minimo is not None and valor < minimo:
            print(f"  ⚠  El valor mínimo permitido es {minimo}.\n")
            continue

        if maximo is not None and valor > maximo:
            print(f"  ⚠  El valor máximo permitido es {maximo}.\n")
            continue

        return valor


# ─────────────────────────────────────────────────────────────
# VALIDACIÓN DE TEXTO
# ─────────────────────────────────────────────────────────────
def leer_texto(mensaje: str, solo_alfa: bool = False, max_len: int = 100) -> str:
    """
    Lee texto con validación de longitud y caracteres.

    Parámetros
    ----------
    solo_alfa : bool
        Si True, solo acepta letras, espacios y tildes.
    max_len : int
        Longitud máxima permitida.
    """
    while True:
        entrada = input(mensaje).strip()

        if not entrada:
            print("  ⚠  Campo obligatorio. No puede estar vacío.\n")
            continue

        if len(entrada) > max_len:
            print(f"  ⚠  Texto demasiado largo (máx. {max_len} caracteres).\n")
            continue

        if solo_alfa and not re.fullmatch(r"[A-Za-záéíóúÁÉÍÓÚñÑ ]+", entrada):
            print("  ⚠  Solo se permiten letras y espacios.\n")
            continue

        return entrada


# ─────────────────────────────────────────────────────────────
# VALIDACIÓN DE PORCENTAJE DE BATERÍA
# ─────────────────────────────────────────────────────────────
def validar_nivel_bateria(nivel: float) -> bool:
    """
    Verifica si el nivel de batería está en rango válido [0, 100].

    Retorna
    -------
    bool
        True si el nivel es válido.
    """
    return 0.0 <= nivel <= 100.0


# ─────────────────────────────────────────────────────────────
# CONFIRMACIÓN S/N
# ─────────────────────────────────────────────────────────────
def confirmar(mensaje: str) -> bool:
    """
    Solicita confirmación S/N al usuario.

    Retorna
    -------
    bool
        True si el usuario responde 's' o 'S'.
    """
    while True:
        resp = input(f"{mensaje} [s/n]: ").strip().lower()
        if resp in ("s", "n"):
            return resp == "s"
        print("  ⚠  Respuesta inválida. Ingrese 's' para sí o 'n' para no.\n")
