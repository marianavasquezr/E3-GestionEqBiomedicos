# Priorización de mantenimiento de equipos biomédicos 

Equipo E3 · Análisis de Datos Intermedio · Estud-IA (Capa 2)

## Brief v2

| Campo | Respuesta |
|---|---|
| Usuario y decisión | Quien coordina el mantenimiento de equipos biomédicos decide cada mes qué equipos críticos atender primero |
| Pregunta | ¿Qué equipos críticos (glucómetros, bombas de infusión, máquinas de gases) fallan más y cuáles se deben priorizar? |
| Fuente con API | API del Hospital Monteverde (hospital ficticio, datos sintéticos): https://github.com/santiagom26cc/api-hospital-monteverde |
| Qué representa una fila |Una orden de mantenimiento |
| Campo que la identifica | id_orden |
| Cada cuánto se actualiza | La fuente: cada día a las 00:00 (hora de Colombia), con lo registrado el día anterior; el reporte: cada mes |
| Dato a confirmar | Que id_orden no se repita (sobre todo en las órdenes de Sede Norte, cargadas desde planilla), que las fechas de solicitud, atención y cierre estén completas y que los valores, que llegan como texto, se conviertan bien |
| Tres indicadores | 1. Tiempo de respuesta ante fallas · 2. Cumplimiento del preventivo · 3. Disponibilidad de equipos |
| Terminó bien si… | Las filas cargadas son iguales al total de la fuente (count(*)), no hay id_orden repetidos y el reporte mensual muestra los tres indicadores y una lista priorizada|
| No vamos a construir | Predicción de fallas, una app web, ni cambios en la API. Las conclusiones no valen para un hospital real |

## Contrato de datos

- Una fila es: una orden de mantenimiento de un equipo.
- La identifica: `id_orden`.
- Si llega una fila repetida: se conserva una sola y se anota cuántas se quitaron.
- Si falta un campo: se marca como sin dato; no se inventa. Si falta la fecha de atención, la orden queda fuera del tiempo de respuesta.
- Los valores llegan como texto y los campos vacíos no aparecen en la fila; se convierten fechas y números antes de calcular.

## Bitácora de decisiones

| Fecha | Decisión | Por qué |
|---|---|---|
| 2026-11-17 | Usar la API del Hospital Monteverde como fuente | No hay acceso a datos reales de un hospital y las fallas no se publican en portales abiertos. Por ende, el profesor construyó una base simulada a partir de nuestro brief |
| 2026-11-24 | Perfilar el bruto con `perfil.py` (pandas) antes de limpiar | La API no agrupa; un script deja las cifras repetibles por cualquiera del equipo. Las reglas del staging salen de este perfil (ver «Perfil de la fuente») |

## Reglas del repositorio

- Es público: nada de datos personales, contraseñas, tokens ni llaves.
- Las credenciales van en un archivo `.env`, que Git ignora (ver `.gitignore`). `.env.example` muestra qué variables hacen falta, sin valores.
- Cada commit explica en su mensaje qué se decidió y por qué.

## Carga y staging

**Carga (bruto):** `bruto.ordenes`, 1390 filas = 1390 traídas (conteos.csv); `bruto.equipos`, 682 = 682. Todo como texto, tal como llegó de la API.

**Qué representa una fila:** una orden de mantenimiento, identificada por `id_orden`. En el bruto no se cumplía (1390 filas y 1351 `id_orden` distintos); en el staging, sí.

**Staging:** vista `staging.stg_ordenes` (`sql/stg_ordenes.sql`). Tres reglas:
- **T1** · `tipo_mantenimiento` llegaba escrito de 9 formas (`CORRECTIVO`, `Corr.`, `Prev.`, espacios al final…). Todas significan Preventivo o Correctivo y se unifican. Ejemplo: `CORRECTIVO` (86 filas) → `Correctivo`.
- **T2** · `fecha_solicitud` y `fecha_atencion` llegaban en dos formatos según el canal (Web: `2026-11-18T13:42:00.000`; Planilla: `29/09/2026 07:00`). Pasan a fecha-hora real. La planilla se lee como día/mes/año. Si no convierte, queda nulo.
- **T3** · `id_orden` llegaba repetido en 39 filas: 20 copias exactas, 10 que solo cambian `fecha_registro` y 9 que cambian `fecha_cierre`. Se conserva una fila por `id_orden`, la de `fecha_registro` más reciente. 

| Control | Antes (bruto) | Después (staging) | ¿Es lo esperado? |
|---|---|---|---|
| Filas | 1390 | 1351 | Sí: T3 quitó las 39 repetidas |
| `id_orden` distintos | 1351 | 1351 | Sí: una fila por llave |
| `tipo_mantenimiento` (valores distintos) | 9 | 2 | Sí: T1 unió las formas de escribir Preventivo y Correctivo |
| `fecha_solicitud` vacías | 0 | 0 | Sí: ninguna venía vacía |
| `fecha_solicitud` con texto que no convirtió | 0 | — | Sí: T2 convirtió todas |
| `fecha_atencion` vacías | 67 | 66 | Sí: 67 venían vacías de origen; la que baja es de una fila repetida que T3 descartó |
| `fecha_atencion` con texto que no convirtió | 0 | — | Sí: T2 convirtió todas |

