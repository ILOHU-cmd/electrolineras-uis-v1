"""
modelo_ml.py
Modulo de Machine Learning para predecir que electrolinera
usara un vehiculo dado su nivel de bateria y tipo.

Se entrena un modelo de clasificacion supervisada:
- Entradas: nivel de bateria, distancia recorrida, tipo de vehiculo
- Salida  : cual electrolinera probablemente usara el vehiculo

Modelos disponibles:
- Regresion Logistica (el mas simple, sirve como punto de comparacion)
- Random Forest       (el que mejor funciona, es el que se guarda)
- XGBoost             (si esta instalado)

El modelo entrenado se guarda en disco para no tener que
reentrenar cada vez que se abre el programa.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.utils.archivos import leer_csv, guardar_json

# Intentar importar las librerias de Machine Learning
try:
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder
    from sklearn.metrics import accuracy_score, f1_score
    import joblib
    ML_DISPONIBLE = True
except ImportError:
    ML_DISPONIBLE = False

try:
    from xgboost import XGBClassifier
    XGB_DISPONIBLE = True
except ImportError:
    XGB_DISPONIBLE = False

import time

# Carpeta donde se guardan los modelos entrenados
CARPETA_MODELOS = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "processed"
)
if not os.path.exists(CARPETA_MODELOS):
    os.makedirs(CARPETA_MODELOS)

# Nombre del archivo del modelo principal
ARCHIVO_MODELO = os.path.join(CARPETA_MODELOS, "modelo_random_forest.pkl")


def preparar_datos():
    """
    Carga el historial de recargas y lo convierte en un dataset
    listo para entrenar el modelo.

    Columnas de entrada (X):
    - nivel_bateria_llegada : que tan baja estaba la bateria
    - distancia_metros      : cuanto recorrio antes de recargar
    - vehiculo_id_enc       : numero que representa el tipo de vehiculo

    Columna de salida (y):
    - electrolinera_id : cual electrolinera uso (lo que queremos predecir)
    """
    if not ML_DISPONIBLE:
        print("Las librerias de Machine Learning no estan instaladas.")
        return None

    filas = leer_csv("historial_recargas")

    if len(filas) < 20:
        print("Datos insuficientes:", len(filas), "registros.")
        print("Se necesitan al menos 20 recargas. Ejecute mas simulaciones.")
        return None

    tabla = pd.DataFrame(filas)
    tabla["nivel_bateria_llegada"] = pd.to_numeric(tabla["nivel_bateria_llegada"], errors="coerce")
    tabla["distancia_metros"]      = pd.to_numeric(tabla["distancia_metros"],      errors="coerce")
    tabla = tabla.dropna()

    # Convertir el ID del vehiculo a numero (los modelos solo aceptan numeros)
    codificador_vehiculo = LabelEncoder()
    tabla["vehiculo_enc"] = codificador_vehiculo.fit_transform(tabla["vehiculo_id"])

    # Convertir el ID de la electrolinera a numero (es lo que queremos predecir)
    codificador_electro = LabelEncoder()
    tabla["objetivo"] = codificador_electro.fit_transform(tabla["electrolinera_id"])

    # Separar entradas y salida
    X = tabla[["nivel_bateria_llegada", "distancia_metros", "vehiculo_enc"]].values
    y = tabla["objetivo"].values

    print("Dataset preparado:", len(tabla), "registros,",
          len(codificador_electro.classes_), "electrolineras distintas")

    return X, y, codificador_electro


def entrenar_modelos():
    """
    Entrena todos los modelos disponibles y guarda el mejor en disco.
    Devuelve un diccionario con los resultados de cada modelo.
    """
    resultado = preparar_datos()
    if resultado is None:
        return {}

    X, y, codificador_electro = resultado

    # Dividir en datos de entrenamiento (75%) y datos de prueba (25%)
    X_entrenamiento, X_prueba, y_entrenamiento, y_prueba = train_test_split(
        X, y, test_size=0.25, random_state=42
    )

    # Definir los modelos a probar
    modelos_a_probar = {
        "Regresion Logistica": LogisticRegression(max_iter=500, random_state=42),
        "Random Forest":       RandomForestClassifier(n_estimators=100, random_state=42)
    }

    if XGB_DISPONIBLE:
        modelos_a_probar["XGBoost"] = XGBClassifier(
            n_estimators=100,
            eval_metric="mlogloss",
            random_state=42,
            verbosity=0
        )

    print("")
    print("Entrenando modelos...")
    print("-" * 50)

    resultados = {}

    for nombre, modelo in modelos_a_probar.items():
        # Entrenar el modelo
        inicio_entrenamiento = time.perf_counter()
        modelo.fit(X_entrenamiento, y_entrenamiento)
        tiempo_entrenamiento = (time.perf_counter() - inicio_entrenamiento) * 1000

        # Medir tiempo de prediccion
        inicio_prediccion = time.perf_counter()
        predicciones = modelo.predict(X_prueba)
        tiempo_prediccion = (time.perf_counter() - inicio_prediccion) * 1000

        # Calcular metricas de calidad
        accuracy = accuracy_score(y_prueba, predicciones)
        f1       = f1_score(y_prueba, predicciones, average="weighted", zero_division=0)

        print(nombre + ":")
        print("  Precision (accuracy):", round(accuracy, 4))
        print("  F1 score            :", round(f1, 4))
        print("  Tiempo entrenamiento:", round(tiempo_entrenamiento, 1), "ms")
        print("  Tiempo prediccion   :", round(tiempo_prediccion, 3), "ms")
        print("")

        resultados[nombre] = {
            "modelo":                    modelo,
            "codificador":               codificador_electro,
            "accuracy":                  round(accuracy, 4),
            "f1_weighted":               round(f1, 4),
            "tiempo_entrenamiento_ms":   round(tiempo_entrenamiento, 2),
            "tiempo_inferencia_ms":      round(tiempo_prediccion, 2)
        }

    # Guardar metricas en JSON para el historial
    metricas = {}
    for nombre, datos in resultados.items():
        metricas[nombre] = {
            "accuracy":                datos["accuracy"],
            "f1_weighted":             datos["f1_weighted"],
            "tiempo_entrenamiento_ms": datos["tiempo_entrenamiento_ms"],
            "tiempo_inferencia_ms":    datos["tiempo_inferencia_ms"]
        }
    guardar_json("metricas_modelos", metricas)

    return resultados


def cargar_o_entrenar(forzar_reentrenamiento=False):
    """
    Punto de entrada para la opcion 6 del menu.

    Si ya existe el archivo del modelo guardado y no se fuerza el
    reentrenamiento, lo carga directamente desde disco.
    Si no existe o se fuerza, entrena uno nuevo y lo guarda.
    """
    if not ML_DISPONIBLE:
        print("Las librerias de Machine Learning no estan instaladas.")
        return {}

    # Intentar cargar desde disco si existe
    if not forzar_reentrenamiento and os.path.exists(ARCHIVO_MODELO):
        try:
            paquete       = joblib.load(ARCHIVO_MODELO)
            modelo        = paquete["modelo"]
            codificador   = paquete["codificador"]
            metricas      = paquete.get("metricas", {})

            print("")
            print("Modelo cargado desde disco:")
            print("  Archivo  :", ARCHIVO_MODELO)
            print("  Tipo     :", type(modelo).__name__)
            print("  Clases   :", list(codificador.classes_))
            if len(metricas) > 0:
                print("  Accuracy :", metricas.get("accuracy", "N/A"))
                print("  F1 score :", metricas.get("f1_weighted", "N/A"))

            return {
                "Random Forest": {
                    "modelo":            modelo,
                    "codificador":       codificador,
                    "accuracy":          metricas.get("accuracy"),
                    "f1_weighted":       metricas.get("f1_weighted"),
                    "tiempo_inferencia_ms": metricas.get("tiempo_inferencia_ms")
                }
            }

        except Exception as error:
            print("Error al cargar el modelo:", error)
            print("Reentrenando desde cero...")

    # Entrenar desde cero
    if forzar_reentrenamiento:
        print("Reentrenamiento solicitado por el usuario.")
    else:
        print("No existe modelo guardado. Entrenando nuevo modelo...")

    resultados = entrenar_modelos()

    # Guardar el Random Forest en disco (incluyendo las metricas)
    if "Random Forest" in resultados:
        datos_rf = resultados["Random Forest"]
        joblib.dump(
            {
                "modelo":      datos_rf["modelo"],
                "codificador": datos_rf["codificador"],
                "metricas": {
                    "accuracy":               datos_rf["accuracy"],
                    "f1_weighted":            datos_rf["f1_weighted"],
                    "tiempo_inferencia_ms":   datos_rf["tiempo_inferencia_ms"]
                }
            },
            ARCHIVO_MODELO
        )
        print("Modelo guardado en:", ARCHIVO_MODELO)

    return resultados


def predecir_electrolinera(nivel_bateria, distancia_m, vehiculo_enc):
    """
    Usa el modelo guardado para predecir que electrolinera
    usara un vehiculo dado su nivel de bateria.

    Devuelve el ID de la electrolinera predicha (ej: "E3")
    """
    if not os.path.exists(ARCHIVO_MODELO):
        print("Modelo no encontrado. Entrene primero (opcion 6).")
        return "N/A"

    paquete     = joblib.load(ARCHIVO_MODELO)
    modelo      = paquete["modelo"]
    codificador = paquete["codificador"]

    # Crear el vector de entrada con los mismos campos que el entrenamiento
    entrada = [[nivel_bateria, distancia_m, vehiculo_enc]]

    inicio      = time.perf_counter()
    prediccion  = modelo.predict(entrada)[0]
    tiempo_ms   = (time.perf_counter() - inicio) * 1000

    # Convertir el numero predicho de vuelta al ID de electrolinera
    electrolinera = codificador.inverse_transform([prediccion])[0]

    print("Prediccion completada en", round(tiempo_ms, 3), "ms")
    return electrolinera
