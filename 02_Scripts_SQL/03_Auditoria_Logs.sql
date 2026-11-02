use master;
go

-- Crear y habilitar la auditoria a nivel del servidor de forma segura
if not exists (select * from sys.server_audits where name = 'audit_GimnasioSystem')
begin 
    exec('
        create server audit [audit_GimnasioSystem]
        to file (
            filepath = N''/var/opt/mssql/data/'', 
            maxsize = 10 MB,
            max_rollover_files = 5,
            reserve_disk_space = off
        )
        with (
            queue_delay = 1000,
            on_failure = continue
        )
        STATE = ON;
    ');
end
go

--Activacion de la auditoria de la base de datos
use GimnasioDB;
go

-- Eliminaremos la especificacion si ya existe para evitar errores
if exists (select * from sys.database_audit_specifications where name = 'SpecAuditoriaGimnasio')
BEGIN
    -- Se usa WITH (STATE = OFF) en lugar de SET STATE
    alter database audit specification [SpecAuditoriaGimnasio] 
    with (state = off);
    
    drop database audit specification [SpecAuditoriaGimnasio];
end
go

--Crear la especificaion conectada al servidor de la auditoria
create database audit specification [SpecAuditoriaGimnasio]
for server audit [audit_GimnasioSystem]
add (select, insert, update, delete on schema::finanzas by public),
add (select, insert, update on schema::socios by public)
with (state = on);
go