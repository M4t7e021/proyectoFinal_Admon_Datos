-- PROYECTO: SISTEMA DE RESERVAS DE GIMNASIO
-- 01. Estructura - Tablas

IF DB_ID('GimnasioDB') IS NULL
    CREATE DATABASE GimnasioDB COLLATE Modern_Spanish_CI_AS;
GO

-- Dimensionamiento
ALTER DATABASE GimnasioDB MODIFY FILE (NAME = 'GimnasioDB',     SIZE = 256MB, FILEGROWTH = 64MB);
ALTER DATABASE GimnasioDB MODIFY FILE (NAME = 'GimnasioDB_log', SIZE = 128MB, FILEGROWTH = 64MB);
GO

-- Estrategia de backup
ALTER DATABASE GimnasioDB SET RECOVERY FULL;
GO

USE GimnasioDB;
GO

-- Esquemas
IF SCHEMA_ID('socios')    IS NULL EXEC('CREATE SCHEMA socios    AUTHORIZATION dbo');
IF SCHEMA_ID('clases')    IS NULL EXEC('CREATE SCHEMA clases    AUTHORIZATION dbo');
IF SCHEMA_ID('finanzas')  IS NULL EXEC('CREATE SCHEMA finanzas  AUTHORIZATION dbo');
IF SCHEMA_ID('reportes')  IS NULL EXEC('CREATE SCHEMA reportes  AUTHORIZATION dbo');
IF SCHEMA_ID('auditoria') IS NULL EXEC('CREATE SCHEMA auditoria AUTHORIZATION dbo');
GO

-- Limpieza 
DROP TABLE IF EXISTS clases.Asistencia;
DROP TABLE IF EXISTS clases.Reserva;
DROP TABLE IF EXISTS clases.SesionClase;
DROP TABLE IF EXISTS finanzas.Pago;
DROP TABLE IF EXISTS socios.Membresia;
DROP TABLE IF EXISTS clases.Sala;
DROP TABLE IF EXISTS clases.TipoClase;
DROP TABLE IF EXISTS clases.Entrenador;
DROP TABLE IF EXISTS socios.PlanMembresia;
DROP TABLE IF EXISTS socios.Socio;
GO

-- Tablas por esquema:

-- Esquema socios
CREATE TABLE socios.Socio (
    SocioID         INT IDENTITY(1,1) NOT NULL,
    Nombre          VARCHAR(50)  NOT NULL,
    Apellido        VARCHAR(50)  NOT NULL,
    Documento       VARCHAR(10)  NOT NULL, -- DUI (formato 00000000-0)
    Email           VARCHAR(100) NOT NULL,
    Telefono        VARCHAR(15)  NULL,
    FechaNacimiento DATE         NOT NULL,
    FechaRegistro   DATE         NOT NULL CONSTRAINT DF_Socio_FechaRegistro DEFAULT (CAST(GETDATE() AS DATE)),
    Estado          VARCHAR(10)  NOT NULL CONSTRAINT DF_Socio_Estado DEFAULT ('Activo'),
    CONSTRAINT PK_Socio           PRIMARY KEY (SocioID),
    CONSTRAINT UQ_Socio_Documento UNIQUE (Documento),
    CONSTRAINT UQ_Socio_Email     UNIQUE (Email),
    CONSTRAINT CK_Socio_Estado    CHECK (Estado IN ('Activo','Inactivo','Suspendido')),
    CONSTRAINT CK_Socio_FechaNac  CHECK (FechaNacimiento < FechaRegistro)
);
GO

CREATE TABLE socios.PlanMembresia (
    PlanID       INT IDENTITY(1,1) NOT NULL,
    Nombre       VARCHAR(50)   NOT NULL,
    DuracionDias SMALLINT      NOT NULL,
    Precio       DECIMAL(8,2)  NOT NULL,
    Estado       VARCHAR(10)   NOT NULL CONSTRAINT DF_Plan_Estado DEFAULT ('Activo'),
    CONSTRAINT PK_PlanMembresia      PRIMARY KEY (PlanID),
    CONSTRAINT UQ_PlanMembresia_Nom  UNIQUE (Nombre),
    CONSTRAINT CK_Plan_Duracion      CHECK (DuracionDias > 0),
    CONSTRAINT CK_Plan_Precio        CHECK (Precio > 0),
    CONSTRAINT CK_Plan_Estado        CHECK (Estado IN ('Activo','Inactivo'))
);
GO

