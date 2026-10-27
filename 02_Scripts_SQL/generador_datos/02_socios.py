"""
02_socios.py - Genera socios.csv (2.000 socios ficticios).

Reglas (ver especificacion de CSV):
  - Documento unico, formato 00000000-0 (ficticio, no es un DUI real)
  - Email unico, con dominio ficticio
  - FechaNacimiento anterior a FechaRegistro (edades de 16 a 70 anios)
  - FechaRegistro entre 2025-01-01 y 2026-09-30, con mas altas en enero, febrero y septiembre
  - Estado: 80 % Activo, 15 % Inactivo, 5 % Suspendido
"""
import random
import unicodedata
from datetime import date, timedelta
from comun import SEMILLA, escribir_csv

N_SOCIOS = 2000
rng = random.Random(SEMILLA)          # generador aleatorio con semilla fija

NOMBRES_M = ["Carlos", "José", "Luis", "Miguel", "Juan", "Pedro", "Jorge", "Mario", "Roberto", "Ricardo",
             "Fernando", "Daniel", "David", "Manuel", "Francisco", "Oscar", "Eduardo", "Rafael", "Héctor",
             "Álvaro", "Andrés", "Sergio", "Víctor", "Wilfredo", "Walter", "Kevin", "Alexander", "Marvin",
             "Gerardo", "Salvador", "Julio", "Rodrigo", "Enrique", "Ernesto", "Mauricio", "Josué"]
NOMBRES_F = ["María", "Ana", "Carmen", "Sofía", "Karla", "Gabriela", "Daniela", "Patricia", "Claudia",
             "Verónica", "Lucía", "Fátima", "Alejandra", "Beatriz", "Cecilia", "Diana", "Elena", "Fernanda",
             "Guadalupe", "Isabel", "Jennifer", "Laura", "Lorena", "Margarita", "Mónica", "Natalia", "Paola",
             "Rosa", "Silvia", "Tatiana", "Ursula", "Wendy", "Yesenia", "Ingrid", "Marta", "Rebeca"]
SEGUNDOS_M = ["José", "Luis", "Carlos", "Antonio", "Alberto", "Ernesto"]
SEGUNDOS_F = ["María", "Alejandra", "Beatriz", "Isabel", "Fernanda", "Lucía"]
APELLIDOS = ["Martínez", "Hernández", "López", "García", "Rodríguez", "Pérez", "González", "Ramírez", "Flores",
             "Rivera", "Gómez", "Díaz", "Cruz", "Morales", "Reyes", "Torres", "Ortiz", "Castillo", "Mejía",
             "Vásquez", "Jiménez", "Alvarado", "Chávez", "Rivas", "Guzmán", "Menjívar", "Portillo", "Orellana",
             "Cáceres", "Serrano", "Mendoza", "Aguilar", "Campos", "Cortez", "Escobar", "Fuentes", "Henríquez",
             "Landaverde", "Molina", "Navarro", "Pineda", "Quintanilla", "Romero", "Salazar", "Tobar", "Umaña",
             "Valle", "Zelaya", "Argueta", "Barrera", "Calderón", "Deras", "Erazo", "Funes", "Guerra", "Interiano",
             "Lemus", "Machado"]
DOMINIOS = ["correo.example", "mail.example", "inbox.example"]


def sin_tildes(texto):
    normal = unicodedata.normalize("NFD", texto)
    return "".join(c for c in normal if unicodedata.category(c) != "Mn").lower()


# ----------------------------------------------------------------------
# 1. Fechas de registro: mas altas en ene, feb y sep, y un leve crecimiento en el tiempo
# ----------------------------------------------------------------------
primer_dia, ultimo_dia = date(2025, 1, 1), date(2026, 9, 30)
dias = [primer_dia + timedelta(days=i) for i in range((ultimo_dia - primer_dia).days + 1)]
FACTOR_MES = {1: 2.0, 2: 1.6, 9: 1.8}          # el resto de meses vale 1.0
pesos = []
for i, d in enumerate(dias):
    crecimiento = 1 + 0.3 * i / len(dias)
    pesos.append(FACTOR_MES.get(d.month, 1.0) * crecimiento)

