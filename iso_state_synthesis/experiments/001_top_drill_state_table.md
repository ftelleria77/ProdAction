# Experimento 001 - Taladro Superior Minimo

Fecha: 2026-05-05

## Proposito

Probar si el enfoque `estado actual -> estado objetivo -> diferencial` ayuda a
separar datos de pieza, datos de trabajo y datos de maquina en un caso minimo
antes de escribir codigo nuevo.

## Evidencia

PGMX:

- `S:\Maestro\Projects\ProdAction\ISO\minimal_fixtures_2026-05-03\ISO_MIN_001_TopDrill_Base.pgmx`
- `S:\Maestro\Projects\ProdAction\ISO\minimal_fixtures_2026-05-03\ISO_MIN_002_TopDrill_Y60.pgmx`
- `S:\Maestro\Projects\ProdAction\ISO\minimal_fixtures_2026-05-03\ISO_MIN_006_TopDrill_OriginY10.pgmx`

ISO:

- `P:\USBMIX\ProdAction\ISO\minimal_fixtures_2026-05-03\iso_min_001_topdrill_base.iso`
- `P:\USBMIX\ProdAction\ISO\minimal_fixtures_2026-05-03\iso_min_002_topdrill_y60.iso`
- `P:\USBMIX\ProdAction\ISO\minimal_fixtures_2026-05-03\iso_min_006_topdrill_originy10.iso`

Lectura PGMX usada:

- `python -m tools.pgmx_snapshot <archivo.pgmx>`
- Desde 2026-05-06, esa lectura tambien expone el `def.tlgx` embebido como
  `tooling_entry_name`, `embedded_tools` y `embedded_spindles`.

## Datos PGMX Relevantes

| Pieza | Length | Width | Depth | Origin X | Origin Y | Origin Z | Punto | Herramienta | Profundidad | Campo |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| `ISO_MIN_001_TopDrill_Base` | 100 | 100 | 18 | 5 | 5 | 25 | `(50, 50, 0)` | `005` | 10 | `HG` |
| `ISO_MIN_002_TopDrill_Y60` | 100 | 100 | 18 | 5 | 5 | 25 | `(50, 60, 0)` | `005` | 10 | `HG` |
| `ISO_MIN_006_TopDrill_OriginY10` | 100 | 100 | 18 | 5 | 10 | 25 | `(50, 50, 0)` | `005` | 10 | `HG` |

## Diferencias Observadas

Base contra `Y60`:

| Cambio | Lectura |
| --- | --- |
| Nombre de programa | identidad de salida, no estado de mecanizado. |
| `G0 X50.000 Y50.000` -> `G0 X50.000 Y60.000` | cambia solo la traza del trabajo. |

Base contra `OriginY10`:

| Cambio | Lectura |
| --- | --- |
| Nombre de programa | identidad de salida, no estado de mecanizado. |
| `;H ... DY=105.000 ...` -> `;H ... DY=110.000 ...` | dato de pieza/cabecera: `width + origin_y`. |
| `SHF[Y]=-1510.600` -> `SHF[Y]=-1505.600` | estado operativo afectado por `origin_y`; sube 5 cuando `origin_y` sube 5. |

Dato importante: `%Or[0].ofY=-1515599.976` no cambia entre base y
`OriginY10`. Para este experimento queda clasificado como valor de
maquina/campo, no como derivado directo de `origin_y`.

Ampliacion revisada el 2026-05-06 con las seis variantes de taladro superior
del fixture minimo (`001` a `006`):

