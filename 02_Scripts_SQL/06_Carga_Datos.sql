USE GimnasioDB;
GO

SET NOCOUNT ON;

DECLARE @ruta NVARCHAR(400) = N'/var/opt/mssql/datos_csv/';
DECLARE @limpiar BIT           = 1;       

DECLARE @archivos TABLE (
    Orden   INT PRIMARY KEY,
    Tabla   NVARCHAR(128),
    Archivo NVARCHAR(128),
    ConID   BIT                
);

INSERT INTO @archivos (Orden, Tabla, Archivo, ConID) VALUES
    (1,  N'socios.Socio',          N'socios.csv',        1),
    (2,  N'socios.PlanMembresia',  N'planes.csv',        1),
    (3,  N'clases.Entrenador',     N'entrenadores.csv',  1),
    (4,  N'clases.TipoClase',      N'tipos_clase.csv',   1),
    (5,  N'clases.Sala',           N'salas.csv',         1),
    (6,  N'socios.Membresia',      N'membresias.csv',    1),
    (7,  N'clases.SesionClase',    N'sesiones.csv',      1),
    (8,  N'finanzas.Pago',         N'pagos.csv',         1),
    (9,  N'clases.Reserva',        N'reservas.csv',      1),
    (10, N'clases.Asistencia',     N'asistencias.csv',   0);

DECLARE @orden   INT = 1;
DECLARE @tabla   NVARCHAR(128);
DECLARE @archivo NVARCHAR(128);
DECLARE @conID   BIT;
DECLARE @sql     NVARCHAR(MAX);

BEGIN TRY
    BEGIN TRANSACTION;

    IF @limpiar = 1
    BEGIN
        PRINT N'Borrando datos anteriores...';
        DELETE FROM clases.Asistencia;
        DELETE FROM clases.Reserva;
        DELETE FROM finanzas.Pago;
        DELETE FROM clases.SesionClase;
        DELETE FROM socios.Membresia;
        DELETE FROM clases.Sala;
        DELETE FROM clases.TipoClase;
        DELETE FROM clases.Entrenador;
        DELETE FROM socios.PlanMembresia;
        DELETE FROM socios.Socio;
    END

    WHILE @orden <= (SELECT MAX(Orden) FROM @archivos)
    BEGIN
        SELECT @tabla = Tabla, @archivo = Archivo, @conID = ConID
        FROM @archivos
        WHERE Orden = @orden;

        SET @sql = N'BULK INSERT ' + @tabla
                 + N' FROM ''' + @ruta + @archivo + N''''
                 + N' WITH (FIRSTROW = 2, FIELDTERMINATOR = '','', ROWTERMINATOR = ''0x0d0a'','
                 + N' KEEPNULLS, CHECK_CONSTRAINTS, TABLOCK'
                 + CASE WHEN @conID = 1 THEN N', KEEPIDENTITY' ELSE N'' END
                 + N');';

        PRINT N'Cargando ' + @tabla + N' desde ' + @archivo + N' ...';
        EXEC sys.sp_executesql @sql;

        SET @orden += 1;
    END

    COMMIT TRANSACTION;
    PRINT N'Carga terminada correctamente.';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    PRINT N'ERROR: la carga se cancelo y no se guardo nada.';
    THROW;
END CATCH;
GO

SELECT 'socios.Socio' AS Tabla, COUNT(*) AS Filas, 2000 AS Esperadas,
       CASE WHEN COUNT(*) = 2000 THEN 'OK' ELSE 'DIFERENCIA' END AS Resultado FROM socios.Socio
UNION ALL SELECT 'socios.PlanMembresia', COUNT(*), 5,     CASE WHEN COUNT(*) = 5     THEN 'OK' ELSE 'DIFERENCIA' END FROM socios.PlanMembresia
UNION ALL SELECT 'clases.Entrenador',    COUNT(*), 15,    CASE WHEN COUNT(*) = 15    THEN 'OK' ELSE 'DIFERENCIA' END FROM clases.Entrenador
UNION ALL SELECT 'clases.TipoClase',     COUNT(*), 12,    CASE WHEN COUNT(*) = 12    THEN 'OK' ELSE 'DIFERENCIA' END FROM clases.TipoClase
UNION ALL SELECT 'clases.Sala',          COUNT(*), 5,     CASE WHEN COUNT(*) = 5     THEN 'OK' ELSE 'DIFERENCIA' END FROM clases.Sala
UNION ALL SELECT 'socios.Membresia',     COUNT(*), 4800,  CASE WHEN COUNT(*) = 4800  THEN 'OK' ELSE 'DIFERENCIA' END FROM socios.Membresia
UNION ALL SELECT 'clases.SesionClase',   COUNT(*), 3000,  CASE WHEN COUNT(*) = 3000  THEN 'OK' ELSE 'DIFERENCIA' END FROM clases.SesionClase
UNION ALL SELECT 'finanzas.Pago',        COUNT(*), 9199,  CASE WHEN COUNT(*) = 9199  THEN 'OK' ELSE 'DIFERENCIA' END FROM finanzas.Pago
UNION ALL SELECT 'clases.Reserva',       COUNT(*), 24545, CASE WHEN COUNT(*) = 24545 THEN 'OK' ELSE 'DIFERENCIA' END FROM clases.Reserva
UNION ALL SELECT 'clases.Asistencia',    COUNT(*), 21284, CASE WHEN COUNT(*) = 21284 THEN 'OK' ELSE 'DIFERENCIA' END FROM clases.Asistencia;
GO

SELECT 'FOREIGN KEY' AS Tipo, name AS Restriccion FROM sys.foreign_keys    WHERE is_not_trusted = 1
UNION ALL
SELECT 'CHECK',               name                 FROM sys.check_constraints WHERE is_not_trusted = 1;
GO


SELECT SUM(Monto) AS IngresoSinAnulados FROM finanzas.Pago WHERE Estado <> 'Anulado';

SELECT Estado, COUNT(*) AS Reservas FROM clases.Reserva GROUP BY Estado ORDER BY Estado;

SELECT r.SesionID, s.CupoMaximo, COUNT(*) AS Confirmadas
FROM clases.Reserva r
JOIN clases.SesionClase s ON s.SesionID = r.SesionID
WHERE r.Estado = 'Confirmada'
GROUP BY r.SesionID, s.CupoMaximo
HAVING COUNT(*) > s.CupoMaximo;

SELECT COUNT(*) AS CheckInNulos FROM clases.Asistencia WHERE FechaCheckIn IS NULL;

SELECT TOP 5 EntrenadorID, Nombre, Apellido, Especialidad FROM clases.Entrenador ORDER BY EntrenadorID;

SELECT IDENT_CURRENT('socios.Socio') AS UltimoIDSocio, IDENT_CURRENT('clases.Reserva') AS UltimoIDReserva;
GO