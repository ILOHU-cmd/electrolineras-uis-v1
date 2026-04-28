"""
Menu preliminar de la aplicacion.

Esta version solo es el menu y valida opciones.
funcionalidades en construccion
"""

import os
import sys

# Permite que Python encuentre los modulos del proyecto
# sin importar desde que carpeta se ejecute el programa
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# --- Importaciones del proyecto ---
# Cada import trae una funcionalidad real de un modulo especifico.
# Si alguna libreria no esta instalada, el programa igual arranca
# y muestra un aviso solo cuando se intenta usar esa opcion.
try:
    from src.grafo.constructor_grafo import construir_grafo
    from src.simulacion.simulacion import ejecutar_simulacion, imprimir_resumen
    from src.grafo.visualizacion import generar_mapa_folium, grafico_uso_electrolineras
    from src.ml.modelo_ml import cargar_o_entrenar, predecir_electrolinera
    from src.utils.archivos import leer_csv, guardar_xlsx
    from data.datos_estaticos import ELECTROLINERAS, PUNTOS_REFERENCIA, VEHICULOS
    MODULOS_DISPONIBLES = True
except ImportError as error:
    MODULOS_DISPONIBLES = False
    _ERROR_IMPORTACION = str(error)

# --- Estado global de la sesion ---
# Estas variables guardan lo que el usuario va construyendo
# durante la ejecucion: el grafo, las estadisticas y el modelo ML.
grafo         = None   # grafo vial cargado con OSMnx
estadisticas  = {}     # resultados de la ultima simulacion
modelos_ml    = {}     # modelos entrenados en la sesion


# ─────────────────────────────────────────────────────────────

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

    # Muestra el estado actual de la sesion debajo del titulo
    estado_grafo = "CARGADO" if grafo else "no cargado"
    estado_sim   = (str(estadisticas.get("total_recorridos", 0)) + " recorridos"
                    if estadisticas else "sin datos")
    estado_ml    = "entrenado" if modelos_ml else "sin entrenar"

    print("Grafo:", estado_grafo,
          " | Simulacion:", estado_sim,
          " | ML:", estado_ml)
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
# FUNCIONES DE CADA OPCION
# Cada funcion reemplaza al mensaje "en construccion" una vez
# que el modulo correspondiente esta listo. Mientras tanto,
# si los modulos no estan disponibles, cae al mensaje original.
# ─────────────────────────────────────────────────────────────

def opcion_1_cargar_grafo():
    """Carga o construye el grafo vial de Bucaramanga con OSMnx."""
    global grafo
    if not MODULOS_DISPONIBLES:
        mostrar_mensaje_opcion("1")
        return

    print()
    print("Construyendo grafo vial de Bucaramanga...")
    respuesta = input("Usar cache local si existe? (s/n): ").strip().lower()
    usar_cache = respuesta == "s"
    grafo = construir_grafo(desde_cache=usar_cache)


def opcion_2_ver_datos():
    """Muestra electrolineras, puntos de referencia y vehiculos."""
    if not MODULOS_DISPONIBLES:
        mostrar_mensaje_opcion("2")
        return

    print()
    print("ELECTROLINERAS (Nodos tipo A)")
    print("-" * 60)
    for e in ELECTROLINERAS:
        print(e["id"], "-", e["nombre"],
              "| lat:", e["lat"], "lon:", e["lon"],
              "| potencia:", e["potencia_kw"], "kW")

    print()
    print("PUNTOS DE REFERENCIA (Nodos tipo B)")
    print("-" * 60)
    for p in PUNTOS_REFERENCIA:
        print(p["id"], "-", p["nombre"],
              "| lat:", p["lat"], "lon:", p["lon"])

    print()
    print("VEHICULOS ELECTRICOS")
    print("-" * 60)
    for clave, v in VEHICULOS.items():
        print(v["id"], "-", v["nombre"],
              "| gama:", v["gama"].upper(),
              "| bateria:", v["bateria_kwh"], "kWh",
              "| autonomia:", v["autonomia_real_km"], "km")


def opcion_3_simulacion():
    """Ejecuta la simulacion de recorridos de vehiculos electricos."""
    global estadisticas
    if not MODULOS_DISPONIBLES:
        mostrar_mensaje_opcion("3")
        return

    if grafo is None:
        print()
        print("Primero debe cargar el grafo (opcion 1).")
        return

    # Validar numero de recorridos
    while True:
        entrada = input("Numero de recorridos a simular (1-500): ").strip()
        if entrada.isdigit() and 1 <= int(entrada) <= 500:
            n_recorridos = int(entrada)
            break
        print("Valor invalido. Ingrese un numero entre 1 y 500.")

    # Validar semilla
    while True:
        entrada = input("Semilla aleatoria (0 para aleatoria): ").strip()
        if entrada.isdigit():
            semilla = int(entrada) if int(entrada) > 0 else None
            break
        print("Valor invalido. Ingrese un numero entero positivo o 0.")

    print()
    estadisticas = ejecutar_simulacion(
        grafo,
        n_recorridos=n_recorridos,
        semilla=semilla,
    )


