# Memoria De Parametros ISO Por Estado

Ultima actualizacion: 2026-05-08

## Alcance

Esta memoria registra solamente:

- instrucciones y parametros observados en ISO;
- valores que toman esos parametros;
- estados, trabajos, familias y transiciones donde aparecen;
- secuencias ISO observadas;
- significados confirmados, inferidos o pendientes.

No registrar aqui decisiones de implementacion, cambios de codigo, planes
generales ni resultados de validacion que no agreguen informacion sobre
parametros ISO.

## Convenciones

| Campo | Uso |
| --- | --- |
| `parametro` | Instruccion, registro o variable ISO observada. |
| `valores` | Valores distintos vistos en el corpus o en fixtures. |
| `capa_estado` | Agrupacion de estudio: `programa`, `pieza`, `marco`, `herramienta`, `salida`, `movimiento`, `reset`, `cierre`. |
| `contexto` | Familia, trabajo o transicion donde se observo. |
| `significado` | Lectura actual: confirmado, inferido o pendiente. |
| `secuencia` | Orden relativo observado en el ISO. |

Para compensacion:

- `G40` se registra como `compensacion_cnc=off`.
- `G41` se registra como `compensacion_cnc=left`.
- `G42` se registra como `compensacion_cnc=right`.
- La condicion geometrica `centrado` no se deduce de `G40` por si sola; debe
  registrarse aparte como base de trayectoria.

## Inventario De Parametros

