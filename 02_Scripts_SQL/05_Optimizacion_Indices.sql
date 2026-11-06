

USE GimnasioDB;
GO
SET ANSI_NULLS ON;            
SET QUOTED_IDENTIFIER ON;
GO


/* Borrar los indices de optimizacion (nuevos y de versiones anteriores del
   script) para que el "antes" siempre parta del mismo estado: solo los indices
   que SQL Server crea por las PK y los UNIQUE. */
DROP INDEX IF EXISTS IX_Reserva_Estado_Sesion  ON clases.Reserva;
DROP INDEX IF EXISTS IX_Reserva_Socio_Fecha    ON clases.Reserva;
DROP INDEX IF EXISTS IX_Pago_Fecha_Pagado      ON finanzas.Pago;
DROP INDEX IF EXISTS IX_Reserva_Socio          ON clases.Reserva;     
DROP INDEX IF EXISTS IX_Reserva_Sesion_Estado  ON clases.Reserva;      
DROP INDEX IF EXISTS IX_Membresia_Socio_Inicio ON socios.Membresia;    
DROP INDEX IF EXISTS IX_Pago_Estado_Fecha      ON finanzas.Pago;       
GO

/* BLOQUE 0: Indices que existen ANTES de optimizar.
   Resultado esperado: 18 indices (los de las PK y los UNIQUE). */
SELECT  s.name  AS Esquema,
        t.name  AS Tabla,
        i.name  AS Indice,
        i.type_desc AS Tipo,
        i.is_unique AS EsUnico,
        i.has_filter AS EsFiltrado,
        STUFF((SELECT ', ' + c.name
               FROM sys.index_columns ic
               JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id
               WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id
                 AND ic.is_included_column = 0
               ORDER BY ic.key_ordinal
               FOR XML PATH('')), 1, 2, '') AS Columnas
FROM sys.indexes i
JOIN sys.tables  t ON t.object_id = i.object_id
JOIN sys.schemas s ON s.schema_id = t.schema_id
WHERE i.type > 0
ORDER BY s.name, t.name, i.index_id;
GO

/* 
   CONSULTA 1 - ANTES
    */
SET STATISTICS IO ON;
SET STATISTICS TIME ON;
SET STATISTICS XML ON;
CHECKPOINT;
DBCC DROPCLEANBUFFERS;   
GO

-- CONSULTA 1: Top 3 de clases mas reservadas en cada mes (ultimos 6 meses).
DECLARE @FechaCorte DATE = '2026-10-25';
DECLARE @Desde      DATE = DATEADD(MONTH, -5, DATEFROMPARTS(YEAR(@FechaCorte), MONTH(@FechaCorte), 1));
DECLARE @Hasta      DATE = DATEADD(DAY, 1, @FechaCorte);

WITH ReservasPorClase AS (
    SELECT  DATEFROMPARTS(YEAR(se.FechaHora), MONTH(se.FechaHora), 1) AS Mes,
            tc.Nombre AS Clase,
            COUNT(*)  AS Reservas
    FROM    clases.Reserva     r
    JOIN    clases.SesionClase se ON se.SesionID    = r.SesionID
    JOIN    clases.TipoClase   tc ON tc.TipoClaseID = se.TipoClaseID
    WHERE   r.Estado  = 'Confirmada'
      AND   se.Estado = 'Realizada'
      AND   se.FechaHora >= @Desde
      AND   se.FechaHora <  @Hasta
    GROUP BY DATEFROMPARTS(YEAR(se.FechaHora), MONTH(se.FechaHora), 1), tc.Nombre
),
Ranking AS (
    SELECT  Mes, Clase, Reservas,
            DENSE_RANK() OVER (PARTITION BY Mes ORDER BY Reservas DESC) AS Posicion,
            CAST(100.0 * Reservas / SUM(Reservas) OVER (PARTITION BY Mes) AS DECIMAL(5,1)) AS PctDelMes
    FROM    ReservasPorClase
)
SELECT  Mes, Posicion, Clase, Reservas, PctDelMes
FROM    Ranking
WHERE   Posicion <= 3
ORDER BY Mes, Posicion, Clase
OPTION (RECOMPILE);
GO

