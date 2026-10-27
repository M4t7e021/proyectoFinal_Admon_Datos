"""
01_catalogos.py - Genera los catalogos pequenos: planes, salas, tipos de clase y entrenadores.
Son datos fijos (escritos a mano), no aleatorios.
"""
import unicodedata
from comun import escribir_csv

# ----------------------------------------------------------------------
# 1. Planes de membresia: (PlanID, Nombre, DuracionDias, Precio, Estado)
# ----------------------------------------------------------------------
planes = [
    (1, "Semanal",     7,   12.00, "Activo"),
    (2, "Mensual",     30,  35.00, "Activo"),
    (3, "Trimestral",  90,  90.00, "Activo"),
    (4, "Semestral",   180, 165.00, "Activo"),
    (5, "Anual",       365, 300.00, "Activo"),
]

# ----------------------------------------------------------------------
# 2. Salas: (SalaID, Nombre, Capacidad)
# ----------------------------------------------------------------------
salas = [
    (1, "Sala Principal", 35),
    (2, "Sala Spinning",  20),
    (3, "Sala Yoga",      30),
    (4, "Sala Funcional", 25),
    (5, "Sala Boxeo",     15),
]

# ----------------------------------------------------------------------
# 3. Tipos de clase: (TipoClaseID, Nombre, Descripcion, DuracionMin, Nivel)
# ----------------------------------------------------------------------
tipos_clase = [
    (1,  "Yoga",         "Posturas y respiración para flexibilidad y calma",      60, "Principiante"),
    (2,  "Pilates",      "Fortalecimiento del core y mejora de la postura",       55, "Intermedio"),
    (3,  "Spinning",     "Ciclismo indoor con música y ritmo",                    45, "Intermedio"),
    (4,  "Zumba",        "Baile fitness con ritmos latinos",                      50, "Principiante"),
    (5,  "CrossFit",     "Entrenamiento de alta intensidad con pesas y gimnasia", 60, "Avanzado"),
    (6,  "Funcional",    "Circuitos de fuerza con el peso corporal",              45, "Intermedio"),
    (7,  "Boxeo",        "Técnica de golpeo y acondicionamiento físico",          60, "Intermedio"),
    (8,  "HIIT",         "Intervalos de alta intensidad",                         30, "Avanzado"),
    (9,  "Aeróbicos",    "Ejercicio cardiovascular coreografiado",                50, "Principiante"),
    (10, "Estiramiento", "Movilidad y relajación muscular",                       30, "Principiante"),
    (11, "TRX",          "Entrenamiento en suspensión",                           45, "Intermedio"),
    (12, "Baile",        "Coreografías de ritmos modernos",                       60, "Principiante"),
]

# ----------------------------------------------------------------------
# 4. Entrenadores: (EntrenadorID, Nombre, Apellido, Especialidad, Estado)
#    El correo se arma solo, sin tildes, con un dominio ficticio.
# ----------------------------------------------------------------------
entrenadores_base = [
    (1,  "Carlos",    "Mejía",     "Ciclismo indoor",         "Activo"),
    (2,  "Ana",       "Martínez",  "Yoga y Pilates",          "Activo"),
    (3,  "Luis",      "Hernández", "Entrenamiento funcional", "Activo"),
    (4,  "María",     "Flores",    "Baile",                   "Activo"),
    (5,  "José",      "Ramírez",   "Boxeo",                   "Activo"),
    (6,  "Karla",     "Portillo",  "Yoga y Pilates",          "Activo"),
    (7,  "Diego",     "Orellana",  "HIIT",                    "Activo"),
    (8,  "Sofía",     "Cruz",      "Baile",                   "Activo"),
    (9,  "Ricardo",   "Alvarado",  "Ciclismo indoor",         "Activo"),
    (10, "Daniela",   "Rivas",     "Entrenamiento funcional", "Activo"),
    (11, "Fernando",  "Guzmán",    "CrossFit",                "Activo"),
    (12, "Gabriela",  "Cáceres",   "Baile",                   "Activo"),
    (13, "Óscar",     "Menjívar",  "Boxeo",                   "Activo"),
    (14, "Paola",     "Chávez",    "Yoga y Pilates",          "Inactivo"),
    (15, "Mauricio",  "Serrano",   "HIIT",                    "Inactivo"),
]


def sin_tildes(texto):
    """'Mejía' -> 'mejia' (para armar correos)."""
    normal = unicodedata.normalize("NFD", texto)
    return "".join(c for c in normal if unicodedata.category(c) != "Mn").lower()


entrenadores = []
for eid, nombre, apellido, especialidad, estado in entrenadores_base:
    email = f"{sin_tildes(nombre)}.{sin_tildes(apellido)}@gymvital.example"
    entrenadores.append((eid, nombre, apellido, especialidad, email, estado))

# ----------------------------------------------------------------------
# Escribir los archivos (el orden de columnas es el de la tabla en SQL Server)
# ----------------------------------------------------------------------
print("Generando catalogos...")
escribir_csv("planes.csv",
             ["PlanID", "Nombre", "DuracionDias", "Precio", "Estado"], planes)
escribir_csv("salas.csv",
             ["SalaID", "Nombre", "Capacidad"], salas)
escribir_csv("tipos_clase.csv",
             ["TipoClaseID", "Nombre", "Descripcion", "DuracionMin", "Nivel"], tipos_clase)
escribir_csv("entrenadores.csv",
             ["EntrenadorID", "Nombre", "Apellido", "Especialidad", "Email", "Estado"], entrenadores)
print("Listo.")
