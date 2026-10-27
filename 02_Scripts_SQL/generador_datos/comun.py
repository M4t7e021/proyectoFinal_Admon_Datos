"""
comun.py - Utilidades compartidas por todos los scripts del generador de datos.
Proyecto de Catedra - GimnasioDB
"""
import csv
import os
from datetime import date

# Semilla fija: si se vuelve a ejecutar, se obtienen exactamente los mismos datos.
SEMILLA = 2026

# Periodo de los datos (ver especificacion de CSV)
FECHA_INICIO = date(2025, 1, 1)     # primer dia con datos
FECHA_HOY = date(2026, 10, 25)      # ultimo dia con sesiones "Realizadas"
FECHA_FIN = date(2026, 10, 31)      # ultimo dia con sesiones "Programadas"

# Los CSV se guardan en la carpeta ../datos_csv respecto a este archivo
CARPETA_SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datos_csv")


def escribir_csv(nombre_archivo, encabezado, filas):
    """Guarda una lista de filas en un CSV UTF-8 con encabezado."""
    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    ruta = os.path.join(CARPETA_SALIDA, nombre_archivo)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(encabezado)
        escritor.writerows(filas)
    print(f"  {nombre_archivo}: {len(filas)} filas")


def leer_csv(nombre_archivo):
    """Lee un CSV generado antes y devuelve una lista de diccionarios (columna -> valor en texto)."""
    ruta = os.path.join(CARPETA_SALIDA, nombre_archivo)
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
