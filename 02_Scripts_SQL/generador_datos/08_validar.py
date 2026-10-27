"""
08_validar.py - Revisa los 10 CSV contra las reglas del modelo (restricciones de la base y reglas de negocio).

Ejecutarlo despues de los pasos 1 a 7 y ANTES de importar a SQL Server.
Guarda el resultado en datos_csv/validacion_resultado.txt (sirve de evidencia para el informe).
Si hay alguna falla, el programa termina con error y muestra ejemplos de las filas que incumplen.
"""
import csv
import os
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from comun import FECHA_INICIO, FECHA_HOY, FECHA_FIN, CARPETA_SALIDA, leer_csv

HOY_FIN = datetime(FECHA_HOY.year, FECHA_HOY.month, FECHA_HOY.day, 23, 59, 59)
d = date.fromisoformat
dt = lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S")

ENCABEZADOS = {
    "socios.csv":        ["SocioID", "Nombre", "Apellido", "Documento", "Email", "Telefono", "FechaNacimiento", "FechaRegistro", "Estado"],
    "planes.csv":        ["PlanID", "Nombre", "DuracionDias", "Precio", "Estado"],
    "entrenadores.csv":  ["EntrenadorID", "Nombre", "Apellido", "Especialidad", "Email", "Estado"],
    "tipos_clase.csv":   ["TipoClaseID", "Nombre", "Descripcion", "DuracionMin", "Nivel"],
    "salas.csv":         ["SalaID", "Nombre", "Capacidad"],
    "membresias.csv":    ["MembresiaID", "SocioID", "PlanID", "FechaInicio", "FechaFin", "Estado"],
    "sesiones.csv":      ["SesionID", "TipoClaseID", "EntrenadorID", "SalaID", "FechaHora", "CupoMaximo", "Estado"],
    "pagos.csv":         ["PagoID", "MembresiaID", "Monto", "FechaPago", "MetodoPago", "Estado"],
    "reservas.csv":      ["ReservaID", "SesionID", "SocioID", "FechaReserva", "Estado"],
    "asistencias.csv":   ["ReservaID", "FechaCheckIn", "Asistio"],
}

# ----------------------------------------------------------------------
# Cargar archivos
# ----------------------------------------------------------------------
datos = {}
for archivo in ENCABEZADOS:
    if not os.path.exists(os.path.join(CARPETA_SALIDA, archivo)):
        sys.exit(f"Falta {archivo}. Ejecuta primero los pasos anteriores.")
    datos[archivo] = leer_csv(archivo)

socios, planes, entrenadores = datos["socios.csv"], datos["planes.csv"], datos["entrenadores.csv"]
tipos, salas, membresias = datos["tipos_clase.csv"], datos["salas.csv"], datos["membresias.csv"]
sesiones, pagos, reservas, asistencias = datos["sesiones.csv"], datos["pagos.csv"], datos["reservas.csv"], datos["asistencias.csv"]

salida = []        # lineas de texto del informe
n_ok = n_falla = 0


def comprobar(nombre, malos):
    """malos = lista de filas que incumplen la regla; vacia significa que la regla se cumple."""
    global n_ok, n_falla
    if not malos:
        n_ok += 1
        salida.append(f"  [OK]    {nombre}")
    else:
        n_falla += 1
        salida.append(f"  [FALLA] {nombre}: {len(malos)} filas incumplen. Ejemplos: {malos[:3]}")


def titulo(texto):
    salida.append("")
    salida.append(texto)


def duplicados(valores):
    vistos, repetidos = set(), []
    for v in valores:
        if v in vistos:
            repetidos.append(v)
        vistos.add(v)
    return repetidos


def entero(x):
    return int(x)


def consecutivos(filas, columna):
    ids = [int(f[columna]) for f in filas]
    return [] if ids == list(range(1, len(ids) + 1)) else ["los IDs no son 1..N consecutivos"]


# ----------------------------------------------------------------------
# 0. Encabezados y conteos
# ----------------------------------------------------------------------
titulo("0. Encabezados y conteo de filas")
for archivo, esperado in ENCABEZADOS.items():
    with open(os.path.join(CARPETA_SALIDA, archivo), encoding="utf-8") as f:
        real = next(csv.reader(f))
    comprobar(f"{archivo}: columnas correctas ({len(datos[archivo])} filas)", [] if real == esperado else [real])

