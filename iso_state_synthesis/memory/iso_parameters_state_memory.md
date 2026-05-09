# Memoria De Parametros ISO Por Estado

Ultima actualizacion: 2026-05-09

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

## Arquitectura CNC Relevante

La maquina tiene dos cabezales principales que se mueven en conjunto, pero no
trabajan al mismo tiempo:

- Cabezal router: usa herramientas `E00x` y ejecuta todos los fresados.
- Cabezal de perforacion/ranurado: comparte motor entre brocas verticales
  `001..007`, sierra vertical `082` y brocas horizontales `058..061`.

Agrupacion funcional del cabezal de perforacion/ranurado:

| grupo | herramientas | uso | eje / sentido de trabajo |
| --- | --- | --- | --- |
| brocas verticales | `001..007` | Top drilling | perforacion en `-Z` |
| sierra vertical | `082` | Top Slot | corte en `-X` |
| brocas horizontales derecha | `060` | huecos cara derecha | perforacion en `-X` |
| brocas horizontales izquierda | `061` | huecos cara izquierda | perforacion en `+X` |
| brocas horizontales frontal | `058` | huecos cara frontal | perforacion en `+Y` |
| brocas horizontales trasera | `059` | huecos cara trasera | perforacion en `-Y` |

Consecuencia observada: las transiciones entre `001..007`, `058..061` y `082`
pueden compartir estado de motor/velocidad. Esto explica reseteos parciales y
que `?%ETK[17]=257` + `S...M3` se emitan solo cuando la velocidad activa del
cabezal compartido cambia.

En el cabezal router, una transicion `E00x -> E00x` se divide en dos casos:

- misma herramienta: transicion incremental; no hay `T`, `SYN`, `M06` ni parada
  completa del motor.
- cambio de herramienta: el CNC debe detener completamente el motor, ir al
  almacen de herramientas, ejecutar el cambio y luego repetir la preparacion de
  router para la herramienta entrante.

## Modelo De Bloques Y Transiciones

Esta seccion es el indice reutilizable de la memoria. La tabla `Sxxx` mantiene
las evidencias observadas; este catalogo clasifica esas evidencias en bloques
reusables y transiciones de estado.

Convencion de ids:

- `B-*`: bloque reutilizable.
- `T-RH-*`: transicion interna del cabezal router.
- `T-BH-*`: transicion interna del cabezal de perforacion/ranurado.
- `T-XH-*`: transicion entre cabezales fisicos.

### Bloques Reutilizables

| id | familia | cabezal | etapa | secuencia ISO base | estado resultante | evidencia |
| --- | --- | --- | --- | --- | --- | --- |
| `B-PG-001` | programa | maquina | preambulo | `?%ETK[500]=100`, `_paras(...)`, `G0 G53 Z...`, `M58`, `G71` | maquina inicializada | `S001` |
| `B-FR-001` | marco | ninguno | activar pieza/campo | `MLV=0`, `%Or[...]`, `?%EDK[...]`, `MLV=1`, `SHF[...]`, `?%ETK[8]=1`, `G40` | marco HG activo | `S002` |
| `B-RH-001` | router | router | preparacion | `Tn`, `SYN`, `M06`, `?%ETK[6]=1`, `?%ETK[9]=n`, `?%ETK[18]=1`, `S18000M3`, `G17`, `MLV=2`, `?%ETK[13]=1` | router preparado | `S006`, `S019` |
| `B-RH-002` | router | router | traza | `D1`, `SVL/VL6`, `SVR/VL7`, `?%ETK[7]=4`, `G40/G41/G42`, `G0/G1/G2/G3` | corte router ejecutado | `S007` |
| `B-RH-003` | router | router | reset | `D0`, offsets a `0`, `?%ETK[7]=0`, `G61`, `MLV=0`, `?%ETK[13]=0`, `?%ETK[18]=0`, `M5` | router detenido/reseteado | `S008`, `S019` |
| `B-BH-001` | top drill | perforacion/ranurado | preparacion | `MLV=1`, `SHF[Z]=origin_z+%ETK[114]/1000`, `MLV=2`, `G17`, `?%ETK[6]=001..007`, `SHF[...]`, velocidad si cambia, `?%ETK[0]=mask` | broca vertical preparada | `S003` |
| `B-BH-002` | top drill | perforacion/ranurado | traza | `G0 X/Y`, `G0 Z`, `?%ETK[7]=3`, `G1 G9 Z... F...`, `G0 Z...` | taladro superior ejecutado | `S004` |
| `B-BH-003` | top drill | perforacion/ranurado | reset completo | `MLV=1`, `SHF[Z]=DZ+%ETK[114]/1000`, `?%ETK[7]=0`, `G61`, `MLV=0`, `?%ETK[0]=0`, `?%ETK[17]=0`, `G4F1.200`, `M5`, `D0` | cabezal perforacion detenido/reseteado | `S005` |
| `B-BH-004` | side drill | perforacion/ranurado | preparacion | `?%ETK[8]=cara`, `G40`, `MLV=1`, `SHF[Z]=origin_z+%ETK[114]/1000`, `MLV=2`, `G17`, `?%ETK[6]=058..061`, parqueo `G53 Z`, `SHF[...]`, velocidad si cambia, `?%ETK[0]=mask` | broca lateral preparada | `S009` |
| `B-BH-005` | side drill | perforacion/ranurado | traza | `G0 X/Y/Z`, `?%ETK[7]=3`, `G1 G9 ... F...`, `G0 ...` | taladro lateral ejecutado | `S010` |
| `B-BH-006` | slot `082` | perforacion/ranurado | preparacion | `?%ETK[6]=82`, `?%ETK[1]=16`, `S4000M3` si cambia velocidad, `SHF[...]` | sierra vertical preparada | `S013`, `S017` |
| `B-BH-007` | slot `082` | perforacion/ranurado | traza | `?%ETK[7]=1`, movimientos de ranura | ranura con sierra ejecutada | `S013` |
| `B-PG-002` | programa | maquina | cierre | `G0 G53 Z201.000`, `G0 G53 X...`, `G64`, `SYN`, resets, `M2` | programa cerrado | `S014` |

