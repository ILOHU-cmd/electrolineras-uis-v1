"""
Menu principal del sistema.

Se mantiene en un estilo sencillo:
- print
- if, elif, else
- while
- while True
"""

import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from data.datos_estaticos import (
    ELECTROLINERAS,
    PUNTOS_REFERENCIA,
    VEHICULOS,
    formatear_nombre_vehiculo,
)
from src.grafo.constructor_grafo import construir_grafo
from src.grafo.visualizacion import generar_mapa_folium, grafico_uso_electrolineras
from src.ml.modelo_ml import (
    entrenar_modelos,
    obtener_nombre_mostrado_modelo,
    predecir_electrolinera,
)
from src.simulacion.simulacion import ejecutar_simulacion, imprimir_resumen
from src.utils.archivos import (
    abrir_archivo,
    guardar_semilla_guardada,
    guardar_xlsx,
    leer_csv,
    leer_semillas_guardadas,
)
from src.utils.validacion import confirmar, leer_entero, leer_flotante, limpiar_pantalla


def mostrar_encabezado(grafo, estadisticas, modelos_entrenados):
    print("=" * 70)
    print("SISTEMA DE ELECTROLINERAS - AREA METROPOLITANA DE BUCARAMANGA")
    print("UIS 2026-1 - Algoritmos y Programacion - Matematicas Discretas")
    print("=" * 70)

    if grafo is None:
        texto_grafo = "No"
    else:
        texto_grafo = "Si"

    if estadisticas:
        texto_simulacion = "Si"
    else:
        texto_simulacion = "No"

    if modelos_entrenados:
        texto_ml = "Si"
    else:
        texto_ml = "No"

    print("Grafo cargado:", texto_grafo)
    print("Simulacion ejecutada:", texto_simulacion)
    print("Modelos entrenados:", texto_ml)
    print()


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


def clasificar_bateria(nivel):
    if nivel < 10:
        return "critica"
    elif nivel <= 20:
        return "baja"
    elif nivel <= 50:
        return "media"
    else:
        return "alta"


def obtener_nombre_electrolinera(id_electrolinera):
    i = 0
    while i < len(ELECTROLINERAS):
        electrolinera = ELECTROLINERAS[i]
        if electrolinera["id"] == id_electrolinera:
            return electrolinera["nombre"]
        i = i + 1
    return "No encontrada"


def mostrar_electrolineras():
    print()
    print("ELECTROLINERAS")
    i = 0
    while i < len(ELECTROLINERAS):
        e = ELECTROLINERAS[i]
        print(
            str(e["id"])
            + " - "
            + str(e["nombre"])
            + " | Potencia: "
            + str(e["potencia_kw"])
            + " kW"
            + " | Coordenadas: ("
            + str(round(e["lat"], 4))
            + ", "
            + str(round(e["lon"], 4))
            + ")"
        )
        i = i + 1


def mostrar_puntos_referencia():
    print()
    print("PUNTOS FIJOS DE REFERENCIA")
    i = 0
    while i < len(PUNTOS_REFERENCIA):
        punto = PUNTOS_REFERENCIA[i]
        print(
            str(punto["id"])
            + " - "
            + str(punto["nombre"])
            + " | Coordenadas: ("
            + str(round(punto["lat"], 4))
            + ", "
            + str(round(punto["lon"], 4))
            + ")"
        )
        i = i + 1


def mostrar_vehiculos():
    print()
    print("VEHICULOS ELECTRICOS")
    claves = list(VEHICULOS.keys())
    i = 0
    while i < len(claves):
        clave = claves[i]
        vehiculo = VEHICULOS[clave]
        nombre_mostrado = formatear_nombre_vehiculo(vehiculo["nombre"], vehiculo["gama"])
        print(
            str(vehiculo["id"])
            + " - "
            + str(nombre_mostrado)
            + " | Bateria: "
            + str(vehiculo["bateria_kwh"])
            + " kWh"
            + " | Autonomia: "
            + str(vehiculo["autonomia_real_km"])
            + " km"
        )
        i = i + 1


def mostrar_datos_base():
    mostrar_electrolineras()
    mostrar_puntos_referencia()
    mostrar_vehiculos()


def pedir_vehiculo_para_prediccion():
    nombre_tesla = formatear_nombre_vehiculo(
        VEHICULOS["tesla_model3_lr"]["nombre"],
        VEHICULOS["tesla_model3_lr"]["gama"],
    )
    nombre_byd = formatear_nombre_vehiculo(
        VEHICULOS["byd_seagull"]["nombre"],
        VEHICULOS["byd_seagull"]["gama"],
    )

    print()
    print("Seleccione el vehiculo:")
    print("1.", nombre_tesla)
    print("2.", nombre_byd)
    opcion_vehiculo = leer_entero("Digite 1 o 2: ", 1, 2)

    if opcion_vehiculo == 1:
        return 0, nombre_tesla
    else:
        return 1, nombre_byd


