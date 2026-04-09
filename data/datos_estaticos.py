"""
datos_estaticos.py
------------------
Datos base del sistema: electrolineras, puntos de referencia
y vehículos eléctricos seleccionados para la simulación.
Los vehículos fueron seleccionados de ev-database.org:
  - Alta gama : Tesla Model 3 Long Range
  - Baja gama  : BYD Seagull
"""

# ─────────────────────────────────────────────────────────────
# ELECTROLINERAS (nodos tipo A)
# ─────────────────────────────────────────────────────────────
ELECTROLINERAS = [
    {
        "id": "E1",
        "nombre": "Homecenter Bucaramanga",
        "lat": 7.1218,
        "lon": -73.1198,
        "potencia_kw": 50,
        "tipo": "electrolinera",
    },
    {
        "id": "E2",
        "nombre": "Centro Comercial Quinta Etapa",
        "lat": 7.1050,
        "lon": -73.1100,
        "potencia_kw": 22,
        "tipo": "electrolinera",
    },
    {
        "id": "E3",
        "nombre": "Centro Comercial Cacique",
        "lat": 7.1157,
        "lon": -73.1068,
        "potencia_kw": 50,
        "tipo": "electrolinera",
    },
    {
        "id": "E4",
        "nombre": "Centro Comercial Canaveral",
        "lat": 7.0948,
        "lon": -73.1098,
        "potencia_kw": 22,
        "tipo": "electrolinera",
    },
    {
        "id": "E5",
        "nombre": "Estación Terpel Piedecuesta",
        "lat": 6.9900,
        "lon": -73.0500,
        "potencia_kw": 50,
        "tipo": "electrolinera",
    },
    {
        "id": "E6",
        "nombre": "Éxito de La Rosita",
        "lat": 7.0759,
        "lon": -73.1238,
        "potencia_kw": 22,
        "tipo": "electrolinera",
    },
    {
        "id": "E7",
        "nombre": "Centro Comercial La Florida",
        "lat": 7.1380,
        "lon": -73.1248,
        "potencia_kw": 22,
        "tipo": "electrolinera",
    },
    {
        "id": "E8",
        "nombre": "Promotores del Oriente (vía a Girón)",
        "lat": 7.0720,
        "lon": -73.1650,
        "potencia_kw": 50,
        "tipo": "electrolinera",
    },
]

# ─────────────────────────────────────────────────────────────
# PUNTOS DE REFERENCIA / ORIGEN (nodos tipo B)
# ─────────────────────────────────────────────────────────────
PUNTOS_REFERENCIA = [
    {
        "id": "P1",
        "nombre": "UIS Campus Central",
        "lat": 7.1398,
        "lon": -73.1227,
        "tipo": "referencia",
    },
    {
        "id": "P2",
        "nombre": "UIS Campus Florida",
        "lat": 7.1372,
        "lon": -73.1261,
        "tipo": "referencia",
    },
    {
        "id": "P3",
        "nombre": "UIS Parque Tecnológico Guatiguará",
        "lat": 6.9935,
        "lon": -73.0540,
        "tipo": "referencia",
    },
    {
        "id": "P4",
        "nombre": "UIS Campus Bucarica (Centro)",
        "lat": 7.1186,
        "lon": -73.1228,
        "tipo": "referencia",
    },
    {
        "id": "P5",
        "nombre": "CENFER",
        "lat": 7.1290,
        "lon": -73.1250,
        "tipo": "referencia",
    },
    {
        "id": "P6",
        "nombre": "UNAB",
        "lat": 7.1189,
        "lon": -73.1060,
        "tipo": "referencia",
    },
    {
        "id": "P7",
        "nombre": "UTS",
        "lat": 7.1208,
        "lon": -73.1219,
        "tipo": "referencia",
    },
    {
        "id": "P8",
        "nombre": "UPB",
        "lat": 7.1075,
        "lon": -73.1119,
        "tipo": "referencia",
    },
    {
        "id": "P9",
        "nombre": "PTAR Río Frío",
        "lat": 7.1500,
        "lon": -73.1280,
        "tipo": "referencia",
    },
    {
        "id": "P10",
        "nombre": "Sede Recreacional Catay",
        "lat": 7.0850,
        "lon": -73.1050,
        "tipo": "referencia",
    },
]

# ─────────────────────────────────────────────────────────────
# VEHÍCULOS ELÉCTRICOS (fuente: ev-database.org)
# ─────────────────────────────────────────────────────────────
VEHICULOS = {
    "tesla_model3_lr": {
        "id": "V1",
        "nombre": "Tesla Model 3 Long Range",
        "gama": "alta",
        "bateria_kwh": 82.0,         # Capacidad total útil en kWh
        "autonomia_real_km": 602.0,  # Autonomía WLTP real aprox.
        "consumo_kwh_100km": 13.6,   # kWh por cada 100 km
        "carga_maxima_kw": 170.0,    # Velocidad máx. de carga DC
    },
    "byd_seagull": {
        "id": "V2",
        "nombre": "BYD Seagull (Std Range)",
        "gama": "baja",
        "bateria_kwh": 38.8,
        "autonomia_real_km": 405.0,
        "consumo_kwh_100km": 9.6,
        "carga_maxima_kw": 30.0,
    },
}
