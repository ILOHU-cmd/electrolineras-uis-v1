"""
algoritmos_grafo.py
Implementacion de los algoritmos de camino mas corto.

Dijkstra: encuentra la ruta mas corta entre dos nodos del grafo.
Funciona como un explorador que siempre elige el camino menos
costoso primero, usando una cola de prioridad (heap).

Floyd-Warshall: calcula todas las rutas mas cortas entre todos
los pares de nodos. Es mas lento pero util para analisis globales.
Solo se usa en grafos pequenos.
"""

import time

try:
    import networkx as nx
    NX_DISPONIBLE = True
except ImportError:
    NX_DISPONIBLE = False


def dijkstra(grafo, nodo_origen, nodo_destino):
    """
    Calcula la ruta mas corta entre dos nodos usando el algoritmo de Dijkstra.
    Usa NetworkX internamente cuando esta disponible.

    Devuelve una tupla con tres valores:
    - ruta      : lista de nodos en orden, desde origen hasta destino
    - distancia : distancia total en metros
    - tiempo_ms : cuanto tardo el calculo en milisegundos
    """
    if not NX_DISPONIBLE:
        # Si no hay NetworkX, usar la version manual
        return dijkstra_manual(grafo, nodo_origen, nodo_destino)

    inicio = time.perf_counter()

    try:
        ruta = nx.shortest_path(grafo, nodo_origen, nodo_destino, weight="length")
        distancia = nx.shortest_path_length(grafo, nodo_origen, nodo_destino, weight="length")
    except nx.NetworkXNoPath:
        # No existe camino entre los dos nodos
        ruta = []
        distancia = float("inf")
    except nx.NodeNotFound:
        # Uno de los nodos no existe en el grafo
        ruta = []
        distancia = float("inf")

    tiempo_ms = (time.perf_counter() - inicio) * 1000
    return ruta, distancia, tiempo_ms


def electrolinera_mas_cercana(grafo, nodo_actual, nodos_electrolineras):
    """
    Encuentra la electrolinera mas cercana al nodo actual.
    Aplica Dijkstra desde el nodo actual hacia cada electrolinera
    y se queda con la de menor distancia.

    nodos_electrolineras es un diccionario como: {"E1": 123456, "E2": 654321}

    Devuelve:
    - id_electrolinera : identificador como "E3"
    - nodo_electrolinera : numero de nodo OSM
    - ruta              : lista de nodos del camino
    - distancia         : metros hasta esa electrolinera
    - tiempo_ms         : tiempo total de todos los Dijkstra ejecutados
    """
    mejor_id         = None
    mejor_nodo       = None
    mejor_ruta       = []
    mejor_distancia  = float("inf")
    tiempo_total     = 0.0

    for id_electro, nodo_electro in nodos_electrolineras.items():
        # Caso especial: ya estamos en la electrolinera
        if nodo_electro == nodo_actual:
            return id_electro, nodo_electro, [nodo_actual], 0.0, 0.0

        ruta, distancia, tiempo_ms = dijkstra(grafo, nodo_actual, nodo_electro)
        tiempo_total = tiempo_total + tiempo_ms

        if distancia < mejor_distancia:
            mejor_distancia = distancia
            mejor_id        = id_electro
            mejor_nodo      = nodo_electro
            mejor_ruta      = ruta

    return mejor_id, mejor_nodo, mejor_ruta, mejor_distancia, tiempo_total


def floyd_warshall(grafo):
    """
    Calcula las rutas mas cortas entre todos los pares de nodos.
    ADVERTENCIA: es muy lento en grafos grandes. Solo usar con el
    grafo sintetico de prueba o subgrafos pequenos.

    Devuelve un diccionario con las distancias y el tiempo que tardo.
    """
    if not NX_DISPONIBLE:
        print("NetworkX no esta disponible para Floyd-Warshall.")
        return {}, 0.0

    print("Ejecutando Floyd-Warshall... esto puede tardar.")
    inicio = time.perf_counter()

    try:
        # all_pairs_dijkstra_path_length es la implementacion eficiente en NetworkX
        distancias = dict(nx.all_pairs_dijkstra_path_length(grafo, weight="length"))
    except Exception as error:
        print("Error al ejecutar Floyd-Warshall:", error)
        distancias = {}

    tiempo_ms = (time.perf_counter() - inicio) * 1000
    print("Floyd-Warshall completado en", round(tiempo_ms, 1), "ms")
    return distancias, tiempo_ms


def dijkstra_manual(grafo, nodo_origen, nodo_destino):
    """
    Implementacion del algoritmo de Dijkstra sin usar NetworkX.
    Se usa como respaldo cuando NetworkX no esta instalado.

    Pasos del algoritmo:
    1. Asignar distancia infinita a todos los nodos
    2. La distancia al origen es 0
    3. Usar un heap (cola de prioridad) para siempre procesar el nodo mas cercano
    4. Para cada vecino, calcular si la nueva ruta es mas corta
    5. Reconstruir la ruta al final siguiendo los nodos previos
    """
    import heapq

    inicio = time.perf_counter()

    # Inicializar distancias
    distancias = {}
    for nodo in grafo.nodes:
        distancias[nodo] = float("inf")
    distancias[nodo_origen] = 0

    # Guardar el nodo anterior en la ruta optima
    previo = {}
    for nodo in grafo.nodes:
        previo[nodo] = None

    # Cola de prioridad: (distancia, nodo)
    heap = [(0, nodo_origen)]

    while len(heap) > 0:
        distancia_actual, nodo_actual = heapq.heappop(heap)

        # Si ya llegamos al destino podemos parar
        if nodo_actual == nodo_destino:
            break

        # Ignorar si ya encontramos una ruta mejor antes
        if distancia_actual > distancias[nodo_actual]:
            continue

        # Revisar todos los vecinos del nodo actual
        for vecino in grafo.successors(nodo_actual):
            # Obtener el peso de la arista (puede haber varias, tomar la menor)
            aristas = grafo.get_edge_data(nodo_actual, vecino)
            peso_minimo = float("inf")
            for datos_arista in aristas.values():
                peso = datos_arista.get("length", float("inf"))
                if peso < peso_minimo:
                    peso_minimo = peso

            nueva_distancia = distancia_actual + peso_minimo

            if nueva_distancia < distancias[vecino]:
                distancias[vecino] = nueva_distancia
                previo[vecino] = nodo_actual
                heapq.heappush(heap, (nueva_distancia, vecino))

    # Reconstruir la ruta desde el destino hasta el origen
    ruta = []
    nodo_actual = nodo_destino
    while nodo_actual is not None:
        ruta.append(nodo_actual)
        nodo_actual = previo[nodo_actual]
    ruta.reverse()

    # Si la ruta no empieza en el origen, no existe camino
    if len(ruta) == 0 or ruta[0] != nodo_origen:
        ruta = []
        distancias[nodo_destino] = float("inf")

    tiempo_ms = (time.perf_counter() - inicio) * 1000
    return ruta, distancias[nodo_destino], tiempo_ms