| Variante | Cambio PGMX | Cambios ISO observados |
| --- | --- | --- |
| `X60` | punto `(60, 50, 0)` | cambia solo `G0 X60.000 Y50.000`. |
| `Y60` | punto `(50, 60, 0)` | cambia solo `G0 X50.000 Y60.000`. |
| `DY200` | `width=200`, punto centrado `(50, 100, 0)` | `DY=205.000`; traza `G0 X50.000 Y100.000`; no cambia `%Or[0].ofY` ni `SHF[Y]`. |
| `DX200` | `length=200`, punto centrado `(100, 50, 0)` | `DX=205.000`; `%Or[0].ofX=-205000.000` en marco inicial; `SHF[X]=-205.000`; en preparacion de herramienta `%Or[0].ofX=-210000.000`; traza `G0 X100.000 Y50.000`. |
| `OriginY10` | `origin_y=10` | `DY=110.000`; `SHF[Y]` de preparacion sube de `-1510.600` a `-1505.600`; no cambia `%Or[0].ofY` ni la coordenada `Y` de traza. |

Lectura ampliada:

- En cabecera, `DX/DY/DZ = dimension + origin`.
- En el marco inicial `HG`, `%Or[0].ofX` y `SHF[X]` siguen `-(length + origin_x)`.
- En preparacion de herramienta superior, `%Or[0].ofX` sigue
  `-(length + 2 * origin_x)` para estas variantes.
- `%Or[0].ofY` queda constante en todas las variantes revisadas; no depende de
  `width`, `origin_y` ni `point_y` en este fixture.
- `SHF[Y]` del marco inicial queda constante en `-1515.600`; `SHF[Y]` de
  preparacion de herramienta queda como esa base mas `origin_y`.

## Cabecera ISO Contra PGMX

Cabecera observada en `iso_min_001_topdrill_base.iso`:

```iso
% iso_min_001_topdrill_base.pgm
;H DX=105.000 DY=105.000 DZ=43.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0
```

Datos encontrados en el XML interno `ISO_MIN_001_TopDrill_Base.xml`:

| Dato ISO | Valor ISO | Fuente PGMX | Valor PGMX | Regla inicial |
| --- | ---: | --- | ---: | --- |
| nombre programa | `iso_min_001_topdrill_base.pgm` | `Workpieces/WorkPiece/Name` y nombre de salida | `ISO_MIN_001_TopDrill_Base` | Relacionado con identidad de pieza/salida; falta definir normalizacion exacta. |
| `DX` | `105.000` | `Workpieces/WorkPiece/Length` o variable `dx1` + `Placement/_xP` | `100 + 5` | `length + origin_x`. |
| `DY` | `105.000` | `Workpieces/WorkPiece/Width` o variable `dy1` + `Placement/_yP` | `100 + 5` | `width + origin_y`. |
| `DZ` | `43.000` | `Workpieces/WorkPiece/Depth` o variable `dz1` + `Placement/_zP` | `18 + 25` | `depth + origin_z`. |
| `-HG` | `HG` | `MachiningParameters/ExecutionFields` | `HG` | Campo/area de ejecucion. |
| `BX/BY/BZ` | `0.000` | no identificado en este experimento | - | Constante observada por ahora. |
| `V/C/T` | `0/0/0` | no identificado en este experimento | - | Constante observada por ahora. |
| `*MM` | `MM` | no identificado en este experimento | - | Unidad observada por ahora. |

El snapshot resume estas fuentes como:

```text
state.piece_name = ISO_MIN_001_TopDrill_Base
state.length = 100
state.width = 100
state.depth = 18
state.origin_x = 5
state.origin_y = 5
state.origin_z = 25
state.execution_fields = HG
```

En el XML, las dimensiones tambien aparecen como variables parametrizadas:

```text
Variables/Variable[Name=dx1]/Value = 100
Variables/Variable[Name=dy1]/Value = 100
Variables/Variable[Name=dz1]/Value = 18
Workpieces/WorkPiece/LengthName = dx1
Workpieces/WorkPiece/WidthName = dy1
Workpieces/WorkPiece/DepthName = dz1
```

Por eso la lectura inicial debe preferir el valor resuelto que ya entrega el
snapshot, pero conservar la fuente: el `WorkPiece` apunta a nombres de
variables y esas variables contienen el valor usado.

Validacion con `ISO_MIN_006_TopDrill_OriginY10`:

