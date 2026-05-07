# Experimento 004 - Estado De Taladro Lateral D8

Fecha: 2026-05-07

## Proposito

Extender el emisor explicativo por estado desde `Top Drill` hacia taladros
laterales simples, sin crear una arquitectura por combinaciones. La pregunta de
este experimento fue que estado minimo cambia cuando la misma pieza usa una
cara lateral distinta.

## Fuentes Revisadas

- `S:\Maestro\Projects\ProdAction\ISO\minimal_fixtures_2026-05-03\ISO_MIN_010_LeftDrill_Base.pgmx`
- `S:\Maestro\Projects\ProdAction\ISO\minimal_fixtures_2026-05-03\ISO_MIN_011_RightDrill_Base.pgmx`
- `S:\Maestro\Projects\ProdAction\ISO\minimal_fixtures_2026-05-03\ISO_MIN_012_FrontDrill_Base.pgmx`
- `S:\Maestro\Projects\ProdAction\ISO\minimal_fixtures_2026-05-03\ISO_MIN_013_BackDrill_Base.pgmx`
- `P:\USBMIX\ProdAction\ISO\minimal_fixtures_2026-05-03\iso_min_010_leftdrill_base.iso`
- `P:\USBMIX\ProdAction\ISO\minimal_fixtures_2026-05-03\iso_min_011_rightdrill_base.iso`
- `P:\USBMIX\ProdAction\ISO\minimal_fixtures_2026-05-03\iso_min_012_frontdrill_base.iso`
- `P:\USBMIX\ProdAction\ISO\minimal_fixtures_2026-05-03\iso_min_013_backdrill_base.iso`
- `def.tlgx` embebido dentro de cada `.pgmx`

## Politica Lateral Observada

| Cara | `ETK[8]` | Spindle | `ETK[0]` | Eje de avance | Direccion | Signo coordenada fija |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| `Left` | 3 | 61 | 2147483648 | `X` | -1 | -1 |
| `Right` | 2 | 60 | 2147483648 | `X` | 1 | 1 |
| `Front` | 5 | 58 | 1073741824 | `Y` | -1 | 1 |
| `Back` | 4 | 59 | 1073741824 | `Y` | 1 | -1 |

Los `SHF[MLV=2]` de herramienta salen del negativo de las traslaciones del
spindle lateral embebido:

| Cara | `SHF[X]` | `SHF[Y]` | `SHF[Z]` |
| --- | ---: | ---: | ---: |
| `Left` | -118.000 | -32.000 | 66.300 |
| `Right` | -66.900 | -32.000 | 66.450 |
| `Front` | 32.000 | -21.750 | 66.500 |
| `Back` | 32.000 | 29.500 | 66.500 |

## Etapas Materializadas

- `side_drill_prepare`: selecciona cara, spindle lateral, mascara `ETK[0]`,
  velocidad del `BooringUnitHead` y offsets fisicos de herramienta.
- `side_drill_trace`: traduce el punto lateral a movimiento sobre el eje activo
  de la cara. La profundidad usa `pilot_length - target_depth - extra_depth`,
  con retirada a `20 + pilot_length`.
- `side_drill_reset`: apaga `ETK[7]`, vuelve el marco, limpia `ETK[0]`,
  resetea `ETK[17]`, `M5` y `D0`.
- `program_close`: conserva el cierre comun, con reentrada adicional de marco en
  `Left` y `Back`, tal como se observo en Maestro.

## Validacion

Comando:

```powershell
py -3 -m iso_state_synthesis compare-candidate <ISO_MIN_010_a_013.pgmx> <maestro.iso>
```

Resultado:

| Variante | Resultado |
| --- | --- |
| `ISO_MIN_010_LeftDrill_Base` | `97 vs 97 lineas`, `0 diferencias` |
| `ISO_MIN_011_RightDrill_Base` | `88 vs 88 lineas`, `0 diferencias` |
| `ISO_MIN_012_FrontDrill_Base` | `88 vs 88 lineas`, `0 diferencias` |
| `ISO_MIN_013_BackDrill_Base` | `97 vs 97 lineas`, `0 diferencias` |

Lectura: el modelo por estado ya cubre taladro superior y taladro lateral simple
como familias separadas. Todavia no mezcla familias dentro de un mismo programa.
