"""
archivos.py
Funciones para guardar y leer archivos en distintos formatos.
El programa usa estos archivos para guardar el historial de
recargas y los resultados de la simulacion.

Formatos manejados: .txt  .csv  .json  .xlsx
"""

import csv
import json
import os
from datetime import datetime

# Intentar importar openpyxl (para archivos Excel)
# Si no esta instalado, se avisa al usuario cuando lo necesite
try:
    import openpyxl
    EXCEL_DISPONIBLE = True
except ImportError:
    EXCEL_DISPONIBLE = False


# Carpeta donde se guardan todos los archivos generados
CARPETA_SALIDA = os.path.join(os.path.dirname(__file__), "..", "..", "data", "output")

# Crear la carpeta si no existe
if not os.path.exists(CARPETA_SALIDA):
    os.makedirs(CARPETA_SALIDA)


def obtener_ruta(nombre_archivo):
    # Arma la ruta completa dentro de la carpeta de salida
    return os.path.join(CARPETA_SALIDA, nombre_archivo)


# ── TXT ──────────────────────────────────────────────────────

def guardar_txt(nombre, lineas):
    # Guarda una lista de textos en un archivo .txt
    # Cada elemento de la lista queda en una linea del archivo
    ruta = obtener_ruta(nombre + ".txt")
    archivo = open(ruta, "w", encoding="utf-8")
    for linea in lineas:
        archivo.write(str(linea) + "\n")
    archivo.close()
    return ruta


def leer_txt(nombre):
    # Lee un archivo .txt y devuelve una lista con sus lineas
    ruta = obtener_ruta(nombre + ".txt")
    if not os.path.exists(ruta):
        return []
    archivo = open(ruta, "r", encoding="utf-8")
    lineas = archivo.readlines()
    archivo.close()
    # Quitar el salto de linea al final de cada linea
    resultado = []
    for linea in lineas:
        resultado.append(linea.rstrip("\n"))
    return resultado


# ── CSV ───────────────────────────────────────────────────────

def guardar_csv(nombre, filas, encabezados=None):
    # Guarda una lista de diccionarios en un archivo .csv
    # Los encabezados son los nombres de las columnas
    ruta = obtener_ruta(nombre + ".csv")
    if len(filas) == 0:
        return ruta

    archivo = open(ruta, "w", newline="", encoding="utf-8")

    if isinstance(filas[0], dict):
        # Si son diccionarios, las claves son los encabezados
        columnas = encabezados if encabezados else list(filas[0].keys())
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(filas)
    else:
        # Si son listas simples, escribir fila por fila
        escritor = csv.writer(archivo)
        if encabezados:
            escritor.writerow(encabezados)
        escritor.writerows(filas)

    archivo.close()
    return ruta


def leer_csv(nombre):
    # Lee un archivo .csv y devuelve una lista de diccionarios
    ruta = obtener_ruta(nombre + ".csv")
    if not os.path.exists(ruta):
        return []
    archivo = open(ruta, "r", encoding="utf-8")
    lector = csv.DictReader(archivo)
    filas = list(lector)
    archivo.close()
    return filas


def agregar_fila_csv(nombre, fila, encabezados):
    # Agrega una sola fila a un csv existente (o lo crea si no existe)
    # Se usa para ir guardando las recargas una por una durante la simulacion
    ruta = obtener_ruta(nombre + ".csv")
    archivo_existe = os.path.exists(ruta)

    archivo = open(ruta, "a", newline="", encoding="utf-8")
    escritor = csv.DictWriter(archivo, fieldnames=encabezados)

    # Solo escribir el encabezado si el archivo es nuevo
    if not archivo_existe:
        escritor.writeheader()

    escritor.writerow(fila)
    archivo.close()


# ── JSON ──────────────────────────────────────────────────────

def guardar_json(nombre, datos):
    # Guarda un diccionario o lista en un archivo .json
    # indent=4 hace que el archivo sea legible para humanos
    ruta = obtener_ruta(nombre + ".json")
    archivo = open(ruta, "w", encoding="utf-8")
    json.dump(datos, archivo, ensure_ascii=False, indent=4)
    archivo.close()
    return ruta


