"""
Modulo de simulacion de recorridos.
"""

import os
import random
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from data.datos_estaticos import VEHICULOS, formatear_nombre_vehiculo
from src.grafo.algoritmos_grafo import dijkstra, electrolinera_mas_cercana
from src.grafo.constructor_grafo import (
    obtener_nodos_electrolineras,
    obtener_nodos_referencia,
    obtener_nombre_nodo,
)
from src.utils.archivos import exportar_estadisticas_json, registrar_recarga


UMBRAL_RECARGA_MIN = 10.0
UMBRAL_RECARGA_MAX = 20.0
BATERIA_INICIAL = 100.0
METROS_POR_KM = 1000.0


class Vehiculo:
    def __init__(self, datos):
        self.id = datos["id"]
        self.nombre = datos["nombre"]
        self.gama = datos["gama"]
        self.nombre_mostrado = formatear_nombre_vehiculo(self.nombre, self.gama)
        self.bateria_kwh = datos["bateria_kwh"]
        self.autonomia_km = datos["autonomia_real_km"]
        self.consumo_kwh_100km = datos["consumo_kwh_100km"]
        self.nivel_bateria = BATERIA_INICIAL
        self.total_recargas = 0
        self.historial_recargas = []

    @property
    def bateria_actual_kwh(self):
        return (self.nivel_bateria / 100.0) * self.bateria_kwh

    def consumir(self, distancia_m):
        distancia_km = distancia_m / METROS_POR_KM
        kwh_consumidos = (self.consumo_kwh_100km / 100.0) * distancia_km
        porcentaje_consumido = (kwh_consumidos / self.bateria_kwh) * 100.0
        self.nivel_bateria = max(0.0, self.nivel_bateria - porcentaje_consumido)

    def recargar(self, hasta_pct=80.0):
        self.nivel_bateria = min(100.0, hasta_pct)
        self.total_recargas = self.total_recargas + 1

    def necesita_recarga(self):
        return UMBRAL_RECARGA_MIN <= self.nivel_bateria <= UMBRAL_RECARGA_MAX

    def bateria_critica(self):
        return self.nivel_bateria < UMBRAL_RECARGA_MIN

    def __str__(self):
        return (
            self.nombre_mostrado
            + " ["
            + self.gama.upper()
            + "] | Bateria: "
            + format(self.nivel_bateria, ".1f")
            + "% | Recargas: "
            + str(self.total_recargas)
        )