### De dónde viene cada columna

Las 24 columnas del staging (`staging.stg_ordenes`) vienen de `bruto.ordenes`, que es el bruto de la API tal como llegó. Tres columnas cambian de valor o de tipo (T1 y T2) y las demás pasan igual. T3 no cambia columnas, solo quita filas repetidas.

| Columna en el staging | Viene de (bruto) | Regla |
|---|---|---|
| socrata_id | `:id` de la API | Pasa igual. Renombrada por `preparar_carga.py` (BigQuery no admite `:` en los nombres) |
| socrata_creado | `:created_at` de la API | Pasa igual (texto). Renombrada por `preparar_carga.py` |
| socrata_actualizado | `:updated_at` de la API | Pasa igual (texto). Renombrada por `preparar_carga.py`. Desempata en T3 |
| id_orden | id_orden | Pasa igual. Es la llave: T3 deja una fila por valor |
| id_equipo | id_equipo | Pasa igual |
| servicio_reporta | servicio_reporta | Pasa igual. Pendiente: 10 valores para unos 6 servicios (Hospitalización escrita de 4 formas = 406 filas; Urgencias de 2 = 291; `Piso 3 - Hospitalización` = 37, por confirmar si es el mismo servicio) |
| tipo_mantenimiento | tipo_mantenimiento | **T1:** 9 formas de escribirlo pasan a `Preventivo` o `Correctivo` |
| fecha_programada | fecha_programada | Pasa igual (texto). Pendiente: convertir a fecha |
| fecha_solicitud | fecha_solicitud | **T2:** texto en dos formatos pasa a fecha-hora (DATETIME) |
| fecha_atencion | fecha_atencion | **T2:** texto en dos formatos pasa a fecha-hora (DATETIME). Quedan 66 vacías, que ya venían vacías de origen |
| fecha_cierre | fecha_cierre | Pasa igual (texto). Pendiente: convertir a fecha. Es la columna que cambia en 9 órdenes repetidas |
| estado | estado | Pasa igual |
| equipo_fuera_servicio | equipo_fuera_servicio | Pasa igual. Pendiente: `Sí`/`SI`/`si` (1330 filas) y `No`/`NO`/`no` (60) son dos valores escritos de 6 formas |
| tipo_ejecutor | tipo_ejecutor | Pasa igual |
| responsable | responsable | Pasa igual |
| costo_repuestos | costo_repuestos | Pasa igual (texto). Pendiente: en la muestra del profe hay valores como `$220.000`; convertir a número |
| costo_servicio_externo | costo_servicio_externo | Pasa igual (texto). Pendiente: igual que costo_repuestos |
| canal_registro | canal_registro | Pasa igual (`Web` o `Planilla`). Explica los dos formatos de fecha |
| fecha_registro | fecha_registro | Pasa igual (texto). T3 la lee como fecha solo para ordenar y escoger la fila más reciente |
| observaciones | observaciones | Pasa igual |
| prioridad | prioridad | Pasa igual. Pendiente: 844 nulas (coincide con los 844 preventivos, por verificar); `Alta`/`Media`/`Baja` (460) mezclados con `1`/`2`/`3` (86), cuyo significado hay que confirmar con el profe |
| falla_reportada | falla_reportada | Pasa igual |
| causa | causa | Pasa igual |
| archivo_origen | archivo_origen | Pasa igual |

## Mi consulta en 3 respuestas (S4)
Consulta: sql/stg_ordenes.sql
1. En tus controles, las `fecha_atencion` vacías dan 67 en el bruto y 66 en el staging. ¿Por qué cambia esa cifra?
   Respuesta: Porque T3 descartó una fila repetida de un id_orden que venía con fecha_atencion vacía. T2 no llena fechas, solo las convierte, así que la diferencia viene de quitar esa fila.
2. ¿Por qué la regla T3 se queda con la fila de `fecha_registro` más reciente de cada `id_orden` y no con otra?
   Respuesta: Porque en los ejemplos que revisamos, la versión vieja tiene la fecha_registro anterior a la atención y al cierre, y la nueva se registra después y con un cierre más tardío, así que parece una corrección
3. Si mañana la API publica órdenes con `fecha_solicitud` en un formato que T2 no conoce (por ejemplo `2026/11/27 08:00`), ¿qué pasaría con esas filas en el staging y cuál de tus controles te lo mostraría?
   Respuesta: Quedarían con fecha_solicitud en nulo, sin error y sin perder la fila, porque SAFE.PARSE_DATETIME devuelve nulo cuando no puede convertir. Lo mostraría el control 08 (fecha_solicitud con texto que no convirtió), que hoy da 0 y dejaría de serlo. Esas órdenes no entrarían en el tiempo de respuesta.
   El control 08 cuenta las fechas de solicitud que traen texto pero que T2 no pudo convertir. Hoy da 0; si algún día sube, significa que llegó un formato nuevo.