CREATE TABLE socios.Membresia (
    MembresiaID INT IDENTITY(1,1) NOT NULL,
    SocioID     INT         NOT NULL,
    PlanID      INT         NOT NULL,
    FechaInicio DATE        NOT NULL,
    FechaFin    DATE        NOT NULL,
    Estado      VARCHAR(10) NOT NULL CONSTRAINT DF_Membresia_Estado DEFAULT ('Activa'),
    CONSTRAINT PK_Membresia        PRIMARY KEY (MembresiaID),
    CONSTRAINT FK_Membresia_Socio  FOREIGN KEY (SocioID) REFERENCES socios.Socio(SocioID),
    CONSTRAINT FK_Membresia_Plan   FOREIGN KEY (PlanID)  REFERENCES socios.PlanMembresia(PlanID),
    CONSTRAINT CK_Membresia_Fechas CHECK (FechaFin >= FechaInicio),
    CONSTRAINT CK_Membresia_Estado CHECK (Estado IN ('Activa','Vencida','Cancelada'))
);
GO

-- Esquema clases
CREATE TABLE clases.Entrenador (
    EntrenadorID INT IDENTITY(1,1) NOT NULL,
    Nombre       VARCHAR(50)  NOT NULL,
    Apellido     VARCHAR(50)  NOT NULL,
    Especialidad VARCHAR(50)  NULL,
    Email        VARCHAR(100) NOT NULL,
    Estado       VARCHAR(10)  NOT NULL CONSTRAINT DF_Entrenador_Estado DEFAULT ('Activo'),
    CONSTRAINT PK_Entrenador       PRIMARY KEY (EntrenadorID),
    CONSTRAINT UQ_Entrenador_Email UNIQUE (Email),
    CONSTRAINT CK_Entrenador_Est   CHECK (Estado IN ('Activo','Inactivo'))
);
GO

CREATE TABLE clases.TipoClase (
    TipoClaseID INT IDENTITY(1,1) NOT NULL,
    Nombre      VARCHAR(50)  NOT NULL,
    Descripcion VARCHAR(200) NULL,
    DuracionMin SMALLINT     NOT NULL,
    Nivel       VARCHAR(15)  NOT NULL,
    CONSTRAINT PK_TipoClase        PRIMARY KEY (TipoClaseID),
    CONSTRAINT UQ_TipoClase_Nombre UNIQUE (Nombre),
    CONSTRAINT CK_TipoClase_Dur    CHECK (DuracionMin > 0),
    CONSTRAINT CK_TipoClase_Nivel  CHECK (Nivel IN ('Principiante','Intermedio','Avanzado'))
);
GO

CREATE TABLE clases.Sala (
    SalaID    INT IDENTITY(1,1) NOT NULL,
    Nombre    VARCHAR(50) NOT NULL,
    Capacidad SMALLINT    NOT NULL,
    CONSTRAINT PK_Sala        PRIMARY KEY (SalaID),
    CONSTRAINT UQ_Sala_Nombre UNIQUE (Nombre),
    CONSTRAINT CK_Sala_Cap    CHECK (Capacidad > 0)
);
GO

