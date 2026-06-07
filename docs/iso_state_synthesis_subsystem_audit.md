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
| Fresado router | `_emit_line_milling_trace` | Conserva la orquestacion de entrada, seleccion de rama y apendice explicado; las ramas de `motion_lines` ya delegan en builders internos. |
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
| Entrada comun | Calcula `rapid_x/rapid_y`, arma `entry_lines` y maneja continuidad con `previous_router_trace`. | Extraida en `_line_milling_rapid_point` y `_line_milling_entry_lines`; la continuidad sigue cerca del emisor porque depende de lineas ya emitidas. |
| Ramas center con leads | `OpenPolyline`, `ClosedPolyline*` y `Circle` con `side_of_feature=Center` y leads reales. | Extraidas como builders de `motion_lines`; siguen dentro de `emitter.py` hasta estabilizar el corte modular. |
| Ramas con estrategia | Circulos con estrategia, estrategias con lead paths y estrategia sin leads. | Extraidas como builders internos y cubiertas con tests puros de forma. |
| Ramas con compensacion lateral | Lineal compensado, `OpenPolyline` compensado, fallback vertical y no-lead side compensation. | La emision lateral ya delega en builders especificos o en el helper lineal previo. |
| Fallbacks | Lead paths simples, sin leads y fallback final. | Extraidos como builders de compatibilidad para conservar la forma heredada. |

Orden recomendado de extraccion futura:

1. Hecho: extraer predicados de modo y cubrirlos con tests puros.
2. Hecho: extraer un contexto interno de fresado router sin cambiar
   comportamiento.
3. Hecho: extraer builders de `motion_lines` por familia/rama, empezando por
   las ramas de geometria ya cubierta.
4. Pendiente futuro: mover esos builders a modulos separados si el corte queda
   estable y si el laboratorio ISO retoma una separacion por familias.

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

## Subcorte Fresado Router Builder OpenPolyline Compensado

Hallazgos aplicados:

- Se extrajo `_line_milling_open_polyline_side_compensation_motion_lines` para
  la rama `uses_side_compensation and profile_family == "OpenPolyline"`.
- El builder cubre polilineas abiertas con compensacion lateral y leads reales,
  tanto lineales como en arco.
- Se agregaron tests puros para fijar el ISO emitido por leads `Line` y `Arc`,
  incluyendo la regla de conservar `Z` cuando la profundidad no es pasante.
- El bloque principal conserva la seleccion de rama y delega otra familia de
  `motion_lines` en un builder aislado.

## Subcorte Fresado Router Builder Fallback Lateral

Hallazgos aplicados:

- Se extrajo `_line_milling_side_compensation_fallback_motion_lines` para el
  fallback generico de `uses_side_compensation`.
- El builder conserva la regla previa de usar `lift.points[-2].y` y
  `overcut_length` para calcular el alejamiento final.
- Se agrego un test puro que fija el ISO emitido por esa rama lateral.

## Subcorte Fresado Router Builder Lead Paths

Hallazgos aplicados:

- Se extrajo `_line_milling_lead_path_motion_lines` para la rama simple
  `has_lead_paths`, sin compensacion lateral ni estrategia.
- El builder conserva el recorrido `Approach` -> `TrajectoryPath` -> `Lift` y
  la regla de feeds: `plunge_feed` en acercamiento y `milling_feed` en
  trayectoria/alejamiento.
- Se agrego un test puro que fija el ISO emitido por esa secuencia.

## Subcorte Fresado Router Builders Restantes

Hallazgos aplicados:

- Se extrajeron los builders internos para las ramas center con leads:
  `_line_milling_open_center_leads_motion_lines`,
  `_line_milling_closed_center_leads_motion_lines` y
  `_line_milling_center_circle_leads_motion_lines`.
- Se extrajeron los builders de estrategia:
  `_line_milling_circle_strategy_motion_lines`,
  `_line_milling_strategy_lead_path_motion_lines` y
  `_line_milling_strategy_motion_lines`.
- Se extrajeron los caminos de compatibilidad
  `_line_milling_no_lead_motion_lines` y
  `_line_milling_fallback_motion_lines`.
- `_emit_line_milling_trace` queda reducido a lectura de contexto, calculo de
  entrada comun, seleccion de builder y apendice explicado de lineas ISO.
- La cobertura pura del subsistema fija los nuevos builders con casos center,
  estrategia, sin leads y fallback final.