def mostrar_explicacion_metricas_ml():
    print()
    print("Explicacion de metricas:")
    print("Exactitud (Accuracy): porcentaje de predicciones correctas del modelo.")
    print(
        "Puntaje F1 ponderado (Weighted F1): equilibrio entre precision y recall."
    )
    print(
        "Tiempo de entrenamiento (Training time): tiempo que tarda el modelo en aprender."
    )
    print(
        "Tiempo de inferencia (Inference time): tiempo que tarda el modelo en responder."
    )


def mostrar_explicacion_comparacion():
    print()
    print("Explicacion de la comparacion:")
    print("Dijkstra: algoritmo clasico para encontrar rutas mas cortas.")
    print("ML (Machine Learning): modelo entrenado para predecir una electrolinera.")
    print("Exactitud (Accuracy): porcentaje de aciertos del modelo.")
    print("Puntaje F1 ponderado (Weighted F1): balance general del modelo.")
    print("Tiempo de inferencia (Inference time): rapidez de respuesta del modelo.")
    print("Tiempo de Dijkstra (Dijkstra time): tiempo de referencia del metodo clasico.")


def mostrar_metricas_modelos(modelos_entrenados):
    print()
    print("COMPARACION ENTRE DIJKSTRA Y ML")
    mostrar_explicacion_comparacion()

    for nombre, datos in modelos_entrenados.items():
        print()
        print("Modelo:", obtener_nombre_mostrado_modelo(nombre))
        print("Exactitud (Accuracy):", format(datos["accuracy"], ".4f"))
        print(
            "Puntaje F1 ponderado (Weighted F1):",
            format(datos["f1_weighted"], ".4f"),
        )
        print(
            "Tiempo de inferencia (Inference time):",
            format(datos["tiempo_inferencia_ms"], ".2f"),
            "ms",
        )
        print("Tiempo de Dijkstra (Dijkstra time): entre 5 y 50 ms")


def generar_semilla_nueva():
    return random.randint(1000, 999999)


def mostrar_semillas_guardadas():
    semillas = leer_semillas_guardadas()

    if not semillas:
        print()
        print("No hay semillas guardadas disponibles.")
        return semillas

    print()
    print("SEMILLAS GUARDADAS DISPONIBLES")

    i = 0
    while i < len(semillas):
        semilla = semillas[i]
        print(
            str(i + 1)
            + ". Codigo: "
            + str(semilla.get("codigo", "S?"))
            + " | Valor: "
            + str(semilla.get("semilla", ""))
            + " | Fecha: "
            + str(semilla.get("fecha_guardado", ""))
            + " | Recorridos: "
            + str(semilla.get("cantidad_recorridos", ""))
        )
        i = i + 1

    print("0. Generar una semilla aleatoria nueva")
    return semillas


def seleccionar_semilla():
    semillas = mostrar_semillas_guardadas()

    if not semillas:
        return None

    opcion = leer_entero("Seleccione una semilla: ", 0, len(semillas))

    if opcion == 0:
        return None

    return semillas[opcion - 1]["semilla"]


def procesar_guardado_semilla(semilla, cantidad):
    guardar = confirmar("Desea guardar la semilla recien generada para futuras simulaciones")

    if guardar:
        datos_guardados = guardar_semilla_guardada(semilla, cantidad)
        if datos_guardados["ya_existia"]:
            print("La semilla ya estaba guardada con el codigo:", datos_guardados["codigo"])
        else:
            print("Semilla guardada correctamente con el codigo:", datos_guardados["codigo"])


def obtener_semilla_para_simulacion(cantidad):
    print()
    print("MANEJO DE SEMILLAS")
    print("0. Generar una semilla aleatoria nueva")
    print("1. Buscar y usar una semilla guardada")
    opcion_semilla = leer_entero("Digite 0 o 1: ", 0, 1)

    if opcion_semilla == 0:
        semilla = generar_semilla_nueva()
        print("Se genero la semilla aleatoria:", semilla)
        procesar_guardado_semilla(semilla, cantidad)
        return semilla

    semilla = seleccionar_semilla()
    if semilla is None:
        print()
        print("No se selecciono una semilla guardada.")
        semilla = generar_semilla_nueva()
        print("Se genero la semilla aleatoria:", semilla)
        procesar_guardado_semilla(semilla, cantidad)
        return semilla

    print("Semilla seleccionada:", semilla)
    return semilla


