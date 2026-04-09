"""
simulacion.py
-------------
Módulo de simulación de recorridos de vehículos eléctricos.

Lógica principal:
  1. Seleccionar n recorridos aleatorios entre puntos de referencia.
  2. Descontar batería según distancia recorrida y consumo del vehículo.
  3. Cuando batería ∈ [10%, 20%], buscar electrolinera más cercana.
  4. Calcular ruta Dijkstra hacia esa electrolinera.
  5. Registrar el evento de recarga en archivos CSV/JSON.
"""

import random
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.grafo.algoritmos_grafo import dijkstra, electrolinera_mas_cercana
from src.grafo.constructor_grafo import obtener_nodos_electrolineras, obtener_nodos_referencia, obtener_nombre_nodo
from src.utils.archivos import registrar_recarga, exportar_estadisticas_json
from data.datos_estaticos import VEHICULOS


# ─────────────────────────────────────────────────────────────
# CONSTANTES DE SIMULACIÓN
# ─────────────────────────────────────────────────────────────
UMBRAL_RECARGA_MIN = 10.0   # % batería mínimo para buscar recarga
UMBRAL_RECARGA_MAX = 20.0   # % batería máximo que activa búsqueda
BATERIA_INICIAL = 100.0     # % con que inicia cada recorrido
METROS_POR_KM = 1000.0


# ─────────────────────────────────────────────────────────────
# CLASE VEHÍCULO (encapsula estado de batería)
# ─────────────────────────────────────────────────────────────
class Vehiculo:
    """Representa un vehículo eléctrico durante la simulación."""

    def __init__(self, datos: dict):
        self.id = datos["id"]
        self.nombre = datos["nombre"]
        self.gama = datos["gama"]
        self.bateria_kwh = datos["bateria_kwh"]
        self.autonomia_km = datos["autonomia_real_km"]
        self.consumo_kwh_100km = datos["consumo_kwh_100km"]

        self.nivel_bateria = BATERIA_INICIAL  # porcentaje actual
        self.total_recargas = 0
        self.historial_recargas = []          # lista de eventos

    @property
    def bateria_actual_kwh(self) -> float:
        return (self.nivel_bateria / 100.0) * self.bateria_kwh

    def consumir(self, distancia_m: float) -> None:
        """Descuenta batería según distancia recorrida."""
        distancia_km = distancia_m / METROS_POR_KM
        kwh_consumidos = (self.consumo_kwh_100km / 100.0) * distancia_km
        kwh_consumidos_pct = (kwh_consumidos / self.bateria_kwh) * 100.0
        self.nivel_bateria = max(0.0, self.nivel_bateria - kwh_consumidos_pct)

    def recargar(self, hasta_pct: float = 80.0) -> None:
        """Recarga la batería hasta un porcentaje dado (default 80%)."""
        self.nivel_bateria = min(100.0, hasta_pct)
        self.total_recargas += 1

    def necesita_recarga(self) -> bool:
        """Retorna True si el nivel está en el umbral de recarga."""
        return UMBRAL_RECARGA_MIN <= self.nivel_bateria <= UMBRAL_RECARGA_MAX

    def bateria_critica(self) -> bool:
        """Retorna True si la batería está por debajo del umbral mínimo."""
        return self.nivel_bateria < UMBRAL_RECARGA_MIN

    def __str__(self):
        return (f"{self.nombre} [{self.gama.upper()}] | "
                f"Batería: {self.nivel_bateria:.1f}% | "
                f"Recargas: {self.total_recargas}")


