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

## Perfil de la fuente (S4)

Bruto revisado: `data/raw/ordenes_2026-11-24_080152.json` · filas: 1.390 y `data/raw/equipos_2026-11-24_080156.json` · filas: 682. Se volvió a extraer el 24/11 con la API arrancada con `API_FECHA_CORTE=2026-11-19`, así que es el mismo corte del bruto del 19/11 (ver `conteos.csv`: 1.390 = 1.390 y 682 = 682).

**Herramienta: pandas, en el script `perfil.py`** (`python3 perfil.py`). La API no agrupa (`$group`), así que sirve para contar casos puntuales pero no para ver todos los valores de una columna. Con un script, cualquiera del equipo lo vuelve a correr sobre el bruto y obtiene las mismas cifras. El script solo lee el bruto: no cambia ni borra nada.

| # | Pregunta | Respuesta (cifra) | Cómo la obtuve | Qué decido para el staging |
|---|---|---|---|---|
| 1 | De las filas que repiten `id_orden`, ¿cuántas son copias exactas, cuántas cambian solo en `fecha_registro` y cuántas cambian en otra columna? | 1.390 filas y **1.351** `id_orden` distintos: **39** id se repiten en 78 filas, es decir, 39 filas sobran. **20** son copias exactas, **10** cambian solo en `fecha_registro` y **9** cambian en `fecha_cierre` (y en `fecha_registro`). De los 39 id, 29 vienen de Web y 10 de Planilla: el problema no es solo de la planilla | `perfil.py` §1: `o.duplicated("id_orden", keep=False)` sin las columnas `:id`, `:created_at` y `:updated_at`; por cada id se listan las columnas que cambian | **Copias exactas:** se deja una y se anotan 20 quitadas. **Solo `fecha_registro`:** es la misma orden cargada dos veces; se deja la de `fecha_registro` más antigua y se anotan 10 quitadas. **Cambia `fecha_cierre`:** no es una copia, es una versión corregida (p. ej. `OT-26-00089`: cierre del 16/05 registrado el 15/05 y cierre del 19/05 registrado el 23/05). Se deja la de `fecha_registro` más reciente y se anotan 9 versiones reemplazadas. Total: 39 quitadas → 1.351 órdenes. *Dato a confirmar:* que la versión registrada después sea la corrección |
| 2 | ¿En cuántos formatos llegan las fechas de una orden? ¿Qué columna lo explica? ¿Qué pasa con el 04/09 si se lee con el formato equivocado? | **2 formatos.** ISO `2026-05-15T01:29:00.000` en 1.143 filas y `dd/mm/aaaa hh:mm` en 247 (`fecha_programada` y `fecha_registro` llegan sin hora). Lo explica **`canal_registro`**: Web → ISO y Planilla → dd/mm, en las 247 de 247. Es día/mes: en todas las fechas con «/» el primer número pasa de 12 (hasta 151 veces) y el segundo nunca. **04/09/2026 = 4 de septiembre**; leído como mes/día sería el 9 de abril, antes de que empiecen los datos (1 de mayo). Además, **114** fechas de solicitud son ambiguas (los dos números ≤ 12) y se leerían mal sin dar ningún error | `perfil.py` §2: patrón de cada fecha (dígito → 9) y `pd.crosstab` del patrón contra cada columna; conteo del 1er y 2º número > 12 | Convertir según `canal_registro`: Web con formato ISO y Planilla con `%d/%m/%Y %H:%M` (o `%d/%m/%Y` si no trae hora). No dejar que la herramienta adivine el formato fila por fila |
| 3 | ¿De cuántas formas viene escrito `tipo_mantenimiento`? ¿Y `prioridad` y `equipo_fuera_servicio`? ¿Cuántos correctivos de un mes se quedan por fuera sin unificar? | `tipo_mantenimiento`: **9 formas** para 2 valores (`Preventivo`, `PREVENTIVO`, `preventivo`, `Prev.`, `Correctivo`, `CORRECTIVO`, `Corr.` y variantes con espacios de sobra). `prioridad`: **7 formas**: `Alta`/`Media`/`Baja` (Web), `1`/`2`/`3` (Planilla) y 844 vacías, que son exactamente los preventivos (683 Web + 161 Planilla). `equipo_fuera_servicio`: **6 formas** (`Sí`, `SI`, `si`, `No`, `NO`, `no`). Contando solo «Correctivo» quedan por fuera **91 de 546 correctivos (16,7 %)**. En **mayo, 23 de 88 (26 %)**; en octubre, 17 de 83 (20 %) | `perfil.py` §3: `value_counts(dropna=False)` y tabla por mes de `fecha_solicitud`; los 3 `Corr.` (mayo, julio y agosto) se ubicaron aparte | Llevar cada columna a un catálogo: `Preventivo`/`Correctivo`, `Sí`/`No` y `Alta`/`Media`/`Baja`. Una `prioridad` vacía en un preventivo queda como «no aplica», no como error. *Dato a confirmar:* que en la planilla 1 = Alta, 2 = Media y 3 = Baja |
| 4 | ¿Cuántas órdenes tienen un `id_equipo` que no está en el inventario? ¿Cuántas se recuperan con una regla de formato y cuáles no? | **20 órdenes** (18 `id_equipo` distintos). **14 se recuperan** pasando el id a mayúsculas, con guion y 4 dígitos (`EQ 0559` → `EQ-0559`, `eq-0057` → `EQ-0057`, `EQ-541` → `EQ-0541`). **6 no se recuperan:** 4 son `ALQ-01` y `ALQ-02`, equipos alquilados (responsable: Alquileres Médicos SAS), que no son un error sino equipos que no están en el inventario; los otros 2 son `EQ-4420` y `EQ-10000`, que no existen ni normalizados. Además, el inventario tiene **12 `id_equipo` repetidos** (682 filas, 670 equipos): en 10 la segunda fila se creó el mismo día en que se actualizó la primera, y 2 (`EQ-0098` y `EQ-0132`) se crearon el mismo día | `perfil.py` §4: `isin` contra `equipos` y una clave de letras + número sin ceros; repetidos con `e["id_equipo"].duplicated()` | Normalizar `id_equipo` antes del cruce. Las 6 órdenes se conservan con la marca `equipo_no_inventariado`. En `equipos` se deja una fila por `id_equipo`, la de `:created_at` más reciente, y se anotan las 12 quitadas; si no, al cruzar se duplican las órdenes de esos equipos. *Datos a confirmar:* si los alquilados cuentan en la disponibilidad, qué equipo son `EQ-4420` y `EQ-10000`, y qué cambió en las 12 versiones del inventario |
| 5 | ¿Qué valores no se pueden convertir a número o a fecha tal como llegan? ¿Hay fechas imposibles? ¿Qué hacen con esas filas sin borrarlas? | **Números:** `costo_repuestos` (38), `costo_servicio_externo` (11) y `equipos.valor_compra` (40) llegan como `$450.000`, con signo y punto de miles. Hay 3 `costo_repuestos` de más de 60 millones (146.290.000, 102.620.000 y 62.700.000), todos de ejecutor externo. **Fechas:** todas convierten, pero **3** `fecha_cierre` dicen `01/01/1900` (las 3 de Planilla y en estado «Cerrada»), **7** órdenes tienen la atención antes de la solicitud y **4** tienen el cierre antes de la atención. Las **20** `fecha_programada` posteriores al corte (hasta el 25/11) no son error: son preventivos agendados | `perfil.py` §5: `pd.to_numeric` y conversión de fechas con `errors="coerce"`, rango de cada fecha y comparación solicitud ≤ atención ≤ cierre | Quitar `$` y puntos y convertir a entero. `01/01/1900` → sin dato (la orden queda cerrada, pero sin fecha de cierre). Ninguna fila se borra: las fechas fuera de orden llevan `fecha_inconsistente = sí` y quedan fuera del tiempo de respuesta. Las fechas programadas futuras se dejan como están. *Dato a confirmar:* los costos de más de 60 millones (el equipo más caro vale 239,7 millones, así que pueden ser reales) |