| Campo | Base | OriginY10 | Efecto ISO |
| --- | ---: | ---: | --- |
| `Placement/_yP` | `5` | `10` | `DY=105.000` -> `DY=110.000`. |
| `WorkPiece/Width` | `100` | `100` | no cambia. |

Esto confirma para la cabecera que `DY` no sale solo del ancho de pieza: sale
de `width + origin_y`.

## Lineas 3-9 - Preambulo De Maquina

Preambulo observado en `iso_min_001_topdrill_base.iso`:

```iso
?%ETK[500]=100

_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )

G0 G53 Z %ax[2].pa[22]/1000
M58
G71
```

Resultado de busqueda en el `.pgmx`:

- El contenedor contiene `ISO_MIN_001_TopDrill_Base.epl`,
  `ISO_MIN_001_TopDrill_Base.xml` y `def.tlgx`.
- No aparecen las cadenas `ETK[500]`, `_paras`, `G0 G53 Z`, `M58`, `G71` ni
  `ax[2].pa[22]` dentro de esas entradas.
- `pgmx_snapshot` tampoco expone datos que expliquen estas lineas como datos de
  pieza o trabajo.

Fuente encontrada en configuracion de maquina:

- Fuente de investigacion del enfoque nuevo:
  `iso_state_synthesis/machine_config/snapshot/xilog_plus/Cfg/NCI.CFG`.
- Fuente original copiada: `S:\Xilog Plus\Cfg\NCI.CFG`.

| Linea ISO | Fuente encontrada | Lectura |
| --- | --- | --- |
| `?%ETK[500]=100` | `iso_state_synthesis/machine_config/snapshot/xilog_plus/Cfg/NCI.CFG`, bloque `$GEN_INIT` | Plantilla de inicio del postprocesador. |
| `_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )` | `NCI.CFG`, bloque `$GEN_INIT` | Plantilla de inicio; en config aparece con `%%` y en ISO sale como `%`. |
| linea vacia entre bloques | `NCI.CFG`, linea `;` | Comentario/separador de plantilla convertido en linea vacia. |
| `G0 G53 Z %ax[2].pa[22]/1000` | `NCI.CFG`, bloque `$GEN_INIT` | Parqueo inicial Z parametrico de maquina. |
| `M58` | `NCI.CFG`, bloque `$GEN_INIT` | En plantilla figura `M58 ;abilita controllo vuoto`; el ISO conserva solo `M58`. |
| `G71` | no encontrado literal en `.pgmx` ni en `NCI.CFG` | Probable salida fija del postprocesador por modo metrico; evidencia cercana: Maestro `IsMM=true` y Xilog `country.cfg` declara `MU MM`. |

Datos de soporte dentro de `machine_config`:

| Dato | Fuente | Lectura |
| --- | --- | --- |
| `ax[0].pa[21]` | `xilog_plus/Cfg/parax.str`: `AP_MINQUOTA ADR = pa21`; `xilog_plus/Cfg/Params.cfg`: `[ax0] AP_MINQUOTA = -3702000` | La plantilla referencia el minimo de X como parametro de eje. |
| `ax[0].pa[22]` comentado en `NCI.CFG` | `parax.str`: `AP_MAXQUOTA ADR = pa22`; `Params.cfg`: `[ax0] AP_MAXQUOTA = 621000` | La linea esta comentada en la plantilla activa (`solo per zone`), por eso no aparece como instruccion ISO. |
| `ax[2].pa[22]` | `parax.str`: `AP_MAXQUOTA ADR = pa22`; `Params.cfg`: `[ax2] AP_MAXQUOTA = 201000` | La plantilla referencia la cota maxima de Z, que coincide numericamente con `AP_PARKQTA = 201000` en este snapshot. |
| unidad Maestro | `maestro/Cfgx/Programaciones.settingsx` dentro de `UI00.exe.Config`: `IsMM=true`, `PostFileFormat=ISO` | Maestro esta configurado para postprocesar ISO en milimetros. |
| unidad Xilog | `xilog_plus/Cfg/country.cfg`: `MU MM`; `xilog_plus/Cfg/Params.cfg`: `CN_MMINCI = 0`; `xilog_plus/Cfg/cnfge.str`: `CN_MMINCI` con `FRM = UNIT, 0` | Evidencia de entorno metrico; todavia no demuestra causalmente la emision de `G71`. |

