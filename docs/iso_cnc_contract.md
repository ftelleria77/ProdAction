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
  En los programas `HG` observados, el marco toma como referencia el campo
  `H`: `Y0=-1515.600`.
- `%Or[0].ofY=-1515599.976` coincide con `-1515.600` almacenado como
  `float32` y multiplicado por `1000`; no requiere una correccion adicional
  desde `yzone.cfg`.

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
| `H` | `1` | `0.00` | `-1515.60` | `0.00` | `1843.00` | `1555.00` |
| `I..P` | `0` | `0.00` | `0.00` | `0.00` | `0.00` | `0.00` |

`Axis.ini` confirma que hay parametros dedicados a dimension de area:

- `GRUPO = "DIM AREA"`
- `QUOTA MAX AREA AB (MM[0]-MM[3])`
- `QUOTA MAX AREA CD (MM[4]-MM[7])`

Observaciones del corpus ISO:

- `%Or[0].ofY` solo aparece con el valor `-1515599.976` en los ISO estudiados;
  corresponde al `Y0` del campo `H` (`-1515.600`) con redondeo interno
  `float32`.
- Los shifts base mas frecuentes de Y son `SHF[Y] = -1515.600` y
  `SHF[Y] = -1510.600`.
- Tambien aparecen shifts de herramienta/operacion como `SHF[Y] = -246.650`,
  `126.950`, `-32.000`, `29.500`, `64.000` y otros valores ligados a offsets
  de cabezal o a operaciones especificas.
- Ademas de los parqueos generales, hay movimientos intermedios `G0 G53
  Z149.500` y `G0 G53 Z149.450` en `pieza_002`, `pieza_003` y `pieza_005`.
  En el corpus local completo aparecen solo al entrar a otro grupo de taladros
  laterales despues de haber usado una cara lateral previa.

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

### Parqueos laterales `Z149.*`

Barrido local del corpus `P:\USBMIX\ProdAction\ISO`:

- `124` archivos `.iso` revisados recursivamente despues de sumar la tanda
  `router_toolset_2026-05-03`.
- Solo `pieza_002.iso`, `pieza_003.iso` y `pieza_005.iso` contienen
  `G0 G53 Z149.*`.
- Los tres son piezas con taladros laterales D8 en varias caras.
- Los fixtures minimos con una sola cara lateral no emiten `Z149.*`; arrancan
  desde el parqueo inicial de `NCI.CFG` o usan `Z201.000`.

Valores observados:

| Corpus | `DZ` cabecera | `G53 Z` intermedio | `G53 Z - DZ` |
| --- | ---: | ---: | ---: |
| `pieza_002/003/005` | `43.000` | `149.500` | `106.500` |
| `pieza_002/003/005` | `43.000` | `149.450` | `106.450` |
| `side_g53_z_fixtures` grupo A | `50.000` | `156.500` | `106.500` |
| `side_g53_z_fixtures` grupo A | `50.000` | `156.450` | `106.450` |
| `side_g53_z_fixtures` grupo B | `58.000` | `164.500` | `106.500` |
| `side_g53_z_fixtures` grupo B | `58.000` | `164.450` | `106.450` |

El corpus Cocina agrega `149.300`, tambien con `DZ=43.000`, por lo que su delta
es `106.300`.

Comparacion contra `Offset Z` de Xilog Plus:

| Mandril | Lado Xilog | `Offset Z` | `SHF_Z` ISO | `DZ=43` -> `DZ+40+SHF_Z` |
| ---: | ---: | ---: | ---: | ---: |
| `58` | `4` | `-66.500` | `66.500` | `149.500` |
| `59` | `5` | `-66.500` | `66.500` | `149.500` |
| `60` | `2` | `-66.450` | `66.450` | `149.450` |
| `61` | `3` | `-66.300` | `66.300` | `149.300` |

Regla observada:

- El valor se emite despues de `MLV=0`, inmediatamente despues de seleccionar
  la broca lateral con `?%ETK[6]=...`, cuando hay una transicion entre grupos
  de herramienta/cara.
- El primer grupo lateral puro `Front / ETK[6]=58` no emite `Z149.*` si la
  pieza empieza directamente por esa cara. Si se llega a `Front` desde una
  herramienta superior/vertical, si puede aparecer el parqueo intermedio.
