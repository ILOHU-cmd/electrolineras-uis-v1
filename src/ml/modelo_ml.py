"""
modelo_ml.py
------------
Módulo de Machine Learning para predicción de electrolinera óptima.

Tarea: Clasificación supervisada
  - Input  : nodo_origen (features), nivel_batería, tipo_vehículo
  - Output : id de la electrolinera que se usará (clase)

Modelos evaluados:
  1. Regresión Logística (baseline)
  2. Random Forest
  3. XGBoost (si está instalado)

Métricas: accuracy, F1-score, tiempo de inferencia vs Dijkstra.

MODIFICACIÓN 2 — Persistencia del modelo (memoria en disco):
  `cargar_o_entrenar()` implementa la lógica de caché:
    1. Si existe `modelo_random_forest.pkl` en data/processed/ → carga.
    2. Si no existe o el usuario fuerza reentrenamiento → entrena y guarda.
  Así el sistema "recuerda" el modelo entre sesiones sin reentrenar
  cada vez que se abre el programa.
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.utils.archivos import leer_csv, guardar_json

try:
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder
    from sklearn.metrics import accuracy_score, f1_score, classification_report
    import joblib
    SK_DISPONIBLE = True
except ImportError:
    SK_DISPONIBLE = False

try:
    from xgboost import XGBClassifier
    XGB_DISPONIBLE = True
except ImportError:
    XGB_DISPONIBLE = False

# Ruta para guardar modelos entrenados
DIR_MODELOS = os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed")
os.makedirs(DIR_MODELOS, exist_ok=True)

# Nombre del modelo principal que se persiste en disco
MODELO_PRINCIPAL = "random_forest"
RUTA_MODELO_PRINCIPAL = os.path.join(DIR_MODELOS, f"modelo_{MODELO_PRINCIPAL}.pkl")


# ─────────────────────────────────────────────────────────────
# MODIFICACIÓN 2 — PERSISTENCIA DEL MODELO (MEMORIA EN DISCO)
# ─────────────────────────────────────────────────────────────

def cargar_o_entrenar(forzar_reentrenamiento: bool = False) -> dict:
    """
    Punto de entrada principal para la Opción [6] del menú.

    Lógica de caché:
      1. Si `forzar_reentrenamiento=False` Y el archivo .pkl existe
         → carga el modelo desde disco (instantáneo, sin reentrenar).
      2. En cualquier otro caso → llama a `entrenar_modelos()`,
         guarda el resultado y lo retorna.

    Parámetros
    ----------
    forzar_reentrenamiento : bool
        Si True, ignora el caché y reentrena desde cero aunque el
        archivo .pkl exista. Útil cuando se agregan nuevos datos de
        simulación.

    Retorna
    -------
    dict
        Mismo formato que `entrenar_modelos()`:
        {nombre_modelo: {modelo, le_target, accuracy, f1, tiempos}}
        Retorna {} si no hay datos suficientes.
    """
    if not SK_DISPONIBLE:
        print("  ⚠  scikit-learn no está instalado.")
        return {}

    # ── RAMA 1: intentar cargar desde disco ──────────────────
    if not forzar_reentrenamiento and os.path.exists(RUTA_MODELO_PRINCIPAL):
        try:
            paquete = joblib.load(RUTA_MODELO_PRINCIPAL)
            modelo    = paquete["modelo"]
            le_target = paquete["le_target"]
            metricas  = paquete.get("metricas", {})

            print(f"\n  ✅ Modelo cargado desde disco:")
            print(f"     Archivo  : {RUTA_MODELO_PRINCIPAL}")
            print(f"     Tipo     : {type(modelo).__name__}")
            print(f"     Clases   : {list(le_target.classes_)}")
            if metricas:
                print(f"     Accuracy : {metricas.get('accuracy', 'N/A')}")
                print(f"     F1       : {metricas.get('f1_weighted', 'N/A')}")
            print(f"\n  💡 Para reentrenar use: cargar_o_entrenar(forzar_reentrenamiento=True)")

            return {
                MODELO_PRINCIPAL: {
                    "modelo":    modelo,
                    "le_target": le_target,
                    **metricas,
                }
            }
        except Exception as e:
            # El archivo existe pero está corrupto → reentrenar
            print(f"  ⚠  Error al cargar modelo desde disco: {e}")
            print(f"  ↺  Reentrenando desde cero...\n")

    # ── RAMA 2: entrenar desde cero ───────────────────────────
    if forzar_reentrenamiento:
        print("\n  🔄 Reentrenamiento forzado por el usuario.\n")
    else:
        print(f"\n  ℹ  No se encontró modelo en disco ({RUTA_MODELO_PRINCIPAL}).")
        print(f"  🔧 Entrenando nuevo modelo...\n")

    resultados = entrenar_modelos()

    # Enriquecer el .pkl del modelo principal con métricas
    # (entrenar_modelos ya guarda el pkl, aquí solo añadimos métricas)
    if MODELO_PRINCIPAL in _normalizar_claves(resultados):
        clave_real = _clave_real(resultados, MODELO_PRINCIPAL)
        datos = resultados[clave_real]
        metricas_guardadas = {
            "accuracy":                datos.get("accuracy"),
            "f1_weighted":             datos.get("f1_weighted"),
            "tiempo_entrenamiento_ms": datos.get("tiempo_entrenamiento_ms"),
            "tiempo_inferencia_ms":    datos.get("tiempo_inferencia_ms"),
        }
        # Reescribir pkl incluyendo métricas para futuras cargas
        joblib.dump(
            {
                "modelo":    datos["modelo"],
                "le_target": datos["le_target"],
                "metricas":  metricas_guardadas,
            },
            RUTA_MODELO_PRINCIPAL,
        )

    return resultados


def _normalizar_claves(d: dict) -> dict:
    """Devuelve un dict con claves normalizadas a minúsculas sin tildes."""
    return {
        k.lower()
         .replace(" ", "_")
         .replace("ó", "o")
         .replace("é", "e")
         .replace("ú", "u"): k
        for k in d
    }


def _clave_real(d: dict, nombre_normalizado: str) -> str | None:
    """Retorna la clave original del dict dado su nombre normalizado."""
    mapa = _normalizar_claves(d)
    return mapa.get(nombre_normalizado)


# ─────────────────────────────────────────────────────────────
# PREPARAR DATASET DESDE HISTORIAL DE RECARGAS
# ─────────────────────────────────────────────────────────────
def preparar_dataset() -> tuple:
    """
    Carga el historial de recargas y construye el dataset de entrenamiento.

    Features (X):
      - nivel_bateria_llegada (float)
      - distancia_recorrida_m (float)
      - vehiculo_id_enc       (int, codificado)

    Target (y):
      - electrolinera_id (string → int codificado)

    Retorna
    -------
    tuple (X, y, le_target) donde le_target es el LabelEncoder de la clase.
    None si no hay datos suficientes.
    """
    if not SK_DISPONIBLE:
        print("  ⚠  scikit-learn no está instalado.")
        return None

    filas = leer_csv("historial_recargas")
    if len(filas) < 20:
        print(f"  ⚠  Dataset insuficiente: {len(filas)} registros. "
              f"Se necesitan al menos 20. Ejecute más simulaciones.")
        return None

    df = pd.DataFrame(filas)
    df["nivel_bateria_llegada"] = pd.to_numeric(df["nivel_bateria_llegada"], errors="coerce")
    df["distancia_recorrida_m"] = pd.to_numeric(df["distancia_recorrida_m"], errors="coerce")
    df = df.dropna()

    # Codificar vehículo
    le_vehiculo = LabelEncoder()
    df["vehiculo_enc"] = le_vehiculo.fit_transform(df["vehiculo_id"])

    # Codificar target (electrolinera)
    le_target = LabelEncoder()
    df["target"] = le_target.fit_transform(df["electrolinera_id"])

    X = df[["nivel_bateria_llegada", "distancia_recorrida_m", "vehiculo_enc"]].values
    y = df["target"].values

    print(f"  ✓  Dataset: {len(df)} registros | {len(le_target.classes_)} clases")
    return X, y, le_target


# ─────────────────────────────────────────────────────────────
# ENTRENAR MODELOS
# ─────────────────────────────────────────────────────────────
def entrenar_modelos() -> dict:
    """
    Entrena y evalúa todos los modelos disponibles.

    Retorna
    -------
    dict
        {nombre_modelo: {modelo, accuracy, f1, tiempo_entrenamiento_ms}}
    """
    resultado = preparar_dataset()
    if resultado is None:
        return {}

    X, y, le_target = resultado

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y if len(set(y)) > 1 else None
    )

    modelos_config = {
        "Regresión Logística": LogisticRegression(max_iter=500, random_state=42),
        "Random Forest":       RandomForestClassifier(n_estimators=100, random_state=42),
    }
    if XGB_DISPONIBLE:
        modelos_config["XGBoost"] = XGBClassifier(
            n_estimators=100, use_label_encoder=False,
            eval_metric="mlogloss", random_state=42, verbosity=0
        )

    resultados = {}
    print("\n  🤖 Entrenando modelos...\n")

    for nombre, modelo in modelos_config.items():
        t_inicio = time.perf_counter()
        modelo.fit(X_train, y_train)
        t_entrenamiento = (time.perf_counter() - t_inicio) * 1000

        t_inf = time.perf_counter()
        y_pred = modelo.predict(X_test)
        t_inferencia = (time.perf_counter() - t_inf) * 1000

        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)

        print(f"  {nombre}:")
        print(f"    Accuracy   : {acc:.4f}")
        print(f"    F1 (weighted): {f1:.4f}")
        print(f"    Entrenamiento: {t_entrenamiento:.1f} ms")
        print(f"    Inferencia   : {t_inferencia:.2f} ms\n")

        # Guardar modelo en disco
        nombre_archivo = nombre.lower().replace(" ", "_").replace("ó", "o")
        ruta_modelo = os.path.join(DIR_MODELOS, f"modelo_{nombre_archivo}.pkl")
        joblib.dump({"modelo": modelo, "le_target": le_target}, ruta_modelo)

        resultados[nombre] = {
            "modelo": modelo,
            "le_target": le_target,
            "accuracy": round(acc, 4),
            "f1_weighted": round(f1, 4),
            "tiempo_entrenamiento_ms": round(t_entrenamiento, 2),
            "tiempo_inferencia_ms": round(t_inferencia, 2),
        }

    # Guardar métricas comparativas
    metricas = {
        k: {kk: vv for kk, vv in v.items() if kk != "modelo" and kk != "le_target"}
        for k, v in resultados.items()
    }
    guardar_json("metricas_modelos", metricas)

    return resultados


# ─────────────────────────────────────────────────────────────
# PREDICCIÓN CON MODELO GUARDADO
# ─────────────────────────────────────────────────────────────
def predecir_electrolinera(nivel_bateria: float,
                            distancia_m: float,
                            vehiculo_id_enc: int,
                            nombre_modelo: str = "random_forest") -> str:
    """
    Predice la electrolinera más probable dado el estado del vehículo.

    Retorna
    -------
    str
        ID de la electrolinera predicha (ej: 'E3'), o 'N/A' si falla.
    """
    ruta_modelo = os.path.join(DIR_MODELOS, f"modelo_{nombre_modelo}.pkl")
    if not os.path.exists(ruta_modelo):
        print(f"  ⚠  Modelo '{nombre_modelo}' no encontrado. Entrene primero.")
        return "N/A"

    paquete = joblib.load(ruta_modelo)
    modelo = paquete["modelo"]
    le_target = paquete["le_target"]

    X_nuevo = [[nivel_bateria, distancia_m, vehiculo_id_enc]]

    t_inicio = time.perf_counter()
    pred_enc = modelo.predict(X_nuevo)[0]
    t_ms = (time.perf_counter() - t_inicio) * 1000

    electrolinera_pred = le_target.inverse_transform([pred_enc])[0]
    print(f"  ✓  Predicción ML: {electrolinera_pred} ({t_ms:.3f} ms)")
    return electrolinera_pred