SET STATISTICS XML OFF;
SET STATISTICS IO OFF;
SET STATISTICS TIME OFF;
GO

/* 
   CONSULTA 2 - ANTES
   */
SET STATISTICS IO ON;
SET STATISTICS TIME ON;
SET STATISTICS XML ON;
CHECKPOINT;
DBCC DROPCLEANBUFFERS;   
GO

-- CONSULTA 2: Ingresos por mes con una columna por metodo de pago, variacion contra
-- el mes anterior y acumulado del anio (solo pagos con estado 'Pagado').
WITH PagosMes AS (
    SELECT  DATEFROMPARTS(YEAR(p.FechaPago), MONTH(p.FechaPago), 1) AS Mes,
            p.MetodoPago,
            p.Monto
    FROM    finanzas.Pago p
    WHERE   p.Estado = 'Pagado'
),
Pivoteado AS (
    SELECT  Mes,
            ISNULL([Efectivo],      0) AS Efectivo,
            ISNULL([Tarjeta],       0) AS Tarjeta,
            ISNULL([Transferencia], 0) AS Transferencia
    FROM    PagosMes
    PIVOT  (SUM(Monto) FOR MetodoPago IN ([Efectivo], [Tarjeta], [Transferencia])) AS pv
),
Totales AS (
    SELECT  Mes, Efectivo, Tarjeta, Transferencia,
            Efectivo + Tarjeta + Transferencia AS Total
    FROM    Pivoteado
)
SELECT  Mes,
        Efectivo, Tarjeta, Transferencia, Total,
        LAG(Total) OVER (ORDER BY Mes) AS TotalMesAnterior,
        CAST(100.0 * (Total - LAG(Total) OVER (ORDER BY Mes))
             / NULLIF(LAG(Total) OVER (ORDER BY Mes), 0) AS DECIMAL(7,2)) AS VariacionPct,
        SUM(Total) OVER (PARTITION BY YEAR(Mes)
                         ORDER BY Mes
                         ROWS UNBOUNDED PRECEDING) AS AcumuladoAnio
FROM    Totales
ORDER BY Mes;
GO

SET STATISTICS XML OFF;
SET STATISTICS IO OFF;
SET STATISTICS TIME OFF;
GO

/* 
   CONSULTA 3 - ANTES
    */
SET STATISTICS IO ON;
SET STATISTICS TIME ON;
SET STATISTICS XML ON;
CHECKPOINT;
DBCC DROPCLEANBUFFERS;   
GO

-- CONSULTA 3: Socios con membresia activa que llevan 30 dias o mas sin reservar
-- (o que nunca han reservado): candidatos a una llamada de retencion.
DECLARE @FechaCorte   DATE = '2026-10-25';
DECLARE @DiasInactivo INT  = 30;

WITH UltimaReserva AS (
    SELECT  r.SocioID,
            r.FechaReserva,
            ROW_NUMBER() OVER (PARTITION BY r.SocioID
                               ORDER BY r.FechaReserva DESC) AS rn
    FROM    clases.Reserva r
    WHERE   r.Estado = 'Confirmada'
)
SELECT  s.SocioID, s.Nombre, s.Apellido,
        pm.Nombre  AS PlanActual,
        m.FechaFin AS MembresiaVigenteHasta,
        u.FechaReserva AS UltimaReserva,
        DATEDIFF(DAY, u.FechaReserva, @FechaCorte) AS DiasSinReservar
FROM    socios.Membresia     m
JOIN    socios.Socio         s  ON s.SocioID = m.SocioID
JOIN    socios.PlanMembresia pm ON pm.PlanID = m.PlanID
LEFT JOIN UltimaReserva      u  ON u.SocioID = s.SocioID AND u.rn = 1
WHERE   m.Estado = 'Activa'
  AND   m.FechaInicio <= @FechaCorte
  AND   m.FechaFin    >= @FechaCorte
  AND  (u.FechaReserva IS NULL OR DATEDIFF(DAY, u.FechaReserva, @FechaCorte) >= @DiasInactivo)
