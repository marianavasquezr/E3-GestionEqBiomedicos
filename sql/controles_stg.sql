-- Cifras de control del staging: filas antes y después, y valores nuevos.
SELECT '1 filas en el bruto' AS control, COUNT(*) AS valor FROM bruto.ordenes
UNION ALL SELECT '2 filas en el staging', COUNT(*) FROM staging.stg_ordenes
UNION ALL SELECT '3 T1: tipos distintos en el bruto', COUNT(DISTINCT tipo_mantenimiento) FROM bruto.ordenes
UNION ALL SELECT '4 T1: tipos distintos en el staging', COUNT(DISTINCT tipo_mantenimiento) FROM staging.stg_ordenes
UNION ALL SELECT '5 T2: fecha_solicitud sin convertir', COUNTIF(fecha_solicitud IS NULL) FROM staging.stg_ordenes
UNION ALL SELECT '6 T2: fecha_atencion nulas en el bruto', COUNTIF(fecha_atencion IS NULL) FROM bruto.ordenes
UNION ALL SELECT '7 T2: fecha_atencion nulas en el staging', COUNTIF(fecha_atencion IS NULL) FROM staging.stg_ordenes
ORDER BY control;