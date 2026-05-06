"""
simulacion.py
Modulo que simula los recorridos de los vehiculos electricos.

La logica funciona asi:
1. Se eligen al azar un origen y un destino entre los puntos de referencia
2. Se calcula la ruta mas corta con Dijkstra
3. Se descuenta la bateria segun la distancia recorrida
4. Si la bateria cae entre 10% y 20%, se busca la electrolinera mas cercana
5. Se registra cada recarga en el historial CSV
6. Al final se genera el reporte TXT con todos los detalles
"""

import random
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.grafo.algoritmos_grafo import dijkstra, electrolinera_mas_cercana
from src.grafo.constructor_grafo import obtener_nodos_electrolineras, obtener_nodos_referencia, obtener_nombre_nodo
from src.utils.archivos import registrar_recarga, guardar_estadisticas, generar_reporte_txt
from data.datos_estaticos import VEHICULOS

# Nivel de bateria en que el vehiculo busca electrolinera
BATERIA_MINIMA  = 10.0   # si baja de aqui es critico
BATERIA_UMBRAL  = 20.0   # entre 10% y 20% activa la busqueda
BATERIA_INICIAL = 100.0  # siempre arranca con carga completa

# Para convertir metros a kilometros
METROS_POR_KM = 1000.0


# ─────────────────────────────────────────────────────────────
# FUNCIONES DE TRAZABILIDAD DE RUTA
# ─────────────────────────────────────────────────────────────

def trazar_historial_ruta(grafo, lista_nodos):
    """
    Recibe la lista de nodos que devuelve Dijkstra y construye
    un historial detallado paso a paso, extrayendo el nombre
    de cada calle desde los atributos de las aristas del grafo.

    Devuelve una lista de diccionarios, uno por cada nodo visitado.
    """
    if len(lista_nodos) == 0:
        return []

    historial = []
    distancia_acumulada = 0.0

    for i in range(len(lista_nodos)):
        nodo = lista_nodos[i]
        datos_nodo   = grafo.nodes[nodo]
        tipo         = datos_nodo.get("tipo", None)
        nombre_lugar = datos_nodo.get("nombre_lugar", None)

        # Calcular distancia y nombre de calle desde el nodo anterior
        nombre_calle   = None
        distancia_paso = 0.0

        if i > 0:
            nodo_anterior = lista_nodos[i - 1]
            datos_aristas = grafo.get_edge_data(nodo_anterior, nodo)

            if datos_aristas:
                # Tomar la arista de menor longitud (la que uso Dijkstra)
                mejor_arista = None
                mejor_peso   = float("inf")
                for arista in datos_aristas.values():
                    peso = arista.get("length", float("inf"))
                    if peso < mejor_peso:
                        mejor_peso   = peso
                        mejor_arista = arista

                distancia_paso = mejor_arista.get("length", 0.0)

                # El nombre de la calle puede ser texto o lista
                nombre_raw = mejor_arista.get("name", None)
                if isinstance(nombre_raw, list):
                    nombre_calle = " / ".join(nombre_raw)
                elif nombre_raw:
                    nombre_calle = nombre_raw
                else:
                    nombre_calle = "sin nombre"

            distancia_acumulada = distancia_acumulada + distancia_paso

        historial.append({
            "paso":           i + 1,
            "nodo_osm":       nodo,
            "tipo_especial":  tipo,
            "nombre_lugar":   nombre_lugar,
            "calle_desde":    nombre_calle,
            "dist_parcial_m": round(distancia_paso, 1),
            "dist_acum_m":    round(distancia_acumulada, 1)
        })

    return historial


# ─────────────────────────────────────────────────────────────
# FUNCIONES DE BATERIA
# ─────────────────────────────────────────────────────────────

def calcular_consumo(distancia_m, consumo_kwh_100km, bateria_total_kwh):
    """
    Calcula cuanto porcentaje de bateria se consume al recorrer
    una distancia dada.

    Formula:
      energia_gastada = (distancia_km / 100) * consumo_kwh_100km
      porcentaje      = (energia_gastada / bateria_total_kwh) * 100
    """
    distancia_km    = distancia_m / METROS_POR_KM
    energia_gastada = (distancia_km / 100.0) * consumo_kwh_100km
    porcentaje      = (energia_gastada / bateria_total_kwh) * 100.0
    return porcentaje


