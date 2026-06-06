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
