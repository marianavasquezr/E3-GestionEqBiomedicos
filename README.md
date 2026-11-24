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

## Reglas del repositorio

- Es público: nada de datos personales, contraseñas, tokens ni llaves.
- Las credenciales van en un archivo `.env`, que Git ignora (ver `.gitignore`). `.env.example` muestra qué variables hacen falta, sin valores.
- Cada commit explica en su mensaje qué se decidió y por qué.

## Carga y staging

**Carga (bruto):** `bruto.ordenes`, 1390 filas = 1390 traídas (conteos.csv); `bruto.equipos`, 682 = 682. Todo como texto, tal como llegó de la API.

**Staging:** vista `staging.stg_ordenes` (`sql/stg_ordenes.sql`). Dos reglas:
- **T1** · `tipo_mantenimiento` llegaba escrito de 9 formas (`CORRECTIVO`, `Corr.`, `Prev.`, espacios al final…). Todas significan Preventivo o Correctivo y se unifican. Ejemplo: `CORRECTIVO` (86 filas) → `Correctivo`.
- **T2** · `fecha_solicitud` y `fecha_atencion` llegaban en dos formatos según el canal (Web: `2026-11-18T13:42:00.000`; Planilla: `29/09/2026 07:00`). Pasan a fecha-hora real. La planilla se lee como día/mes/año. Si no convierte, queda nulo.

| Control | Bruto | Staging | ¿Es lo esperado? |
|---|---|---|---|
| Filas | 1390 | 1390 | Sí: el staging no quita filas |
| `tipo_mantenimiento` (valores distintos) | 9 | 2 | Sí: T1 unió las formas de escribir Preventivo y Correctivo |
| `fecha_solicitud` sin convertir | 0 | 0 | Sí: T2 convirtió las 1390 |
| `fecha_atencion` vacías | 67 | 67 | Sí: T2 no creó nulos nuevos; esas 67 ya venían vacías |