# ─────────────────────────────────────────────────────────────
# SIMULACIÓN PRINCIPAL
# ─────────────────────────────────────────────────────────────
def ejecutar_simulacion(G, n_recorridos: int = 20,
                        ids_vehiculos: list = None,
                        semilla: int = None) -> dict:
    """
    Ejecuta la simulación completa de recorridos.

    Parámetros
    ----------
    G : nx.MultiDiGraph
        Grafo vial con nodos etiquetados.
    n_recorridos : int
        Número de recorridos aleatorios a simular.
    ids_vehiculos : list[str]
        Claves de VEHICULOS a incluir (default: todos).
    semilla : int
        Semilla aleatoria para reproducibilidad.

    Retorna
    -------
    dict
        Estadísticas completas de la simulación.
    """
    if semilla is not None:
        random.seed(semilla)

    if ids_vehiculos is None:
        ids_vehiculos = list(VEHICULOS.keys())

    # Obtener nodos OSM de electrolineras y puntos de referencia
    nodos_electro = obtener_nodos_electrolineras(G)
    nodos_ref = obtener_nodos_referencia(G)

    if not nodos_electro:
        print("  ⚠  No se encontraron electrolineras en el grafo.")
        return {}

    if not nodos_ref:
        print("  ⚠  No se encontraron puntos de referencia en el grafo.")
        return {}

    lista_nodos_ref = list(nodos_ref.values())

    # Crear instancias de vehículos
    vehiculos = [Vehiculo(VEHICULOS[k]) for k in ids_vehiculos if k in VEHICULOS]
    if not vehiculos:
        print("  ⚠  No se encontraron vehículos válidos.")
        return {}

    print(f"\n  🚗 Iniciando simulación: {n_recorridos} recorridos | "
          f"{len(vehiculos)} vehículo(s)")

    # Timestamp base de simulación (empezamos en 07:00 del día actual)
    ts_base = datetime.now().replace(hour=7, minute=0, second=0, microsecond=0)

    estadisticas = {
        "total_recorridos": 0,
        "total_recargas": 0,
        "uso_electrolineras": {},   # {nombre: conteo}
        "por_vehiculo": {},         # {nombre_vehiculo: {recargas, km_total}}
        "recorridos": [],           # detalle de cada recorrido
    }

    for vid, v in enumerate(vehiculos):
        estadisticas["por_vehiculo"][v.nombre] = {"recargas": 0, "km_total": 0.0}

    # ─── BUCLE PRINCIPAL (controlado por centinela: i < n_recorridos) ───
    i = 0
    while i < n_recorridos:
        # Seleccionar origen y destino aleatorios distintos
        origen = random.choice(lista_nodos_ref)
        destino_candidatos = [n for n in lista_nodos_ref if n != origen]
        if not destino_candidatos:
            i += 1
            continue
        destino = random.choice(destino_candidatos)

        # Seleccionar vehículo (rotación circular)
        vehiculo = vehiculos[i % len(vehiculos)]
        """vehiculo.nivel_bateria = BATERIA_INICIAL  # reiniciar batería"""

        ts_actual = ts_base + timedelta(hours=i * 2)  # timestamp simulado

        # Calcular ruta origen→destino
        ruta, distancia_m, _ = dijkstra(G, origen, destino)

        if not ruta or distancia_m == float("inf"):
            i += 1
            continue

        # Consumir batería del recorrido
        vehiculo.consumir(distancia_m)
        estadisticas["por_vehiculo"][vehiculo.nombre]["km_total"] += (
            distancia_m / METROS_POR_KM
        )

        detalle_recorrido = {
            "recorrido_num": i + 1,
            "vehiculo": vehiculo.nombre,
            "origen_osm": origen,
            "destino_osm": destino,
            "origen_nombre": obtener_nombre_nodo(G, origen),
            "destino_nombre": obtener_nombre_nodo(G, destino),
            "distancia_km": round(distancia_m / METROS_POR_KM, 3),
            "bateria_final_pct": round(vehiculo.nivel_bateria, 2),
            "recarga_activada": False,
        }

        # ─── ACTIVAR BÚSQUEDA DE ELECTROLINERA ───
        if vehiculo.necesita_recarga() or vehiculo.bateria_critica():
            nodo_actual = ruta[-1]  # nodo donde quedó el vehículo

            id_electro, nodo_electro, ruta_carga, dist_carga, t_ms = \
                electrolinera_mas_cercana(G, nodo_actual, nodos_electro)

            if id_electro:
                nombre_electro = obtener_nombre_nodo(G, nodo_electro)

                # Registrar evento
                evento = {
                    "timestamp": ts_actual.strftime("%Y-%m-%d %H:%M:%S"),
                    "vehiculo_id": vehiculo.id,
                    "vehiculo_nombre": vehiculo.nombre,
                    "electrolinera_id": id_electro,
                    "electrolinera_nombre": nombre_electro,
                    "nodo_origen_osm": nodo_actual,
                    "nivel_bateria_llegada": round(vehiculo.nivel_bateria, 2),
                    "distancia_recorrida_m": round(dist_carga, 1),
                }
                registrar_recarga(evento)

                # Actualizar contadores
                vehiculo.recargar(hasta_pct=80.0)
                estadisticas["total_recargas"] += 1
                estadisticas["por_vehiculo"][vehiculo.nombre]["recargas"] += 1
                estadisticas["uso_electrolineras"][nombre_electro] = (
                    estadisticas["uso_electrolineras"].get(nombre_electro, 0) + 1
                )

                detalle_recorrido["recarga_activada"] = True
                detalle_recorrido["electrolinera_usada"] = nombre_electro
                detalle_recorrido["distancia_a_electro_km"] = round(
                    dist_carga / METROS_POR_KM, 3
                )

        estadisticas["recorridos"].append(detalle_recorrido)
        estadisticas["total_recorridos"] += 1
        i += 1

    # Guardar estadísticas
    exportar_estadisticas_json(estadisticas)

    print(f"\n  ✓  Simulación completada:")
    print(f"     Recorridos: {estadisticas['total_recorridos']}")
    print(f"     Recargas:   {estadisticas['total_recargas']}")

    return estadisticas


# ─────────────────────────────────────────────────────────────
# RESUMEN ESTADÍSTICO EN CONSOLA
# ─────────────────────────────────────────────────────────────
def imprimir_resumen(estadisticas: dict) -> None:
    """Imprime un resumen legible de la simulación en consola."""
    if not estadisticas:
        print("  ⚠  No hay estadísticas para mostrar.")
        return

    print("\n" + "=" * 60)
    print("  RESUMEN DE SIMULACIÓN")
    print("=" * 60)
    print(f"  Total recorridos : {estadisticas['total_recorridos']}")
    print(f"  Total recargas   : {estadisticas['total_recargas']}")

    print("\n  Uso de electrolineras:")
    electros = estadisticas.get("uso_electrolineras", {})
    if electros:
        for nombre, conteo in sorted(electros.items(), key=lambda x: -x[1]):
            print(f"    {nombre:<45} → {conteo} recargas")
    else:
        print("    (ninguna recarga registrada)")

    print("\n  Por vehículo:")
    for nombre, datos in estadisticas.get("por_vehiculo", {}).items():
        print(f"    {nombre:<30} | Recargas: {datos['recargas']:>3} | "
              f"km totales: {datos['km_total']:>8.1f}")
    print("=" * 60)