Conclusion provisional:

- Las lineas `3-8` no pertenecen al `.pgmx`; pertenecen al entorno
  maquina/postprocesador.
- `G71` tampoco aparece en el `.pgmx`. Por ahora se clasifica como linea fija
  de postprocesador asociada a unidad metrica, con fuente causal pendiente.
- Para el sintetizador nuevo, estas lineas deberian venir de una capa
  `maquina/postprocesador`, no de la capa `pieza` ni de la capa `trabajo`.

## Cotas Z Y Herramienta En Taladro Superior

Evidencia revisada el 2026-05-06 para `ISO_MIN_001_TopDrill_Base`.

El `pgmx_snapshot` expone la operacion de taladro con:

- `feature.depth_end = 10.0`.
- `operation.approach_security_plane = 20.0`.
- `operation.retract_security_plane = 20.0`.
- plano `Top` con `placement.z_p = 18.0`, igual a la profundidad de la pieza.
- herramienta `005`.
- `tooling_entry_name = def.tlgx`.
- herramienta embebida `005`: `ToolOffsetLength=77`, `PilotLength=77`,
  `Diameter=5`, `SpindleSpeed.Standard=6000`,
  `DescentSpeed.Standard=2`, `FeedRate.Standard=3`.
- spindle embebido `Id=5`: `RefToolKey.ID=1892`, `OX=64`, `OY=0`, `OZ=0.95`,
  `PilotLength=77`, `Radius=2.5`.

Toolpaths normalizados por Maestro dentro del PGMX:

| Toolpath | Puntos PGMX locales | Lectura |
| --- | --- | --- |
| `Approach` | `(50, 50, 38)` -> `(50, 50, 18)` | `depth + approach_security_plane = 18 + 20 = 38`. |
| `TrajectoryPath` | `(50, 50, 18)` -> `(50, 50, 8)` | `depth - feature.depth_end = 18 - 10 = 8`. |
| `Lift` | `(50, 50, 8)` -> `(50, 50, 38)` | regreso al plano de seguridad local. |

Fuente principal para los datos de herramienta del trabajo: el `def.tlgx`
embebido dentro del propio `.pgmx`. En este fixture, el contenedor
`ISO_MIN_001_TopDrill_Base.pgmx` trae `def.tlgx` junto con el XML de la pieza,
por lo que esa es la fuente preferida para explicar la herramienta efectivamente
usada por Maestro al postprocesar ese archivo.

Datos de herramienta `005` encontrados en el `def.tlgx` embebido:

| Dato herramienta | Valor |
| --- | ---: |
| `ToolOffsetLength` | 77 |
| `PilotLength` | 77 |
| `Diameter` | 5 |
| `SpindleSpeed.Standard` | 6000 |
| `DescentSpeed.Standard` | 2 |
| `FeedRate.Standard` | 3 |

Las copias de configuracion local se usan como respaldo y contraste:

- `iso_state_synthesis/machine_config/snapshot/maestro/Tlgx/def.tlgx` contiene
  la misma descripcion legible de herramientas.
- `iso_state_synthesis/machine_config/snapshot/xilog_plus/Job/def.tlg`
  confirma la tabla operativa de Xilog.

En `xilog_plus/Job/def.tlg`, el bloque numerico de la herramienta `005` muestra:

| Fuente | Dato | Valor |
| --- | --- | ---: |
| `Job/def.tlg` | herramienta/slot | `5` |
| `Job/def.tlg` | longitud de herramienta | `77.00` |
| `Job/def.tlg` | diametro | `5.00` |
| `Job/def.tlg` | longitud de hundimiento | `40.00` |
| `Job/def.tlg` | velocidad spindle | `6000.00` |

