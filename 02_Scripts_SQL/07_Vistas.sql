----VISTA PARA EL PRIMER DASHBOARD

use GimnasioDB;
go

create or alter view reportes.vw_TopClasesUltimoAno as
select  
    DATEFROMPARTS(year(se.FechaHora), month(se.FechaHora), 1) Mes,
    tc.Nombre Clase,
    count(r.ReservaID) TotalReservas
from clases.Reserva     r
join clases.SesionClase se on se.SesionID    = r.SesionID
join clases.TipoClase   tc on tc.TipoClaseID = se.TipoClaseID
where r.Estado  = 'Confirmada'
 and se.Estado = 'Realizada'
 and se.FechaHora >= DATEADD(MONTH, -12, CAST(GETDATE() AS DATE))
group by DATEFROMPARTS(year(se.FechaHora), month(se.FechaHora), 1), tc.Nombre;
go
--VISTA PARA EL SEGUNDO DASHBOARD
create or alter view reportes.vw_GananciaMembresiasUltimoAno as
select  
    YEAR(p.FechaPago) Anio,
    MONTH(p.FechaPago)  Mes,
    pm.Nombre TipoMembresia,
    COUNT(m.MembresiaID) CantidadAdquirida,
    ISNULL(SUM(p.Monto), 0) TotalIngresos
from socios.Membresia       m
join socios.PlanMembresia   pm on pm.PlanID      = m.PlanID
join finanzas.Pago        p  on p.MembresiaID  = m.MembresiaID and p.Estado = 'Pagado'
where m.Estado in ('Activa', 'Vencida')
    and p.FechaPago >= DATEADD(YEAR, -1, GETDATE())
group by 
    YEAR(p.FechaPago),
    MONTH(p.FechaPago),
    pm.Nombre;
GO
---VISTA PARA EL TERCER DASHBOARD

create or alter view reportes.vw_TopEntrenadoresClases as
select  
    concat(e.Nombre, ' ', e.Apellido) Entrenador,
    e.Especialidad,
    count(distinct se.SesionID) ClasesImpartidas,
    count(r.ReservaID) AlumnosAtendidos
from clases.SesionClase se
join clases.Entrenador e on e.EntrenadorID = se.EntrenadorID
left join clases.Reserva  r on r.SesionID  = se.SesionID AND r.Estado = 'Confirmada'
where se.Estado = 'Realizada'
group by e.EntrenadorID, e.Nombre, e.Apellido, e.Especialidad;
go

