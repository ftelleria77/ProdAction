# Experimento 005 - Estado De Fresado Lineal E004

Fecha: 2026-05-07

## Proposito

Agregar la familia de fresado lineal superior con herramienta `E004` al emisor
explicativo por estado, usando las variantes minimas `ISO_MIN_020` a
`ISO_MIN_023`.

## Fuentes Revisadas

- `S:\Maestro\Projects\ProdAction\ISO\minimal_fixtures_2026-05-03\ISO_MIN_020_LineE004_Base.pgmx`
- `S:\Maestro\Projects\ProdAction\ISO\minimal_fixtures_2026-05-03\ISO_MIN_021_LineE004_Y60.pgmx`
- `S:\Maestro\Projects\ProdAction\ISO\minimal_fixtures_2026-05-03\ISO_MIN_022_LineE004_PH5.pgmx`
- `S:\Maestro\Projects\ProdAction\ISO\minimal_fixtures_2026-05-03\ISO_MIN_023_LineE004_OriginY10.pgmx`
- `P:\USBMIX\ProdAction\ISO\minimal_fixtures_2026-05-03\iso_min_020_linee004_base.iso`
- `P:\USBMIX\ProdAction\ISO\minimal_fixtures_2026-05-03\iso_min_021_linee004_y60.iso`
- `P:\USBMIX\ProdAction\ISO\minimal_fixtures_2026-05-03\iso_min_022_linee004_ph5.iso`
- `P:\USBMIX\ProdAction\ISO\minimal_fixtures_2026-05-03\iso_min_023_linee004_originy10.iso`
- `def.tlgx` embebido dentro de cada `.pgmx`
- `iso_state_synthesis/machine_config/snapshot/xilog_plus/Cfg/pheads.cfg`

## Estado De Herramienta

La operacion PGMX es `BottomAndSideFinishMilling` con `ToolKey=E004`. La
herramienta se toma del `def.tlgx` embebido:

| Valor | Fuente | ISO |
| --- | --- | --- |
| Numero de herramienta `4` | `ToolKey/Name=E004` | `T4`, `?%ETK[9]=4` |
| Spindle router `1` | regla observada E004 | `?%ETK[6]=1` |
| Activacion router | regla observada E004 | `?%ETK[18]=1` |
| Velocidad `18000` | `SpindleSpeed.Standard` | `S18000M3` |
| Largo `107.200` | `ToolOffsetLength` | `SVL 107.200`, `VL6=107.200` |
| Radio `2.000` | `tool_width / 2` | `SVR 2.000`, `VL7=2.000` |

Los offsets `MLV=2` del router salen de `pheads.cfg`, usando los valores
numericos 308..310 con signo invertido:

| Indice numerico | Valor config | ISO |
| ---: | ---: | ---: |
| 308 | -32.05 | `SHF[X]=32.050` |
| 309 | 246.65 | `SHF[Y]=-246.650` |
| 310 | 125.30 | `SHF[Z]=-125.300` |

## Reglas De Traza

Para la linea simple:

- la entrada rapida usa `Z = security_plane + ToolOffsetLength`;
- la profundidad pasante usa `Z = -(piece_depth + extra_depth)`;
- el avance de bajada usa `DescentSpeed.Standard * 1000`;
- el avance de corte usa `FeedRate.Standard * 1000`;
- Maestro repite la cota `Z` tambien cuando solo cambia `X` o `Y`.

Para `ISO_MIN_022_LineE004_PH5`, la estrategia unidireccional `PH=5` no emite
`G41/G42` cuando `SideOfFeature=Center`. La trayectoria se toma de los
`TrajectoryPath` del `.pgmx` y traduce cada punto con:

```text
Z ISO = local_z - piece_depth
```

Esto reproduce los niveles alternados `Z-5`, `Z5`, `Z-10`, `Z0`, `Z-15`,
`Z-5` y `Z-19`.

## Reset Y Cierre

El reset posterior E004 limpia:

- `D0`;
- `SVL/VL6`;
- `SVR/VL7`;
- `?%ETK[7]=0`.

El cierre router agrega antes del reset comun:

```iso
G61
MLV=0
?%ETK[13]=0
?%ETK[18]=0
M5
D0
G0 G53 Z201.000
G0 G53 X-3700.000
G64
```

## Validacion

Comando:

```powershell
py -3 -m iso_state_synthesis compare-candidate <ISO_MIN_020_a_023.pgmx> <maestro.iso>
```

Resultado:

| Variante | Resultado |
| --- | --- |
| `ISO_MIN_020_LineE004_Base` | `94 vs 94 lineas`, `0 diferencias` |
| `ISO_MIN_021_LineE004_Y60` | `94 vs 94 lineas`, `0 diferencias` |
| `ISO_MIN_022_LineE004_PH5` | `108 vs 108 lineas`, `0 diferencias` |
| `ISO_MIN_023_LineE004_OriginY10` | `94 vs 94 lineas`, `0 diferencias` |

Lectura: el emisor candidato ya reproduce las 14 piezas minimas del corpus
`ISO_MIN_*`: Top Drill, Side Drill y Line E004. Sigue acotado a una familia por
programa.
