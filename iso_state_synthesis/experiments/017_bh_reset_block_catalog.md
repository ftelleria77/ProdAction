# Boring Head Reset Block Catalog

Fecha: 2026-05-14

## Objetivo

Separar los resets completos y parciales del cabezal de perforacion/ranurado
en bloques `B-*` distintos, sin cambiar el texto ISO emitido.

Antes del cambio, los resets de `top_drill`, `side_drill` y `slot_milling`
quedaban mezclados como etapas `*_reset` sin granularidad suficiente para
estadisticas de bloques. En particular, `B-BH-003` describia el reset completo
de taladro superior, pero las lineas de reset parcial usadas en transiciones
no tenian un bloque propio.

## Bloques Agregados

| bloque | familia | rol |
| --- | --- | --- |
| `B-BH-008` | `top_drill` | reset parcial |
| `B-BH-009` | `side_drill` | reset completo |
| `B-BH-010` | `side_drill` | reset parcial |
| `B-BH-011` | `slot_milling` | reset completo |
| `B-BH-012` | `slot_milling` | reset parcial |

`B-BH-003` queda como reset completo de `top_drill`.

## Regla De Emision

Los emisores de reset ahora asignan `block_id` explicito segun el parametro
`final`:

```text
top_drill_reset(final=False)    -> B-BH-008
top_drill_reset(final=True)     -> B-BH-003
side_drill_reset(final=False)   -> B-BH-010
side_drill_reset(final=True)    -> B-BH-009
slot_milling_reset(final=False) -> B-BH-012
slot_milling_reset(final=True)  -> B-BH-011
```

No se cambio ningun comando ISO; solo cambia la metadata explicativa
`ExplainedIsoLine.block_id`.

## Validacion

Comando:

```powershell
py -3 -m tools.studies.iso.block_transition_corpus_analysis_2026_05_13
```

Salida:

```text
Analyzed 104 PGMX/ISO rows.
exact: 76
header_only: 21
operational_diff: 7
```

Conteo directo de `block_sequence` en Cazaux:

| bloque | apariciones | ejemplos |
| --- | ---: | ---: |
| `B-BH-008` | 495 | 69 |
| `B-BH-009` | 41 | 41 |
| `B-BH-010` | 187 | 42 |
| `B-BH-011` | 7 | 7 |
| `B-BH-012` | 17 | 17 |

## Lectura

La separacion confirma que la mayor parte de los resets de taladro superior son
parciales y pertenecen a continuidad/transiciones internas, no a un cierre
completo del cabezal. Esto hace que las estadisticas de bloques sean mas utiles
para decidir la proxima frontera.