def opcion_4_resumen():
    """Muestra el resumen estadistico de la ultima simulacion."""
    if not MODULOS_DISPONIBLES:
        mostrar_mensaje_opcion("4")
        return

    if not estadisticas:
        print()
        print("No hay estadisticas disponibles. Ejecute la simulacion primero (opcion 3).")
        return

    imprimir_resumen(estadisticas)

    if estadisticas.get("uso_electrolineras"):
        respuesta = input("Generar grafico de barras del uso? (s/n): ").strip().lower()
        if respuesta == "s":
            grafico_uso_electrolineras(estadisticas)


def opcion_5_mapa():
    """Genera el mapa interactivo HTML con Folium."""
    if not MODULOS_DISPONIBLES:
        mostrar_mensaje_opcion("5")
        return

    print()
    print("Generando mapa interactivo...")
    ruta = generar_mapa_folium(G=grafo)
    if ruta:
        print("Mapa guardado. Abra este archivo en su navegador:")
        print(ruta)


def opcion_6_entrenar_ml():
    """Entrena o carga desde disco el modelo de Machine Learning."""
    global modelos_ml
    if not MODULOS_DISPONIBLES:
        mostrar_mensaje_opcion("6")
        return

    ruta_pkl = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "processed",
        "modelo_random_forest.pkl"
    )

    forzar = False
    if os.path.exists(ruta_pkl):
        print()
        print("Se encontro un modelo guardado en disco.")
        respuesta = input("Desea REENTRENAR el modelo con los datos actuales? (s/n): ").strip().lower()
        forzar = respuesta == "s"
    else:
        print()
        print("No existe modelo guardado. Se entrenara uno nuevo.")

    modelos_ml = cargar_o_entrenar(forzar_reentrenamiento=forzar)

    if not modelos_ml:
        print("No se pudo cargar ni entrenar el modelo.")
        print("Asegurese de haber ejecutado la simulacion primero (opcion 3).")


def opcion_7_predecir():
    """Predice la electrolinera mas probable usando el modelo ML."""
    if not MODULOS_DISPONIBLES:
        mostrar_mensaje_opcion("7")
        return

    if not modelos_ml:
        print()
        print("Primero entrene los modelos (opcion 6).")
        return

    print()
    print("PREDICCION DE ELECTROLINERA")
    print("-" * 40)

    # Validar nivel de bateria
    while True:
        entrada = input("Nivel de bateria actual (0-100): ").strip()
        try:
            nivel = float(entrada)
            if 0.0 <= nivel <= 100.0:
                break
            print("El nivel debe estar entre 0 y 100.")
        except ValueError:
            print("Valor invalido. Use numeros decimales (ej: 15.5).")

    # Validar distancia
    while True:
        entrada = input("Distancia al ultimo destino en metros: ").strip()
        try:
            dist = float(entrada)
            if dist >= 0.0:
                break
            print("La distancia no puede ser negativa.")
        except ValueError:
            print("Valor invalido. Use numeros positivos.")

    # Seleccionar vehiculo
    print("Vehiculos: 0 = Tesla Model 3 LR   |   1 = BYD Seagull")
    while True:
        entrada = input("Numero de vehiculo: ").strip()
        if entrada in ("0", "1"):
            vid_enc = int(entrada)
            break
        print("Opcion invalida. Ingrese 0 o 1.")

    resultado = predecir_electrolinera(nivel, dist, vid_enc)
    print()
    print("Electrolinera predicha por ML:", resultado)


def opcion_8_exportar():
    """Exporta el historial de recargas a un archivo Excel."""
    if not MODULOS_DISPONIBLES:
        mostrar_mensaje_opcion("8")
        return

    filas = leer_csv("historial_recargas")
    if not filas:
        print()
        print("No hay historial de recargas. Ejecute la simulacion primero.")
        return

    ruta = guardar_xlsx("historial_recargas", filas)
    print()
    print("Exportado correctamente a:")
    print(ruta)


def opcion_9_comparar():
    """Compara las metricas de precision y tiempo entre Dijkstra y ML."""
    if not MODULOS_DISPONIBLES:
        mostrar_mensaje_opcion("9")
        return

    if not modelos_ml:
        print()
        print("Entrene los modelos primero (opcion 6).")
        return

    print()
    print("COMPARACION: DIJKSTRA vs MACHINE LEARNING")
    print("-" * 50)
    for nombre, datos in modelos_ml.items():
        print("Modelo:", nombre)
        print("  Accuracy         :", datos.get("accuracy", "N/A"))
        print("  F1 (weighted)    :", datos.get("f1_weighted", "N/A"))
        print("  Tiempo inferencia:", datos.get("tiempo_inferencia_ms", "N/A"), "ms")
        print("  (Dijkstra tipico : 5-50 ms para 8 electrolineras)")
        print()


# ─────────────────────────────────────────────────────────────
# BUCLE PRINCIPAL DEL MENU
# ─────────────────────────────────────────────────────────────

def ejecutar_menu():
    while True:
        limpiar_pantalla()
        mostrar_encabezado()
        mostrar_menu()
        opcion = input("Seleccione una opcion: ").strip()

        if opcion == "1":
            opcion_1_cargar_grafo()
        elif opcion == "2":
            opcion_2_ver_datos()
        elif opcion == "3":
            opcion_3_simulacion()
        elif opcion == "4":
            opcion_4_resumen()
        elif opcion == "5":
            opcion_5_mapa()
        elif opcion == "6":
            opcion_6_entrenar_ml()
        elif opcion == "7":
            opcion_7_predecir()
        elif opcion == "8":
            opcion_8_exportar()
        elif opcion == "9":
            opcion_9_comparar()
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