Lectura: para este enfoque, los datos de herramienta se leen primero desde el
`def.tlgx` embebido en el `.pgmx`. Las copias bajo `machine_config/snapshot`
sirven para validar que el dato coincide con la configuracion instalada y para
investigar valores que no esten en el paquete del trabajo.

Ademas, el `def.tlgx` embebido contiene el agregado `BooringUnitHead` con un
`SpindleComponent` de `Id=5` asociado a la herramienta `005`. Ese spindle tiene
`OriginPlacement/Translation`:

| Dato spindle | Valor |
| --- | ---: |
| `OX` | 64 |
| `OY` | 0 |
| `OZ` | 0.95 |

Reglas confirmadas para este caso:

- `SHF[X]=-64.000`, `SHF[Y]=0.000` y `SHF[Z]=-0.950` salen de la traslacion
  del spindle `005`, emitida con signo negativo.
- Las cotas ISO de taladro superior salen de `toolpath_z + ToolOffsetLength`.
- `G0 Z115.000` sale de `38 + 77`.
- `G1 G9 Z85.000` sale de `8 + 77`.
- La subida posterior vuelve a `G0 Z115.000` por el mismo plano local `38 + 77`.
- `S6000M3` sale de `SpindleSpeed.Standard = 6000`.
- `F2000.000` sale de `DescentSpeed.Standard = 2`, expresado como `2 * 1000`.

Esto corrige la lectura anterior: la profundidad PGMX no se traduce sola a
`Z85`; primero Maestro genera toolpaths locales relativos al plano, y despues
la salida ISO suma la longitud/offset de herramienta.

Pendientes asociados:

- `?%ETK[17]=257` tampoco aparece literal en el XML de pieza ni en `def.tlgx`;
  en `spindles.cfg` y en `xilog_plus/Job/def.tlg` existe un registro `257`, y
  la linea se repite en taladros superiores y laterales con herramienta `005`,
  pero queda como hipotesis de estado de cabezal/spindle Xilog.
- `NCI.CFG` y `NCI_ORI.CFG` solo documentan el reset comun
  `?%ETK[17]=0` dentro de `$GEN_END`; no documentan el significado de cargar
  `257` durante la preparacion.

## Tabla Manual De Estados

| Etapa | Estado recibido | Estado objetivo | Diferencial emitido | Fuente principal | Estado posterior |
| --- | --- | --- | --- | --- | --- |
| `program_header` | vacio | identificar programa y dimensiones CNC de pieza | `% nombre.pgm`; `;H DX=... DY=... DZ=... -HG ...` | PGMX `state` + identidad de salida | cabecera escrita; sin herramienta activa |
| `machine_preamble` | cabecera escrita | maquina en preambulo ISO esperado | `?%ETK[500]=100`; `_paras(...)`; `G0 G53 Z...`; `M58`; `G71` | observado en ISO; fuente de maquina pendiente de clasificar | preambulo activo |
| `piece_frame_hg` | preambulo activo | marco de pieza/campo listo | `MLV=0`; `%Or[...]`; `?%EDK[...]`; `MLV=1`; `SHF[...]`; `?%ETK[8]=1`; `G40` repetido | PGMX `state.execution_fields`, dimensiones y valores observados de campo/maquina | marco inicial de pieza listo |
| `top_drill_prepare` | marco inicial listo | herramienta `005` y plano superior listos para taladrar | `SHF[Z]=25...`; `MLV=2`; `G17`; `?%ETK[6]=5`; `%Or[0].ofX=-110000`; `SHF[Y]=...`; `SHF` de herramienta; `?%ETK[17]=257`; `S6000M3`; `?%ETK[0]=16` | PGMX feature/operation/tool + valores observados de herramienta/maquina | herramienta activa y offsets de trabajo listos |
| `top_drill_trace` | herramienta activa | ejecutar punto y profundidad | `G0 X... Y...`; `G0 Z115.000`; `?%ETK[7]=3`; `G1 G9 Z85.000 F2000.000`; `G0 Z115.000` | punto PGMX, profundidad PGMX y reglas Z/feed pendientes de clasificar | taladro ejecutado; herramienta sigue activa |
| `top_drill_reset` | taladro ejecutado | salir del modo taladro y apagar preparacion de herramienta | `MLV=1`; `SHF[Z]=43...`; `?%ETK[7]=0`; `G61`; `MLV=0`; `?%ETK[0]=0`; `?%ETK[17]=0`; `G4F1.200`; `M5`; `D0` | reset observado despues de taladro superior | modo taladro apagado |
| `program_close` | modo taladro apagado | parqueo y limpieza final | `G0 G53 Z201.000`; `G0 G53 X-3700.000`; `G64`; `SYN`; resets `ETK/EDK/SHF/VL`; `M2` | paso `Xn` del PGMX + valores de maquina observados | programa cerrado |