ORDER BY CASE WHEN u.FechaReserva IS NULL THEN 0 ELSE 1 END, DiasSinReservar DESC, s.SocioID
OPTION (RECOMPILE);
GO

SET STATISTICS XML OFF;
SET STATISTICS IO OFF;
SET STATISTICS TIME OFF;
GO

/* BLOQUE A  -  Tamano de tablas e indices ANTES (tomar captura) */
SELECT  s.name AS Esquema,
        t.name AS Tabla,
        i.name AS Indice,
        i.type_desc AS Tipo,
        SUM(ps.row_count)         AS Filas,
        SUM(ps.used_page_count)   AS Paginas,
        SUM(ps.used_page_count) * 8 AS KB
FROM    sys.dm_db_partition_stats ps
JOIN    sys.indexes i ON i.object_id = ps.object_id AND i.index_id = ps.index_id
JOIN    sys.tables  t ON t.object_id = i.object_id
JOIN    sys.schemas s ON s.schema_id = t.schema_id
GROUP BY s.name, t.name, i.name, i.type_desc, i.index_id
ORDER BY s.name, t.name, i.index_id;
GO

SELECT  s.name AS Esquema,
        t.name AS Tabla,
        SUM(CASE WHEN i.index_id IN (0,1) THEN ps.used_page_count ELSE 0 END) * 8 AS KB_Datos,
        SUM(CASE WHEN i.index_id >  1     THEN ps.used_page_count ELSE 0 END) * 8 AS KB_Indices,
        SUM(ps.used_page_count) * 8 AS KB_Total,
        CAST(SUM(ps.used_page_count) * 1.0
             / NULLIF(SUM(CASE WHEN i.index_id IN (0,1) THEN ps.used_page_count ELSE 0 END), 0)
             AS DECIMAL(5,2)) AS FactorIndices
FROM    sys.dm_db_partition_stats ps
JOIN    sys.indexes i ON i.object_id = ps.object_id AND i.index_id = ps.index_id
JOIN    sys.tables  t ON t.object_id = i.object_id
JOIN    sys.schemas s ON s.schema_id = t.schema_id
GROUP BY s.name, t.name
ORDER BY s.name, t.name;
GO

/* 
   BLOQUE B  -  Crear los 3 indices
   */

-- CONSULTA 1: IGUALDAD PRIMERO, UNION DESPUES.
CREATE NONCLUSTERED INDEX IX_Reserva_Estado_Sesion
    ON clases.Reserva (Estado, SesionID);
GO

-- CONSULTA 2: INDICE FILTRADO.
CREATE NONCLUSTERED INDEX IX_Pago_Fecha_Pagado
    ON finanzas.Pago (FechaPago)
    INCLUDE (MetodoPago, Monto)
    WHERE Estado = 'Pagado';
GO

-- CONSULTA 3: INDICE A LA MEDIDA DE LA FUNCION VENTANA.
CREATE NONCLUSTERED INDEX IX_Reserva_Socio_Fecha
    ON clases.Reserva (SocioID, FechaReserva DESC)
    INCLUDE (Estado);
GO


UPDATE STATISTICS clases.Reserva WITH FULLSCAN;
UPDATE STATISTICS finanzas.Pago  WITH FULLSCAN;
GO

/* BLOQUE C  -  Tamano de tablas e indices DESPUES (tomar captura;
   es la misma consulta del bloque A) */
SELECT  s.name AS Esquema,
        t.name AS Tabla,
        i.name AS Indice,
        i.type_desc AS Tipo,
        SUM(ps.row_count)         AS Filas,
        SUM(ps.used_page_count)   AS Paginas,
        SUM(ps.used_page_count) * 8 AS KB
FROM    sys.dm_db_partition_stats ps
JOIN    sys.indexes i ON i.object_id = ps.object_id AND i.index_id = ps.index_id
JOIN    sys.tables  t ON t.object_id = i.object_id
JOIN    sys.schemas s ON s.schema_id = t.schema_id
GROUP BY s.name, t.name, i.name, i.type_desc, i.index_id
ORDER BY s.name, t.name, i.index_id;
GO