### Transiciones Internas Y Entre Cabezales

| id | tipo | desde -> hacia | condicion | conserva | resetea / emite | evidencia |
| --- | --- | --- | --- | --- | --- | --- |
| `T-RH-001` | interna router incremental | router `E00x` -> router `E00x` | misma herramienta | herramienta montada, cabezal router preparado | no emite `T`, `SYN`, `M06`, `?%ETK[9]`, `?%ETK[18]` ni `M5`; reactiva `D1`, offsets y `?%ETK[7]=4` | `S015` |
| `T-RH-002` | interna router con cambio fisico | router `E00x` -> router `E00y` | herramienta saliente distinta de entrante | cabezal fisico router, no la herramienta ni el motor activo | reset router saliente, `M5`, viaje/cambio con `Tn`, `SYN`, `M06`, nueva preparacion router | `S019` |
| `T-BH-001` | interna perforacion/ranurado | side drill -> side drill | cambia broca lateral/cara o eje | cabezal compartido y motor si la velocidad no cambia | `?%ETK[6]=nuevo`, parqueo lateral `G53 Z`, `SHF[...]`; velocidad solo si cambia | `S011` |
| `T-BH-002` | interna perforacion/ranurado | side drill -> top drill | vuelve desde cara lateral a superior | cabezal compartido; velocidad si coincide | `?%ETK[8]=1`, `G40`, `SHF[Z]`, `G17`, `?%ETK[6]=tool`, parqueo `G53 Z` | `S012` |
| `T-BH-003` | interna perforacion/ranurado | top drill -> slot `082` | sierra usa el mismo motor; velocidad puede coincidir | velocidad activa si ya es `4000` | `?%ETK[0]=0`, `?%ETK[6]=82`, `?%ETK[1]=16`; no emite `?%ETK[17]=257` ni `S4000M3` si no cambia velocidad | `S017` |
| `T-BH-004` | interna perforacion/ranurado | slot `082` -> top drill | salida de sierra hacia broca vertical | cabezal compartido | reset parcial de slot: `D0`, offsets a `0`, `?%ETK[7]=0`, `?%ETK[1]=0`; luego preparacion top drill sin cierre final | `S018` |
| `T-XH-001` | entre cabezales | router -> perforacion/ranurado | siguiente trabajo usa `001..007`, `058..061` o `082` | movimiento conjunto de cabezales, no el motor/herramienta router | reset router saliente; preparar herramienta del cabezal de perforacion/ranurado entrante | pendiente de aislar como evidencia especifica |
| `T-XH-002` | entre cabezales | perforacion/ranurado -> router | siguiente trabajo usa `E00x` | movimiento conjunto de cabezales, no el motor compartido de perforacion | reset completo o parcial del cabezal de perforacion segun caso; preparar router con `T/SYN/M06` si corresponde | pendiente de aislar como evidencia especifica |

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
| `?%ETK[6]` | `1..7`, `58..61`, `82` | salida | Seleccion de herramienta del cabezal activo: brocas verticales/laterales o sierra; en router queda `1`. |
| `?%ETK[0]` | `0`, `1`, `2`, `4`, `8`, `16`, `32`, `64`, `1073741824`, `2147483648` | salida | Mascara de herramienta/cabezal activo. |
| `?%ETK[1]` | `0`, `16` | salida | Registro asociado a sierra/SlotSide; significado pendiente. |
| `?%ETK[2]` | `0` | salida | Registro constante observado. |
| `?%ETK[7]` | `0`, `1`, `3`, `4` | salida/movimiento | Modo de operacion inferido: `0=reset`, `1=sierra`, `3=taladro`, `4=router`. |
| `?%ETK[13]` | `0`, `1` | salida | Activo durante bloques router; significado formal pendiente. |
| `?%ETK[17]` | `0`, `257` | salida | Activacion de cambio/preparacion de velocidad antes de `S...M3`; no se repite si la velocidad activa no cambia. |
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
| sierra vertical `082` | no observado | no observado | `82` | `60.000` | `1.900` | `4000` |

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