def necesita_recarga(nivel_bateria):
    """
    Retorna True si el nivel de bateria esta en el rango critico
    que activa la busqueda de electrolinera (entre 10% y 20%).
    """
    return BATERIA_MINIMA <= nivel_bateria <= BATERIA_UMBRAL


# ─────────────────────────────────────────────────────────────
# SIMULACION PRINCIPAL
# ─────────────────────────────────────────────────────────────

def ejecutar_simulacion(grafo, n_recorridos=20, semilla=None):
    """
    Ejecuta la simulacion completa de recorridos.
    Devuelve un diccionario con todas las estadisticas.
    """
    # Si se fija una semilla, los resultados son reproducibles
    if semilla is not None:
        random.seed(semilla)

    # Obtener los nodos del grafo que son electrolineras y referencias
    nodos_electro = obtener_nodos_electrolineras(grafo)
    nodos_ref     = obtener_nodos_referencia(grafo)

    if len(nodos_electro) == 0:
        print("No se encontraron electrolineras en el grafo.")
        return {}

    if len(nodos_ref) == 0:
        print("No se encontraron puntos de referencia en el grafo.")
        return {}

    # Convertir los nodos de referencia a una lista para elegir al azar
    lista_nodos_ref = list(nodos_ref.values())

    # Crear una lista con los vehiculos a usar en la simulacion
    lista_vehiculos = list(VEHICULOS.values())

    # Estructura que guarda todos los resultados
    estadisticas = {
        "total_recorridos":   0,
        "total_recargas":     0,
        "uso_electrolineras": {},   # cuantas veces se uso cada electrolinera
        "por_vehiculo":       {},   # resultados separados por vehiculo
        "recorridos":         []    # detalle de cada recorrido
    }

    # Inicializar contadores por vehiculo
    for vehiculo in lista_vehiculos:
        estadisticas["por_vehiculo"][vehiculo["nombre"]] = {
            "recargas":  0,
            "km_total":  0.0
        }

    print("Iniciando simulacion:", n_recorridos, "recorridos con",
          len(lista_vehiculos), "vehiculos")

    # Hora de inicio simulada (para los timestamps del historial)
    hora_inicio = datetime.now().replace(hour=7, minute=0, second=0)

    # ── BUCLE PRINCIPAL controlado por centinela ──────────────
    # El centinela es la variable i: el bucle corre hasta que
    # i llegue a n_recorridos
    i = 0
    while i < n_recorridos:

        # Elegir origen y destino distintos al azar
        origen  = random.choice(lista_nodos_ref)
        destinos_posibles = []
        for nodo in lista_nodos_ref:
            if nodo != origen:
                destinos_posibles.append(nodo)

        if len(destinos_posibles) == 0:
            i = i + 1
            continue

        destino = random.choice(destinos_posibles)

        # Seleccionar vehiculo de forma rotatoria (0,1,0,1,...)
        vehiculo = lista_vehiculos[i % len(lista_vehiculos)]
        nivel_bateria = BATERIA_INICIAL

        # Timestamp simulado para este recorrido
        hora_recorrido = hora_inicio + timedelta(hours=i * 2)

        # Calcular ruta del recorrido
        ruta, distancia_m, _ = dijkstra(grafo, origen, destino)

        # Si no existe ruta, saltar este recorrido
        if len(ruta) == 0 or distancia_m == float("inf"):
            i = i + 1
            continue

        # Descontar bateria segun distancia recorrida
        consumo_pct = calcular_consumo(
            distancia_m,
            vehiculo["consumo_kwh_100km"],
            vehiculo["bateria_kwh"]
        )
        nivel_bateria = nivel_bateria - consumo_pct
        if nivel_bateria < 0.0:
            nivel_bateria = 0.0

        # Sumar km al contador del vehiculo
        estadisticas["por_vehiculo"][vehiculo["nombre"]]["km_total"] += (
            distancia_m / METROS_POR_KM
        )

        # Construir historial de nodos visitados
        historial_ruta = trazar_historial_ruta(grafo, ruta)

        # Guardar datos de este recorrido
        detalle = {
            "recorrido_num":    i + 1,
            "vehiculo":         vehiculo["nombre"],
            "origen_osm":       origen,
            "destino_osm":      destino,
            "origen_nombre":    obtener_nombre_nodo(grafo, origen),
            "destino_nombre":   obtener_nombre_nodo(grafo, destino),
            "distancia_km":     round(distancia_m / METROS_POR_KM, 3),
            "bateria_final_pct": round(nivel_bateria, 2),
            "recarga_activada": False,
            "historial_ruta":   historial_ruta
        }

        # ── ACTIVAR BUSQUEDA DE ELECTROLINERA ─────────────────
        if necesita_recarga(nivel_bateria):

            nodo_actual = ruta[-1]  # ultimo nodo de la ruta

            id_electro, nodo_electro, ruta_carga, dist_carga, _ = \
                electrolinera_mas_cercana(grafo, nodo_actual, nodos_electro)

            if id_electro is not None:
                nombre_electro = obtener_nombre_nodo(grafo, nodo_electro)

                # Registrar el evento de recarga en el CSV
                evento = {
                    "timestamp":             hora_recorrido.strftime("%Y-%m-%d %H:%M:%S"),
                    "vehiculo_id":           vehiculo["id"],
                    "vehiculo_nombre":       vehiculo["nombre"],
                    "electrolinera_id":      id_electro,
                    "electrolinera_nombre":  nombre_electro,
                    "nodo_origen":           nodo_actual,
                    "nivel_bateria_llegada": round(nivel_bateria, 2),
                    "distancia_metros":      round(dist_carga, 1)
                }
                registrar_recarga(evento)

                # Recargar hasta el 80%
                nivel_bateria = 80.0

                # Actualizar estadisticas
                estadisticas["total_recargas"] += 1
                estadisticas["por_vehiculo"][vehiculo["nombre"]]["recargas"] += 1

                if nombre_electro in estadisticas["uso_electrolineras"]:
                    estadisticas["uso_electrolineras"][nombre_electro] += 1
                else:
                    estadisticas["uso_electrolineras"][nombre_electro] = 1

                # Agregar datos de la recarga al detalle del recorrido
                detalle["recarga_activada"]       = True
                detalle["electrolinera_usada"]    = nombre_electro
                detalle["distancia_a_electro_km"] = round(dist_carga / METROS_POR_KM, 3)

        estadisticas["recorridos"].append(detalle)
        estadisticas["total_recorridos"] += 1
        i = i + 1

    # Guardar estadisticas en JSON
    guardar_estadisticas(estadisticas)

    # Generar el reporte TXT detallado
    ruta_reporte = generar_reporte_txt(estadisticas)

    # Mostrar solo el mensaje final en la terminal
    print("")
    print("-" * 55)
    print("Simulacion completada.")
    print("  Recorridos : " + str(estadisticas["total_recorridos"]))
    print("  Recargas   : " + str(estadisticas["total_recargas"]))
    print("-" * 55)
    print("Reporte detallado generado con exito en:")
    print(ruta_reporte)
    print("-" * 55)

    return estadisticas


def imprimir_resumen(estadisticas):
    """
    Muestra un resumen corto de la simulacion en la terminal.
    El detalle completo esta en el archivo reporte_simulacion.txt
    """
    if len(estadisticas) == 0:
        print("No hay estadisticas para mostrar.")
        return

    print("")
    print("=" * 60)
    print("  RESUMEN DE SIMULACION")
    print("=" * 60)
    print("  Total recorridos :", estadisticas["total_recorridos"])
    print("  Total recargas   :", estadisticas["total_recargas"])

    print("")
    print("  Electrolineras mas usadas:")
    uso = estadisticas.get("uso_electrolineras", {})
    if len(uso) > 0:
        ordenado = sorted(uso.items(), key=lambda x: x[1], reverse=True)
        for nombre, conteo in ordenado:
            print("    " + nombre + " : " + str(conteo) + " recargas")
    else:
        print("    (ninguna recarga en esta simulacion)")

    print("")
    print("  Por vehiculo:")
    for nombre, datos in estadisticas.get("por_vehiculo", {}).items():
        print("    " + nombre +
              " | Recargas: " + str(datos["recargas"]) +
              " | km: " + str(round(datos["km_total"], 1)))
    print("=" * 60)