- Entre taladros de una misma cara lateral el postprocesador no cambia
  `ETK[6]`; puede usar `Z201.000` para `Front/Back` o reposicionar en plano
  lateral para `Left/Right`.
- La forma numerica observada es:
  `G53_Z_lateral = DZ_cabecera + 40.000 + max(SHF_Z_lateral_involucrado)`.
- `DZ_cabecera` es `depth + origin_z`, la misma cota emitida en la cabecera
  `;H` y en `%Or[0].ofZ`.
- El `40.000` coincide con `2 * SecurityDistance`: Maestro declara
  `SecurityDistance=20`, y los PGMX laterales revisados tienen
  `ApproachSecurityPlane=20` y `RetractSecurityPlane=20`. La lectura operativa
  actual es que el movimiento despeja las dos cotas de seguridad alrededor del
  panel.
- Los `SHF_Z` laterales salen de la configuracion de spindles:
  - `Front`/`Back`: `66.500`;
  - `Right`: `66.450`;
  - `Left`: `66.300`.
- Al entrar o salir de una broca lateral desde una herramienta vertical, la
  formula usa la cota lateral de la broca involucrada. Al cambiar de lateral a
  lateral, usa la mayor cota lateral entre cara activa y cara destino.
- La comparacion `destino solamente` no alcanza: en 74 movimientos
  intermedios revisados, 15 fallan si se usa solo el mandril destino, por
  ejemplo `59 -> 61` con `DZ=43` emite `149.500`, aunque el destino `61`
  daria `149.300`. En esos mismos 74 casos, usar la mayor cota Z de los
  laterales involucrados coincide siempre.
- El emitter ya lee esta holgura como `2 * SecurityDistance` desde
  `Maestro/Cfgx/Programaciones.settingsx`, no como literal propio.
- La ventana/configuracion `GENDATA` de Xilog Plus muestra varios `40.000`,
  pero las etiquetas internas los ubican como velocidades de referencia para
  arcos y avances de discontinuidad, no como cotas de despeje `Z`.

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
| `1901` | `E002` | `Sierra Horizontal` | `HSK63` | `100` | `107` | `30` | `107` | `3` | `6000` |
| `1902` | `E003` | `Endmill` | `HSK63` | `9.52` | `111.5` | `38` | `111.5` | `18` | `18000` |
| `1903` | `E004` | `Endmill` | `HSK63` | `4` | `107.2` | `22` | `107.2` | `5` | `18000` |
| `1904` | `E005` | `Fresa 45 grados` | `HSK63` | `76` | `145.9` | `54` | `145.9` | `5` | `18000` |
| `1905` | `E006` | `Fresa 0 grados / Rectificado` | `HSK63` | `80` | `120.87` | `36` | `120.87` | `2` | `18000` |
| `1906` | `E007` | `Fresa 90 grados / Recta` | `HSK63` | `17.72` | `152.1` | `50` | `152.1` | `5` | `18000` |

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

Estas reglas salen del corpus ISO disponible y de la memoria ISO historica.
Donde no hay significado completo, queda marcado como inferencia.

| Variable | Rol observado |
| --- | --- |
| `?%ETK[500]=100` | constante presente en todos los ISO estudiados. |
| `?%ETK[6]` | selecciona broca/cabezal/sierra para operaciones de agregado: `1..7`, `58..61`, `82`. En fresados con router queda observado como `1`. |
| `?%ETK[8]` | cara/plano de brocado lateral observado: `1=Top`, `2=Right`, `3=Left`, `4=Back`, `5=Front`. |
| `?%ETK[9]` | herramienta de router/magazine: `E001 -> 1`, `E003 -> 3`, `E004 -> 4`, `E005 -> 5`, `E006 -> 6`, `E007 -> 7`. |
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
| `1904 / E005` | `T5`, `M06`, `S18000M3` | `?%ETK[9]=5`, `SVL=145.900`, `SVR=38.000`, `?%ETK[7]=4`, `D1` |
| `1905 / E006` | `T6`, `M06`, `S18000M3` | `?%ETK[9]=6`, `SVL=120.870`, `SVR=40.000`, `?%ETK[7]=4`, `D1` |
| `1906 / E007` | `T7`, `M06`, `S18000M3` | `?%ETK[9]=7`, `SVL=152.100`, `SVR=8.860`, `?%ETK[7]=4`, `D1` |