### Indicador que más cambia

**Disponibilidad de equipos.** Contando solo «Sí» en `equipo_fuera_servicio`, se cuentan 1.092 de las 1.330 órdenes con el equipo fuera de servicio: **se pierden 238 (17,9 %)**, todas de la planilla (`SI` y `si`). En el tiempo de respuesta, sin unificar `tipo_mantenimiento` se pierden 91 de 546 correctivos (16,7 %), y en mayo, 23 de 88 (26 %).

### Dos reglas para el staging (bloque 3)

**Regla 1 · Convertir las fechas según el canal.** Web llega en ISO; Planilla, en día/mes/año.

| | id_orden | canal_registro | fecha_solicitud |
|---|---|---|---|
| Antes | OT-26-00450 | Planilla | `06/07/2026 07:00` (texto) |
| Después | OT-26-00450 | Planilla | `2026-07-06 07:00` (fecha: 6 de julio) |

**Regla 2 · Un `id_orden`, una fila.** Las copias exactas se quitan; si cambió otra columna, se deja la versión registrada de última. Cada fila quitada se anota.

| | id_orden | fecha_cierre | fecha_registro | Qué pasa |
|---|---|---|---|---|
| Antes | OT-26-00089 | `2026-05-16 21:58` | `2026-05-15 01:29` | versión 1 |
| Antes | OT-26-00089 | `2026-05-19 07:58` | `2026-05-23 00:58` | versión 2 |
| Después | OT-26-00089 | `2026-05-19 07:58` | `2026-05-23 00:58` | queda 1 fila; se anota «1 versión reemplazada» |