CREATE TABLE clases.SesionClase (
    SesionID     INT IDENTITY(1,1) NOT NULL,
    TipoClaseID  INT          NOT NULL,
    EntrenadorID INT          NOT NULL,
    SalaID       INT          NOT NULL,
    FechaHora    DATETIME2(0) NOT NULL,
    CupoMaximo   SMALLINT     NOT NULL,
    Estado       VARCHAR(12)  NOT NULL CONSTRAINT DF_Sesion_Estado DEFAULT ('Programada'),
    CONSTRAINT PK_SesionClase       PRIMARY KEY (SesionID),
    CONSTRAINT FK_Sesion_TipoClase  FOREIGN KEY (TipoClaseID)  REFERENCES clases.TipoClase(TipoClaseID),
    CONSTRAINT FK_Sesion_Entrenador FOREIGN KEY (EntrenadorID) REFERENCES clases.Entrenador(EntrenadorID),
    CONSTRAINT FK_Sesion_Sala       FOREIGN KEY (SalaID)       REFERENCES clases.Sala(SalaID),
    CONSTRAINT UQ_Sesion_SalaHora   UNIQUE (SalaID, FechaHora),  -- una sala no puede tener 2 clases a la vez
    CONSTRAINT CK_Sesion_Cupo       CHECK (CupoMaximo > 0),
    CONSTRAINT CK_Sesion_Estado     CHECK (Estado IN ('Programada','Realizada','Cancelada'))
);
GO

CREATE TABLE clases.Reserva (
    ReservaID     INT IDENTITY(1,1) NOT NULL,
    SesionID      INT          NOT NULL,
    SocioID       INT          NOT NULL,
    FechaReserva  DATETIME2(0) NOT NULL CONSTRAINT DF_Reserva_Fecha  DEFAULT (SYSDATETIME()),
    Estado        VARCHAR(10)  NOT NULL CONSTRAINT DF_Reserva_Estado DEFAULT ('Confirmada'),
    CONSTRAINT PK_Reserva         PRIMARY KEY (ReservaID),
    CONSTRAINT FK_Reserva_Sesion  FOREIGN KEY (SesionID) REFERENCES clases.SesionClase(SesionID),
    CONSTRAINT FK_Reserva_Socio   FOREIGN KEY (SocioID)  REFERENCES socios.Socio(SocioID),
    CONSTRAINT UQ_Reserva_SesSoc  UNIQUE (SesionID, SocioID),  -- sin reservas duplicadas
    CONSTRAINT CK_Reserva_Estado  CHECK (Estado IN ('Confirmada','Cancelada'))
);
GO

CREATE TABLE clases.Asistencia (
    ReservaID    INT          NOT NULL,   
    FechaCheckIn DATETIME2(0) NULL,
    Asistio      BIT          NOT NULL,
    CONSTRAINT PK_Asistencia         PRIMARY KEY (ReservaID),
    CONSTRAINT FK_Asistencia_Reserva FOREIGN KEY (ReservaID) REFERENCES clases.Reserva(ReservaID),
    CONSTRAINT CK_Asistencia_CheckIn CHECK (Asistio = 1 OR FechaCheckIn IS NULL)
);
GO

-- Esquema finanzas
CREATE TABLE finanzas.Pago (
    PagoID      INT IDENTITY(1,1) NOT NULL,
    MembresiaID INT          NOT NULL,
    Monto       DECIMAL(8,2) NOT NULL,
    FechaPago   DATETIME2(0) NOT NULL CONSTRAINT DF_Pago_Fecha  DEFAULT (SYSDATETIME()),
    MetodoPago  VARCHAR(15)  NOT NULL,
    Estado      VARCHAR(10)  NOT NULL CONSTRAINT DF_Pago_Estado DEFAULT ('Pagado'),
    CONSTRAINT PK_Pago            PRIMARY KEY (PagoID),
    CONSTRAINT FK_Pago_Membresia  FOREIGN KEY (MembresiaID) REFERENCES socios.Membresia(MembresiaID),
    CONSTRAINT CK_Pago_Monto      CHECK (Monto > 0),
    CONSTRAINT CK_Pago_Metodo     CHECK (MetodoPago IN ('Efectivo','Tarjeta','Transferencia')),
    CONSTRAINT CK_Pago_Estado     CHECK (Estado IN ('Pagado','Pendiente','Anulado'))
);
GO

-- Verificación de lista de tablas creadas por esquema
SELECT s.name AS Esquema, t.name AS Tabla
FROM sys.tables t
JOIN sys.schemas s ON s.schema_id = t.schema_id
ORDER BY s.name, t.name;
GO