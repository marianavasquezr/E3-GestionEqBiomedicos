-- Staging de ordenes (órdenes de mantenimiento, Hospital Monteverde)
-- Origen: bruto.ordenes, cargado tal como llegó (todo texto).
-- Una fila del staging = una orden de mantenimiento, identificada por id_orden.
-- T1 · tipo_mantenimiento llega escrito de 9 formas (mayúsculas, abreviaturas, espacios).
--      Todas significan «Preventivo» o «Correctivo»; se unifican.
-- T2 · fecha_solicitud y fecha_atencion llegan en dos formatos según el canal
--      (Web: año-mes-día con T; Planilla: día/mes/año hora). Pasan a fecha-hora real.
--      La planilla se lee como día/mes/año (ej. 29/09/2026). Si no convierte, queda nulo.
-- T3 · id_orden llega repetido en 39 filas (20 copias exactas, 10 que solo cambian
--      fecha_registro y 9 que cambian fecha_cierre). Se conserva una fila por id_orden:
--      la de fecha_registro más reciente. Se asume que es la versión actualizada.
CREATE OR REPLACE VIEW staging.stg_ordenes AS
SELECT * REPLACE (
  CASE LOWER(TRIM(tipo_mantenimiento))                       -- T1
    WHEN 'preventivo' THEN 'Preventivo'
    WHEN 'prev.' THEN 'Preventivo'
    WHEN 'correctivo' THEN 'Correctivo'
    WHEN 'corr.' THEN 'Correctivo'
    ELSE TRIM(tipo_mantenimiento)
  END AS tipo_mantenimiento,
  COALESCE(                                                  -- T2
    SAFE.PARSE_DATETIME('%Y-%m-%dT%H:%M:%E*S', fecha_solicitud),
    SAFE.PARSE_DATETIME('%d/%m/%Y %H:%M', fecha_solicitud)
  ) AS fecha_solicitud,
  COALESCE(                                                  -- T2
    SAFE.PARSE_DATETIME('%Y-%m-%dT%H:%M:%E*S', fecha_atencion),
    SAFE.PARSE_DATETIME('%d/%m/%Y %H:%M', fecha_atencion)
  ) AS fecha_atencion
)
FROM bruto.ordenes
WHERE TRUE
QUALIFY ROW_NUMBER() OVER (                                  -- T3
  PARTITION BY id_orden
  ORDER BY COALESCE(
             SAFE.PARSE_DATETIME('%Y-%m-%dT%H:%M:%E*S', fecha_registro),
             SAFE.PARSE_DATETIME('%d/%m/%Y %H:%M', fecha_registro),
             SAFE.PARSE_DATETIME('%d/%m/%Y', fecha_registro)
           ) DESC,
           socrata_actualizado DESC
) = 1;