# ----------------------------------------------------------------------
# 1. Catalogos
# ----------------------------------------------------------------------
titulo("1. Catalogos (planes, entrenadores, tipos de clase, salas)")
comprobar("planes: IDs consecutivos", consecutivos(planes, "PlanID"))
comprobar("planes: Nombre unico", duplicados([p["Nombre"] for p in planes]))
comprobar("planes: DuracionDias > 0 y Precio > 0", [p for p in planes if int(p["DuracionDias"]) <= 0 or Decimal(p["Precio"]) <= 0])
comprobar("planes: Estado valido", [p for p in planes if p["Estado"] not in ("Activo", "Inactivo")])
comprobar("entrenadores: IDs consecutivos", consecutivos(entrenadores, "EntrenadorID"))
comprobar("entrenadores: Email unico", duplicados([e["Email"] for e in entrenadores]))
comprobar("entrenadores: Estado valido", [e for e in entrenadores if e["Estado"] not in ("Activo", "Inactivo")])
comprobar("tipos_clase: IDs consecutivos", consecutivos(tipos, "TipoClaseID"))
comprobar("tipos_clase: Nombre unico", duplicados([t["Nombre"] for t in tipos]))
comprobar("tipos_clase: DuracionMin > 0", [t for t in tipos if int(t["DuracionMin"]) <= 0])
comprobar("tipos_clase: Nivel valido", [t for t in tipos if t["Nivel"] not in ("Principiante", "Intermedio", "Avanzado")])
comprobar("salas: IDs consecutivos", consecutivos(salas, "SalaID"))
comprobar("salas: Nombre unico", duplicados([s["Nombre"] for s in salas]))
comprobar("salas: Capacidad > 0", [s for s in salas if int(s["Capacidad"]) <= 0])

# ----------------------------------------------------------------------
# 2. Socios
# ----------------------------------------------------------------------
titulo("2. Socios")
comprobar("socios: IDs consecutivos", consecutivos(socios, "SocioID"))
comprobar("socios: Documento con formato 00000000-0", [s["Documento"] for s in socios if not re.fullmatch(r"\d{8}-\d", s["Documento"])])
comprobar("socios: Documento unico", duplicados([s["Documento"] for s in socios]))
comprobar("socios: Email unico", duplicados([s["Email"] for s in socios]))
comprobar("socios: Email valido (con @, maximo 100 caracteres)", [s["Email"] for s in socios if "@" not in s["Email"] or len(s["Email"]) > 100])
comprobar("socios: Nombre y Apellido no vacios (maximo 50)", [s["SocioID"] for s in socios if not s["Nombre"] or not s["Apellido"] or len(s["Nombre"]) > 50 or len(s["Apellido"]) > 50])
comprobar("socios: Telefono vacio o de maximo 15 caracteres", [s["SocioID"] for s in socios if len(s["Telefono"]) > 15])
comprobar("socios: FechaNacimiento anterior a FechaRegistro", [s["SocioID"] for s in socios if not d(s["FechaNacimiento"]) < d(s["FechaRegistro"])])
comprobar("socios: edad al registrarse entre 16 y 70 anios",
          [s["SocioID"] for s in socios if not 15.99 <= (d(s["FechaRegistro"]) - d(s["FechaNacimiento"])).days / 365.25 <= 70.01])
comprobar("socios: FechaRegistro entre 2025-01-01 y 2026-09-30", [s["SocioID"] for s in socios if not date(2025, 1, 1) <= d(s["FechaRegistro"]) <= date(2026, 9, 30)])
comprobar("socios: Estado valido", [s["SocioID"] for s in socios if s["Estado"] not in ("Activo", "Inactivo", "Suspendido")])

# ----------------------------------------------------------------------
# 3. Membresias
# ----------------------------------------------------------------------
titulo("3. Membresias")
id_socio = {s["SocioID"]: s for s in socios}
dur_plan = {p["PlanID"]: int(p["DuracionDias"]) for p in planes}
precio_plan = {p["PlanID"]: Decimal(p["Precio"]) for p in planes}
comprobar("membresias: IDs consecutivos", consecutivos(membresias, "MembresiaID"))
comprobar("membresias: SocioID existe", [m["MembresiaID"] for m in membresias if m["SocioID"] not in id_socio])
comprobar("membresias: PlanID existe", [m["MembresiaID"] for m in membresias if m["PlanID"] not in dur_plan])
comprobar("membresias: FechaFin >= FechaInicio", [m["MembresiaID"] for m in membresias if d(m["FechaFin"]) < d(m["FechaInicio"])])
comprobar("membresias: FechaFin = FechaInicio + DuracionDias del plan",
          [m["MembresiaID"] for m in membresias if d(m["FechaFin"]) != d(m["FechaInicio"]) + timedelta(days=dur_plan[m["PlanID"]])])
