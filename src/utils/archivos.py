"""
archivos.py
-----------
Módulo de lectura y escritura de archivos en formatos:
.txt, .csv, .json, .xlsx
Requisito explícito de la rúbrica del profesor.
"""

import csv
import json
import os
from datetime import datetime

# openpyxl se importa con manejo de error para no bloquear el resto
try:
    import openpyxl
    XLSX_DISPONIBLE = True
except ImportError:
    XLSX_DISPONIBLE = False

# ─────────────────────────────────────────────────────────────
# RUTAS BASE
# ─────────────────────────────────────────────────────────────
DIR_OUTPUT = os.path.join(os.path.dirname(__file__), "..", "..", "data", "output")
os.makedirs(DIR_OUTPUT, exist_ok=True)


def _ruta(nombre_archivo: str) -> str:
    """Retorna la ruta completa dentro del directorio de salida."""
    return os.path.join(DIR_OUTPUT, nombre_archivo)


# ─────────────────────────────────────────────────────────────
# TXT
# ─────────────────────────────────────────────────────────────
def guardar_txt(nombre: str, lineas: list) -> str:
    """
    Guarda una lista de strings en un archivo .txt.

    Parámetros
    ----------
    nombre : str
        Nombre del archivo (sin extensión).
    lineas : list[str]
        Líneas de texto a escribir.

    Retorna
    -------
    str
        Ruta del archivo guardado.
    """
    ruta = _ruta(f"{nombre}.txt")
    with open(ruta, "w", encoding="utf-8") as f:
        for linea in lineas:
            f.write(str(linea) + "\n")
    return ruta


def leer_txt(nombre: str) -> list:
    """Lee un archivo .txt y retorna lista de líneas."""
    ruta = _ruta(f"{nombre}.txt")
    if not os.path.exists(ruta):
        return []
    with open(ruta, "r", encoding="utf-8") as f:
        return [linea.rstrip("\n") for linea in f.readlines()]


# ─────────────────────────────────────────────────────────────
# CSV
# ─────────────────────────────────────────────────────────────
def guardar_csv(nombre: str, filas: list, encabezados: list = None) -> str:
    """
    Guarda una lista de diccionarios o listas en un .csv.

    Parámetros
    ----------
    nombre : str
        Nombre del archivo (sin extensión).
    filas : list[dict] | list[list]
        Datos a guardar.
    encabezados : list[str], opcional
        Encabezados de columnas (se infieren si filas son dicts).
    """
    ruta = _ruta(f"{nombre}.csv")
    if not filas:
        return ruta

    with open(ruta, "w", newline="", encoding="utf-8") as f:
        if isinstance(filas[0], dict):
            campos = encabezados or list(filas[0].keys())
            writer = csv.DictWriter(f, fieldnames=campos)
            writer.writeheader()
            writer.writerows(filas)
        else:
            writer = csv.writer(f)
            if encabezados:
                writer.writerow(encabezados)
            writer.writerows(filas)
    return ruta


def leer_csv(nombre: str) -> list:
    """Lee un .csv y retorna lista de diccionarios."""
    ruta = _ruta(f"{nombre}.csv")
    if not os.path.exists(ruta):
        return []
    with open(ruta, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


# ─────────────────────────────────────────────────────────────
# JSON
# ─────────────────────────────────────────────────────────────
def guardar_json(nombre: str, datos: dict | list) -> str:
    """Guarda datos en un archivo .json con formato legible."""
    ruta = _ruta(f"{nombre}.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)
    return ruta


def leer_json(nombre: str) -> dict | list | None:
    """Lee un .json y retorna su contenido. None si no existe."""
    ruta = _ruta(f"{nombre}.json")
    if not os.path.exists(ruta):
        return None
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────────────────────────
# XLSX
# ─────────────────────────────────────────────────────────────
def guardar_xlsx(nombre: str, filas: list, encabezados: list = None) -> str:
    """
    Guarda datos en un archivo .xlsx.
    Requiere openpyxl instalado.
    """
    ruta = _ruta(f"{nombre}.xlsx")
    if not XLSX_DISPONIBLE:
        print("  ⚠  openpyxl no está instalado. Guardando como CSV en su lugar.")
        return guardar_csv(nombre, filas, encabezados)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = nombre[:31]  # Excel limita título de hoja a 31 chars

    if filas and isinstance(filas[0], dict):
        cols = encabezados or list(filas[0].keys())
        ws.append(cols)
        for fila in filas:
            ws.append([fila.get(c, "") for c in cols])
    else:
        if encabezados:
            ws.append(encabezados)
        for fila in filas:
            ws.append(fila)

    wb.save(ruta)
    return ruta


# ─────────────────────────────────────────────────────────────
# REGISTRO DE RECARGAS (uso transversal en simulación)
# ─────────────────────────────────────────────────────────────
def registrar_recarga(evento: dict) -> None:
    """
    Agrega un evento de recarga al CSV de historial.

    Campos esperados en evento:
    - timestamp, vehiculo_id, vehiculo_nombre, electrolinera_id,
      electrolinera_nombre, nodo_origen_osm, nivel_bateria_llegada,
      distancia_recorrida_m
    """
    ruta = _ruta("historial_recargas.csv")
    existe = os.path.exists(ruta)

    campos = [
        "timestamp", "vehiculo_id", "vehiculo_nombre",
        "electrolinera_id", "electrolinera_nombre",
        "nodo_origen_osm", "nivel_bateria_llegada",
        "distancia_recorrida_m",
    ]

    with open(ruta, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        if not existe:
            writer.writeheader()
        writer.writerow({k: evento.get(k, "") for k in campos})


def exportar_estadisticas_json(estadisticas: dict) -> str:
    """Exporta el resumen estadístico de la simulación a JSON."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return guardar_json(f"estadisticas_{ts}", estadisticas)