| parametro | valores observados | capa_estado | significado actual |
| --- | --- | --- | --- |
| `% <programa>.pgm` | nombre de programa | programa | Identificador textual del ISO. |
| `;H DX` | `length + origin_x` | pieza | Dimension X de cabecera. |
| `;H DY` | `width + origin_y` | pieza | Dimension Y de cabecera. |
| `;H DZ` | `depth + origin_z` | pieza | Dimension Z de cabecera; tambien participa en parqueos laterales. |
| `;H BX/BY/BZ` | `0.000` | pieza | Base de pieza, constante observada. |
| `;H -HG` | `HG` | pieza | Campo o area de ejecucion usado en el corpus. |
| `?%ETK[500]` | `100` | salida | Constante de preambulo usada por `_paras`. |
| `_paras(...)` | `0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500]` | maquina | Parametrizacion inicial de eje desde plantilla NCI. |
| `%ax[2].pa[22]` | `Z201.000` efectivo | maquina | Park Z de maquina usado en `G0 G53 Z...`. |
| `%Or[0].ofX` | depende de `length/origin_x` | marco | Origen X de pieza escalado. |
| `%Or[0].ofY` | `-1515599.976` observado en HG | marco | Origen Y de campo; fuente causal pendiente. |
| `%Or[0].ofZ` | `DZ * 1000` | marco | Origen Z de pieza escalado. |
| `?%EDK[0].0` | `0` | salida | Registro de entorno/campo; significado pendiente. |
| `?%EDK[1].0` | `0` | salida | Registro de entorno/campo; significado pendiente. |
| `?%EDK[13].0` | `0`, `1` | salida | Registro de entorno/campo; se activa/desactiva en preambulo/cierre. |
| `MLV` | `0`, `1`, `2` | marco | Nivel o marco activo de coordenadas; significado formal pendiente. |
| `SHF[X]` | pieza, campo, router o spindle | marco/herramienta | Shift X activo. |
| `SHF[Y]` | pieza, campo, router o spindle | marco/herramienta | Shift Y activo. |
| `SHF[Z]` | pieza, router o spindle | marco/herramienta | Shift Z activo. |
| `?%ETK[8]` | `1`, `2`, `3`, `4`, `5` | salida | Cara/plano: `1=Top`, `2=Right`, `3=Left`, `4=Back`, `5=Front`. |
| `G17` | modal | movimiento | Plano de interpolacion XY. |
| `G40` | modal | movimiento | Compensacion CNC desactivada. |
| `G41` | modal | movimiento | Compensacion CNC izquierda. |
| `G42` | modal | movimiento | Compensacion CNC derecha. |
| `D` | `0`, `1` | herramienta | Corrector: `D0` desactivado, `D1` activo. |
| `T` | `1..7` | herramienta | Herramienta router/magazine. |
| `M06` | modal | herramienta | Cambio de herramienta. |
| `?%ETK[9]` | `1..7` | salida | Codigo de herramienta router: `E001->1`, `E004->4`, etc. |
| `?%ETK[6]` | `1..7`, `58..61`, `82` | salida | Seleccion de spindle/cabezal: verticales, laterales o sierra. |
| `?%ETK[0]` | `0`, `1`, `2`, `4`, `8`, `16`, `32`, `64`, `1073741824`, `2147483648` | salida | Mascara de herramienta/cabezal activo. |
| `?%ETK[1]` | `0`, `16` | salida | Registro asociado a sierra/SlotSide; significado pendiente. |
| `?%ETK[2]` | `0` | salida | Registro constante observado. |
| `?%ETK[7]` | `0`, `1`, `3`, `4` | salida/movimiento | Modo de operacion inferido: `0=reset`, `1=sierra`, `3=taladro`, `4=router`. |
| `?%ETK[13]` | `0`, `1` | salida | Activo durante bloques router; significado formal pendiente. |
| `?%ETK[17]` | `0`, `257` | salida | Activacion de cambio/preparacion de velocidad antes de `S...M3`. |
| `?%ETK[18]` | `0`, `1` | salida | Activacion router/fresado; significado formal pendiente. |
| `?%ETK[19]` | `0` | salida | Registro constante observado. |
| `S...M3` | `4000`, `6000`, `18000` | herramienta | Velocidad de spindle y arranque horario. |
| `SVL` | `0.000`, longitudes herramienta | herramienta | Longitud/offset izquierdo o principal. |
| `VL6` | `0`, `0.000`, longitudes herramienta | herramienta | Espejo/registro de `SVL`. |
| `SVR` | `0.000`, radios herramienta | herramienta | Radio efectivo. |
| `VL7` | `0`, `0.000`, radios herramienta | herramienta | Espejo/registro de `SVR`. |
| `G0` | movimientos rapidos | movimiento | Movimiento rapido en coordenadas activas o `G53`. |
| `G1` | movimientos lineales | movimiento | Corte, bajada o avance lineal. |
| `G2` | arcos horarios | movimiento | Interpolacion circular con `I/J`. |
| `G3` | arcos antihorarios | movimiento | Interpolacion circular con `I/J`. |
| `G9` | modal en traza | movimiento | Parada exacta observada en taladros. |
| `G53` | modal de coordenada maquina | movimiento | Movimiento en coordenadas maquina. |
| `X/Y/Z` | coordenadas | movimiento | Posiciones de trabajo o maquina segun marco activo. |
| `I/J` | coordenadas de arco | movimiento | Centro de arco en `G2/G3`. |
| `F` | avances | movimiento | Feed de bajada/corte; valores dependen de herramienta/operacion. |
| `G4F...` | `0.500`, `1.200` | reset | Pausa/dwell observada. |
| `G61` | modal | reset | Modo trayectoria/reset; significado formal pendiente. |
| `G64` | modal | cierre | Modo trayectoria/cierre; significado formal pendiente. |
| `M5` | modal | reset | Apaga spindle. |
| `M58` | modal | maquina | Control de vacio/sujecion desde preambulo NCI. |
| `SYN` | modal | herramienta/cierre | Sincronizacion observada en cambios y cierre. |
| `M2` | modal | cierre | Fin de programa. |

## Valores De Herramienta Observados

|    contexto   |  `T` | `?%ETK[9]` | `?%ETK[6]` | `SVL/VL6` | `SVR/VL7` | `S...M3` |
|       ---     | ---: |    ---:    |    ---:    |    ---:   |    ---:   |   ---:   |
| router `E001` |  `1` |     `1`    |     `1`    | `125.400` |  `9.180`  |  `18000` |
| router `E002` |  `2` |     `2`    |     `1`    | `107.000` | `50.000`  |   `6000` |
| router `E003` |  `3` |     `3`    |     `1`    | `111.500` |  `4.760`  |  `18000` |
| router `E004` |  `4` |     `4`    |     `1`    | `107.200` |  `2.000`  |  `18000` |
| router `E005` |  `5` |     `5`    |     `1`    | `145.900` | `38.000`  |  `18000` |
| router `E006` |  `6` |     `6`    |     `1`    | `120.870` | `40.000`  |  `18000` |
| router `E007` |  `7` |     `7`    |     `1`    | `152.100` |  `8.860`  |  `18000` |
| sierra vertical `082` | pendiente | pendiente | `82` | `107.000` o `60.000` observado | `1.900` | `4000` |

