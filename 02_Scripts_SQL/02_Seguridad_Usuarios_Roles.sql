USE master;
GO

--Creacion de login 
IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = N'login_recepcion')
    CREATE LOGIN login_recepcion WITH PASSWORD = N'Recep#Gym2026!', DEFAULT_DATABASE = GimnasioDB, CHECK_EXPIRATION = OFF;
IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = N'login_entrenador')
    CREATE LOGIN login_entrenador WITH PASSWORD = N'Entre#Gym2026!', DEFAULT_DATABASE = GimnasioDB, CHECK_EXPIRATION = OFF;
IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = N'login_finanzas')
    CREATE LOGIN login_finanzas WITH PASSWORD = N'Finan#Gym2026!', DEFAULT_DATABASE = GimnasioDB, CHECK_EXPIRATION = OFF;
IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = N'login_bi')
    CREATE LOGIN login_bi WITH PASSWORD = N'Report#Gym2026!', DEFAULT_DATABASE = GimnasioDB, CHECK_EXPIRATION = OFF;
IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = N'login_admin')
    CREATE LOGIN login_admin WITH PASSWORD = N'Admin#Gym2026!', DEFAULT_DATABASE = GimnasioDB, CHECK_EXPIRATION = OFF;
GO

USE GimnasioDB;
GO

--Usuarios de la Base de Datos
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'usr_recepcion')  CREATE USER usr_recepcion  FOR LOGIN login_recepcion;
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'usr_entrenador') CREATE USER usr_entrenador FOR LOGIN login_entrenador;
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'usr_finanzas')   CREATE USER usr_finanzas   FOR LOGIN login_finanzas;
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'usr_bi')         CREATE USER usr_bi         FOR LOGIN login_bi;
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'usr_admin')      CREATE USER usr_admin      FOR LOGIN login_admin;
GO

--Creacin de roles 
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'rolRecepcion'  AND type = 'R') CREATE ROLE rolRecepcion;
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'rolEntrenador' AND type = 'R') CREATE ROLE rolEntrenador;
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'rolFinanzas'   AND type = 'R') CREATE ROLE rolFinanzas;
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'rolBI'         AND type = 'R') CREATE ROLE rolBI;
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'rolAdminBD'    AND type = 'R') CREATE ROLE rolAdminBD;
GO

--Asignacion de Usuarios a los roles 
ALTER ROLE rolRecepcion  ADD MEMBER usr_recepcion;
ALTER ROLE rolEntrenador ADD MEMBER usr_entrenador;
ALTER ROLE rolFinanzas   ADD MEMBER usr_finanzas;
ALTER ROLE rolBI         ADD MEMBER usr_bi;
ALTER ROLE rolAdminBD    ADD MEMBER usr_admin;
GO

--Permisos para la Recepcion (Gestionar Socios, pagos y asistencias)
-- RECEPCION
GRANT SELECT, INSERT, UPDATE ON socios.Socio       TO rolRecepcion;
GRANT SELECT, INSERT, UPDATE ON socios.Membresia   TO rolRecepcion;
GRANT SELECT                 ON socios.PlanMembresia TO rolRecepcion;
GRANT SELECT, INSERT         ON finanzas.Pago      TO rolRecepcion;
GRANT SELECT, INSERT, UPDATE ON clases.Reserva     TO rolRecepcion;
GRANT SELECT, INSERT, UPDATE ON clases.Asistencia  TO rolRecepcion;
GRANT SELECT ON clases.SesionClase TO rolRecepcion;
GRANT SELECT ON clases.TipoClase   TO rolRecepcion;
GRANT SELECT ON clases.Sala        TO rolRecepcion;
GRANT SELECT ON clases.Entrenador  TO rolRecepcion;
DENY DELETE ON SCHEMA::socios   TO rolRecepcion;
DENY DELETE ON SCHEMA::clases   TO rolRecepcion;
DENY DELETE ON SCHEMA::finanzas TO rolRecepcion;
DENY UPDATE ON finanzas.Pago    TO rolRecepcion;
GO

--Permisos para los Entrenadores (Ver sesiones, entredores, y gestionar la asistencia)
GRANT SELECT ON clases.SesionClase TO rolEntrenador;
GRANT SELECT ON clases.TipoClase   TO rolEntrenador;
GRANT SELECT ON clases.Sala        TO rolEntrenador;
GRANT SELECT ON clases.Reserva     TO rolEntrenador;
GRANT SELECT, INSERT, UPDATE ON clases.Asistencia TO rolEntrenador;
GRANT SELECT (SocioID, Nombre, Apellido) ON socios.Socio TO rolEntrenador;
DENY  SELECT (Documento, Email, Telefono, FechaNacimiento) ON socios.Socio TO rolEntrenador;
DENY SELECT ON SCHEMA::finanzas TO rolEntrenador;
DENY DELETE ON SCHEMA::clases   TO rolEntrenador;
GO

--Permisos para el de finanzas 
GRANT SELECT, INSERT, UPDATE ON finanzas.Pago TO rolFinanzas;
GRANT SELECT ON socios.Membresia     TO rolFinanzas;
GRANT SELECT ON socios.PlanMembresia TO rolFinanzas;
GRANT SELECT (SocioID, Nombre, Apellido) ON socios.Socio TO rolFinanzas;
DENY DELETE ON SCHEMA::finanzas TO rolFinanzas;
GO

--Permisos para el encargado de BI
GRANT SELECT ON SCHEMA::reportes TO rolBI;
GO

--Administrador de la Base de Datos 
ALTER ROLE db_ddladmin       ADD MEMBER rolAdminBD;
ALTER ROLE db_backupoperator ADD MEMBER rolAdminBD;
GRANT VIEW DEFINITION    TO rolAdminBD;
GRANT VIEW DATABASE STATE TO rolAdminBD;
GO