Barrido local del corpus `P:\USBMIX\ProdAction\ISO` antes de generar la tanda
`router_toolset_2026-05-03`:

- valores `T` de router encontrados: `T1`, `T3`, `T4`;
- valores `?%ETK[9]` encontrados: `1`, `3`, `4`;
- no aparecen `T2`, `T5`, `T6`, `T7` ni `?%ETK[9]=2/5/6/7`;
- los valores `?%ETK[6]=2/5/6/7` pertenecen a brocas verticales
  `002/005/006/007`, no a las fresas `E002/E005/E006/E007`.

La tanda `router_toolset_2026-05-03` agrega validacion ISO de `E005`, `E006` y
`E007`:

- `SVL` coincide con `ToolOffsetLength`;
- `SVR` coincide con `tool_width / 2`;
- el punto de aproximacion/retracta lineal se separa una herramienta completa:
  `X_inicio - tool_width` y `X_fin + tool_width`;
- el primer tramo de entrada usa `F2000.000`;
- el corte usa el feed estandar de cada herramienta: `F5000.000` en
  `E005/E007`, `F2000.000` en `E006`.

Importante: esta tanda valida el mapeo ISO de herramienta, no autoriza todos
los usos operativos de esas herramientas.

## Politica operativa de herramientas E00x

| Herramienta | Uso operativo | Estado para sintesis automatica |
| --- | --- | --- |
| `E001` | Fresa recta principal para escuadrado y fresados ya estudiados. | Permitida segun reglas ya validadas. |
| `E002` | Sierra horizontal. No tiene filo para cortar la superficie de la cara superior, aunque su recorrido debe programarse como un fresado de cara superior. | Bloquear generacion automatica de trazas en `.pgmx` hasta modelar la familia de Sierra Horizontal y sus reglas seguras. |
| `E003` | Fresa recta chica ya estudiada en polilineas/circulos. | Permitida segun reglas ya validadas. |
| `E004` | Fresa recta chica ya estudiada en lineas, polilineas y PH. | Permitida segun reglas ya validadas y restricciones de `PH=5` documentadas. |
| `E005` | Fresa de 45 grados. Herramienta sensible, preferible para uso manual desde Maestro en fresados manuales o en division/escuadrado de piezas especiales. Puede usarse para dividir en juegos solo aplicando la regla operativa de separacion entre piezas y profundidad de fresado. | Permitir generacion automatica solo para division de `en_juego` aplicando la regla ya establecida. No promover a uso automatico general. |
| `E006` | Fresa de 0 grados / rectificado. Sirve para tratar extensiones superficiales sobre la cara superior, con fresados o vaciados de poca profundidad por pasada. | Bloquear generacion automatica de trazas en `.pgmx`. El fixture lineal pasante `router_toolset_2026-05-03` solo sirve para reconocer `T6/ETK[9]=6`, no como patron permitido. |
| `E007` | Fresa recta de 90 grados. Opera como `E001`, con mayor largo util para piezas de mayor espesor. | Permitida como equivalente funcional de `E001` cuando se necesita mayor largo util, respetando las mismas reglas de fresado/escuadrado ya validadas. |

### Separacion entre sintesis PGMX y traduccion ISO

La restriccion anterior aplica a la generacion automatica de trazas nuevas en
`.pgmx`. El futuro traductor `.pgmx -> .iso` tiene una frontera distinta:

- Si el sistema crea o modifica trazas PGMX, debe bloquear `E002` y `E006` y
  permitir `E005` solo para division de `en_juego` con la regla establecida.
- Si el sistema traduce un `.pgmx` existente, guardado por Maestro o por un
  usuario competente de Maestro, debe respetar la herramienta y la trayectoria
  indicadas en el archivo y emitir el `.iso` equivalente siempre que el contrato
  ISO de esa operacion este suficientemente generalizado.
- En ese modo de traduccion, el sistema puede advertir sobre herramientas
  sensibles, pero no debe rechazar automaticamente `E002`, `E005` o `E006` solo
  por la herramienta si la traza ya viene definida en el `.pgmx`.

