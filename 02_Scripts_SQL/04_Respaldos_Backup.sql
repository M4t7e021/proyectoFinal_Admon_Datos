use master;
go

--Declarar la ruta y todas las variables al inicio de la sesión
declare @RutaBackup nvarchar(300) = N'/var/opt/mssql/backup/';
declare @PathFull nvarchar(400) = @RutaBackup + N'GimnasioDB_Full.bak';
declare @PathDiff nvarchar(400) = @RutaBackup + N'GimnasioDB_Diff.bak';
declare @PathLog  nvarchar(400) = @RutaBackup + N'GimnasioDB_Log.trn';

--Respaldo FULL BACKUP de toda la Base de Datos	
backup database GimnasioDB
	to disk = @PathFull
	with format, init, name = N'Gimnasio_Respaldo Completo' ,
	stats = 10;

--Respaldo diferencial 
backup database GimnasioDB
	to disk = @PathDiff
	with differential, name = N'Gimnasio_Respaldo Diferencial',
	stats = 10;

--Respaldo del log de transacciones (Para una recuperacion ante fallos)
backup log GimnasioDB
to disk = @PathLog
with name = N'Gimnasio_Respaldo de Transacciones',
	stats = 10;