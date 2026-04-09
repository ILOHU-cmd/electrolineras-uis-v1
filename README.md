# ⚡ Sistema de Electrolineras — Área Metropolitana de Bucaramanga

> **Proyecto de Aula · Semestre 2026-1**  
> Asignaturas: *Algoritmos y Programación* · *Matemáticas Discretas*  
> Universidad Industrial de Santander (UIS) — Facultad de Ingeniería en Ciencia de Datos

---

## Descripción general

Este sistema modela la red vial del área metropolitana de Bucaramanga como un
**grafo ponderado dirigido** (usando OSMnx y NetworkX), simula recorridos de
vehículos eléctricos de alta y baja gama, y aplica técnicas de **Machine Learning**
supervisado para predecir qué electrolinera usará un vehículo dado su estado de
batería, sin necesidad de ejecutar Dijkstra en cada consulta.

```
Problema real → Grafo ponderado G=(V,E,w) → Dijkstra → Dataset → Random Forest
```

---

## Estructura del proyecto

```
electrolineras/
├── main.py                        # Punto de entrada — ejecute este archivo
├── requirements.txt               # Dependencias Python
├── README.md                      # Este documento
│
├── data/
│   ├── datos_estaticos.py         # Electrolineras, puntos de referencia y vehículos
│   ├── raw/                       # Caché del grafo OSM (.graphml) — se genera al correr
│   ├── processed/                 # Modelos ML serializados (.pkl)
│   └── output/                    # CSV, JSON, XLSX y mapas HTML generados
│
└── src/
    ├── ui/
    │   └── menu.py                # Menú interactivo (bucle while centinela)
    ├── grafo/
    │   ├── constructor_grafo.py   # Descarga/carga grafo OSM + etiqueta nodos especiales
    │   ├── algoritmos_grafo.py    # Dijkstra (NetworkX + implementación manual) y Floyd-Warshall
    │   └── visualizacion.py       # Mapas Folium interactivos y gráficos Matplotlib
    ├── simulacion/
    │   └── simulacion.py          # Clase Vehiculo + bucle de simulación + trazabilidad de ruta
    ├── ml/
    │   └── modelo_ml.py           # Random Forest, Logistic Regression, XGBoost + persistencia
    └── utils/
        ├── validacion.py          # Validación de entradas (negativos, rango, caracteres)
        └── archivos.py            # Lectura/escritura TXT · CSV · JSON · XLSX
```

---

## Instalación

### Requisitos previos

- Python **3.11** o superior
- `pip` actualizado (`pip install --upgrade pip`)
- Conexión a internet la primera vez (para descargar el grafo de OpenStreetMap)

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/ILOHU-cmd/electrolineras-uis-v1.git
cd electrolineras-uis-v1

# 2. (Recomendado) Crear entorno virtual
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar el sistema
python main.py
```

> **Nota para entornos ARM64 (Termux / tablet):** si la instalación de
> `osmnx` falla, instale primero `shapely` y `fiona` con conda o wheels
> precompilados. El sistema incluye un **grafo sintético de respaldo**
> que permite probar todas las funciones sin conexión.

---

## Uso del sistema — Tutorial para el evaluador

Al ejecutar `python main.py` aparece el menú principal:

```
╔══════════════════════════════════════════════════════════════╗
║   ⚡ SISTEMA DE ELECTROLINERAS - BUCARAMANGA  2026-1        ║
║   UIS · Algoritmos y Programación · Matemáticas Discretas   ║
╚══════════════════════════════════════════════════════════════╝

  Grafo: ✗ No cargado  |  Simulación: ✗ Sin datos  |  ML: ✗ Sin entrenar

   [1]  Cargar / Construir grafo vial
   [2]  Ver electrolineras y puntos de referencia
   [3]  Ejecutar simulación de recorridos
   [4]  Ver resumen estadístico de la simulación
   [5]  Generar mapa interactivo (Folium HTML)
   [6]  Entrenar modelo de Machine Learning
   [7]  Predecir electrolinera con ML
   [8]  Exportar datos a Excel (.xlsx)
   [9]  Comparar Dijkstra vs ML (métricas)
   [0]  Salir
