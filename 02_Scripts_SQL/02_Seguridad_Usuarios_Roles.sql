use GimnasioDB;
go

--Creacion de rol para la Recepcion 
IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'rolRecepcion' AND type = 'R')
    CREATE ROLE rolRecepcion;
GO

--Creacion de rol para los Entrenadores 
IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'rolEntrenador' AND type = 'R')
    CREATE ROLE rolEntrenador;
GO

--Permisos para la Recepcion (Gestionar Socios, pagos y asistencias)
grant select, insert, update on schema::socios to rolRecepcion;
grant select, insert, update on schema::finanzas to rolRecepcion;
grant select, insert, update, delete on clases.Asistencia to rolRecepcion;
grant select, insert, update, delete on clases.Reserva to rolRecepcion;
go

--Permisos para los Entrenadores (Ver sesiones, entredores, y gestionar la asistencia)
grant select on schema::socios to rolEntrenador;
grant select, update on clases.SesionClase to rolEntrenador;
grant select, insert, update on clases.Asistencia to rolEntrenador;
go