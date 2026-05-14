# Memoria De Parametros ISO Por Estado

Ultima actualizacion: 2026-05-11

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
| `B-BH-002` | top drill | perforacion/ranurado | traza | `G0 X/Y`, `G0 Z`, `?%ETK[7]=3`, `G1 G9 Z... F...`, `G0 Z...` | taladro superior ejecutado | `S004`, `S042` |
| `B-BH-003` | top drill | perforacion/ranurado | reset completo | `MLV=1`, `SHF[Z]=DZ+%ETK[114]/1000`, `?%ETK[7]=0`, `G61`, `MLV=0`, `?%ETK[0]=0`, `?%ETK[17]=0`, `G4F1.200`, `M5`, `D0` | cabezal perforacion detenido/reseteado | `S005`, `S040` |
| `B-BH-004` | side drill | perforacion/ranurado | preparacion | `?%ETK[8]=cara`, `G40`, `MLV=1`, `SHF[Z]=origin_z+%ETK[114]/1000`, `MLV=2`, `G17`, `?%ETK[6]=058..061`, parqueo `G53 Z`, `SHF[...]`, velocidad si cambia, `?%ETK[0]=mask` | broca lateral preparada | `S009` |
| `B-BH-005` | side drill | perforacion/ranurado | traza | `G0 X/Y/Z`, `?%ETK[7]=3`, `G1 G9 ... F...`, `G0 ...` | taladro lateral ejecutado | `S010`, `S041` |
| `B-BH-006` | top slot | perforacion/ranurado | preparacion | `?%ETK[6]=82`, `?%ETK[1]=16`, `S4000M3` si cambia velocidad, `SHF[...]` | sierra vertical preparada | `S013`, `S017` |
| `B-BH-007` | top slot | perforacion/ranurado | traza | `?%ETK[7]=1`, movimientos de ranura | ranura con sierra ejecutada | `S013` |
| `B-BH-008` | top drill | perforacion/ranurado | reset parcial | `MLV=1`, `SHF[Z]=DZ+%ETK[114]/1000`, `?%ETK[7]=0` | taladro superior queda limpio para transicion interna | `S021`, `S022`, `S040` |
| `B-BH-009` | side drill | perforacion/ranurado | reset completo | `MLV=1`, `SHF[Z]=DZ+%ETK[114]/1000`, `?%ETK[7]=0`, `G61`, `MLV=0`, `?%ETK[0]=0`, `?%ETK[17]=0`, `G4F1.200`, `M5`, `D0` | taladro lateral detenido/reseteado | `S010`, `S040` |
| `B-BH-010` | side drill | perforacion/ranurado | reset parcial | `MLV=1`, `SHF[Z]=DZ+%ETK[114]/1000`, `?%ETK[7]=0` | taladro lateral queda limpio para transicion interna | `S023`, `S024`, `S040` |
| `B-BH-011` | top slot | perforacion/ranurado | reset completo | `D0`, `SVL/VL6=0`, `SVR/VL7=0`, `?%ETK[7]=0`, `G61`, `MLV=0`, `?%ETK[1]=0`, `?%ETK[17]=0`, `G4F1.200`, `M5`, `D0` | sierra vertical detenida/reseteada | `S013`, `S040` |
| `B-BH-012` | top slot | perforacion/ranurado | reset parcial | `D0`, `SVL/VL6=0`, `SVR/VL7=0`, `?%ETK[7]=0` segun contexto | sierra vertical queda limpia para transicion interna | `S018`, `S026`, `S040` |
| `B-PG-002` | programa | maquina | cierre | `G0 G53 Z201.000`, `G0 G53 X...`, `G64`, `SYN`, resets, `M2` | programa cerrado | `S014` |

### Transiciones Internas Y Entre Cabezales