## Campos Confirmados Por Esta Triangulacion

- `pieza.length`, `pieza.width`, `pieza.depth`, `pieza.origin_x`,
  `pieza.origin_y`, `pieza.origin_z` deben entrar al estado de pieza.
- `trabajo.geometry.point` pertenece a la traza: cambiar `Y` del punto cambia
  solo el movimiento `G0 X... Y...` en este par.
- `trabajo.tool = 005` pertenece al estado de herramienta/trabajo, no a la
  cabecera.
- `trabajo.depth_target = 10` pertenece al trabajo; para taladro superior se
  refleja primero en los toolpaths locales del PGMX y luego en ISO como
  `toolpath_z + ToolOffsetLength`.
- `herramienta.ToolOffsetLength = 77`, `SpindleSpeed.Standard = 6000` y
  `DescentSpeed.Standard = 2` son necesarios para explicar `Z115/Z85`,
  `S6000M3` y `F2000.000`.
- `herramienta.spindle_translation = (64, 0, 0.95)` para el spindle `005`
  explica los `SHF` de herramienta `(-64, 0, -0.950)` en taladro superior.
- `origin_y` participa en la cabecera y en un estado operativo `SHF[Y]`, pero
  no cambia la coordenada `Y` de la traza cuando el punto PGMX no cambia.

## Campos Dudosos O Pendientes

- Fuente exacta de `%Or[0].ofY`.
- Si las tres repeticiones `?%ETK[8]=1` + `G40` son estado obligatorio, reset
  defensivo o plantilla fija.
- Sentido formal de `?%ETK[17]=257`; por ahora queda como hipotesis observada
  de preparacion de cabezal/spindle, con reset confirmado por `NCI.CFG`.
- Generalizar si `toolpath_z + ToolOffsetLength` se mantiene para otras
  herramientas, caras y familias.
- Si `G61`, `G64`, `SYN` pertenecen a resets por familia o al cierre comun.
- Como registrar lineas obligatorias que se repiten aunque no haya diferencial
  numerico.

## Decision Provisional

La primera implementacion no deberia empezar por un emisor especifico de
taladro superior. Deberia empezar por algo mas neutral:

- lector de evidencia PGMX/ISO;
- modelo de `StateLayer`;
- modelo de `Stage`;
- tabla de `StateTransition`;
- explicacion por linea emitida.

La familia `Top Drill` solo debe ser el primer caso de prueba, no el nombre de
la arquitectura.

## Validacion Del Primer Emisor Explicativo

El 2026-05-06 se agrego un emisor candidato acotado en
`iso_state_synthesis/emitter.py`, alimentado por `StageDifferential`.

Comando de comparacion:

```powershell
py -3 -m iso_state_synthesis compare-candidate <archivo.pgmx> <maestro.iso>
```

Resultado contra las seis variantes del fixture minimo:

