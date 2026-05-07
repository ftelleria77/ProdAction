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
`ISO_MIN_*`: Top Drill, Side Drill y Line E004.

## Ampliacion Con Secuencias E001 A E004

En el barrido posterior contra `Pieza_063..071`, `E004` aparece despues de un
perfil `E001`. En esa secuencia la preparacion E004 es incremental:

- no repite `?%ETK[6]=1`;
- no reemite `%Or[0]` ni `SHF[X/Y/Z]` del router;
- conserva cambio de herramienta, `?%ETK[9]=4`, `?%ETK[18]=1`, velocidad,
  `G17`, `MLV=2` y `?%ETK[13]=1`.

La traza lineal E004 ahora distingue:

- fixture minimo sin acercamiento/alejamiento real: mantiene el patron
  `ISO_MIN_020..023`;
- acercamiento/alejamiento lineal: emite los toolpaths `Approach`,
  `TrajectoryPath` y `Lift`;
- `SideOfFeature=Right/Left` sin PH5: emite coordenada nominal con `G42/G41`;
- PH5: conserva el toolpath offset y no emite `G41/G42`.

Validacion posterior:

| Variante | Resultado |
| --- | --- |
| `Pieza_063` | `143 vs 143 lineas`, `0 diferencias` |
| `Pieza_064` | `147 vs 147 lineas`, `0 diferencias` |
| `Pieza_065` | `147 vs 147 lineas`, `0 diferencias` |
| `Pieza_066` | `156 vs 156 lineas`, `0 diferencias` |
| `Pieza_067` | `156 vs 156 lineas`, `0 diferencias` |
| `Pieza_068` | `156 vs 156 lineas`, `0 diferencias` |
| `Pieza_069` | `150 vs 150 lineas`, `0 diferencias` |
| `Pieza_070` | `150 vs 150 lineas`, `0 diferencias` |
| `Pieza_071` | `150 vs 150 lineas`, `0 diferencias` |

Nota de generalizacion: el detector ya no queda atado a `ToolKey=E004`. Para
operaciones de fresado acepta herramientas `E00x`, incluida `E002`; el emisor
usa `ToolOffsetLength`, diametro/radio, avances y velocidad desde el `def.tlgx`
embebido. La evidencia exacta disponible en este corpus ya cubre `E004` y dos
casos `E003`; faltan piezas espejo para confirmar las otras herramientas con los
mismos recorridos.

## Ampliacion A Contornos E004 Center Sin Lead

En el mismo corpus, se agrego un subcaso acotado para `E004` con
`SideOfFeature=Center`, sin estrategia y sin acercamiento/alejamiento habilitado.
La preparacion sigue siendo la incremental de router cuando viene despues de
`E001`.

Reglas observadas:

- `OpenPolyline` sin compensacion usa los puntos de `TrajectoryPath`; despues de
  la bajada inicial Maestro no repite `Z` en los movimientos XY si la cota no
  cambia.
- `Circle` usa el centro del perfil como `I/J` y deduce `G3` o `G2` por el
  sentido `CounterClockwise`/`Clockwise`.
- El reset intermedio `E001 -> E004` no duplica `?%ETK[7]=0` cuando el siguiente
  `E004` no tiene acercamiento habilitado.

Validacion:

| Variante | Resultado |
| --- | --- |
| `Pieza_022` | `142 vs 142 lineas`, `0 diferencias` |
| `Pieza_025` | `141 vs 141 lineas`, `0 diferencias` |
| `Pieza_026` | `141 vs 141 lineas`, `0 diferencias` |

## Ampliacion A Contornos Sin Lead Left/Right

Para `OpenPolyline` y `Circle` con `SideOfFeature=Left/Right`, Maestro vuelve a
la coordenada nominal y activa compensacion:

- `Left` emite `G41`;
- `Right` emite `G42`;
- el acercamiento/alejamiento corto sin lead usa una distancia fija `1.000`
  sobre la tangente nominal, no `tool_radius / 2`;
- en secuencia `E001 -> E004`, el reset intermedio conserva el `?%ETK[7]=0`
  adicional para `Left/Right`.

Validacion:

| Variante | Resultado |
| --- | --- |
| `Pieza_016` | `100 vs 100 lineas`, `0 diferencias` |
| `Pieza_017` | `100 vs 100 lineas`, `0 diferencias` |
| `Pieza_023` | `147 vs 147 lineas`, `0 diferencias` |
| `Pieza_024` | `147 vs 147 lineas`, `0 diferencias` |
| `Pieza_027` | `146 vs 146 lineas`, `0 diferencias` |
| `Pieza_028` | `146 vs 146 lineas`, `0 diferencias` |
| `Pieza_029` | `146 vs 146 lineas`, `0 diferencias` |
| `Pieza_030` | `146 vs 146 lineas`, `0 diferencias` |
| `Pieza_096` | `100 vs 100 lineas`, `0 diferencias` |
| `Pieza_097` | `100 vs 100 lineas`, `0 diferencias` |

## Ampliacion A OpenPolyline Left/Right Con Lead

Para `OpenPolyline` con `SideOfFeature=Left/Right`, sin estrategia y con
acercamiento/alejamiento habilitados en modo `Down/Up`, Maestro conserva la
misma politica de compensacion:

- `Left` emite `G41`;
- `Right` emite `G42`;
- la trayectoria de corte vuelve a la geometria nominal;
- `Line/Down-Up` calcula entrada y salida sobre la tangente nominal con
  distancia `tool_radius * radius_multiplier`; la posicion rapida agrega
  `1.000` adicional sobre esa tangente;
- `Arc/Down-Up` calcula el centro del arco desplazando el punto nominal por la
  normal del lado de compensacion, con radio
  `tool_radius * radius_multiplier`; la posicion rapida agrega `1.000` sobre
  esa normal.

Validacion:

| Variante | Resultado |
| --- | --- |
| `Pieza_092` | `147 vs 147 lineas`, `0 diferencias` |
| `Pieza_093` | `147 vs 147 lineas`, `0 diferencias` |
| `Pieza_094` | `147 vs 147 lineas`, `0 diferencias` |
| `Pieza_095` | `147 vs 147 lineas`, `0 diferencias` |