Herramientas o familias aun pendientes para reglas seguras de generacion PGMX:

- `E002`
- `E006` en extensiones superficiales/vaciados
- `E005` fuera de division de `en_juego`

Nota sobre `E002`: el catalogo local la clasifica como `Sierra Horizontal`. La
sintesis publica actual no genera ese caso con `LineMillingSpec`; hace falta
modelar la familia correcta antes de pedir ISO.

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

## Reglas HG Confirmadas Por Fixtures Minimos

La tanda `minimal_fixtures_2026-05-03` agrego 14 `.pgmx` minimos y sus 14
`.iso` postprocesados por Maestro. Cada fixture cambio una sola variable para
separar geometria, dimensiones y origen.

Reglas confirmadas:

- Mover solo la geometria `X/Y` de una operacion cambia los movimientos
  operativos (`G0/G1 X... Y...`), pero no cambia `%Or`, `SHF`, `MLV` ni `ETK`.
- En `HG`, `%Or[0].ofY=-1515599.976` se mantuvo constante al mover geometria,
  al cambiar el ancho de panel y al cambiar `origin_y`.
- El `SHF[Y]` inicial de `MLV=1` se mantuvo en `-1515.600`.
- El `SHF[Y]` operativo de `MLV=1` sigue:
  `SHF[Y] = -1515.600 + origin_y`.
  Con `origin_y=5` dio `-1510.600`; con `origin_y=10` dio `-1505.600`.
- Cambiar el ancho de panel `width` de `100` a `200` cambio `DY` y la
  coordenada operativa, pero no `%Or[Y]` ni `SHF[Y]`.
- Cambiar el largo de panel `length` de `100` a `200` cambio el marco X:
  `DX=205.000`, `%Or[0].ofX=-205000.000`, `%Or[0].ofX` operativo
  `-210000.000` y `SHF[X]=-205.000`.
- Para los casos con `origin_x=5`, `%Or[0].ofX` inicial sigue
  `-(length + origin_x) * 1000`; el `%Or[0].ofX` operativo queda 5000 unidades
  mas negativo, consistente con sumar otra vez `origin_x`.
- En esta tanda no aparecieron parqueos intermedios `G0 G53 Z149.500` ni
  `G0 G53 Z149.450`; solo aparecieron el `Z` parametrico inicial, `Z201.000` y
  `X-3700.000`.

Mapeo lateral confirmado en fixtures D8:

| Cara | `ETK[8]` | `ETK[6]` | `ETK[0]` | `SHF[MLV=2]` |
| --- | ---: | ---: | ---: | --- |
| `Left` | `3` | `61` | `2147483648` | `(-118.000, -32.000, 66.300)` |
| `Right` | `2` | `60` | `2147483648` | `(-66.900, -32.000, 66.450)` |
| `Front` | `5` | `58` | `1073741824` | `(32.000, -21.750, 66.500)` |
| `Back` | `4` | `59` | `1073741824` | `(32.000, 29.500, 66.500)` |

Router E004 en pieza minima:

- `T4`, `M06`, `S18000M3`;
- `?%ETK[6]=1`, `?%ETK[9]=4`, `?%ETK[7]=4`;
- `SVL/VL6=107.200`;
- `SVR/VL7=2.000`;
- `SHF[MLV=2]=(32.050, -246.650, -125.300)`.

La variante `PH=5` sobre linea E004 centrada no usa `G41/G42`; genera pasadas
alternadas por niveles de profundidad. Como la linea estaba en
`SideOfFeature=Center`, esto no cierra todavia el cruce de compensacion
`Left/Right + PH=5`.

La segunda tanda `ph5_compensation_2026-05-03` cerro parte de ese cruce:

- `Left/Right + Line + Down/Up + PH=5` en polilinea abierta E004 postprocesa.
- En el bloque E004 no aparece `G41/G42`; Maestro emite coordenadas ya
  compensadas por lado.
- `Left` y `Right` cambian coordenadas y arcos de enlace del perfil compensado,
  no solo una bandera de corrector CNC.
- `Left/Right + Arc + Down/Up + PH=5` no postprocesa en Maestro para la
  polilinea abierta estudiada. El log falla en `MoveOnCompositeCurve` /
  `WritePointOnParameters` al crear un `GeomCartesianPoint`, con mensaje
  `El numero del valor utilizado no es valido`.
