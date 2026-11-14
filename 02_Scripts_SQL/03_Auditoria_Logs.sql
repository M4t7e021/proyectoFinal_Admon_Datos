USE master;
GO

-- Crear y habilitar la auditoria a nivel del servidor de forma segura
IF NOT EXISTS (SELECT 1 FROM sys.server_audits WHERE name = N'audit_GimnasioSystem')
    CREATE SERVER AUDIT [audit_GimnasioSystem]
    TO FILE (
        FILEPATH = N'/var/opt/mssql/data/',
        MAXSIZE = 10 MB,
        MAX_ROLLOVER_FILES = 5,
        RESERVE_DISK_SPACE = OFF
    )
    WITH (QUEUE_DELAY = 1000, ON_FAILURE = CONTINUE);
GO

-- Activacion de la auditoria de la base de datos
IF NOT EXISTS (SELECT 1 FROM sys.dm_server_audit_status WHERE name = N'audit_GimnasioSystem' AND status_desc = N'STARTED')
    ALTER SERVER AUDIT [audit_GimnasioSystem] WITH (STATE = ON);
GO

-- Especificacion a nivel de servidor
IF NOT EXISTS (SELECT 1 FROM sys.server_audit_specifications WHERE name = N'SpecAuditoriaServidor')
    CREATE SERVER AUDIT SPECIFICATION [SpecAuditoriaServidor]
    FOR SERVER AUDIT [audit_GimnasioSystem]
    ADD (FAILED_LOGIN_GROUP),
    ADD (SERVER_PRINCIPAL_CHANGE_GROUP),
    ADD (SERVER_ROLE_MEMBER_CHANGE_GROUP)
    WITH (STATE = ON);
GO

USE GimnasioDB;
GO

-- Especificacion a nivel de base de datos
IF EXISTS (SELECT 1 FROM sys.database_audit_specifications WHERE name = N'SpecAuditoriaGimnasio')
BEGIN
    ALTER DATABASE AUDIT SPECIFICATION [SpecAuditoriaGimnasio] WITH (STATE = OFF);
    DROP DATABASE AUDIT SPECIFICATION [SpecAuditoriaGimnasio];
END
GO

CREATE DATABASE AUDIT SPECIFICATION [SpecAuditoriaGimnasio]
FOR SERVER AUDIT [audit_GimnasioSystem]
    ADD (SELECT, INSERT, UPDATE, DELETE ON SCHEMA::finanzas BY public),
    ADD (SELECT, INSERT, UPDATE, DELETE ON SCHEMA::socios   BY public),
    ADD (INSERT, UPDATE, DELETE ON SCHEMA::clases BY public),
    ADD (SCHEMA_OBJECT_PERMISSION_CHANGE_GROUP),
    ADD (DATABASE_PERMISSION_CHANGE_GROUP),
    ADD (DATABASE_ROLE_MEMBER_CHANGE_GROUP)
WITH (STATE = ON);
GO

-- Consulta de logs de la auditoria corregida (Soluciona el conflicto de Collation y la columna)
SELECT TOP 50
       f.event_time                AS Fecha,
       a.name                      AS Accion,
       f.succeeded                 AS Exitoso,
       f.server_principal_name     AS Login,
       f.database_principal_name   AS Usuario,
       f.schema_name               AS Esquema,
       f.object_name               AS Objeto,
       f.statement                 AS Sentencia
FROM   sys.fn_get_audit_file(N'/var/opt/mssql/data/audit_GimnasioSystem*.sqlaudit', DEFAULT, DEFAULT) f
OUTER APPLY (
    SELECT TOP 1 d.name
    FROM sys.dm_audit_actions d
    WHERE d.action_id COLLATE DATABASE_DEFAULT = f.action_id COLLATE DATABASE_DEFAULT
) a
ORDER BY f.event_time DESC;
GO