| Variante | Resultado |
| --- | --- |
| `ISO_MIN_001_TopDrill_Base` | `84 vs 84 lineas`, `0 diferencias` |
| `ISO_MIN_002_TopDrill_Y60` | `84 vs 84 lineas`, `0 diferencias` |
| `ISO_MIN_003_TopDrill_X60` | `84 vs 84 lineas`, `0 diferencias` |
| `ISO_MIN_004_TopDrill_DY200` | `84 vs 84 lineas`, `0 diferencias` |
| `ISO_MIN_005_TopDrill_DX200` | `84 vs 84 lineas`, `0 diferencias` |
| `ISO_MIN_006_TopDrill_OriginY10` | `84 vs 84 lineas`, `0 diferencias` |

Lectura: el primer emisor explicativo ya reproduce el bloque completo Top Drill
para las variantes controladas. Sigue siendo un emisor acotado a esta familia y
todavia no prueba otras caras ni otras operaciones.

## Clasificacion En El Emisor

El 2026-05-06 se agrego clasificacion explicita por linea en
`ExplainedIsoLine.rule_status`. El objetivo es que el emisor no mezcle en una
misma categoria lo que ya generalizo en las seis variantes con lo que todavia
es constante observada o hipotesis.

Estados usados inicialmente:

| `rule_status` | Lectura |
| --- | --- |
| `generalized_top_drill_001_006` | Regla que sobrevivio a las variantes `001` a `006`: cabecera `DX/DY/DZ`, offsets derivados de dimensiones/origen, herramienta `005`, `S6000M3`, `SHF` de spindle y traza `XY/Z/F`. |
| `identity_normalization_pending` | Nombre de programa normalizado; falta definir la regla exacta de identidad/salida. |
| `machine_config_template` | Linea tomada de plantilla/configuracion de maquina, por ahora `NCI.CFG`. |
| `field_constant_pending_source` | Constante de campo observada, como `%Or[0].ofY` o `SHF[Y]`, que no cambio con las variantes pero todavia necesita fuente causal. |
| `field_modal_pending_source` | Valor modal/de campo observado en el marco inicial, todavia sin fuente causal. |
| `modal_frame_observed` | Cambio de marco observado (`MLV`) que se conserva separado de los valores derivados. |
| `top_drill_modal_observed` | Comando modal observado durante preparacion de Top Drill. |
| `top_drill_reset_observed` | Reset observado despues de Top Drill. |
| `machine_close_observed` | Linea de cierre comun observada. |
| `machine_metric_hypothesis` | `G71`; asociado al entorno metrico, sin fuente literal todavia. |
| `boring_head_speed_change` | `?%ETK[17]=257` y `S...M3`; activacion de cambio de velocidad del `BooringUnitHead` calculada por diferencial. |
| `repeated_modal_reset_hypothesis` | Repeticiones `?%ETK[8]=1` y `G40`; falta decidir si son estado obligatorio, reset defensivo o plantilla fija. |
| `modal_trace_hypothesis` | Comandos modales de traza como `?%ETK[7]=3` y `MLV=2` que aun no tienen fuente causal aislada. |
| `top_drill_modal_hypothesis` | Registro modal observado en preparacion Top Drill, como `?%ETK[0]=16`, sin significado formal aislado. |
| `modal_reset_hypothesis` | `G61`; falta clasificar si depende de la familia de taladro o de una plantilla comun. |
| `machine_close_hypothesis` | `G64` y `SYN`; cierre observado con causalidad pendiente. |

Esta clasificacion no cambia el texto ISO emitido. Solo agrega metadata para
inspeccion con `emit-candidate --json`.

Validacion posterior con las rutas de fabrica disponibles:

```powershell
py -3 -m iso_state_synthesis compare-candidate <TopDrill_001_a_006.pgmx> <Maestro.iso>
```

Resultado: las seis variantes siguen comparando `84 vs 84 lineas`,
`0 diferencias`.
