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


# ─────────────────────────────────────────────────────────────
# REPORTE TXT DE SIMULACIÓN  (Mejora: salida a archivo)
# ─────────────────────────────────────────────────────────────

# Separadores visuales reutilizables
_SEP_GRUESO  = "=" * 70
_SEP_DELGADO = "-" * 70
_SEP_ALERTA  = "!" * 70

NOMBRE_REPORTE = "reporte_simulacion"


def generar_reporte_txt(estadisticas: dict) -> str:
    """
    Escribe el historial completo de la simulación en
    `data/output/reporte_simulacion.txt`.

    Estructura del archivo
    ----------------------
    ENCABEZADO GENERAL
      — metadatos: fecha, semilla usada, totales globales

    Por cada recorrido:
      ENCABEZADO DE RECORRIDO
        — vehículo, origen, destino, distancia, batería final

      TABLA DE PASOS  (nodo a nodo desde Dijkstra)
        — paso | nodo OSM | calle | distancia parcial | acumulada

      [Si hubo recarga]
      !!!!!!! CAMBIO DE RUTA: EMERGENCIA POR BATERÍA BAJA !!!!!!!
        — nodo de desvío exacto
        — electrolinera destino
        — distancia adicional al punto de carga

    RESUMEN FINAL
      — ranking de electrolineras por uso
      — km totales y recargas por vehículo

    Parámetros
    ----------
    estadisticas : dict
        Salida directa de `ejecutar_simulacion()`.

    Retorna
    -------
    str
        Ruta absoluta del archivo generado.
    """
    ruta = _ruta(f"{NOMBRE_REPORTE}.txt")
    lineas = []

    # ── ENCABEZADO GENERAL ───────────────────────────────────
    ts_ahora = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    lineas += [
        _SEP_GRUESO,
        "  REPORTE DE SIMULACIÓN — SISTEMA DE ELECTROLINERAS BGA",
        "  Universidad Industrial de Santander · Semestre 2026-1",
        _SEP_GRUESO,
        f"  Fecha de generación : {ts_ahora}",
        f"  Total recorridos    : {estadisticas.get('total_recorridos', 0)}",
        f"  Total recargas      : {estadisticas.get('total_recargas', 0)}",
        _SEP_GRUESO,
        "",
    ]

    # ── DETALLE POR RECORRIDO ────────────────────────────────
    for rec in estadisticas.get("recorridos", []):
        num          = rec.get("recorrido_num", "?")
        vehiculo     = rec.get("vehiculo", "?")
        origen       = rec.get("origen_nombre", rec.get("origen_osm", "?"))
        destino      = rec.get("destino_nombre", rec.get("destino_osm", "?"))
        dist_km      = rec.get("distancia_km", 0.0)
        bat_final    = rec.get("bateria_final_pct", 0.0)
        recarga_ok   = rec.get("recarga_activada", False)
        historial    = rec.get("historial_ruta", [])

        # Encabezado del recorrido
        lineas += [
            _SEP_DELGADO,
            f"  RECORRIDO #{num:>3}",
            _SEP_DELGADO,
            f"  Vehículo       : {vehiculo}",
            f"  Origen         : {origen}",
            f"  Destino        : {destino}",
            f"  Distancia      : {dist_km:.3f} km",
            f"  Batería final  : {bat_final:.1f} %",
        ]

        if recarga_ok:
            electro  = rec.get("electrolinera_usada", "?")
            dist_e   = rec.get("distancia_a_electro_km", 0.0)
            lineas.append(f"  Electrolinera  : {electro}  "
                          f"(desvío: {dist_e:.3f} km adicionales)")
        lineas.append("")

        # Tabla de pasos
        if historial:
            lineas += [
                f"  {'Paso':>4}  {'Nodo OSM':>12}  {'Calle':<30}  "
                f"{'Parcial':>9}  {'Acum.':>9}",
                f"  {'─'*68}",
            ]

            for paso in historial:
                tipo    = paso.get("tipo_especial")
                nombre  = paso.get("nombre_lugar", "")
                calle   = (paso.get("calle_desde") or "─")[:30]
                dp      = paso.get("dist_parcial_m", 0.0)
                da      = paso.get("dist_acum_m", 0.0)
                n_osm   = paso.get("nodo_osm", "")

                # Indicador de tipo de nodo
                if tipo == "electrolinera":
                    marcador = "[ELECTRO]"
                elif tipo == "referencia":
                    marcador = "[REF]    "
                else:
                    marcador = "         "

                dist_p_str = f"{dp:>8.1f}m" if paso["paso"] > 1 else "  origen "
                linea = (f"  {paso['paso']:>4}  {marcador} {n_osm!s:>10}  "
                         f"{calle:<30}  {dist_p_str}  {da:>8.1f}m")

                # Añadir nombre del lugar especial inline
                if nombre:
                    linea += f"   <<< {nombre} >>>"

                lineas.append(linea)

            lineas.append("")  # separador tras tabla

        # ── BLOQUE DE EMERGENCIA POR BATERÍA BAJA ────────────
        if recarga_ok:
            nodo_desvio = rec.get("origen_osm", "?")   # último nodo de la ruta
            electro     = rec.get("electrolinera_usada", "?")
            dist_e      = rec.get("distancia_a_electro_km", 0.0)

            lineas += [
                _SEP_ALERTA,
                "  !!!  CAMBIO DE RUTA: EMERGENCIA POR BATERÍA BAJA  !!!",
                _SEP_ALERTA,
                f"  Nodo de desvío   : {nodo_desvio}",
                f"  Batería al desvío: {bat_final:.1f} %  "
                f"(umbral: 10 % – 20 %)",
                f"  Nueva ruta hacia : {electro}",
                f"  Distancia extra  : {dist_e:.3f} km",
                _SEP_ALERTA,
                "",
            ]

    # ── RESUMEN FINAL ────────────────────────────────────────
    lineas += [
        _SEP_GRUESO,
        "  RESUMEN FINAL",
        _SEP_GRUESO,
        "",
        "  Uso de electrolineras (ordenado por frecuencia):",
        f"  {'─'*50}",
    ]

    uso = estadisticas.get("uso_electrolineras", {})
    if uso:
        for nombre_e, conteo in sorted(uso.items(), key=lambda x: -x[1]):
            barra = "█" * conteo
            lineas.append(f"  {nombre_e:<40}  {conteo:>3} recargas  {barra}")
    else:
        lineas.append("  (ninguna recarga registrada)")

    lineas += ["", "  Por vehículo:", f"  {'─'*50}"]
    for nombre_v, datos in estadisticas.get("por_vehiculo", {}).items():
        lineas.append(
            f"  {nombre_v:<35} | "
            f"Recargas: {datos['recargas']:>3} | "
            f"km totales: {datos['km_total']:>8.1f}"
        )

    lineas += ["", _SEP_GRUESO, "  FIN DEL REPORTE", _SEP_GRUESO]

    # ── ESCRITURA ────────────────────────────────────────────
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))

    return ruta