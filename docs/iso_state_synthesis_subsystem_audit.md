# Auditoria Del Subsistema `iso_state_synthesis/`

Estado: corte inicial del bloque `iso_state_synthesis/`, 2026-06-06.

Este documento registra el primer corte estable de auditoria del subsistema ISO
por estado. El paquete sigue siendo experimental: no reemplaza a Maestro ni al
postprocesador. Su valor actual es explicar candidatos ISO desde snapshots PGMX,
estados, diferenciales, bloques, transiciones y evidencia observada.

## Mapa Actual

| Zona | Modulos | Funcion |
| --- | --- | --- |
| API publica | `iso_state_synthesis.__init__` | Reexporta dataclasses, catalogo, builders de plan/evaluacion y emisor candidato. |
| CLI | `iso_state_synthesis.cli`, `__main__` | Expone `inspect-pgmx`, `evaluate-pgmx`, `emit-candidate` y `compare-candidate`. |
| Modelo | `iso_state_synthesis.model` | Define fuentes, valores, vectores de estado, etapas, diferenciales, evaluaciones y serializacion JSON. |
| Adaptador PGMX | `iso_state_synthesis.pgmx_source` | Convierte `pgmx.snapshot` en un plan de estados ordenado por worksteps. |
| Diferencial | `iso_state_synthesis.differential` | Calcula cambios entre estado activo, objetivo, valores forzados y resets. |
| Catalogo | `iso_state_synthesis.catalog` | Nombra bloques `B-*` y transiciones `T-*` observadas contra el contrato ISO. |
| Emisor | `iso_state_synthesis.emitter` | Emite ISO candidato explicado para el subset soportado y compara contra Maestro. |
| Evidencia | `memory/`, `experiments/`, `contracts/`, `machine_config/` | Memoria viva, estudios fechados, contrato intermedio y snapshot local de maquina. |

## Procesos Donde Interviene

| Proceso | Entrada | Salida | Modulos |
| --- | --- | --- | --- |
| Inspeccion de estado | `.pgmx` Maestro | Plan interno y JSON opcional | `pgmx_source`, `model`, `cli`. |
| Evaluacion de diferenciales | Plan de estado | Cambios por etapa y estado final | `differential`, `model`, `cli`. |
| Emision candidata | `.pgmx` soportado | ISO candidato con fuente por linea | `emitter`, `catalog`, `differential`. |
| Comparacion contra Maestro | `.pgmx` + `.iso` esperado | Igual/distinto, diferencias y diff opcional | `emitter`, `cli`. |
| Investigacion | Corpus PGMX/ISO y config local | Reglas documentadas y pendientes | `experiments/`, `memory/`, `machine_config/`. |

## Frontera Actual

- `model.py`, `differential.py` y `catalog.py` son el contrato mas estable del
  bloque: pueden cubrirse con tests puros sin corpus externo.
- `pgmx_source.py` es adaptador experimental desde `pgmx.snapshot`. Tiene reglas
  de ordenamiento y familias observadas; no debe confundirse con un parser PGMX
  general.
- `emitter.py` es el frente mas grande y menos modular. Produce candidatos
  explicables para familias y secuencias controladas, pero no es traductor ISO
  general.
- La CLI es operativa para investigacion y debe seguir funcionando con
  `py -3 -m iso_state_synthesis --help`.

## Subcorte Inicial

Hallazgos aplicados:

- Se agrego `tests/test_iso_state_synthesis.py` para cubrir contratos puros:
  fachada publica, `StateVector`, serializacion JSON, diferenciales, seleccion
  de transiciones y comparacion normalizada de ISO candidato.
- Se mantiene intacto el emisor grande; este corte no intenta resolver los
  residuales de corpus ni ampliar familias.
- Se documenta explicitamente que el bloque esta activo como laboratorio
  experimental, no como API productiva de generacion ISO.

Validaciones del corte:

- `py -3 -m iso_state_synthesis --help`
- `py -3 -m compileall -q iso_state_synthesis`
- `py -3 -m unittest tests.test_iso_state_synthesis`