SELECT  s.name AS Esquema,
        t.name AS Tabla,
        SUM(CASE WHEN i.index_id IN (0,1) THEN ps.used_page_count ELSE 0 END) * 8 AS KB_Datos,
        SUM(CASE WHEN i.index_id >  1     THEN ps.used_page_count ELSE 0 END) * 8 AS KB_Indices,
        SUM(ps.used_page_count) * 8 AS KB_Total,
        CAST(SUM(ps.used_page_count) * 1.0
             / NULLIF(SUM(CASE WHEN i.index_id IN (0,1) THEN ps.used_page_count ELSE 0 END), 0)
             AS DECIMAL(5,2)) AS FactorIndices
FROM    sys.dm_db_partition_stats ps
JOIN    sys.indexes i ON i.object_id = ps.object_id AND i.index_id = ps.index_id
JOIN    sys.tables  t ON t.object_id = i.object_id
JOIN    sys.schemas s ON s.schema_id = t.schema_id
GROUP BY s.name, t.name
ORDER BY s.name, t.name;
GO

-- BLOQUE D  -  Comprobar que ahora hay 21 indices (18 + los 3 nuevos) 
SELECT COUNT(*) AS TotalIndices
FROM   sys.indexes i
JOIN   sys.tables  t ON t.object_id = i.object_id
WHERE  i.type > 0;                                   

SELECT s.name AS Esquema, t.name AS Tabla, i.name AS IndiceNuevo, i.has_filter AS EsFiltrado
FROM   sys.indexes i
JOIN   sys.tables  t ON t.object_id = i.object_id
JOIN   sys.schemas s ON s.schema_id = t.schema_id
WHERE  i.name LIKE 'IX[_]%'
ORDER BY s.name, t.name, i.name;                      
GO



  -- PARTE 3 - DESPUES (con los indices nuevos)
/* ---------------------------------------------------------------------
   CONSULTA 1 - DESPUES
   --------------------------------------------------------------------- */
SET STATISTICS IO ON;
SET STATISTICS TIME ON;
SET STATISTICS XML ON;
CHECKPOINT;
DBCC DROPCLEANBUFFERS;   
GO

-- CONSULTA 1: Top 3 de clases mas reservadas en cada mes (ultimos 6 meses).
DECLARE @FechaCorte DATE = '2026-10-25';
DECLARE @Desde      DATE = DATEADD(MONTH, -5, DATEFROMPARTS(YEAR(@FechaCorte), MONTH(@FechaCorte), 1));
DECLARE @Hasta      DATE = DATEADD(DAY, 1, @FechaCorte);

WITH ReservasPorClase AS (
    SELECT  DATEFROMPARTS(YEAR(se.FechaHora), MONTH(se.FechaHora), 1) AS Mes,
            tc.Nombre AS Clase,
            COUNT(*)  AS Reservas
    FROM    clases.Reserva     r
    JOIN    clases.SesionClase se ON se.SesionID    = r.SesionID
    JOIN    clases.TipoClase   tc ON tc.TipoClaseID = se.TipoClaseID
    WHERE   r.Estado  = 'Confirmada'
      AND   se.Estado = 'Realizada'
      AND   se.FechaHora >= @Desde
      AND   se.FechaHora <  @Hasta
    GROUP BY DATEFROMPARTS(YEAR(se.FechaHora), MONTH(se.FechaHora), 1), tc.Nombre
),
Ranking AS (
    SELECT  Mes, Clase, Reservas,
            DENSE_RANK() OVER (PARTITION BY Mes ORDER BY Reservas DESC) AS Posicion,
            CAST(100.0 * Reservas / SUM(Reservas) OVER (PARTITION BY Mes) AS DECIMAL(5,1)) AS PctDelMes
    FROM    ReservasPorClase
)
SELECT  Mes, Posicion, Clase, Reservas, PctDelMes
FROM    Ranking
WHERE   Posicion <= 3
ORDER BY Mes, Posicion, Clase
OPTION (RECOMPILE);
GO

SET STATISTICS XML OFF;
SET STATISTICS IO OFF;
SET STATISTICS TIME OFF;
GO

/* 
   CONSULTA 2 - DESPUES
   */
