"""
03_membresias.py - Genera membresias.csv (aprox. 5.000 membresias).

Lee socios.csv y planes.csv (generados en los pasos 1 y 2).

Reglas (ver especificacion de CSV):
  - Cada socio tiene entre 1 y 5 membresias (promedio cercano a 2,5)
  - FechaInicio nunca es anterior a la FechaRegistro del socio, y nunca es futura
  - FechaFin = FechaInicio + DuracionDias del plan
  - Las membresias de un mismo socio no se solapan
  - Estado: Vencida si FechaFin <= 2026-10-25, Activa si la incluye, Cancelada en ~5 %
"""
import random
from datetime import date, timedelta
from comun import SEMILLA, FECHA_HOY, escribir_csv, leer_csv

rng = random.Random(SEMILLA + 3)       # semilla propia de este paso (SEMILLA + numero de paso)

planes = leer_csv("planes.csv")
socios = leer_csv("socios.csv")
DURACION = {int(p["PlanID"]): int(p["DuracionDias"]) for p in planes}

# Peso de cada plan: mas Mensual y Trimestral, menos Semanal
PESO_PLAN = {1: 8, 2: 38, 3: 28, 4: 12, 5: 14}
# Cuantas membresias tendra cada socio (se corta antes si no hay tiempo suficiente)
CANTIDAD = [1, 2, 3, 4, 5]
PESO_CANTIDAD = [0.16, 0.26, 0.26, 0.18, 0.14]


def elegir_plan(inicio, fin_maximo=None):
    """Elige un plan al azar segun los pesos. Si se pide, solo planes que terminen antes de fin_maximo."""
    ids, pesos = [], []
    for pid, peso in PESO_PLAN.items():
        if fin_maximo is None or inicio + timedelta(days=DURACION[pid]) <= fin_maximo:
            ids.append(pid)
            pesos.append(peso)
    return rng.choices(ids, weights=pesos)[0]


def pausa_entre_membresias():
    """Dias sin membresia entre una y la siguiente: casi siempre renueva rapido, a veces regresa meses despues."""
    return rng.randint(0, 10) if rng.random() < 0.7 else rng.randint(11, 90)


filas = []     # (SocioID, PlanID, FechaInicio, FechaFin, es_ultima_del_socio)

for s in socios:
    socio_id = int(s["SocioID"])
    registro = date.fromisoformat(s["FechaRegistro"])
    estado_socio = s["Estado"]
    cantidad = rng.choices(CANTIDAD, weights=PESO_CANTIDAD)[0]

    inicio = registro + timedelta(days=rng.randint(0, 5))

    # Un socio Inactivo dejo de comprar hace tiempo: sus membresias terminan antes de HOY - 15 dias
    if estado_socio == "Inactivo":
        ultimo_inicio_permitido = rng.choice([registro + timedelta(days=d) for d in range(20, (FECHA_HOY - timedelta(days=45) - registro).days + 1)])
        fin_maximo = FECHA_HOY - timedelta(days=15)
    else:
        ultimo_inicio_permitido = FECHA_HOY
        fin_maximo = None

    cadena = []
    while len(cadena) < cantidad and inicio <= ultimo_inicio_permitido:
        plan = elegir_plan(inicio, fin_maximo)
        fin = inicio + timedelta(days=DURACION[plan])
        cadena.append([socio_id, plan, inicio, fin])
        inicio = fin + timedelta(days=1 + pausa_entre_membresias())

    # El 70 % de los socios Activos que se quedaron sin membresia vigente "regresan" con una que cubre hoy
    if estado_socio == "Activo" and len(cadena) < 5 and cadena[-1][3] < FECHA_HOY and rng.random() < 0.7:
        plan = rng.choices(list(PESO_PLAN), weights=list(PESO_PLAN.values()))[0]
        nuevo_inicio = max(cadena[-1][3] + timedelta(days=1), FECHA_HOY - timedelta(days=rng.randint(0, DURACION[plan] - 1)))
        cadena.append([socio_id, plan, nuevo_inicio, nuevo_inicio + timedelta(days=DURACION[plan])])

    for i, m in enumerate(cadena):
        filas.append(m + [i == len(cadena) - 1, estado_socio])

# ----------------------------------------------------------------------
# Asignar estado de cada membresia
# ----------------------------------------------------------------------
resultado = []
for socio_id, plan, inicio, fin, es_ultima, estado_socio in filas:
    if estado_socio == "Suspendido" and es_ultima:
        estado = "Cancelada"                 # un socio suspendido tiene su ultima membresia cancelada
    elif rng.random() < 0.03:
        estado = "Cancelada"                 # algunas cancelaciones al azar
    elif fin <= FECHA_HOY:
        estado = "Vencida"
    else:
        estado = "Activa"
    resultado.append((inicio, socio_id, plan, fin, estado))

# IDs en orden cronologico: la membresia mas antigua es la 1
resultado.sort(key=lambda r: (r[0], r[1]))
membresias = [(i + 1, socio_id, plan, inicio.isoformat(), fin.isoformat(), estado)
              for i, (inicio, socio_id, plan, fin, estado) in enumerate(resultado)]

print("Generando membresias...")
escribir_csv("membresias.csv",
             ["MembresiaID", "SocioID", "PlanID", "FechaInicio", "FechaFin", "Estado"], membresias)

# ----------------------------------------------------------------------
# Resumen de control
# ----------------------------------------------------------------------
por_socio = {}
for m in membresias:
    por_socio[m[1]] = por_socio.get(m[1], 0) + 1
print("  Resumen de control:")
print(f"    Membresias por socio: minimo {min(por_socio.values())}, maximo {max(por_socio.values())}, "
      f"promedio {len(membresias) / len(socios):.2f}")
for est in ("Activa", "Vencida", "Cancelada"):
    print(f"    {est}: {sum(1 for m in membresias if m[5] == est)}")
for pid in sorted(DURACION):
    nombre = next(p["Nombre"] for p in planes if int(p["PlanID"]) == pid)
    print(f"    Plan {nombre}: {sum(1 for m in membresias if m[2] == pid)}")
print(f"    Socios sin ninguna membresia: {len(socios) - len(por_socio)}")