## Subcorte Fresado Router Entrada Comun

Hallazgos aplicados:

- Se extrajo `_line_milling_rapid_point` para concentrar la seleccion del punto
  rapido de entrada segun center leads, compensacion lateral, estrategia,
  no-lead y fallback.
- Se extrajo `_line_milling_entry_lines` para construir la entrada E004 comun,
  incluyendo continuidad desde un router previo mediante la ultima XY emitida,
  `leadout_x/y` o `Lift`.
- `_emit_line_milling_trace` conserva la orquestacion: contexto, entrada,
  seleccion del builder de `motion_lines` y apendice explicado.
- Se agregaron tests puros para rapid point y entry lines con y sin router
  previo.

## Subcorte Fresado Router Selector De Movimiento

Hallazgos aplicados:

- Se extrajo `_line_milling_trace_motion_lines` para concentrar la seleccion
  del builder de movimiento segun modo, estrategia, compensacion lateral,
  leads y fallbacks.
- Se extrajo `_line_milling_linear_side_compensation_motion_lines` para que la
  rama lineal compensada tambien lea desde `_LineMillingTraceContext`.
- `_emit_line_milling_trace` ya no contiene ramas de geometria de traza: arma
  contexto, entrada y apende la salida del selector de movimiento.
- Se agregaron tests puros para el builder lineal contextual y para el
  despacho del selector hacia center leads y compensacion lineal.

## Subcorte Transicion Router Entre Trabajos

Hallazgos aplicados:

- Se extrajo `_router_inter_work_reset_lines` desde
  `_emit_router_inter_work_reset` para separar la decision de lineas del
  apendice explicado.
- El helper conserva la regla observada: reset completo por defecto y reset
  sin `?%ETK[7]=0` cuando el siguiente router trae estrategia o entra sin
  acercamiento lateral/central.
- Se agregaron tests puros para el reset completo y para el caso con estrategia
  en el siguiente router.

## Subcorte Transiciones Router/Boring

Hallazgos aplicados:

- Se extrajo `_router_to_boring_transition_lines` para compartir el reset
  router hacia top drill, side drill y slot milling.
- Se extrajeron `_boring_to_router_side_restore_lines`,
  `_boring_to_router_top_face_lines` y `_boring_to_router_cleanup_lines` para
  separar restauracion de marco lateral, seleccion de cara Top y limpieza antes
  de volver al router.
- Se extrajo `_line_milling_prepare_after_boring_lines` para la preparacion
  incremental del router despues del cabezal de perforacion/ranurado.
- Se extrajeron `_top_drill_prepare_after_router_base_lines`,
  `_side_drill_prepare_after_router_lines` y `_tool_shift_lines` para separar
  preparaciones base y shifts de herramienta en entradas desde router.
- Se agregaron tests puros para cada helper nuevo del bloque.

## Subcorte Resets Por Cabezal

Hallazgos aplicados:

- Se extrajo `_line_milling_reset_lines` como builder interno del reset router
  base; `profile_milling` conserva su delegacion sobre el mismo reset.
- Se extrajeron `_top_drill_reset_lines` y `_side_drill_reset_lines` sobre un
  builder comun de boring head para fijar las variantes parcial/final sin
  duplicar la secuencia `MLV/SHF/ETK/G61`.
- Se extrajo `_slot_milling_reset_lines` para aislar las variantes final,
  parcial y parcial sin `?%ETK[7]=0` usadas por las transiciones de sierra.
- Los emisores de reset siguen dentro de `emitter.py` porque todavia adjuntan
  fuentes, confianza, `block_id` y notas explicativas por linea.
- Se agregaron tests puros para reset router, reset top/side parcial/final y
  reset de ranura final/parcial.

## Deuda Residual

- Extraer `iso_state_synthesis.emitter` por familias o etapas cuando se retome
  la generacion ISO, porque todavia concentra preparacion, apendice explicado
  de resets, formato y comparacion. La traza router y los resets principales
  ya tienen builders internos de lineas, pero aun no se movieron a modulos
  separados.
- Agregar fixtures PGMX/ISO chicos dentro de `tests/fixtures` o `tmp` controlado
  para cubrir `pgmx_source.py` y una emision real sin depender de rutas `S:` o
  `P:`.
- Separar claramente los estudios fechados de las reglas promovidas al catalogo.
- Auditar `tools/studies/iso/` despues de este bloque para confirmar que los
  estudios reproducibles apuntan al paquete vigente.