def ejecutar_simulacion(G, n_recorridos=20, ids_vehiculos=None, semilla=None):
    if semilla is not None:
        random.seed(semilla)

    if ids_vehiculos is None:
        ids_vehiculos = list(VEHICULOS.keys())

    nodos_electro = obtener_nodos_electrolineras(G)
    nodos_referencia = obtener_nodos_referencia(G)

    if not nodos_electro:
        print("No se encontraron electrolineras en el grafo.")
        return {}

    if not nodos_referencia:
        print("No se encontraron puntos de referencia en el grafo.")
        return {}

    lista_nodos_referencia = list(nodos_referencia.values())
    vehiculos = [Vehiculo(VEHICULOS[clave]) for clave in ids_vehiculos if clave in VEHICULOS]

    if not vehiculos:
        print("No se encontraron vehiculos validos.")
        return {}

    print()
    print(
        "Iniciando simulacion:",
        n_recorridos,
        "recorridos |",
        len(vehiculos),
        "vehiculo(s)",
    )

    tiempo_base = datetime.now().replace(hour=7, minute=0, second=0, microsecond=0)

    estadisticas = {
        "total_recorridos": 0,
        "total_recargas": 0,
        "uso_electrolineras": {},
        "por_vehiculo": {},
        "recorridos": [],
    }

    for vehiculo in vehiculos:
        estadisticas["por_vehiculo"][vehiculo.nombre_mostrado] = {
            "recargas": 0,
            "km_total": 0.0,
        }

    i = 0
    while i < n_recorridos:
        origen = random.choice(lista_nodos_referencia)
        destinos = [nodo for nodo in lista_nodos_referencia if nodo != origen]

        if not destinos:
            i = i + 1
            continue

        destino = random.choice(destinos)
        vehiculo = vehiculos[i % len(vehiculos)]
        tiempo_actual = tiempo_base + timedelta(hours=i * 2)

        ruta, distancia_m, _ = dijkstra(G, origen, destino)

        if not ruta or distancia_m == float("inf"):
            i = i + 1
            continue

        vehiculo.consumir(distancia_m)
        estadisticas["por_vehiculo"][vehiculo.nombre_mostrado]["km_total"] = (
            estadisticas["por_vehiculo"][vehiculo.nombre_mostrado]["km_total"]
            + (distancia_m / METROS_POR_KM)
        )

        detalle_recorrido = {
            "recorrido_num": i + 1,
            "vehiculo": vehiculo.nombre_mostrado,
            "origen_osm": origen,
            "destino_osm": destino,
            "origen_nombre": obtener_nombre_nodo(G, origen),
            "destino_nombre": obtener_nombre_nodo(G, destino),
            "distancia_km": round(distancia_m / METROS_POR_KM, 3),
            "bateria_final_pct": round(vehiculo.nivel_bateria, 2),
            "recarga_activada": False,
        }

        if vehiculo.necesita_recarga() or vehiculo.bateria_critica():
            nodo_actual = ruta[-1]

            id_electrolinera, nodo_electrolinera, ruta_carga, distancia_carga, tiempo_ms = (
                electrolinera_mas_cercana(G, nodo_actual, nodos_electro)
            )

            if id_electrolinera:
                nombre_electrolinera = obtener_nombre_nodo(G, nodo_electrolinera)

                evento = {
                    "timestamp": tiempo_actual.strftime("%Y-%m-%d %H:%M:%S"),
                    "vehiculo_id": vehiculo.id,
                    "vehiculo_nombre": vehiculo.nombre_mostrado,
                    "electrolinera_id": id_electrolinera,
                    "electrolinera_nombre": nombre_electrolinera,
                    "nodo_origen_osm": nodo_actual,
                    "nivel_bateria_llegada": round(vehiculo.nivel_bateria, 2),
                    "distancia_recorrida_m": round(distancia_carga, 1),
                }
                registrar_recarga(evento)

                vehiculo.recargar(80.0)
                estadisticas["total_recargas"] = estadisticas["total_recargas"] + 1
                estadisticas["por_vehiculo"][vehiculo.nombre_mostrado]["recargas"] = (
                    estadisticas["por_vehiculo"][vehiculo.nombre_mostrado]["recargas"] + 1
                )
                estadisticas["uso_electrolineras"][nombre_electrolinera] = (
                    estadisticas["uso_electrolineras"].get(nombre_electrolinera, 0) + 1
                )

                detalle_recorrido["recarga_activada"] = True
                detalle_recorrido["electrolinera_usada"] = nombre_electrolinera
                detalle_recorrido["distancia_a_electro_km"] = round(
                    distancia_carga / METROS_POR_KM, 3
                )
                detalle_recorrido["ruta_carga"] = ruta_carga
                detalle_recorrido["tiempo_busqueda_ms"] = round(tiempo_ms, 3)

        estadisticas["recorridos"].append(detalle_recorrido)
        estadisticas["total_recorridos"] = estadisticas["total_recorridos"] + 1
        i = i + 1

    exportar_estadisticas_json(estadisticas)

    print()
    print("Simulacion completada:")
    print("Recorridos:", estadisticas["total_recorridos"])
    print("Recargas:", estadisticas["total_recargas"])

    return estadisticas


def imprimir_resumen(estadisticas):
    if not estadisticas:
        print("No hay estadisticas para mostrar.")
        return

    print()
    print("=" * 60)
    print("  RESUMEN DE SIMULACION")
    print("=" * 60)
    print("  Total recorridos :", estadisticas["total_recorridos"])
    print("  Total recargas   :", estadisticas["total_recargas"])

    print()
    print("  Uso de electrolineras:")
    electrolineras = estadisticas.get("uso_electrolineras", {})
    if electrolineras:
        for nombre, conteo in sorted(electrolineras.items(), key=lambda dato: -dato[1]):
            print("   ", f"{nombre:<45}", "->", conteo, "recargas")
    else:
        print("    (ninguna recarga registrada)")

    print()
    print("  Por vehiculo:")
    for nombre, datos in estadisticas.get("por_vehiculo", {}).items():
        print(
            "   ",
            f"{nombre:<40}",
            "| Recargas:",
            f"{datos['recargas']:>3}",
            "| km totales:",
            f"{datos['km_total']:>8.1f}",
        )

    print("=" * 60)
