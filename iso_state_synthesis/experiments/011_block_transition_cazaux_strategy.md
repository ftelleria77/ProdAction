# Block And Transition Strategy - Cazaux

Fecha: 2026-05-13

## Objetivo

Continuar el estudio de `Prod 26-01-01 Cazaux` desde la secuencia de bloques y
transiciones, no desde diferencias linea-a-linea aisladas. El reporte clasifica
cada primera diferencia significativa con el `block_id`, `transition_id`,
`stage_key` y secuencia de familias que ya emite el candidato.

## Herramienta

Script:

`tools/studies/iso/block_transition_corpus_analysis_2026_05_13.py`

Comando:

```powershell
py -3 -m tools.studies.iso.block_transition_corpus_analysis_2026_05_13
```

Salidas:

- `S:\Maestro\Projects\ProdAction\Prod 26-01-01 Cazaux\_analysis\block_transition_corpus_analysis.csv`
- `S:\Maestro\Projects\ProdAction\Prod 26-01-01 Cazaux\_analysis\block_transition_corpus_summary.md`

La clasificacion ignora, solo para buscar la primera diferencia operativa,
deltas menores de cabecera `%Or[...]` de hasta `0.05`. El comparador exacto no
se modifica.

## Resultado Del Corpus

Pares PGMX/ISO: `104/104`

| clase | cantidad |
| --- | ---: |
| `exact` | 62 |
| `header_only` | 20 |
| `operational_diff` | 22 |

Lectura: si se separa la precision menor de cabecera, el frente operativo real
queda en `22/104`.

## Frentes Operativos

| frente | cantidad | primera diferencia tipica | punto de codigo |
| --- | ---: | --- | --- |
| `B-RH-002` | 9 | `G0 / MLV`, `G1 / G1` | `emitter.py::_emit_line_milling_trace` |
| `T-XH-001` | 4 | `?%ETK[17]=257 / ?%ETK[0]=16` | `emitter.py::_emit_top_drill_prepare_after_router` |
| `B-BH-005` | 3 | `G0 / G0`, `G4F0.500 / G0` | `pgmx_source.py::_ordered_side_drill_block`, `emitter.py::_emit_side_drill_trace` |
| `B-BH-007` | 3 | `G0 Z20 / G1 X... Z20` | `emitter.py::_emit_slot_milling_trace` |
| `B-BH-002` | 2 | `G0 / G0` | `pgmx_source.py::_ordered_top_drill_block` |
| `T-XH-002` | 1 | `MLV=1 / ?%ETK[8]=1` | `emitter.py::_emit_boring_to_router_transition` |

## Estrategia De Mejora

### 1. `B-RH-002`: traza router

Es el frente con mas residuales operativos (`9/22`).

Subcasos:

- `6` casos `G0 / MLV`: el candidato agrega `MLV=2` despues de `G17` antes del
  primer `G0`; Maestro entra directo con `G0 X... Y... Z...`.
- `3` casos `G1 / G1`: Maestro repite `Z-13.000` en un segmento de corte y el
  candidato lo omite por modalidad.

Plan:

1. Armar mini tanda para `line_milling` despues de router previo, especialmente
   cuando `_emit_line_milling_trace(..., previous_router_trace=...)` esta activo.
2. Separar dos reglas:
   - entrada: condicion para omitir `MLV=2` despues de `G17`;
   - traza: condicion para `always_include_z` en segmentos `OpenPolyline` o
     linea posterior a cadena de cabezal perforador.
3. Validar contra Cazaux, `Cocina` y `Pieza*` antes de tocar otras
   transiciones.

### 2. `T-XH-001`: router -> top drill

Los `4` casos fallan porque Maestro emite:

```text
?%ETK[17]=257
S6000M3
?%ETK[0]=16
```

El candidato salta directo a `?%ETK[0]=16`.

Plan:

1. Aislar mini tanda `line_milling -> top_drill 005` y otra
   `profile_milling -> top_drill 005`.
2. Confirmar si la activacion de velocidad debe forzarse en `T-XH-001` aun
   cuando el diferencial no marque cambio de `etk_17`.
3. Si se confirma, agregar condicion acotada en
   `_emit_top_drill_prepare_after_router`, no en la preparacion general de
   `top_drill`.