| id | tipo | desde -> hacia | condicion | conserva | resetea / emite | evidencia |
| --- | --- | --- | --- | --- | --- | --- |
| `T-RH-001` | internal router incremental | router -> router | misma herramienta | herramienta montada, cabezal router preparado | no emite `T`, `SYN`, `M06`, `?%ETK[9]`, `?%ETK[18]` ni `M5`; reactiva `D1`, offsets y `?%ETK[7]=4` | `S015` |
| `T-RH-002` | internal router physical change | router -> router | diferente herramienta | cabezal fisico router, no la herramienta ni el motor activo | reset router saliente, `M5`, viaje/cambio con `Tn`, `SYN`, `M06`, nueva preparacion router | `S019` |
| `T-BH-001` | internal boring head | top drill -> top drill | cambia o conserva broca vertical en cara superior | cabezal compartido; motor y herramienta si no cambian | reset corto saliente; si cambia herramienta: `?%ETK[6]=nuevo`, `SHF[...]`, velocidad solo si cambia y `?%ETK[0]=mask`; si no cambia herramienta: reposicion incremental sin repetir herramienta/velocidad/mascara | `S020`, `S021` |
| `T-BH-002` | internal boring head | top drill -> side drill | cambia de broca vertical a broca horizontal | cabezal compartido | reset corto de top; seleccion lateral, parqueo `G53 Z`, `SHF[...]`; velocidad solo si cambia | `S022` |
| `T-BH-003` | internal boring head | side drill -> side drill | cambia de broca horizontal, lateral, cara o eje | cabezal compartido y motor si la velocidad no cambia | `?%ETK[6]=nuevo`, parqueo lateral `G53 Z`, `SHF[...]`; velocidad solo si cambia; en transiciones aisladas de dos laterales Back/Left ajustan la cota fija espejo | `S011`, `S023` |
| `T-BH-004` | internal boring head | side drill -> top drill | cambia de broca horizontal a broca vertical | cabezal compartido; velocidad si coincide | pausa lateral inicial, reset corto lateral, `?%ETK[8]=1`, `G40`, `SHF[Z]`, `G17`, `?%ETK[6]=tool`, parqueo `G53 Z`; velocidad solo si cambia | `S012`, `S024` |
| `T-BH-005` | internal boring head | top drill -> top slot | cambia de broca vertical a sierra vertical | velocidad activa si ya es `4000` | `?%ETK[0]=0`, `?%ETK[6]=82`, `?%ETK[1]=16`; no emite `?%ETK[17]=257` ni `S4000M3` si no cambia velocidad | `S017` |
| `T-BH-006` | internal boring head | top slot -> top drill | cambia de sierra vertical a broca vertical | cabezal compartido | reset parcial de slot: `D0`, offsets a `0`, `?%ETK[7]=0`, `?%ETK[1]=0`; luego preparacion top drill sin cierre final | `S018` |
| `T-BH-007` | internal boring head | side drill -> top slot | cambia de broca horizontal a sierra vertical | cabezal compartido | reset lateral parcial, retorno a Top, `?%ETK[0]=0`, preparacion sierra con cambio `6000 -> 4000`; `Back/Left` restauran marco lateral derecho antes de Top | `S025` |
| `T-BH-008` | internal boring head | top slot -> side drill | cambia de sierra vertical a broca horizontal | cabezal compartido | reset parcial de sierra, seleccion lateral, `?%ETK[1]=0`, preparacion lateral con cambio `4000 -> 6000`; si entra a una secuencia lateral multiple, pausa `G4F0.500` antes de la primera traza | `S026`, `S041` |
| `T-XH-001` | switching heads | router -> boring head | cambia de fresa a broca o sierra | movimiento conjunto de cabezales, no el motor/herramienta router | reset router saliente; preparar herramienta del cabezal de perforacion/ranurado entrante; la seleccion `?%ETK[8]=1/G40` depende del perfil router saliente y de su salida geometrica | `S027`, `S031` |
| `T-XH-002` | switching heads | boring head -> router | cambia de broca o sierra a fresa | movimiento conjunto de cabezales, no el motor compartido de perforacion | limpieza segun familia saliente y preparacion router incremental sin recomponer marco completo; al entrar a `OpenPolyline` aplica reglas de reset, herramienta router y compensacion segun `S029/S030`; puede heredar seleccion Top desde el perfil router previo segun `S031` | `S028`, `S029`, `S030`, `S031` |

### Evidencia Controlada Cerrada

