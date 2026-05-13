# B-BH-007 Slot Exit - Cazaux

Fecha: 2026-05-13

## Objetivo

Cerrar el frente `B-BH-007` que quedo despues de la correccion de
`T-XH-001`, sin romper los fixtures historicos de `SlotSide`.

El sintoma inicial era la salida de sierra vertical en transiciones
`top_drill -> slot_milling`:

```text
Maestro:   G0 Z20.000
Candidato: G1 X... Z20.000 F5000.000
```

## Casos Observados

Los `8` casos con primera diferencia `B-BH-007` pertenecian a laterales con la
secuencia:

```text
top_drill -> T-BH-005 -> slot_milling -> T-BH-006 -> top_drill
```

En esos casos, la herramienta superior siguiente era `005` y Maestro omitia la
salida lateral completa de la ranura: conservaba solo el levantamiento
`G1 Z20.000 F5000.000` y pasaba al reset/transicion siguiente.

Controles que no debian cambiar:

- si el siguiente `top_drill` usa herramienta `001`, Maestro conserva la salida
  lateral completa;
- si la ranura termina el programa, conserva la salida completa;
- si la ranura pasa a `side_drill` (`T-BH-008`), conserva la salida completa;
- las matrices historicas `Pieza_151`, `Pieza_155` y `Pieza_162` deben seguir
  exactas.

## Regla Aplicada

Punto de codigo:

`iso_state_synthesis/emitter.py::_emit_slot_milling_trace`

En la rama planificada `T-BH-005`, el emisor separa dos decisiones:

- `emit_transition_lift=True` siempre, porque Maestro mantiene el
  levantamiento feed a `Z20` despues del corte de ranura;
- `emit_transition_exit` depende del trabajo siguiente.

Predicado:

```text
next_group == None          -> salida completa
next_group.family != top    -> salida completa
next top tool == 001        -> salida completa
next top tool != 001        -> solo lift, sin salida lateral/reentrada
```

La regla queda acotada a `T-BH-005`; no cambia las ramas `T-BH-007`,
`T-BH-008` ni `T-XH-001`.

## Validacion

Comando principal:

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

Primeros frentes operativos despues del cambio:

| frente | cantidad |
| --- | ---: |
| `B-PG-002` | 8 |
| `T-XH-002` | 5 |
| `B-BH-005` | 3 |
| `B-BH-002` | 2 |

`B-BH-007` queda en `0` como primer frente. Los `8` laterales pasan al frente
siguiente real, `B-PG-002`, por cierre de programa:

```text
Maestro:   G0 G53 X... Y0.000
Candidato: G64
```

Controles puntuales:

| caso | resultado |
| --- | --- |
| `Cocina\mod 1 - bajo 1 puerta IZQ\Lado_derecho.pgmx` | exacto |
| `Lavadero\mod 2 - bajo 1 puerta\Lado_derecho.pgmx` | `header_only` |
| `Pieza_151.pgmx` | exacto `117/117` |
| `Pieza_155.pgmx` | exacto `120/120` |
| `Pieza_162.pgmx` | exacto `125/125` |
| raiz `Pieza*` | `217/222` |
| `ISO\Cocina` | `72/84` |
| Cazaux completo | `65/104` exactos + `21/104` `header_only` |

## Nueva Frontera

El siguiente frente cuantitativo es `B-PG-002` con `8` casos: los laterales
generan la ranura correcta y ahora difieren en el cierre final de maquina.

Despues quedan:

- `T-XH-002` con `5` casos;
- `B-BH-005` con `3` casos;
- `B-BH-002` con `2` casos.