def preguntar_si_desea_abrir(ruta, tipo_archivo):
    print(tipo_archivo + " generado en:")
    print(ruta)

    abrir = confirmar("Desea abrirlo ahora")
    if abrir:
        abierto = abrir_archivo(ruta)
        if abierto:
            print("Archivo abierto correctamente.")
        else:
            print("No se pudo abrir el archivo de forma automatica.")


def ejecutar_menu():
    grafo = None
    estadisticas = {}
    modelos_entrenados = {}

    while True:
        limpiar_pantalla()
        mostrar_encabezado(grafo, estadisticas, modelos_entrenados)
        mostrar_menu()
        opcion = input("Seleccione una opcion: ").strip()

        if opcion == "1":
            print()
            print("CARGA DEL GRAFO")
            usar_cache = confirmar("Desea usar el archivo guardado si existe")
            grafo = construir_grafo(desde_cache=usar_cache)

        elif opcion == "2":
            mostrar_datos_base()

        elif opcion == "3":
            if grafo is None:
                print()
                print("Primero debe cargar el grafo en la opcion 1.")
            else:
                print()
                print("SIMULACION DE RECORRIDOS")
                cantidad = leer_entero("Numero de recorridos a simular (1-500): ", 1, 500)
                semilla = obtener_semilla_para_simulacion(cantidad)

                estadisticas = ejecutar_simulacion(
                    grafo,
                    n_recorridos=cantidad,
                    semilla=semilla,
                )
                imprimir_resumen(estadisticas)

        elif opcion == "4":
            if not estadisticas:
                print()
                print("No hay estadisticas disponibles. Ejecute la simulacion primero.")
            else:
                imprimir_resumen(estadisticas)
                print()
                ver_grafico = confirmar("Desea generar el grafico de uso de electrolineras")
                if ver_grafico:
                    ruta_grafico = grafico_uso_electrolineras(estadisticas)
                    if ruta_grafico != "":
                        preguntar_si_desea_abrir(ruta_grafico, "Grafico")

        elif opcion == "5":
            print()
            print("GENERACION DE MAPA")
            ruta_mapa = generar_mapa_folium(G=grafo)

            if ruta_mapa != "":
                preguntar_si_desea_abrir(ruta_mapa, "Mapa")

        elif opcion == "6":
            print()
            print("ENTRENAMIENTO DE MODELOS")
            mostrar_explicacion_metricas_ml()
            modelos_entrenados = entrenar_modelos()

            if not modelos_entrenados:
                print("No fue posible entrenar modelos con los datos actuales.")

        elif opcion == "7":
            if not modelos_entrenados:
                print()
                print("Primero debe entrenar los modelos en la opcion 6.")
            else:
                print()
                print("PREDICCION DE ELECTROLINERA")
                nivel = leer_flotante("Nivel actual de bateria (%): ", 0.0, 100.0)
                distancia = leer_flotante("Distancia recorrida en metros: ", 0.0)
                vehiculo_id_enc, nombre_vehiculo = pedir_vehiculo_para_prediccion()
                categoria = clasificar_bateria(nivel)

                print()
                print("Vehiculo seleccionado:", nombre_vehiculo)
                print("Categoria de bateria:", categoria)

                resultado, tiempo_ms = predecir_electrolinera(nivel, distancia, vehiculo_id_enc)
                nombre_electrolinera = obtener_nombre_electrolinera(resultado)

                print(
                    "Prediccion ML:",
                    resultado,
                    "(" + nombre_electrolinera + ")",
                    "(" + format(tiempo_ms, ".3f") + " ms)",
                )
                print(
                    "Electrolinera sugerida por el modelo:",
                    resultado,
                    "(" + nombre_electrolinera + ")",
                )

        elif opcion == "8":
            print()
            print("EXPORTAR HISTORIAL")
            filas = leer_csv("historial_recargas")

            if not filas:
                print("No hay historial para exportar. Ejecute la simulacion primero.")
            else:
                ruta_archivo = guardar_xlsx("historial_recargas", filas)
                preguntar_si_desea_abrir(ruta_archivo, "Archivo")

        elif opcion == "9":
            if not modelos_entrenados:
                print()
                print("Primero debe entrenar los modelos en la opcion 6.")
            else:
                mostrar_metricas_modelos(modelos_entrenados)

        elif opcion == "0":
            print()
            print("Programa finalizado.")
            break

        else:
            print()
            print("Opcion invalida. Debe escribir un numero del 0 al 9.")

        print()
        pausar()
