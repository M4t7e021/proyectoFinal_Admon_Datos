"""
07_asistencias.py - Genera asistencias.csv (una fila por reserva Confirmada de una sesion Realizada).

Lee reservas.csv y sesiones.csv (pasos 5 y 6).

Reglas (ver especificacion de CSV):
  - Solo hay asistencia para reservas 'Confirmada' de sesiones 'Realizada'
    (no para reservas canceladas ni para sesiones programadas o canceladas)
  - ReservaID no se repite
  - Asistio = 1 en aprox. 80 % de los casos
  - Si Asistio = 1, FechaCheckIn va entre 15 minutos antes y 10 minutos despues del inicio de la sesion
  - Si Asistio = 0, FechaCheckIn queda vacia (NULL)
"""
import random
from datetime import datetime, timedelta
from comun import SEMILLA, escribir_csv, leer_csv

rng = random.Random(SEMILLA + 7)

reservas = leer_csv("reservas.csv")
sesiones = {s["SesionID"]: s for s in leer_csv("sesiones.csv")}

# Cada socio tiene su propia tendencia a asistir: la mayoria casi siempre va, algunos faltan mucho.
# betavariate(8, 2) tiene media 0.8, que es el 80 % de asistencia buscado.
tendencia = {}


def probabilidad_de_asistir(socio_id):
    if socio_id not in tendencia:
        tendencia[socio_id] = rng.betavariate(8, 2)
    return tendencia[socio_id]


filas = []
for r in reservas:                                   # ya vienen ordenadas por ReservaID
    s = sesiones[r["SesionID"]]
    if r["Estado"] != "Confirmada" or s["Estado"] != "Realizada":
        continue

    asistio = rng.random() < probabilidad_de_asistir(r["SocioID"])
    if asistio:
        inicio = datetime.strptime(s["FechaHora"], "%Y-%m-%d %H:%M:%S")
        # Casi todos llegan unos minutos antes; unos pocos, un poco tarde
        minutos = rng.triangular(-15, 10, -5)
        checkin = (inicio + timedelta(seconds=int(minutos * 60))).strftime("%Y-%m-%d %H:%M:%S")
        filas.append((int(r["ReservaID"]), checkin, 1))
    else:
        filas.append((int(r["ReservaID"]), "", 0))     # sin check-in: campo vacio

print("Generando asistencias...")
escribir_csv("asistencias.csv", ["ReservaID", "FechaCheckIn", "Asistio"], filas)

# ----------------------------------------------------------------------
# Resumen de control
# ----------------------------------------------------------------------
print("  Resumen de control:")
n1 = sum(1 for f in filas if f[2] == 1)
print(f"    Asistio = 1: {n1} ({n1 / len(filas):.1%})")
print(f"    Asistio = 0: {len(filas) - n1} ({(len(filas) - n1) / len(filas):.1%})")
print(f"    Check-in vacios: {sum(1 for f in filas if f[1] == '')}")
sin_fila = sum(1 for r in reservas if r["Estado"] == "Confirmada" and sesiones[r["SesionID"]]["Estado"] != "Realizada")
print(f"    Reservas Confirmadas sin asistencia (sesion aun no realizada): {sin_fila}")
estado_reserva = {int(r["ReservaID"]): r["Estado"] for r in reservas}
print(f"    Asistencias de reservas Canceladas: {sum(1 for f in filas if estado_reserva[f[0]] == 'Cancelada')}")
print(f"    ReservaID repetidos: {len(filas) - len({f[0] for f in filas})}")