Nota: `E002` queda registrado como valor observado para conversion ISO de un
`.pgmx` existente que Maestro acepta. No habilita por si solo la generacion
automatica de trazas `.pgmx` con Sierra Horizontal sin reglas preventivas
propias.

## Valores Laterales Observados

|  cara   | `?%ETK[8]` | `?%ETK[6]` |    `?%ETK[0]`    |   `SHF[X]` |  `SHF[Y]` | `SHF[Z]` |
|   ---   |    ---:    |    ---:    |       ---:       |     ---:   |    ---:   |   ---:   |
|  `Top`  |     `1`    |   `1..7`   | mascara vertical |   variable |  variable | variable |
| `Right` |     `2`    |    `60`    |   `2147483648`   |  `-66.900` | `-32.000` | `66.450` |
| `Left`  |     `3`    |    `61`    |   `2147483648`   | `-118.000` | `-32.000` | `66.300` |
| `Back`  |     `4`    |    `59`    |   `1073741824`   |   `32.000` |  `29.500` | `66.500` |
| `Front` |     `5`    |    `58`    |   `1073741824`    |  `32.000` | `-21.750` | `66.500` |

Parqueo lateral observado:

`G53_Z_lateral = DZ_cabecera + 2*SecurityDistance + max(SHF_Z lateral involucrado)`

Con `SecurityDistance=20`. Ejemplos:

| `DZ_cabecera` | lateral involucrado | `G53 Z` observado |
|      ---:     |         ---         |        ---:       |
|    `43.000`   |     `Front/Back`    |     `149.500`     |
|    `43.000`   |        `Right`      |     `149.450`     |
|    `43.000`   |         `Left`      |     `149.300`     |
|    `50.000`   |     `Front/Back`    |     `156.500`     |
|    `50.000`   |        `Right`      |     `156.450`     |
|    `58.000`   |     `Front/Back`    |     `164.500`     |
|    `58.000`   |        `Right`      |     `164.450`     |

## Tabla De Estados Y Transiciones

Registrar aqui cada hallazgo nuevo como fila. Mantener solo datos ISO,
valores y secuencias observadas.