### 3. `B-BH-007`: sierra vertical / `SlotSide`

Los `3` casos fallan en la salida de ranura: Maestro hace `G0 Z20.000`, mientras
el candidato conserva una salida compensada con `G1 X... Z20.000`.

Plan:

1. Aislar `top_drill -> slot_milling -> top_drill/side_drill`.
2. Ver si el parametro actual `emit_transition_exit=True` debe depender de la
   geometria de salida o del trabajo siguiente.
3. Ajustar `_emit_slot_milling_trace` solo despues de esa tanda, porque el bloque
   tambien se usa en transiciones ya cerradas.

### 4. `B-BH-005`: side drill

Tres residuales mezclan orden/posicion lateral y pausa:

- `G0 / G0`: el primer punto lateral no coincide;
- `G4F0.500 / G0`: Maestro pausa antes de la traza lateral y el candidato entra
  directo.

Plan:

1. Separar ordenamiento lateral (`_ordered_side_drill_block`) de emision de
   traza (`_emit_side_drill_trace`).
2. Para los `G0 / G0`, comparar orden crudo vs candidato vs Maestro como se hizo
   con `top_drill`.
3. Para `G4F0.500 / G0`, revisar si pertenece a `T-BH-008`
   (`slot_milling -> side_drill`) y no al bloque lateral puro.

### 5. `B-BH-002`: top drill residual menor

Solo quedan dos casos (`mod 8 - Abierto`) despues de la regla de herramienta
explicita/automatica. Ambos parecen ser una regla secundaria de punto inicial:
Maestro arranca en `005@516,50` y la regla actual arranca por menor `(X,Y)`.

Plan:

1. No tocar la regla general, que ya cubre `58/60` casos comparables.
2. Aislar una mini tanda de cuatro huecos `005` con forma similar a `mod 8`.
3. Buscar condicion de arranque por menor `Y` o por punto cercano a la salida
   del perfil previo.

### 6. `T-XH-002`: boring head -> router

Un solo caso (`Divisor_Horiz`) muestra que Maestro empieza el retorno con
`MLV=1` y el candidato selecciona Top con `?%ETK[8]=1` demasiado temprano.

Plan:

1. Dejarlo despues de `B-RH-002` y `T-XH-001`.
2. Al retomarlo, aislar `side_drill -> line_milling` con cadena lateral previa.
3. Ajustar `_emit_boring_to_router_transition` solo para el retorno desde
   lateral si la mini tanda lo confirma.

## Orden Recomendado

1. `B-RH-002` entrada/traza router.
2. `T-XH-001` activacion de velocidad al pasar de router a top drill.
3. `B-BH-007` salida de sierra vertical.
4. `B-BH-005` orden/pausa lateral.
5. `B-BH-002` arranque residual de top drill.
6. `T-XH-002` retorno lateral/router.

Los `20` casos `header_only` se tratan como frente separado de formato de
cabecera. No deben mezclarse con decisiones de bloque/transicion.

## Seguimiento

- 2026-05-13: `B-RH-002` quedo cerrado en el corpus Cazaux. La regla y la
  validacion estan registradas en
  `iso_state_synthesis/experiments/012_b_rh_002_cazaux_router_trace.md`.
- Resultado posterior: `65` exactos, `21` `header_only` y `18`
  `operational_diff`. El primer frente `B-RH-002` baja de `9` a `0`.
- Nueva prioridad: `T-XH-001`, con `5/18` residuales operativos.
- 2026-05-13: `T-XH-001` tambien quedo cerrado como primer frente. La lista
  antes/despues, el plan y la validacion estan en
  `iso_state_synthesis/experiments/013_txh001_cazaux_transition_audit.md`.
  La auditoria dedicada muestra `33` casos que siguen exactos, `20` que siguen
  `header_only`, `5` casos con `T-XH-001` despejado hacia el siguiente frente y
  `0` empeorados. El corpus general queda `65` exactos, `21` `header_only` y
  `18` residuales; los primeros frentes son ahora `B-BH-007` `8`,
  `T-XH-002` `5`, `B-BH-005` `3` y `B-BH-002` `2`.