comprobar("membresias: FechaInicio no anterior al registro del socio", [m["MembresiaID"] for m in membresias if d(m["FechaInicio"]) < d(id_socio[m["SocioID"]]["FechaRegistro"])])
comprobar("membresias: FechaInicio no es futura (hasta 2026-10-25)", [m["MembresiaID"] for m in membresias if d(m["FechaInicio"]) > FECHA_HOY])
comprobar("membresias: Estado valido", [m["MembresiaID"] for m in membresias if m["Estado"] not in ("Activa", "Vencida", "Cancelada")])
comprobar("membresias: Vencida termina hasta hoy; Activa termina despues de hoy",
          [m["MembresiaID"] for m in membresias
           if (m["Estado"] == "Vencida" and d(m["FechaFin"]) > FECHA_HOY) or (m["Estado"] == "Activa" and d(m["FechaFin"]) <= FECHA_HOY)])
por_socio = defaultdict(list)
for m in membresias:
    por_socio[m["SocioID"]].append((d(m["FechaInicio"]), d(m["FechaFin"]), m["MembresiaID"]))
comprobar("membresias: cada socio tiene entre 1 y 5", [s for s in id_socio if not 1 <= len(por_socio.get(s, [])) <= 5])
solapes = []
for sid, lista in por_socio.items():
    lista.sort()
    solapes += [(sid, a[2], b[2]) for a, b in zip(lista, lista[1:]) if b[0] <= a[1]]
comprobar("membresias: las de un mismo socio no se solapan", solapes)

# ----------------------------------------------------------------------
# 4. Sesiones
# ----------------------------------------------------------------------
titulo("4. Sesiones de clase")
ids_tipo = {t["TipoClaseID"]: int(t["DuracionMin"]) for t in tipos}
cap_sala = {s["SalaID"]: int(s["Capacidad"]) for s in salas}
ids_entr = {e["EntrenadorID"] for e in entrenadores}
comprobar("sesiones: IDs consecutivos", consecutivos(sesiones, "SesionID"))
comprobar("sesiones: TipoClaseID, EntrenadorID y SalaID existen",
          [s["SesionID"] for s in sesiones if s["TipoClaseID"] not in ids_tipo or s["EntrenadorID"] not in ids_entr or s["SalaID"] not in cap_sala])
comprobar("sesiones: no hay dos con la misma SalaID y FechaHora", duplicados([(s["SalaID"], s["FechaHora"]) for s in sesiones]))
comprobar("sesiones: FechaHora entre 2025-01-01 y 2026-10-31",
          [s["SesionID"] for s in sesiones if not FECHA_INICIO <= dt(s["FechaHora"]).date() <= FECHA_FIN])
comprobar("sesiones: horario de 06:00 a 21:00, en punto o y media",
          [s["SesionID"] for s in sesiones
           if dt(s["FechaHora"]).minute not in (0, 30) or not (6 <= dt(s["FechaHora"]).hour <= 21)
           or (dt(s["FechaHora"]).hour == 21 and dt(s["FechaHora"]).minute == 30)])
comprobar("sesiones: 0 < CupoMaximo <= capacidad de la sala", [s["SesionID"] for s in sesiones if not 0 < int(s["CupoMaximo"]) <= cap_sala[s["SalaID"]]])
comprobar("sesiones: Estado valido y coherente con la fecha",
          [s["SesionID"] for s in sesiones
           if s["Estado"] not in ("Programada", "Realizada", "Cancelada")
           or (dt(s["FechaHora"]).date() > FECHA_HOY and s["Estado"] != "Programada")
           or (dt(s["FechaHora"]).date() <= FECHA_HOY and s["Estado"] == "Programada")])
agenda_sala, agenda_entr = defaultdict(list), defaultdict(list)
for s in sesiones:
    ini = dt(s["FechaHora"])
    fin = ini + timedelta(minutes=ids_tipo[s["TipoClaseID"]])
    agenda_sala[(s["SalaID"], ini.date())].append((ini, fin, s["SesionID"]))
    agenda_entr[(s["EntrenadorID"], ini.date())].append((ini, fin, s["SesionID"]))


