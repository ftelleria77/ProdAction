# Contrato CNC/ISO Observado

Estado: 2026-05-02.

Esta guia consolida el punto 1 de la investigacion ISO: que se sabe del
contrato real entre Maestro/postprocesador y la CNC. Es una base para un futuro
sintetizador `.iso`, no una especificacion completa del controlador.

## Fuentes verificadas

- PGMX de estudio: `S:\Maestro\Projects\ProdAction\ISO`
- ISO postprocesados: `P:\USBMIX\ProdAction\ISO`
- Configuracion Maestro copiada: `S:\Maestro\Cfgx`
- Toolset Maestro copiado: `S:\Maestro\Tlgx\def.tlgx`
- Configuracion Xilog Plus/CNC: `S:\Xilog Plus`
- Catalogo normalizado del repo: `tools/tool_catalog.csv`
- Plan de fixtures minimos: `docs/iso_minimal_fixtures_plan.md`

Comprobacion local:

- `101` archivos `.pgmx`.
- `101` archivos `.iso`.
- Todos los `.iso` tienen pareja `.pgmx` por nombre base.
- Los `.pgmx` son paquetes zip con XML interno legible.

## Entorno Maestro observado

`S:\Maestro\Cfgx\Programaciones.settingsx` es un zip con configuraciones .NET.
La configuracion `UI00.exe.Config` declara:

| Clave | Valor observado |
| --- | --- |
| `CurrentToolingFileName` | `def.tlgx` |
| `PostFileFormat` | `ISO` |
| `PostProcessorDir` | `C:\PrgMaestro\USBMIX` |
| `SecurityDistance` | `20` |
| `MillingRetractDistance` | `10` |
| `RapidFeed` | `50` |
| `IsMM` | `true` |
| `IsAreaScm` | `False` |
| `IsZetaScm` | `False` |
| `CurrentUICulture` | `es-ES` |

`S:\Maestro\Cfgx\Maestro.rel` contiene `1.00.006.1010`.

`S:\Maestro\Cfgx\Head.cfg` contiene un unico `Head` observado:

| Campo | Valor |
| --- | --- |
| `Number` | `3` |
| `SpindleNumber` | `1` |
| `HeadType` | `None` |
| `IsVector` | `false` |
| `DustpanRadius` | `0` |

`PostProcessorDir` es la carpeta local donde Maestro deja los `.iso` al
postprocesar. En el flujo de estudio, esos `.iso` luego se copian a
`P:\USBMIX\ProdAction\ISO`, que es la carpeta de red usada para que Codex pueda
analizarlos.

En esta maquina no existen las rutas locales declaradas por la configuracion:

- `C:\PrgMaestro`
- `C:\Archivos de programa\Scm Group\Maestro`
- `C:\Archivos de programa\Scm Group\Xilog Plus`

Por lo tanto, no se debe tratar la ausencia local de `C:\PrgMaestro\USBMIX`
como falta de los ISO de estudio: la copia analizable esta en
`P:\USBMIX\ProdAction\ISO`. La carpeta `S:\Xilog Plus` si contiene parte de la
configuracion que usa el postprocesado, incluyendo plantilla NCI y parametros de
ejes.

## Configuracion Xilog Plus/CNC

`S:\Xilog Plus` contiene configuracion adicional del entorno Xilog/CNC. Esta
capa es importante porque explica partes del ISO que no vienen del `.pgmx`.

Archivos relevantes observados:

| Ruta | Rol observado |
| --- | --- |
| `S:\Xilog Plus\Cfg\NCI.CFG` | Plantilla NCI usada para generar el preambulo/final ISO. |
| `S:\Xilog Plus\Cfg\Params.cfg` | Parametros de controlador/ejes. |
| `S:\Xilog Plus\Cfg\spindles.cfg` | Definicion historica de spindles/cabezales con offsets fisicos. |
| `S:\Xilog Plus\Cfg\fields.cfg` | Definicion de campos/areas de trabajo; contiene valores cercanos a los shifts Y observados. |
| `S:\Xilog Plus\Cfg\RELCNC.CFG` | Version de Xilog Plus. |
| `S:\Xilog Plus\Cfg\Nci.ini` | Opciones NCI32DLL, familia de maquina y CPU. |

Versiones/opciones observadas:

| Archivo | Dato | Valor |
| --- | --- | --- |
| `RELCNC.CFG` | `Xilog Plus` | `01.14.029.1006 (AUTHOR/TECH)` |
| `Nci.ini` | `NCI32DLL` | `version=b1` |
| `Nci.ini` | `MACHINEFAMILY` | `version=2` |
| `Nci.ini` | `TESTMODE` | `enable=1` |
| `Nci.ini` | `CPU` | `number=12` |
| `Nci.ini` | `CNCNAME` | vacio |

`Params.cfg` declara `CN_NUMAX = 11` y mapea los ejes principales asi:

| Eje logico | Indice | Nombre |
| --- | ---: | --- |
| X | `0` | `ASSE X` |
| Y | `1` | `ASSE Y` |
| Z | `2` | `ASSE Z` |
| C | `3` | `VECTOR` |
| B | `4` | `0-360` |
| A | `5` | `LIBERO` |
| M | `9` | `TOOLROOM` |

Parametros de ejes que ya explican movimientos ISO:

| Eje | `AP_MINQUOTA` | `AP_MAXQUOTA` | `AP_TARQUOTA` | `AP_PARKQTA` |
| --- | ---: | ---: | ---: | ---: |
| X | `-3702000` | `621000` | `335550` | `0` |
| Y | `-1870000` | `131000` | `119100` | `0` |
| Z | `-53000` | `201000` | `189150` | `201000` |

Reglas observadas desde estos archivos:

- `NCI.CFG` contiene literalmente el inicio ISO:
  - `?%%ETK[500]=100`
  - `_paras( 0x00, X, 3, %%ax[0].pa[21]/1000, %%ETK[500] )`
  - `G0 G53 Z %%ax[2].pa[22]/1000`
  - `M58 ;abilita controllo vuoto`
- Los ISO postprocesados conservan ese bloque con `%` simple.
- `Params.cfg` explica movimientos de parqueo:
  - `G0 G53 Z201.000` corresponde a `ASSE Z / AP_PARKQTA = 201000`.
  - `G0 G53 X-3700.000` corresponde a `ASSE X / AP_MINQUOTA = -3702000`.
- `NCI.CFG` tambien fija:
  - `$GEN_MAXTOOLRAD = 100`
  - `$GEN_MAXTOOLLEN = 160.1`
  - `$GEN_SPINTIME = 0.5`
  - `$GEN_UTMAXLEN = 155`
- `fields.cfg` contiene campos `E/F/G/H` con valores Y alrededor de `-1515`.
  Esos valores estan en la misma familia que `SHF[Y] = -1515.600` y
  `%Or[0].ofY=-1515599.976`, pero la regla exacta de seleccion/ajuste del
  campo todavia no esta cerrada.

Campos de mesa parseados desde `fields.cfg` con lectura de registro binario
simple. En este archivo la etiqueta queda al final del registro:

| Campo | Habilitado | X0 | Y0 | Z0 | XSize | YSize |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `A` | `1` | `-3685.85` | `0.00` | `0.00` | `1843.00` | `1555.00` |
| `B` | `1` | `-1843.00` | `0.00` | `0.00` | `1843.00` | `1555.00` |
| `C` | `1` | `-1843.00` | `0.00` | `0.00` | `1843.00` | `1555.00` |
| `D` | `1` | `0.00` | `0.00` | `0.00` | `1843.00` | `1555.00` |
| `E` | `1` | `-3688.00` | `-1515.25` | `0.00` | `1843.00` | `1555.00` |
| `F` | `1` | `-1843.00` | `-1515.75` | `0.00` | `1843.00` | `1555.00` |
| `G` | `1` | `-1843.00` | `-1515.75` | `0.00` | `1843.00` | `1555.00` |
| `H` | `1` | `0.00` | `-1515.00` | `0.00` | `1843.00` | `1555.00` |
| `I..P` | `0` | `0.00` | `0.00` | `0.00` | `0.00` | `0.00` |

`Axis.ini` confirma que hay parametros dedicados a dimension de area:

- `GRUPO = "DIM AREA"`
- `QUOTA MAX AREA AB (MM[0]-MM[3])`
- `QUOTA MAX AREA CD (MM[4]-MM[7])`

Observaciones del corpus ISO:

- `%Or[0].ofY` solo aparece con el valor `-1515599.976` en los ISO estudiados.
- Los shifts base mas frecuentes de Y son `SHF[Y] = -1515.600` y
  `SHF[Y] = -1510.600`.
- Tambien aparecen shifts de herramienta/operacion como `SHF[Y] = -246.650`,
  `126.950`, `-32.000`, `29.500`, `64.000` y otros valores ligados a offsets
  de cabezal o a operaciones especificas.
- Ademas de los parqueos generales, hay movimientos `G0 G53 Z149.500` y
  `G0 G53 Z149.450` en pocos ISO. Esos valores todavia no tienen formula
  cerrada.

`NCI_ORI.CFG` parece una plantilla alternativa/anterior. Mantiene familias de
claves similares (`$GEN_INIT`, `$GEN_END`, `$H03_VECTOR`, `$H04_VECTOR`,
`$GEN_MAXTOOLRAD`, `$GEN_MAXTOOLLEN`, `$GEN_SPINTIME`, `$GEN_UTMAXLEN`), pero
no coincide con el preambulo usado por los ISO actuales. La plantilla activa
para el corpus observado es `NCI.CFG`.

`S:\Xilog Plus\Fxc\fxdcyc.tab` enumera macros/ciclos Xilog como `B`, `BO`,
`G0`, `G1`, `G2`, `G3`, `ISO`, `F`, `C`, etc. Los archivos `Fxdcycdb.tab` y
varios `.pgm` contienen estructuras binarias/compiladas; se pueden usar para
buscar nombres y parametros, pero no alcanzan por si solos como fuente legible
de la logica de postprocesado.

`spindles.cfg` confirma por otra via los offsets ya vistos en `def.tlgx`:

- `58`: `X=-32.00`, `Y=21.75`, `Z=-66.50`
- `59`: `X=-32.00`, `Y=-29.50`, `Z=-66.50`
- `60`: `X=66.90`, `Y=32.00`, `Z=-66.45`
- `61`: `X=118.00`, `Y=32.00`, `Z=-66.30`
- `82`: `X=96.00`, `Y=-128.85`, `Z=-22.15`

## Herramientas del toolset

`S:\Maestro\Tlgx\def.tlgx` contiene las herramientas y el cabezal agregado
`BooringUnitHead`.

| ID | Nombre | Tipo | Holder | Diametro | Pilot | Sink | Offset | Feed std | RPM std |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `1888` | `001` | `FlatDrill` | `ERClamp` | `8` | `77` | `40` | `77` | `2` | `6000` |
| `1889` | `002` | `FlatDrill` | `ERClamp` | `15` | `77` | `20` | `77` | `1` | `4000` |
| `1890` | `003` | `FlatDrill` | `ERClamp` | `20` | `77` | `20` | `77` | `1` | `4000` |
| `1891` | `004` | `FlatDrill` | `ERClamp` | `35` | `77` | `20` | `77` | `1` | `4000` |
| `1892` | `005` | `FlatDrill` | `ERClamp` | `5` | `77` | `40` | `77` | `3` | `6000` |
| `1893` | `006` | `FlatDrill` | `ERClamp` | `4` | `77` | `40` | `77` | `3` | `6000` |
| `1894` | `007` | `ConicalDrill` | `ERClamp` | `5` | `77` | `40` | `77` | `3` | `6000` |
| `1895` | `058` | `FlatDrill` | `ERClamp` | `8` | `65` | `30` | `65` | `3` | `6000` |
| `1896` | `059` | `FlatDrill` | `ERClamp` | `8` | `65` | `30` | `65` | `3` | `6000` |
| `1897` | `060` | `FlatDrill` | `ERClamp` | `8` | `65` | `30` | `65` | `3` | `6000` |
| `1898` | `061` | `FlatDrill` | `ERClamp` | `8` | `65` | `30` | `65` | `3` | `6000` |
| `1899` | `082` | `UniversalBlade` | `ERClamp` | `120` | `0` | `10` | `60` | `5` | `4000` |
| `1900` | `E001` | `Endmill` | `HSK63` | `18.36` | `125.4` | `30` | `125.4` | `5` | `18000` |
| `1901` | `E002` | `Endmill` | `HSK63` | `100` | `107` | `30` | `107` | `3` | `6000` |
| `1902` | `E003` | `Endmill` | `HSK63` | `9.52` | `111.5` | `38` | `111.5` | `18` | `18000` |
| `1903` | `E004` | `Endmill` | `HSK63` | `4` | `107.2` | `22` | `107.2` | `5` | `18000` |
| `1904` | `E005` | `Endmill` | `HSK63` | `76` | `145.9` | `54` | `145.9` | `5` | `18000` |
| `1905` | `E006` | `Endmill` | `HSK63` | `80` | `120.87` | `36` | `120.87` | `2` | `18000` |
| `1906` | `E007` | `Endmill` | `HSK63` | `17.72` | `152.1` | `50` | `152.1` | `5` | `18000` |