- 2026-05-13: `B-BH-007` quedo cerrado como primer frente. La salida de
  `SlotSide` en `T-BH-005` siempre conserva el lift a `Z20`; la salida
  lateral/reentrada completa solo se omite cuando el trabajo siguiente es
  `top_drill` con herramienta distinta de `001`. La validacion esta registrada
  en `iso_state_synthesis/experiments/014_b_bh_007_cazaux_slot_exit.md`.
  El corpus general sigue `65` exactos, `21` `header_only` y `18`
  residuales, pero `B-BH-007` baja a `0`. Los primeros frentes son ahora
  `B-PG-002` `8`, `T-XH-002` `5`, `B-BH-005` `3` y `B-BH-002` `2`.
- 2026-05-13: `B-PG-002` quedo cerrado como primer frente. El prefijo especial
  de cierre lateral derecho se conserva para los `fajx` con `Xn` sin `Y`, pero
  se omite cuando el cierre trae `program_close_y=0.0`. La validacion esta en
  `iso_state_synthesis/experiments/015_b_pg_002_cazaux_program_close.md`.
  El corpus general sube a `73` exactos, `21` `header_only` y `10`
  residuales; los primeros frentes son ahora `T-XH-002` `5`, `B-BH-005` `3` y
  `B-BH-002` `2`.
- 2026-05-13: `T-XH-002` quedo cerrado como primer frente. La regla agrega
  seleccion Top al volver desde `top_drill` a router cuando el router previo es
  una cadena `OpenPolyline` (`T-RH-001`), y restaura marco lateral derecho al
  volver desde `side_drill Back/Left` a router. La validacion esta en
  `iso_state_synthesis/experiments/016_txh002_cazaux_boring_to_router.md`.
  El corpus general sube a `76` exactos, `21` `header_only` y `7`
  residuales; los primeros frentes son ahora `B-BH-005` `3`, `B-BH-002` `2`,
  `B-RH-002` `1` y `T-XH-001` `1`.
- 2026-05-14: los resets completos/parciales quedaron separados como bloques
  `B-BH-003/008`, `B-BH-009/010` y `B-BH-011/012`, sin cambiar texto ISO.
  La validacion esta en
  `iso_state_synthesis/experiments/017_bh_reset_block_catalog.md`.
- 2026-05-14: `B-BH-005` bajo como primer frente con el reorden de tandas
  laterales `Back -> Front -> Back` y la pausa al entrar desde sierra a una
  secuencia lateral multiple. La validacion esta en
  `iso_state_synthesis/experiments/018_b_bh_005_cazaux_side_drill_order_pause.md`.
  El corpus general sube a `77` exactos, `22` `header_only` y `5` residuales.
- 2026-05-14: `B-BH-002` quedo cerrado con arranque top drill en maximo `X` y
  minimo `Y` para bloques automaticos de cuatro perforaciones, una herramienta
  efectiva y profundidades mixtas. La validacion esta en
  `iso_state_synthesis/experiments/019_b_bh_002_cazaux_top_drill_corner_start.md`.
  El corpus general sube a `79` exactos, `22` `header_only` y `3` residuales.
- 2026-05-14: el residual final `B-BH-005` quedo cerrado con cota directa para
  `Left` angosto sin replicacion. La validacion queda agregada en
  `iso_state_synthesis/experiments/018_b_bh_005_cazaux_side_drill_order_pause.md`.
  El corpus general sube a `80` exactos, `22` `header_only` y `2` residuales.
- 2026-05-14: el residual aislado `B-RH-002` de `Divisor_Horiz.pgmx` quedo
  cerrado con la regla de `LineHorizontal`/`LineVertical` compensado `Line Down`
  + `Line Up`. La validacion esta en
  `iso_state_synthesis/experiments/020_b_rh_002_cazaux_linear_side_compensation.md`.
  El corpus general queda `81` exactos, `22` `header_only` y `1` residual. El
  unico primer frente operativo restante es `T-XH-001`.
- 2026-05-14: el residual final `T-XH-001` de `Lat_Der.pgmx` quedo cerrado al
  extender la reactivacion de velocidad a `line_milling -> side_drill`. La
  validacion esta en
  `iso_state_synthesis/experiments/021_txh001_cazaux_router_to_side_speed.md`.
  El corpus general queda `82` exactos, `22` `header_only` y `0` residuales
  operativos; `ISO/Cocina` queda `84/84`.
