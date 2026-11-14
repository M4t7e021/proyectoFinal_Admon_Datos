

use GimnasioDB;
go

--CREACION DE LA PRIMERA VISTA
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
--CREACION DE LA SEGUNDA VISTA A UTILIAR

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