## Cabezal de brocas y sierra

El agregado `BooringUnitHead` (`ID 1907`) contiene estos `SpindleComponent`.
Los valores `OX/OY/OZ` son los offsets fisicos declarados en `def.tlgx`.

| Id ISO/cabezal | Tool ID | Pilot | Radio | OX | OY | OZ | AX | AY | AZ |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `1` | `1888` | `77` | `4` | `0` | `0` | `0` | `0` | `0` | `0` |
| `2` | `1889` | `77` | `7.5` | `0` | `-32` | `0.2` | `0` | `0` | `0` |
| `3` | `1890` | `77` | `10` | `0` | `-64` | `0.25` | `0` | `0` | `0` |
| `4` | `1891` | `77` | `17.5` | `32` | `0` | `0.35` | `0` | `0` | `0` |
| `5` | `1892` | `77` | `2.5` | `64` | `0` | `0.95` | `0` | `0` | `0` |
| `6` | `1893` | `77` | `2` | `96` | `0` | `0.2` | `0` | `0` | `0` |
| `7` | `1894` | `77` | `2.5` | `128` | `0` | `0` | `0` | `0` | `0` |
| `58` | `1895` | `65` | `4` | `-32` | `21.75` | `-66.5` | `90` | `0` | `0` |
| `59` | `1896` | `65` | `4` | `-32` | `-29.5` | `-66.5` | `90` | `0` | `180` |
| `60` | `1897` | `65` | `4` | `66.9000015258789` | `32` | `-66.45` | `90` | `0` | `90` |
| `61` | `1898` | `65` | `4` | `118` | `32` | `-66.3` | `90` | `0` | `270` |
| `82` | `1899` | `60` | `1.9` | `96` | `-128.85000610351563` | `-22.15` | `0` | `0` | `0` |

Regla observada:

- En brocas verticales y laterales, `SHF[X/Y/Z]` del ISO coincide en general
  con el negativo de `OX/OY/OZ`.
- En la sierra `82`, `SHF[X] = -96` y `SHF[Z] = 22.15` siguen esa regla, pero
  `SHF[Y] = 126.950` parece aplicar ademas la correccion del radio `1.9`
  sobre `-OY = 128.850`.

## Variables ISO observadas

Estas reglas salen de los 101 ISO disponibles y de la memoria ISO historica.
Donde no hay significado completo, queda marcado como inferencia.

| Variable | Rol observado |
| --- | --- |
| `?%ETK[500]=100` | constante presente en todos los ISO estudiados. |
| `?%ETK[6]` | selecciona broca/cabezal/sierra para operaciones de agregado: `1..7`, `58..61`, `82`. En fresados con router queda observado como `1`. |
| `?%ETK[8]` | cara/plano de brocado lateral observado: `1=Top`, `2=Right`, `3=Left`, `4=Back`, `5=Front`. |
| `?%ETK[9]` | herramienta de router/magazine: `E001 -> 1`, `E003 -> 3`, `E004 -> 4`. |
| `?%ETK[0]` | mascara de herramienta/cabezal. Verticales: `001=1`, `002=2`, `003=4`, `004=8`, `005=16`, `006=32`, `007=64`. Laterales: `Front/Back=1073741824`, `Left/Right=2147483648`. |
| `?%ETK[7]` | modo de operacion inferido: `1` en ranura con sierra, `3` en taladrado, `4` en fresado/router. |
| `?%ETK[17]=257` | activacion/preparacion de cabezal agregado en taladros/ranuras; significado exacto pendiente. |
| `?%ETK[13]` y `?%ETK[18]` | pasan a `1` durante bloques de fresado/router y vuelven a `0`; significado exacto pendiente. |
| `SVL` / `VL6` | longitud/offset de herramienta usado por el controlador. Coincide con `ToolOffsetLength` en fresas y con `end_radius` en sierra vertical. |
| `SVR` / `VL7` | radio efectivo: `tool_width / 2` en fresas y sierra. |
| `SHF[X/Y/Z]` | shifts de marco/herramienta; mezcla offsets de pieza, maquina y herramienta. En agregado coincide con offsets fisicos del `BooringUnitHead`. |
| `MLV=0/1/2` | niveles o marcos de coordenadas del controlador. En el corpus aparecen los tres valores (`0`, `1`, `2`), pero el significado formal sigue pendiente. |
| `D0` / `D1` | corrector desactivado/activado. `D1` aparece durante corte con sierra/fresa. |