| id | corpus / pieza | contexto | estado_antes | parametro | valor_antes | valor_despues | secuencia observada | significado / pendiente |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `S001` | preambulo comun | inicio programa | vacio | `?%ETK[500]` | - | `100` | `?%ETK[500]=100`, `_paras(...)`, `G0 G53 Z %ax[2].pa[22]/1000`, `M58`, `G71` | preambulo maquina desde NCI |
| `S002` | HG observado | marco pieza inicial | preambulo | `%Or[0].ofX/Y/Z`, `?%EDK`, `MLV`, `SHF` | - | marco HG activo | `MLV=0`, `%Or[...]`, `?%EDK[0/1/13]`, `MLV=1`, `SHF[...]`, `?%ETK[8]=1`, `G40` | marco pieza/campo |
| `S003` | top drill | preparacion | marco HG | `?%ETK[6]`, `?%ETK[0]`, `SHF`, `S` | variable | herramienta vertical activa | `MLV=1`, `SHF[Z]=origin_z+%ETK[114]/1000`, `MLV=2`, `G17`, `?%ETK[6]=tool`, `SHF[...]`, `?%ETK[17]=257`, `S...M3`, `?%ETK[0]=mask` | preparar taladro superior |
| `S004` | top drill | traza | herramienta vertical activa | `?%ETK[7]` | `0` o sin modo | `3` | `G0 X... Y...`, `G0 Z...`, `?%ETK[7]=3`, `G1 G9 Z... F...`, `G0 Z...` | modo taladro |
| `S005` | top drill | reset | taladro ejecutado | `?%ETK[7]`, `?%ETK[0]`, `?%ETK[17]` | `3`, mascara, `257` | `0`, `0`, `0` | `MLV=1`, `SHF[Z]=DZ+%ETK[114]/1000`, `?%ETK[7]=0`, `G61`, `MLV=0`, `?%ETK[0]=0`, `?%ETK[17]=0`, `G4F1.200`, `M5`, `D0` | reset de taladro |
| `S006` | router | preparacion | marco HG o reset previo | `T`, `?%ETK[9]`, `?%ETK[18]`, `S`, `?%ETK[13]` | variable | router activo | `Tn`, `SYN`, `M06`, `?%ETK[6]=1`, `?%ETK[9]=n`, `?%ETK[18]=1`, `S18000M3`, `G17`, `MLV=2`, `?%ETK[13]=1` | preparar router |
| `S007` | router | traza | router activo | `D`, `SVL/VL6`, `SVR/VL7`, `?%ETK[7]`, `G40/G41/G42` | `D0`, offsets previos | `D1`, offsets herramienta, modo `4`, compensacion | `D1`, `SVL/VL6`, `SVR/VL7`, `?%ETK[7]=4`, `G40/G41/G42`, `G0/G1/G2/G3` | corte router |
| `S008` | router | reset | corte router | `D`, `SVL/VL6`, `SVR/VL7`, `?%ETK[7]`, `?%ETK[13]`, `?%ETK[18]` | activos | `0` | `D0`, `SVL 0.000`, `VL6=0.000`, `SVR 0.000`, `VL7=0.000`, `?%ETK[7]=0`, `G61`, `MLV=0`, `?%ETK[13]=0`, `?%ETK[18]=0`, `M5` | reset router |
| `S009` | side drill | preparacion lateral | top/router/lateral previo | `?%ETK[8]`, `?%ETK[6]`, `SHF`, `?%ETK[0]` | variable | lateral activo | `?%ETK[8]=cara`, `G40`, `MLV=1`, `SHF[Z]=origin_z+%ETK[114]/1000`, `MLV=2`, `G17`, `?%ETK[6]=58..61`, `MLV=0`, `G0 G53 Z...`, `MLV=2`, `SHF[...]`, `?%ETK[17]=257`, `S...M3`, `?%ETK[0]=mask` | preparar taladro lateral |
| `S010` | side drill | traza lateral | lateral activo | `?%ETK[7]` | `0` o sin modo | `3` | `G0 X... Y... Z...`, `?%ETK[7]=3`, `G1 G9 ... F...`, `G0 ...` | modo taladro lateral |
| `S011` | side drill -> side drill | cambio lateral | lateral activo | `G53 Z` | depende lateral saliente | calculado por laterales involucrados | `?%ETK[6]=nuevo`, `MLV=0`, `G0 G53 Z...`, `MLV=2`, `SHF[...]` | parqueo seguro lateral |
| `S012` | side drill -> top drill | vuelta a superior | lateral activo | `?%ETK[8]`, `G40`, `G53 Z` | cara lateral | `Top`, compensacion off, park lateral | `?%ETK[8]=1`, `G40`, `MLV=1`, `SHF[Z]=origin_z+%ETK[114]/1000`, `MLV=2`, `G17`, `?%ETK[6]=tool`, `MLV=0`, `G0 G53 Z...` | transicion lateral a superior |
| `S013` | slot milling | sierra vertical | marco/top previo | `?%ETK[6]`, `?%ETK[1]`, `?%ETK[7]`, `S` | variable | sierra activa | `?%ETK[6]=82`, `?%ETK[1]=16`, `S4000M3`, `?%ETK[7]=1` | ranura con sierra; detalle pendiente |
| `S014` | cierre comun | fin programa | ultimo trabajo | `G53`, `G64`, `SYN`, `M2` | variable | cerrado | `G0 G53 Z201.000`, `G0 G53 X...`, `G64`, `SYN`, resets, `M2` | cierre maquina |

## Significados Pendientes

| parametro | pendiente |
| --- | --- |
| `MLV` | Semantica formal de los niveles `0/1/2`. |
| `%Or[0]` | Fuente exacta de algunos valores de campo, especialmente `ofY`. |
| `?%EDK[0/1/13]` | Significado formal y relacion con campo/entorno. |
| `?%ETK[1]` | Confirmar rol exacto en sierra/SlotSide. |
| `?%ETK[2]` | Confirmar si siempre es constante `0`. |
| `?%ETK[13]` | Rol formal durante router/fresado. |
| `?%ETK[17]` | Confirmar si representa activacion de cambio de velocidad o preparacion de cabezal. |
| `?%ETK[18]` | Rol formal durante router/fresado. |
| `?%ETK[19]` | Confirmar si siempre es constante `0`. |
| `%ETK[114]` | Confirmar fuente/control de la correccion Z usada en `SHF[Z]=...+%ETK[114]/1000`. |
| `G61/G64` | Clasificar si pertenecen a reset por familia, trayectoria o cierre comun. |
| `SYN` | Clasificar sincronizacion: cambio de herramienta, reset o cierre. |
| `G4F...` | Diferenciar pausas por familia, repeticion de spindle o reset comun. |
| `G40` repetido | Determinar si es reset defensivo, requisito de cara/plano o plantilla fija. |
