"""
constructor_grafo.py
--------------------
Construye el grafo ponderado de la red vial de Bucaramanga
usando OSMnx + NetworkX.

Nodos especiales:
  - Tipo A: Electrolineras  (color rojo  en visualización)
  - Tipo B: Puntos de referencia (color azul en visualización)

Las aristas tienen como peso la distancia en metros ('length').
"""

import sys
import os

# Importaciones con manejo de error para entornos sin las librerías
try:
    import osmnx as ox
    import networkx as nx
    OSMNX_DISPONIBLE = True
except ImportError:
    OSMNX_DISPONIBLE = False

# Añadir ruta raíz al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from data.datos_estaticos import ELECTROLINERAS, PUNTOS_REFERENCIA


# ─────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────
CIUDAD = "Bucaramanga, Santander, Colombia"
RADIO_METROS = 15000  # Radio de extracción de la red vial


# ─────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL: CONSTRUIR GRAFO
# ─────────────────────────────────────────────────────────────
def construir_grafo(desde_cache: bool = True) -> "nx.MultiDiGraph":
    """
    Descarga (o carga desde caché) el grafo vial de Bucaramanga
    y agrega los nodos especiales de electrolineras y puntos de
    referencia como atributos sobre los nodos OSM más cercanos.

    Parámetros
    ----------
    desde_cache : bool
        Si True, intenta cargar el grafo guardado en disco.
        Si no existe caché, lo descarga de OpenStreetMap.

    Retorna
    -------
    nx.MultiDiGraph
        Grafo vial enriquecido con atributos de nodos especiales.
    """
    if not OSMNX_DISPONIBLE:
        print("  ⚠  OSMnx no está instalado. Usando grafo sintético de prueba.")
        return _grafo_sintetico()

    ruta_cache = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "raw", "grafo_bga.graphml"
    )

    if desde_cache and os.path.exists(ruta_cache):
        print("  ✓  Cargando grafo desde caché local...")
        G = ox.load_graphml(ruta_cache)
    else:
        print("  ↓  Descargando red vial de OpenStreetMap (puede tardar)...")
        G = ox.graph_from_place(CIUDAD, network_type="drive")
        ox.save_graphml(G, ruta_cache)
        print(f"  ✓  Grafo guardado en {ruta_cache}")

    print(f"  ✓  Grafo cargado: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")

    # Agregar atributos especiales a nodos OSM cercanos
    G = _etiquetar_nodos_especiales(G)
    return G


# ─────────────────────────────────────────────────────────────
# ETIQUETADO DE NODOS ESPECIALES
# ─────────────────────────────────────────────────────────────
def _etiquetar_nodos_especiales(G: "nx.MultiDiGraph") -> "nx.MultiDiGraph":
    """
    Encuentra el nodo OSM más cercano a cada electrolinera y punto
    de referencia, y agrega atributos al grafo.

    Atributos agregados:
        - tipo_especial : 'electrolinera' | 'referencia' | None
        - id_especial   : 'E1'...'E8' | 'P1'...'P10' | None
        - nombre_especial : nombre legible del lugar
    """
    # Inicializar todos los nodos como sin tipo especial
    for nodo in G.nodes:
        G.nodes[nodo]["tipo_especial"] = None
        G.nodes[nodo]["id_especial"] = None
        G.nodes[nodo]["nombre_especial"] = None

    todos_especiales = ELECTROLINERAS + PUNTOS_REFERENCIA

    for lugar in todos_especiales:
        nodo_cercano = ox.distance.nearest_nodes(G, lugar["lon"], lugar["lat"])
        G.nodes[nodo_cercano]["tipo_especial"] = lugar["tipo"]
        G.nodes[nodo_cercano]["id_especial"] = lugar["id"]
        G.nodes[nodo_cercano]["nombre_especial"] = lugar["nombre"]

    n_electro = sum(
        1 for n, d in G.nodes(data=True) if d.get("tipo_especial") == "electrolinera"
    )
    n_ref = sum(
        1 for n, d in G.nodes(data=True) if d.get("tipo_especial") == "referencia"
    )
    print(f"  ✓  Electrolineras mapeadas: {n_electro} | Puntos de referencia: {n_ref}")

    return G


# ─────────────────────────────────────────────────────────────
# CONSULTAS SOBRE EL GRAFO
# ─────────────────────────────────────────────────────────────
def obtener_nodos_electrolineras(G: "nx.MultiDiGraph") -> dict:
    """
    Retorna diccionario {id_especial: nodo_osm} de electrolineras.

    Retorna
    -------
    dict
        {'E1': 123456789, 'E2': 987654321, ...}
    """
    return {
        d["id_especial"]: n
        for n, d in G.nodes(data=True)
        if d.get("tipo_especial") == "electrolinera"
    }


def obtener_nodos_referencia(G: "nx.MultiDiGraph") -> dict:
    """
    Retorna diccionario {id_especial: nodo_osm} de puntos de referencia.
    """
    return {
        d["id_especial"]: n
        for n, d in G.nodes(data=True)
        if d.get("tipo_especial") == "referencia"
    }


def obtener_nombre_nodo(G: "nx.MultiDiGraph", nodo_osm: int) -> str:
    """Retorna el nombre especial de un nodo, o su ID OSM como string."""
    nombre = G.nodes[nodo_osm].get("nombre_especial")
    return nombre if nombre else str(nodo_osm)


# ─────────────────────────────────────────────────────────────
# GRAFO SINTÉTICO (fallback si OSMnx no está disponible)
# ─────────────────────────────────────────────────────────────
def _grafo_sintetico() -> "nx.MultiDiGraph":
    """
    Crea un grafo sintético pequeño para pruebas sin conexión.
    Los nodos representan ubicaciones simplificadas.
    """
    import networkx as nx
    import random

    G = nx.MultiDiGraph()
    nodos = list(range(1, 20))

    for n in nodos:
        G.add_node(n, tipo_especial=None, id_especial=None, nombre_especial=None)

    # Conectar nodos con distancias aleatorias entre 500 y 5000 m
    for i in nodos:
        for j in nodos:
            if i != j and random.random() < 0.3:
                dist = random.randint(500, 5000)
                G.add_edge(i, j, length=dist)
                G.add_edge(j, i, length=dist)

    # Asignar electrolineras a nodos 1-8
    for idx, e in enumerate(ELECTROLINERAS):
        nodo = idx + 1
        G.nodes[nodo]["tipo_especial"] = "electrolinera"
        G.nodes[nodo]["id_especial"] = e["id"]
        G.nodes[nodo]["nombre_especial"] = e["nombre"]

    # Asignar puntos de referencia a nodos 9-18
    for idx, p in enumerate(PUNTOS_REFERENCIA):
        nodo = idx + 9
        G.nodes[nodo]["tipo_especial"] = "referencia"
        G.nodes[nodo]["id_especial"] = p["id"]
        G.nodes[nodo]["nombre_especial"] = p["nombre"]

    print(f"  ✓  Grafo sintético creado: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")
    return G
