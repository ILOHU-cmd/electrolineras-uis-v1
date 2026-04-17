"""
Funciones de visualizacion del proyecto.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from data.datos_estaticos import (
    ELECTROLINERAS,
    PUNTOS_REFERENCIA,
    VEHICULOS,
    formatear_nombre_vehiculo,
)

DIR_OUTPUT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "output")
)
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


def generar_mapa_folium(G=None, rutas_resaltadas=None):
    if not FOLIUM_DISPONIBLE:
        print("Folium no esta instalado. Instale con: pip install folium")
        return ""

    mapa = folium.Map(location=[7.1100, -73.1198], zoom_start=13)

    i = 0
    while i < len(ELECTROLINERAS):
        electrolinera = ELECTROLINERAS[i]
        folium.Marker(
            location=[electrolinera["lat"], electrolinera["lon"]],
            popup=folium.Popup(
                "<b>"
                + electrolinera["nombre"]
                + "</b><br>ID: "
                + electrolinera["id"]
                + "<br>Potencia: "
                + str(electrolinera["potencia_kw"])
                + " kW",
                max_width=250,
            ),
            tooltip=electrolinera["nombre"],
            icon=folium.Icon(color="red", icon="bolt", prefix="fa"),
        ).add_to(mapa)
        i = i + 1

    i = 0
    while i < len(PUNTOS_REFERENCIA):
        punto = PUNTOS_REFERENCIA[i]
        folium.Marker(
            location=[punto["lat"], punto["lon"]],
            popup=folium.Popup(
                "<b>" + punto["nombre"] + "</b><br>ID: " + punto["id"],
                max_width=250,
            ),
            tooltip=punto["nombre"],
            icon=folium.Icon(color="blue", icon="university", prefix="fa"),
        ).add_to(mapa)
        i = i + 1

    if rutas_resaltadas and G is not None:
        i = 0
        while i < len(rutas_resaltadas):
            ruta = rutas_resaltadas[i]
            coordenadas = []

            j = 0
            while j < len(ruta):
                nodo = ruta[j]
                latitud = G.nodes[nodo].get("y", 0)
                longitud = G.nodes[nodo].get("x", 0)
                coordenadas.append((latitud, longitud))
                j = j + 1

            if coordenadas:
                folium.PolyLine(
                    coordenadas,
                    color="green",
                    weight=4,
                    opacity=0.8,
                    tooltip="Ruta optima",
                ).add_to(mapa)

            i = i + 1

    leyenda_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
                background: white; padding: 10px; border-radius: 8px;
                border: 2px solid #ccc; font-size: 13px;">
      <b>Leyenda</b><br>
      <span style="color:red;">●</span> Electrolinera<br>
      <span style="color:#3c6dc5;">●</span> Punto de referencia<br>
      <span style="color:green;">─</span> Ruta optima
    </div>
    """
    mapa.get_root().html.add_child(folium.Element(leyenda_html))

    ruta_html = os.path.join(DIR_OUTPUT, "mapa_electrolineras.html")
    mapa.save(ruta_html)
    print("Mapa guardado en:", ruta_html)
    return ruta_html


def visualizar_grafo_nx(G, ruta_resaltada=None):
    if not MPL_DISPONIBLE:
        print("Matplotlib no esta instalado.")
        return ""

    colores = []
    tamanos = []

    for nodo, datos in G.nodes(data=True):
        tipo = datos.get("tipo_especial")
        if tipo == "electrolinera":
            colores.append("#e74c3c")
            tamanos.append(200)
        elif tipo == "referencia":
            colores.append("#3498db")
            tamanos.append(150)
        elif ruta_resaltada and nodo in ruta_resaltada:
            colores.append("#2ecc71")
            tamanos.append(120)
        else:
            colores.append("#bdc3c7")
            tamanos.append(30)

    posiciones = nx.spring_layout(G, seed=42)

    plt.figure(figsize=(14, 10))
    nx.draw_networkx_nodes(
        G, posiciones, node_color=colores, node_size=tamanos, alpha=0.9
    )
    nx.draw_networkx_edges(G, posiciones, alpha=0.2, edge_color="#7f8c8d", arrows=False)

    etiquetas = {}
    for nodo, datos in G.nodes(data=True):
        if datos.get("tipo_especial"):
            etiquetas[nodo] = datos.get("id_especial", "")

    nx.draw_networkx_labels(
        G, posiciones, labels=etiquetas, font_size=7, font_color="black"
    )

    from matplotlib.patches import Patch

    leyenda = [
        Patch(facecolor="#e74c3c", label="Electrolinera"),
        Patch(facecolor="#3498db", label="Punto de referencia"),
        Patch(facecolor="#2ecc71", label="Ruta optima"),
    ]
    plt.legend(handles=leyenda, loc="upper right")
    plt.title("Red vial Bucaramanga - Sistema de electrolineras", fontsize=14)
    plt.axis("off")

    ruta_img = os.path.join(DIR_OUTPUT, "grafo_electrolineras.png")
    plt.savefig(ruta_img, dpi=150, bbox_inches="tight")
    plt.close()
    print("Grafico guardado en:", ruta_img)
    return ruta_img