def leer_json(nombre):
    # Lee un archivo .json y devuelve su contenido
    # Retorna None si el archivo no existe
    ruta = obtener_ruta(nombre + ".json")
    if not os.path.exists(ruta):
        return None
    archivo = open(ruta, "r", encoding="utf-8")
    datos = json.load(archivo)
    archivo.close()
    return datos


# ── XLSX ──────────────────────────────────────────────────────

def guardar_xlsx(nombre, filas, encabezados=None):
    # Guarda los datos en un archivo Excel .xlsx
    # Requiere que openpyxl este instalado
    if not EXCEL_DISPONIBLE:
        print("La libreria openpyxl no esta instalada.")
        print("Instala con: pip install openpyxl")
        print("Guardando como CSV en su lugar...")
        return guardar_csv(nombre, filas, encabezados)

    ruta = obtener_ruta(nombre + ".xlsx")
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.title = nombre[:31]  # Excel no acepta titulos de mas de 31 caracteres

    if len(filas) > 0 and isinstance(filas[0], dict):
        columnas = encabezados if encabezados else list(filas[0].keys())
        hoja.append(columnas)
        for fila in filas:
            hoja.append([fila.get(col, "") for col in columnas])
    else:
        if encabezados:
            hoja.append(encabezados)
        for fila in filas:
            hoja.append(fila)

    libro.save(ruta)
    return ruta


# ── FUNCIONES ESPECIFICAS DEL PROYECTO ───────────────────────

# Nombres de columnas del historial de recargas
COLUMNAS_RECARGAS = [
    "timestamp",
    "vehiculo_id",
    "vehiculo_nombre",
    "electrolinera_id",
    "electrolinera_nombre",
    "nodo_origen",
    "nivel_bateria_llegada",
    "distancia_metros"
]


def registrar_recarga(evento):
    # Guarda un evento de recarga en el historial CSV
    # Se llama cada vez que un vehiculo llega a una electrolinera
    agregar_fila_csv("historial_recargas", evento, COLUMNAS_RECARGAS)


def guardar_estadisticas(estadisticas):
    # Guarda el resumen de la simulacion en un archivo JSON
    # Le pone la fecha y hora en el nombre para no sobreescribir anteriores
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    return guardar_json("estadisticas_" + fecha, estadisticas)


