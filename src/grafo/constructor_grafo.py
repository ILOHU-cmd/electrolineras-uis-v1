"""
constructor_grafo.py
Construye el grafo de la red vial de Bucaramanga usando OSMnx.

Un grafo es una estructura matematica formada por nodos (intersecciones)
y aristas (calles). Cada arista tiene un peso que en este caso es la
distancia en metros. Esto permite aplicar algoritmos como Dijkstra
para encontrar la ruta mas corta entre dos puntos.

Este archivo se encarga de:
1. Descargar la red vial desde OpenStreetMap (o cargarla desde cache)
2. Marcar cuales nodos son electrolineras y cuales son puntos de referencia
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from data.datos_estaticos import ELECTROLINERAS, PUNTOS_REFERENCIA

# Intentar importar las librerias necesarias
try:
    import osmnx as ox
    import networkx as nx
    LIBRERIAS_DISPONIBLES = True
except ImportError:
    LIBRERIAS_DISPONIBLES = False

# Nombre de la ciudad a descargar
NOMBRE_CIUDAD = "Bucaramanga, Santander, Colombia"

# Ruta donde se guarda el grafo descargado para no tener que
# descargarlo cada vez que se abre el programa
RUTA_CACHE = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "raw", "grafo_bga.graphml"
)

# Crear carpeta raw si no existe
carpeta_raw = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")
if not os.path.exists(carpeta_raw):
    os.makedirs(carpeta_raw)


def construir_grafo(desde_cache=True):
    """
    Descarga o carga el grafo vial de Bucaramanga.
    Si desde_cache es True y ya existe el archivo, lo carga desde disco.
    Si no existe o desde_cache es False, lo descarga de OpenStreetMap.
    """
    if not LIBRERIAS_DISPONIBLES:
        print("Las librerias osmnx y networkx no estan instaladas.")
        print("Usando grafo de prueba en su lugar.")
        return crear_grafo_sintetico()

    if desde_cache and os.path.exists(RUTA_CACHE):
        print("Cargando grafo desde archivo local...")
        grafo = ox.load_graphml(RUTA_CACHE)
    else:
        print("Descargando red vial desde OpenStreetMap...")
        print("Esto puede tardar unos minutos la primera vez.")
        grafo = ox.graph_from_place(NOMBRE_CIUDAD, network_type="drive")
        ox.save_graphml(grafo, RUTA_CACHE)
        print("Grafo guardado en disco para usos futuros.")

    print("Grafo cargado:", grafo.number_of_nodes(), "nodos,", grafo.number_of_edges(), "aristas")

    # Marcar los nodos especiales (electrolineras y puntos de referencia)
    grafo = marcar_nodos_especiales(grafo)
    return grafo


def marcar_nodos_especiales(grafo):
    """
    Busca el nodo OSM mas cercano a cada electrolinera y punto de referencia
    y les agrega una etiqueta para identificarlos en el grafo.
    """
    # Primero inicializar todos los nodos sin etiqueta especial
    for nodo in grafo.nodes:
        grafo.nodes[nodo]["tipo"] = None
        grafo.nodes[nodo]["id_lugar"] = None
        grafo.nodes[nodo]["nombre_lugar"] = None

    # Marcar electrolineras
    for lugar in ELECTROLINERAS:
        nodo_cercano = ox.distance.nearest_nodes(grafo, lugar["lon"], lugar["lat"])
        grafo.nodes[nodo_cercano]["tipo"] = "electrolinera"
        grafo.nodes[nodo_cercano]["id_lugar"] = lugar["id"]
        grafo.nodes[nodo_cercano]["nombre_lugar"] = lugar["nombre"]

    # Marcar puntos de referencia
    for lugar in PUNTOS_REFERENCIA:
        nodo_cercano = ox.distance.nearest_nodes(grafo, lugar["lon"], lugar["lat"])
        grafo.nodes[nodo_cercano]["tipo"] = "referencia"
        grafo.nodes[nodo_cercano]["id_lugar"] = lugar["id"]
        grafo.nodes[nodo_cercano]["nombre_lugar"] = lugar["nombre"]

    # Contar cuantos se marcaron
    total_electro = 0
    total_ref = 0
    for nodo, datos in grafo.nodes(data=True):
        if datos.get("tipo") == "electrolinera":
            total_electro = total_electro + 1
        elif datos.get("tipo") == "referencia":
            total_ref = total_ref + 1

    print("Electrolineras marcadas:", total_electro)
    print("Puntos de referencia marcados:", total_ref)
    return grafo


def obtener_nodos_electrolineras(grafo):
    """
    Recorre el grafo y devuelve un diccionario con los nodos
    que son electrolineras.
    Ejemplo de resultado: {"E1": 3245871012, "E2": 987654321}
    """
    resultado = {}
    for nodo, datos in grafo.nodes(data=True):
        if datos.get("tipo") == "electrolinera":
            resultado[datos["id_lugar"]] = nodo
    return resultado


def obtener_nodos_referencia(grafo):
    """
    Igual que la anterior pero para puntos de referencia.
    """
    resultado = {}
    for nodo, datos in grafo.nodes(data=True):
        if datos.get("tipo") == "referencia":
            resultado[datos["id_lugar"]] = nodo
    return resultado


def obtener_nombre_nodo(grafo, nodo):
    """
    Devuelve el nombre de un nodo especial.
    Si el nodo no tiene nombre, devuelve el numero de nodo como texto.
    """
    nombre = grafo.nodes[nodo].get("nombre_lugar", None)
    if nombre:
        return nombre
    return str(nodo)


def crear_grafo_sintetico():
    """
    Crea un grafo pequeño de prueba cuando OSMnx no esta disponible.
    Util para probar el programa sin conexion a internet.
    """
    import networkx as nx
    import random

    grafo = nx.MultiDiGraph()

    # Crear 20 nodos numerados del 1 al 20
    for i in range(1, 21):
        grafo.add_node(i, tipo=None, id_lugar=None, nombre_lugar=None)

    # Conectar los nodos con distancias aleatorias
    for i in range(1, 21):
        for j in range(1, 21):
            if i != j and random.random() < 0.3:
                distancia = random.randint(300, 4000)
                grafo.add_edge(i, j, length=distancia)
                grafo.add_edge(j, i, length=distancia)

    # Asignar las 8 electrolineras a los nodos 1 al 8
    for i, electrolinera in enumerate(ELECTROLINERAS):
        nodo = i + 1
        grafo.nodes[nodo]["tipo"] = "electrolinera"
        grafo.nodes[nodo]["id_lugar"] = electrolinera["id"]
        grafo.nodes[nodo]["nombre_lugar"] = electrolinera["nombre"]

    # Asignar los 10 puntos de referencia a los nodos 9 al 18
    for i, punto in enumerate(PUNTOS_REFERENCIA):
        nodo = i + 9
        grafo.nodes[nodo]["tipo"] = "referencia"
        grafo.nodes[nodo]["id_lugar"] = punto["id"]
        grafo.nodes[nodo]["nombre_lugar"] = punto["nombre"]

    print("Grafo sintetico creado:", grafo.number_of_nodes(), "nodos,", grafo.number_of_edges(), "aristas")
    return grafo
