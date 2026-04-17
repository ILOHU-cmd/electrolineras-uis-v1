"""
Modulo de Machine Learning para el proyecto.
"""

import os
import sys
import time
import warnings

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.utils.archivos import guardar_json, leer_csv

try:
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, f1_score
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import LabelEncoder, StandardScaler
    import joblib
    SK_DISPONIBLE = True
except ImportError:
    SK_DISPONIBLE = False

try:
    from xgboost import XGBClassifier
    XGB_DISPONIBLE = True
except ImportError:
    XGB_DISPONIBLE = False


DIR_MODELOS = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed")
)
os.makedirs(DIR_MODELOS, exist_ok=True)


def obtener_nombre_mostrado_modelo(nombre):
    nombre_minusculas = nombre.lower()

    if "random" in nombre_minusculas:
        return "Bosque Aleatorio (Random Forest)"
    if "log" in nombre_minusculas:
        return "Regresion Logistica (Logistic Regression)"
    if "xgboost" in nombre_minusculas:
        return "XGBoost"

    return nombre


def obtener_codigo_archivo_modelo(nombre):
    nombre_minusculas = nombre.lower()

    if "random" in nombre_minusculas:
        return "random_forest"
    if "log" in nombre_minusculas:
        return "regresion_logistica"
    if "xgboost" in nombre_minusculas:
        return "xgboost"

    return nombre_minusculas.replace(" ", "_")


def preparar_dataset():
    if not SK_DISPONIBLE:
        print("scikit-learn no esta instalado.")
        return None

    filas = leer_csv("historial_recargas")
    if len(filas) < 20:
        print(
            "Conjunto de datos (Dataset) insuficiente:",
            len(filas),
            "registros. Se necesitan al menos 20.",
        )
        return None

    dataframe = pd.DataFrame(filas)
    dataframe["nivel_bateria_llegada"] = pd.to_numeric(
        dataframe["nivel_bateria_llegada"], errors="coerce"
    )
    dataframe["distancia_recorrida_m"] = pd.to_numeric(
        dataframe["distancia_recorrida_m"], errors="coerce"
    )
    dataframe = dataframe.dropna()

    codificador_vehiculo = LabelEncoder()
    dataframe["vehiculo_enc"] = codificador_vehiculo.fit_transform(
        dataframe["vehiculo_id"]
    )

    codificador_objetivo = LabelEncoder()
    dataframe["target"] = codificador_objetivo.fit_transform(
        dataframe["electrolinera_id"]
    )

    x = dataframe[["nivel_bateria_llegada", "distancia_recorrida_m", "vehiculo_enc"]].values
    y = dataframe["target"].values

    print()
    print(
        "Conjunto de datos (Dataset):",
        len(dataframe),
        "registros |",
        len(codificador_objetivo.classes_),
        "clases",
    )

    return x, y, codificador_objetivo


def entrenar_modelos():
    resultado = preparar_dataset()
    if resultado is None:
        return {}

    x, y, codificador_objetivo = resultado

    x_entrenamiento, x_prueba, y_entrenamiento, y_prueba = train_test_split(
        x,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y if len(set(y)) > 1 else None,
    )

    configuraciones = {
        "Regresion Logistica": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=2000, random_state=42),
        ),
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
    }

    if XGB_DISPONIBLE:
        configuraciones["XGBoost"] = XGBClassifier(
            n_estimators=100,
            use_label_encoder=False,
            eval_metric="mlogloss",
            random_state=42,
            verbosity=0,
        )

    resultados = {}

    print()
    print("Iniciando entrenamiento de modelos...")
    print()

    for nombre, modelo in configuraciones.items():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)

            tiempo_inicio = time.perf_counter()
            modelo.fit(x_entrenamiento, y_entrenamiento)
            tiempo_entrenamiento = (time.perf_counter() - tiempo_inicio) * 1000

            tiempo_inicio = time.perf_counter()
            y_pred = modelo.predict(x_prueba)
            tiempo_inferencia = (time.perf_counter() - tiempo_inicio) * 1000

        exactitud = accuracy_score(y_prueba, y_pred)
        puntaje_f1 = f1_score(y_prueba, y_pred, average="weighted", zero_division=0)
        nombre_mostrado = obtener_nombre_mostrado_modelo(nombre)

        print(nombre_mostrado + ":")
        print("  Exactitud (Accuracy):", format(exactitud, ".4f"))
        print("  Puntaje F1 ponderado (Weighted F1):", format(puntaje_f1, ".4f"))
        print(
            "  Tiempo de entrenamiento (Training time):",
            format(tiempo_entrenamiento, ".2f"),
            "ms",
        )
        print(
            "  Tiempo de inferencia (Inference time):",
            format(tiempo_inferencia, ".2f"),
            "ms",
        )
        print()

        codigo_archivo = obtener_codigo_archivo_modelo(nombre)
        ruta_modelo = os.path.join(DIR_MODELOS, "modelo_" + codigo_archivo + ".pkl")
        joblib.dump(
            {
                "modelo": modelo,
                "le_target": codificador_objetivo,
            },
            ruta_modelo,
        )

        resultados[nombre] = {
            "modelo": modelo,
            "le_target": codificador_objetivo,
            "accuracy": round(exactitud, 4),
            "f1_weighted": round(puntaje_f1, 4),
            "tiempo_entrenamiento_ms": round(tiempo_entrenamiento, 2),
            "tiempo_inferencia_ms": round(tiempo_inferencia, 2),
        }

    metricas = {}
    for nombre, datos in resultados.items():
        metricas[nombre] = {
            "accuracy": datos["accuracy"],
            "f1_weighted": datos["f1_weighted"],
            "tiempo_entrenamiento_ms": datos["tiempo_entrenamiento_ms"],
            "tiempo_inferencia_ms": datos["tiempo_inferencia_ms"],
        }

    guardar_json("metricas_modelos", metricas)
    return resultados


def predecir_electrolinera(
    nivel_bateria,
    distancia_m,
    vehiculo_id_enc,
    nombre_modelo="random_forest",
):
    ruta_modelo = os.path.join(DIR_MODELOS, "modelo_" + nombre_modelo + ".pkl")
    if not os.path.exists(ruta_modelo):
        print("Modelo", nombre_modelo, "no encontrado. Entrene primero.")
        return "N/A", 0.0

    paquete = joblib.load(ruta_modelo)
    modelo = paquete["modelo"]
    codificador_objetivo = paquete["le_target"]

    x_nuevo = [[nivel_bateria, distancia_m, vehiculo_id_enc]]

    tiempo_inicio = time.perf_counter()
    prediccion_codificada = modelo.predict(x_nuevo)[0]
    tiempo_ms = (time.perf_counter() - tiempo_inicio) * 1000

    electrolinera_predicha = codificador_objetivo.inverse_transform(
        [prediccion_codificada]
    )[0]

    return electrolinera_predicha, round(tiempo_ms, 3)
