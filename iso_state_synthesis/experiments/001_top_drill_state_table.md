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
- `trabajo.depth_target = 10` pertenece al trabajo, aunque todavia falta
  explicar formalmente las cotas ISO `Z115` y `Z85`.
- `origin_y` participa en la cabecera y en un estado operativo `SHF[Y]`, pero
  no cambia la coordenada `Y` de la traza cuando el punto PGMX no cambia.

## Campos Dudosos O Pendientes

- Fuente exacta de `%Or[0].ofY`.
- Si las tres repeticiones `?%ETK[8]=1` + `G40` son estado obligatorio, reset
  defensivo o plantilla fija.
- Fuente exacta de `?%ETK[17]=257`.
- Relacion exacta entre profundidad PGMX `10`, pieza `depth=18`,
  `origin_z=25`, y movimientos `G0 Z115`, `G1 Z85`.
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
