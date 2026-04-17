"""
algoritmos_grafo.py
-------------------
Implementación de algoritmos de caminos más cortos:
  1. Dijkstra    → ruta individual (uso principal en simulación)
  2. Floyd-Warshall → todas las rutas (uso en análisis completo)

Se usa NetworkX internamente, pero las funciones están
encapsuladas para facilitar comparación con modelo de ML.
"""

import sys
import os
import time

try:
    import networkx as nx
    NX_DISPONIBLE = True
except ImportError:
    NX_DISPONIBLE = False


# ─────────────────────────────────────────────────────────────
# DIJKSTRA: RUTA MÁS CORTA ENTRE DOS NODOS
# ─────────────────────────────────────────────────────────────
def dijkstra(G: "nx.MultiDiGraph", origen: int, destino: int,
             peso: str = "length") -> tuple:
    """
    Calcula la ruta más corta entre origen y destino usando Dijkstra.

    Parámetros
    ----------
    G : nx.MultiDiGraph
        Grafo de la red vial.
    origen : int
        Nodo OSM de partida.
    destino : int
        Nodo OSM de llegada.
    peso : str
        Atributo de arista a minimizar (default: 'length' en metros).

    Retorna
    -------
    tuple (ruta: list[int], distancia_m: float, tiempo_ms: float)
        ruta          → lista de nodos OSM en orden de recorrido.
        distancia_m   → distancia total en metros.
        tiempo_ms     → tiempo de cómputo en milisegundos.
        Si no existe ruta, retorna ([], float('inf'), tiempo_ms).
    """
    if not NX_DISPONIBLE:
        return _dijkstra_manual(G, origen, destino)

    t_inicio = time.perf_counter()
    try:
        ruta = nx.shortest_path(G, origen, destino, weight=peso)
        distancia = nx.shortest_path_length(G, origen, destino, weight=peso)
    except nx.NetworkXNoPath:
        ruta = []
        distancia = float("inf")
    except nx.NodeNotFound as e:
        print(f"  ⚠  Nodo no encontrado: {e}")
        ruta = []
        distancia = float("inf")

    tiempo_ms = (time.perf_counter() - t_inicio) * 1000
    return ruta, distancia, tiempo_ms


# ─────────────────────────────────────────────────────────────
# ELECTROLINERA MÁS CERCANA DESDE UN NODO
# ─────────────────────────────────────────────────────────────
def electrolinera_mas_cercana(G: "nx.MultiDiGraph",
                               nodo_actual: int,
                               nodos_electrolineras: dict) -> tuple:
    """
    Encuentra la electrolinera más cercana desde nodo_actual
    evaluando Dijkstra contra cada electrolinera.

    Parámetros
    ----------
    G : nx.MultiDiGraph
        Grafo vial.
    nodo_actual : int
        Nodo OSM desde donde está el vehículo.
    nodos_electrolineras : dict
        {'E1': nodo_osm, 'E2': nodo_osm, ...}

    Retorna
    -------
    tuple (id_electrolinera: str, nodo_osm: int, ruta: list,
           distancia_m: float, tiempo_ms: float)
    """
    mejor_id = None
    mejor_nodo = None
    mejor_ruta = []
    mejor_dist = float("inf")
    tiempo_total = 0.0

    for id_electro, nodo_electro in nodos_electrolineras.items():
        if nodo_electro == nodo_actual:
            # Ya estamos en la electrolinera
            return id_electro, nodo_electro, [nodo_actual], 0.0, 0.0

        ruta, dist, t_ms = dijkstra(G, nodo_actual, nodo_electro)
        tiempo_total += t_ms

        if dist < mejor_dist:
            mejor_dist = dist
            mejor_id = id_electro
            mejor_nodo = nodo_electro
            mejor_ruta = ruta

    return mejor_id, mejor_nodo, mejor_ruta, mejor_dist, tiempo_total


# ─────────────────────────────────────────────────────────────
# FLOYD-WARSHALL: TODAS LAS RUTAS (análisis global)
# ─────────────────────────────────────────────────────────────
def floyd_warshall(G: "nx.MultiDiGraph", peso: str = "length") -> tuple:
    """
    Calcula todas las rutas más cortas entre todos los pares de nodos.
    ADVERTENCIA: O(n³) — solo usar en grafos pequeños o sintéticos.

    Retorna
    -------
    tuple (distancias: dict, tiempo_ms: float)
        distancias → {nodo_i: {nodo_j: distancia_metros}}
    """
    if not NX_DISPONIBLE:
        print("  ⚠  NetworkX no disponible para Floyd-Warshall.")
        return {}, 0.0

    print("  ⏳ Ejecutando Floyd-Warshall (puede tardar en grafos grandes)...")
    t_inicio = time.perf_counter()

    try:
        # NetworkX implementa Floyd-Warshall optimizado
        distancias = dict(nx.all_pairs_dijkstra_path_length(G, weight=peso))
    except Exception as e:
        print(f"  ⚠  Error en Floyd-Warshall: {e}")
        distancias = {}

    tiempo_ms = (time.perf_counter() - t_inicio) * 1000
    print(f"  ✓  Floyd-Warshall completado en {tiempo_ms:.1f} ms")
    return distancias, tiempo_ms


# ─────────────────────────────────────────────────────────────
# DIJKSTRA MANUAL (fallback sin NetworkX)
# ─────────────────────────────────────────────────────────────
def _dijkstra_manual(G, origen: int, destino: int) -> tuple:
    """
    Implementación manual de Dijkstra usando heap.
    Fallback para cuando NetworkX no está disponible.
    """
    import heapq
    t_inicio = time.perf_counter()

    distancias = {nodo: float("inf") for nodo in G.nodes}
    distancias[origen] = 0
    previo = {nodo: None for nodo in G.nodes}
    heap = [(0, origen)]

    while heap:
        dist_actual, nodo_actual = heapq.heappop(heap)

        if nodo_actual == destino:
            break

        if dist_actual > distancias[nodo_actual]:
            continue

        for vecino in G.successors(nodo_actual):
            # Tomar la arista con menor peso entre multi-aristas
            edges_data = G.get_edge_data(nodo_actual, vecino)
            peso_min = min(
                d.get("length", float("inf"))
                for d in edges_data.values()
            )
            nueva_dist = dist_actual + peso_min

            if nueva_dist < distancias[vecino]:
                distancias[vecino] = nueva_dist
                previo[vecino] = nodo_actual
                heapq.heappush(heap, (nueva_dist, vecino))

    # Reconstruir ruta
    ruta = []
    nodo = destino
    while nodo is not None:
        ruta.append(nodo)
        nodo = previo[nodo]
    ruta.reverse()

    if ruta[0] != origen:
        ruta = []
        distancias[destino] = float("inf")

    tiempo_ms = (time.perf_counter() - t_inicio) * 1000
    return ruta, distancias[destino], tiempo_ms