| transicion | fixtures | manifiesto | generador | resultado |
| --- | --- | --- | --- | --- |
| `T-BH-002` | `Pieza_098..102` | `S:\Maestro\Projects\ProdAction\ISO\Pieza_098_102_TBH002_manifest.csv` | `tools/studies/iso/tbh002_top_to_side_fixtures_2026_05_10.py` | `5/5` exactos contra `pieza_098..102.iso`; evidencia `S022` |
| `T-BH-001` misma herramienta | `Pieza_119..122` | `S:\Maestro\Projects\ProdAction\ISO\Pieza_119_122_TBH001_same_tool_manifest.csv` | `tools/studies/iso/tbh001_same_tool_fixtures_2026_05_10.py` | `4/4` exactos contra `pieza_119..122.iso`; evidencia `S021` |
| `T-BH-003` | `Pieza_103..118` | `S:\Maestro\Projects\ProdAction\ISO\Pieza_103_118_TBH003_manifest.csv` | `tools/studies/iso/tbh003_side_to_side_fixtures_2026_05_10.py` | `16/16` exactos contra `pieza_103..118.iso`; evidencia `S023` |
| `T-BH-004` | `Pieza_123..150` | `S:\Maestro\Projects\ProdAction\ISO\Pieza_123_150_TBH004_manifest.csv` | `tools/studies/iso/tbh004_side_to_top_fixtures_2026_05_11.py` | `28/28` exactos contra `pieza_123..150.iso`; evidencia `S024` |
| `T-BH-007` | `Pieza_151..154` | `S:\Maestro\Projects\ProdAction\ISO\Pieza_151_158_TBH007_008_manifest.csv` | `tools/studies/iso/tbh007_008_side_slot_fixtures_2026_05_11.py` | `4/4` exactos contra `pieza_151..154.iso`; evidencia `S025` |
| `T-BH-008` | `Pieza_155..158` | `S:\Maestro\Projects\ProdAction\ISO\Pieza_151_158_TBH007_008_manifest.csv` | `tools/studies/iso/tbh007_008_side_slot_fixtures_2026_05_11.py` | `4/4` exactos contra `pieza_155..158.iso`; evidencia `S026` |
| `T-XH-001` | `Pieza_159..161` | `S:\Maestro\Projects\ProdAction\ISO\Pieza_159_164_TXH001_002_manifest.csv` | `tools/studies/iso/txh001_002_router_boring_fixtures_2026_05_11.py` | `3/3` exactos contra `pieza_159..161.iso`; evidencia `S027` |
| `T-XH-002` | `Pieza_162..164` | `S:\Maestro\Projects\ProdAction\ISO\Pieza_159_164_TXH001_002_manifest.csv` | `tools/studies/iso/txh001_002_router_boring_fixtures_2026_05_11.py` | `3/3` exactos contra `pieza_162..164.iso`; evidencia `S028` |
| `T-XH-002` OpenPolyline | `Pieza_192..208` | `S:\Maestro\Projects\ProdAction\ISO\Pieza_192_198_TXH_open_profile_reentry_manifest.csv`; `S:\Maestro\Projects\ProdAction\ISO\Pieza_199_205_TXH_open_profile_center_reentry_manifest.csv`; `S:\Maestro\Projects\ProdAction\ISO\Pieza_206_208_TXH_top_open_profile_direct_manifest.csv` | `tools/studies/iso/txh_open_profile_reentry_fixtures_2026_05_11.py`; `tools/studies/iso/txh_open_profile_center_reentry_fixtures_2026_05_11.py`; `tools/studies/iso/txh_top_open_profile_direct_fixtures_2026_05_11.py` | `17/17` exactos contra `pieza_192..208.iso`; evidencia `S029/S030` |