- Los `.pgmx` fallidos adaptan sin material `unsupported` y no contienen
  marcadores `NaN`/`Infinity`; por ahora el caso se clasifica como combinacion
  no valorable por Maestro/postprocesador, no como archivo corrupto.

La tanda diagnostica `arc_ph5_diagnostics_2026-05-03` acoto mejor la regla:

- La combinacion que falla es polilinea abierta de varios segmentos con
  estrategia `PH=5` y `Retract Arc + Up`.
- El fallo tambien ocurre con `SideOfFeature=Center`, por lo que no depende de
  `Left/Right`.
- El fallo tambien ocurre sin escuadrado E001 previo.
- Fijar `ArcSide=Left` o `ArcSide=Right` no evita el fallo.
- `Approach Arc + Down` no falla por si solo: la variante
  `Arc Down + Line Up + PH5` postprocesa.
- Una linea simple `Left/Right + Arc Down/Up + PH5` postprocesa.
- Una polilinea abierta con `Arc + Quote + PH5` postprocesa.

Regla practica: para ISO postprocesable con Maestro, evitar `Retract Arc + Up`
en polilineas abiertas de varios segmentos cuando se usa `PH=5`; usar
`Retract Line + Up` o `Arc + Quote`.

## Huecos pendientes del contrato

Para reemplazar Maestro/postprocesador por un sintetizador ISO nativo todavia
falta cerrar:

1. Modelo exacto de CNC/controlador. `S:\Xilog Plus\Cfg\RELCNC.CFG` identifica
   Xilog Plus `01.14.029.1006 (AUTHOR/TECH)` y `Nci.ini` deja `CNCNAME` vacio.
   En los configs copiados no aparece el nombre comercial de la maquina. Para
   cerrar esto haria falta una foto/placa/manual de la maquina o una copia mas
   directa de la configuracion del control.
2. Regla general de seleccion de campos/areas fuera del caso `HG`. Para `HG`
   observado, `fields.cfg` ya explica `SHF[Y]=-1515.600` desde el campo `H`,
   y `%Or[0].ofY=-1515599.976` sale del mismo valor tras redondeo `float32`.
   Falta validar otros valores de area (`A`, `EF`, combinaciones distintas) si
   aparecen en piezas reales.
3. Significado formal de `MLV`, `%Or`, `%ETK[13]`, `%ETK[17]`, `%ETK[18]`,
   `%ETK[114]` y `%EDK`. Se conocen patrones de uso, pero no la semantica de
   controlador que garantice que un ISO sintetico sea equivalente.
4. Logica completa del postprocesador mas alla de `NCI.CFG`. `NCI.CFG` cubre
   preambulo/final, parqueos y limites generales, pero no describe como Maestro
   transforma cada operacion PGMX en bloques ISO. Parte de esa logica parece
   estar en binarios/plantillas Xilog, o embebida en Maestro.
5. Validacion causal de la holgura lateral `40.000`. La mejor fuente legible
   encontrada es `2 * SecurityDistance` de Maestro (`20 + 20`), y el emitter ya
   la lee desde `Programaciones.settingsx`; falta una prueba cambiando
   `SecurityDistance` o las cotas de seguridad de operaciones laterales para
   confirmar que Maestro mueve los `G0 G53 Z...` en consecuencia.
6. Validacion fisica o simulada de compensacion `G41/G42`, especialmente en
   esquinas donde el ISO delega la compensacion al CNC.
7. Reglas seguras para herramientas especiales:
   - para generacion automatica de trazas PGMX, `E002` queda bloqueada hasta
     modelar Sierra Horizontal;
   - para generacion automatica de trazas PGMX, `E006` queda bloqueada hasta
     estudiar extensiones superficiales y vaciados de poca profundidad por
     pasada;
   - `E005` queda permitida automaticamente solo para division de `en_juego`
     aplicando la regla establecida de separacion y profundidad;
   - para traduccion de un `.pgmx` existente a `.iso`, no se debe bloquear por
     herramienta si el contrato ISO de la operacion puede generalizarse y la
     traza ya esta indicada en el `.pgmx`.