SET STATISTICS IO ON;
SET STATISTICS TIME ON;
SET STATISTICS XML ON;
CHECKPOINT;
DBCC DROPCLEANBUFFERS;   
GO

-- CONSULTA 2: Ingresos por mes con una columna por metodo de pago, variacion contra
-- el mes anterior y acumulado del anio (solo pagos con estado 'Pagado').
WITH PagosMes AS (
    SELECT  DATEFROMPARTS(YEAR(p.FechaPago), MONTH(p.FechaPago), 1) AS Mes,
            p.MetodoPago,
            p.Monto
    FROM    finanzas.Pago p
    WHERE   p.Estado = 'Pagado'
),
Pivoteado AS (
    SELECT  Mes,
            ISNULL([Efectivo],      0) AS Efectivo,
            ISNULL([Tarjeta],       0) AS Tarjeta,
            ISNULL([Transferencia], 0) AS Transferencia
    FROM    PagosMes
    PIVOT  (SUM(Monto) FOR MetodoPago IN ([Efectivo], [Tarjeta], [Transferencia])) AS pv
),
Totales AS (
    SELECT  Mes, Efectivo, Tarjeta, Transferencia,
            Efectivo + Tarjeta + Transferencia AS Total
    FROM    Pivoteado
)
SELECT  Mes,
        Efectivo, Tarjeta, Transferencia, Total,
        LAG(Total) OVER (ORDER BY Mes) AS TotalMesAnterior,
        CAST(100.0 * (Total - LAG(Total) OVER (ORDER BY Mes))
             / NULLIF(LAG(Total) OVER (ORDER BY Mes), 0) AS DECIMAL(7,2)) AS VariacionPct,
        SUM(Total) OVER (PARTITION BY YEAR(Mes)
                         ORDER BY Mes
                         ROWS UNBOUNDED PRECEDING) AS AcumuladoAnio
FROM    Totales
ORDER BY Mes;
GO

SET STATISTICS XML OFF;
SET STATISTICS IO OFF;
SET STATISTICS TIME OFF;
GO

/* 
   CONSULTA 3 - DESPUES
   */
SET STATISTICS IO ON;
SET STATISTICS TIME ON;
SET STATISTICS XML ON;
CHECKPOINT;
DBCC DROPCLEANBUFFERS;   
GO

-- CONSULTA 3: Socios con membresia activa que llevan 30 dias o mas sin reservar
-- (o que nunca han reservado): candidatos a una llamada de retencion.
DECLARE @FechaCorte   DATE = '2026-10-25';
DECLARE @DiasInactivo INT  = 30;

WITH UltimaReserva AS (
    SELECT  r.SocioID,
            r.FechaReserva,
            ROW_NUMBER() OVER (PARTITION BY r.SocioID
                               ORDER BY r.FechaReserva DESC) AS rn
    FROM    clases.Reserva r
    WHERE   r.Estado = 'Confirmada'
)
SELECT  s.SocioID, s.Nombre, s.Apellido,
        pm.Nombre  AS PlanActual,
        m.FechaFin AS MembresiaVigenteHasta,
        u.FechaReserva AS UltimaReserva,
        DATEDIFF(DAY, u.FechaReserva, @FechaCorte) AS DiasSinReservar
FROM    socios.Membresia     m
JOIN    socios.Socio         s  ON s.SocioID = m.SocioID
JOIN    socios.PlanMembresia pm ON pm.PlanID = m.PlanID
LEFT JOIN UltimaReserva      u  ON u.SocioID = s.SocioID AND u.rn = 1
WHERE   m.Estado = 'Activa'
  AND   m.FechaInicio <= @FechaCorte
  AND   m.FechaFin    >= @FechaCorte
  AND  (u.FechaReserva IS NULL OR DATEDIFF(DAY, u.FechaReserva, @FechaCorte) >= @DiasInactivo)
ORDER BY CASE WHEN u.FechaReserva IS NULL THEN 0 ELSE 1 END, DiasSinReservar DESC, s.SocioID
OPTION (RECOMPILE);
GO

SET STATISTICS XML OFF;
SET STATISTICS IO OFF;
SET STATISTICS TIME OFF;
GO