```

### Flujo recomendado (primera ejecución)

| Paso | Opción | Qué hace |
|------|--------|----------|
| 1 | `[1]` | Descarga la red vial de Bucaramanga desde OpenStreetMap y la guarda en caché |
| 2 | `[2]` | Lista las 8 electrolineras, 10 puntos de referencia y 2 vehículos |
| 3 | `[3]` | Ejecuta la simulación (se recomienda ≥ 50 recorridos para ML) |
| 4 | `[4]` | Muestra estadísticas y genera gráfico de barras por electrolinera |
| 5 | `[5]` | Genera `mapa_electrolineras.html` — ábralo en cualquier navegador |
| 6 | `[6]` | Entrena Random Forest / XGBoost y **guarda el modelo en disco** |
| 7 | `[7]` | Predice electrolinera en microsegundos sin Dijkstra |
| 8 | `[8]` | Exporta historial completo a `.xlsx` |
| 9 | `[9]` | Tabla comparativa de precisión y tiempo (ML vs Dijkstra) |

---

## Características técnicas destacadas

### 1. Trazabilidad de nodos — Historial detallado de ruta

Cuando se ejecuta la simulación con una **semilla fija** (reproducible),
el sistema imprime el recorrido calle por calle:

```
python main.py
→ Opción [3] → recorridos: 5 → semilla: 1
```

Salida esperada:

```
  ──────────────────────────────────────────────────────────────
  RECORRIDO #1 | Tesla Model 3 LR | UIS Campus Central → UNAB
  ──────────────────────────────────────────────────────────────
  Paso      Nodo OSM  Calle                           Parcial     Acum.
  ──────────────────────────────────────────────────────────────
     1  📍 3245871012  ─                               origen    0.0m
     2       987654321  Carrera 27                      142.3m    142.3m
     3       123456789  Calle 9                          89.7m    232.0m
     ...
    47  📍  456789012  Calle 45                         55.1m   4821.4m  → UNAB
  ──────────────────────────────────────────────────────────────
  Distancia total: 4821.4 m  (4.821 km) | Nodos recorridos: 47
```

Los iconos `📍` marcan puntos de referencia y `⚡` marca electrolineras.
El historial completo también se guarda en `estadisticas["recorridos"][n]["historial_ruta"]`.

**Funciones involucradas** (`src/simulacion/simulacion.py`):

```python
# Construye el historial a partir de los nodos de Dijkstra
historial = trazar_historial_ruta(G, ruta_nodos)

# Lo imprime en consola con formato tabular
imprimir_historial_ruta(historial, titulo="RECORRIDO #1 | ...")
```

---

### 2. Persistencia del modelo ML — Memoria entre sesiones

El modelo entrenado se **guarda automáticamente** en
`data/processed/modelo_random_forest.pkl` al usar la opción `[6]`.
En sesiones posteriores, el sistema lo **carga en menos de 1 segundo**
sin reentrenar.

```
Segunda ejecución → Opción [6]:

  ℹ  Se encontró un modelo guardado en disco.
  ¿Desea REENTRENAR el modelo con los datos actuales? [s/n]: n

  ✅ Modelo cargado desde disco:
     Archivo  : .../data/processed/modelo_random_forest.pkl
     Tipo     : RandomForestClassifier
     Clases   : ['E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8']
     Accuracy : 0.8750
     F1       : 0.8612
```

Para forzar reentrenamiento (cuando se agregan nuevos datos de simulación):

```
  ¿Desea REENTRENAR el modelo con los datos actuales? [s/n]: s
  🔄 Reentrenamiento forzado por el usuario.
  🤖 Entrenando modelos...
