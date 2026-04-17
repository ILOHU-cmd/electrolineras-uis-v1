"""
Funciones de lectura y escritura de archivos del proyecto.
"""

import csv
import json
import os
import webbrowser
from datetime import datetime

try:
    import openpyxl
    XLSX_DISPONIBLE = True
except ImportError:
    XLSX_DISPONIBLE = False


DIR_OUTPUT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "output")
)
os.makedirs(DIR_OUTPUT, exist_ok=True)


def _ruta(nombre_archivo):
    return os.path.abspath(os.path.join(DIR_OUTPUT, nombre_archivo))


def guardar_txt(nombre, lineas):
    ruta = _ruta(nombre + ".txt")
    with open(ruta, "w", encoding="utf-8") as archivo:
        i = 0
        while i < len(lineas):
            archivo.write(str(lineas[i]) + "\n")
            i = i + 1
    return ruta


def leer_txt(nombre):
    ruta = _ruta(nombre + ".txt")
    if not os.path.exists(ruta):
        return []

    with open(ruta, "r", encoding="utf-8") as archivo:
        return [linea.rstrip("\n") for linea in archivo.readlines()]


def guardar_csv(nombre, filas, encabezados=None):
    ruta = _ruta(nombre + ".csv")
    if not filas:
        return ruta

    with open(ruta, "w", newline="", encoding="utf-8") as archivo:
        if isinstance(filas[0], dict):
            campos = encabezados or list(filas[0].keys())
            escritor = csv.DictWriter(archivo, fieldnames=campos)
            escritor.writeheader()
            escritor.writerows(filas)
        else:
            escritor = csv.writer(archivo)
            if encabezados:
                escritor.writerow(encabezados)
            escritor.writerows(filas)

    return ruta


def leer_csv(nombre):
    ruta = _ruta(nombre + ".csv")
    if not os.path.exists(ruta):
        return []

    with open(ruta, "r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        return list(lector)


def guardar_json(nombre, datos):
    ruta = _ruta(nombre + ".json")
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=4)
    return ruta


def leer_json(nombre):
    ruta = _ruta(nombre + ".json")
    if not os.path.exists(ruta):
        return None

    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def guardar_xlsx(nombre, filas, encabezados=None):
    ruta = _ruta(nombre + ".xlsx")

    if not XLSX_DISPONIBLE:
        print("openpyxl no esta instalado. Se guardara como CSV.")
        return guardar_csv(nombre, filas, encabezados)

    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.title = nombre[:31]

    if filas and isinstance(filas[0], dict):
        columnas = encabezados or list(filas[0].keys())
        hoja.append(columnas)

        i = 0
        while i < len(filas):
            fila = filas[i]
            hoja.append([fila.get(columna, "") for columna in columnas])
            i = i + 1
    else:
        if encabezados:
            hoja.append(encabezados)

        i = 0
        while i < len(filas):
            hoja.append(filas[i])
            i = i + 1

    libro.save(ruta)
    return ruta


def registrar_recarga(evento):
    ruta = _ruta("historial_recargas.csv")
    existe = os.path.exists(ruta)

    campos = [
        "timestamp",
        "vehiculo_id",
        "vehiculo_nombre",
        "electrolinera_id",
        "electrolinera_nombre",
        "nodo_origen_osm",
        "nivel_bateria_llegada",
        "distancia_recorrida_m",
    ]

    with open(ruta, "a", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        if not existe:
            escritor.writeheader()
        escritor.writerow({campo: evento.get(campo, "") for campo in campos})


def exportar_estadisticas_json(estadisticas):
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    return guardar_json("estadisticas_" + fecha, estadisticas)


def leer_semillas_guardadas():
    semillas = leer_json("semillas_simulacion")
    if semillas is None:
        return []
    if not isinstance(semillas, list):
        return []
    return semillas


def guardar_semilla_guardada(semilla, cantidad_recorridos):
    semillas = leer_semillas_guardadas()

    i = 0
    while i < len(semillas):
        actual = semillas[i]
        if actual.get("semilla") == semilla:
            copia = dict(actual)
            copia["ya_existia"] = True
            return copia
        i = i + 1

    codigo = "S" + str(len(semillas) + 1)
    nueva = {
        "codigo": codigo,
        "semilla": semilla,
        "fecha_guardado": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cantidad_recorridos": cantidad_recorridos,
    }
    semillas.append(nueva)
    guardar_json("semillas_simulacion", semillas)

    copia = dict(nueva)
    copia["ya_existia"] = False
    return copia


def abrir_archivo(ruta):
    ruta_normalizada = os.path.abspath(ruta)
    if not os.path.exists(ruta_normalizada):
        return False

    try:
        if os.name == "nt":
            os.startfile(ruta_normalizada)
        else:
            webbrowser.open("file://" + ruta_normalizada)
        return True
    except Exception:
        return False