def hay_solapes(agenda):
    malos = []
    for clave, lista in agenda.items():
        lista.sort()
        malos += [(clave[0], a[2], b[2]) for a, b in zip(lista, lista[1:]) if b[0] < a[1]]
    return malos


comprobar("sesiones: ninguna sala tiene dos clases solapadas", hay_solapes(agenda_sala))
comprobar("sesiones: ningun entrenador tiene dos clases solapadas", hay_solapes(agenda_entr))

# ----------------------------------------------------------------------
# 5. Pagos
# ----------------------------------------------------------------------
titulo("5. Pagos")
id_memb = {m["MembresiaID"]: m for m in membresias}
comprobar("pagos: IDs consecutivos", consecutivos(pagos, "PagoID"))
comprobar("pagos: MembresiaID existe", [p["PagoID"] for p in pagos if p["MembresiaID"] not in id_memb])
comprobar("pagos: Monto > 0", [p["PagoID"] for p in pagos if Decimal(p["Monto"]) <= 0])
comprobar("pagos: MetodoPago valido", [p["PagoID"] for p in pagos if p["MetodoPago"] not in ("Efectivo", "Tarjeta", "Transferencia")])
comprobar("pagos: Estado valido", [p["PagoID"] for p in pagos if p["Estado"] not in ("Pagado", "Pendiente", "Anulado")])
comprobar("pagos: ninguna FechaPago posterior a 2026-10-25", [p["PagoID"] for p in pagos if dt(p["FechaPago"]) > HOY_FIN])
comprobar("pagos: FechaPago no anterior al registro del socio",
          [p["PagoID"] for p in pagos if dt(p["FechaPago"]).date() < d(id_socio[id_memb[p["MembresiaID"]]["SocioID"]]["FechaRegistro"])])
filas_por_memb, suma_memb = defaultdict(int), defaultdict(Decimal)
for p in pagos:
    filas_por_memb[p["MembresiaID"]] += 1
    if p["Estado"] != "Anulado":
        suma_memb[p["MembresiaID"]] += Decimal(p["Monto"])
comprobar("pagos: cada membresia tiene entre 1 y 4 pagos", [m for m in id_memb if not 1 <= filas_por_memb.get(m, 0) <= 4])
comprobar("pagos: cuotas Pagado + Pendiente suman el precio del plan", [m for m in id_memb if suma_memb.get(m) != precio_plan[id_memb[m]["PlanID"]]])

# ----------------------------------------------------------------------
# 6. Reservas
# ----------------------------------------------------------------------
titulo("6. Reservas")
id_sesion = {s["SesionID"]: s for s in sesiones}
vigencias = defaultdict(list)             # socio -> membresias NO canceladas
for m in membresias:
    if m["Estado"] != "Cancelada":
        vigencias[m["SocioID"]].append((d(m["FechaInicio"]), d(m["FechaFin"])))
comprobar("reservas: IDs consecutivos", consecutivos(reservas, "ReservaID"))
comprobar("reservas: SesionID y SocioID existen", [r["ReservaID"] for r in reservas if r["SesionID"] not in id_sesion or r["SocioID"] not in id_socio])
comprobar("reservas: no se repite la pareja (SesionID, SocioID)", duplicados([(r["SesionID"], r["SocioID"]) for r in reservas]))
comprobar("reservas: Estado valido", [r["ReservaID"] for r in reservas if r["Estado"] not in ("Confirmada", "Cancelada")])
comprobar("reservas: FechaReserva entre 7 dias y 1 hora antes de la sesion",
          [r["ReservaID"] for r in reservas
           if not dt(id_sesion[r["SesionID"]]["FechaHora"]) - timedelta(days=7) <= dt(r["FechaReserva"]) <= dt(id_sesion[r["SesionID"]]["FechaHora"]) - timedelta(hours=1)])
comprobar("reservas: ninguna FechaReserva posterior a 2026-10-25", [r["ReservaID"] for r in reservas if dt(r["FechaReserva"]) > HOY_FIN])


def membresia_que_cubre(r):
    dia = dt(id_sesion[r["SesionID"]]["FechaHora"]).date()
    return [v for v in vigencias[r["SocioID"]] if v[0] <= dia <= v[1]]


comprobar("reservas: el socio tenia una membresia no cancelada vigente el dia de la sesion", [r["ReservaID"] for r in reservas if not membresia_que_cubre(r)])
comprobar("reservas: no se reserva antes del primer dia de la membresia",
          [r["ReservaID"] for r in reservas if membresia_que_cubre(r) and dt(r["FechaReserva"]).date() < membresia_que_cubre(r)[0][0]])
