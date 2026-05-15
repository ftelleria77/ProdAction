# 018 - B-BH-005 Cazaux Side Drill Order And Pause

Fecha: 2026-05-14

## Objetivo

Reducir los residuales operativos del bloque `B-BH-005` en el corpus real
`Prod 26-01-01 Cazaux` sin cambiar reglas laterales que ya estaban exactas.

Punto de partida despues de la catalogacion de resets:

- `76` exactos
- `21` `header_only`
- `7` operativos
- `B-BH-005`: `3` primeros frentes

## Casos

| pieza | sintoma | decision |
| --- | --- | --- |
| `Cocina/mod 12 - Isla/Faja_Superior.pgmx` | Maestro ejecuta `Back` final, luego `Front`, luego `Back` inicial | rotar tandas cuando la misma cara abre y cierra el bloque lateral |
| `Lavadero/mod 2 - bajo 1 puerta/Fondo.pgmx` | falta `G4F0.500` antes de la primera lateral despues de `top slot` | agregar pausa en `T-BH-008` si entra a secuencia lateral multiple |
| `Bano/Vanitory/Faja frontal.pgmx` | cota fija `Left`: Maestro usa `Y-130/-70`, candidato `Y-80/-20` | queda pendiente; la regla global de geometria rompe otros casos |

## Reglas Aplicadas

### Orden De Tandas Laterales

En `iso_state_synthesis/pgmx_source.py::_ordered_side_drill_block`, si la
secuencia lateral cruda contiene tandas de cara y la primera cara tambien es la
ultima, se rota la tanda final al frente:

```text
Back -> Front -> Back
```

queda como:

```text
Back(tanda final) -> Front -> Back(tanda inicial)
```

Cada tanda conserva el orden interno por `_side_drill_step_sort_key`.

### Pausa Desde Top Slot

En `iso_state_synthesis/emitter.py::_emit_side_drill_prepare_after_slot`, la
preparacion `T-BH-008` emite `G4F0.500` despues de `?%ETK[0]` cuando el
siguiente trabajo tambien es `side_drill`.

## Hipotesis Descartada

Se probo usar la geometria de la feature como cota fija global para `Left`.
Arreglaba `Bano/Vanitory/Faja frontal.pgmx`, pero rompia casos que ya estaban
exactos:

- `67` exactos
- `22` `header_only`
- `15` operativos

Conclusion: la cota `Left` residual no debe generalizarse solo por geometria.
Hace falta una mini tanda o una condicion mas fuerte para piezas angostas.

## Validacion

Comandos:

```powershell
py -3 -m py_compile iso_state_synthesis\pgmx_source.py iso_state_synthesis\emitter.py
py -3 -m tools.studies.iso.block_transition_corpus_analysis_2026_05_13
```

Resultado Cazaux:

- `77` exactos
- `22` `header_only`
- `5` operativos

Validacion ampliada:

- raiz `Pieza*`: `217/222` exactos
- `ISO/Cocina`: `80/84` exactos

Primeros frentes restantes:

| frente | casos |
| --- | ---: |
| `B-BH-002` | 2 |
| `B-BH-005` | 1 |
| `B-RH-002` | 1 |
| `T-XH-001` | 1 |

## Pendiente

El ultimo `B-BH-005` es `Bano/Vanitory/Faja frontal.pgmx`. Maestro usa cota
fija `Left` espejo de geometria en una pieza angosta (`width=150`), pero no es
seguro aplicar esa regla a todos los `Left`: hay muchos exactos donde Maestro
usa la cota de toolpath actual.

## Actualizacion 2026-05-14

El residual `Bano/Vanitory/Faja frontal.pgmx` quedo cerrado con una condicion
mas acotada que la hipotesis global descartada:

- plano `Left`;
- sin replicacion;
- la cota fija de toolpath mas la geometria infiere ancho `<=150`;
- en ese caso se usa la geometria directa como cota fija lateral y tambien para
  ordenar el bloque.

Actualizacion posterior 2026-05-15: esta pausa no se conserva para todos los
anchos `<=150`. La regla amplia reabria `4` DeMarco. La condicion vigente queda
mas estrecha: ultimo `Left -> Left`, sin trabajo posterior, mismo spindle, eje
`X`, ancho `150`, largo `<=1000` y cota fija lateral `-130 -> -70`.

Validacion:

- `Bano/Vanitory/Faja frontal.pgmx`: exacto;
- Cazaux completo: `82` exactos, `22` `header_only`;
- raiz `Pieza*`: `217/222` exactos;
- `ISO/Cocina`: `84/84` exactos.

Con esto `B-BH-005` queda en `0` como primer frente del corpus Cazaux.

## Actualizacion 2026-05-15 DeMarco

El mismo frente reaparecio en DeMarco con ancho `220`: el toolpath `Left`
venia espejado y Maestro usaba la geometria directa por bloque. La condicion
vigente para cota fija `Left` queda:

- sin replicacion;
- working step `XBO_*`;
- `toolpath_raw + geometry_x` coincide con el ancho real del plano.

Esta regla conserva Cazaux `82` exactos, `22` `header_only`; `ISO/Cocina`
`84/84`; y cierra DeMarco a `329` exactos, `2` `header_only`, `5`
`precision_only`, `0` operativos.
