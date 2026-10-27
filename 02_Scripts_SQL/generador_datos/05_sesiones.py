"""
05_sesiones.py - Genera sesiones.csv (3.000 sesiones de clase).

Lee tipos_clase.csv, salas.csv y entrenadores.csv (paso 1).

Reglas (ver especificacion de CSV):
  - FechaHora entre 2025-01-01 y 2026-10-31, de 06:00 a 21:00, en punto o y media
  - Una sala no puede tener dos clases a la misma hora (en realidad, ni siquiera solapadas)
  - Un entrenador no puede dar dos clases a la vez y solo imparte clases de su especialidad
  - CupoMaximo mayor que 0 y no mayor que la capacidad de la sala
  - Estado: Realizada hasta 2026-10-25 (~3 % Cancelada) y Programada desde 2026-10-26
  - Mas sesiones en horas pico (6-9 y 17-20) y en dias habiles
"""
import random
from datetime import date, datetime, timedelta
from comun import SEMILLA, FECHA_INICIO, FECHA_HOY, FECHA_FIN, escribir_csv, leer_csv

N_SESIONES = 3000
rng = random.Random(SEMILLA + 5)

tipos = leer_csv("tipos_clase.csv")
salas = leer_csv("salas.csv")
entrenadores = leer_csv("entrenadores.csv")

TIPO_ID = {t["Nombre"]: int(t["TipoClaseID"]) for t in tipos}
TIPO_DURACION = {int(t["TipoClaseID"]): int(t["DuracionMin"]) for t in tipos}
SALA_ID = {s["Nombre"]: int(s["SalaID"]) for s in salas}
SALA_CAPACIDAD = {int(s["SalaID"]): int(s["Capacidad"]) for s in salas}

# ----------------------------------------------------------------------
# Reglas del gimnasio
# ----------------------------------------------------------------------
# Que clases se dan en cada sala, con su peso (mas peso = se programa mas seguido)
CLASES_POR_SALA = {
    "Sala Principal": {"Zumba": 0.45, "Baile": 0.25, "Aeróbicos": 0.30},
    "Sala Spinning":  {"Spinning": 1.0},
    "Sala Funcional": {"Funcional": 0.40, "HIIT": 0.25, "CrossFit": 0.20, "TRX": 0.15},
    "Sala Yoga":      {"Yoga": 0.50, "Pilates": 0.30, "Estiramiento": 0.20},
    "Sala Boxeo":     {"Boxeo": 1.0},
}
PESO_SALA = {"Sala Principal": 1.3, "Sala Spinning": 1.2, "Sala Funcional": 1.1, "Sala Yoga": 0.9, "Sala Boxeo": 0.6}

# Que clases puede dar cada especialidad
CLASES_POR_ESPECIALIDAD = {
    "Ciclismo indoor":         ["Spinning"],
    "Yoga y Pilates":          ["Yoga", "Pilates", "Estiramiento"],
    "Entrenamiento funcional": ["Funcional", "TRX"],
    "Baile":                   ["Zumba", "Baile", "Aeróbicos"],
    "Boxeo":                   ["Boxeo"],
    "HIIT":                    ["HIIT"],
    "CrossFit":                ["CrossFit"],
}
# Los entrenadores Inactivos dejaron de dar clases en esta fecha
BAJA_ENTRENADOR = {14: date(2026, 3, 31), 15: date(2026, 5, 31)}

# Entrenadores: id -> clases que puede dar
ENTRENADOR_CLASES = {int(e["EntrenadorID"]): {TIPO_ID[c] for c in CLASES_POR_ESPECIALIDAD[e["Especialidad"]]}
                     for e in entrenadores}

# ----------------------------------------------------------------------
# Pesos de dias y horas
# ----------------------------------------------------------------------
dias = [FECHA_INICIO + timedelta(days=i) for i in range((FECHA_FIN - FECHA_INICIO).days + 1)]
PESO_DIA_SEMANA = {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 0.65, 6: 0.25}   # lunes=0 ... domingo=6
pesos_dias = []
for i, d in enumerate(dias):
    crecimiento = 0.7 + 0.5 * i / len(dias)                  # el gimnasio programa mas clases con el tiempo
    feriado = 0.3 if (d.month == 12 and d.day >= 24) or (d.month == 1 and d.day == 1) else 1.0
    pesos_dias.append(PESO_DIA_SEMANA[d.weekday()] * crecimiento * feriado)

horas = [(h, m) for h in range(6, 22) for m in (0, 30) if not (h == 21 and m == 30)]   # 06:00 ... 21:00


def peso_hora(h, m):
    base = 3.0 if (6 <= h <= 8 or 17 <= h <= 19) else (1.2 if h in (12, 13) else 1.0)
    return base * (1.5 if m == 0 else 0.6)                   # mas clases "en punto" que "y media"


