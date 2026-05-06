"""
simulacion.py
Modulo que simula los recorridos de los vehiculos electricos.
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
BATERIA_MINIMA  = 10.0   
BATERIA_UMBRAL  = 20.0   # Si baja de este %, busca recarga
BATERIA_INICIAL = 100.0  

METROS_POR_KM = 1000.0

# ─────────────────────────────────────────────────────────────
# FUNCIONES DE TRAZABILIDAD DE RUTA
# ─────────────────────────────────────────────────────────────

def trazar_historial_ruta(grafo, lista_nodos):
    if len(lista_nodos) == 0:
        return []

    historial = []
    distancia_acumulada = 0.0

    for i in range(len(lista_nodos)):
        nodo = lista_nodos[i]
        datos_nodo   = grafo.nodes[nodo]
        tipo         = datos_nodo.get("tipo", None)
        nombre_lugar = datos_nodo.get("nombre_lugar", None)

        nombre_calle   = None
        distancia_paso = 0.0

        if i > 0:
            nodo_anterior = lista_nodos[i - 1]
            datos_aristas = grafo.get_edge_data(nodo_anterior, nodo)

            if datos_aristas:
                mejor_arista = None
                mejor_peso   = float("inf")
                for arista in datos_aristas.values():
                    peso = arista.get("length", float("inf"))
                    if peso < mejor_peso:
                        mejor_peso   = peso
                        mejor_arista = arista

                distancia_paso = mejor_arista.get("length", 0.0)
                nombre_raw = mejor_arista.get("name", None)
                if isinstance(nombre_raw, list):
                    nombre_calle = " / ".join(nombre_raw)
                elif nombre_raw:
                    nombre_calle = nombre_raw
                else:
                    nombre_calle = "sin nombre"

            distancia_acumulada = distancia_acumulada + distancia_paso

        historial.append({
            "paso":            i + 1,
            "nodo_osm":        nodo,
            "tipo_especial":   tipo,
            "nombre_lugar":    nombre_lugar,
            "calle_desde":     nombre_calle,
            "dist_parcial_m": round(distancia_paso, 1),
            "dist_acum_m":     round(distancia_acumulada, 1)
        })

    return historial

# ─────────────────────────────────────────────────────────────
# FUNCIONES DE BATERIA
# ─────────────────────────────────────────────────────────────

def calcular_consumo(distancia_m, consumo_kwh_100km, bateria_total_kwh):
    distancia_km    = distancia_m / METROS_POR_KM
    energia_gastada = (distancia_km / 100.0) * consumo_kwh_100km
    porcentaje      = (energia_gastada / bateria_total_kwh) * 100.0
    return porcentaje

def necesita_recarga(nivel_bateria):
    # CORRECCIÓN: Si es menor o igual al 20%, recarga. 
    # Ya no ignoramos a los coches que llegan con 0% o 5%.
    return nivel_bateria <= BATERIA_UMBRAL

# ─────────────────────────────────────────────────────────────
# SIMULACION PRINCIPAL
# ─────────────────────────────────────────────────────────────

def ejecutar_simulacion(grafo, n_recorridos=20, semilla=None):
    if semilla is not None:
        random.seed(semilla)

    nodos_electro = obtener_nodos_electrolineras(grafo)
    nodos_ref     = obtener_nodos_referencia(grafo)

    if not nodos_electro or not nodos_ref:
        print("Error: Grafo incompleto (faltan electrolineras o referencias).")
        return {}

    lista_nodos_ref = list(nodos_ref.values())
    lista_vehiculos = list(VEHICULOS.values())

    # --- Persistencia de bateria entre recorridos ---
    estado_baterias = {}
    for v in lista_vehiculos:
        estado_baterias[v["nombre"]] = BATERIA_INICIAL

    estadisticas = {
        "total_recorridos":   0,
        "total_recargas":     0,
        "uso_electrolineras": {},
        "por_vehiculo":       {},
        "recorridos":         []
    }

    for vehiculo in lista_vehiculos:
        estadisticas["por_vehiculo"][vehiculo["nombre"]] = {
            "recargas":  0,
            "km_total":  0.0
        }

    print(f"Iniciando simulacion: {n_recorridos} recorridos con {len(lista_vehiculos)} vehiculos")
    hora_inicio = datetime.now().replace(hour=7, minute=0, second=0)

    i = 0
    while i < n_recorridos:
        origen  = random.choice(lista_nodos_ref)
        destinos_posibles = [n for n in lista_nodos_ref if n != origen]

        if not destinos_posibles:
            i += 1
            continue

        destino = random.choice(destinos_posibles)
        vehiculo = lista_vehiculos[i % len(lista_vehiculos)]
        
        # Recuperar la batería que le quedó al vehículo
        nivel_bateria = estado_baterias[vehiculo["nombre"]]

        hora_recorrido = hora_inicio + timedelta(hours=i * 2)
        ruta, distancia_m, _ = dijkstra(grafo, origen, destino)

        if len(ruta) == 0 or distancia_m == float("inf"):
            i += 1
            continue

        # Descontar bateria (¡La carga perdida ya no desaparece!)
        consumo_pct = calcular_consumo(distancia_m, vehiculo["consumo_kwh_100km"], vehiculo["bateria_kwh"])
        nivel_bateria -= consumo_pct
        
        if nivel_bateria < 0.0: 
            nivel_bateria = 0.0

        # Acumular KM
        estadisticas["por_vehiculo"][vehiculo["nombre"]]["km_total"] += (distancia_m / METROS_POR_KM)

        historial_ruta = trazar_historial_ruta(grafo, ruta)
        detalle = {
            "recorrido_num":     i + 1,
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

        # Lógica de recarga
        if necesita_recarga(nivel_bateria):
            nodo_actual = ruta[-1]
            id_electro, nodo_electro, ruta_carga, dist_carga, _ = electrolinera_mas_cercana(grafo, nodo_actual, nodos_electro)

            if id_electro is not None:
                nombre_electro = obtener_nombre_nodo(grafo, nodo_electro)
                
                evento = {
                    "timestamp":            hora_recorrido.strftime("%Y-%m-%d %H:%M:%S"),
                    "vehiculo_id":           vehiculo["id"],
                    "vehiculo_nombre":       vehiculo["nombre"],
                    "electrolinera_id":      id_electro,
                    "electrolinera_nombre":  nombre_electro,
                    "nodo_origen":           nodo_actual,
                    "nivel_bateria_llegada": round(nivel_bateria, 2),
                    "distancia_metros":      round(dist_carga, 1)
                }
                registrar_recarga(evento)

                nivel_bateria = 80.0  # Se recarga al 80%
                
                estadisticas["total_recargas"] += 1
                estadisticas["por_vehiculo"][vehiculo["nombre"]]["recargas"] += 1
                estadisticas["uso_electrolineras"][nombre_electro] = estadisticas["uso_electrolineras"].get(nombre_electro, 0) + 1

                detalle["recarga_activada"]       = True
                detalle["electrolinera_usada"]    = nombre_electro
                detalle["distancia_a_electro_km"] = round(dist_carga / METROS_POR_KM, 3)

        # GUARDAR el estado para el próximo viaje
        estado_baterias[vehiculo["nombre"]] = nivel_bateria

        estadisticas["recorridos"].append(detalle)
        estadisticas["total_recorridos"] += 1
        i += 1

    # Finalización
    guardar_estadisticas(estadisticas)
    ruta_reporte = generar_reporte_txt(estadisticas)

    print(f"\n{'-'*55}\nSimulacion completada.\n  Recorridos : {estadisticas['total_recorridos']}")
    print(f"  Recargas   : {estadisticas['total_recargas']}\n{'-'*55}")
    print(f"Reporte generado en: {ruta_reporte}\n{'-'*55}")

    return estadisticas

def imprimir_resumen(estadisticas):
    if not estadisticas:
        print("No hay estadisticas para mostrar.")
        return

    print(f"\n{'='*60}\n  RESUMEN DE SIMULACION\n{'='*60}")
    print(f"  Total recorridos : {estadisticas['total_recorridos']}")
    print(f"  Total recargas   : {estadisticas['total_recargas']}\n")

    print("  Electrolineras mas usadas:")
    uso = estadisticas.get("uso_electrolineras", {})
    if uso:
        for nombre, conteo in sorted(uso.items(), key=lambda x: x[1], reverse=True):
            print(f"    {nombre} : {conteo} recargas")
    else:
        print("    (ninguna recarga)")

    print("\n  Por vehiculo:")
    for nombre, datos in estadisticas.get("por_vehiculo", {}).items():
        print(f"    {nombre} | Recargas: {datos['recargas']} | km: {round(datos['km_total'], 1)}")
    print("=" * 60)