fechas_registro = sorted(rng.choices(dias, weights=pesos, k=N_SOCIOS))
# Al estar ordenadas, el SocioID 1 es el que se registro primero.

# ----------------------------------------------------------------------
# 2. Estados: Inactivo solo entre quienes se registraron antes de junio de 2026
# ----------------------------------------------------------------------
estados = ["Activo"] * N_SOCIOS
elegibles_inactivo = [i for i, d in enumerate(fechas_registro) if d < date(2026, 6, 1)]
inactivos = set(rng.sample(elegibles_inactivo, int(N_SOCIOS * 0.15)))
restantes = [i for i in range(N_SOCIOS) if i not in inactivos]
suspendidos = set(rng.sample(restantes, int(N_SOCIOS * 0.05)))
for i in inactivos:
    estados[i] = "Inactivo"
for i in suspendidos:
    estados[i] = "Suspendido"

# ----------------------------------------------------------------------
# 3. Construir cada socio
# ----------------------------------------------------------------------
documentos_usados, emails_usados = set(), set()
socios = []
for i in range(N_SOCIOS):
    socio_id = i + 1
    es_mujer = rng.random() < 0.5
    nombre = rng.choice(NOMBRES_F if es_mujer else NOMBRES_M)
    primer_nombre = nombre
    if rng.random() < 0.25:                                     # 25 % con nombre compuesto
        segundo = rng.choice(SEGUNDOS_F if es_mujer else SEGUNDOS_M)
        if segundo != nombre:
            nombre = f"{nombre} {segundo}"
    ap1 = rng.choice(APELLIDOS)
    apellido = ap1
    if rng.random() < 0.6:                                      # 60 % con dos apellidos
        ap2 = rng.choice(APELLIDOS)
        if ap2 != ap1:
            apellido = f"{ap1} {ap2}"

    # Documento ficticio unico: 8 digitos + guion + 1 digito (empieza en 9 para no parecer uno real)
    while True:
        doc = f"9{rng.randint(0, 9999999):07d}-{rng.randint(0, 9)}"
        if doc not in documentos_usados:
            documentos_usados.add(doc)
            break

    # Email unico: nombre.apellido@dominio, con numero si ya existe
    base = f"{sin_tildes(primer_nombre)}.{sin_tildes(ap1)}"
    email = f"{base}@{rng.choice(DOMINIOS)}"
    while email in emails_usados:
        email = f"{base}{rng.randint(1, 99)}@{rng.choice(DOMINIOS)}"
    emails_usados.add(email)

    # Telefono: 95 % lo tiene
    telefono = ""
    if rng.random() < 0.95:
        telefono = f"{rng.choice([6, 7])}{rng.randint(0, 999):03d}-{rng.randint(0, 9999):04d}"

    # Fecha de nacimiento: edad al registrarse entre 16 y 70 anios (la mayoria cerca de 30)
    registro = fechas_registro[i]
    edad = rng.triangular(16, 70, 30)
    nacimiento = registro - timedelta(days=int(edad * 365.25))

    socios.append((socio_id, nombre, apellido, doc, email, telefono,
                   nacimiento.isoformat(), registro.isoformat(), estados[i]))

# ----------------------------------------------------------------------
# 4. Guardar y mostrar un resumen para comprobar
# ----------------------------------------------------------------------
print("Generando socios...")
escribir_csv("socios.csv",
             ["SocioID", "Nombre", "Apellido", "Documento", "Email", "Telefono",
              "FechaNacimiento", "FechaRegistro", "Estado"], socios)

print("  Resumen de control:")
for est in ("Activo", "Inactivo", "Suspendido"):
    print(f"    {est}: {estados.count(est)}")
print(f"    Documentos unicos: {len(documentos_usados) == N_SOCIOS}")
print(f"    Emails unicos: {len(emails_usados) == N_SOCIOS}")
print(f"    Primer registro: {fechas_registro[0]}  |  Ultimo registro: {fechas_registro[-1]}")
print(f"    Sin telefono: {sum(1 for s in socios if s[5] == '')}")