```

**Función involucrada** (`src/ml/modelo_ml.py`):

```python
# Carga desde disco si existe; entrena desde cero si no existe
# o si forzar_reentrenamiento=True
resultados = cargar_o_entrenar(forzar_reentrenamiento=False)
```

El archivo `.pkl` contiene un diccionario con tres llaves:

```python
{
    "modelo":    RandomForestClassifier(...),   # objeto sklearn entrenado
    "le_target": LabelEncoder(...),             # mapeo clase → ID electrolinera
    "metricas":  {"accuracy": 0.875, ...}       # para mostrar al cargar
}
```

---

## Vehículos seleccionados

| ID | Modelo | Gama | Batería | Autonomía real | Consumo |
|----|--------|------|---------|----------------|---------|
| V1 | Tesla Model 3 Long Range | Alta | 82 kWh | 602 km | 13.6 kWh/100km |
| V2 | BYD Seagull Std Range | Baja | 38.8 kWh | 405 km | 9.6 kWh/100km |

Fuente: [ev-database.org](https://ev-database.org/cheatsheet/range-electric-car)

---

## Electrolineras del sistema

| ID | Nombre | Potencia |
|----|--------|----------|
| E1 | Homecenter Bucaramanga | 50 kW |
| E2 | C.C. Quinta Etapa | 22 kW |
| E3 | C.C. Cacique | 50 kW |
| E4 | C.C. Canaveral | 22 kW |
| E5 | Estación Terpel Piedecuesta | 50 kW |
| E6 | Éxito de La Rosita | 22 kW |
| E7 | C.C. La Florida | 22 kW |
| E8 | Promotores del Oriente (vía a Girón) | 50 kW |

---

## Requisitos de la rúbrica — Verificación

| Criterio | Archivo | Función / Sección |
|----------|---------|-------------------|
| Código modular (una función por funcionalidad) | todos los módulos | cada función es atómica |
| Validación de entradas (negativos, rango, caracteres) | `utils/validacion.py` | `leer_entero`, `leer_flotante`, `leer_texto` |
| Estructuras homogéneas (listas, dicts, arrays) | `simulacion.py`, `modelo_ml.py` | `historial_recargas`, `estadisticas`, `X` (numpy array) |
| Ciclo `while` controlado por centinela | `menu.py`, `simulacion.py` | `while opcion != "0"`, `while i < n_recorridos` |
| Lectura y escritura de archivos `.csv` | `utils/archivos.py` | `guardar_csv`, `leer_csv` |
| Lectura y escritura de archivos `.json` | `utils/archivos.py` | `guardar_json`, `leer_json` |
| Lectura y escritura de archivos `.xlsx` | `utils/archivos.py` | `guardar_xlsx` |
| Lectura y escritura de archivos `.txt` | `utils/archivos.py` | `guardar_txt`, `leer_txt` |
| Menú interactivo de opciones | `ui/menu.py` | clase `Menu` |
| Teoría de grafos (Dijkstra) | `grafo/algoritmos_grafo.py` | `dijkstra`, `electrolinera_mas_cercana` |
| Algoritmos de ML | `ml/modelo_ml.py` | `entrenar_modelos`, `cargar_o_entrenar` |
| Visualización | `grafo/visualizacion.py` | `generar_mapa_folium`, `grafico_uso_electrolineras` |

---

## Dependencias

```
osmnx>=1.9.1          # Red vial OpenStreetMap
networkx>=3.3          # Manipulación de grafos
numpy>=1.26.0          # Arrays numéricos
pandas>=2.2.0          # DataFrames
scikit-learn>=1.4.0    # Modelos ML
xgboost>=2.0.0         # Gradient Boosting
joblib>=1.3.0          # Serialización de modelos
matplotlib>=3.8.0      # Gráficos estáticos
folium>=0.16.0         # Mapas interactivos HTML
openpyxl>=3.1.0        # Archivos Excel
```

---

## Autores

Proyecto desarrollado como trabajo individual — Semestre 2026-1  
Universidad Industrial de Santander · Escuela de Ingeniería de Sistemas  
Facultad de Ingeniería en Ciencia de Datos

---

## Licencia

Uso académico exclusivo — UIS 2026-1
