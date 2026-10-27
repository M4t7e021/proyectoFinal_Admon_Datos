"""
04_pagos.py - Genera pagos.csv (aprox. 10.000 pagos).

Lee membresias.csv y planes.csv (pasos 1 y 3).

Como se arma cada membresia:
  - El precio del plan se divide en cuotas (1 a 4, segun el plan). Las cuotas suman exactamente el precio.
  - La primera cuota se paga alrededor de la FechaInicio y las demas cada cierto numero de dias.
  - Solo se registran cuotas con fecha hasta 2026-10-25 (nunca pagos futuros).
  - Algunas cuotas quedan 'Pendiente' (recientes, sin pagar) y otras filas 'Anulado' (cobros duplicados que se anularon).
  - Una membresia nunca tiene mas de 4 filas de pago.
"""
import random
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_DOWN
from comun import SEMILLA, FECHA_HOY, escribir_csv, leer_csv

rng = random.Random(SEMILLA + 4)

planes = leer_csv("planes.csv")
membresias = leer_csv("membresias.csv")
socios = {s["SocioID"]: s for s in leer_csv("socios.csv")}
PRECIO = {int(p["PlanID"]): Decimal(p["Precio"]) for p in planes}
DURACION = {int(p["PlanID"]): int(p["DuracionDias"]) for p in planes}

# Cuantas cuotas por plan: (opciones, pesos)
CUOTAS = {
    1: ([1],       [1]),
    2: ([1, 2],    [0.6, 0.4]),
    3: ([1, 2, 3], [0.2, 0.3, 0.5]),
    4: ([2, 3, 4], [0.2, 0.3, 0.5]),
    5: ([2, 3, 4], [0.25, 0.35, 0.40]),
}
METODOS = ["Efectivo", "Tarjeta", "Transferencia"]
PESO_METODOS = [30, 50, 20]
PCT_PENDIENTE = 0.05
PCT_ANULADO = 0.03


def con_hora(dia):
    """Agrega una hora al azar entre las 08:00 y las 20:59."""
    return datetime(dia.year, dia.month, dia.day, rng.randint(8, 20), rng.randint(0, 59), rng.randint(0, 59))


# ----------------------------------------------------------------------
# 1. Cuotas "normales" de cada membresia
# ----------------------------------------------------------------------
cuotas = []        # dicts: membresia, monto, fecha (datetime), metodo, estado
for m in membresias:
    mid, plan = int(m["MembresiaID"]), int(m["PlanID"])
    inicio = date.fromisoformat(m["FechaInicio"])
    registro = date.fromisoformat(socios[m["SocioID"]]["FechaRegistro"])

    opciones, pesos = CUOTAS[plan]
    n_objetivo = rng.choices(opciones, weights=pesos)[0]
    separacion = DURACION[plan] // n_objetivo

    # Fechas de cada cuota: la primera cerca del inicio, las demas separadas; ninguna despues de hoy
    fechas = [max(registro, inicio - timedelta(days=rng.randint(0, 3)))]
    for k in range(1, n_objetivo):
        f = inicio + timedelta(days=k * separacion)
        if f <= FECHA_HOY:
            fechas.append(f)
    n = len(fechas)

    # Dividir el precio en n cuotas que sumen exactamente el precio
    base = (PRECIO[plan] / n).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    montos = [base] * (n - 1) + [PRECIO[plan] - base * (n - 1)]

    for f, monto in zip(fechas, montos):
        cuotas.append({"membresia": mid, "monto": monto, "fecha": con_hora(f),
                       "metodo": rng.choices(METODOS, weights=PESO_METODOS)[0], "estado": "Pagado"})

principales = len(cuotas)
total_objetivo = round(principales / (1 - PCT_ANULADO))     # las anuladas se suman aparte
n_pendientes = round(total_objetivo * PCT_PENDIENTE)
n_anulados = total_objetivo - principales

# ----------------------------------------------------------------------
# 2. Cuotas Pendientes: solo entre las de los ultimos 120 dias
# ----------------------------------------------------------------------
recientes = [i for i, c in enumerate(cuotas) if c["fecha"].date() >= FECHA_HOY - timedelta(days=120)]
for i in rng.sample(recientes, min(n_pendientes, len(recientes))):
    cuotas[i]["estado"] = "Pendiente"

# ----------------------------------------------------------------------
# 3. Filas Anuladas: cobros duplicados (mismo monto, minutos despues) de membresias con menos de 4 filas
# ----------------------------------------------------------------------
filas_por_membresia = {}
for c in cuotas:
    filas_por_membresia[c["membresia"]] = filas_por_membresia.get(c["membresia"], 0) + 1
candidatas = [i for i, c in enumerate(cuotas)
              if filas_por_membresia[c["membresia"]] < 4 and c["estado"] == "Pagado"]
extras = []
for i in rng.sample(candidatas, min(n_anulados, len(candidatas))):
    c = cuotas[i]
    if filas_por_membresia[c["membresia"]] >= 4:
        continue
    filas_por_membresia[c["membresia"]] += 1
    extras.append({"membresia": c["membresia"], "monto": c["monto"],
                   "fecha": c["fecha"] + timedelta(minutes=rng.randint(5, 45)),
                   "metodo": c["metodo"], "estado": "Anulado"})

todos = cuotas + extras
todos.sort(key=lambda c: (c["fecha"], c["membresia"]))      # IDs en orden cronologico

pagos = [(i + 1, c["membresia"], f"{c['monto']:.2f}", c["fecha"].strftime("%Y-%m-%d %H:%M:%S"),
          c["metodo"], c["estado"]) for i, c in enumerate(todos)]

print("Generando pagos...")
escribir_csv("pagos.csv", ["PagoID", "MembresiaID", "Monto", "FechaPago", "MetodoPago", "Estado"], pagos)

# ----------------------------------------------------------------------
# Resumen de control
# ----------------------------------------------------------------------
print("  Resumen de control:")
for est in ("Pagado", "Pendiente", "Anulado"):
    n = sum(1 for p in pagos if p[5] == est)
    print(f"    {est}: {n} ({n / len(pagos):.1%})")
for met in METODOS:
    n = sum(1 for p in pagos if p[4] == met)
    print(f"    {met}: {n} ({n / len(pagos):.1%})")
por_membresia = {}
for p in pagos:
    por_membresia[p[1]] = por_membresia.get(p[1], 0) + 1
print(f"    Pagos por membresia: minimo {min(por_membresia.values())}, maximo {max(por_membresia.values())}, "
      f"promedio {len(pagos) / len(membresias):.2f}")
print(f"    Membresias sin ningun pago: {len(membresias) - len(por_membresia)}")

# Comprobacion: las cuotas Pagado + Pendiente de cada membresia suman el precio de su plan
descuadradas = 0
suma = {}
for p in pagos:
    if p[5] != "Anulado":
        suma[p[1]] = suma.get(p[1], Decimal("0")) + Decimal(p[2])
for m in membresias:
    if suma.get(int(m["MembresiaID"])) != PRECIO[int(m["PlanID"])]:
        descuadradas += 1
print(f"    Membresias cuyas cuotas no suman el precio del plan: {descuadradas}")
print(f"    Monto total (sin anulados): ${sum(suma.values()):,.2f}")
