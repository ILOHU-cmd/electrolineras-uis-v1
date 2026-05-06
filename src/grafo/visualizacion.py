"""
visualizacion.py
Funciones para generar mapas y graficos del sistema.

Mapa interactivo (Folium): genera un archivo HTML con marcadores
para cada electrolinera y punto de referencia. Se puede abrir
en cualquier navegador sin necesidad de internet.

Grafico de barras (Matplotlib): muestra cuantas veces se uso
cada electrolinera durante la simulacion.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from data.datos_estaticos import ELECTROLINERAS, PUNTOS_REFERENCIA

# Carpeta de salida para los archivos generados
CARPETA_SALIDA = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "output"
)
if not os.path.exists(CARPETA_SALIDA):
    os.makedirs(CARPETA_SALIDA)

try:
    import folium
    FOLIUM_DISPONIBLE = True
except ImportError:
    FOLIUM_DISPONIBLE = False

try:
    import matplotlib.pyplot as plt
    MPL_DISPONIBLE = True
except ImportError:
    MPL_DISPONIBLE = False


def generar_mapa_folium(grafo=None, rutas=None):
    """
    Genera un mapa HTML interactivo con los marcadores de todas
    las electrolineras y puntos de referencia sobre Bucaramanga.

    Si se pasan rutas, las dibuja en verde sobre el mapa.
    """
    if not FOLIUM_DISPONIBLE:
        print("Folium no esta instalado.")
        print("Instale con: pip install folium")
        return ""

    # Centro del mapa sobre Bucaramanga
    mapa = folium.Map(location=[7.1100, -73.1198], zoom_start=13)

    # Agregar marcadores rojos para electrolineras
    for e in ELECTROLINERAS:
        folium.Marker(
            location=[e["lat"], e["lon"]],
            popup=e["nombre"] + " | " + str(e["potencia_kw"]) + " kW",
            tooltip=e["nombre"],
            icon=folium.Icon(color="red", icon="bolt", prefix="fa")
        ).add_to(mapa)

    # Agregar marcadores azules para puntos de referencia
    for p in PUNTOS_REFERENCIA:
        folium.Marker(
            location=[p["lat"], p["lon"]],
            popup=p["nombre"],
            tooltip=p["nombre"],
            icon=folium.Icon(color="blue", icon="university", prefix="fa")
        ).add_to(mapa)

    # Dibujar rutas si se proporcionaron
    if rutas is not None and grafo is not None:
        for ruta in rutas:
            coordenadas = []
            for nodo in ruta:
                lat = grafo.nodes[nodo].get("y", 0)
                lon = grafo.nodes[nodo].get("x", 0)
                coordenadas.append((lat, lon))
            if len(coordenadas) > 0:
                folium.PolyLine(
                    coordenadas,
                    color="green",
                    weight=4,
                    opacity=0.8,
                    tooltip="Ruta optima"
                ).add_to(mapa)

    # Guardar el archivo HTML
    ruta_archivo = os.path.join(CARPETA_SALIDA, "mapa_electrolineras.html")
    mapa.save(ruta_archivo)
    return ruta_archivo


def grafico_uso_electrolineras(estadisticas):
    """
    Genera un grafico de barras con la frecuencia de uso
    de cada electrolinera durante la simulacion.
    """
    if not MPL_DISPONIBLE:
        print("Matplotlib no esta instalado.")
        print("Instale con: pip install matplotlib")
        return

    uso = estadisticas.get("uso_electrolineras", {})

    if len(uso) == 0:
        print("No hay datos de uso para graficar.")
        return

    nombres  = list(uso.keys())
    conteos  = list(uso.values())

    # Acortar nombres largos para que quepan en el grafico
    nombres_cortos = []
    for nombre in nombres:
        if len(nombre) > 20:
            nombres_cortos.append(nombre[:20] + "...")
        else:
            nombres_cortos.append(nombre)

    plt.figure(figsize=(12, 5))
    barras = plt.bar(nombres_cortos, conteos, color="#e74c3c", alpha=0.85)
    plt.bar_label(barras, padding=3)
    plt.xlabel("Electrolinera")
    plt.ylabel("Numero de recargas")
    plt.title("Frecuencia de uso de electrolineras en la simulacion")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    ruta_archivo = os.path.join(CARPETA_SALIDA, "uso_electrolineras.png")
    plt.savefig(ruta_archivo, dpi=150, bbox_inches="tight")
    plt.close()

    print("Grafico guardado en:", ruta_archivo)