## Mapeo router observado en ISO

| PGMX ToolKey | ISO | Variables observadas |
| --- | --- | --- |
| `1900 / E001` | `T1`, `M06`, `S18000M3` | `?%ETK[9]=1`, `SVL=125.400`, `SVR=9.180`, `?%ETK[7]=4`, `D1` |
| `1902 / E003` | `T3`, `M06`, `S18000M3` | `?%ETK[9]=3`, `SVL=111.500`, `SVR=4.760`, `?%ETK[7]=4`, `D1` |
| `1903 / E004` | `T4`, `M06`, `S18000M3` | `?%ETK[9]=4`, `SVL=107.200`, `SVR=2.000`, `?%ETK[7]=4`, `D1` |

Herramientas del toolset aun no validadas en ISO de esta investigacion:

- `E002`
- `E005`
- `E006`
- `E007`

## Cabecera ISO

Regla ya validada en la memoria ISO:

- linea 1: `% nombre_programa.pgm`
- linea 2:
  `;H DX=... DY=... DZ=... BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0`
- `DX = length + origin_x`
- `DY = width + origin_y`
- `DZ = depth + origin_z`
- `BX/BY/BZ` quedaron en `0` en los casos estudiados.
- `-HG` corresponde al area de ejecucion usada por los PGMX de estudio.

## Huecos pendientes del contrato

Para reemplazar Maestro/postprocesador por un sintetizador ISO nativo todavia
falta cerrar:

1. Modelo exacto de CNC/controlador. `S:\Xilog Plus\Cfg\RELCNC.CFG` identifica
   Xilog Plus `01.14.029.1006 (AUTHOR/TECH)` y `Nci.ini` deja `CNCNAME` vacio.
   En los configs copiados no aparece el nombre comercial de la maquina. Para
   cerrar esto haria falta una foto/placa/manual de la maquina o una copia mas
   directa de la configuracion del control.
2. Regla completa de seleccion de campo/area `HG`. `fields.cfg` explica la
   familia de valores `-1515`, pero falta saber que campo se selecciona para
   cada pieza y que correccion produce exactamente `%Or[0].ofY=-1515599.976`,
   `SHF[Y]=-1515.600` y `SHF[Y]=-1510.600`.
3. Significado formal de `MLV`, `%Or`, `%ETK[13]`, `%ETK[17]`, `%ETK[18]`,
   `%ETK[114]` y `%EDK`. Se conocen patrones de uso, pero no la semantica de
   controlador que garantice que un ISO sintetico sea equivalente.
4. Logica completa del postprocesador mas alla de `NCI.CFG`. `NCI.CFG` cubre
   preambulo/final, parqueos y limites generales, pero no describe como Maestro
   transforma cada operacion PGMX en bloques ISO. Parte de esa logica parece
   estar en binarios/plantillas Xilog, o embebida en Maestro.
5. Formula de los movimientos `G0 G53 Z149.500` y `G0 G53 Z149.450`. Los
   parqueos `Z201.000` y `X-3700.000` ya estan explicados por `Params.cfg`; esos
   Z intermedios todavia no.
6. Validacion fisica o simulada de compensacion `G41/G42`, especialmente en
   esquinas donde el ISO delega la compensacion al CNC.
7. Validacion de herramientas `E002`, `E005`, `E006` y `E007` si van a entrar
   en el primer alcance del sintetizador.
