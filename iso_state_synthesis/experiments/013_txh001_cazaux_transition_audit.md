# T-XH-001 Transition Audit - Cazaux

Fecha: 2026-05-13

## Objetivo

Crear una lista antes/despues de los candidatos ISO que ejercitan
`T-XH-001`, separar los exactos de los que fallan en esa transicion y medir el
impacto del cambio.

## Herramienta

Script:

`tools/studies/iso/txh001_transition_audit_2026_05_13.py`

Lista base:

```powershell
py -3 -m tools.studies.iso.txh001_transition_audit_2026_05_13 --label before
```

Lista posterior:

```powershell
py -3 -m tools.studies.iso.txh001_transition_audit_2026_05_13 `
  --label after `
  --baseline-csv "S:\Maestro\Projects\ProdAction\Prod 26-01-01 Cazaux\_analysis\txh001_transition_audit_before.csv"
```

Salidas:

- `S:\Maestro\Projects\ProdAction\Prod 26-01-01 Cazaux\_analysis\txh001_transition_audit_before.csv`
- `S:\Maestro\Projects\ProdAction\Prod 26-01-01 Cazaux\_analysis\txh001_transition_audit_before.md`
- `S:\Maestro\Projects\ProdAction\Prod 26-01-01 Cazaux\_analysis\txh001_transition_audit_after.csv`
- `S:\Maestro\Projects\ProdAction\Prod 26-01-01 Cazaux\_analysis\txh001_transition_audit_after.md`

## Lista Base

Filas con `T-XH-001`: `71`.

| resultado | cantidad |
| --- | ---: |
| `exact` | 33 |
| `header_only` | 20 |
| `other_diff` | 13 |
| `txh001_diff` | 5 |

Los `5` `txh001_diff` comparten el mismo patron:

- transicion visible: `line_milling -> top_drill`;
- herramienta entrante: `005`;
- velocidad: `6000`;
- mascara: `?%ETK[0]=16`;
- el diferencial no traia `salida.etk_17` porque ya habia existido un
  `top_drill 005` previo.

Sintoma:

```text
Maestro:   ?%ETK[17]=257
Candidato: ?%ETK[0]=16
```

## Regla Aplicada

Punto de codigo:

`iso_state_synthesis/emitter.py::_emit_top_drill_prepare_after_router`

Cuando la preparacion de top drill viene de `line_milling` y el diferencial no
trae cambio explicito de `salida.etk_17`, el emisor reactiva la velocidad del
cabezal perforador antes de emitir la mascara:

```text
?%ETK[17]=257
S...M3
?%ETK[0]=...
```

La regla queda acotada a `T-XH-001` y no cambia la preparacion general de
`top_drill`.

## Lista Posterior

Filas con `T-XH-001`: `71`.

| resultado | cantidad |
| --- | ---: |
| `exact` | 33 |
| `header_only` | 20 |
| `other_diff` | 18 |
| `txh001_diff` | 0 |

Comparacion contra la lista base:

| cambio | cantidad |
| --- | ---: |
| `still_exact` | 33 |
| `still_header_only` | 20 |
| `unchanged_same_front` | 13 |
| `txh001_cleared_next_front` | 5 |
| `worsened` | 0 |

Los `5` casos que antes fallaban en `T-XH-001` ahora muestran el siguiente
frente:

| nuevo frente | cantidad |
| --- | ---: |
| `B-BH-007` | 4 |
| `T-XH-002` | 1 |

## Corpus Completo Despues Del Cambio

El clasificador general queda:

| clase | cantidad |
| --- | ---: |
| `exact` | 65 |
| `header_only` | 21 |
| `operational_diff` | 18 |

Primeros frentes operativos:

| frente | cantidad |
| --- | ---: |
| `B-BH-007` | 8 |
| `T-XH-002` | 5 |
| `B-BH-005` | 3 |
| `B-BH-002` | 2 |

`T-XH-001` queda en `0` como primer frente operativo. El proximo frente
recomendado es `B-BH-007`, porque concentra las salidas de sierra vertical
`G0 Z20.000` vs `G1 X... Z20.000`.

## Validacion Ampliada

| corpus | resultado |
| --- | ---: |
| raiz `Pieza*` | `217/222` |
| `ISO\Cocina` | `72/84` |
| Cazaux completo | `65/104` exactos + `21/104` `header_only` |

La raiz `Pieza*` queda estable. `ISO\Cocina` sube de `68/84` a `72/84` porque
cuatro casos que antes se detenian en `T-XH-001` ahora avanzan hasta el frente
real siguiente (`B-BH-007`).
