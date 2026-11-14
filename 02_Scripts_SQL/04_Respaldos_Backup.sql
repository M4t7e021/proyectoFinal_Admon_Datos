USE master;
GO
--Declarar la ruta y todas las variables al inicio de la sesión
DECLARE @ruta  NVARCHAR(300) = N'/var/opt/mssql/backup/';
DECLARE @sello VARCHAR(20)   = CONVERT(VARCHAR(8), GETDATE(), 112) + '_' + REPLACE(CONVERT(VARCHAR(8), GETDATE(), 108), ':', '');
DECLARE @full  NVARCHAR(400) = @ruta + N'GimnasioDB_FULL_' + @sello + N'.bak';
DECLARE @diff  NVARCHAR(400) = @ruta + N'GimnasioDB_DIFF_' + @sello + N'.bak';
DECLARE @log   NVARCHAR(400) = @ruta + N'GimnasioDB_LOG_'  + @sello + N'.trn';

--Respaldo FULL BACKUP de toda la Base de Datos	
BACKUP DATABASE GimnasioDB TO DISK = @full
    WITH COMPRESSION, CHECKSUM, INIT, NAME = N'GimnasioDB - Completo', STATS = 25;
RESTORE VERIFYONLY FROM DISK = @full WITH CHECKSUM;

--Respaldo diferencial 
BACKUP DATABASE GimnasioDB TO DISK = @diff
    WITH DIFFERENTIAL, COMPRESSION, CHECKSUM, INIT, NAME = N'GimnasioDB - Diferencial', STATS = 25;
RESTORE VERIFYONLY FROM DISK = @diff WITH CHECKSUM;

--Respaldo del log de transacciones (Para una recuperacion ante fallos)
BACKUP LOG GimnasioDB TO DISK = @log
    WITH COMPRESSION, CHECKSUM, INIT, NAME = N'GimnasioDB - Log', STATS = 25;
RESTORE VERIFYONLY FROM DISK = @log WITH CHECKSUM;
GO

--Consulta de verificacion de backup, mostrara los respaldos hechos y el tamaño que tienen cada uno 
SELECT TOP 5 bs.backup_start_date AS Inicio,
       CASE bs.type WHEN 'D' THEN 'Completo' WHEN 'I' THEN 'Diferencial' WHEN 'L' THEN 'Log' END AS Tipo,
       CAST(bs.compressed_backup_size / 1048576.0 AS DECIMAL(10,2)) AS MB_Comprimidos,
       bmf.physical_device_name AS Archivo
FROM   msdb.dbo.backupset bs
JOIN   msdb.dbo.backupmediafamily bmf ON bmf.media_set_id = bs.media_set_id
WHERE  bs.database_name = N'GimnasioDB'
ORDER BY bs.backup_start_date DESC;
GO