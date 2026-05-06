"""
Menu de la aplicacion.
Contiene el bucle principal y todas las opciones del sistema.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.grafo.constructor_grafo import construir_grafo
from src.simulacion.simulacion import ejecutar_simulacion, imprimir_resumen
from src.grafo.visualizacion import generar_mapa_folium, grafico_uso_electrolineras
from src.ml.modelo_ml import cargar_o_entrenar, predecir_electrolinera
from src.utils.archivos import leer_csv, guardar_xlsx
from src.utils.validacion import leer_entero, leer_flotante, leer_si_no
from data.datos_estaticos import ELECTROLINERAS, PUNTOS_REFERENCIA, VEHICULOS

# Variables globales de la sesion
# Se van llenando a medida que el usuario usa el programa
grafo        = None
estadisticas = {}
modelos_ml   = {}


def limpiar_pantalla():
    if os.name == "nt": #funciones que ayudan a que la terminal se limpie tanto en windows como en linux
        os.system("cls")
    else:
        os.system("clear")


# Funciones para mostrar el menu y manejar opciones
def mostrar_encabezado():
    print("=" * 70)
    print("SISTEMA DE ELECTROLINERAS - AREA METROPOLITANA DE BUCARAMANGA")
    print("MENU PRELIMINAR DE LA APLICACION")
    print("=" * 70)

    # Mostrar el estado actual del programa debajo del titulo
    if grafo is not None:
        estado_grafo = "CARGADO"
    else:
        estado_grafo = "no cargado"

    if len(estadisticas) > 0:
        estado_sim = str(estadisticas.get("total_recorridos", 0)) + " recorridos"
    else:
        estado_sim = "sin datos"

    if len(modelos_ml) > 0:
        estado_ml = "entrenado"
    else:
        estado_ml = "sin entrenar"

    print("Grafo:", estado_grafo, " | Simulacion:", estado_sim, " | ML:", estado_ml)
    print()


#funcion que muestra el menu de opciones y valida la seleccion del usuario, cada opcion muestra un mensaje indicando que la funcionalidad esta en construccion, excepto la opcion 0 que finaliza el programa
def mostrar_menu():
    print("MENU DE OPCIONES")
    print("1. Cargar o construir el grafo vial")
    print("2. Ver electrolineras, puntos de referencia y vehiculos")
    print("3. Ejecutar simulacion de recorridos")
    print("4. Ver resumen estadistico")
    print("5. Generar mapa interactivo")
    print("6. Entrenar modelos de Machine Learning")
    print("7. Predecir electrolinera con ML")
    print("8. Exportar historial a Excel")
    print("9. Comparar Dijkstra y ML")
    print("0. Salir")
    print()


def pausar():
    input("Presione Enter para continuar...")


def mostrar_mensaje_opcion(numero):
    print()
    print("Opcion", numero, "seleccionada.")
    print("Esta funcionalidad se encuentra en construccion")


# ─────────────────────────────────────────────────────────────
# OPCION 1: cargar el grafo vial
# ─────────────────────────────────────────────────────────────
def opcion_1():
    global grafo
    print()
    print("Construyendo grafo vial de Bucaramanga...")
    usar_cache = leer_si_no("Usar archivo guardado si existe")
    grafo = construir_grafo(desde_cache=usar_cache)


# ─────────────────────────────────────────────────────────────
# OPCION 2: ver datos del sistema
# ─────────────────────────────────────────────────────────────
def opcion_2():
    print()
    print("ELECTROLINERAS (Nodos tipo A)")
    print("-" * 60)
    for e in ELECTROLINERAS:
        print(e["id"], "-", e["nombre"])
        print("    lat:", e["lat"], " lon:", e["lon"], " potencia:", e["potencia_kw"], "kW")

    print()
    print("PUNTOS DE REFERENCIA (Nodos tipo B)")
    print("-" * 60)
    for p in PUNTOS_REFERENCIA:
        print(p["id"], "-", p["nombre"])
        print("    lat:", p["lat"], " lon:", p["lon"])

    print()
    print("VEHICULOS ELECTRICOS")
    print("-" * 60)
    for clave in VEHICULOS:
        v = VEHICULOS[clave]
        print(v["id"], "-", v["nombre"], "[" + v["gama"].upper() + "]")
        print("    Bateria:", v["bateria_kwh"], "kWh",
              " | Autonomia:", v["autonomia_km"], "km",
              " | Consumo:", v["consumo_kwh_100km"], "kWh/100km")


# ─────────────────────────────────────────────────────────────
# OPCION 3: ejecutar simulacion
# ─────────────────────────────────────────────────────────────
def opcion_3():
    global estadisticas
    if grafo is None:
        print()
        print("Primero debe cargar el grafo (opcion 1).")
        return

    n_recorridos = leer_entero("Numero de recorridos a simular (1-500): ", minimo=1, maximo=500)
    semilla_raw  = leer_entero("Semilla aleatoria (0 para aleatoria): ", minimo=0)
    semilla      = semilla_raw if semilla_raw > 0 else None

    print()
    estadisticas = ejecutar_simulacion(grafo, n_recorridos=n_recorridos, semilla=semilla)


# ─────────────────────────────────────────────────────────────
# OPCION 4: ver resumen estadistico
# ─────────────────────────────────────────────────────────────
def opcion_4():
    if len(estadisticas) == 0:
        print()
        print("No hay estadisticas disponibles. Ejecute la simulacion primero (opcion 3).")
        return

    imprimir_resumen(estadisticas)

    if len(estadisticas.get("uso_electrolineras", {})) > 0:
        generar_grafico = leer_si_no("Generar grafico de barras del uso")
        if generar_grafico:
            grafico_uso_electrolineras(estadisticas)


# ─────────────────────────────────────────────────────────────
# OPCION 5: generar mapa interactivo
# ─────────────────────────────────────────────────────────────
def opcion_5():
    print()
    print("Generando mapa interactivo...")
    ruta = generar_mapa_folium(grafo=grafo)
    if ruta != "":
        print("Mapa guardado correctamente.")
        print("Abra este archivo en su navegador:")
        print(ruta)


# ─────────────────────────────────────────────────────────────
# OPCION 6: entrenar o cargar modelo de ML
# ─────────────────────────────────────────────────────────────
def opcion_6():
    global modelos_ml

    ruta_modelo = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "processed",
        "modelo_random_forest.pkl"
    )

    forzar = False
    if os.path.exists(ruta_modelo):
        print()
        print("Se encontro un modelo guardado en disco.")
        forzar = leer_si_no("Desea REENTRENAR el modelo con los datos actuales")
    else:
        print()
        print("No existe modelo guardado. Se entrenara uno nuevo.")

    modelos_ml = cargar_o_entrenar(forzar_reentrenamiento=forzar)

    if len(modelos_ml) == 0:
        print("No se pudo cargar ni entrenar el modelo.")
        print("Ejecute la simulacion primero para generar datos (opcion 3).")


# ─────────────────────────────────────────────────────────────
# OPCION 7: predecir electrolinera con ML
# ─────────────────────────────────────────────────────────────
def opcion_7():
    if len(modelos_ml) == 0:
        print()
        print("Primero entrene los modelos (opcion 6).")
        return

    print()
    print("PREDICCION DE ELECTROLINERA")
    print("-" * 40)

    nivel_bateria = leer_flotante("Nivel de bateria actual (0-100): ", minimo=0.0, maximo=100.0)
    distancia_m   = leer_flotante("Distancia recorrida en metros: ", minimo=0.0)

    print("Vehiculos disponibles:")
    print("  0 = Tesla Model 3 Long Range")
    print("  1 = BYD Seagull")
    vehiculo_enc = leer_entero("Seleccione el vehiculo (0 o 1): ", minimo=0, maximo=1)

    resultado = predecir_electrolinera(nivel_bateria, distancia_m, vehiculo_enc)
    print()
    print("Electrolinera predicha por el modelo:", resultado)


# ─────────────────────────────────────────────────────────────
# OPCION 8: exportar historial a Excel
# ─────────────────────────────────────────────────────────────
def opcion_8():
    filas = leer_csv("historial_recargas")

    if len(filas) == 0:
        print()
        print("No hay historial de recargas.")
        print("Ejecute la simulacion primero (opcion 3).")
        return

    ruta = guardar_xlsx("historial_recargas", filas)
    print()
    print("Archivo Excel exportado correctamente:")
    print(ruta)


# ─────────────────────────────────────────────────────────────
# OPCION 9: comparar Dijkstra y ML
# ─────────────────────────────────────────────────────────────
def opcion_9():
    if len(modelos_ml) == 0:
        print()
        print("Entrene los modelos primero (opcion 6).")
        return

    print()
    print("COMPARACION: DIJKSTRA vs MACHINE LEARNING")
    print("-" * 50)
    print("Dijkstra:")
    print("  Tiempo tipico : 5 a 50 ms (por cada consulta de 8 electrolineras)")
    print("  Precision     : 100% (calculo exacto)")
    print()

    for nombre in modelos_ml:
        datos = modelos_ml[nombre]
        print(nombre + ":")
        print("  Precision (accuracy) :", datos.get("accuracy", "N/A"))
        print("  F1 score             :", datos.get("f1_weighted", "N/A"))
        print("  Tiempo de prediccion :", datos.get("tiempo_inferencia_ms", "N/A"), "ms")
        print()


# ─────────────────────────────────────────────────────────────
# BUCLE PRINCIPAL
# ─────────────────────────────────────────────────────────────
def ejecutar_menu():
    while True:
        limpiar_pantalla()
        mostrar_encabezado()
        mostrar_menu()
        opcion = input("Seleccione una opcion: ").strip()

        if opcion == "1":
            opcion_1()
        elif opcion == "2":
            opcion_2()
        elif opcion == "3":
            opcion_3()
        elif opcion == "4":
            opcion_4()
        elif opcion == "5":
            opcion_5()
        elif opcion == "6":
            opcion_6()
        elif opcion == "7":
            opcion_7()
        elif opcion == "8":
            opcion_8()
        elif opcion == "9":
            opcion_9()
        elif opcion == "0":
            print()
            print("Programa finalizado.")
            break
        else:
            print()
            print("Opcion invalida. Debe escribir un numero del 0 al 9.")

        print()
        pausar()


if __name__ == "__main__":
    ejecutar_menu()
