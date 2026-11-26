-- Cifras de control del staging (stg_ordenes): filas, llave, y antes y después de cada regla.
SELECT '01 filas en el bruto' AS control, COUNT(*) AS valor FROM bruto.ordenes
UNION ALL SELECT '02 filas en el staging', COUNT(*) FROM staging.stg_ordenes
UNION ALL SELECT '03 T3: id_orden distintos en el bruto', COUNT(DISTINCT id_orden) FROM bruto.ordenes
UNION ALL SELECT '04 T3: id_orden distintos en el staging', COUNT(DISTINCT id_orden) FROM staging.stg_ordenes
UNION ALL SELECT '05 T1: tipos distintos antes', COUNT(DISTINCT tipo_mantenimiento) FROM bruto.ordenes
UNION ALL SELECT '06 T1: tipos distintos después', COUNT(DISTINCT tipo_mantenimiento) FROM staging.stg_ordenes
UNION ALL SELECT '07 T2 fecha_solicitud: venían vacías', COUNTIF(fecha_solicitud IS NULL) FROM bruto.ordenes
UNION ALL SELECT '08 T2 fecha_solicitud: con texto y no convirtieron', COUNTIF(fecha_solicitud IS NOT NULL AND COALESCE(SAFE.PARSE_DATETIME('%Y-%m-%dT%H:%M:%E*S', fecha_solicitud), SAFE.PARSE_DATETIME('%d/%m/%Y %H:%M', fecha_solicitud)) IS NULL) FROM bruto.ordenes
UNION ALL SELECT '09 T2 fecha_atencion: venían vacías', COUNTIF(fecha_atencion IS NULL) FROM bruto.ordenes
UNION ALL SELECT '10 T2 fecha_atencion: con texto y no convirtieron', COUNTIF(fecha_atencion IS NOT NULL AND COALESCE(SAFE.PARSE_DATETIME('%Y-%m-%dT%H:%M:%E*S', fecha_atencion), SAFE.PARSE_DATETIME('%d/%m/%Y %H:%M', fecha_atencion)) IS NULL) FROM bruto.ordenes
ORDER BY control;