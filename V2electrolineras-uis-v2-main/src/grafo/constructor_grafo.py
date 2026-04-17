"""
Construccion del grafo vial y etiquetado de nodos especiales.
"""

import os
import sys

try:
    import osmnx as ox
    import networkx as nx
    OSMNX_DISPONIBLE = True
except ImportError:
    OSMNX_DISPONIBLE = False

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from data.datos_estaticos import ELECTROLINERAS, PUNTOS_REFERENCIA


CIUDAD = "Bucaramanga, Santander, Colombia"


def construir_grafo(desde_cache=True):
    if not OSMNX_DISPONIBLE:
        print("OSMnx no esta instalado. Se usara un grafo sintetico.")
        return _grafo_sintetico()

    ruta_cache = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "grafo_bga.graphml")
    )

    if desde_cache and os.path.exists(ruta_cache):
        print("Cargando grafo desde cache local...")
        grafo = ox.load_graphml(ruta_cache)
    else:
        print("Descargando red vial de OpenStreetMap (puede tardar)...")
        grafo = ox.graph_from_place(CIUDAD, network_type="drive")
        ox.save_graphml(grafo, ruta_cache)
        print("Grafo guardado en", ruta_cache)

    print(
        "Grafo cargado:",
        grafo.number_of_nodes(),
        "nodos,",
        grafo.number_of_edges(),
        "aristas",
    )

    return _etiquetar_nodos_especiales(grafo)


def _inicializar_nodos_especiales(grafo):
    for nodo in grafo.nodes:
        grafo.nodes[nodo]["tipo_especial"] = None
        grafo.nodes[nodo]["id_especial"] = None
        grafo.nodes[nodo]["nombre_especial"] = None


def _distancia_cuadrada(lat1, lon1, lat2, lon2):
    return ((lat1 - lat2) ** 2) + ((lon1 - lon2) ** 2)


def _buscar_nodo_disponible_mas_cercano(grafo, latitud, longitud, nodos_ocupados):
    mejor_nodo = None
    mejor_distancia = None

    for nodo, datos in grafo.nodes(data=True):
        if nodo in nodos_ocupados:
            continue

        latitud_nodo = datos.get("y")
        longitud_nodo = datos.get("x")

        if latitud_nodo is None or longitud_nodo is None:
            continue

        distancia = _distancia_cuadrada(latitud, longitud, latitud_nodo, longitud_nodo)

        if mejor_nodo is None or distancia < mejor_distancia:
            mejor_nodo = nodo
            mejor_distancia = distancia

    return mejor_nodo


def _asignar_lugar(grafo, nodo, lugar):
    grafo.nodes[nodo]["tipo_especial"] = lugar["tipo"]
    grafo.nodes[nodo]["id_especial"] = lugar["id"]
    grafo.nodes[nodo]["nombre_especial"] = lugar["nombre"]


def _etiquetar_nodos_especiales(grafo):
    _inicializar_nodos_especiales(grafo)

    nodos_ocupados = set()
    lugares = ELECTROLINERAS + PUNTOS_REFERENCIA

    i = 0
    while i < len(lugares):
        lugar = lugares[i]
        nodo_cercano = _buscar_nodo_disponible_mas_cercano(
            grafo,
            lugar["lat"],
            lugar["lon"],
            nodos_ocupados,
        )

        if nodo_cercano is not None:
            _asignar_lugar(grafo, nodo_cercano, lugar)
            nodos_ocupados.add(nodo_cercano)

        i = i + 1

    total_electrolineras = 0
    total_referencias = 0

    for _, datos in grafo.nodes(data=True):
        if datos.get("tipo_especial") == "electrolinera":
            total_electrolineras = total_electrolineras + 1
        elif datos.get("tipo_especial") == "referencia":
            total_referencias = total_referencias + 1

    print(
        "Electrolineras mapeadas:",
        total_electrolineras,
        "| Puntos de referencia:",
        total_referencias,
    )

    return grafo


def obtener_nodos_electrolineras(grafo):
    resultado = {}

    for nodo, datos in grafo.nodes(data=True):
        if datos.get("tipo_especial") == "electrolinera":
            resultado[datos["id_especial"]] = nodo

    return resultado


def obtener_nodos_referencia(grafo):
    resultado = {}

    for nodo, datos in grafo.nodes(data=True):
        if datos.get("tipo_especial") == "referencia":
            resultado[datos["id_especial"]] = nodo

    return resultado


def obtener_nombre_nodo(grafo, nodo_osm):
    nombre = grafo.nodes[nodo_osm].get("nombre_especial")
    if nombre:
        return nombre
    return str(nodo_osm)


def _grafo_sintetico():
    import networkx as nx
    import random

    grafo = nx.MultiDiGraph()
    nodos = list(range(1, 20))

    for nodo in nodos:
        grafo.add_node(nodo, tipo_especial=None, id_especial=None, nombre_especial=None)

    for origen in nodos:
        for destino in nodos:
            if origen != destino and random.random() < 0.3:
                distancia = random.randint(500, 5000)
                grafo.add_edge(origen, destino, length=distancia)
                grafo.add_edge(destino, origen, length=distancia)

    i = 0
    while i < len(ELECTROLINERAS):
        nodo = i + 1
        _asignar_lugar(grafo, nodo, ELECTROLINERAS[i])
        i = i + 1

    i = 0
    while i < len(PUNTOS_REFERENCIA):
        nodo = i + 9
        _asignar_lugar(grafo, nodo, PUNTOS_REFERENCIA[i])
        i = i + 1

    print(
        "Grafo sintetico creado:",
        grafo.number_of_nodes(),
        "nodos,",
        grafo.number_of_edges(),
        "aristas",
    )
    return grafo
