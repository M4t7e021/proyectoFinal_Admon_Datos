"""
06_reservas.py - Genera reservas.csv (aprox. 20.000 reservas).

Lee socios.csv, membresias.csv, sesiones.csv y tipos_clase.csv (pasos 1 a 5).

Reglas (ver especificacion de CSV):
  - Un socio solo reserva una sesion si tiene una membresia NO cancelada que cubra ese dia
  - No se repite la pareja (SesionID, SocioID)
  - Las reservas Confirmadas de una sesion nunca superan su CupoMaximo
  - FechaReserva: entre 7 dias y 1 hora antes de la sesion, nunca antes de las 08:00 del primer dia de la membresia
    y nunca despues de hoy (2026-10-25)
  - Estado: ~88 % Confirmada, ~12 % Cancelada (en una sesion cancelada, todas las reservas quedan canceladas)
  - Un socio no confirma dos clases que se solapan en el tiempo (maximo 2 por dia)
"""
import random
from datetime import date, datetime, timedelta
from comun import SEMILLA, FECHA_HOY, FECHA_FIN, escribir_csv, leer_csv

rng = random.Random(SEMILLA + 6)

socios = leer_csv("socios.csv")
membresias = leer_csv("membresias.csv")
sesiones = leer_csv("sesiones.csv")
tipos = leer_csv("tipos_clase.csv")
NOMBRE_TIPO = {int(t["TipoClaseID"]): t["Nombre"] for t in tipos}
DURACION = {int(t["TipoClaseID"]): int(t["DuracionMin"]) for t in tipos}

# ----------------------------------------------------------------------
# Parametros que controlan cuanta gente reserva
# ----------------------------------------------------------------------
BASE_OCUPACION = 0.19            # ocupacion tipica de una sesion antes de aplicar los factores
P_CANCELADA = 0.108              # probabilidad de que una reserva de una sesion normal se cancele
POPULARIDAD = {                  # clases mas o menos populares
    "Spinning": 1.5, "Zumba": 1.4, "Funcional": 1.3, "HIIT": 1.1, "Boxeo": 1.0, "Aeróbicos": 0.9,
    "Baile": 0.9, "CrossFit": 0.9, "TRX": 0.8, "Pilates": 0.8, "Yoga": 0.75, "Estiramiento": 0.55,
}
HOY_FIN_DIA = datetime(FECHA_HOY.year, FECHA_HOY.month, FECHA_HOY.day, 23, 59, 59)

# ----------------------------------------------------------------------
# 1. Quien tiene membresia vigente cada dia (solo membresias no canceladas)
# ----------------------------------------------------------------------
vigentes = {}      # dia -> lista de (socio_id, fecha_inicio_de_su_membresia)
for m in membresias:
    if m["Estado"] == "Cancelada":
        continue
    inicio, fin = date.fromisoformat(m["FechaInicio"]), date.fromisoformat(m["FechaFin"])
    d = inicio
    while d <= min(fin, FECHA_FIN):
        vigentes.setdefault(d, []).append((int(m["SocioID"]), inicio))
        d += timedelta(days=1)

# Cada socio tiene una "afición": unos van mucho y otros poco (distribucion con cola larga)
AFICION = {int(s["SocioID"]): min(rng.paretovariate(2.5), 8.0) for s in socios}

# ----------------------------------------------------------------------
# 2. Recorrer las sesiones en orden cronologico y llenar cada una
# ----------------------------------------------------------------------
ocupado = {}       # (socio_id, dia) -> lista de (inicio, fin) de clases confirmadas
reservas = []      # (fecha_reserva, sesion_id, socio_id, estado)