comprobar("reservas: sesion Cancelada => todas sus reservas Canceladas",
          [r["ReservaID"] for r in reservas if id_sesion[r["SesionID"]]["Estado"] == "Cancelada" and r["Estado"] != "Cancelada"])
confirmadas = defaultdict(int)
agenda_socio = defaultdict(list)
for r in reservas:
    if r["Estado"] == "Confirmada":
        confirmadas[r["SesionID"]] += 1
        s = id_sesion[r["SesionID"]]
        ini = dt(s["FechaHora"])
        agenda_socio[(r["SocioID"], ini.date())].append((ini, ini + timedelta(minutes=ids_tipo[s["TipoClaseID"]]), r["ReservaID"]))
comprobar("reservas: las Confirmadas de cada sesion no superan su CupoMaximo",
          [sid for sid, n in confirmadas.items() if n > int(id_sesion[sid]["CupoMaximo"])])
choques = []
for clave, lista in agenda_socio.items():
    lista.sort()
    if len(lista) > 2:
        choques.append((clave[0], "mas de 2 clases en un dia"))
    choques += [(clave[0], a[2], b[2]) for a, b in zip(lista, lista[1:]) if b[0] < a[1]]
comprobar("reservas: ningun socio confirma clases solapadas (maximo 2 por dia)", choques)

# ----------------------------------------------------------------------
# 7. Asistencias
# ----------------------------------------------------------------------
titulo("7. Asistencias")
id_reserva = {r["ReservaID"]: r for r in reservas}
comprobar("asistencias: ReservaID existe", [a["ReservaID"] for a in asistencias if a["ReservaID"] not in id_reserva])
comprobar("asistencias: ReservaID sin repetir", duplicados([a["ReservaID"] for a in asistencias]))
comprobar("asistencias: solo reservas Confirmadas de sesiones Realizadas",
          [a["ReservaID"] for a in asistencias
           if a["ReservaID"] in id_reserva and (id_reserva[a["ReservaID"]]["Estado"] != "Confirmada"
                                                 or id_sesion[id_reserva[a["ReservaID"]]["SesionID"]]["Estado"] != "Realizada")])
con_fila = {a["ReservaID"] for a in asistencias}
comprobar("asistencias: toda reserva Confirmada de sesion Realizada tiene su fila",
          [r["ReservaID"] for r in reservas
           if r["Estado"] == "Confirmada" and id_sesion[r["SesionID"]]["Estado"] == "Realizada" and r["ReservaID"] not in con_fila])
comprobar("asistencias: Asistio es 0 o 1", [a["ReservaID"] for a in asistencias if a["Asistio"] not in ("0", "1")])
comprobar("asistencias: Asistio = 0 => FechaCheckIn vacia; Asistio = 1 => con fecha",
          [a["ReservaID"] for a in asistencias if (a["Asistio"] == "0") != (a["FechaCheckIn"] == "")])
comprobar("asistencias: check-in entre 15 min antes y 10 min despues del inicio",
          [a["ReservaID"] for a in asistencias
           if a["FechaCheckIn"] and a["ReservaID"] in id_reserva
           and not dt(id_sesion[id_reserva[a["ReservaID"]]["SesionID"]]["FechaHora"]) - timedelta(minutes=15)
           <= dt(a["FechaCheckIn"]) <= dt(id_sesion[id_reserva[a["ReservaID"]]["SesionID"]]["FechaHora"]) + timedelta(minutes=10)])

# ----------------------------------------------------------------------
# Resumen y guardado
# ----------------------------------------------------------------------
salida.insert(0, "VALIDACION DE LOS ARCHIVOS CSV - GimnasioDB")
salida.append("")
salida.append("Filas por archivo:")
for archivo in ENCABEZADOS:
    salida.append(f"  {archivo}: {len(datos[archivo])}")
salida.append("")
salida.append(f"RESUMEN: {n_ok + n_falla} comprobaciones, {n_ok} OK, {n_falla} con falla")
salida.append("RESULTADO: " + ("LOS DATOS CUMPLEN TODAS LAS REGLAS" if n_falla == 0 else "HAY FALLAS, NO IMPORTAR TODAVIA"))

texto = "\n".join(salida)
print(texto)
with open(os.path.join(CARPETA_SALIDA, "validacion_resultado.txt"), "w", encoding="utf-8") as f:
    f.write(texto + "\n")
sys.exit(0 if n_falla == 0 else 1)
