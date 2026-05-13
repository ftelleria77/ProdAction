# B-PG-002 Program Close - Cazaux

Fecha: 2026-05-13

## Objetivo

Cerrar el frente `B-PG-002` que quedo despues de resolver la salida de
`SlotSide` (`B-BH-007`). El sintoma estaba concentrado en laterales
`Lado_izquierdo` cuyo cierre final saltaba al `G64` demasiado temprano:

```text
Maestro:   G0 G53 X... Y0.000
Candidato: G64
```

## Casos Observados

Los `8` casos con primera diferencia `B-PG-002` compartian:

- ultimo trabajo real: `side_drill` sobre plano `Right`;
- programa mixto con trabajo previo `Top` y `SlotSide`;
- cierre `Xn` con `program_close_y=0.0`;
- candidato con prefijo de cierre lateral derecho
  `?%ETK[8]=2/G40/T1/M06` antes del cierre comun.

Controles exactos que si necesitaban ese prefijo:

- `fajx *.pgmx` de Cazaux;
- ultimo trabajo `side_drill` sobre plano `Right`;
- programa mixto con alternancia `Top/Left/Top/Left/Top/Right`;
- cierre `Xn` con solo `X=-2500`, sin `Y` explicito.

## Regla Aplicada

Punto de codigo:

`iso_state_synthesis/emitter.py::_emit_program_close`

El prefijo especial de cierre lateral derecho ahora se emite solo si:

```text
plane == Right
hay trabajos no laterales
program_close_x != -3700
program_close_y esta ausente
```

Si el `Xn` trae `Y` explicito, como `Y0.000`, Maestro usa el cierre comun
directo:

```text
G0 G53 Z201.000
G0 G53 X... Y0.000
G64
G61
D0
G0 G53 Z201.000
G64
SYN
...
```

## Validacion

Comando principal:

```powershell
py -3 -m tools.studies.iso.block_transition_corpus_analysis_2026_05_13
```

Salida:

```text
Analyzed 104 PGMX/ISO rows.
exact: 73
header_only: 21
operational_diff: 10
```

Primeros frentes operativos despues del cambio:

| frente | cantidad |
| --- | ---: |
| `T-XH-002` | 5 |
| `B-BH-005` | 3 |
| `B-BH-002` | 2 |

`B-PG-002` queda en `0` como primer frente. Los `8` laterales que antes
fallaban ahora quedan exactos:

- `Cocina\mod 1 - bajo 1 puerta IZQ\Lado_izquierdo.pgmx`
- `Cocina\mod 10,11 - Bajos ISLA\Lado_izquierdo.pgmx`
- `Cocina\mod 2 - bajo 2 puertas\Lado_izquierdo.pgmx`
- `Cocina\mod 3,4 - bajo 3 cajones\Lado_izquierdo.pgmx`
- `Cocina\mod 5 - Bajo despensero\Lado_izquierdo.pgmx`
- `Cocina\mod 7 - bajo 1 puerta DER\Lado_izquierdo.pgmx`
- `Lavadero\mod 1 - bajo 2 puertas\Lado_izquierdo.pgmx`
- `Lavadero\mod 2 - bajo 1 puerta\Lado_izquierdo.pgmx`

Controles:

| caso | resultado |
| --- | --- |
| `fajx *.pgmx` Cazaux | siguen exactos |
| raiz `Pieza*` | `217/222` |
| `ISO\Cocina` | `78/84` |
| Cazaux completo | `73/104` exactos + `21/104` `header_only` |

## Nueva Frontera

El siguiente frente cuantitativo es `T-XH-002` con `5` casos de retorno desde
cabezal de perforacion/ranurado hacia router. Despues quedan `B-BH-005` con
`3` casos y `B-BH-002` con `2` casos.