for s in sesiones:
    sesion_id = int(s["SesionID"])
    tipo_id, cupo = int(s["TipoClaseID"]), int(s["CupoMaximo"])
    inicio_sesion = datetime.strptime(s["FechaHora"], "%Y-%m-%d %H:%M:%S")
    dia = inicio_sesion.date()
    estado_sesion = s["Estado"]
    minutos_ini = inicio_sesion.hour * 60 + inicio_sesion.minute
    minutos_fin = minutos_ini + DURACION[tipo_id]

    # Cuanta gente quiere ir: depende de la clase, la hora y el dia
    hora = inicio_sesion.hour
    f_hora = 1.4 if (6 <= hora <= 8 or 17 <= hora <= 19) else (1.0 if hora in (12, 13) else 0.6)
    f_dia = 0.8 if dia.weekday() >= 5 else 1.0
    ocupacion = BASE_OCUPACION * POPULARIDAD[NOMBRE_TIPO[tipo_id]] * f_hora * f_dia * rng.lognormvariate(0, 0.4)
    if rng.random() < 0.06:
        ocupacion = 1.0                                   # algunas clases se llenan
    ocupacion = min(ocupacion, 1.0)
    n_confirmadas = int(round(ocupacion * cupo))

    if estado_sesion == "Cancelada":
        n_confirmadas = int(round(n_confirmadas * 0.6))   # se habian apuntado menos; todas quedan canceladas
        n_canceladas = n_confirmadas
        n_confirmadas = 0
    else:
        if estado_sesion == "Programada":
            n_confirmadas = int(round(n_confirmadas * 0.5))   # aun falta tiempo para reservar
        ratio = P_CANCELADA / (1 - P_CANCELADA)
        n_canceladas = int(n_confirmadas * ratio + rng.random())

    # Candidatos: socios con membresia vigente ese dia, ordenados al azar segun su aficion
    candidatos = vigentes.get(dia, [])
    ordenados = sorted(candidatos, key=lambda c: rng.random() ** (1.0 / AFICION[c[0]]), reverse=True)

    confirmadas, canceladas = [], []
    for socio_id, inicio_membresia in ordenados:
        if len(confirmadas) >= n_confirmadas and len(canceladas) >= n_canceladas:
            break
        # Momento de la reserva: entre 7 dias y 1 hora antes (la mayoria, el dia anterior)
        limite_inf = max(inicio_sesion - timedelta(days=7),
                         datetime(inicio_membresia.year, inicio_membresia.month, inicio_membresia.day, 8, 0))   # el gimnasio abre a las 08:00
        limite_sup = min(inicio_sesion - timedelta(hours=1), HOY_FIN_DIA)
        if limite_inf > limite_sup:
            continue
        horas_antes = min(168.0, 1.0 + rng.expovariate(1 / 30))
        momento = min(max(inicio_sesion - timedelta(hours=horas_antes), limite_inf), limite_sup)
        momento = momento.replace(microsecond=0)

        agenda = ocupado.get((socio_id, dia), [])
        libre = len(agenda) < 2 and all(not (minutos_ini < f and minutos_fin > i) for i, f in agenda)

        if len(confirmadas) < n_confirmadas and libre:
            confirmadas.append((momento, socio_id))
            ocupado.setdefault((socio_id, dia), []).append((minutos_ini, minutos_fin))
        elif len(canceladas) < n_canceladas:
            canceladas.append((momento, socio_id))

    for momento, socio_id in confirmadas:
        reservas.append((momento, sesion_id, socio_id, "Confirmada"))
    for momento, socio_id in canceladas:
        reservas.append((momento, sesion_id, socio_id, "Cancelada"))

# ----------------------------------------------------------------------
# 3. Asignar IDs en el orden en que se hicieron las reservas y guardar
# ----------------------------------------------------------------------
reservas.sort(key=lambda r: (r[0], r[1], r[2]))
filas = [(i + 1, ses, soc, f.strftime("%Y-%m-%d %H:%M:%S"), est)
         for i, (f, ses, soc, est) in enumerate(reservas)]

print("Generando reservas...")
escribir_csv("reservas.csv", ["ReservaID", "SesionID", "SocioID", "FechaReserva", "Estado"], filas)

# ----------------------------------------------------------------------
# Resumen de control
# ----------------------------------------------------------------------
print("  Resumen de control:")
n_conf = sum(1 for f in filas if f[4] == "Confirmada")
n_canc = len(filas) - n_conf
print(f"    Confirmada: {n_conf} ({n_conf / len(filas):.1%})")
print(f"    Cancelada: {n_canc} ({n_canc / len(filas):.1%})")

conf_por_sesion = {}
for f in filas:
    if f[4] == "Confirmada":
        conf_por_sesion[f[1]] = conf_por_sesion.get(f[1], 0) + 1
cupo_de = {int(s["SesionID"]): int(s["CupoMaximo"]) for s in sesiones}
excedidas = sum(1 for sid, n in conf_por_sesion.items() if n > cupo_de[sid])
llenas = sum(1 for sid, n in conf_por_sesion.items() if n == cupo_de[sid])
print(f"    Sesiones con mas confirmadas que su cupo: {excedidas}")
print(f"    Sesiones llenas: {llenas}")
print(f"    Sesiones sin ninguna reserva confirmada: {len(sesiones) - len(conf_por_sesion)}")
print(f"    Socios que han reservado: {len({f[2] for f in filas})} de {len(socios)}")

tipo_de = {int(s["SesionID"]): int(s["TipoClaseID"]) for s in sesiones}
por_clase = {}
for f in filas:
    if f[4] == "Confirmada":
        nombre = NOMBRE_TIPO[tipo_de[f[1]]]
        por_clase[nombre] = por_clase.get(nombre, 0) + 1
print("    Reservas confirmadas por clase:")
for nombre, n in sorted(por_clase.items(), key=lambda x: -x[1]):
    print(f"      {nombre}: {n}")