def grafico_uso_electrolineras(estadisticas):
    if not MPL_DISPONIBLE:
        return ""

    recorridos = estadisticas.get("recorridos", [])
    if not recorridos:
        print("No hay datos de uso de electrolineras.")
        return ""

    nombres_electrolineras = []
    i = 0
    while i < len(ELECTROLINERAS):
        nombres_electrolineras.append(ELECTROLINERAS[i]["nombre"])
        i = i + 1

    nombres_vehiculos = []
    for datos_vehiculo in VEHICULOS.values():
        nombres_vehiculos.append(
            formatear_nombre_vehiculo(datos_vehiculo["nombre"], datos_vehiculo["gama"])
        )

    conteos = {}
    i = 0
    while i < len(nombres_electrolineras):
        nombre_electrolinera = nombres_electrolineras[i]
        conteos[nombre_electrolinera] = {}

        j = 0
        while j < len(nombres_vehiculos):
            nombre_vehiculo = nombres_vehiculos[j]
            conteos[nombre_electrolinera][nombre_vehiculo] = 0
            j = j + 1

        i = i + 1

    i = 0
    total_recargas = 0
    while i < len(recorridos):
        recorrido = recorridos[i]
        if recorrido.get("recarga_activada"):
            nombre_electrolinera = recorrido.get("electrolinera_usada", "")
            nombre_vehiculo = recorrido.get("vehiculo", "")

            if nombre_electrolinera in conteos and nombre_vehiculo in conteos[nombre_electrolinera]:
                conteos[nombre_electrolinera][nombre_vehiculo] = (
                    conteos[nombre_electrolinera][nombre_vehiculo] + 1
                )
                total_recargas = total_recargas + 1
        i = i + 1

    if total_recargas == 0:
        print("No se registraron recargas en la simulacion actual.")
        return ""

    nombres_cortos = []
    i = 0
    while i < len(nombres_electrolineras):
        nombre = nombres_electrolineras[i]
        if len(nombre) > 18:
            nombres_cortos.append(nombre[:18] + "...")
        else:
            nombres_cortos.append(nombre)
        i = i + 1

    posiciones = list(range(len(nombres_electrolineras)))
    ancho_barra = 0.35
    colores = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    totales_por_electrolinera = []

    i = 0
    while i < len(nombres_electrolineras):
        nombre_electrolinera = nombres_electrolineras[i]
        total = 0

        j = 0
        while j < len(nombres_vehiculos):
            nombre_vehiculo = nombres_vehiculos[j]
            total = total + conteos[nombre_electrolinera][nombre_vehiculo]
            j = j + 1

        totales_por_electrolinera.append(total)
        i = i + 1

    plt.figure(figsize=(16, 7))

    i = 0
    while i < len(nombres_vehiculos):
        nombre_vehiculo = nombres_vehiculos[i]
        desplazamiento = (i - (len(nombres_vehiculos) - 1) / 2) * ancho_barra
        posiciones_barra = []
        valores_barra = []

        j = 0
        while j < len(posiciones):
            posiciones_barra.append(posiciones[j] + desplazamiento)
            nombre_electrolinera = nombres_electrolineras[j]
            valores_barra.append(conteos[nombre_electrolinera][nombre_vehiculo])
            j = j + 1

        barras = plt.bar(
            posiciones_barra,
            valores_barra,
            width=ancho_barra,
            color=colores[i % len(colores)],
            alpha=0.9,
            label=nombre_vehiculo,
        )

        etiquetas = []
        j = 0
        while j < len(valores_barra):
            if valores_barra[j] == 0:
                etiquetas.append("")
            else:
                etiquetas.append(str(valores_barra[j]))
            j = j + 1

        plt.bar_label(barras, labels=etiquetas, padding=3, fontsize=9)
        i = i + 1

    plt.xlabel("Electrolinera")
    plt.ylabel("Numero de recargas")
    plt.title("Uso comparativo de electrolineras por vehiculo")
    plt.xticks(posiciones, nombres_cortos, rotation=25, ha="right")
    plt.legend(title="Vehiculo (modelo y gama)")
    plt.grid(axis="y", linestyle="--", alpha=0.3)

    i = 0
    while i < len(posiciones):
        total = totales_por_electrolinera[i]
        if total > 0:
            plt.text(
                posiciones[i],
                total + 0.05,
                "Total: " + str(total),
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
            )
        i = i + 1

    plt.tight_layout()

    ruta_img = os.path.join(DIR_OUTPUT, "uso_electrolineras.png")
    plt.savefig(ruta_img, dpi=150, bbox_inches="tight")
    plt.close()
    print("Grafico de barras guardado en:", ruta_img)
    return ruta_img