pesos_horas = [peso_hora(h, m) for h, m in horas]
nombres_salas = list(CLASES_POR_SALA)
pesos_salas = [PESO_SALA[s] for s in nombres_salas]

# ----------------------------------------------------------------------
# Generar sesiones (se rechaza un intento si la sala o el entrenador estan ocupados)
# ----------------------------------------------------------------------
ocupado_sala = {}          # (sala_id, dia) -> lista de (inicio, fin) en minutos del dia
ocupado_entr = {}          # (entrenador_id, dia) -> lista de (inicio, fin)
HOLGURA = 10               # minutos libres entre clases en la misma sala o del mismo entrenador


def libre(agenda, clave, inicio, fin):
    for i, f in agenda.get(clave, []):
        if inicio < f + HOLGURA and fin + HOLGURA > i:
            return False
    return True


sesiones = []
intentos = 0
while len(sesiones) < N_SESIONES and intentos < 500_000:
    intentos += 1
    dia = rng.choices(dias, weights=pesos_dias)[0]
    h, m = rng.choices(horas, weights=pesos_horas)[0]
    sala_nombre = rng.choices(nombres_salas, weights=pesos_salas)[0]
    sala_id = SALA_ID[sala_nombre]

    opciones = CLASES_POR_SALA[sala_nombre]
    tipo_id = TIPO_ID[rng.choices(list(opciones), weights=list(opciones.values()))[0]]
    inicio = h * 60 + m
    fin = inicio + TIPO_DURACION[tipo_id]

    if not libre(ocupado_sala, (sala_id, dia), inicio, fin):
        continue

    # Entrenadores que dan esa clase, estaban activos ese dia y estan libres a esa hora
    candidatos = [e for e, clases in ENTRENADOR_CLASES.items()
                  if tipo_id in clases
                  and (e not in BAJA_ENTRENADOR or dia <= BAJA_ENTRENADOR[e])
                  and libre(ocupado_entr, (e, dia), inicio, fin)]
    if not candidatos:
        continue
    entrenador_id = rng.choice(candidatos)

    ocupado_sala.setdefault((sala_id, dia), []).append((inicio, fin))
    ocupado_entr.setdefault((entrenador_id, dia), []).append((inicio, fin))

    # Cupo: normalmente la capacidad completa, a veces menos
    capacidad = SALA_CAPACIDAD[sala_id]
    cupo = rng.choices([capacidad, capacidad - 2, capacidad - 5], weights=[0.60, 0.25, 0.15])[0]

    if dia > FECHA_HOY:
        estado = "Programada"
    else:
        estado = "Cancelada" if rng.random() < 0.03 else "Realizada"

    sesiones.append((datetime(dia.year, dia.month, dia.day, h, m), sala_id, tipo_id, entrenador_id, cupo, estado))

if len(sesiones) < N_SESIONES:
    raise SystemExit(f"Solo se lograron {len(sesiones)} sesiones; revisar las reglas.")

# IDs en orden cronologico
sesiones.sort(key=lambda s: (s[0], s[1]))
filas = [(i + 1, tipo, entr, sala, f.strftime("%Y-%m-%d %H:%M:%S"), cupo, estado)
         for i, (f, sala, tipo, entr, cupo, estado) in enumerate(sesiones)]

print("Generando sesiones...")
escribir_csv("sesiones.csv",
             ["SesionID", "TipoClaseID", "EntrenadorID", "SalaID", "FechaHora", "CupoMaximo", "Estado"], filas)

# ----------------------------------------------------------------------
# Resumen de control
# ----------------------------------------------------------------------
print("  Resumen de control:")
for est in ("Realizada", "Cancelada", "Programada"):
    print(f"    {est}: {sum(1 for f in filas if f[6] == est)}")
print("    Sesiones por clase:")
nombre_tipo = {int(t["TipoClaseID"]): t["Nombre"] for t in tipos}
conteo = {}
for f in filas:
    conteo[f[1]] = conteo.get(f[1], 0) + 1
for tid, n in sorted(conteo.items(), key=lambda x: -x[1]):
    print(f"      {nombre_tipo[tid]}: {n}")
carga = {}
for f in filas:
    carga[f[2]] = carga.get(f[2], 0) + 1
print(f"    Sesiones por entrenador: minimo {min(carga.values())}, maximo {max(carga.values())}")
pico = sum(1 for f in filas if int(f[4][11:13]) in (6, 7, 8, 17, 18, 19))
print(f"    Sesiones en horas pico (6-8 y 17-19): {pico / len(filas):.0%}")
print(f"    Sesiones en fin de semana: {sum(1 for f in filas if datetime.strptime(f[4], '%Y-%m-%d %H:%M:%S').weekday() >= 5) / len(filas):.0%}")