## Bitacora De Estados Y Transiciones Observadas

Registrar aqui cada hallazgo nuevo como fila de evidencia. Mantener solo datos
ISO, valores y secuencias observadas. Para el modelo reutilizable, usar
`Modelo De Bloques Y Transiciones`.

| id | corpus / pieza | contexto | estado_antes | parametro | valor_antes | valor_despues | secuencia observada | significado / pendiente |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `S001` | preambulo comun | inicio programa | vacio | `?%ETK[500]` | - | `100` | `?%ETK[500]=100`, `_paras(...)`, `G0 G53 Z %ax[2].pa[22]/1000`, `M58`, `G71` | preambulo maquina desde NCI |
| `S002` | HG observado | marco pieza inicial | preambulo | `%Or[0].ofX/Y/Z`, `?%EDK`, `MLV`, `SHF` | - | marco HG activo | `MLV=0`, `%Or[...]`, `?%EDK[0/1/13]`, `MLV=1`, `SHF[...]`, `?%ETK[8]=1`, `G40` | marco pieza/campo |
| `S003` | top drill | preparacion | marco HG | `?%ETK[6]`, `?%ETK[0]`, `SHF`, `S` | variable | herramienta vertical activa | `MLV=1`, `SHF[Z]=origin_z+%ETK[114]/1000`, `MLV=2`, `G17`, `?%ETK[6]=tool`, `SHF[...]`, `?%ETK[17]=257` si cambia velocidad, `S...M3` si cambia velocidad, `?%ETK[0]=mask` | preparar taladro superior en cabezal compartido |
| `S004` | top drill | traza | herramienta vertical activa | `?%ETK[7]` | `0` o sin modo | `3` | `G0 X... Y...`, `G0 Z...`, `?%ETK[7]=3`, `G1 G9 Z... F...`, `G0 Z...` | modo taladro |
| `S005` | top drill | reset | taladro ejecutado | `?%ETK[7]`, `?%ETK[0]`, `?%ETK[17]` | `3`, mascara, `257` | `0`, `0`, `0` | `MLV=1`, `SHF[Z]=DZ+%ETK[114]/1000`, `?%ETK[7]=0`, `G61`, `MLV=0`, `?%ETK[0]=0`, `?%ETK[17]=0`, `G4F1.200`, `M5`, `D0` | reset de taladro |
| `S006` | router | preparacion | marco HG o reset previo | `T`, `?%ETK[9]`, `?%ETK[18]`, `S`, `?%ETK[13]` | variable | router activo | `Tn`, `SYN`, `M06`, `?%ETK[6]=1`, `?%ETK[9]=n`, `?%ETK[18]=1`, `S18000M3`, `G17`, `MLV=2`, `?%ETK[13]=1` | preparar router |
| `S007` | router | traza | router activo | `D`, `SVL/VL6`, `SVR/VL7`, `?%ETK[7]`, `G40/G41/G42` | `D0`, offsets previos | `D1`, offsets herramienta, modo `4`, compensacion | `D1`, `SVL/VL6`, `SVR/VL7`, `?%ETK[7]=4`, `G40/G41/G42`, `G0/G1/G2/G3` | corte router |
| `S008` | router | reset | corte router | `D`, `SVL/VL6`, `SVR/VL7`, `?%ETK[7]`, `?%ETK[13]`, `?%ETK[18]` | activos | `0` | `D0`, `SVL 0.000`, `VL6=0.000`, `SVR 0.000`, `VL7=0.000`, `?%ETK[7]=0`, `G61`, `MLV=0`, `?%ETK[13]=0`, `?%ETK[18]=0`, `M5` | reset router |
| `S009` | side drill | preparacion lateral | top/router/lateral previo | `?%ETK[8]`, `?%ETK[6]`, `SHF`, `?%ETK[0]` | variable | lateral activo | `?%ETK[8]=cara`, `G40`, `MLV=1`, `SHF[Z]=origin_z+%ETK[114]/1000`, `MLV=2`, `G17`, `?%ETK[6]=58..61`, `MLV=0`, `G0 G53 Z...`, `MLV=2`, `SHF[...]`, `?%ETK[17]=257` si cambia velocidad, `S...M3` si cambia velocidad, `?%ETK[0]=mask` | preparar taladro lateral en cabezal compartido |
| `S010` | side drill | traza lateral | lateral activo | `?%ETK[7]` | `0` o sin modo | `3` | `G0 X... Y... Z...`, `?%ETK[7]=3`, `G1 G9 ... F...`, `G0 ...` | modo taladro lateral |
| `S011` | side drill -> side drill | cambio lateral | lateral activo | `G53 Z` | depende lateral saliente | calculado por laterales involucrados | `?%ETK[6]=nuevo`, `MLV=0`, `G0 G53 Z...`, `MLV=2`, `SHF[...]` | parqueo seguro lateral |
| `S012` | side drill -> top drill | vuelta a superior | lateral activo | `?%ETK[8]`, `G40`, `G53 Z` | cara lateral | `Top`, compensacion off, park lateral | `?%ETK[8]=1`, `G40`, `MLV=1`, `SHF[Z]=origin_z+%ETK[114]/1000`, `MLV=2`, `G17`, `?%ETK[6]=tool`, `MLV=0`, `G0 G53 Z...` | transicion lateral a superior |
| `S013` | slot milling | sierra vertical | marco/top previo | `?%ETK[6]`, `?%ETK[1]`, `?%ETK[7]`, `S` | variable | sierra activa | `?%ETK[6]=82`, `?%ETK[1]=16`, `S4000M3` si cambia velocidad activa, `?%ETK[7]=1` | ranura con sierra en cabezal compartido; detalle de `?%ETK[1]` pendiente |
| `S014` | cierre comun | fin programa | ultimo trabajo | `G53`, `G64`, `SYN`, `M2` | variable | cerrado | `G0 G53 Z201.000`, `G0 G53 X...`, `G64`, `SYN`, resets, `M2` | cierre maquina |
| `S015` | Cocina / `Lado_derecho` | router -> router misma herramienta | router activo, `E001`, `D0`, offsets de corte reseteados | `G17`, `MLV`, `D`, `SVL/VL6`, `SVR/VL7`, `?%ETK[7]` | `G17/MLV=2` activos, `D0`, `SVL/VL6=0`, `SVR/VL7=0`, `?%ETK[7]=0` | mismo router activo para nueva traza | `?%ETK[7]=0`, `G17`, `MLV=2`, `G0 Xprev Yprev Zrapid`, `G0 Xrapid Yrapid Zrapid`, `G0 Xrapid Yrapid Zrapid`, `D1`, `SVL/VL6`, `SVR/VL7`, `?%ETK[7]=4`, `G41/G42`, traza | Transicion incremental: sin `MLV=0`, sin `G53 Z201`, sin `T`, sin `SYN`, sin `M06`, sin `?%ETK[9]`, sin `?%ETK[18]`, sin `M5`. |
| `S016` | Cocina / `Lado_derecho` | orden Top Drill en bloque no rectangular | top drill activo o bloque superior despues de router/slot | `G0 X/Y/Z`, `?%ETK[6]`, `?%ETK[0]`, `SHF` | punto anterior del bloque | siguiente punto segun recorrido por bandas | primera banda Y baja: `33,32` con `002`, luego `250.5,60 -> 450.5,60` con `005`; segunda banda Y alta: `450.5,532 -> 250.5,532` con `005`, cierre `33,553` con `002`; bloque posterior: `741,53 -> 773,53 -> 773,562 -> 741,562` | Maestro puede ordenar taladros superiores por bandas horizontales en serpentina, no solo por columnas. |
| `S017` | Cocina / `Lado_derecho` | top drill -> slot sierra `082` | taladro superior `002` activo a `4000` | `?%ETK[17]`, `S...M3`, `?%ETK[1]`, `?%ETK[6]` | `maquina.boring_head_speed=4000`, `?%ETK[1]=0`, `?%ETK[6]=2` | sierra `082` activa a `4000`, `?%ETK[1]=16` | `?%ETK[8]=1`, `G40`, `MLV=0`, `G0 G53 Z201.000`, `MLV=2`, `?%ETK[0]=0`, `?%ETK[6]=82`, `G17`, `?%ETK[1]=16`, `MLV=2`, `SHF[...]`, traza slot | No se emite `?%ETK[17]=257` ni `S4000M3` si la sierra mantiene la velocidad activa del cabezal perforador. |
| `S018` | Cocina / `Lado_derecho` | slot sierra `082` -> top drill | sierra activa, `?%ETK[1]=16`, offsets slot activos | `?%ETK[1]`, `?%ETK[8]`, `G40`, `G53 Z`, `SHF`, `?%ETK[6]`, `?%ETK[0]` | slot activo | top drill activo | `D0`, `SVL/VL6=0`, `SVR/VL7=0`, `?%ETK[7]=0`, `?%ETK[8]=1`, `G40`, `MLV=0`, `G0 G53 Z201.000`, `MLV=2`, `?%ETK[1]=0`, `MLV=1`, `SHF[Z]=origin_z+%ETK[114]/1000`, `MLV=2`, `G17`, `?%ETK[6]=tool`, `MLV=2`, `SHF[...]`, `?%ETK[0]=mask` | Reset parcial de slot y preparacion incremental de taladro superior, sin cierre final de programa. |
| `S019` | router | router -> router con cambio `E00x -> E00y` | router activo con herramienta saliente | `D`, `SVL/VL6`, `SVR/VL7`, `?%ETK[7]`, `?%ETK[13]`, `?%ETK[18]`, `T`, `?%ETK[9]` | herramienta router saliente activa | herramienta router entrante activa | reset router saliente con `D0`, offsets a `0`, `?%ETK[7]=0`, `G61`, `MLV=0`, `?%ETK[13]=0`, `?%ETK[18]=0`, `M5`; luego preparacion entrante con `Tn`, `SYN`, `M06`, `?%ETK[6]=1`, `?%ETK[9]=n`, `?%ETK[18]=1`, `S18000M3`, `G17`, `MLV=2`, `?%ETK[13]=1` | Transicion interna del cabezal router con cambio fisico de herramienta: requiere parada completa, viaje a almacen/cambio y nueva preparacion. |