def generar_reporte_txt(estadisticas):
    """
    Genera el archivo reporte_simulacion.txt con el historial
    completo de todos los recorridos, calles visitadas y
    alertas de bateria baja.
    """
    lineas = []
    separador_grueso  = "=" * 70
    separador_delgado = "-" * 70
    separador_alerta  = "!" * 70

    # Encabezado del reporte
    lineas.append(separador_grueso)
    lineas.append("  REPORTE DE SIMULACION - SISTEMA DE ELECTROLINERAS BGA")
    lineas.append("  Universidad Industrial de Santander - Semestre 2026-1")
    lineas.append(separador_grueso)
    lineas.append("  Fecha: " + datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))
    lineas.append("  Total recorridos: " + str(estadisticas.get("total_recorridos", 0)))
    lineas.append("  Total recargas  : " + str(estadisticas.get("total_recargas", 0)))
    lineas.append(separador_grueso)
    lineas.append("")

    # Detalle de cada recorrido
    for rec in estadisticas.get("recorridos", []):
        numero      = rec.get("recorrido_num", "?")
        vehiculo    = rec.get("vehiculo", "?")
        origen      = rec.get("origen_nombre", str(rec.get("origen_osm", "?")))
        destino     = rec.get("destino_nombre", str(rec.get("destino_osm", "?")))
        distancia   = rec.get("distancia_km", 0.0)
        bateria     = rec.get("bateria_final_pct", 0.0)
        hubo_recarga = rec.get("recarga_activada", False)
        historial   = rec.get("historial_ruta", [])

        lineas.append(separador_delgado)
        lineas.append("  RECORRIDO #" + str(numero))
        lineas.append(separador_delgado)
        lineas.append("  Vehiculo      : " + vehiculo)
        lineas.append("  Origen        : " + origen)
        lineas.append("  Destino       : " + destino)
        lineas.append("  Distancia     : " + str(round(distancia, 3)) + " km")
        lineas.append("  Bateria final : " + str(round(bateria, 1)) + " %")

        if hubo_recarga:
            electrolinera = rec.get("electrolinera_usada", "?")
            dist_extra    = rec.get("distancia_a_electro_km", 0.0)
            lineas.append("  Electrolinera : " + electrolinera +
                          "  (desvio: " + str(round(dist_extra, 3)) + " km extra)")
        lineas.append("")

        # Tabla de pasos del recorrido
        if len(historial) > 0:
            lineas.append("  Paso   Nodo OSM       Calle                           Parcial    Acumulado")
            lineas.append("  " + "-" * 68)

            for paso in historial:
                tipo   = paso.get("tipo_especial", None)
                nombre = paso.get("nombre_lugar", "")
                calle  = str(paso.get("calle_desde") or "sin nombre")[:30]
                dp     = paso.get("dist_parcial_m", 0.0)
                da     = paso.get("dist_acum_m", 0.0)
                nodo   = str(paso.get("nodo_osm", ""))

                # Marcar nodos especiales con etiquetas
                if tipo == "electrolinera":
                    etiqueta = "[ELECTRO]"
                elif tipo == "referencia":
                    etiqueta = "[REF]    "
                else:
                    etiqueta = "         "

                if paso["paso"] > 1:
                    distancia_parcial = str(round(dp, 1)) + "m"
                else:
                    distancia_parcial = "origen"

                linea = ("  " + str(paso["paso"]).rjust(4) + "   " +
                         etiqueta + " " + nodo.rjust(10) + "   " +
                         calle.ljust(30) + "   " +
                         distancia_parcial.rjust(8) + "   " +
                         (str(round(da, 1)) + "m").rjust(9))

                # Agregar nombre del lugar si es especial
                if nombre:
                    linea = linea + "   <<< " + nombre + " >>>"

                lineas.append(linea)

            lineas.append("")

        # Bloque de alerta si hubo recarga de emergencia
        if hubo_recarga:
            nodo_desvio   = rec.get("origen_osm", "desconocido")
            electrolinera = rec.get("electrolinera_usada", "?")
            dist_extra    = rec.get("distancia_a_electro_km", 0.0)

            lineas.append(separador_alerta)
            lineas.append("  !!!  CAMBIO DE RUTA: EMERGENCIA POR BATERIA BAJA  !!!")
            lineas.append(separador_alerta)
            lineas.append("  Nodo donde se tomo la decision : " + str(nodo_desvio))
            lineas.append("  Nivel de bateria en ese momento: " + str(round(bateria, 1)) + " %  (rango critico: 10% - 20%)")
            lineas.append("  El vehiculo se redirige hacia  : " + electrolinera)
            lineas.append("  Distancia adicional al punto   : " + str(round(dist_extra, 3)) + " km")
            lineas.append(separador_alerta)
            lineas.append("")

    # Resumen final
    lineas.append(separador_grueso)
    lineas.append("  RESUMEN FINAL")
    lineas.append(separador_grueso)
    lineas.append("")
    lineas.append("  Uso de electrolineras:")
    lineas.append("  " + "-" * 50)

    uso = estadisticas.get("uso_electrolineras", {})
    if len(uso) > 0:
        # Ordenar de mayor a menor uso
        electrolineras_ordenadas = sorted(uso.items(), key=lambda x: x[1], reverse=True)
        for nombre_e, conteo in electrolineras_ordenadas:
            barra = "█" * conteo
            lineas.append("  " + nombre_e.ljust(40) + str(conteo).rjust(3) + " recargas  " + barra)
    else:
        lineas.append("  Ninguna recarga registrada en esta simulacion.")

    lineas.append("")
    lineas.append("  Resultados por vehiculo:")
    lineas.append("  " + "-" * 50)

    for nombre_v, datos in estadisticas.get("por_vehiculo", {}).items():
        lineas.append("  " + nombre_v.ljust(35) +
                      "Recargas: " + str(datos["recargas"]).rjust(3) +
                      "   km totales: " + str(round(datos["km_total"], 1)).rjust(8))

    lineas.append("")
    lineas.append(separador_grueso)
    lineas.append("  FIN DEL REPORTE")
    lineas.append(separador_grueso)

    # Escribir el archivo
    ruta = obtener_ruta("reporte_simulacion.txt")
    archivo = open(ruta, "w", encoding="utf-8")
    for linea in lineas:
        archivo.write(linea + "\n")
    archivo.close()

    return ruta
