# T-XH-002 Boring To Router - Cazaux

Fecha: 2026-05-13

## Objetivo

Cerrar el frente `T-XH-002` que quedo despues de resolver `B-PG-002`.
El frente agrupaba retornos desde cabezal de perforacion/ranurado hacia router.

Sintomas iniciales:

- en retornos `top_drill -> line_milling`, Maestro insertaba
  `?%ETK[8]=1/G40` antes de apagar velocidad;
- en retorno `side_drill Back -> line_milling`, Maestro restauraba el marco
  lateral derecho antes de seleccionar Top.

## Casos Observados

Lista inicial de `5` primeras diferencias:

| caso | sintoma inicial |
| --- | --- |
| `Baño\Vanitory\Lat_Der.pgmx` | `?%ETK[8]=1 / ?%ETK[17]=0` |
| `Baño\Vanitory\Lat_Izq.pgmx` | `?%ETK[8]=1 / ?%ETK[17]=0` |
| `Cocina\mod 6 - Torre horno\Divisor_Horiz.pgmx` | `MLV=1 / ?%ETK[8]=1` |
| `Cocina\mod 6 - Torre horno\Lat_Der.pgmx` | `?%ETK[8]=1 / ?%ETK[17]=0` |
| `Cocina\mod 6 - Torre horno\Lat_Izq.pgmx` | `?%ETK[8]=1 / ?%ETK[17]=0` |

Controles historicos:

- `Pieza_162.pgmx`: `top_drill -> line_milling`, sin router previo, no debe
  insertar `?%ETK[8]=1/G40`;
- `Pieza_163.pgmx`: `side_drill Front -> line_milling`, no debe restaurar
  marco lateral derecho adicional;
- `Pieza_164.pgmx`: `slot_milling -> line_milling`, no debe cambiar.

## Reglas Aplicadas

Punto de codigo:

`iso_state_synthesis/emitter.py::_emit_boring_to_router_transition`

### Top Drill Con Router Previo

Cuando el retorno `top_drill -> line_milling` viene despues de un router previo
real, Maestro puede exigir la seleccion Top antes de limpiar velocidad.

La regla previa ya cubria `previous_router_group == profile_milling` cuando el
perfil lo justificaba. Se agrego el subcaso:

```text
previous_router_group.family == line_milling
previous_router_group.incoming_transition_id == T-RH-001
profile_family == OpenPolyline
side_of_feature in {Left, Right}
```

En ese caso se emite:

```text
?%ETK[8]=1
G40
?%ETK[17]=0
M5
?%ETK[0]=0
...
```

### Side Drill Back/Left A Router

Cuando el retorno sale desde lateral `Back` o `Left`, Maestro restaura primero
el marco lateral derecho y repite `?%ETK[7]=0` antes de seleccionar Top:

```text
MLV=1
SHF[X]=...
SHF[Y]=...
SHF[Z]=...+%ETK[114]/1000
?%ETK[7]=0
?%ETK[8]=1
G40
```

La restauracion usa el marco `Right`, igual que otros retornos desde
`Back/Left` hacia trabajos Top.

## Validacion

Comando principal:

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

`T-XH-002` queda en `0` como primer frente. Resultado de los `5` casos:

| caso | resultado posterior |
| --- | --- |
| `Baño\Vanitory\Lat_Der.pgmx` | exacto |
| `Baño\Vanitory\Lat_Izq.pgmx` | exacto |
| `Cocina\mod 6 - Torre horno\Divisor_Horiz.pgmx` | despeja `T-XH-002`; nuevo frente `B-RH-002` |
| `Cocina\mod 6 - Torre horno\Lat_Der.pgmx` | despeja `T-XH-002`; nuevo frente `T-XH-001` |
| `Cocina\mod 6 - Torre horno\Lat_Izq.pgmx` | exacto |

Controles:

| caso | resultado |
| --- | --- |
| `Pieza_162.pgmx` | exacto `125/125` |
| `Pieza_163.pgmx` | exacto `129/129` |
| `Pieza_164.pgmx` | exacto `132/132` |
| raiz `Pieza*` | `217/222` |
| `ISO\Cocina` | `79/84` |
| Cazaux completo | `76/104` exactos + `21/104` `header_only` |

## Nueva Frontera

Los primeros frentes operativos quedan:

| frente | cantidad |
| --- | ---: |
| `B-BH-005` | 3 |
| `B-BH-002` | 2 |
| `B-RH-002` | 1 |
| `T-XH-001` | 1 |

El siguiente frente cuantitativo recomendado es `B-BH-005`.