## Significados Pendientes

| parametro | pendiente |
| --- | --- |
| `MLV` | Semantica formal de los niveles `0/1/2`. |
| `%Or[0]` | Fuente exacta de algunos valores de campo, especialmente `ofY`. |
| `?%EDK[0/1/13]` | Significado formal y relacion con campo/entorno. |
| `?%ETK[1]` | Confirmar rol exacto en sierra/SlotSide. |
| `?%ETK[2]` | Confirmar si siempre es constante `0`. |
| `?%ETK[13]` | Rol formal durante router/fresado. |
| `?%ETK[17]` | Confirmar significado formal en controlador; funcionalmente activa/prepara cambio de velocidad y no se repite si `maquina.boring_head_speed` no cambia. |
| `?%ETK[18]` | Rol formal durante router/fresado. |
| `?%ETK[19]` | Confirmar si siempre es constante `0`. |
| `%ETK[114]` | Confirmar fuente/control de la correccion Z usada en `SHF[Z]=...+%ETK[114]/1000`. |
| `G61/G64` | Clasificar si pertenecen a reset por familia, trayectoria o cierre comun. |
| `SYN` | Clasificar sincronizacion: cambio de herramienta, reset o cierre. |
| `G4F...` | Diferenciar pausas por familia, repeticion de spindle o reset comun. |
| `G40` repetido | Determinar si es reset defensivo, requisito de cara/plano o plantilla fija. |
