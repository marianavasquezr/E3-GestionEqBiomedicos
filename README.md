# Priorización de mantenimiento de equipos biomédicos 

Equipo E3 · Análisis de Datos Intermedio · Estud-IA (Capa 2)

## Brief v1

| Campo | Respuesta |
|---|---|
| Usuario y decisión | Quien coordina el mantenimiento de equipos biomédicos decide cada mes qué equipos críticos atender primero |
| Pregunta | ¿Qué equipos críticos (glucómetros, bombas de infusión, máquinas de gases) fallan más y cuáles se deben priorizar? |
| Fuente con API | API Simulada |
| Qué representa una fila |Una orden de mantenimiento |
| Campo que la identifica | id_orden |
| Cada cuánto se actualiza | el reporte se calcula cada mes |
| Dato a confirmar | Que `id_orden` no se repita y que las fechas de solicitud y atención estén completas|
| Tres indicadores | 1. Tiempo de respuesta ante fallas · 2. Cumplimiento del preventivo · 3. Disponibilidad de equipos |
| Terminó bien si… | Las filas cargadas son iguales al total de la fuente, no hay `id_orden` repetidos y el reporte mensual muestra los tres indicadores y una lista priorizada|
| No vamos a construir | Predicción de fallas, una app web ni nada con datos reales de pacientes u hospitales |

## Contrato de datos

- Una fila es: una orden de mantenimiento de un equipo.
- La identifica: `id_orden`.
- Si llega una fila repetida: se conserva una sola y se anota cuántas se quitaron.
- Si falta un campo: se marca como sin dato; no se inventa. Si falta la fecha de atención, la orden queda fuera del tiempo de respuesta.

## Bitácora de decisiones

| Fecha | Decisión | Por qué |
|---|---|---|
| 2026-11-17 | Usar la base simulada de órdenes de mantenimiento | No hay acceso a datos reales de un hospital y las fallas no se publican en portales abiertos |

## Reglas del repositorio

- Es público: nada de datos personales, contraseñas, tokens ni llaves.
- Las credenciales van en un archivo `.env`, que Git ignora (ver `.gitignore`). `.env.example` muestra qué variables hacen falta, sin valores.
- Cada commit explica en su mensaje qué se decidió y por qué.