Validacion de regresion posterior a `S031`: la serie controlada
`Pieza_192..208` queda `17/17` exacta. El corpus raiz `Pieza*.pgmx` con ISO
Maestro disponible queda `210/215` exacto; los cinco residuales son
`Pieza_181..185`, con diferencias geometricas de 1 mm en perfil previas a esta
regla. El corpus `Cocina` queda `65/84` exactos; los residuales ya no son la
firma masiva `?%ETK[8]/G40`, sino diferencias de ordenamiento, herramienta,
traza o laterales.

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
| `S020` | `Pieza_001` / `Pieza_001_R` | top drill -> top drill con cambio de broca vertical | taladro superior activo tras reset corto intermedio | `?%ETK[6]`, `?%ETK[17]`, `S...M3`, `SHF`, `?%ETK[0]` | broca vertical anterior y velocidad activa previa | broca vertical nueva; velocidad conservada o cambiada | secuencia incremental: `MLV=1`, `SHF[Z]=origin_z+%ETK[114]/1000`, `MLV=2`, `G17`, `?%ETK[6]=nuevo`, `G0 Xprev Yprev Zrapid`, `MLV=2`, `SHF[...]`, `?%ETK[17]=257` y `S...M3` solo si cambia velocidad, `?%ETK[0]=mask`; verificado contra `S:\Maestro\Projects\ProdAction\ISO\Pieza_001*.pgmx` y `P:\USBMIX\ProdAction\ISO\pieza_001*.iso`: `Pieza_001` confirma `001,002,003,004,005,006,007` con activacion solo en `001`, `002` y `005`; `Pieza_001_R` confirma `001,002,005,003,006,004,007` con activacion en cada alternancia de velocidad; `compare-candidate` exacto: `202/202` y `210/210` lineas | Evidencia especifica de `T-BH-001`: cambio interno de broca vertical dentro del mismo cabezal, sin cierre completo ni `M5` entre trabajos. |
| `S021` | `Pieza_119..122` | top drill -> top drill sin cambio de broca vertical | taladro superior activo tras reset corto intermedio | `?%ETK[6]`, `?%ETK[17]`, `S...M3`, `SHF`, `?%ETK[0]`, `G0` | misma broca vertical y velocidad activa | mismo cabezal, misma herramienta | tras `MLV=1`, `SHF[Z]=DZ+%ETK[114]/1000`, `?%ETK[7]=0`, Maestro reposiciona sin repetir `?%ETK[6]`, `SHF[...]`, `?%ETK[17]`, `S...M3` ni `?%ETK[0]`; verificado con `Pieza_119..122`: `4/4` exactos | Cierra subcaso de `T-BH-001` con misma herramienta: continuidad incremental sin cambio fisico ni reactivacion de velocidad. |
| `S022` | `Pieza_098..102` | top drill -> side drill | taladro superior activo tras reset corto intermedio | `?%ETK[8]`, `G40`, `SHF[Z]`, `?%ETK[6]`, `G53 Z`, `SHF`, `?%ETK[17]`, `S...M3`, `?%ETK[0]` | broca vertical activa | broca horizontal lateral activa | Maestro conserva el cabezal compartido: despues del top drill emite solo `MLV=1`, `SHF[Z]=DZ+%ETK[114]/1000`, `?%ETK[7]=0`; no emite `G61`, `?%ETK[0]=0`, `?%ETK[17]=0`, `G4F1.200`, `M5` ni `D0` antes del lateral; luego prepara cara lateral y velocidad solo si cambia; `Pieza_098..102`: `5/5` exactos | Evidencia especifica de `T-BH-002`: transicion interna vertical a horizontal con reset parcial. |
| `S023` | `Pieza_103..118` | side drill -> side drill aislado | lateral activo tras reset corto intermedio | `?%ETK[8]`, `G40`, `SHF[X/Y/Z]`, `?%ETK[6]`, `G53 Z`, `?%ETK[0]`, cota fija lateral | broca horizontal/cara anterior | broca horizontal/cara siguiente | matriz dirigida completa `Front/Right/Back/Left -> Front/Right/Back/Left`: `16/16` exactos; en cambios de cara, el marco lateral se restaura segun cara saliente/entrante; en transiciones aisladas hacia o desde `Back/Left`, la cota fija usa el espejo `span - abs(toolpath_fixed)` con el signo de la cara; bloques laterales largos mantienen la regla previa | Evidencia especifica de `T-BH-003`: cambio interno horizontal-horizontal entre caras, conservando cabezal y velocidad si coincide. |
| `S024` | `Pieza_123..150` | side drill -> top drill | lateral activo tras reset corto intermedio | `G4F0.500`, `?%ETK[8]`, `G40`, `SHF[Z]`, `?%ETK[6]`, `G53 Z`, `SHF`, `?%ETK[17]`, `S...M3`, `?%ETK[0]` | broca horizontal lateral activa | broca vertical superior activa | Maestro emite `G4F0.500` antes de la traza lateral inicial cuando el siguiente trabajo es top drill; luego reset lateral corto `MLV=1`, `SHF[Z]=DZ+%ETK[114]/1000`, `?%ETK[7]=0` y prepara Top con `?%ETK[8]=1`, `G40`, `?%ETK[6]=001..007`, parqueo lateral `G53 Z`, offsets verticales y velocidad solo si cambia; `Pieza_123..150`: `28/28` exactos | Cierra matriz `T-BH-004` de horizontal a vertical para cuatro caras laterales por siete brocas superiores. |
| `S025` | `Pieza_151..154` | side drill -> top slot | lateral activo tras reset corto intermedio | `G4F0.500`, `?%ETK[8]=1`, `G40`, `G53 Z201`, `?%ETK[0]=0`, `?%ETK[6]=82`, `?%ETK[1]=16` | broca horizontal lateral a `6000` | sierra vertical `082` a `4000` | `4/4` exactos; Maestro conserva cabezal compartido, emite pausa lateral antes de la traza si hay trabajo posterior, usa reset lateral parcial y retorna a Top sin `G61/M5`; para `Back/Left` restaura el marco lateral derecho antes de `?%ETK[8]=1` | Evidencia especifica de `T-BH-007`: horizontal a sierra vertical con retorno parcial a Top. |
| `S026` | `Pieza_155..158` | top slot -> side drill | sierra vertical activa tras reset de traza | `?%ETK[8]`, `G40`, `G53 Z201`, `?%ETK[1]=0`, `?%ETK[6]=58..61`, `?%ETK[17]=257`, `S6000M3` | sierra vertical `082` a `4000` | broca horizontal lateral a `6000` | `4/4` exactos; la sierra hace reset parcial de offsets y `?%ETK[7]`, luego selecciona cara lateral, limpia `?%ETK[1]` y prepara la broca lateral sin cierre completo del cabezal | Evidencia especifica de `T-BH-008`: sierra vertical a horizontal lateral conservando cabezal compartido. |
| `S027` | `Pieza_159..161` | router -> boring head | router E004 activo tras reset de traza | `?%ETK[8]`, `G40`, `G61/G64`, `?%ETK[13]`, `?%ETK[18]`, preparacion BH | router `E004` | top drill, side drill o top slot | `3/3` exactos; `line_milling -> top_drill` aislado no repite `?%ETK[8]=1/G40` ni `?%ETK[6]=1`; `line_milling -> side_drill` mantiene la regla previa de seleccion lateral; `line_milling -> slot_milling` usa reset router con seleccion Top y `MLV=2` antes del cambio de velocidad a `4000` | Evidencia especifica de `T-XH-001`: cambio de cabezal router a perforacion/ranurado. |
| `S028` | `Pieza_162..164` | boring head -> router | top drill, side drill o slot activo | `?%ETK[17]`, `M5`, `?%ETK[0]`/`?%ETK[1]`, `T4`, `SYN`, `M06`, `G61/G64`, `?%ETK[9]`, `?%ETK[18]`, `?%ETK[13]` | cabezal de perforacion/ranurado activo | router `E004` activo | `3/3` exactos; Maestro limpia el estado saliente segun familia, hace cambio fisico a router y prepara `E004` incrementalmente sin recomponer `%Or`/marco completo; en `slot -> router`, `?%ETK[7]=0` se emite antes del lift final de la ranura | Evidencia especifica de `T-XH-002`: cambio de cabezal de perforacion/ranurado a router. |
| `S029` | `Pieza_192..208` | top drill -> router OpenPolyline | taladro superior activo tras reset corto o cierre de cadena superior | `?%ETK[7]`, `?%ETK[6]`, `?%ETK[9]`, `?%ETK[17]`, `M5`, `?%ETK[0]` | cabezal de perforacion activo; router anterior opcional | router `E001` preparado | si el router entrante es `OpenPolyline`, Maestro duplica `?%ETK[7]=0` antes de `?%ETK[17]=0/M5` cuando `SideOfFeature` es `Left/Right` o cuando `Center` tiene approach/retract activo; no duplica en `Center` sin approach/retract; `?%ETK[6]=1` se emite si la broca superior saliente no es `001`; `?%ETK[9]=n` se omite si el router anterior ya habia seleccionado la misma herramienta | Cierra subcasos de `T-XH-002` para retorno desde taladro superior a router `OpenPolyline`. |
| `S030` | `Pieza_192..208` | traza router OpenPolyline | router `E001` preparado | `G41/G42/G40`, `Z` modal en segmentos | compensacion segun PGMX | traza ejecutada | `SideOfFeature=Right` emite `G42 ... G40`; `Left` emite `G41 ... G40`; `Center` no emite `G41/G42/G40` dentro de la traza; en `OpenPolyline` que sale del rectangulo nominal de la pieza Maestro repite `Z` en los segmentos de corte, mientras que las polilineas internas conservan `Z` modal | Regla de compensacion y modalidad de coordenadas para `OpenPolyline`, independiente de la transicion de cabezal. |
| `S031` | `Cocina` + controles `Pieza_190/191/193/198` | profile milling -> top drill; top drill -> router posterior | router `E001` de perfil cerrado; posible cadena superior intermedia | `?%ETK[8]=1`, `G40`, `?%ETK[7]=0` | router perfil reseteado o taladro superior activo tras cadena | cara Top seleccionada antes de preparar BH o antes de volver al router | Maestro emite `?%ETK[8]=1/G40` al salir de perfiles cerrados reales cuando la salida no agrega desplazamiento extra (`leadout == exit`) o cuando el primer punto del contorno esta sobre el borde superior de pieza; en retornos `top drill -> router OpenPolyline`, esa seleccion se hereda del perfil previo y va despues del reset extra `?%ETK[7]=0`; `Pieza_190/191/193/198` confirman que no debe emitirse cuando el perfil sintetico conserva el desplazamiento extra de salida | Generaliza la seleccion Top que recupera `Cocina` a `65/84` sin romper el corpus raiz `Pieza*` (`210/215`). |
| `S032` | `Pieza_209..214` | orden top drill mixto `005/002/001` | orden fuente del `.pgmx` mezclado o inverso; contexto sin router, con linea previa o con perfil previo | `G0 X/Y`, `?%ETK[6]`, `?%ETK[7]=3` | orden de `WorkingStep` crudo | orden ISO Maestro | Maestro conserva el orden fuente en `6/6` casos: `209..210` sin router previo, `211..212` con linea `E001` previa en sentidos opuestos, `213..214` con perfil `E001` previo horario/antihorario. El candidato actual coincide solo en `209..210`; en `211..214` reordena por heuristica y falla. Una prueba local de preservar orden fuente global daba `Pieza* 217/222`, pero rompia `Cocina` a `30/84`. | Evidencia abierta: en PGMX sinteticos el orden fuente es autoridad; en PGMX reales de `Cocina` falta identificar que metadato permite reproducir el orden Maestro sin romper casos ya cerrados. |
| `S033` | `Prod 26-01-01 Cazaux` + `Pieza_209..214` | orden top drill segun herramienta explicita o automatica | bloque `top_drill` con `Operation.ToolKey.name` explicito o vacio | `G0 X/Y`, `?%ETK[6]`, `?%ETK[7]=3` | orden de `WorkingStep` y modo de resolucion de herramienta | orden ISO Maestro | En Cazaux todos los `94` casos con top drill usan herramienta automatica/embebida (`ToolKey` vacio); de `60` comparables, el orden crudo coincide `0/60` y la regla de vecino mas cercano desde menor `(X,Y)` coincide `58/60`, con dos residuales `mod 8 - Abierto`. En `Pieza_209..214`, con `ToolKey` explicito, Maestro conserva el orden fuente `6/6`. Regla aplicada: conservar fuente cuando todo el bloque tiene `ToolKey.name`; usar vecino mas cercano para bloques automaticos. Validacion: `Pieza_209..214` `6/6`, raiz `Pieza*` `217/222`, `Cocina` `68/84`, Cazaux completo `62/104`. | Distingue PGMX sintetico explicito de PGMX Maestro automatico y mejora orden top drill sin la regresion de preservar fuente global. |
| `S034` | `Prod 26-01-01 Cazaux` | clasificacion residual por bloque/transicion | corpus real con secuencias mixtas router, top drill, slot y side drill | `block_id`, `transition_id`, primera diferencia normalizada | candidato explicado `B-*`/`T-*` | ISO Maestro | Nuevo clasificador: `62` exactos, `20` `header_only` por delta menor `%Or`, `22` residuales operativos. Frentes: `B-RH-002` `9` (`G0/MLV` y `G1` sin `Z`), `T-XH-001` `4` (falta `?%ETK[17]=257/S6000M3` antes de `?%ETK[0]`), `B-BH-005` `3` (orden/pausa lateral), `B-BH-007` `3` (salida sierra vertical `G0 Z20` vs `G1 X... Z20`), `B-BH-002` `2` (arranque top residual), `T-XH-002` `1` (retorno boring head -> router). | Prioridad de trabajo: `B-RH-002`, `T-XH-001`, `B-BH-007`, `B-BH-005`, `B-BH-002`, `T-XH-002`; mantener `header_only` como frente separado de formato de cabecera. |
| `S035` | `Prod 26-01-01 Cazaux` | traza router incremental `B-RH-002` | `profile_milling -> line_milling` o `line_milling -> line_milling`; `OpenPolyline` compensada con corte superficial | `G17`, `MLV=2`, `G0`, `G1 ... Z...` | router previo activo, profundidad de pieza y `cut_z` | traza router candidata | Regla aplicada: conservar `MLV=2` despues de `G17` cuando la traza incremental viene de `profile_milling`, omitirlo cuando viene de `line_milling`; en `OpenPolyline` compensada, repetir `Z` si la polilinea sale del rectangulo nominal o si `cut_z > -pieza.depth`. Validacion Cazaux: `B-RH-002` baja de `9` a `0` como primer frente; corpus queda `65` exactos, `21` `header_only`, `18` residuales operativos. | Cierra `B-RH-002`; la nueva prioridad operativa es `T-XH-001` por activacion de velocidad al pasar de router a top drill. |
| `S036` | `Prod 26-01-01 Cazaux` | router -> top drill `T-XH-001` | entrada `line_milling -> top_drill` sin cambio explicito de `salida.etk_17` en el diferencial | `?%ETK[17]=257`, `S...M3`, `?%ETK[0]` | router lineal previo y velocidad de broca superior | taladro superior activo | Auditoria dedicada: `71` candidatos con `T-XH-001`; lista base `33` exactos, `20` `header_only`, `13` otros frentes y `5` `txh001_diff`. Regla aplicada: si la preparacion de top drill viene de `line_milling` y no hay `etk_17` explicito, reactivar velocidad antes de la mascara. Lista posterior: `33` siguen exactos, `20` siguen `header_only`, `5` despejan `T-XH-001` hacia el siguiente frente y `0` empeoran; `T-XH-001` queda en `0` como primer frente. Validacion ampliada: raiz `Pieza*` estable `217/222`, `ISO\Cocina` mejora `68/84` -> `72/84`. | Cierra la activacion de velocidad de `T-XH-001`; el siguiente frente recomendado es `B-BH-007`. |
| `S037` | `Prod 26-01-01 Cazaux` | salida de sierra vertical `B-BH-007` en `T-BH-005` | `top_drill -> slot_milling`, con trabajo posterior variable | `G1 Z20`, `G1 X... Z20`, `G1 Z-10`, `G0 Z20` | sierra vertical `082` activa despues de top drill | reset de ranura, top drill siguiente, side drill siguiente o cierre final | Regla aplicada: separar lift y salida completa. El lift feed `G1 Z20...` siempre se emite en `T-BH-005`; la salida lateral/reentrada completa se mantiene si no hay trabajo siguiente, si el siguiente no es `top_drill`, o si el siguiente `top_drill` usa herramienta `001`; se suprime solo ante `top_drill` siguiente con herramienta distinta de `001`. Validacion Cazaux: `B-BH-007` baja de `8` a `0`; el corpus queda `65` exactos, `21` `header_only`, `18` residuales. Controles `Pieza_151`, `Pieza_155`, `Pieza_162` exactos; raiz `Pieza*` estable `217/222`, `ISO\Cocina` estable `72/84`. | Cierra `B-BH-007`; la nueva frontera cuantitativa es `B-PG-002` con `8` cierres finales de laterales. |
| `S038` | `Prod 26-01-01 Cazaux` | cierre final `B-PG-002` despues de lateral derecho | ultimo trabajo `side_drill` en plano `Right`, con programa mixto y `Xn` variable | `G0 G53 X...`, `Y0.000`, prefijo `?%ETK[8]=2/G40/T1/M06` | reset lateral derecho previo | cierre comun de maquina | Regla aplicada: el prefijo especial de cierre lateral derecho solo se emite si el `Xn` trae `program_close_x` distinto de `-3700` y no trae `program_close_y`. Los `fajx` con `X=-2500` sin `Y` conservan el prefijo; los `Lado_izquierdo` con `Y0.000` usan cierre comun directo. Validacion Cazaux: `B-PG-002` baja de `8` a `0`; corpus `73` exactos, `21` `header_only`, `10` residuales. Raiz `Pieza*` estable `217/222`, `ISO\Cocina` sube a `78/84`. | Cierra `B-PG-002`; la nueva frontera cuantitativa es `T-XH-002` con `5` casos. |
| `S039` | `Prod 26-01-01 Cazaux` | boring head -> router `T-XH-002` | retorno desde `top_drill` o `side_drill` hacia `line_milling` con router previo variable | `?%ETK[8]=1`, `G40`, `SHF[X/Y/Z]`, `?%ETK[7]=0`, limpieza de velocidad | cabezal de perforacion/ranurado activo | router preparado incrementalmente | Regla aplicada: en `top_drill -> line_milling`, heredar seleccion Top si el router previo es una cadena `OpenPolyline` `T-RH-001` con compensacion `Left/Right`; en `side_drill Back/Left -> line_milling`, restaurar marco lateral derecho y repetir `?%ETK[7]=0` antes de `?%ETK[8]=1/G40`. Validacion Cazaux: `T-XH-002` baja de `5` a `0`; corpus `76` exactos, `21` `header_only`, `7` residuales. Controles `Pieza_162..164` exactos; raiz `Pieza*` estable `217/222`, `ISO\Cocina` sube a `79/84`. | Cierra `T-XH-002`; la nueva frontera cuantitativa es `B-BH-005` con `3` casos. |
| `S040` | `Prod 26-01-01 Cazaux` | separacion de resets completos/parciales como bloques `B-*` | etapas `top_drill_reset`, `side_drill_reset`, `slot_milling_reset` con `final=True/False` | `block_id` explicado por linea | reset parcial o completo segun contexto de emision | secuencia de bloques mas granular, sin cambiar texto ISO | Regla aplicada: `top_drill_reset(final=False)` usa `B-BH-008` y `final=True` usa `B-BH-003`; `side_drill_reset(final=False)` usa `B-BH-010` y `final=True` usa `B-BH-009`; `slot_milling_reset(final=False)` usa `B-BH-012` y `final=True` usa `B-BH-011`. Validacion Cazaux conserva `76` exactos, `21` `header_only`, `7` residuales. Conteo directo `block_sequence`: `B-BH-008` `495`, `B-BH-009` `41`, `B-BH-010` `187`, `B-BH-011` `7`, `B-BH-012` `17`. | Mejora la estadistica de bloques y evita mezclar resets cortos de transicion con resets completos. |
| `S041` | `Prod 26-01-01 Cazaux` | orden y pausa de side drill `B-BH-005` | secuencias laterales con `Back -> Front -> Back` o entrada `top slot -> side drill` seguida de mas laterales | primera traza lateral `G0`, pausa `G4F0.500`, orden de caras | bloque lateral candidato | ISO Maestro | Regla aplicada: `_ordered_side_drill_block` rota tandas laterales donde la misma cara abre y cierra el bloque (`Back -> Front -> Back` queda como tanda final de `Back`, luego `Front`, luego tanda inicial de `Back`), manteniendo orden interno por cota fija; `_emit_side_drill_prepare_after_slot` emite `G4F0.500` si `T-BH-008` entra a una secuencia lateral multiple. Validacion Cazaux: `Faja_Superior.pgmx` queda exacta, `Lavadero/mod 2/Fondo.pgmx` pasa a `header_only`; corpus `77` exactos, `22` `header_only`, `5` residuales. Validacion ampliada: raiz `Pieza*` estable `217/222`, `ISO/Cocina` sube a `80/84`. Hipotesis descartada: usar geometria como cota fija global para `Left` arregla `Faja frontal.pgmx` pero rompe el corpus (`67` exactos, `22` `header_only`, `15` operativos). | Reduce `B-BH-005` de `3` a `1`; el residual restante requiere evidencia adicional para cota fija `Left` en pieza angosta. |
| `S042` | `Prod 26-01-01 Cazaux` | arranque secundario de orden `B-BH-002` | bloque automatico de `4` top drills, una sola herramienta efectiva y profundidades mixtas | primer `G0 X/Y`, orden vecino mas cercano | regla candidata arrancaba por menor `(X,Y)` | ISO Maestro | Regla aplicada: si el bloque `top_drill` no tiene `Operation.ToolKey.name`, tiene exactamente `4` perforaciones, una sola herramienta efectiva por diametro y mas de una profundidad, se arranca en maximo `X` y minimo `Y`; luego se conserva vecino mas cercano. Esto cierra `Cocina/mod 8 - Abierto/Lat_Der.pgmx` y `Lat_Izq.pgmx`. Analisis de orden Cazaux: `60/60` comparables exactos, `0` neither. Validacion Cazaux: `79` exactos, `22` `header_only`, `3` operativos. Validacion ampliada: raiz `Pieza*` estable `217/222`, `ISO/Cocina` sube a `82/84`. | Cierra `B-BH-002`; quedan `B-BH-005`, `B-RH-002` y `T-XH-001` con `1` caso cada uno. |

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