## Subcorte Emisor Helpers

Hallazgos aplicados:

- Se corrigio `_xy_changed` para detectar movimientos donde cambia solo un eje
  XY. La condicion anterior exigia cambio simultaneo de X e Y, lo que podia
  degradar trazas de perfil alineadas a un eje durante la emision candidata.
- Se agrego cobertura pura para helpers compartidos de `emitter.py`: deteccion
  XY, emision compacta de movimientos lineales y geometria lateral de perfiles.
- Se alinearon el docstring de `emit_candidate_from_evaluation`, su mensaje de
  error para grupos incompletos y el README del paquete con el alcance real del
  emisor observado.

Concentracion actual detectada en `emitter.py`:

| Zona | Funcion dominante | Observacion |
| --- | --- | --- |
| Fresado router | `_emit_line_milling_trace` | Mezcla fresado lineal, contornos abiertos/cerrados, circulos, leads, estrategias y lifts. Es el primer candidato para una extraccion futura por familia de mecanizado. |
| Dispatcher de trabajos | `_emit_planned_work_group` | Centraliza decisiones entre familias y transiciones. Conviene mantenerlo como orquestador, pero extraer reglas de transicion cuando se estabilicen. |
| Preparaciones por cabezal | `_emit_top_drill_prepare*`, `_emit_side_drill_prepare*` | Tienen variantes segun familia previa. Son candidatos a modulos de transicion o preparacion por cabezal. |
| Helpers geometricos | `_line_milling_motion_line`, `_unit_vector`, `_side_normal`, `_xy_changed` | Quedaron cubiertos como helpers puros antes de cualquier extraccion estructural. |

## Subcorte Emisor Dispatcher

Hallazgos aplicados:

- Se agrego cobertura pura para `_work_stage_groups` y `_plan_work_groups`.
- El dispatcher queda documentado como dos pasos: reconocer triples completos
  `prepare/trace/reset` ignorando etapas comunes, y luego enriquecer cada grupo
  con `incoming_transition_id` y `outgoing_transition_id`.
- Los tests fijan que el emisor rechaza secuencias incompletas o desordenadas
  antes de intentar emitir ISO.
- Los tests cubren transiciones internas de router (`T-RH-*`), cambios de
  cabezal router/boring (`T-XH-*`) y transiciones de boring head con ranuras
  (`T-BH-005`, `T-BH-007`, `T-BH-008`).

## Subcorte Fresado Router Geometria

Hallazgos aplicados:

- Se agrego cobertura pura para helpers geometricos usados por
  `_emit_line_milling_trace`.
- Los tests cubren seleccion de eje dominante, tangente de toolpath, direccion
  de leads lineales compensados y extensiones sin lead.
- Los tests fijan geometria de entrada/salida para polilineas abiertas y
  cerradas, tanto con lead lineal como con lead en arco.
- Este corte prepara una eventual extraccion de geometria de fresado router sin
  modificar todavia la emision ISO candidata.

## Mapa Interno `_emit_line_milling_trace`

Lectura estructural del bloque principal de fresado router:

| Zona | Responsabilidad actual | Observacion |
| --- | --- | --- |
| Lectura de estado | Extrae coordenadas, feeds, herramienta, estrategia, familia de perfil, leads y primitivas desde `StageDifferential` y `evaluation.final_state`. | Conviene promover a un contexto/dataclass interno antes de extraer familias. |
| Predicados de modo | Calcula `has_lead_paths`, `uses_side_compensation`, `uses_no_lead_side_compensation`, `uses_center_circle_leads`, `uses_closed_center_leads`, `uses_open_center_leads`. | Primer candidato a extraccion segura porque no emite lineas. |
| Entrada comun | Calcula `rapid_x/rapid_y`, arma `entry_lines` y maneja continuidad con `previous_router_trace`. | Mezcla seleccion geometrica con estado modal anterior. Debe quedar cerca del dispatcher hasta tener tests de secuencia. |
| Ramas center con leads | `OpenPolyline`, `ClosedPolyline*` y `Circle` con `side_of_feature=Center` y leads reales. | Comparten estructura approach/trajectory/retract. Se puede extraer despues de fijar predicados. |
| Ramas con estrategia | Circulos con estrategia, estrategias con lead paths y estrategia sin leads. | Dependen de toolpaths Maestro y primitivas; requieren fixtures o tests de motion-line builders antes de extraer. |
| Ramas con compensacion lateral | Lineal compensado, `OpenPolyline` compensado, fallback vertical y no-lead side compensation. | Ya tienen helpers geometricos cubiertos; falta cubrir la emision de motion lines por rama. |
| Fallbacks | Lead paths simples, sin leads y fallback final. | Deben quedar como ultimo corte porque son los caminos de compatibilidad. |

Orden recomendado de extraccion futura:

1. Hecho: extraer predicados de modo y cubrirlos con tests puros.
2. Extraer un contexto interno de fresado router sin cambiar comportamiento.
3. Extraer builders de `motion_lines` por familia/rama, empezando por las ramas
   de geometria ya cubierta.
4. Recién despues mover esos builders a modulos separados si el corte queda
   estable.

## Subcorte Fresado Router Predicados

Hallazgos aplicados:

- Se agrego `_LineMillingTraceModes` como contrato interno para nombrar las
  ramas de `_emit_line_milling_trace`.
- Se extrajo `_line_milling_trace_modes`, que calcula si la traza usa leads
  reales, compensacion lateral, compensacion lateral sin lead, circulos center,
  polilineas cerradas center o polilineas abiertas center.
- Se agregaron tests puros para fijar esos predicados con casos center,
  lateral, sin lead y estrategia activa.
- La emision ISO candidata no cambia: el bloque principal sigue consumiendo las
  mismas banderas, ahora derivadas desde el helper.

## Subcorte Fresado Router Contexto

Hallazgos aplicados:

- Se agrego `_LineMillingTraceContext` como contrato interno para separar la
  lectura de estado de la emision de ISO en `_emit_line_milling_trace`.
- Se extrajo `_line_milling_trace_context`, que reune coordenadas, alturas,
  feeds, herramienta, toolpaths, geometria nominal, primitivas, estrategia,
  acercamiento/alejamiento y predicados de modo.
- Se agrego un test puro que construye un `StageDifferential` minimo y confirma
  que el contexto lee valores directos, defaults desde `final_state`, geometria
  nominal y modos de compensacion.
- La funcion principal conserva las ramas de emision actuales; el cambio solo
  separa la fase de lectura para preparar builders de `motion_lines`.

## Subcorte Fresado Router Builder No-Lead

Hallazgos aplicados:

- Se extrajo `_line_milling_no_lead_side_compensation_motion_lines` como primer
  builder de `motion_lines` desde `_emit_line_milling_trace`.
- El builder cubre la rama `uses_no_lead_side_compensation`: lineas/perfiles
  sin leads reales con compensacion lateral y circulos sin lead con arcos.
- Se agregaron tests puros para fijar el ISO emitido por una linea compensada
  derecha y por un circulo compensado izquierdo.
- `_emit_line_milling_trace` queda un paso mas cerca de separar seleccion de
  rama, lectura de estado y generacion de movimiento.

## Deuda Residual

- Extraer `iso_state_synthesis.emitter` por familias o etapas cuando se retome
  la generacion ISO, porque concentra preparacion, trazas, transiciones,
  resets, formato y comparacion.
- Agregar fixtures PGMX/ISO chicos dentro de `tests/fixtures` o `tmp` controlado
  para cubrir `pgmx_source.py` y una emision real sin depender de rutas `S:` o
  `P:`.
- Separar claramente los estudios fechados de las reglas promovidas al catalogo.
- Auditar `tools/studies/iso/` despues de este bloque para confirmar que los
  estudios reproducibles apuntan al paquete vigente.
