"""
visualizacion.py
----------------
Visualización del grafo vial y resultados de la simulación.

Opciones:
  1. Mapa interactivo con Folium (HTML exportable)
  2. Grafo coloreado con NetworkX + Matplotlib
     - Rojo   → Electrolineras
     - Azul   → Puntos de referencia
     - Verde  → Rutas óptimas resaltadas
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from data.datos_estaticos import ELECTROLINERAS, PUNTOS_REFERENCIA

DIR_OUTPUT = os.path.join(os.path.dirname(__file__), "..", "..", "data", "output")
os.makedirs(DIR_OUTPUT, exist_ok=True)

try:
    import folium
    FOLIUM_DISPONIBLE = True
except ImportError:
    FOLIUM_DISPONIBLE = False

try:
    import matplotlib.pyplot as plt
    import networkx as nx
    MPL_DISPONIBLE = True
except ImportError:
    MPL_DISPONIBLE = False


# ─────────────────────────────────────────────────────────────
# MAPA INTERACTIVO CON FOLIUM
# ─────────────────────────────────────────────────────────────
def generar_mapa_folium(G=None, rutas_resaltadas: list = None) -> str:
    """
    Genera un mapa HTML interactivo con marcadores para electrolineras
    y puntos de referencia.

    Parámetros
    ----------
    G : nx.MultiDiGraph, opcional
        Si se provee, se dibujan las aristas del grafo.
    rutas_resaltadas : list[list[int]], opcional
        Lista de rutas (listas de nodos OSM) a resaltar en verde.

    Retorna
    -------
    str
        Ruta del archivo HTML generado.
    """
    if not FOLIUM_DISPONIBLE:
        print("  ⚠  Folium no está instalado. Instale con: pip install folium")
        return ""

    # Centro del mapa: Bucaramanga
    mapa = folium.Map(location=[7.1100, -73.1198], zoom_start=13)

    # ── Marcadores de electrolineras (rojo) ──
    for e in ELECTROLINERAS:
        folium.Marker(
            location=[e["lat"], e["lon"]],
            popup=folium.Popup(
                f"<b>⚡ {e['nombre']}</b><br>"
                f"ID: {e['id']}<br>"
                f"Potencia: {e['potencia_kw']} kW",
                max_width=250,
            ),
            tooltip=e["nombre"],
            icon=folium.Icon(color="red", icon="bolt", prefix="fa"),
        ).add_to(mapa)

    # ── Marcadores de puntos de referencia (azul) ──
    for p in PUNTOS_REFERENCIA:
        folium.Marker(
            location=[p["lat"], p["lon"]],
            popup=folium.Popup(
                f"<b>📍 {p['nombre']}</b><br>ID: {p['id']}",
                max_width=250,
            ),
            tooltip=p["nombre"],
            icon=folium.Icon(color="blue", icon="university", prefix="fa"),
        ).add_to(mapa)

    # ── Rutas resaltadas (verde) ──
    if rutas_resaltadas and G is not None:
        for ruta in rutas_resaltadas:
            coordenadas = []
            for nodo in ruta:
                lat = G.nodes[nodo].get("y", 0)
                lon = G.nodes[nodo].get("x", 0)
                coordenadas.append((lat, lon))
            if coordenadas:
                folium.PolyLine(
                    coordenadas,
                    color="green",
                    weight=4,
                    opacity=0.8,
                    tooltip="Ruta óptima",
                ).add_to(mapa)

    # ── Leyenda ──
    leyenda_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
                background: white; padding: 10px; border-radius: 8px;
                border: 2px solid #ccc; font-size: 13px;">
      <b>Leyenda</b><br>
      <span style="color:red;">●</span> Electrolinera<br>
      <span style="color:#3c6dc5;">●</span> Punto de referencia<br>
      <span style="color:green;">─</span> Ruta óptima
    </div>
    """
    mapa.get_root().html.add_child(folium.Element(leyenda_html))

    ruta_html = os.path.join(DIR_OUTPUT, "mapa_electrolineras.html")
    mapa.save(ruta_html)
    print(f"  ✓  Mapa guardado en: {ruta_html}")
    return ruta_html


# ─────────────────────────────────────────────────────────────
# GRAFO COLOREADO CON MATPLOTLIB
# ─────────────────────────────────────────────────────────────
def visualizar_grafo_nx(G, ruta_resaltada: list = None) -> None:
    """
    Dibuja el grafo con NetworkX y Matplotlib, coloreando nodos especiales.
    Solo recomendado para grafos pequeños/sintéticos.
    """
    if not MPL_DISPONIBLE:
        print("  ⚠  Matplotlib no está instalado.")
        return

    colores = []
    tamaños = []
    for nodo, datos in G.nodes(data=True):
        tipo = datos.get("tipo_especial")
        if tipo == "electrolinera":
            colores.append("#e74c3c")   # rojo
            tamaños.append(200)
        elif tipo == "referencia":
            colores.append("#3498db")  # azul
            tamaños.append(150)
        elif ruta_resaltada and nodo in ruta_resaltada:
            colores.append("#2ecc71")  # verde
            tamaños.append(120)
        else:
            colores.append("#bdc3c7")  # gris
            tamaños.append(30)

    pos = nx.spring_layout(G, seed=42)

    plt.figure(figsize=(14, 10))
    nx.draw_networkx_nodes(G, pos, node_color=colores, node_size=tamaños, alpha=0.9)
    nx.draw_networkx_edges(G, pos, alpha=0.2, edge_color="#7f8c8d", arrows=False)

    # Etiquetas solo para nodos especiales
    etiquetas = {
        n: d.get("id_especial", "")
        for n, d in G.nodes(data=True)
        if d.get("tipo_especial")
    }
    nx.draw_networkx_labels(G, pos, labels=etiquetas, font_size=7, font_color="black")

    # Leyenda manual
    from matplotlib.patches import Patch
    leyenda = [
        Patch(facecolor="#e74c3c", label="Electrolinera"),
        Patch(facecolor="#3498db", label="Punto de referencia"),
        Patch(facecolor="#2ecc71", label="Ruta óptima"),
    ]
    plt.legend(handles=leyenda, loc="upper right")
    plt.title("Red Vial Bucaramanga - Sistema de Electrolineras", fontsize=14)
    plt.axis("off")

    ruta_img = os.path.join(DIR_OUTPUT, "grafo_electrolineras.png")
    plt.savefig(ruta_img, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓  Gráfico guardado en: {ruta_img}")


# ─────────────────────────────────────────────────────────────
# VISUALIZAR USO DE ELECTROLINERAS (barras)
# ─────────────────────────────────────────────────────────────
def grafico_uso_electrolineras(estadisticas: dict) -> None:
    """Genera gráfico de barras con el conteo de recargas por electrolinera."""
    if not MPL_DISPONIBLE:
        return

    uso = estadisticas.get("uso_electrolineras", {})
    if not uso:
        print("  ⚠  No hay datos de uso de electrolineras.")
        return

    nombres = list(uso.keys())
    conteos = list(uso.values())
    nombres_cortos = [n[:20] + "…" if len(n) > 20 else n for n in nombres]

    plt.figure(figsize=(12, 5))
    bars = plt.bar(nombres_cortos, conteos, color="#e74c3c", alpha=0.85)
    plt.bar_label(bars, padding=3)
    plt.xlabel("Electrolinera")
    plt.ylabel("Número de recargas")
    plt.title("Frecuencia de uso de electrolineras en la simulación")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    ruta_img = os.path.join(DIR_OUTPUT, "uso_electrolineras.png")
    plt.savefig(ruta_img, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓  Gráfico de barras guardado en: {ruta_img}")
