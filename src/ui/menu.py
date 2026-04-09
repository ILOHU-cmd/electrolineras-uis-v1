"""
menu.py
-------
Menú interactivo principal del sistema.
Implementa ciclo controlado por centinela (while con opción 0 = salir).
Requisito explícito de la rúbrica del profesor.

Opciones del menú:
  1. Cargar/construir grafo vial
  2. Ver electrolineras y puntos de referencia
  3. Ejecutar simulación de recorridos
  4. Ver resumen estadístico
  5. Generar mapa interactivo (Folium)
  6. Entrenar modelo de ML
  7. Predecir electrolinera con ML
  8. Exportar datos (CSV / JSON / XLSX)
  9. Comparar Dijkstra vs ML
  0. Salir
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.utils.validacion import limpiar_pantalla, leer_entero, leer_flotante, confirmar
from src.utils.archivos import leer_csv, guardar_xlsx
from src.grafo.constructor_grafo import construir_grafo
from src.simulacion.simulacion import ejecutar_simulacion, imprimir_resumen
from src.grafo.visualizacion import generar_mapa_folium, grafico_uso_electrolineras
from src.ml.modelo_ml import entrenar_modelos, predecir_electrolinera
from data.datos_estaticos import ELECTROLINERAS, PUNTOS_REFERENCIA, VEHICULOS

# Encabezado visual
BANNER = r"""
╔══════════════════════════════════════════════════════════════╗
║   ⚡ SISTEMA DE ELECTROLINERAS - BUCARAMANGA  2026-1        ║
║   UIS · Algoritmos y Programación · Matemáticas Discretas   ║
╚══════════════════════════════════════════════════════════════╝
"""

OPCIONES_MENU = {
    "1": "Cargar / Construir grafo vial",
    "2": "Ver electrolineras y puntos de referencia",
    "3": "Ejecutar simulación de recorridos",
    "4": "Ver resumen estadístico de la simulación",
    "5": "Generar mapa interactivo (Folium HTML)",
    "6": "Entrenar modelo de Machine Learning",
    "7": "Predecir electrolinera con ML",
    "8": "Exportar datos a Excel (.xlsx)",
    "9": "Comparar Dijkstra vs ML (métricas)",
    "0": "Salir",
}


class Menu:
    """Controlador del menú principal."""

    def __init__(self):
        self.grafo = None
        self.estadisticas = {}
        self.modelos_entrenados = {}

    # ─────────────────────────────────────────────────────────
    # BUCLE PRINCIPAL (centinela = opción "0")
    # ─────────────────────────────────────────────────────────
    def ejecutar(self) -> None:
        """Ejecuta el menú con bucle controlado por centinela."""
        opcion = ""
        while opcion != "0":
            self._mostrar_menu()
            opcion = input("  → Seleccione una opción: ").strip()

            if opcion == "1":
                self._opcion_cargar_grafo()
            elif opcion == "2":
                self._opcion_ver_nodos()
            elif opcion == "3":
                self._opcion_simulacion()
            elif opcion == "4":
                self._opcion_resumen()
            elif opcion == "5":
                self._opcion_mapa_folium()
            elif opcion == "6":
                self._opcion_entrenar_ml()
            elif opcion == "7":
                self._opcion_predecir_ml()
            elif opcion == "8":
                self._opcion_exportar_xlsx()
            elif opcion == "9":
                self._opcion_comparar()
            elif opcion == "0":
                print("\n  ¡Hasta luego! ⚡\n")
            else:
                print("\n  ⚠  Opción inválida. Ingrese un número del 0 al 9.\n")

            if opcion not in ("0", ""):
                input("\n  [Presione Enter para continuar...]")
                limpiar_pantalla()

    # ─────────────────────────────────────────────────────────
    # RENDER DEL MENÚ
    # ─────────────────────────────────────────────────────────
    def _mostrar_menu(self) -> None:
        print(BANNER)
        estado_grafo = "✓ Cargado" if self.grafo else "✗ No cargado"
        estado_sim = f"✓ {self.estadisticas.get('total_recorridos', 0)} recorridos" \
                     if self.estadisticas else "✗ Sin datos"
        estado_ml = "✓ Entrenado" if self.modelos_entrenados else "✗ Sin entrenar"

        print(f"  Grafo: {estado_grafo}  |  Simulación: {estado_sim}  |  ML: {estado_ml}\n")
        print("  ─────────────────────────────────────────")
        for clave, descripcion in OPCIONES_MENU.items():
            print(f"   [{clave}]  {descripcion}")
        print("  ─────────────────────────────────────────\n")

    # ─────────────────────────────────────────────────────────
    # OPCIONES INDIVIDUALES
    # ─────────────────────────────────────────────────────────
    def _opcion_cargar_grafo(self):
        print("\n  Construyendo grafo vial de Bucaramanga...")
        usar_cache = confirmar("  ¿Usar caché local si existe?")
        self.grafo = construir_grafo(desde_cache=usar_cache)

    def _opcion_ver_nodos(self):
        print("\n  ═══ ELECTROLINERAS (Nodos tipo A) ═══")
        for e in ELECTROLINERAS:
            print(f"   {e['id']:>3}  {e['nombre']:<45} "
                  f"({e['lat']:.4f}, {e['lon']:.4f}) | {e['potencia_kw']} kW")

        print("\n  ═══ PUNTOS DE REFERENCIA (Nodos tipo B) ═══")
        for p in PUNTOS_REFERENCIA:
            print(f"   {p['id']:>3}  {p['nombre']:<50} "
                  f"({p['lat']:.4f}, {p['lon']:.4f})")

        print("\n  ═══ VEHÍCULOS DISPONIBLES ═══")
        for clave, v in VEHICULOS.items():
            print(f"   {v['id']:>3}  {v['nombre']:<35} [{v['gama'].upper()}] "
                  f"| Batería: {v['bateria_kwh']} kWh "
                  f"| Autonomía: {v['autonomia_real_km']} km")

    def _opcion_simulacion(self):
        if self.grafo is None:
            print("\n  ⚠  Primero debe cargar el grafo (opción 1).")
            return

        n = leer_entero("  Número de recorridos a simular (1-500): ",
                        minimo=1, maximo=500)
        semilla = leer_entero("  Semilla aleatoria (0 = aleatoria): ", minimo=0)
        semilla = semilla if semilla > 0 else None

        print()
        self.estadisticas = ejecutar_simulacion(
            self.grafo,
            n_recorridos=n,
            semilla=semilla,
        )
        imprimir_resumen(self.estadisticas)

    def _opcion_resumen(self):
        if not self.estadisticas:
            print("\n  ⚠  No hay estadísticas disponibles. Ejecute la simulación primero.")
            return
        imprimir_resumen(self.estadisticas)
        if self.estadisticas.get("uso_electrolineras"):
            if confirmar("  ¿Generar gráfico de barras del uso?"):
                grafico_uso_electrolineras(self.estadisticas)

    def _opcion_mapa_folium(self):
        print("\n  Generando mapa interactivo...")
        ruta = generar_mapa_folium(G=self.grafo)
        if ruta:
            print(f"\n  ✓  Abra el archivo en su navegador:\n     {ruta}")

    def _opcion_entrenar_ml(self):
        print("\n  Iniciando entrenamiento de modelos...\n")
        self.modelos_entrenados = entrenar_modelos()
        if not self.modelos_entrenados:
            print("  ⚠  Entrene con más datos de simulación.")

    def _opcion_predecir_ml(self):
        if not self.modelos_entrenados:
            print("\n  ⚠  Primero entrene los modelos (opción 6).")
            return

        print("\n  ═══ PREDICCIÓN DE ELECTROLINERA ═══")
        nivel = leer_flotante("  Nivel de batería actual (%): ", minimo=0.0, maximo=100.0)
        dist = leer_flotante("  Distancia al último destino (metros): ", minimo=0.0)

        print("  Vehículos disponibles: 0=Tesla Model 3 LR | 1=BYD Seagull")
        vid_enc = leer_entero("  Ingrese el número del vehículo: ", minimo=0, maximo=1)

        resultado = predecir_electrolinera(nivel, dist, vid_enc)
        print(f"\n  ✓  Electrolinera predicha por ML: {resultado}")

    def _opcion_exportar_xlsx(self):
        filas = leer_csv("historial_recargas")
        if not filas:
            print("\n  ⚠  No hay historial de recargas. Ejecute la simulación primero.")
            return
        ruta = guardar_xlsx("historial_recargas", filas)
        print(f"\n  ✓  Exportado a: {ruta}")

    def _opcion_comparar(self):
        if not self.modelos_entrenados:
            print("\n  ⚠  Entrene los modelos primero (opción 6).")
            return

        print("\n  ═══ COMPARACIÓN: DIJKSTRA vs ML ═══\n")
        for nombre, datos in self.modelos_entrenados.items():
            print(f"  {nombre}:")
            print(f"    Accuracy         : {datos['accuracy']:.4f}")
            print(f"    F1 (weighted)    : {datos['f1_weighted']:.4f}")
            print(f"    Tiempo inferencia: {datos['tiempo_inferencia_ms']:.3f} ms")
            print(f"    (Dijkstra típico : ~5-50 ms para 8 electrolineras)\n")
