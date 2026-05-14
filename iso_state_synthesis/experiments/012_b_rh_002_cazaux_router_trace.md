# B-RH-002 Router Trace - Cazaux

Fecha: 2026-05-13

## Objetivo

Cerrar el frente `B-RH-002` detectado en
`011_block_transition_cazaux_strategy.md`, sin tocar todavia las transiciones
`T-XH-001` ni `T-XH-002`.

El frente tenia dos sintomas:

- entrada incremental `line_milling -> line_milling`: sobraba `MLV=2` despues
  de `G17`;
- traza `OpenPolyline` compensada superficial: faltaba repetir `Z-13.000` en
  el tramo largo de corte.

## Regla Aplicada

Punto de codigo:

`iso_state_synthesis/emitter.py::_emit_line_milling_trace`

Entrada incremental router:

- `profile_milling -> line_milling` conserva `?%ETK[7]=0`, `G17`, `MLV=2`;
- `line_milling -> line_milling` conserva `?%ETK[7]=0`, `G17` y entra directo
  al primer `G0`, sin repetir `MLV=2`.

Traza `OpenPolyline` con compensacion lateral:

- se sigue repitiendo `Z` cuando la polilinea sale del rectangulo nominal de
  pieza;
- tambien se repite `Z` cuando el corte es superficial
  (`cut_z > -pieza.depth`).

## Evidencia

Antes del cambio, Cazaux tenia `9` primeras diferencias en `B-RH-002`:

| sintoma | cantidad |
| --- | ---: |
| `G0 / MLV` | 6 |
| `G1 / G1` sin `Z` | 3 |

Despues del cambio:

| clase | antes | despues |
| --- | ---: | ---: |
| `exact` | 62 | 65 |
| `header_only` | 20 | 21 |
| `operational_diff` | 22 | 18 |
| primer frente `B-RH-002` | 9 | 0 |

Comando:

```powershell
py -3 -m tools.studies.iso.block_transition_corpus_analysis_2026_05_13
```

Salida:

```text
Analyzed 104 PGMX/ISO rows.
exact: 65
header_only: 21
operational_diff: 18
```

Controles puntuales:

| caso | resultado |
| --- | --- |
| `Cocina\mod 3,4 - bajo 3 cajones\Lado_derecho.pgmx` | exacto `387/387` |
| `Cocina\mod 6 - Torre horno\Fondo.pgmx` | solo dos deltas menores `%Or` |
| `Bano\Vanitory\Lat_Der.pgmx` | `B-RH-002` queda cerrado; el primer residual visible pasa a `T-XH-002` |

## Nueva Frontera

Con `B-RH-002` cerrado, los `18` residuales operativos quedan asi:

| frente | cantidad |
| --- | ---: |
| `T-XH-001` | 5 |
| `T-XH-002` | 4 |
| `B-BH-007` | 4 |
| `B-BH-005` | 3 |
| `B-BH-002` | 2 |

La prioridad recomendada pasa a `T-XH-001`, porque concentra los casos donde
falta `?%ETK[17]=257/S6000M3` antes de `?%ETK[0]` al pasar de router a
taladro superior.

## Addendum 2026-05-14

Despues de cerrar otros frentes, reaparecio un residual `B-RH-002` aislado en
`Cocina\mod 6 - Torre horno\Divisor_Horiz.pgmx`.

Se registro como ficha separada:

`iso_state_synthesis/experiments/020_b_rh_002_cazaux_linear_side_compensation.md`

La regla nueva cubre `LineHorizontal`/`LineVertical` con compensacion lateral,
`Line Down` y `Line Up`, usando eje tangencial desde `Approach/Lift` y eje
normal nominal. Resultado Cazaux: `81` exactos, `22` `header_only`, `1`
operativo. El unico residual operativo restante pasa a `T-XH-001`.

Ese residual `T-XH-001` queda cerrado en
`iso_state_synthesis/experiments/021_txh001_cazaux_router_to_side_speed.md`.
