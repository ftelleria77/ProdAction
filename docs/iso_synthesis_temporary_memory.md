# Memoria Temporal ISO

Este archivo registra hallazgos para estudiar la sintesis de archivos `.ISO`,
que son los programas finales que ejecuta el CNC.

Estado inicial:

- Fecha de apertura: 2026-04-28.
- Todavia no se toca codigo para ISO.
- No hay soporte ISO encontrado en el repo con busqueda textual.
- No hay ejemplos `.iso`, `.ISO` o `.Iso` encontrados en el workspace.
- `main` esta `ahead 1` por el commit anterior.
- `projects_list.json` tiene una modificacion local fuera de este trabajo y no
  debe mezclarse con esta investigacion.

## Objetivo

Definir una estrategia verificable para sintetizar archivos `.ISO` desde la
informacion que ya produce o puede producir el sistema:

1. entender el formato real que espera el CNC
2. obtener ejemplos manuales generados por Maestro
3. comparar esos ejemplos con los `.pgmx` de origen
4. identificar que datos del `.pgmx` son suficientes para emitir ISO
5. decidir si el flujo debe invocar Maestro/postprocesador o sintetizar ISO de
   forma nativa
6. documentar validaciones antes de integrar el modulo al sistema principal

## Preguntas Abiertas

- Que dialecto ISO/G-code usa el CNC real.
- Si Maestro genera el `.ISO` directamente desde `.pgmx` o si interviene un
  postprocesador/configuracion externa.
- Donde vive la configuracion del postprocesador.
- Si el ISO final conserva nombres de piezas, operaciones, herramientas y
  worksteps o solo movimientos CNC.
- Como se expresan:
  - cambios de herramienta
  - origen y offsets
  - planos de seguridad
  - avance, spindle y velocidades
  - taladros
  - fresados lineales, polilineas, circulares y ranuras
  - escuadrado exterior
  - pausas, campana, aspiracion u otras funciones de maquina
- Que diferencias hay entre ISO de pieza individual, En-Juego y programas con
  divisiones/nesting.

## Datos Que Necesitamos Relevar

- Pares `.pgmx` + `.ISO` exportados desde Maestro para una misma pieza.
- Al menos estos casos minimos:
  - pieza sin mecanizados
  - taladro superior simple
  - fresado lineal simple
  - ranura valida con Sierra Vertical X
  - escuadrado exterior
  - pieza con origen distinto de `(0, 0, 0)`
  - pieza girada o reparada por la regla de `SlotSide` vertical
- Si existen, archivos auxiliares de postprocesador o configuracion CNC.
- Nombre/modelo de CNC y controlador.

## Hipotesis Iniciales

- El `.pgmx` conserva geometria CAM de alto nivel; el `.ISO` probablemente es
  una salida postprocesada con movimientos y codigos maquina.
- Para una primera version segura, puede convenir tratar ISO como export final
  dependiente de ejemplos y postprocesador, no como una extension directa del
  sintetizador PGMX.
- Si el dialecto ISO usa codigos propietarios, sintetizar nativamente sin
  ejemplos suficientes seria riesgoso.

## Rondas

### Ronda 1 - Apertura

- Busquedas ejecutadas:
  - `rg -n "ISO|\\.iso|iso" . -S`
  - `rg --files -g "*.iso" -g "*.ISO" -g "*.Iso"`
- Resultado:
  - sin soporte ISO existente
  - sin ejemplos ISO locales
  - solo falsos positivos de `isoformat`
- Proxima accion recomendada:
  - conseguir uno o mas pares reales `.pgmx` + `.ISO` exportados desde Maestro
  - mantener esos ejemplos fuera del flujo principal hasta entender el formato

### Ronda 2 - Pieza base para postprocesado

- Solicitud:
  - crear `Pieza.pgmx`
  - dimensiones nominales: `300 x 400 x 18`
  - destino PGMX: `S:\Maestro\Projects\ProdAction\ISO`
  - destino esperado del ISO postprocesado: `P:\USBMIX\ProdAction\ISO`
- Convencion aplicada:
  - `300 x 400 x 18` se interpreta como `width=300`, `length=400`,
    `depth=18`
  - origen inicial: `(0, 0, 0)`
- Archivo generado:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza.pgmx`
- Validacion local:
  - `piece_name = Pieza`
  - `length = 400`
  - `width = 300`
  - `depth = 18`
  - `origin = 0,0,0`
  - `features = 0`
  - `operations = 0`
  - `working_steps = 1` (`XN`)
  - `sha256 = d25b4822c558b5c594d897023660e161156bcdb4e6e7ec7c5c88f45b995602ab`
- Proximo paso externo:
  - abrir el `.pgmx` en la PC del CNC
  - postprocesar con la configuracion propia del CNC
  - guardar el `.ISO` resultante en `P:\USBMIX\ProdAction\ISO`

### Ronda 3 - Primer ISO postprocesado sin mecanizados

- Archivo analizado:
  - `P:\USBMIX\ProdAction\ISO\pieza.iso`
- Archivo de origen:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza.pgmx`
- Propiedades del ISO:
  - texto UTF-8/ASCII
  - `51` lineas
  - `737` bytes
  - `sha256 = 5C506F4D555A78C71843FB89F8C97CFCCD4B514129DD5C2E0008DBAD85E41C2A`
- Relacion directa con el PGMX:
  - PGMX: `piece_name = Pieza`
  - PGMX: `length = 400`, `width = 300`, `depth = 18`
  - PGMX: `origin = 0,0,0`
  - PGMX: `execution_fields = HG`
  - ISO linea 1: `% pieza.pgm`
  - ISO linea 2:
    `;H DX=400.000 DY=300.000 DZ=18.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0`
- Interpretacion inicial del encabezado:
  - `DX` corresponde a `length`
  - `DY` corresponde a `width`
  - `DZ` corresponde a `depth`
  - `BX/BY/BZ` corresponden al origen/base de la pieza
  - `-HG` corresponde a `execution_fields`
  - `*MM` confirma unidades metricas
  - `pieza.pgm` es el nombre interno del programa aunque el archivo final sea
    `.iso`
- Estructura observada:
  - lineas 1-3: encabezado y parametro inicial `ETK[500]`
  - linea 5: llamada `_paras(...)`
  - lineas 7-24: preparacion de maquina, unidades, offsets y shifts
  - lineas 25-30: posicion segura/salida sin mecanizados
  - lineas 31-51: reset de variables, shifts y fin con `M2`
- Codigos/bloques identificados:
  - `G0 G53`: movimientos rapidos en coordenadas de maquina
  - `G71`: modo metrico o preparacion metrica del controlador
  - `G40`: cancelacion de compensacion de herramienta
  - `G61`: modo exact stop/preciso
  - `G64`: modo continuo
  - `D0`: sin corrector/herramienta activa
  - `M2`: fin de programa
  - `MLV`, `SHF`, `%Or`, `%ETK`, `%EDK`, `VL6`, `VL7` son variables o macros
    propietarias del postprocesador/controlador
- Hallazgo importante:
  - como el PGMX no tiene features ni operations, el ISO no contiene bloques
    de mecanizado: no aparecen `G1`, `G2`, `G3`, cambios de herramienta,
    spindle, feed ni trayectorias.
  - este archivo sirve como plantilla de preambulo/postambulo para el CNC.
- Offsets observados:
  - `%Or[0].ofX=-400000.000` y `SHF[X]=-400.000` coinciden con `DX=400`
  - `%Or[0].ofZ=18000.000` coincide con `DZ=18` en milesimas
  - `%Or[0].ofY=-1515599.976` y `SHF[Y]=-1515.600` no coinciden con `DY=300`
    y parecen depender de la referencia/configuracion de la CNC; requieren
    mas muestras para inferir regla
- Proxima muestra util:
  - repetir con la misma pieza pero agregando un mecanizado minimo, idealmente
    un taladro superior simple, para aislar el primer bloque real de operacion

### Ronda 4 - Pieza base con taladro superior D8

- Solicitud:
  - sintetizar una nueva pieza con un hueco de `8 mm` en la cara superior
  - guardar en `S:\Maestro\Projects\ProdAction\ISO`
- Archivo generado:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_Hueco8.pgmx`
- Convencion aplicada:
  - dimensiones: `width=300`, `length=400`, `depth=18`
  - origen: `(0, 0, 0)`
  - centro del taladro: `(150, 200)` sobre `Top`
  - diametro: `8`
  - profundidad: pasante, `extra_depth=0`
  - nombre de feature: `Hueco_D8`
- Validacion local:
  - `piece_name = Pieza_Hueco8`
  - `features = 1`
  - `operations = 1`
  - `working_steps = 2` (`Drilling` + `XN`)
  - feature: `Hueco_D8`, `a:RoundHole`, `diameter = 8`
  - operation: `a:DrillingOperation`
  - herramienta resuelta: `1888 / 001`
  - `security_plane = 20`
  - adaptador: `adapted = 1`, `unsupported = 0`, `drillings = 1`
  - `sha256 = 32e9bb70284079a5718b4c6a0b464ada1cc89158252c45a42ff282def3154a56`
- Proximo paso externo:
  - abrir `Pieza_Hueco8.pgmx` en la PC del CNC
  - postprocesar
  - guardar el ISO resultante en `P:\USBMIX\ProdAction\ISO`
  - comparar contra `pieza.iso` para aislar el bloque agregado por el taladro

### Ronda 5 - ISO de taladro superior D8

- Archivo analizado:
  - `P:\USBMIX\ProdAction\ISO\pieza_hueco8.iso`
- Archivo de origen:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_Hueco8.pgmx`
- Propiedades del ISO:
  - texto UTF-8/ASCII
  - `86` lineas
  - `1254` bytes
  - `sha256 = B85A6C1EC41CEBF9B5E1959F3C67060ED9C7B17A063814ADC79C3874A23E5D24`
- Comparacion con `pieza.iso` sin mecanizados:
  - el encabezado dimensional se conserva igual salvo el nombre interno:
    `% pieza_hueco8.pgm`
  - el bloque agregado por el taladro queda entre la cancelacion inicial de
    compensacion y el cierre comun del programa
- Bloque de taladro observado:
  - preparacion:
    - `G17`
    - `?%ETK[6]=1`
    - restablece `%Or[0]` y `SHF[X/Y/Z]`
    - `?%ETK[17]=257`
    - `S6000M3`
    - `?%ETK[0]=1`
  - posicion:
    - `G0 X150.000 Y200.000`
    - `G0 Z115.000`
  - perforacion:
    - `?%ETK[7]=3`
    - `MLV=2`
    - `G1 G9 Z77.000 F2000.000`
    - `G0 Z115.000`
  - salida:
    - `SHF[Z]=18.000+%ETK[114]/1000`
    - `?%ETK[7]=0`
    - `G61`
    - `?%ETK[0]=0`
    - `?%ETK[17]=0`
    - `G4F1.200`
    - `M5`
    - `D0`
- Relacion directa con el PGMX:
  - PGMX feature: `Hueco_D8`, `a:RoundHole`
  - PGMX operation: `a:DrillingOperation`
  - PGMX herramienta: `1888 / 001`
  - catalogo herramienta `001`:
    - descripcion: `Broca Plana Vertical D8mm`
    - diametro: `8`
    - `tool_offset_length = 77`
    - `pilot_length = 77`
    - `sinking_length = 40`
    - `spindle_speed_std = 6000`
    - `descent_speed_std = 2`
  - ISO `S6000M3` corresponde al spindle standard de la herramienta
  - ISO `F2000.000` corresponde a `descent_speed_std = 2` expresado como
    `2000 mm/min`
  - ISO `G0 X150.000 Y200.000` corresponde al centro del taladro
- Relacion de Z observada:
  - PGMX toolpaths locales:
    - `Approach`: `(150,200,38) -> (150,200,18)`
    - `TrajectoryPath`: `(150,200,18) -> (150,200,0)`
    - `Lift`: `(150,200,0) -> (150,200,38)`
  - ISO:
    - posicion segura: `Z115.000`
    - perforacion hasta: `Z77.000`
  - hipotesis fuerte para esta herramienta:
    - `Z ISO = Z local + tool_offset_length`
    - `38 + 77 = 115`
    - `0 + 77 = 77`
  - el ISO no emite una parada intermedia en `Z95` (`18 + 77`); agrupa
    approach + trayectoria en una unica bajada `G1 G9 Z77 F2000`
- Codigos aun no resueltos:
  - `?%ETK[17]=257`: parece seleccionar estado/herramienta/cabezal, pero no
    coincide directamente con `tool_id = 1888`; requiere mas muestras
  - `?%ETK[7]=3`: parece activar modo/ciclo de perforacion
  - `?%ETK[6]=1`: preparacion del plano/cabezal vertical, pendiente
  - `MLV=1/2`: niveles o marcos de coordenadas del postprocesador
- Proxima muestra util:
  - mismo taladro D8 pero en otra coordenada para confirmar que solo cambian
    `X/Y`
  - o un taladro de otro diametro/herramienta para estudiar `ETK[17]`,
    velocidades y offsets

### Ronda 6 - Taladro D8 con origen no nulo

- Solicitud:
  - sintetizar la misma pieza con origen `(5, 5, 25)`
  - guardar en `S:\Maestro\Projects\ProdAction\ISO`
- Archivo generado:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_Hueco8_Origen_5_5_25.pgmx`
- Convencion aplicada:
  - dimensiones: `width=300`, `length=400`, `depth=18`
  - origen: `(5, 5, 25)`
  - centro local del taladro: `(150, 200)` sobre `Top`
  - diametro: `8`
  - profundidad: pasante, `extra_depth=0`
  - nombre de feature: `Hueco_D8`
- Validacion local:
  - `piece_name = Pieza_Hueco8_Origen_5_5_25`
  - `features = 1`
  - `operations = 1`
  - `working_steps = 2` (`Drilling` + `XN`)
  - operation: `a:DrillingOperation`
  - herramienta resuelta: `1888 / 001`
  - adaptador: `adapted = 1`, `unsupported = 0`, `drillings = 1`
  - `sha256 = 890dd3fe16ba0ad06e8f82ae2618344d682eeeef36805d81c4fc86eb507dade8`
- Hallazgo esperado a confirmar con ISO:
  - el origen no deberia trasladar la geometria local del taladro dentro del
    PGMX
  - el ISO deberia revelar si `BX/BY/BZ`, `%Or` y/o `SHF` incorporan el origen
    de colocacion
- Proximo paso externo:
  - postprocesar `Pieza_Hueco8_Origen_5_5_25.pgmx`
  - guardar el ISO resultante en `P:\USBMIX\ProdAction\ISO`
  - comparar contra `pieza_hueco8.iso`

### Ronda 7 - ISO de taladro D8 con origen no nulo

- Archivo analizado:
  - `P:\USBMIX\ProdAction\ISO\pieza_hueco8_origen_5_5_25.iso`
- Archivo comparado:
  - `P:\USBMIX\ProdAction\ISO\pieza_hueco8.iso`
- Archivo de origen:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_Hueco8_Origen_5_5_25.pgmx`
- Propiedades del ISO:
  - texto UTF-8/ASCII
  - `86` lineas
  - `1270` bytes
  - `sha256 = 4F091CF08833CB02F733AD13B0A811043DDEC797E6F92141DD685D2C38C61DC7`
- Diferencia de encabezado:
  - sin origen:
    `;H DX=400.000 DY=300.000 DZ=18.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0`
  - con origen `(5,5,25)`:
    `;H DX=405.000 DY=305.000 DZ=43.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0`
- Hallazgo de encabezado:
  - `BX/BY/BZ` siguen en `0`
  - el origen no aparece como `B`
  - el postprocesador expande las dimensiones:
    - `DX = length + origin_x = 400 + 5 = 405`
    - `DY = width + origin_y = 300 + 5 = 305`
    - `DZ = depth + origin_z = 18 + 25 = 43`
- Cambios de setup inicial:
  - `%Or[0].ofX`: `-400000.000 -> -405000.000`
  - `%Or[0].ofY`: sin cambio, `-1515599.976`
  - `%Or[0].ofZ`: `18000.000 -> 43000.000`
  - `SHF[X]`: `-400.000 -> -405.000`
  - `SHF[Y]`: sin cambio inicial, `-1515.600`
  - `SHF[Z]`: `18.000+%ETK[114]/1000 -> 43.000+%ETK[114]/1000`
- Cambios dentro del bloque de taladro:
  - `SHF[Z]` previo al mecanizado:
    - `0.000+%ETK[114]/1000 -> 25.000+%ETK[114]/1000`
  - `%Or[0].ofX` dentro de la operacion:
    - `-400000.000 -> -410000.000`
    - hipotesis: `-(length + 2*origin_x) * 1000`
  - `%Or[0].ofY`: sin cambio, `-1515599.976`
  - `%Or[0].ofZ`: `18000.000 -> 43000.000`
  - `SHF[X]`: `-400.000 -> -405.000`
  - `SHF[Y]`: `-1515.600 -> -1510.600`
  - `SHF[Z]`: `0.000 -> 25.000`
  - `SHF[Z]` posterior al mecanizado:
    - `18.000+%ETK[114]/1000 -> 43.000+%ETK[114]/1000`
- Bloque de taladro que no cambio:
  - `?%ETK[17]=257`
  - `S6000M3`
  - `G0 X150.000 Y200.000`
  - `G0 Z115.000`
  - `?%ETK[7]=3`
  - `G1 G9 Z77.000 F2000.000`
  - `G0 Z115.000`
- Hallazgo importante:
  - el origen no traslada las coordenadas locales emitidas para el taladro:
    `X150 Y200` permanece igual
  - tampoco cambia los valores `Z115/Z77` del movimiento de herramienta
  - el origen se aplica mediante dimensiones efectivas, `%Or` y `SHF`
  - esto coincide con la regla PGMX ya observada: `origin_x/y/z` cambia
    `WorkpieceSetup/Placement`, no las curvas internas
- Preguntas abiertas:
  - confirmar con mas muestras la formula de `%Or[0].ofX` dentro de la
    operacion, porque suma dos veces `origin_x` en este caso
  - entender por que `%Or[0].ofY` permanece fijo mientras `SHF[Y]` si absorbe
    `origin_y`
  - confirmar si `DZ = depth + origin_z` se mantiene en otros mecanizados

### Ronda 8 - Pieza con dos taladros superiores diferentes

- Solicitud:
  - sintetizar una pieza con `2` huecos diferentes
  - guardar en `S:\Maestro\Projects\ProdAction\ISO`
- Archivo generado:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_DosHuecos.pgmx`
- Convencion aplicada:
  - dimensiones: `width=300`, `length=400`, `depth=18`
  - origen: `(0, 0, 0)`
  - taladro 1:
    - nombre: `Hueco_D8`
    - centro local: `(100, 200)` sobre `Top`
    - diametro: `8`
    - familia: `Flat`
    - herramienta: `1888 / 001`
  - taladro 2:
    - nombre: `Hueco_D5`
    - centro local: `(220, 200)` sobre `Top`
    - diametro: `5`
    - familia: `Conical`
    - herramienta: `1894 / 007`
- Validacion local:
  - `piece_name = Pieza_DosHuecos`
  - `features = 2`
  - `operations = 2`
  - `working_steps = 3` (`Hueco_D8`, `Hueco_D5`, `XN`)
  - feature `Hueco_D8`: `a:RoundHole`, `diameter = 8`,
    `bottom_condition = a:ThroughHoleBottom`
  - feature `Hueco_D5`: `a:RoundHole`, `diameter = 5`,
    `bottom_condition = a:ThroughHoleBottom`
  - adaptador: `adapted = 2`, `unsupported = 0`, `drillings = 2`
  - `sha256 = 216c42b563a2538fb78afb6e72101bdbd1484efb8828d3c56777a36b8ad59e2f`
- Proximo paso externo:
  - postprocesar `Pieza_DosHuecos.pgmx`
  - guardar el ISO resultante en `P:\USBMIX\ProdAction\ISO`
  - comparar contra `pieza_hueco8.iso` para aislar:
    - repeticion del bloque de taladro
    - cambio de herramienta `001 -> 007`
    - valor de `ETK[17]` para la herramienta `007`
    - si el segundo taladro conserva `Z115/Z77` por compartir
      `tool_offset_length = 77`

### Ronda 9 - Dos taladros diferentes con origen no nulo

- Solicitud:
  - volver a sintetizar la pieza de dos huecos con origen `(5, 5, 25)`
  - guardar en `S:\Maestro\Projects\ProdAction\ISO`
- Archivo generado:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_DosHuecos_Origen_5_5_25.pgmx`
- Convencion aplicada:
  - dimensiones: `width=300`, `length=400`, `depth=18`
  - origen: `(5, 5, 25)`
  - taladro 1:
    - nombre: `Hueco_D8`
    - centro local: `(100, 200)` sobre `Top`
    - diametro: `8`
    - familia: `Flat`
    - herramienta: `1888 / 001`
  - taladro 2:
    - nombre: `Hueco_D5`
    - centro local: `(220, 200)` sobre `Top`
    - diametro: `5`
    - familia: `Conical`
    - herramienta: `1894 / 007`
- Validacion local:
  - `piece_name = Pieza_DosHuecos_Origen_5_5_25`
  - `features = 2`
  - `operations = 2`
  - `working_steps = 3` (`Hueco_D8`, `Hueco_D5`, `XN`)
  - adaptador: `adapted = 2`, `unsupported = 0`, `drillings = 2`
  - `sha256 = d33b5c74e2167c0765b1f7e7c99a1aa8be5b7d7f2d1fd0a6b26940cb31dddf28`
- Hallazgo esperado a confirmar con ISO:
  - comparar contra `Pieza_DosHuecos.pgmx` postprocesada para ver si el origen
    vuelve a afectar solo encabezado, `%Or` y `SHF`
  - observar si los bloques de ambas herramientas conservan coordenadas locales
    `X100 Y200` y `X220 Y200`
  - confirmar si el cambio de herramienta interactua con el origen en
    `ETK[17]`, `SHF` o `%Or`

### Ronda 10 - ISO de dos taladros diferentes

- Archivos analizados:
  - `P:\USBMIX\ProdAction\ISO\pieza_doshuecos.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_doshuecos_origen_5_5_25.iso`
- Archivos de origen:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_DosHuecos.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_DosHuecos_Origen_5_5_25.pgmx`
- Propiedades del ISO sin origen:
  - texto UTF-8/ASCII
  - `105` lineas
  - `1565` bytes
  - `sha256 = 01A2BFF395C33408F864428782D3A269B1A99961920FC987436D99986A23E943`
- Propiedades del ISO con origen `(5,5,25)`:
  - texto UTF-8/ASCII
  - `105` lineas
  - `1582` bytes
  - `sha256 = 7BE007003EA3BC2656823E3F9D07DFD371A4C45999B87EF2911AF3DD5C27424E`
- Comparacion con `pieza_hueco8.iso`:
  - el primer taladro D8 conserva el bloque conocido, pero cambia el centro:
    - muestra anterior: `G0 X150.000 Y200.000`
    - dos huecos: `G0 X100.000 Y200.000`
  - el segundo taladro D5 agrega un sub-bloque nuevo sin apagar el spindle entre
    operaciones.
- Bloque D8 observado:
  - `?%ETK[6]=1`
  - `?%ETK[17]=257`
  - `S6000M3`
  - `?%ETK[0]=1`
  - `G0 X100.000 Y200.000`
  - `G0 Z115.000`
  - `?%ETK[7]=3`
  - `MLV=2`
  - `G1 G9 Z77.000 F2000.000`
  - `G0 Z115.000`
  - `?%ETK[7]=0`
- Bloque D5 observado:
  - `MLV=1`
  - `SHF[Z]=0.000+%ETK[114]/1000`
  - `MLV=2`
  - `G17`
  - `?%ETK[6]=7`
  - `G0 X100.000 Y200.000 Z115.000`
  - `MLV=2`
  - `SHF[X]=-128.000`
  - `SHF[Y]=0.000`
  - `SHF[Z]=0.000`
  - `?%ETK[0]=64`
  - `G0 X220.000 Y200.000`
  - `G0 Z115.000`
  - `?%ETK[7]=3`
  - `G1 G9 Z77.000 F2000.000`
  - `G0 Z115.000`
  - `?%ETK[7]=0`
- Relaciones nuevas:
  - `?%ETK[6]` parece mapear al numero de broca vertical:
    - herramienta `001` -> `?%ETK[6]=1`
    - herramienta `007` -> `?%ETK[6]=7`
  - `?%ETK[0]` parece ser bitmask de broca activa:
    - herramienta `001` -> `1`
    - herramienta `007` -> `64` (`2^(7-1)`)
  - `SHF[X]=-128.000` parece representar el desplazamiento mecanico entre la
    broca `001` y la broca `007` en el cabezal vertical.
  - `?%ETK[17]=257` solo se emite al iniciar el bloque con la primera broca y
    se resetea al final; no cambia explicitamente al pasar a `007`.
  - No hay `M5` ni nuevo `S...M3` entre D8 y D5; esto es consistente con que
    ambas herramientas usan `spindle_speed_std = 6000`.
  - Ambas herramientas tienen `tool_offset_length = 77`, por eso ambas
    operaciones conservan `Z115/Z77`.
- Comparacion de origen:
  - el ISO con origen conserva sin cambios los comandos locales de mecanizado:
    - `G0 X100.000 Y200.000`
    - `G0 X220.000 Y200.000`
    - `G0 Z115.000`
    - `G1 G9 Z77.000 F2000.000`
    - `SHF[X]=-128.000`
    - `?%ETK[6]=1/7`
    - `?%ETK[0]=1/64`
  - vuelven a cambiar solo encabezado, `%Or` y `SHF` de marco:
    - `DX=400 -> 405`
    - `DY=300 -> 305`
    - `DZ=18 -> 43`
    - `%Or[0].ofX=-400000 -> -405000` en setup inicial
    - `%Or[0].ofX=-400000 -> -410000` dentro del bloque de operacion
    - `%Or[0].ofZ=18000 -> 43000`
    - `SHF[X]=-400 -> -405`
    - `SHF[Y]=-1515.600 -> -1510.600` dentro del bloque de operacion
    - `SHF[Z]=0 -> 25` antes de mecanizar
    - `SHF[Z]=18... -> 43...` al salir
- Hallazgo importante:
  - la presencia de dos herramientas verticales no invalida la regla observada
    para origen: el origen no traslada las coordenadas locales `X/Y/Z` de las
    operaciones, sino que se absorbe en el marco del postprocesador.
  - para multiples taladros verticales, el ISO parece seleccionar brocas
    dentro del cabezal mediante `ETK[6]`, `ETK[0]` y shifts mecanicos, no con
    un cambio de herramienta tradicional.
- Preguntas abiertas:
  - confirmar `SHF[X]=-128` con otras combinaciones de brocas para reconstruir
    la tabla de offsets entre spindles.
  - confirmar si aparece un nuevo `S...M3` cuando dos brocas tienen distinta
    velocidad standard.
  - confirmar si `?%ETK[17]` depende solo del arranque del grupo vertical o de
    la primera broca activa.

## Convencion De Nombres Desde Ronda 11

- Desde esta ronda, las piezas de prueba ISO se sintetizan siempre con origen
  `(5, 5, 25)`.
- El origen y las medidas ya no se agregan al nombre de archivo.
- Los archivos se nombran con numeracion ascendente:
  - `Pieza_001.pgmx`
  - `Pieza_002.pgmx`
  - etc.

### Ronda 11 - Pieza 001 con siete brocas verticales

- Solicitud:
  - sintetizar una pieza de `400 x 250 x 18`
  - origen fijo: `(5, 5, 25)`
  - incluir agujeros con las brocas `001`, `002`, `003`, `004`, `005`, `006`
    y `007`
  - guardar en `S:\Maestro\Projects\ProdAction\ISO`
- Archivo generado:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_001.pgmx`
- Convencion dimensional aplicada:
  - para la cara `Top`, el eje local `X` valida contra `length`
  - para representar una pieza `400 x 250 x 18`, se uso:
    - `length = 400`
    - `width = 250`
    - `depth = 18`
  - origen: `(5, 5, 25)`
- Distribucion de taladros:
  - broca `001`: `D8`, `Flat`, centro `(50, 60)`, herramienta `1888 / 001`
  - broca `002`: `D15`, `Flat`, centro `(115, 60)`, herramienta `1889 / 002`
  - broca `003`: `D20`, `Flat`, centro `(190, 60)`, herramienta `1890 / 003`
  - broca `004`: `D35`, `Flat`, centro `(300, 60)`, herramienta `1891 / 004`
  - broca `005`: `D5`, `Flat`, centro `(80, 170)`, herramienta `1892 / 005`
  - broca `006`: `D4`, `Flat`, centro `(180, 170)`, herramienta `1893 / 006`
  - broca `007`: `D5`, `Conical`, centro `(280, 170)`, herramienta `1894 / 007`
- Validacion local:
  - `piece_name = Pieza_001`
  - `features = 7`
  - `operations = 7`
  - `working_steps = 8` (`7` taladros + `XN`)
  - adaptador: `adapted = 7`, `unsupported = 0`, `drillings = 7`
  - `sha256 = 1ac49e1040e3ed991a047d0eb8e504c7f486a47184fee153599fee40336d8153`
- Nota:
  - la feature de la broca `005` queda con herramienta `1892 / 005`, pero el
    adaptador actual vuelve a clasificar el `D5` pasante superior como
    `Conical` por heuristica; para este estudio ISO manda la herramienta
    resuelta del snapshot.
- Proximo paso externo:
  - postprocesar `Pieza_001.pgmx`
  - guardar el ISO resultante en `P:\USBMIX\ProdAction\ISO`
  - comparar contra las rondas anteriores para reconstruir:
    - `ETK[6]` por broca `001..007`
    - `ETK[0]` como bitmask
    - offsets mecanicos `SHF[X/Y]` entre brocas
    - comportamiento cuando cambia `S6000` a `S4000`

### Ronda 12 - ISO de Pieza 001 con siete brocas verticales

- Archivo analizado:
  - `P:\USBMIX\ProdAction\ISO\pieza_001.iso`
- Archivo de origen:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_001.pgmx`
- Propiedades del ISO:
  - texto UTF-8/ASCII
  - `204` lineas
  - `3144` bytes
  - `sha256 = 2AC501F39616649109B89FDDA7F526F59545AAEA0133CC75C88912F80BBA6F36`
- Encabezado:
  - `% pieza_001.pgm`
  - `;H DX=405.000 DY=255.000 DZ=43.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0`
- Confirmacion de regla de dimensiones con origen:
  - `DX = length + origin_x = 400 + 5 = 405`
  - `DY = width + origin_y = 250 + 5 = 255`
  - `DZ = depth + origin_z = 18 + 25 = 43`
- Tabla observada por broca:

| Broca | Tool | Centro | ETK[6] | ETK[0] | SHF[X] | SHF[Y] | SHF[Z] | Spindle | Bajada |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `001` | `1888` | `X50 Y60` | `1` | `1` | `0.000` | `0.000` | `0.000` | `S6000M3` | `F2000` |
| `002` | `1889` | `X115 Y60` | `2` | `2` | `0.000` | `32.000` | `-0.200` | `S4000M3` | `F1000` |
| `003` | `1890` | `X190 Y60` | `3` | `4` | `0.000` | `64.000` | `-0.250` | continua `S4000` | `F1000` |
| `004` | `1891` | `X300 Y60` | `4` | `8` | `-32.000` | `0.000` | `-0.350` | continua `S4000` | `F1000` |
| `005` | `1892` | `X80 Y170` | `5` | `16` | `-64.000` | `0.000` | `-0.950` | `S6000M3` | `F2000` |
| `006` | `1893` | `X180 Y170` | `6` | `32` | `-96.000` | `0.000` | `-0.200` | continua `S6000` | `F2000` |
| `007` | `1894` | `X280 Y170` | `7` | `64` | `-128.000` | `0.000` | `0.000` | continua `S6000` | `F2000` |

- Reglas confirmadas:
  - `ETK[6]` coincide con el numero de broca vertical.
  - `ETK[0]` es una mascara de bit:
    - `001 -> 1`
    - `002 -> 2`
    - `003 -> 4`
    - `004 -> 8`
    - `005 -> 16`
    - `006 -> 32`
    - `007 -> 64`
  - `SHF[X/Y/Z]` representa el offset mecanico de cada broca dentro del cabezal.
  - Las coordenadas `G0 X... Y...` siguen siendo las coordenadas locales de
    cada taladro.
  - Todas las brocas tienen `tool_offset_length = 77`, por eso todas conservan
    `G0 Z115.000` y `G1 G9 Z77.000`.
- Spindle y feed:
  - `S6000M3` aparece al iniciar con `001`.
  - `S4000M3` aparece al cambiar a `002`.
  - no se repite para `003` ni `004`, que siguen a `4000 rpm`.
  - `S6000M3` reaparece al cambiar a `005`.
  - no se repite para `006` ni `007`, que siguen a `6000 rpm`.
  - `F1000` aparece en brocas `002`, `003` y `004`.
  - `F2000` aparece en brocas `001`, `005`, `006` y `007`.
- Nueva inferencia:
  - `?%ETK[17]=257` se emite junto con el arranque o cambio de velocidad de
    spindle:
    - antes de `S6000M3` en `001`
    - antes de `S4000M3` en `002`
    - antes de `S6000M3` en `005`
  - no se emite al pasar a brocas que conservan la misma velocidad de spindle.
- Preguntas abiertas:
  - por que las brocas `002-004` usan `F1000` aunque `descent_speed_std` del
    catalogo es `2`; podria estar usando `feed_rate_std = 1` para estas brocas.
  - por que las brocas `005-007` usan `F2000` aunque `feed_rate_std = 3`;
    podria haber una regla por familia/tamano o una limitacion del
    postprocesador.
  - validar si la tabla `SHF[X/Y/Z]` se mantiene en otros tamanos de pieza y
    otros ordenamientos de brocas.

### Ronda 13 - Pieza 002 con taladros centrados en caras laterales

- Solicitud:
  - sintetizar la misma pieza base de la ronda anterior:
    - `400 x 250 x 18`
    - origen fijo: `(5, 5, 25)`
  - agregar un agujero centrado en cada cara lateral, frontal y posterior.
- Archivo generado:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_002.pgmx`
- Criterio aplicado:
  - se uso `D8 Flat`.
  - se configuro como no pasante con `target_depth = 10`.
  - la primera version generada habia resuelto herramientas laterales
    explicitamente; esto fue corregido despues de abrir el archivo en Maestro.
- Distribucion de taladros:
  - `Front`: centro local `(200, 9)`
  - `Back`: centro local `(200, 9)`
  - `Left`: centro local `(125, 9)`
  - `Right`: centro local `(125, 9)`
- Validacion local con `pgmx_snapshot`:
  - `piece_name = Pieza_002`
  - `length = 400`, `width = 250`, `depth = 18`
  - `origin = (5, 5, 25)`
  - `features = 4`
  - `operations = 4`
  - `working_steps = 5` (`4` taladros + `XN`)
  - todas las features quedan como `RoundHole` con `BottomCondition = FlatHoleBottom`
  - `sha256 = 37655f9b3503229ade21ce40c350c5a4e2147febd15427343aec285e4b6a7076`
- Trayectorias efectivas observadas:
  - `Front`: entra desde `Y=-20`, perfora de `Y=0` a `Y=10`
  - `Back`: entra desde `Y=270`, perfora de `Y=250` a `Y=240`
  - `Left`: entra desde `X=-20`, perfora de `X=0` a `X=10`
  - `Right`: entra desde `X=420`, perfora de `X=400` a `X=390`
- Proximo paso externo:
  - abrir `Pieza_002.pgmx` en la PC del CNC.
  - postprocesar y guardar el ISO como `pieza_002.iso`.
  - comparar el ISO resultante para relevar:
    - codificacion que el postprocesador elige para las herramientas laterales
    - ejes usados por cada cara
    - offsets `SHF`
    - relacion de las cotas ISO con el esquema real de herramientas laterales.

### Ronda 14 - Correccion de Pieza 002 y regla de ToolKey lateral

- El archivo `S:\Maestro\Projects\ProdAction\ISO\Pieza_002.pgmx` fue abierto y
  corregido manualmente en Maestro/CNC.
- Propiedades del archivo corregido:
  - `sha256 = 5450a300c2dcd7eade3b4714e7fe373cc4d6273c2dcb8d1218a320ed0046e555`
  - `piece_name = Pieza_002`
  - `length = 400`, `width = 250`, `depth = 18`
  - `origin = (5, 5, 25)`
  - `features = 4`
  - `operations = 4`
  - `working_steps = 5`
- Hallazgo principal:
  - las cuatro `DrillingOperation` quedaron con `ToolKey` vacio:
    - `ID = 0`
    - `ObjectType = System.Object`
    - `Name = ""`
  - esto aplica a `Front`, `Back`, `Left` y `Right`.
- Trayectorias efectivas preservadas:
  - `Front`: `Y=-20 -> Y=0 -> Y=10 -> Y=-20`
  - `Back`: `Y=270 -> Y=250 -> Y=240 -> Y=270`
  - `Left`: `X=-20 -> X=0 -> X=10 -> X=-20`
  - `Right`: `X=420 -> X=400 -> X=390 -> X=420`
- Correccion de criterio:
  - no se debe resolver automaticamente `Front D8`, `Back D8`, `Left D8` ni
    `Right D8` a `058..061` al escribir el PGMX.
  - para huecos laterales/frontal/posterior, `tool_resolution="Auto"` debe
    dejar `ToolKey` vacio.
  - si en el futuro se quiere forzar una herramienta lateral concreta, debe
    hacerse con `tool_resolution="Explicit"` y validacion fuerte.

### Ronda 15 - ISO de Pieza 002 con taladros laterales sin ToolKey

- Archivo analizado:
  - `P:\USBMIX\ProdAction\ISO\pieza_002.iso`
- Archivo de origen:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_002.pgmx`
- Propiedades del ISO:
  - `171` lineas
  - `2545` bytes
  - `sha256 = EBBD3449109D8A816567CE96D8A35D7DC0E18A737C996E40DB4B97D8960582E1`
- Encabezado:
  - `% pieza_002.pgm`
  - `;H DX=405.000 DY=255.000 DZ=43.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0`
- Confirmacion:
  - aunque el PGMX corregido tiene `ToolKey` vacio en las cuatro
    `DrillingOperation`, el postprocesador resolvio herramientas laterales
    reales desde la cara/trayectoria.
  - esto valida la correccion de `tool_resolution="Auto"` lateral: no escribir
    `058..061` en el PGMX y dejar que Maestro/postprocesador los determine.

| Cara | PGMX efectivo | ISO herramienta | ETK[8] | ETK[0] | SHF herramienta | Movimiento ISO |
| --- | --- | --- | --- | --- | --- | --- |
| `Front` | `X=200`, `Y -20 -> 0 -> 10`, `Z=9` | `58` | `5` | `1073741824` | `X=32`, `Y=-21.750`, `Z=66.500` | `G0 X200 Y-85`, `G1 Y-55 F2000` |
| `Back` | `X=200`, `Y 270 -> 250 -> 240`, `Z=9` | `59` | `4` | continua `1073741824` | `X=32`, `Y=29.500`, `Z=66.500` | `G0 X-200 Y335`, `G1 Y305 F2000` |
| `Left` | `X -20 -> 0 -> 10`, `Y=125`, `Z=9` | `61` | `3` | `2147483648` | `X=-118`, `Y=-32`, `Z=66.300` | `G0 X-85 Y-125`, `G1 X-55 F2000` |
| `Right` | `X 420 -> 400 -> 390`, `Y=125`, `Z=9` | `60` | `2` | continua `2147483648` | `X=-66.900`, `Y=-32`, `Z=66.450` | `G0 X485 Y125`, `G1 X455 F2000` |

- Reglas observadas:
  - `ETK[6]` identifica la broca lateral real:
    - `Front -> 58`
    - `Back -> 59`
    - `Left -> 61`
    - `Right -> 60`
  - `ETK[8]` cambia por cara:
    - `Front -> 5`
    - `Back -> 4`
    - `Left -> 3`
    - `Right -> 2`
  - `ETK[0]` parece seleccionar grupo de laterales:
    - `Front/Back -> 1073741824`
    - `Left/Right -> 2147483648`
  - `S6000M3` se emite una sola vez al entrar al primer taladro lateral; las
    cuatro brocas laterales comparten `spindle_speed_std = 6000`.
  - todos los taladros laterales bajan con `F2000`.
  - nueva hipotesis sobre feed de brocas:
    - el postprocesador parece usar el menor valor util entre `descent_speed`
      y `feed_rate`, multiplicado por `1000`.
    - para `058..061`: `min(2, 3) * 1000 = F2000`.
    - esto tambien explicaria por que `002..004` dieron `F1000`:
      `min(2, 1) * 1000 = F1000`.
- Regla geometrica ISO/PGMX:
  - las brocas laterales tienen `tool_offset_length = 65`.
  - el ISO desplaza `65 mm` sobre el eje de perforacion:
    - `Front`: `Y_iso = Y_pgmx - 65`
    - `Back`: `Y_iso = Y_pgmx + 65`, con `X_iso = -X_pgmx`
    - `Left`: `X_iso = X_pgmx - 65`, con `Y_iso = -Y_pgmx`
    - `Right`: `X_iso = X_pgmx + 65`
  - `Z` queda como altura local del agujero (`9 mm`, centro del espesor de
    `18 mm`).
  - la carrera ISO de perforacion mide `30 mm`, que corresponde a
    `security_plane 20 + target_depth 10`.
- Pendientes:
  - validar las mismas reglas con agujeros no centrados para separar claramente
    transformacion de cara, espejo de eje y offsets.
  - validar si `ETK[0]` siempre agrupa `Front/Back` y `Left/Right` de esta
    manera.

### Ronda 16 - Pieza 003 con dos taladros por cara lateral

- Solicitud:
  - sintetizar la misma pieza base:
    - `400 x 250 x 18`
    - origen fijo: `(5, 5, 25)`
  - agregar dos agujeros por cara:
    - `Front`
    - `Back`
    - `Left`
    - `Right`
- Archivo generado:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_003.pgmx`
- Criterio aplicado:
  - `D8 Flat`
  - no pasante
  - `target_depth = 10`
  - `tool_resolution = Auto`
  - por la regla corregida, `Auto` en `Front/Back/Left/Right` deja
    `ToolKey` vacio.
- Distribucion local pedida al sintetizador:

| Cara | Taladro | Centro local | Profundidad |
| --- | --- | --- | --- |
| `Front` | `Taladro_Frente_Izquierdo_D8` | `(120, 9)` | `10` |
| `Front` | `Taladro_Frente_Derecho_D8` | `(280, 9)` | `10` |
| `Back` | `Taladro_Posterior_Izquierdo_D8` | `(120, 9)` | `10` |
| `Back` | `Taladro_Posterior_Derecho_D8` | `(280, 9)` | `10` |
| `Left` | `Taladro_Izquierdo_Frontal_D8` | `(75, 9)` | `10` |
| `Left` | `Taladro_Izquierdo_Posterior_D8` | `(175, 9)` | `10` |
| `Right` | `Taladro_Derecho_Frontal_D8` | `(75, 9)` | `10` |
| `Right` | `Taladro_Derecho_Posterior_D8` | `(175, 9)` | `10` |

- Validacion local con `pgmx_snapshot`:
  - `piece_name = Pieza_003`
  - `length = 400`, `width = 250`, `depth = 18`
  - `origin = (5, 5, 25)`
  - `execution_fields = HG`
  - `features = 8`
  - `operations = 8`
  - `working_steps = 9` (`8` taladros + `XN`)
  - las ocho operaciones tienen:
    - `ToolKey.ID = 0`
    - `ToolKey.ObjectType = System.Object`
    - `ToolKey.Name = ""`
  - `sha256 = 32d3753908cde220015ef1fba171737e298c5e553c65db48bcf37627cda2df38`
- Trayectorias efectivas observadas:
  - `Front 120`: `Y=-20 -> 0 -> 10 -> -20`, `X=120`, `Z=9`
  - `Front 280`: `Y=-20 -> 0 -> 10 -> -20`, `X=280`, `Z=9`
  - `Back local 120`: `Y=270 -> 250 -> 240 -> 270`, `X=280`, `Z=9`
  - `Back local 280`: `Y=270 -> 250 -> 240 -> 270`, `X=120`, `Z=9`
  - `Left local 75`: `X=-20 -> 0 -> 10 -> -20`, `Y=175`, `Z=9`
  - `Left local 175`: `X=-20 -> 0 -> 10 -> -20`, `Y=75`, `Z=9`
  - `Right local 75`: `X=420 -> 400 -> 390 -> 420`, `Y=75`, `Z=9`
  - `Right local 175`: `X=420 -> 400 -> 390 -> 420`, `Y=175`, `Z=9`
- Proximo paso externo:
  - abrir `Pieza_003.pgmx` en la PC del CNC.
  - postprocesar y guardar el ISO como `pieza_003.iso`.
  - comparar el ISO para validar:
    - si `ETK[6]` se mantiene `58/59/61/60`
    - si `ETK[8]` sigue `5/4/3/2`
    - si el grupo `ETK[0]` se mantiene por par de caras
    - si los espejos de `Back` y `Left` quedan iguales con agujeros no
      centrados.

### Ronda 17 - ISO de Pieza 003 con dos taladros por cara

- Archivo analizado:
  - `P:\USBMIX\ProdAction\ISO\pieza_003.iso`
- Archivo de origen:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_003.pgmx`
- Propiedades del ISO:
  - `228` lineas
  - `3484` bytes
  - `sha256 = 850208ED7B12BF0D74C713D7302C0EB6EF62E5A734B6820AD734727027D7DC8E`
- Encabezado:
  - `% pieza_003.pgm`
  - `;H DX=405.000 DY=255.000 DZ=43.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0`
- Confirmaciones:
  - con dos taladros por cara, el postprocesador sigue agrupando por cara /
    herramienta.
  - el PGMX mantiene `ToolKey` vacio y el postprocesador vuelve a resolver:
    - `Front -> ETK[6] = 58`
    - `Back -> ETK[6] = 59`
    - `Left -> ETK[6] = 61`
    - `Right -> ETK[6] = 60`
  - `ETK[8]` se mantiene:
    - `Front -> 5`
    - `Back -> 4`
    - `Left -> 3`
    - `Right -> 2`
  - `ETK[0]` se mantiene por grupo:
    - `Front/Back -> 1073741824`
    - `Left/Right -> 2147483648`
  - `S6000M3` se emite una sola vez al entrar al primer grupo lateral.
  - todos los taladros laterales bajan con `F2000`.

| Cara | PGMX efectivo | ISO observado | Regla confirmada |
| --- | --- | --- | --- |
| `Front` | `X=120`, `Y -20 -> 0 -> 10`, `Z=9` | `G0 X120 Y-85`, `G1 Y-55 F2000` | `X_iso = X_pgmx`, `Y_iso = Y_pgmx - 65` |
| `Front` | `X=280`, `Y -20 -> 0 -> 10`, `Z=9` | `G0 X280 Y-85`, `G1 Y-55 F2000` | `X_iso = X_pgmx`, `Y_iso = Y_pgmx - 65` |
| `Back` | `X=280`, `Y 270 -> 250 -> 240`, `Z=9` | `G0 X-280 Y335`, `G1 Y305 F2000` | `X_iso = -X_pgmx`, `Y_iso = Y_pgmx + 65` |
| `Back` | `X=120`, `Y 270 -> 250 -> 240`, `Z=9` | `G0 X-120 Y335`, `G1 Y305 F2000` | `X_iso = -X_pgmx`, `Y_iso = Y_pgmx + 65` |
| `Left` | `X -20 -> 0 -> 10`, `Y=175`, `Z=9` | `G0 X-85 Y-175`, `G1 X-55 F2000` | `X_iso = X_pgmx - 65`, `Y_iso = -Y_pgmx` |
| `Left` | `X -20 -> 0 -> 10`, `Y=75`, `Z=9` | `G0 X-85 Y-75`, `G1 X-55 F2000` | `X_iso = X_pgmx - 65`, `Y_iso = -Y_pgmx` |
| `Right` | `X 420 -> 400 -> 390`, `Y=75`, `Z=9` | `G0 X485 Y75`, `G1 X455 F2000` | `X_iso = X_pgmx + 65`, `Y_iso = Y_pgmx` |
| `Right` | `X 420 -> 400 -> 390`, `Y=175`, `Z=9` | `G0 X485 Y175`, `G1 X455 F2000` | `X_iso = X_pgmx + 65`, `Y_iso = Y_pgmx` |

- Agrupacion y movimiento entre taladros:
  - `ETK[6]`, `ETK[8]`, `SHF` y `ETK[0]` se preparan una vez por grupo/cara,
    no por cada taladro individual.
  - en `Front` y `Back`, entre los dos taladros de la misma cara aparece un
    retorno a `G0 G53 Z201.000` antes de reposicionar.
  - en `Left` y `Right`, el reposicionamiento al segundo taladro se hace en el
    plano lateral de seguridad ya transformado:
    - `Left`: de `G0 X-85 Y-175 Z9` a `G0 X-85 Y-75 Z9`
    - `Right`: de `G0 X485 Y75 Z9` a `G0 X485 Y175 Z9`
- Lectura nueva:
  - el desplazamiento de `65 mm` sobre el eje de perforacion queda confirmado
    como efecto del `tool_offset_length` de las brocas laterales.
  - los espejos ya no dependen de que el agujero este centrado:
    - `Back` espeja `X`
    - `Left` espeja `Y`
    - `Front` conserva `X`
    - `Right` conserva `Y`
- Pendientes:
  - validar una altura distinta de `Z=9` para confirmar que el ISO conserva la
    altura local del taladro sin transformaciones adicionales.
  - validar si los retornos intermedios `G53 Z201` dependen de la orientacion
    de cara o de la distancia entre taladros.

### Ronda 18 - Pieza 004 con patrones superior horizontal y vertical

- Solicitud:
  - sintetizar una pieza de la misma serie ISO.
  - agregar dos patrones de huecos:
    - un patron con `3` huecos en linea horizontal separados `32 mm`
    - un patron con `3` huecos en linea vertical separados `32 mm`
- Supuesto aplicado:
  - como no se indico otra cara, se genero sobre `Top`.
  - se usaron huecos `D8 Flat` pasantes, con resolucion automatica vertical.
- Archivo generado:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_004.pgmx`
- Pieza:
  - `piece_name = Pieza_004`
  - `length = 400`
  - `width = 250`
  - `depth = 18`
  - `origin = (5, 5, 25)`
  - `execution_fields = HG`
- Distribucion local pedida al sintetizador:

| Patron | Taladro | Centro local | Separacion |
| --- | --- | --- | --- |
| Horizontal | `Patron_Horizontal_1_D8` | `(80, 80)` | inicio |
| Horizontal | `Patron_Horizontal_2_D8` | `(112, 80)` | `+32 mm` en `X` |
| Horizontal | `Patron_Horizontal_3_D8` | `(144, 80)` | `+32 mm` en `X` |
| Vertical | `Patron_Vertical_1_D8` | `(280, 80)` | inicio |
| Vertical | `Patron_Vertical_2_D8` | `(280, 112)` | `+32 mm` en `Y` |
| Vertical | `Patron_Vertical_3_D8` | `(280, 144)` | `+32 mm` en `Y` |

- Validacion local con `pgmx_snapshot`:
  - `features = 6`
  - `operations = 6`
  - `working_steps = 7` (`6` taladros + `XN`)
  - todas las features:
    - `plane = Top`
    - `diameter = 8`
    - `BottomCondition = ThroughHoleBottom`
    - `Depth = (18, 18)`
  - todas las operaciones:
    - `ToolKey = 1888 / 001`
    - `ObjectType = ScmGroup.XCam.ToolDataModel.Tool.CuttingTool`
  - trayectorias por taladro:
    - `Approach`: `Z 38 -> 18`
    - `TrajectoryPath`: `Z 18 -> 0`
    - `Lift`: `Z 0 -> 38`
  - `sha256 = d0c6463dad3857f49095465dd3348c7b9ca49a21856ccfd5dbe4eb400a6d34f9`
- Correccion posterior:
  - al abrir `Pieza_004.pgmx` en Maestro se verifico que no eran patrones
    reales, sino seis huecos individuales.
  - el caso manual corregido quedo guardado como
    `S:\Maestro\Projects\ProdAction\ISO\Pieza_004_Repeticiones.pgmx`.
  - ese archivo contiene `2` features `ReplicateFeature`:
    - patron horizontal `3 x 1`, base `(80, 80)`, separacion `32`
    - patron vertical `1 x 3`, base `(280, 80)`, separacion `32`
  - el sintetizador `.pgmx` fue corregido con `DrillingPatternSpec` para
    generar la misma semantica Maestro.
- Postprocesado recibido:
  - `P:\USBMIX\ProdAction\ISO\pieza_004.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_004_repeticiones.iso`
- Comparacion ISO:
  - ambos archivos tienen `146` lineas.
  - difieren solo en la primera linea de identificacion del programa:
    - `% pieza_004.pgm`
    - `% pieza_004_repeticiones.pgm`
  - al excluir esa primera linea, el cuerpo completo es identico.
  - `body_sha256 = 121e5a67127df90029275b9c69f55d254728a7e30aeb078ca468c3045e0babe6`
  - hash archivo completo `pieza_004.iso`:
    `3BF1E17DD1C8D803718BBEF2D7DD14226E09F356CD32949202BD2E19DBB3B06D`
  - hash archivo completo `pieza_004_repeticiones.iso`:
    `8299100F908C10D903EC96DD2F99226FEAF5C8013737366816454EC5362A6911`
- Conclusiones:
  - Maestro conserva la diferencia semantica en `.pgmx`: seis `RoundHole`
    individuales vs dos `ReplicateFeature`.
  - El postprocesador CNC no emite una instruccion ISO compacta de patron para
    este caso.
  - El ISO final queda expandido como seis ciclos/bloques equivalentes de
    taladrado con broca `001`.
  - Para sintesis `.pgmx` conviene seguir usando `DrillingPatternSpec` cuando
    el usuario pida patrones, porque conserva la intencion editable en Maestro;
    para el ISO final, por ahora no cambia el programa ejecutado.
- Bloques de taladrado ISO observados:
  - herramienta: `?%ETK[6]=1`, `?%ETK[17]=257`, `S6000M3`
  - coordenadas ejecutadas:
    - `(80, 80)`
    - `(112, 80)`
    - `(144, 80)`
    - `(280, 80)`
    - `(280, 112)`
    - `(280, 144)`
  - cada hueco ejecuta `G1 G9 Z77.000 F2000.000` y retorna a `G0 Z115.000`.

### Ronda 19 - Pieza 005 con patrones en caras laterales

- Solicitud:
  - sintetizar la siguiente pieza de la serie ISO.
  - agregar patrones de `3` columnas separadas `32 mm` en las caras:
    - `Front`
    - `Back`
    - `Left`
    - `Right`
- Archivo generado:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_005.pgmx`
- Pieza:
  - `piece_name = Pieza_005`
  - `length = 400`
  - `width = 250`
  - `depth = 18`
  - `origin = (5, 5, 25)`
  - `execution_fields = HG`
- Criterio aplicado:
  - `D8 Flat`
  - no pasante
  - `target_depth = 10`
  - `tool_resolution = Auto`
  - `ToolKey` queda vacio en todas las operaciones laterales.
- Distribucion local:

| Cara | Patron | Base local | Patron |
| --- | --- | --- | --- |
| `Front` | `Patron_Frente_D8_3x32` | `(168, 9)` | `3 x 1`, separacion `32` |
| `Back` | `Patron_Posterior_D8_3x32` | `(168, 9)` | `3 x 1`, separacion `32` |
| `Left` | `Patron_Izquierdo_D8_3x32` | `(93, 9)` | `3 x 1`, separacion `32` |
| `Right` | `Patron_Derecho_D8_3x32` | `(93, 9)` | `3 x 1`, separacion `32` |

- Validacion local con `pgmx_snapshot`:
  - `features = 4`
  - `operations = 4`
  - `working_steps = 5` (`4` patrones + `XN`)
  - todos los features son `ReplicateFeature`
  - todos los patrones son `RectangularPattern`
  - todos los `BaseFeature` son `RoundHole D8`
  - todas las profundidades son `10`
  - todas las operaciones tienen `ToolKey = 0 / System.Object / ""`
  - `sha256 = b4a71ed3bb52a050a87b313d6e3abb92ca54902486c438d04ded921fecc0a177`
- Validacion interna adicional:
  - `tools.pgmx_adapters.adapt_pgmx_path(...)` ahora reconoce estos
    `ReplicateFeature` como `DrillingPatternSpec`.
  - resultado sobre `Pieza_005.pgmx`:
    - `adapted = 4`
    - `unsupported = 0`
    - `ignored = 1`
    - `drilling_patterns = 4`
- Postprocesado recibido:
  - `P:\USBMIX\ProdAction\ISO\pieza_005.iso`
- Propiedades del ISO:
  - `286` lineas
  - `4437` bytes
  - `sha256 = 769409E52924529E5C165D953BD0572A40DE6C542C43AEC9E5CAEE15A5DC23AA`
  - encabezado:
    - `% pieza_005.pgm`
    - `;H DX=405.000 DY=255.000 DZ=43.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0`
- Confirmaciones:
  - Maestro/CNC acepto el `.pgmx` con `ReplicateFeature` en caras laterales y
    pudo postprocesarlo.
  - El postprocesador no emitio una instruccion compacta de patron: expandio
    los `4` patrones a `12` taladros individuales.
  - La agrupacion por cara/herramienta conserva las reglas de `Pieza_003`:
    - `Front -> ETK[6] = 58`, `ETK[8] = 5`
    - `Back -> ETK[6] = 59`, `ETK[8] = 4`
    - `Left -> ETK[6] = 61`, `ETK[8] = 3`
    - `Right -> ETK[6] = 60`, `ETK[8] = 2`
  - `ETK[0]` sigue agrupando por par de caras:
    - `Front/Back -> 1073741824`
    - `Left/Right -> 2147483648`
  - `S6000M3` se emite una sola vez al entrar al primer grupo lateral.
  - todos los taladros laterales bajan con `F2000`.

| Cara | ISO observado | Regla confirmada |
| --- | --- | --- |
| `Front` | `G0 X168 Y-85`, `G1 Y-55 F2000` | `X_iso = X_pgmx`, `Y_iso = -85/-55` |
| `Front` | `G0 X200 Y-85`, `G1 Y-55 F2000` | separacion `+32` en `X` |
| `Front` | `G0 X232 Y-85`, `G1 Y-55 F2000` | separacion `+32` en `X` |
| `Back` | `G0 X-232 Y335`, `G1 Y305 F2000` | `Back` espeja `X` y mantiene separacion `32` |
| `Back` | `G0 X-200 Y335`, `G1 Y305 F2000` | `ETK[0]` no se reemite; sigue grupo `Front/Back` |
| `Back` | `G0 X-168 Y335`, `G1 Y305 F2000` | patron expandido |
| `Left` | `G0 X-85 Y-157`, `G1 X-55 F2000` | `Left` espeja `Y` y mantiene separacion `32` |
| `Left` | `G0 X-85 Y-125`, `G1 X-55 F2000` | reposiciona dentro de la cara sin `G53 Z201` |
| `Left` | `G0 X-85 Y-93`, `G1 X-55 F2000` | patron expandido |
| `Right` | `G0 X485 Y93`, `G1 X455 F2000` | `Right` conserva `Y` y mantiene separacion `32` |
| `Right` | `G0 X485 Y125`, `G1 X455 F2000` | `ETK[0]` no se reemite; sigue grupo `Left/Right` |
| `Right` | `G0 X485 Y157`, `G1 X455 F2000` | patron expandido |

- Movimientos entre taladros:
  - en `Front` y `Back`, entre taladros de la misma cara aparece
    `G0 G53 Z201.000`.
  - en `Left` y `Right`, el reposicionamiento interno se hace en el plano
    lateral de seguridad, igual que en `Pieza_003`.
  - al cambiar de cara lateral aparecen movimientos de preparacion
    `G0 G53 Z149.500` o `G0 G53 Z149.450` segun herramienta/cara.

### Ronda 20 - Pieza 006 con ranura central superior

- Estado: postprocesado recibido y analizado; pendiente validar variantes de
  ranura.
- Solicitud:
  - continuar investigando ranurados.
  - sintetizar la siguiente pieza de la serie con una ranura central.
- Archivo generado:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_006.pgmx`
- Pieza:
  - `piece_name = Pieza_006`
  - `length = 400`
  - `width = 250`
  - `depth = 18`
  - `origin = (5, 5, 25)`
  - `execution_fields = HG`
- Ranura:
  - feature `Ranura_Central`
  - tipo `a:SlotSide`
  - cara `Top`
  - recorrido local `(50, 125) -> (350, 125)`
  - familia geometrica `LineHorizontal`
  - profundidad no pasante `10 mm`
  - herramienta sintetizada por default:
    - `ToolKey.ID = 1899`
    - `ToolKey.Name = 082`
    - `Sierra Vertical X`
  - ancho de herramienta `3.8`
- Validacion local con `pgmx_snapshot`:
  - `features = 1`
  - `operations = 1`
  - `working_steps = 2` (`Ranura_Central` + `Xn`)
  - bounding box de geometria `(50, 125, 350, 125)`
  - `sha256 = 6c505688db5c83b9488710b32508dfb64b58b213ac4ff32cf78f093e62b171be`
- Validacion interna adicional:
  - `tools.pgmx_adapters.adapt_pgmx_path(...)` reconoce la ranura como
    `SlotMillingSpec`.
  - resultado sobre `Pieza_006.pgmx`:
    - `adapted = 1`
    - `unsupported = 0`
    - `ignored = 1`
    - `slot_millings = 1`
- Postprocesado recibido:
  - `P:\USBMIX\ProdAction\ISO\pieza_006.iso`
- Propiedades del ISO:
  - `92` lineas
  - `1309` bytes
  - `sha256 = B11BC08C69BFBF5996D36E01301CAE1EF1E79420DA4B7AAEC13D66DE7ED6B341`
  - encabezado:
    - `% pieza_006.pgm`
    - `;H DX=405.000 DY=255.000 DZ=43.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0`
- Bloque ISO observado para la ranura:
  - seleccion de herramienta:
    - `?%ETK[6]=82`
    - `G17`
    - `?%ETK[17]=257`
    - `S4000M3`
    - `?%ETK[1]=16`
  - offsets antes del corte:
    - `SHF[X]=-96.000`
    - `SHF[Y]=126.950`
    - `SHF[Z]=22.150`
  - recorrido:
    - `G0 X350.000 Y125.000`
    - `G0 Z80.000`
    - `D1`
    - `SVL 60.000` / `VL6=60.000`
    - `SVR 1.900` / `VL7=1.900`
    - `G1 Z-10.000 F2000.000`
    - `?%ETK[7]=1`
    - `G1 X50.000 Z-10.000 F5000.000`
    - `G0 Z20.000`
    - `D0`
    - reset de `SVL/SVR` y `?%ETK[7]=0`
- Relacion PGMX -> ISO confirmada en este caso:
  - `ToolKey.Name = 082` se emite como `?%ETK[6]=82`.
  - `tool_width = 3.8` se emite como `SVR = 1.900`
    (`tool_width / 2`).
  - `end_radius = 60` se emite como `SVL = 60.000`.
  - `target_depth = 10` se emite como `G1 Z-10.000`.
  - el punto de aproximacion usa el extremo derecho de la ranura:
    `X350 Y125`.
  - el avance de corte va de `X350` a `X50`, aunque la geometria PGMX fue
    definida como `(50, 125) -> (350, 125)`.
- Conclusiones provisorias:
  - una `SlotSide` horizontal superior valida no se postprocesa como fresado
    lineal generico: usa variables especificas de ranura/sierra (`D1`, `SVL`,
    `SVR`, `ETK[7]`).
  - el ISO conserva coordenadas locales de la pieza para `X/Y` y expresa la
    profundidad de ranura como `Z` negativo.
  - el sentido de corte no queda gobernado por el orden de puntos PGMX en los
    dos casos estudiados; ver `Pieza_007`.
  - aclaracion operativa: esto no es una inversion arbitraria del
    postprocesador. La herramienta es una sierra con dientes que giran en un
    unico sentido, y el corte debe hacerse en el sentido observado para no
    dañar la superficie de la placa.
- Pendientes directos:
  - generar una variante cambiando `side_of_feature` para comprobar si cambia
    el lado de compensacion o los offsets.
  - variar largo/profundidad para confirmar que `SVL` y `Z` escalan como
    `end_radius` y `target_depth`.

### Ronda 21 - Pieza 007 con ranura central en sentido inverso

- Estado: postprocesado recibido y analizado.
- Solicitud:
  - generar la variante de `Pieza_006` con la ranura definida en sentido
    inverso.
- Archivo generado:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_007.pgmx`
- Pieza:
  - `piece_name = Pieza_007`
  - `length = 400`
  - `width = 250`
  - `depth = 18`
  - `origin = (5, 5, 25)`
  - `execution_fields = HG`
- Ranura:
  - feature `Ranura_Central_Inversa`
  - tipo `a:SlotSide`
  - cara `Top`
  - recorrido local pedido `(350, 125) -> (50, 125)`
  - familia geometrica `LineHorizontal`
  - bounding box de geometria `(50, 125, 350, 125)`
  - profundidad no pasante `10 mm`
  - herramienta sintetizada por default:
    - `ToolKey.ID = 1899`
    - `ToolKey.Name = 082`
    - `Sierra Vertical X`
  - ancho de herramienta `3.8`
  - `end_radius = 60`
- Validacion local con `pgmx_snapshot`:
  - `features = 1`
  - `operations = 1`
  - `working_steps = 2` (`Ranura_Central_Inversa` + `Xn`)
  - `sha256 = cebb68e0da68d862369bf149e925f55904381da7f91083fded9f02ab6392850d`
- Validacion interna adicional:
  - `tools.pgmx_adapters.adapt_pgmx_path(...)` reconoce la ranura como
    `SlotMillingSpec`.
  - resultado sobre `Pieza_007.pgmx`:
    - `adapted = 1`
    - `unsupported = 0`
    - `ignored = 1`
    - `slot_millings = 1`
  - el spec adaptado conserva el sentido inverso:
    - `start = (350, 125)`
    - `end = (50, 125)`
- Postprocesado recibido:
  - `P:\USBMIX\ProdAction\ISO\pieza_007.iso`
- Propiedades del ISO:
  - `92` lineas
  - `1309` bytes
  - `sha256 = AF9C74659EF1605CA6384C6ACD26DF50735A467B08740E38CF089AEB50C4CB6B`
  - encabezado:
    - `% pieza_007.pgm`
    - `;H DX=405.000 DY=255.000 DZ=43.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0`
- Comparacion contra `pieza_006.iso`:
  - la unica diferencia de archivo completo es la primera linea:
    - `% pieza_006.pgm`
    - `% pieza_007.pgm`
  - desde la linea `2` hasta `M2`, el cuerpo ISO es identico.
  - `body_sha256_normalizado = 189AAA1F272AA17965C30A9D0ABEC625BE2C80950052CC35D8730405DCBC2DF4`
- Confirmacion:
  - `Pieza_006.pgmx` se adapto como `start = (50, 125)`,
    `end = (350, 125)`.
  - `Pieza_007.pgmx` se adapto como `start = (350, 125)`,
    `end = (50, 125)`.
  - a pesar de esa diferencia PGMX, ambos ISO ejecutan la ranura igual:
    - aproxima en `G0 X350.000 Y125.000`
    - baja en `G1 Z-10.000 F2000.000`
    - corta con `G1 X50.000 Z-10.000 F5000.000`
- Conclusion:
  - para una `SlotSide` horizontal superior con `Sierra Vertical X`, al menos
    en esta geometria, el postprocesador no respeta el orden de puntos PGMX
    como direccion de corte.
  - el postprocesador normaliza el corte al sentido `derecha -> izquierda`
    (`X mayor -> X menor`).
  - esta direccion unica responde a la rotacion de la sierra: los dientes
    cortan correctamente en un solo sentido y el recorrido observado evita
    dañar la superficie de la placa.
  - si se necesita cambiar el lado mecanizado, la siguiente variable a estudiar
    es `side_of_feature`/compensacion, no el sentido de la linea.

### Ronda 22 - Variantes `SideOfFeature` para ranura central

- Estado: postprocesados recibidos y analizados.
- Solicitud:
  - sintetizar cuatro variantes:
    - dos basadas en la geometria de `Pieza_006`
    - dos basadas en la geometria invertida de `Pieza_007`
    - correccion derecha e izquierda en cada par.
- Objetivo de la prueba:
  - confirmar si `SideOfFeature = Right/Left` modifica compensacion, offsets o
    lado mecanizado en el ISO.
  - no se espera que cambie el sentido de corte, porque ya quedo aclarado que
    la `Sierra Vertical X` impone un unico sentido por rotacion de dientes.

| Archivo | Base geometrica | Recorrido PGMX | `SideOfFeature` | Feature | SHA256 |
| --- | --- | --- | --- | --- | --- |
| `Pieza_008.pgmx` | `Pieza_006` | `(50, 125) -> (350, 125)` | `Right` | `Ranura_Central_006_Correccion_Derecha` | `c918f5c5a7b2c5ab02aeee70a9bd94f771936e5f2bd5b580d02bf83f0346878b` |
| `Pieza_009.pgmx` | `Pieza_006` | `(50, 125) -> (350, 125)` | `Left` | `Ranura_Central_006_Correccion_Izquierda` | `07f4c67fd6c22f86c2c788e895bd1aad950eeead8a4111b031abdfe6e6523689` |
| `Pieza_010.pgmx` | `Pieza_007` | `(350, 125) -> (50, 125)` | `Right` | `Ranura_Central_007_Correccion_Derecha` | `81fe3ccaf1dc675f1077b79d64f95374add36b812e866a2c599086efc92e3570` |
| `Pieza_011.pgmx` | `Pieza_007` | `(350, 125) -> (50, 125)` | `Left` | `Ranura_Central_007_Correccion_Izquierda` | `07a2df0b9e641aa8f6cd0a01003d1564cfce19b3f4cf48abcc1105b351e1430c` |

- Parametros comunes:
  - `length = 400`
  - `width = 250`
  - `depth = 18`
  - `origin = (5, 5, 25)`
  - `execution_fields = HG`
  - `target_depth = 10`
  - herramienta `1899 / 082` (`Sierra Vertical X`)
  - `tool_width = 3.8`
  - `end_radius = 60`
- Validacion local con `pgmx_snapshot`:
  - cada archivo tiene:
    - `features = 1`
    - `operations = 1`
    - `working_steps = 2` (`ranura` + `Xn`)
    - feature `a:SlotSide` en `Top`
    - bounding box `(50, 125, 350, 125)`
- Validacion interna adicional:
  - `tools.pgmx_adapters.adapt_pgmx_path(...)` reconoce cada archivo como
    `SlotMillingSpec`.
  - en los cuatro casos:
    - `adapted = 1`
    - `unsupported = 0`
    - `ignored = 1`
    - `slot_millings = 1`
  - el spec adaptado conserva el recorrido y `SideOfFeature` solicitado.
- Postprocesados recibidos:
  - `P:\USBMIX\ProdAction\ISO\pieza_008.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_009.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_010.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_011.iso`
- Propiedades:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | --- | --- | --- | --- |
| `pieza_008.iso` | `92` | `1309` | `19F56F9450382FB13C444C7C1139A56F219E01FB470CA2E7BEEE4EE11BE296A4` | `B079C318B78BB42F699C55BC7DE968E8ED46A0963AF7A7FE319A2F00A4EB29BD` |
| `pieza_009.iso` | `92` | `1309` | `AC181F9E8E881BF35D9C0DD645255AA175DCBECF816966CCD92BFAAD39F21DB8` | `6519CED4E90827FB3322F40DB90E5D6BDFCCEDB4059B205AD91A83CB074DC37B` |
| `pieza_010.iso` | `92` | `1309` | `F93AB3385C3873ED832D9B473C6637EDA52734ADA7095EBF0EE5352417280EB6` | `6519CED4E90827FB3322F40DB90E5D6BDFCCEDB4059B205AD91A83CB074DC37B` |
| `pieza_011.iso` | `92` | `1309` | `2BB13074E7D5A5E480DE1AA37E9FD0F6B2BC8EBC5C1DEFDEFE7917DD6EA1D7AE` | `B079C318B78BB42F699C55BC7DE968E8ED46A0963AF7A7FE319A2F00A4EB29BD` |

- Comparacion contra `Center` (`pieza_006.iso` / `pieza_007.iso`):
  - todas las diferencias quedan concentradas en la linea `44`, ademas del
    nombre de programa de la linea `1`.
  - `SHF[X/Y/Z]` no cambia.
  - `ETK` no cambia.
  - `SVL/SVR` no cambia.
  - `D1` no cambia.
  - profundidad y avance no cambian.
  - el sentido de corte sigue siendo `X350 -> X50`.
- Linea de aproximacion/corte:

| ISO | Base PGMX | `SideOfFeature` | Linea 44 ISO |
| --- | --- | --- | --- |
| `pieza_006.iso` | `(50, 125) -> (350, 125)` | `Center` | `G0 X350.000 Y125.000` |
| `pieza_007.iso` | `(350, 125) -> (50, 125)` | `Center` | `G0 X350.000 Y125.000` |
| `pieza_008.iso` | `(50, 125) -> (350, 125)` | `Right` | `G0 X350.000 Y123.100` |
| `pieza_009.iso` | `(50, 125) -> (350, 125)` | `Left` | `G0 X350.000 Y126.900` |
| `pieza_010.iso` | `(350, 125) -> (50, 125)` | `Right` | `G0 X350.000 Y126.900` |
| `pieza_011.iso` | `(350, 125) -> (50, 125)` | `Left` | `G0 X350.000 Y123.100` |

- Equivalencias:
  - `pieza_008.iso` y `pieza_011.iso` tienen cuerpo ISO identico desde la linea
    `2`.
  - `pieza_009.iso` y `pieza_010.iso` tienen cuerpo ISO identico desde la linea
    `2`.
- Regla inferida:
  - `SideOfFeature` desplaza la trayectoria en `Y` por `tool_width / 2`.
  - con `tool_width = 3.8`, el desplazamiento observado es `1.9 mm`.
  - `Center` queda en `Y125.000`.
  - para geometria `(50, 125) -> (350, 125)`:
    - `Right` desplaza a `Y123.100`
    - `Left` desplaza a `Y126.900`
  - para geometria invertida `(350, 125) -> (50, 125)`, el signo se invierte:
    - `Right` desplaza a `Y126.900`
    - `Left` desplaza a `Y123.100`
  - el desplazamiento se calcula respecto del sentido geometrico de la linea
    PGMX, aunque el postprocesador luego normalice el sentido fisico de corte
    por la sierra.
- Conclusion:
  - `SideOfFeature` si controla el lado de compensacion de la ranura.
  - no modifica la direccion de corte.
  - para obtener la misma trayectoria compensada, se puede usar:
    - geometria normal + `Right` = geometria invertida + `Left`
    - geometria normal + `Left` = geometria invertida + `Right`
  - por claridad, conviene emitir ranuras con un sentido geometrico consistente
    y elegir `SideOfFeature` segun el lado real que se quiera mecanizar.

### Ronda 23 - Piezas 012 a 014 con taladro D8 y profundidades variables

- Estado: postprocesados recibidos y analizados.
- Solicitud:
  - sintetizar tres ejemplos de piezas con huecos de `8 mm`:
    - `Profundidad = 15 mm`
    - `Profundidad pasante Extra = 0`
    - `Profundidad pasante Extra = 1`
- Parametros comunes:
  - pieza `400 x 250 x 18`
  - origen `(5, 5, 25)`
  - centro del taladro superior `(200, 125)`
  - diametro `8`
  - herramienta resuelta automaticamente `1888 / 001`
  - `security_plane = 20`

| Archivo | Feature | Configuracion de profundidad | BottomCondition | Depth XML | TrajectoryPath | SHA256 |
| --- | --- | --- | --- | --- | --- | --- |
| `Pieza_012.pgmx` | `Hueco_D8_Profundidad_15` | no pasante, `target_depth = 15` | `FlatHoleBottom` | `15 / 15` | `8 0 15` | `f974eebbd337d585a7f9275ad7f395c6590437bbfa6e1c022d73673f4936155d` |
| `Pieza_013.pgmx` | `Hueco_D8_Pasante_Extra_0` | pasante, `extra_depth = 0` | `ThroughHoleBottom` | `18 / 18` | `8 0 18` | `cd59b1f946cdce3a61e20bada273caea6663a6444b821561f3848290ff56c9c0` |
| `Pieza_014.pgmx` | `Hueco_D8_Pasante_Extra_1` | pasante, `extra_depth = 1` | `ThroughHoleBottom` | `18 / 18` | `8 0 19` | `a9b58f5d8f6120e89b038afa7f6a8d2653b73dca0b5760354d86e8c01f0100e1` |

- Validacion local con `pgmx_snapshot`:
  - cada archivo tiene:
    - `features = 1`
    - `operations = 1`
    - `working_steps = 2` (`taladro` + `Xn`)
    - feature `a:RoundHole` en `Top`
    - operation `a:DrillingOperation`
  - `Pieza_012`:
    - `depth_spec = is_through=False, target_depth=15, extra_depth=0`
  - `Pieza_013`:
    - `depth_spec = is_through=True, target_depth=None, extra_depth=0`
  - `Pieza_014`:
    - `depth_spec = is_through=True, target_depth=None, extra_depth=1`
- Mejora aplicada al lector:
  - `tools/pgmx_snapshot.py` ahora infiere `extra_depth` de taladros pasantes
    desde la longitud del `TrajectoryPath` cuando `OvercutLength` queda en
    `0`.
  - Esto es necesario porque en `RoundHole` pasante el `Extra` no se guarda
    como `OvercutLength`; queda expresado en la trayectoria efectiva:
    - `Extra = 0` -> `TrajectoryPath = 18`
    - `Extra = 1` -> `TrajectoryPath = 19`
- Postprocesados recibidos:
  - `P:\USBMIX\ProdAction\ISO\pieza_012.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_013.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_014.iso`
- Propiedades ISO:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | --- | --- | --- | --- |
| `pieza_012.iso` | `86` | `1253` | `AAF48A35BC17938314A1148AB136C800978FC8ED2E8105E3D10C795311683A14` | `3CBF8ECE53DBD0A181B11CAF7E778FFB072AFBFF748B8B939D3D3F1171F1E8AD` |
| `pieza_013.iso` | `86` | `1253` | `813CF0F0B7B44EC9AFCF2B52BB0A3A428B426182E875DE883DD472223504FEBD` | `FA5E2969223E658B5C78077A73DB85FD059333A207ECFAF5F7C91FEA5C61C99B` |
| `pieza_014.iso` | `86` | `1253` | `30D7CAA3B8ACCA9B7CF8FA15AEA439F5847A213A89364C3C00BFFB7CF4D8903D` | `FA5E2969223E658B5C78077A73DB85FD059333A207ECFAF5F7C91FEA5C61C99B` |

- Bloque comun de taladro:
  - `G17`
  - `?%ETK[6]=1`
  - `?%ETK[17]=257`
  - `S6000M3`
  - `?%ETK[0]=1`
  - `G0 X200.000 Y125.000`
  - `G0 Z115.000`
  - `?%ETK[7]=3`
  - `MLV=2`
  - retorno `G0 Z115.000`
- Diferencia de profundidad ISO:

| PGMX | Configuracion | Trayectoria PGMX | Corte ISO |
| --- | --- | --- | --- |
| `Pieza_012.pgmx` | no pasante `15 mm` | `TrajectoryPath = 15` | `G1 G9 Z80.000 F2000.000` |
| `Pieza_013.pgmx` | pasante `Extra = 0` | `TrajectoryPath = 18` | `G1 G9 Z77.000 F2000.000` |
| `Pieza_014.pgmx` | pasante `Extra = 1` | `TrajectoryPath = 19` | `G1 G9 Z77.000 F2000.000` |

- Comparacion:
  - `pieza_012.iso` difiere de `pieza_013.iso` solo en:
    - linea `1`: nombre del programa
    - linea `50`: `Z80.000` vs `Z77.000`
  - `pieza_013.iso` y `pieza_014.iso` son identicos despues de la primera
    linea.
- Regla inferida:
  - para taladro vertical D8 con herramienta `001`, el no pasante se emite
    como una cota ISO proporcional a la profundidad efectiva:
    - `15 mm` sobre placa de `18 mm` -> `Z80`
    - pasante `18 mm` -> `Z77`
  - en este caso, el `Extra = 1` del PGMX no modifica el ISO final.
  - el PGMX de `Pieza_014` si conserva el sobrepaso (`TrajectoryPath = 19`),
    pero el postprocesador emite el mismo cuerpo que `Extra = 0`.
- Conclusion:
  - `target_depth` no pasante si afecta la cota de taladrado ISO.
  - `ThroughHoleBottom + Extra = 1` no produjo cambio ISO frente a
    `ThroughHoleBottom + Extra = 0` para D8/001 en esta muestra.
  - queda pendiente investigar si el postprocesador ignora siempre el `Extra`
    en taladros verticales o si depende de herramienta, familia de broca,
    diametro o configuracion interna de Maestro/CNC.

### Ronda 24 - Pieza 015 con fresado lineal vertical E004 central

- Estado: postprocesado recibido y analizado.
- Solicitud:
  - pasar a estudiar fresados sobre polilineas.
  - sintetizar una pieza con un fresado de linea vertical.
  - usar fresa `E004`, correccion central y profundidad `15 mm`.
- Archivo generado:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_015.pgmx`
- Pieza:
  - `piece_name = Pieza_015`
  - `length = 400`
  - `width = 250`
  - `depth = 18`
  - `origin = (5, 5, 25)`
  - `execution_fields = HG`
- Fresado:
  - spec publica: `LineMillingSpec`
  - feature `Fresado_Linea_Vertical_E004_Central_P15`
  - feature type `a:GeneralProfileFeature`
  - operation type `a:BottomAndSideFinishMilling`
  - plano `Top`
  - geometria nominal `(200, 50) -> (200, 200)`
  - familia geometrica `LineVertical`
  - `SideOfFeature = Center`
  - herramienta `1903 / E004`
  - `tool_width = 4.0`
  - profundidad no pasante `15 mm`
  - `BottomCondition = GeneralMillingBottom`
  - `Depth.StartDepth = 15`
  - `Depth.EndDepth = 15`
- Toolpaths sintetizados:
  - `Approach = 8 0 35 | 1 200 50 38 0 0 -1`
  - `TrajectoryPath = 8 0 150 | 1 200 50 3 0 1 0`
  - `Lift = 8 0 35 | 1 200 200 3 0 0 1`
  - la cota efectiva del fresado queda en `Z = 3`, porque
    `depth 18 - target_depth 15 = 3`.
- Validacion local con `pgmx_snapshot`:
  - `features = 1`
  - `operations = 1`
  - `working_steps = 2` (`Fresado_Linea_Vertical_E004_Central_P15` + `Xn`)
  - bounding box `(200, 50, 200, 200)`
  - `sha256 = d96e8edd99fafff80d5eb1588df8408467fd80de4314393b7cb383a0902b41ef`
- Validacion interna adicional:
  - `tools.pgmx_adapters.adapt_pgmx_path(...)` reconoce el caso como
    `LineMillingSpec`.
  - resultado sobre `Pieza_015.pgmx`:
    - `adapted = 1`
    - `unsupported = 0`
    - `ignored = 1`
    - `line_millings = 1`
- Postprocesado recibido:
  - `P:\USBMIX\ProdAction\ISO\pieza_015.iso`
- Propiedades del ISO:
  - `96` lineas
  - `1344` bytes
  - `sha256 = 6AB983FBAC156EB9513E395A212565A4BE7D2C65BB568AB1BE90F9B6A50071DB`
  - `body_sha256_normalizado = D4216233FB1D7508A23E52898B4FBE5DABDF45B378DD65914B382DC4E3FD94D0`
  - encabezado:
    - `% pieza_015.pgm`
    - `;H DX=405.000 DY=255.000 DZ=43.000 BX=0.000 BY=0.000 BZ=0.000 -HG V=0 *MM C=0 T=0`
- Bloque ISO observado:
  - cambio de herramienta:
    - `T4`
    - `SYN`
    - `M06`
  - seleccion/estado:
    - `?%ETK[6]=1`
    - `?%ETK[9]=4`
    - `?%ETK[18]=1`
    - `S18000M3`
    - `G17`
    - `?%ETK[13]=1`
  - offsets de herramienta:
    - `SHF[X]=32.050`
    - `SHF[Y]=-246.650`
    - `SHF[Z]=-125.300`
  - recorrido:
    - `G0 X200.000 Y50.000`
    - `G0 Z127.200`
    - `D1`
    - `SVL 107.200` / `VL6=107.200`
    - `SVR 2.000` / `VL7=2.000`
    - `G1 Z-15.000 F2000.000`
    - `?%ETK[7]=4`
    - `G1 Y200.000 Z-15.000 F5000.000`
    - `G0 Z20.000`
    - `D0`
    - reset de `SVL/SVR` y `?%ETK[7]=0`
- Relacion PGMX/catalogo -> ISO:
  - `ToolKey.Name = E004`, `ToolKey.ID = 1903`
  - catalogo:
    - `holder_key = 004`
    - `diameter = 4`
    - `tool_offset_length = 107.2`
    - `feed_rate_std = 5`
    - `descent_speed_std = 2`
    - `spindle_speed_std = 18000`
  - ISO:
    - `T4` y `?%ETK[9]=4` corresponden al portaherramienta `004`
    - `S18000M3` corresponde al spindle estandar de E004
    - `SVL = 107.200` corresponde a `tool_offset_length`
    - `SVR = 2.000` corresponde a `tool_width / 2`
    - bajada `F2000` corresponde a `descent_speed_std = 2 m/min`
    - avance `F5000` corresponde a `feed_rate_std = 5 m/min`
  - el `TrajectoryPath` PGMX trabaja a `Z = 3` (`18 - 15`), pero el ISO
    expresa la profundidad como `Z-15.000`.
- Conclusiones provisorias:
  - el fresado lineal con E004 no se emite como ranura `SlotSide`; usa cambio
    real de herramienta `T4/M06`.
  - comparte con ranuras el uso de `D1`, `SVL`, `SVR` y `?%ETK[7]`, pero con
    valores y flags propios de fresa:
    - ranura sierra: `?%ETK[7]=1`
    - linea E004: `?%ETK[7]=4`
  - las coordenadas `X/Y` del recorrido ISO coinciden con la geometria nominal:
    entra en `(200, 50)` y avanza hasta `Y=200`.
  - la profundidad ISO de fresado lineal no pasante se expresa como valor
    negativo absoluto: `target_depth = 15` -> `Z-15`.
  - `SVL` para E004 parece venir del `tool_offset_length`, no del largo de la
    trayectoria ni de la profundidad.
- Proximo paso:
  - generar una polilinea abierta de dos segmentos con E004 y profundidad
    `15 mm` para ver si el postprocesador mantiene un unico bloque continuo o
    parte el recorrido en varios avances.
  - luego variar `SideOfFeature` para fresado lineal/polilinea y confirmar si
    la compensacion se emite como desplazamiento de trayectoria igual que en
    `SlotSide`.

### Ronda 25 - Piezas 016 y 017 con polilinea E004 izquierda/derecha

- Estado: postprocesado Maestro/CNC recibido y analizado.
- Solicitud:
  - hacer dos variantes del fresado sobre polilinea:
    - por izquierda
    - por derecha
- Archivos generados:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_016.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_017.pgmx`
- Parametros comunes:
  - pieza `400 x 250 x 18`
  - origen `(5, 5, 25)`
  - spec publica `PolylineMillingSpec`
  - feature type `a:GeneralProfileFeature`
  - operation type `a:BottomAndSideFinishMilling`
  - plano `Top`
  - polilinea abierta en dos segmentos:
    - `(150, 50) -> (150, 125) -> (250, 125)`
  - herramienta `1903 / E004`
  - `tool_width = 4.0`
  - profundidad no pasante `15 mm`
  - cota efectiva de trayectoria `Z = 3`

| Archivo | Feature | `SideOfFeature` | SHA256 |
| --- | --- | --- | --- |
| `Pieza_016.pgmx` | `Fresado_Polilinea_E004_Izquierda_P15` | `Left` | `d341ccc12e9a301f1bad3b47ff81e4f5e34585c96cf3df771c484119ad59f077` |
| `Pieza_017.pgmx` | `Fresado_Polilinea_E004_Derecha_P15` | `Right` | `631e91659847e2b18344404d774472d0e3d5b0f1cab892b4bc6cc627a3a9956e` |

- Validacion local con `pgmx_snapshot`:
  - cada archivo tiene:
    - `features = 1`
    - `operations = 1`
    - `working_steps = 2`
    - feature `a:GeneralProfileFeature` en `Top`
    - familia geometrica `OpenPolyline`
    - bounding box nominal `(150, 50, 250, 125)`
  - `tools.pgmx_adapters.adapt_pgmx_path(...)` reconoce ambos como
    `PolylineMillingSpec`.
  - en ambos casos:
    - `adapted = 1`
    - `unsupported = 0`
    - `ignored = 1`
    - `polyline_millings = 1`
- Toolpath compensado observado en PGMX:
  - `Pieza_016` / `Left`:
    - `Approach = 8 0 35 | 1 148 50 38 0 0 -1`
    - `TrajectoryPath` compuesto:
      - linea `8 0 75 | 1 148 50 3 0 1 0`
      - arco `8 3.1415926535897931 4.7123889803846897 | 2 150 125 3 0 0 -1 1 0 0 0 -1 0 2`
      - linea `8 0 100 | 1 150 127 3 1 0 0`
    - `Lift = 8 0 35 | 1 250 127 3 0 0 1`
  - `Pieza_017` / `Right`:
    - `Approach = 8 0 35 | 1 152 50 38 0 0 -1`
    - `TrajectoryPath` compuesto:
      - linea `8 0 73 | 1 152 50 3 0 1 0`
      - linea `8 0 98 | 1 152 123 3 1 0 0`
    - `Lift = 8 0 35 | 1 250 123 3 0 0 1`
- Lectura geometrica:
  - `Left` desplaza el primer tramo a `X148` y el segundo a `Y127`.
  - al quedar del lado exterior de la esquina, el sintetizador genera un arco
    de radio `2 mm` en torno al vertice nominal `(150, 125)`.
  - `Right` desplaza el primer tramo a `X152` y el segundo a `Y123`.
  - en ese lado, los tramos compensados se encuentran directamente en
    `(152, 123)`, sin arco intermedio.
- Archivos ISO analizados:
  - `P:\USBMIX\ProdAction\ISO\pieza_016.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_017.iso`
- Propiedades ISO:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | ---: | ---: | --- | --- |
| `pieza_016.iso` | `102` | `1493` | `BDD4C3D51CD9807869FA93C70D8C7C26B61F55507246CB248372F7749ECA1BD2` | `F0793419E2767610F9E4C296609D1D7A958CD29C5A23EF740568B9CE33531ECF` |
| `pieza_017.iso` | `102` | `1493` | `1364B1923A461B3DCDE45A07FDEC4293A4CE5D9E5425E40E1A91F993949B78C3` | `DBDEB87A1893DB29B84BE95D71BF329C64E1DD36E6EF2DB2BBD4459F7C516187` |

- Comparacion ISO:
  - despues del nombre de programa, la unica diferencia de cuerpo es la linea
    `58`.
  - `pieza_016.iso` (`SideOfFeature = Left`) emite `G41`.
  - `pieza_017.iso` (`SideOfFeature = Right`) emite `G42`.
  - el resto del bloque de corte es identico.
- Bloque comun observado:
  - `T4`, `M06`, `?%ETK[9]=4`, `?%ETK[18]=1`, `S18000M3`
  - `SHF[X]=32.050`, `SHF[Y]=-246.650`, `SHF[Z]=-125.300`
  - `G0 X150.000 Y49.000`
  - `D1`
  - `SVL 107.200`
  - `SVR 2.000`
  - `G1 X150.000 Y50.000 Z20.000 F2000.000`
  - `G1 Z-15.000 F2000.000`
  - `G1 Y125.000 Z-15.000 F5000.000`
  - `G1 X250.000 Z-15.000 F5000.000`
  - `G1 Z20.000 F5000.000`
  - `G40`
  - `G1 X251.000 Y125.000 Z20.000 F5000.000`
- Relacion PGMX -> ISO:
  - el PGMX contiene trayectorias compensadas explicitamente en el
    `TrajectoryPath`:
    - `Left`: offsets `X148`/`Y127` y arco exterior de radio `2 mm`.
    - `Right`: offsets `X152`/`Y123` y esquina directa.
  - el ISO no emite esas coordenadas compensadas ni emite `G2/G3` para el arco
    de `Left`.
  - el postprocesador vuelve al contorno nominal
    `(150, 50) -> (150, 125) -> (250, 125)` y delega la compensacion al control
    CNC mediante:
    - `G41` para izquierda
    - `G42` para derecha
    - `SVR 2.000` como radio de herramienta
  - la entrada/salida agregada por el postprocesador es de `1 mm`:
    - aproximacion `G0 X150.000 Y49.000`
    - entrada `G1 X150.000 Y50.000`
    - salida `G1 X251.000 Y125.000`
- Conclusiones provisorias:
  - en fresado E004 sobre polilinea abierta, `SideOfFeature` si llega al ISO,
    pero no como desplazamiento geometrico en `X/Y`; llega como compensacion
    de herramienta `G41/G42`.
  - a diferencia de las ranuras `SlotSide`, donde la compensacion aparecio como
    desplazamiento numerico de la trayectoria, en `GeneralProfileFeature` con
    E004 la compensacion queda dinamica en el CNC.
  - el ISO conserva un unico bloque continuo para la polilinea y no separa los
    dos tramos.
  - para validar el resultado fisico de la esquina, hay que observar como el
    control CNC resuelve `G41/G42` sobre el vertice nominal.

### Ronda 26 - Piezas 018 y 019 con escuadrado E001 pasante Extra 1

- Estado: PGMX corregidos sin acercamiento/alejamiento y nuevos ISO
  postprocesados analizados. El primer analisis ISO de esta ronda queda como
  historico de la version anterior con `Arc + Quote`.
- Solicitud:
  - sintetizar dos variantes de escuadrado exterior:
    - una antihoraria
    - una horaria
  - usar fresa `E001`
  - profundidad pasante con `Extra = 1`
- Archivos generados:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_018.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_019.pgmx`
- Parametros comunes:
  - pieza `400 x 250 x 18`
  - origen `(5, 5, 25)`
  - spec publica `SquaringMillingSpec`
  - `start_edge = Bottom`
  - plano `Top`
  - geometria nominal `ClosedPolylineMidEdgeStart`
  - bounding box nominal `(0, 0, 400, 250)`
  - herramienta `1900 / E001`
  - `tool_width = 18.36`
  - profundidad pasante `Extra = 1`
  - `BottomCondition = ThroughMillingBottom`
  - `Depth.StartDepth/EndDepth = 18 / 18`
  - `OvercutLength = 1`
  - `Approach = Arc + Quote`
  - `Retract = Arc + Quote`

| Archivo | Feature | Winding | `SideOfFeature` | SHA256 |
| --- | --- | --- | --- | --- |
| `Pieza_018.pgmx` | `Escuadrado_Antihorario_E001_Pasante_Extra1` | `CounterClockwise` | `Right` | `42ecd54c6d65953ba55edaa8d38615f983ce622c1157606d35337de0fda77b20` |
| `Pieza_019.pgmx` | `Escuadrado_Horario_E001_Pasante_Extra1` | `Clockwise` | `Left` | `b5b1527655611b5d9878265e5a05266cbb7b7a9b7a19a6929f0c7d7c10184511` |

- Validacion local con `pgmx_snapshot`:
  - cada archivo tiene:
    - `features = 1`
    - `operations = 1`
    - `working_steps = 2`
    - feature `a:GeneralProfileFeature` en `Top`
    - operacion `a:BottomAndSideFinishMilling`
    - herramienta `1900 / E001`
    - `security_plane = 20`
  - `tools.pgmx_adapters.adapt_pgmx_path(...)` reconoce ambos como
    `SquaringMillingSpec`.
  - en ambos casos:
    - `adapted = 1`
    - `unsupported = 0`
    - `ignored = 1`
    - `squaring_millings = 1`
- Lectura geometrica:
  - el punto inicial nominal queda en mitad del borde inferior:
    `(200, 0, 0)`.
  - `Pieza_018` usa winding `CounterClockwise` y correccion exterior `Right`.
  - `Pieza_019` usa winding `Clockwise` y correccion exterior `Left`.
  - ambas variantes generan `TrajectoryPath` compuesto de `9` miembros:
    `5` lineas y `4` arcos de esquina.
  - ambas trabajan a cota efectiva `Z = -1`, consistente con espesor `18` y
    `Extra = 1`.
- Toolpath resumido:
  - `Pieza_018` / antihoraria:
    - `Approach`: `(190.82, -18.36, 38)` -> `(200, -9.18, -1)`
    - `TrajectoryPath`: inicia y cierra en `(200, -9.18, -1)`
    - `Lift`: `(200, -9.18, -1)` -> `(209.18, -18.36, 38)`
  - `Pieza_019` / horaria:
    - `Approach`: `(209.18, -18.36, 38)` -> `(200, -9.18, -1)`
    - `TrajectoryPath`: inicia y cierra en `(200, -9.18, -1)`
    - `Lift`: `(200, -9.18, -1)` -> `(190.82, -18.36, 38)`
- Archivos ISO analizados:
  - `P:\USBMIX\ProdAction\ISO\pieza_018.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_019.iso`
- Propiedades ISO:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | ---: | ---: | --- | --- |
| `pieza_018.iso` | `107` | `1690` | `C4DDE5DC42C1467E85C667AC4C07756A099DBB37C51C205F8A6575B946226D99` | `BD0370CE302010C70AF733B2D4C795B94EF201229A4203D635D11E6B6BBA2777` |
| `pieza_019.iso` | `107` | `1690` | `1EFB7ED5375FF8912C82161D4520A26BE12D4B6A2A193BC5FFA76E77019AFFEF` | `E9DFC6D44A708992C324F4E9160BE26E3E4FE5F0DFA0654F1BEDD290BD70617A` |

- Bloque comun:
  - `T1`, `M06`
  - `?%ETK[6]=1`, `?%ETK[9]=1`, `?%ETK[18]=1`
  - `S18000M3`
  - `SHF[X]=32.050`, `SHF[Y]=-246.650`, `SHF[Z]=-125.300`
  - `D1`
  - `SVL 125.400`
  - `SVR 9.180`
  - `?%ETK[7]=4`
  - `G40` al cerrar la compensacion
- Diferencias principales:

| Linea | `pieza_018.iso` antihoraria | `pieza_019.iso` horaria |
| ---: | --- | --- |
| 50 | `G0 X181.640 Y-19.360` | `G0 X218.360 Y-19.360` |
| 58 | `G42` | `G41` |
| 59 | `G1 X181.640 Y-18.360 Z20.000 F2000.000` | `G1 X218.360 Y-18.360 Z20.000 F2000.000` |
| 61 | `G2 X200.000 Y0.000 I200.000 J-18.360 F2000.000` | `G3 X200.000 Y0.000 I200.000 J-18.360 F2000.000` |
| 62 | `G1 X400.000 Z-19.000 F5000.000` | `G1 X0.000 Z-19.000 F5000.000` |
| 64 | `G1 X0.000 Z-19.000 F5000.000` | `G1 X400.000 Z-19.000 F5000.000` |
| 67 | `G2 X218.360 Y-18.360 I200.000 J-18.360 F5000.000` | `G3 X181.640 Y-18.360 I200.000 J-18.360 F5000.000` |
| 70 | `G1 X218.360 Y-19.360 Z20.000 F5000.000` | `G1 X181.640 Y-19.360 Z20.000 F5000.000` |

- Recorridos ISO:
  - antihorario / `Pieza_018`:
    - entrada desde `X181.640`
    - compensacion `G42`
    - arco de entrada `G2` hacia `(200, 0)`
    - recorrido nominal:
      `(200, 0) -> (400, 0) -> (400, 250) -> (0, 250) -> (0, 0) -> (200, 0)`
    - arco de salida `G2` hacia `X218.360 Y-18.360`
  - horario / `Pieza_019`:
    - entrada desde `X218.360`
    - compensacion `G41`
    - arco de entrada `G3` hacia `(200, 0)`
    - recorrido nominal:
      `(200, 0) -> (0, 0) -> (0, 250) -> (400, 250) -> (400, 0) -> (200, 0)`
    - arco de salida `G3` hacia `X181.640 Y-18.360`
- Relacion PGMX -> ISO:
  - el ISO conserva el sentido de recorrido declarado en PGMX:
    - `CounterClockwise` queda antihorario.
    - `Clockwise` queda horario.
  - la compensacion exterior se emite como compensacion CNC:
    - `Right -> G42`
    - `Left -> G41`
  - el ISO no emite los cuatro arcos de esquina del `TrajectoryPath`
    compensado PGMX; emite el rectangulo nominal y deja la resolucion de
    esquinas a `G41/G42` con `SVR 9.180`.
  - `SVR 9.180` coincide con `tool_width / 2` para `E001 = 18.36`.
  - `SVL 125.400` coincide con el largo/offset de herramienta usado por el
    postprocesador para `E001`.
  - `Extra = 1` se refleja directamente en profundidad ISO:
    - espesor `18` + extra `1` -> `G1 Z-19.000`.
- Conclusiones provisorias:
  - a diferencia de las ranuras con sierra, el escuadrado E001 no normaliza a
    un unico sentido fisico; el ISO conserva horario/antihorario.
  - al igual que la polilinea E004, el escuadrado E001 usa `G41/G42` en vez de
    coordenadas ya desplazadas para la compensacion.
  - las entradas/salidas se emiten como arcos `G2/G3` alrededor del punto medio
    del borde inferior, con desplazamiento `18.36 mm` en `X` y `Y`.
- Correccion posterior:
  - el usuario aclaro que en `Pieza_018` y `Pieza_019` no habia pedido
    acercamiento ni alejamiento habilitados.
  - se sobrescribieron ambos PGMX para quitar esas opciones.
  - los ISO `pieza_018.iso` y `pieza_019.iso` analizados arriba corresponden a
    la version anterior con `Approach/Retract = Arc + Quote`; quedan obsoletos
    para la nueva version de los PGMX.
  - nuevos archivos PGMX actuales:

| Archivo | Feature actual | Winding | `SideOfFeature` | Approach | Retract | SHA256 actual |
| --- | --- | --- | --- | --- | --- | --- |
| `Pieza_018.pgmx` | `Escuadrado_Antihorario_E001_SinAcercamientoAlejamiento` | `CounterClockwise` | `Right` | deshabilitado | deshabilitado | `b637a0157010ea9f753cfedfb4802010f40a5be67359917b7479c84cbd749128` |
| `Pieza_019.pgmx` | `Escuadrado_Horario_E001_SinAcercamientoAlejamiento` | `Clockwise` | `Left` | deshabilitado | deshabilitado | `4f3fa5cfc79e3c7a7cc9b80ac165992ad556ac38881c702160b54e7b7bb0ee89` |

  - validacion local nueva:
    - `adapted = 1`
    - `unsupported = 0`
    - `ignored = 1`
    - `squaring_millings = 1`
    - `Approach` y `Lift` existen como registros de toolpath, pero sin miembros
      de curva; la bajada/subida queda directa sobre `(200, -9.18)`.
  - el usuario volvio a postprocesar `Pieza_018.pgmx` y `Pieza_019.pgmx`.
- Nuevos ISO actuales analizados:
  - `P:\USBMIX\ProdAction\ISO\pieza_018.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_019.iso`

| ISO actual | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | ---: | ---: | --- | --- |
| `pieza_018.iso` | `105` | `1584` | `8874807C3FEF36136A08220EBA34ADA240C00F2EC4A492F27D5B2250E0F38F8A` | `3063E0BA5699E3C2DAD785748B7F832282587C2C93B3162B138076B3419754C1` |
| `pieza_019.iso` | `105` | `1584` | `D929F154234C074BFBD190DDDEE081A762E25EAFED1BF8EE206302DE523FC92B` | `B47F7086E541F80FE9084A708803A8089CD4546C9DA0EDED1A8728F0B985048E` |

- Bloque comun actual sin acercamiento/alejamiento:
  - `T1`, `M06`
  - `?%ETK[6]=1`, `?%ETK[9]=1`, `?%ETK[18]=1`
  - `S18000M3`
  - `SVL 125.400`
  - `SVR 9.180`
  - `?%ETK[7]=4`
  - `G1 Z-19.000 F2000.000`
  - corte `F5000.000`
- Diferencias actuales entre 018 y 019:

| Linea | `pieza_018.iso` antihoraria sin A/A | `pieza_019.iso` horaria sin A/A |
| ---: | --- | --- |
| 50 | `G0 X199.000 Y0.000` | `G0 X201.000 Y0.000` |
| 58 | `G42` | `G41` |
| 61 | `G1 X400.000 Z-19.000 F5000.000` | `G1 X0.000 Z-19.000 F5000.000` |
| 63 | `G1 X0.000 Z-19.000 F5000.000` | `G1 X400.000 Z-19.000 F5000.000` |
| 68 | `G1 X201.000 Y0.000 Z20.000 F5000.000` | `G1 X199.000 Y0.000 Z20.000 F5000.000` |

- Recorridos actuales:
  - `pieza_018.iso` / antihoraria:
    - aproximacion directa: `G0 X199.000 Y0.000`
    - entrada: `G1 X200.000 Y0.000 Z20.000 F2000.000`
    - compensacion: `G42`
    - baja: `G1 Z-19.000 F2000.000`
    - recorrido nominal:
      `(200, 0) -> (400, 0) -> (400, 250) -> (0, 250) -> (0, 0) -> (200, 0)`
    - sube directo: `G1 Z20.000 F5000.000`
    - salida: `G1 X201.000 Y0.000 Z20.000 F5000.000`
  - `pieza_019.iso` / horaria:
    - aproximacion directa: `G0 X201.000 Y0.000`
    - entrada: `G1 X200.000 Y0.000 Z20.000 F2000.000`
    - compensacion: `G41`
    - baja: `G1 Z-19.000 F2000.000`
    - recorrido nominal:
      `(200, 0) -> (0, 0) -> (0, 250) -> (400, 250) -> (400, 0) -> (200, 0)`
    - sube directo: `G1 Z20.000 F5000.000`
    - salida: `G1 X199.000 Y0.000 Z20.000 F5000.000`
- Comparacion contra `pieza_020.iso` y `pieza_021.iso`:
  - `pieza_018.iso` y `pieza_019.iso` actuales tienen `105` lineas y
    `1584` bytes.
  - `pieza_020.iso` y `pieza_021.iso` con `Arco 2 en cota` tienen `107`
    lineas y `1690` bytes.
  - sin acercamiento/alejamiento desaparecen:
    - los arcos `G2/G3` de entrada/salida.
    - las aproximaciones `X181.640/Y-19.360` y `X218.360/Y-19.360`.
  - el postprocesador reemplaza esas entradas por un movimiento lineal corto
    de `1 mm` sobre `X` antes/despues del punto nominal `(200, 0)`.
- Conclusiones actuales:
  - `Approach.IsEnabled = False` y `Retract.IsEnabled = False` si modifican el
    ISO final.
  - la compensacion exterior sigue llegando como:
    - `Right -> G42`
    - `Left -> G41`
  - el sentido de recorrido sigue conservandose:
    - antihorario en `pieza_018.iso`
    - horario en `pieza_019.iso`
  - `Extra = 1` sigue expresandose como profundidad `Z-19.000`.

### Ronda 27 - Piezas 020 y 021 con escuadrado E001 Arco 2 en cota

- Estado: postprocesado Maestro/CNC recibido y analizado.
- Solicitud:
  - sintetizar dos variantes de escuadrado:
    - antihoraria
    - horaria
  - ambas con:
    - acercamiento `Arco`
    - alejamiento `Arco`
    - radio/multiplicador `2`
    - modo `En cota`
- Archivos generados:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_020.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_021.pgmx`
- Parametros comunes:
  - pieza `400 x 250 x 18`
  - origen `(5, 5, 25)`
  - spec publica `SquaringMillingSpec`
  - `start_edge = Bottom`
  - plano `Top`
  - geometria nominal `ClosedPolylineMidEdgeStart`
  - bounding box nominal `(0, 0, 400, 250)`
  - herramienta `1900 / E001`
  - `tool_width = 18.36`
  - profundidad pasante `Extra = 1`
  - `BottomCondition = ThroughMillingBottom`
  - `Depth.StartDepth/EndDepth = 18 / 18`
  - `OvercutLength = 1`
  - acercamiento:
    - `enabled = true`
    - `type = Arc`
    - `mode = Quote`
    - `radius_multiplier = 2.0`
    - `arc_side = Automatic`
  - alejamiento:
    - `enabled = true`
    - `type = Arc`
    - `mode = Quote`
    - `radius_multiplier = 2.0`
    - `arc_side = Automatic`
    - `overlap = 0.0`

| Archivo | Feature | Winding | `SideOfFeature` | SHA256 |
| --- | --- | --- | --- | --- |
| `Pieza_020.pgmx` | `Escuadrado_Antihorario_E001_Arco2EnCota` | `CounterClockwise` | `Right` | `11b394b846eb1ec3deac59a99db8364334759e90f560e4b2f7ddde1784094611` |
| `Pieza_021.pgmx` | `Escuadrado_Horario_E001_Arco2EnCota` | `Clockwise` | `Left` | `c05074bd7fc77745a3a38f94cdd7ab2bd8409a848f3f0c2986a119c8e6e25d7b` |

- Validacion local con `pgmx_snapshot`:
  - cada archivo tiene:
    - `features = 1`
    - `operations = 1`
    - `working_steps = 2`
    - feature `a:GeneralProfileFeature` en `Top`
    - operacion `a:BottomAndSideFinishMilling`
    - herramienta `1900 / E001`
  - `tools.pgmx_adapters.adapt_pgmx_path(...)` reconoce ambos como
    `SquaringMillingSpec`.
  - en ambos casos:
    - `adapted = 1`
    - `unsupported = 0`
    - `ignored = 1`
    - `squaring_millings = 1`
- Toolpath resumido:
  - ambas variantes generan `TrajectoryPath` compuesto de `9` miembros:
    `5` lineas y `4` arcos de esquina.
  - ambas trabajan a cota efectiva `Z = -1`, consistente con espesor `18` y
    `Extra = 1`.
  - `Pieza_020` / antihoraria:
    - `Approach`: `(190.82, -18.36, 38)` -> `(200, -9.18, -1)`
    - `TrajectoryPath`: inicia y cierra en `(200, -9.18, -1)`
    - `Lift`: `(200, -9.18, -1)` -> `(209.18, -18.36, 38)`
  - `Pieza_021` / horaria:
    - `Approach`: `(209.18, -18.36, 38)` -> `(200, -9.18, -1)`
    - `TrajectoryPath`: inicia y cierra en `(200, -9.18, -1)`
    - `Lift`: `(200, -9.18, -1)` -> `(190.82, -18.36, 38)`
- Observacion:
  - esta configuracion coincide funcionalmente con los defaults publicos ya
    usados en `Pieza_018` y `Pieza_019`, pero en esta ronda queda declarada de
    forma explicita en la llamada al sintetizador.
- Archivos ISO analizados:
  - `P:\USBMIX\ProdAction\ISO\pieza_020.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_021.iso`
- Propiedades ISO:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | ---: | ---: | --- | --- |
| `pieza_020.iso` | `107` | `1690` | `B6E2E55ECB92B082879AC5424308F3936FED90A0FA7B9E14BC1E427DA4EACE5D` | `BD0370CE302010C70AF733B2D4C795B94EF201229A4203D635D11E6B6BBA2777` |
| `pieza_021.iso` | `107` | `1690` | `EB806826F4A116419338C8B77D896D4F9ED31934FB6A1437086D1B9EF846B93E` | `E9DFC6D44A708992C324F4E9160BE26E3E4FE5F0DFA0654F1BEDD290BD70617A` |

- Comparacion contra la ronda anterior:
  - `pieza_020.iso` es igual a `pieza_018.iso` despues de la primera linea
    del nombre de programa.
  - `pieza_021.iso` es igual a `pieza_019.iso` despues de la primera linea
    del nombre de programa.
  - por lo tanto, declarar explicitamente `Arco 2 en cota` en acercamiento y
    alejamiento no cambia el programa efectivo frente al default publico del
    escuadrado.
- Bloque efectivo confirmado:
  - antihorario / `Pieza_020`:
    - `G42`
    - `G2` en entrada y salida
    - recorrido nominal antihorario:
      `(200, 0) -> (400, 0) -> (400, 250) -> (0, 250) -> (0, 0) -> (200, 0)`
  - horario / `Pieza_021`:
    - `G41`
    - `G3` en entrada y salida
    - recorrido nominal horario:
      `(200, 0) -> (0, 0) -> (0, 250) -> (400, 250) -> (400, 0) -> (200, 0)`
  - en ambos casos:
    - `T1`, `M06`
    - `S18000M3`
    - `SVL 125.400`
    - `SVR 9.180`
    - `G1 Z-19.000 F2000.000`
    - avance de corte `F5000.000`
- Conclusion:
  - el builder publico ya tenia como default exactamente el caso
    `Acercamiento Arco, 2, en cota` y `Alejamiento Arco, 2, en cota`.
  - al explicitar esos parametros, Maestro/CNC postprocesa el mismo cuerpo ISO.

### Ronda 28 - Pieza 022 con escuadrado E001 y polilinea E004 centrada

- Estado: postprocesado Maestro/CNC recibido y analizado.
- Solicitud:
  - sintetizar una misma pieza con:
    - escuadrado antihorario estandar;
    - fresado siguiendo la polilinea
      `(150, 0) -> (100, 150) -> (300, 100) -> (250, 250)`;
    - herramienta `E004`;
    - correccion centrada;
    - profundidad pasante con `Extra = 0.5`.
- Archivo generado:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_022.pgmx`
- Parametros comunes:
  - pieza `400 x 250 x 18`
  - origen `(5, 5, 25)`
  - `ordered_machinings` para conservar el orden:
    1. `SquaringMillingSpec`
    2. `PolylineMillingSpec`
- Escuadrado:
  - feature `Escuadrado_Antihorario_E001_Estandar`
  - `start_edge = Bottom`
  - `winding = CounterClockwise`
  - `SideOfFeature = Right`
  - herramienta `1900 / E001`
  - se usaron los defaults publicos ya validados:
    - pasante `Extra = 1`
    - acercamiento `Arc + Quote`, radio x2
    - alejamiento `Arc + Quote`, radio x2
- Fresado de polilinea:
  - feature `Fresado_Polilinea_E004_Centro_Pasante_Extra05`
  - puntos nominales:
    - `(150, 0)`
    - `(100, 150)`
    - `(300, 100)`
    - `(250, 250)`
  - herramienta `1903 / E004`
  - `tool_width = 4.0`
  - `SideOfFeature = Center`
  - profundidad pasante `Extra = 0.5`
  - `Depth.StartDepth/EndDepth = 18 / 18`
  - `OvercutLength = 0.5`
  - cota efectiva PGMX del `TrajectoryPath`: `Z = -0.5`
  - acercamiento y alejamiento deshabilitados.
- Validacion local con `pgmx_snapshot` y `pgmx_adapters`:
  - `piece_name = Pieza_022`
  - `features = 2`
  - `operations = 2`
  - `working_steps = 3`
  - orden real:
    1. `Escuadrado_Antihorario_E001_Estandar`
    2. `Fresado_Polilinea_E004_Centro_Pasante_Extra05`
    3. `Xn`
  - adaptador:
    - `adapted = 2`
    - `unsupported = 0`
    - `ignored = 1`
    - `squaring_millings = 1`
    - `polyline_millings = 1`
  - SHA256 PGMX:
    `B8CB7B3E66642733323992DD1E92DF9BB2CD38131D997EC818367CC4E3409E03`
- Archivo ISO analizado:
  - `P:\USBMIX\ProdAction\ISO\pieza_022.iso`
- Propiedades ISO:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | ---: | ---: | --- | --- |
| `pieza_022.iso` | `144` | `2178` | `45B5D4919655CE6FEE35CB0D1F1D74F7C1E8E2C00B2EF09BDCCA8A11BCACEE7C` | `A40FAFD0BC965F508C1F155DAEABF730427F2B5F810876738CA04048C17CBDF7` |

- Cabecera:
  - `% pieza_022.pgm`
  - `DX=405.000`
  - `DY=255.000`
  - `DZ=43.000`
  - confirma otra vez:
    - `DX = length + origin_x`
    - `DY = width + origin_y`
    - `DZ = depth + origin_z`
- Bloque de escuadrado:
  - despues del nombre de programa, las lineas `2..76` coinciden con
    `pieza_020.iso`.
  - conserva el bloque antihorario estandar:
    - `T1`, `M06`
    - `S18000M3`
    - `SVL 125.400`
    - `SVR 9.180`
    - `G42`
    - `G1 Z-19.000 F2000.000`
    - entrada y salida con `G2`
    - recorrido nominal:
      `(200, 0) -> (400, 0) -> (400, 250) -> (0, 250) -> (0, 0) -> (200, 0)`
  - como hay una segunda operacion, en lugar del postambulo final de
    `pieza_020.iso` el postprocesador inserta una transicion segura:
    - reset de `SVL/SVR`
    - `G0 G53 Z201.000`
    - apagado de husillo con `M5`
    - nuevo cambio de herramienta.
- Bloque de polilinea E004:
  - herramienta:
    - `T4`
    - `M06`
    - `?%ETK[9]=4`
    - `S18000M3`
  - variables:
    - `SVL 107.200`
    - `SVR 2.000`
    - `D1` activo durante el corte
  - entrada:
    - `G0 X150.000 Y0.000`
    - `G0 Z127.200`
    - no aparece entrada XY de `1 mm` como en las polilineas izquierda/derecha
      anteriores; al estar centrada, baja directamente sobre el punto inicial.
  - profundidad:
    - el PGMX trabaja a `Z = -0.5`
    - el ISO emite `G1 Z-18.500 F2000.000`
    - por lo tanto, para pasante `Extra = 0.5` en E004 el ISO usa profundidad
      negativa absoluta `depth + extra`.
  - corte:
    - no aparece `G41` ni `G42`, consistente con `SideOfFeature = Center`.
    - `?%ETK[7]=4`
    - `G1 X100.000 Y150.000 F5000.000`
    - `G1 X300.000 Y100.000 F5000.000`
    - `G1 X250.000 Y250.000 F5000.000`
    - `G0 Z20.000`
- Conclusion:
  - el postprocesador respeta el orden `Escuadrado -> Fresado`.
  - el escuadrado combinado conserva el mismo cuerpo efectivo que
    `pieza_020.iso` hasta el reset posterior a la operacion.
  - la polilinea centrada con E004 se emite sobre coordenadas nominales sin
    `G41/G42`.
  - `Extra = 0.5` en fresado pasante se expresa como `Z-18.500`.

### Ronda 29 - Piezas 023 y 024 con escuadrado E001 y polilinea E004 izquierda/derecha

- Estado: postprocesado Maestro/CNC recibido y analizado.
- Solicitud:
  - generar dos versiones de `Pieza_022` cambiando solo la correccion del
    fresado E004:
    - `Pieza_023`: por izquierda
    - `Pieza_024`: por derecha
- Archivos generados:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_023.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_024.pgmx`
- Parametros comunes:
  - pieza `400 x 250 x 18`
  - origen `(5, 5, 25)`
  - `ordered_machinings`:
    1. `SquaringMillingSpec`
    2. `PolylineMillingSpec`
  - escuadrado antihorario estandar:
    - `start_edge = Bottom`
    - `winding = CounterClockwise`
    - `SideOfFeature = Right`
    - herramienta `1900 / E001`
    - pasante `Extra = 1`
  - polilinea E004:
    - puntos nominales:
      `(150, 0) -> (100, 150) -> (300, 100) -> (250, 250)`
    - herramienta `1903 / E004`
    - `tool_width = 4.0`
    - profundidad pasante `Extra = 0.5`
    - `OvercutLength = 0.5`
    - acercamiento y alejamiento deshabilitados.

| Archivo | Feature E004 | `SideOfFeature` | SHA256 PGMX |
| --- | --- | --- | --- |
| `Pieza_023.pgmx` | `Fresado_Polilinea_E004_Izquierda_Pasante_Extra05` | `Left` | `8C97C40A8B224F59BDB1A303040309FE949CF81B2917980608DDF0310FE32933` |
| `Pieza_024.pgmx` | `Fresado_Polilinea_E004_Derecha_Pasante_Extra05` | `Right` | `9CC8B2C12E6FD77B58C761F37180D497DE9F36975F0C51474A1749966322BD23` |

- Validacion local con `pgmx_snapshot` y `pgmx_adapters`:
  - cada archivo tiene:
    - `features = 2`
    - `operations = 2`
    - `working_steps = 3`
    - orden real:
      1. `Escuadrado_Antihorario_E001_Estandar`
      2. fresado E004
      3. `Xn`
  - adaptador:
    - `adapted = 2`
    - `unsupported = 0`
    - `ignored = 1`
    - `squaring_millings = 1`
    - `polyline_millings = 1`
- Toolpath PGMX de la polilinea:
  - `Pieza_023` / `Left`:
    - inicia compensada en `(148.102633, -0.632456, -0.5)`
    - contiene un arco compensado alrededor del vertice `(100, 150)`
    - termina con lift desde `(248.102633, 249.367544, -0.5)`
  - `Pieza_024` / `Right`:
    - inicia compensada en `(151.897367, 0.632456, -0.5)`
    - contiene un arco compensado alrededor del vertice `(300, 100)`
    - termina con lift desde `(251.897367, 250.632456, -0.5)`
  - aunque el PGMX contiene compensacion geometrica y arcos distintos, el ISO
    no emite esas curvas compensadas.
- Archivos ISO analizados:
  - `P:\USBMIX\ProdAction\ISO\pieza_023.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_024.iso`
- Propiedades ISO:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | ---: | ---: | --- | --- |
| `pieza_023.iso` | `149` | `2294` | `E7A2CEB0D29F3ABA7109C019B76FBBAE0E8D87DB5AA249667B47C94E2803BA6C` | `60FD0F31741FF17BEDB4D24862A7AD9795281976AC39D68D00FD1C615D90DE8E` |
| `pieza_024.iso` | `149` | `2294` | `C33A076F913F13456C0F27C72A8C2F25567700E6BFC4E3725652A12BFB723E7D` | `7BB817F469C01D3D7AFA7AC69A62884AC6623F777A39D99D0635648CE18BBE84` |

- Comparacion ISO:
  - `pieza_023.iso` y `pieza_024.iso` son identicos salvo:
    - linea 1: nombre de programa
    - linea 104:
      - `Pieza_023` emite `G41`
      - `Pieza_024` emite `G42`
  - despues del nombre de programa, las lineas `2..76` coinciden con
    `pieza_020.iso`, igual que en `Pieza_022`.
  - a diferencia de `Pieza_022`, aparece una linea extra `?%ETK[7]=0` antes de
    la transicion hacia la segunda herramienta.
- Bloque de polilinea E004:
  - herramienta:
    - `T4`
    - `M06`
    - `?%ETK[9]=4`
    - `S18000M3`
  - entrada:
    - `G0 X150.316 Y-0.949`
    - `G0 Z127.200`
    - `D1`
    - `SVL 107.200`
    - `SVR 2.000`
    - `?%ETK[7]=4`
    - `G41` o `G42`
    - `G1 X150.000 Y0.000 Z20.000 F2000.000`
  - profundidad:
    - `G1 Z-18.500 F2000.000`
  - corte:
    - `G1 X100.000 Y150.000 F5000.000`
    - `G1 X300.000 Y100.000 F5000.000`
    - `G1 X250.000 Y250.000 F5000.000`
  - salida:
    - `G1 Z20.000 F5000.000`
    - `G40`
    - `G1 X249.684 Y250.949 Z20.000 F5000.000`
- Conclusion:
  - para una polilinea E004 abierta, `SideOfFeature = Left/Right` no cambia las
    coordenadas nominales emitidas en ISO.
  - el lado de correccion queda delegado al CNC mediante:
    - `Left -> G41`
    - `Right -> G42`
  - las coordenadas de entrada/salida son puntos auxiliares a `1 mm` sobre la
    prolongacion tangente de la polilinea:
    - entrada: `(150.316, -0.949) -> (150, 0)`
    - salida: `(250, 250) -> (249.684, 250.949)`
  - `Extra = 0.5` vuelve a emitirse como `Z-18.500`.

### Ronda 30 - Piezas 025 y 026 con escuadrado E001 y circulo E004 centrado

- Estado: postprocesado Maestro/CNC recibido y analizado.
- Solicitud:
  - sintetizar la misma pieza base con escuadrado antihorario estandar y,
    en lugar de polilinea abierta, mecanizar un circulo centrado en la pieza:
    - diametro `100`
    - herramienta `E004`
    - correccion centrada
    - pasante con `Extra = 0.5`
  - generar ademas una variante con el circulo en sentido horario.
- Archivos generados:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_025.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_026.pgmx`
- Parametros comunes:
  - pieza `400 x 250 x 18`
  - origen `(5, 5, 25)`
  - `ordered_machinings`:
    1. `SquaringMillingSpec`
    2. `CircleMillingSpec`
  - escuadrado antihorario estandar:
    - `start_edge = Bottom`
    - `winding = CounterClockwise`
    - `SideOfFeature = Right`
    - herramienta `1900 / E001`
    - pasante `Extra = 1`
  - circulo E004:
    - centro `(200, 125)`
    - radio `50`
    - diametro `100`
    - herramienta `1903 / E004`
    - `tool_width = 4.0`
    - `SideOfFeature = Center`
    - profundidad pasante `Extra = 0.5`
    - acercamiento y alejamiento deshabilitados.

| Archivo | Feature E004 | Winding | SHA256 PGMX |
| --- | --- | --- | --- |
| `Pieza_025.pgmx` | `Fresado_Circulo_D100_E004_Centro_Pasante_Extra05` | `CounterClockwise` | `3007BE0225E5418A84D48856796052C703E0A31F90DB0A1A3E1BEDD663E66A63` |
| `Pieza_026.pgmx` | `Fresado_Circulo_D100_E004_Centro_Horario_Pasante_Extra05` | `Clockwise` | `A909075C07F0DA40A853815F204CE6BF021A9044E37482411C6C912A5522234F` |

- Validacion local con `pgmx_snapshot` y `pgmx_adapters`:
  - cada archivo tiene:
    - `features = 2`
    - `operations = 2`
    - `working_steps = 3`
    - orden real:
      1. `Escuadrado_Antihorario_E001_Estandar`
      2. fresado circular E004
      3. `Xn`
  - adaptador:
    - `adapted = 2`
    - `unsupported = 0`
    - `ignored = 1`
    - `squaring_millings = 1`
    - `circle_millings = 1`
- Toolpath PGMX del circulo:
  - ambos empiezan en `(250, 125)`, que es el extremo derecho del circulo.
  - el `TrajectoryPath` se serializa como dos arcos de `180 grados`:
    - `(250, 125) -> (150, 125)`
    - `(150, 125) -> (250, 125)`
  - `Pieza_025` conserva eje/sentido antihorario.
  - `Pieza_026` invierte el eje/sentido para horario.
  - el `TrajectoryPath` trabaja a `Z = -0.5`.
- Archivos ISO analizados:
  - `P:\USBMIX\ProdAction\ISO\pieza_025.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_026.iso`
- Propiedades ISO:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | ---: | ---: | --- | --- |
| `pieza_025.iso` | `143` | `2183` | `4476C6D2F09755E4A0515009D76070E384BBDD0B3C494BA265821C10F1F6DEA4` | `631F077C9159A0428B8D0DA169F2521DA463AB6C3244FDE7AD560632BD5E2169` |
| `pieza_026.iso` | `143` | `2183` | `15F9AB7DB8DF7178597D8AC3968DD84CB768CCFB843CC6A8F468EAF6CAD453E6` | `5A0A4166F49973EC34079808239C4D82CE65A0759412AD3530A07AA9DA0B8F86` |

- Comparacion ISO:
  - `pieza_025.iso` y `pieza_026.iso` son identicos salvo:
    - linea 1: nombre de programa
    - lineas 104 y 105:
      - `Pieza_025` / antihorario emite `G3`
      - `Pieza_026` / horario emite `G2`
  - despues del nombre de programa, las lineas `2..76` coinciden con
    `pieza_020.iso`, igual que en las piezas combinadas anteriores.
- Bloque circular E004:
  - herramienta:
    - `T4`
    - `M06`
    - `?%ETK[9]=4`
    - `S18000M3`
  - entrada:
    - `G0 X250.000 Y125.000`
    - `G0 Z127.200`
    - `D1`
    - `SVL 107.200`
    - `SVR 2.000`
  - profundidad:
    - `G1 Z-18.500 F2000.000`
  - corte antihorario:
    - `G3 X150.000 Y125.000 I200.000 J125.000 F5000.000`
    - `G3 X250.000 Y125.000 I200.000 J125.000 F5000.000`
  - corte horario:
    - `G2 X150.000 Y125.000 I200.000 J125.000 F5000.000`
    - `G2 X250.000 Y125.000 I200.000 J125.000 F5000.000`
  - salida:
    - `G0 Z20.000`
    - reset de `SVL/SVR`
- Conclusion:
  - para circulo E004 centrado, el postprocesador emite el circulo como dos
    semicirculos sobre coordenadas nominales.
  - `SideOfFeature = Center` no emite `G41/G42`.
  - el winding cambia solo el codigo de interpolacion:
    - `CounterClockwise -> G3`
    - `Clockwise -> G2`
  - `Extra = 0.5` vuelve a emitirse como `Z-18.500`.

### Ronda 31 - Piezas 027 a 030 con circulo E004 izquierda/derecha en ambos sentidos

- Estado: postprocesado Maestro/CNC recibido y analizado.
- Solicitud:
  - sintetizar cuatro variantes de la misma pieza:
    - antihorario por izquierda
    - antihorario por derecha
    - horario por izquierda
    - horario por derecha
- Archivos generados:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_027.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_028.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_029.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_030.pgmx`
- Parametros comunes:
  - pieza `400 x 250 x 18`
  - origen `(5, 5, 25)`
  - `ordered_machinings`:
    1. `SquaringMillingSpec`
    2. `CircleMillingSpec`
  - escuadrado antihorario estandar:
    - `start_edge = Bottom`
    - `winding = CounterClockwise`
    - `SideOfFeature = Right`
    - herramienta `1900 / E001`
    - pasante `Extra = 1`
  - circulo E004:
    - centro `(200, 125)`
    - radio nominal `50`
    - diametro nominal `100`
    - herramienta `1903 / E004`
    - `tool_width = 4.0`
    - profundidad pasante `Extra = 0.5`
    - acercamiento y alejamiento deshabilitados.

| Archivo | Winding | `SideOfFeature` | SHA256 PGMX |
| --- | --- | --- | --- |
| `Pieza_027.pgmx` | `CounterClockwise` | `Left` | `6124ECDFCB871EFAFA5931A4D8408E2B0543BA3FDA20E9A488A53724D757FBA5` |
| `Pieza_028.pgmx` | `CounterClockwise` | `Right` | `1B0AED2242C8AAB543E04714A317D0BCE7042D3EFD409841BCB0DE5C8DA87590` |
| `Pieza_029.pgmx` | `Clockwise` | `Left` | `6EF0F237A457A81EC424C2458A6A73FC5D9B7E4873594F55F85F63BE04B05C9D` |
| `Pieza_030.pgmx` | `Clockwise` | `Right` | `CBBACD0E55751292F7A595E9CE27511E3B5BD1F364BEEC44296F84B70DF4A552` |

- Validacion local con `pgmx_snapshot` y `pgmx_adapters`:
  - cada archivo tiene:
    - `features = 2`
    - `operations = 2`
    - `working_steps = 3`
    - orden real:
      1. `Escuadrado_Antihorario_E001_Estandar`
      2. fresado circular E004
      3. `Xn`
  - adaptador:
    - `adapted = 2`
    - `unsupported = 0`
    - `ignored = 1`
    - `squaring_millings = 1`
    - `circle_millings = 1`
- Toolpath PGMX del circulo:
  - el PGMX compensa geometricamente el radio efectivo:
    - `CounterClockwise + Left -> radio 48`
    - `CounterClockwise + Right -> radio 52`
    - `Clockwise + Left -> radio 52`
    - `Clockwise + Right -> radio 48`
  - en todos los casos mantiene centro `(200, 125)` y dos arcos de medio
    circulo.
  - el `TrajectoryPath` trabaja a `Z = -0.5`.
- Archivos ISO analizados:
  - `P:\USBMIX\ProdAction\ISO\pieza_027.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_028.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_029.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_030.iso`
- Propiedades ISO:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | ---: | ---: | --- | --- |
| `pieza_027.iso` | `148` | `2300` | `40F75CBCC579512738E9861AD45495B26F8C8BB780C0F2E064CDDDA2C749341F` | `9DA68F6FDAAE3DAD0024C04A3798CE10A2570E57F4FA52F953AF2443BDC23517` |
| `pieza_028.iso` | `148` | `2300` | `C72B0B56C7B5EA8D78CEC27906D49D70ABCCA8122CA0D0D01873C3E86A7EBF3C` | `74C5B8056C7ACD5FBB7BC38B9D109D4EDA2A9EC1B3BCC1234E57CF8FFBA35EE4` |
| `pieza_029.iso` | `148` | `2300` | `E0D066F8C515F1C026AFCCD2291273BDE2805E4E7AE3CF7EB51DEE8D3FA8A32A` | `B3AB4CF38D4DA40092A323DA38D3B1B4BC7E239B3AEEC526AA11789E458A8F8B` |
| `pieza_030.iso` | `148` | `2300` | `B05F6A08FC7CDFDE7DF413B58754FBB2EAC4D3E4C3B287E487F0DF8A3D5FB7E6` | `1175B6CACF53619E83C035370CC81ED3CB07F2393A3D4C27C408E6D105B15B6E` |

- Comparacion ISO por lado:
  - `pieza_027.iso` y `pieza_028.iso` son identicos salvo:
    - linea 1: nombre de programa
    - linea 104:
      - `Pieza_027` emite `G41`
      - `Pieza_028` emite `G42`
  - `pieza_029.iso` y `pieza_030.iso` son identicos salvo:
    - linea 1: nombre de programa
    - linea 104:
      - `Pieza_029` emite `G41`
      - `Pieza_030` emite `G42`
- Comparacion ISO por sentido:
  - antihorario (`Pieza_027/028`):
    - entrada auxiliar `G0 X250.000 Y124.000`
    - corte con dos `G3`
    - salida auxiliar `G1 X250.000 Y126.000 Z20.000`
  - horario (`Pieza_029/030`):
    - entrada auxiliar `G0 X250.000 Y126.000`
    - corte con dos `G2`
    - salida auxiliar `G1 X250.000 Y124.000 Z20.000`
- Bloque circular E004:
  - herramienta:
    - `T4`
    - `M06`
    - `?%ETK[9]=4`
    - `S18000M3`
  - variables:
    - `D1`
    - `SVL 107.200`
    - `SVR 2.000`
    - `?%ETK[7]=4`
  - entrada comun al punto nominal:
    - `G1 X250.000 Y125.000 Z20.000 F2000.000`
  - profundidad:
    - `G1 Z-18.500 F2000.000`
  - el circulo ISO se emite sobre radio nominal `50`, no sobre el radio
    compensado del PGMX:
    - `G2/G3 X150.000 Y125.000 I200.000 J125.000 F5000.000`
    - `G2/G3 X250.000 Y125.000 I200.000 J125.000 F5000.000`
  - salida:
    - `G1 Z20.000 F5000.000`
    - `G40`
    - punto auxiliar segun sentido.
- Conclusion:
  - en circulos E004 con `SideOfFeature = Left/Right`, el postprocesador no
    emite el radio compensado que aparece en el PGMX.
  - el ISO conserva el circulo nominal y delega la correccion al CNC:
    - `Left -> G41`
    - `Right -> G42`
  - el sentido sigue determinando la interpolacion circular:
    - `CounterClockwise -> G3`
    - `Clockwise -> G2`
  - las entradas/salidas auxiliares de `1 mm` dependen del sentido:
    - antihorario entra por `Y124` y sale por `Y126`
    - horario entra por `Y126` y sale por `Y124`
  - `Extra = 0.5` vuelve a emitirse como `Z-18.500`.

### Ronda 32 - Piezas 031 a 034 con circulo E004 helicoidal

- Estado: postprocesado Maestro/CNC recibido y analizado.
- Solicitud:
  - sintetizar dos variantes con circulos horario y antihorario usando
    estrategia helicoidal.
  - sintetizar dos variantes adicionales con la misma estrategia pero
    `PH = 5`.
- Archivos generados:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_031.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_032.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_033.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_034.pgmx`
- Parametros comunes:
  - pieza `400 x 250 x 18`
  - origen `(5, 5, 25)`
  - `ordered_machinings`:
    1. `SquaringMillingSpec`
    2. `CircleMillingSpec`
  - escuadrado antihorario estandar:
    - `start_edge = Bottom`
    - `winding = CounterClockwise`
    - `SideOfFeature = Right`
    - herramienta `1900 / E001`
    - pasante `Extra = 1`
  - circulo E004:
    - centro `(200, 125)`
    - radio nominal `50`
    - diametro nominal `100`
    - herramienta `1903 / E004`
    - `tool_width = 4.0`
    - `SideOfFeature = Center`
    - profundidad pasante `Extra = 0.5`
    - estrategia `HelicalMillingStrategySpec`
    - `allows_finish_cutting = true`
    - `UH = 0`.

| Archivo | Winding | PH | SHA256 PGMX |
| --- | --- | ---: | --- |
| `Pieza_031.pgmx` | `CounterClockwise` | `0` | `B29C5E89A9878174DBE6D91AC8B116FD55635F65EDF826FB3535825B25174A5E` |
| `Pieza_032.pgmx` | `Clockwise` | `0` | `C10201739CFF75E08DC0C8CF66C6FAAB8CA40C75C5293F4EAB348449D9833A78` |
| `Pieza_033.pgmx` | `CounterClockwise` | `5` | `167497FA2343F2349BAE223DEFDA94BF38964E2CA28615CB723EDCD779DFE1C8` |
| `Pieza_034.pgmx` | `Clockwise` | `5` | `2993CFA9483F29F59B724CAAC357AB5C7F8B46BAAA08880252B797502F1549C8` |

- Validacion local con `pgmx_snapshot` y `pgmx_adapters`:
  - cada archivo tiene:
    - `features = 2`
    - `operations = 2`
    - `working_steps = 3`
    - orden real:
      1. `Escuadrado_Antihorario_E001_Estandar`
      2. fresado circular E004 helicoidal
      3. `Xn`
  - adaptador:
    - `adapted = 2`
    - `unsupported = 0`
    - `ignored = 1`
    - `squaring_millings = 1`
    - `circle_millings = 1`
- Toolpath PGMX:
  - `PH = 0`:
    - el toolpath helicoidal tiene una vuelta completa de bajada, serializada
      como dos semicirculos con cota media `Z = 13.375` y `Z = 4.125`.
    - despues agrega una vuelta final a `Z = -0.5`.
  - `PH = 5`:
    - el toolpath helicoidal tiene cuatro vueltas de bajada:
      - tres vueltas completas repartidas cada `5 mm`
      - una vuelta final de bajada menor hasta `Z = -0.5`
    - despues agrega una vuelta final a `Z = -0.5`.
- Archivos ISO analizados:
  - `P:\USBMIX\ProdAction\ISO\pieza_031.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_032.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_033.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_034.iso`
- Propiedades ISO:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | ---: | ---: | --- | --- |
| `pieza_031.iso` | `147` | `2346` | `0962AE4555777A1CD09E7618F6ED7C08060CAAF639E19A97D59E8CF05279D111` | `856DAE643C48E6EE2EE59FB995F8562834A6AF5582E70C77EB417D0968452904` |
| `pieza_032.iso` | `147` | `2346` | `BF427D107195280A53568562B30A07A40CF4214FAD0FB2AA2E1A6BC3C784840C` | `FD65760EDEA4CFDC4E9E664A4E5EDFA2358AF47BAB0470941CC06A4B484E0AE4` |
| `pieza_033.iso` | `153` | `2704` | `C6D82B9BCCBD15DF0B089C02563AC45E7A85151BE3E6D4B30713AA776DCECE04` | `3DDB384C113BDBBB7E9B2293D8A10D659E673C080E9CA6D533A618356DED763E` |
| `pieza_034.iso` | `153` | `2704` | `F9E81D2B2E702C08CE2D9221B48A161A21985F6569E2DEC6E622B1E99FB18397` | `ADEE7553328F8C264DEA52EB1ACAB4E9F7895D4064845B28D7EC105B9C2E1A13` |

- Bloque comun helicoidal E004:
  - herramienta:
    - `T4`
    - `M06`
    - `?%ETK[9]=4`
    - `S18000M3`
  - entrada:
    - `G0 X250.000 Y125.000`
    - `G0 Z127.200`
    - `D1`
    - `SVL 107.200`
    - `SVR 2.000`
    - `G1 Z20.000 F2000.000`
    - `?%ETK[7]=4`
    - `G1 Z0.000 F5000.000`
  - salida:
    - `G1 Z20.000 F5000.000`
    - `G0 Z20.000`
    - reset de `SVL/SVR`.
- Bloque helicoidal con `PH = 0`:
  - antihorario (`Pieza_031`):
    - `G3 X150.000 Y125.000 Z-9.250 I200.000 J125.213 F5000.000`
    - `G3 X250.000 Y125.000 Z-18.500 I200.000 J124.787 F5000.000`
    - pasada final:
      - `G3 X150.000 Y125.000 I200.000 J125.000 F5000.000`
      - `G3 X250.000 Y125.000 I200.000 J125.000 F5000.000`
  - horario (`Pieza_032`):
    - mismo patron, con `G2` y offsets `J` espejados:
      - primer semiarco `J124.787`
      - segundo semiarco `J125.213`
- Bloque helicoidal con `PH = 5`:
  - antihorario (`Pieza_033`):
    - baja en semicirculos a:
      - `Z-2.500`
      - `Z-5.000`
      - `Z-7.500`
      - `Z-10.000`
      - `Z-12.500`
      - `Z-15.000`
      - `Z-16.750`
      - `Z-18.500`
    - despues ejecuta una vuelta final a profundidad constante `Z-18.500`.
  - horario (`Pieza_034`):
    - mismo patron de niveles, con `G2` y offsets `J` espejados.
- Comparacion ISO:
  - `Pieza_031` vs `Pieza_032`:
    - cambian solo el nombre de programa y los arcos del bloque circular:
      - `G3` vs `G2`
      - offsets `J` espejados.
  - `Pieza_033` vs `Pieza_034`:
    - misma regla: `G3` vs `G2` y offsets `J` espejados.
  - `PH = 5` agrega `6` lineas frente a `PH = 0`, porque descompone la bajada
    helicoidal en mas semiarcos.
- Conclusion:
  - en estrategia helicoidal, el ISO no baja directamente a `Z-18.500`; primero
    baja a `Z0.000` y luego reparte la bajada en arcos.
  - `PH = 0` produce una vuelta helicoidal completa de bajada hasta `Z-18.500`
    y luego una vuelta final.
  - `PH = 5` produce multiples semiarcos de bajada y luego una vuelta final.
  - el sentido conserva la misma regla:
    - `CounterClockwise -> G3`
    - `Clockwise -> G2`
  - `Extra = 0.5` sigue fijando la profundidad final `Z-18.500`.

### Ronda 33 - Piezas 035 y 036 con polilinea E004 centrada PH5

- Estado: postprocesado Maestro/CNC recibido y analizado.
- Solicitud:
  - volver a los fresados sobre polilineas.
  - sintetizar la misma pieza con:
    - escuadrado antihorario estandar.
    - fresado siguiendo la polilinea
      `(150, 0) -> (100, 150) -> (300, 100) -> (250, 250)`.
    - herramienta `E004`.
    - correccion centrada.
    - profundidad pasante con `Extra = 0.5`.
    - estrategia unidireccional `PH = 5`.
    - otra variante con estrategia bidireccional.
- Archivos generados:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_035.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_036.pgmx`
- Parametros comunes:
  - pieza `400 x 250 x 18`
  - origen `(5, 5, 25)`
  - `ordered_machinings`:
    1. `SquaringMillingSpec`
    2. `PolylineMillingSpec`
  - escuadrado antihorario estandar:
    - `start_edge = Bottom`
    - `winding = CounterClockwise`
    - `SideOfFeature = Right`
    - herramienta `1900 / E001`
    - pasante `Extra = 1`
  - polilinea E004:
    - puntos nominales:
      `(150, 0) -> (100, 150) -> (300, 100) -> (250, 250)`
    - herramienta `1903 / E004`
    - `tool_width = 4.0`
    - `SideOfFeature = Center`
    - profundidad pasante `Extra = 0.5`
    - acercamiento y alejamiento deshabilitados.

| Archivo | Feature E004 | Estrategia | SHA256 PGMX |
| --- | --- | --- | --- |
| `Pieza_035.pgmx` | `Fresado_Polilinea_E004_Centro_Unidireccional_PH5_Pasante_Extra05` | `Unidirectional`, `SafetyHeight`, `PH = 5` | `028B7E72F6274F0B17A3BA922DA9222DD26B0DF7D8A774A5A4B314763528E788` |
| `Pieza_036.pgmx` | `Fresado_Polilinea_E004_Centro_Bidireccional_PH5_Pasante_Extra05` | `Bidirectional`, `PH = 5` | `1049D9EDA27FDF6DEA8545BCE0A11851AC30C9D97ACC82B195E53674B495F3F8` |

- Validacion local con `pgmx_snapshot` y `pgmx_adapters`:
  - cada archivo tiene:
    - `features = 2`
    - `operations = 2`
    - `working_steps = 3`
    - orden real:
      1. `Escuadrado_Antihorario_E001_Estandar`
      2. fresado E004 sobre polilinea
      3. `Xn`
  - adaptador:
    - `adapted = 2`
    - `unsupported = 0`
    - `ignored = 1`
    - `squaring_millings = 1`
    - `polyline_millings = 1`
- Toolpath PGMX:
  - ambos empiezan con aproximacion vertical:
    - `(150, 0, 38) -> (150, 0, 13)`
  - los niveles PGMX del fresado son:
    - `Z = 13`
    - `Z = 8`
    - `Z = 3`
    - `Z = -0.5`
  - esos niveles corresponden en ISO a:
    - `Z-5.000`
    - `Z-10.000`
    - `Z-15.000`
    - `Z-18.500`
  - `Pieza_035` / unidireccional:
    - estrategia:
      `UnidirectionalMillingStrategySpec(connection_mode='SafetyHeight', allow_multiple_passes=True, axial_cutting_depth=5.0, axial_finish_cutting_depth=0.0)`.
    - en cada nivel corta la polilinea en sentido directo.
    - despues de cada pasada no final sube a `Z = 38` y vuelve al punto
      inicial recorriendo la polilinea en sentido inverso a altura segura.
  - `Pieza_036` / bidireccional:
    - estrategia:
      `BidirectionalMillingStrategySpec(allow_multiple_passes=True, axial_cutting_depth=5.0, axial_finish_cutting_depth=0.0)`.
    - alterna el sentido de corte en cada nivel.
    - no vuelve a altura segura entre niveles; baja verticalmente en el extremo
      donde termino la pasada anterior.
- Archivos ISO analizados:
  - `P:\USBMIX\ProdAction\ISO\pieza_035.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_036.iso`
- Propiedades ISO:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | ---: | ---: | --- | --- |
| `pieza_035.iso` | `170` | `2952` | `9DAC839D240AD9739D9A078C8B92846AA100CEA195AD5368F89567D94DACE38F` | `9DE1A800DB30CA53BECDB58335CF554EA3025876CEEF0CA5E1689D9DD195CADE` |
| `pieza_036.iso` | `158` | `2588` | `E3C525336EEA5D0F7BCCDD57CC2EE79179324BD85261B9EA50779E54111319B3` | `D1222F81A543A5F455295342448B3C351753D09367A321B9D5A01E5D727B9038` |

- Comparacion contra `Pieza_022`:
  - `Pieza_022` sin estrategia multipasada bajaba directo a `Z-18.500` y
    ejecutaba una unica pasada directa por la polilinea.
  - `Pieza_035` y `Pieza_036` agregan multipasadas por `PH = 5`.
  - las coordenadas XY siguen siendo nominales.
  - no aparece `G41/G42`, consistente con `SideOfFeature = Center`.
- Bloque E004 comun:
  - herramienta:
    - `T4`
    - `M06`
    - `?%ETK[9]=4`
    - `S18000M3`
  - entrada:
    - `G0 X150.000 Y0.000`
    - `G0 Z127.200`
    - `D1`
    - `SVL 107.200`
    - `SVR 2.000`
    - `G1 Z20.000 F2000.000`
    - `?%ETK[7]=4`
- Bloque unidireccional `Pieza_035`:
  - primera pasada:
    - `G1 Z-5.000 F5000.000`
    - `(150, 0) -> (100, 150) -> (300, 100) -> (250, 250)`
  - retorno entre pasadas:
    - `G1 Z20.000 F5000.000`
    - `(250, 250) -> (300, 100) -> (100, 150) -> (150, 0)`
  - repite el patron en:
    - `Z-10.000`
    - `Z-15.000`
    - `Z-18.500`
  - tras la pasada final solo retrae a `Z20`.
- Bloque bidireccional `Pieza_036`:
  - primera pasada:
    - `G1 Z-5.000 F5000.000`
    - `(150, 0) -> (100, 150) -> (300, 100) -> (250, 250)`
  - segunda pasada:
    - `G1 Z-10.000 F5000.000`
    - `(250, 250) -> (300, 100) -> (100, 150) -> (150, 0)`
  - tercera pasada:
    - `G1 Z-15.000 F5000.000`
    - `(150, 0) -> (100, 150) -> (300, 100) -> (250, 250)`
  - cuarta pasada:
    - `G1 Z-18.500 F5000.000`
    - `(250, 250) -> (300, 100) -> (100, 150) -> (150, 0)`
  - retrae a `Z20` recien al terminar la pasada final.
- Conclusion:
  - en polilinea abierta centrada, `PH = 5` produce pasadas a
    `Z-5.000`, `Z-10.000`, `Z-15.000` y `Z-18.500`.
  - la estrategia unidireccional con `SafetyHeight` conserva un solo sentido de
    corte y usa retornos intermedios a altura segura.
  - la estrategia bidireccional alterna el sentido de corte y evita esos
    retornos intermedios, por eso el ISO es mas corto.
  - `Extra = 0.5` sigue fijando la profundidad final `Z-18.500`.

### Ronda 34 - Piezas 037 y 038 con polilinea cerrada E003 centrada

- Estado: postprocesado Maestro/CNC recibido y analizado.
- Solicitud:
  - sintetizar la misma pieza con un mecanizado con herramienta `E003`
    centrada siguiendo la polilinea cerrada:
    `(200, 50) -> (350, 50) -> (350, 200) -> (50, 200) -> (50, 50) -> (200, 50)`.
  - profundidad `15 mm`.
  - acercamiento lineal `4` en bajada.
  - alejamiento lineal `4` en subida.
  - generar otra igual pero con el fresado en sentido inverso.
- Archivos generados:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_037.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_038.pgmx`
- Parametros comunes:
  - pieza `400 x 250 x 18`
  - origen `(5, 5, 25)`
  - `ordered_machinings`:
    1. `SquaringMillingSpec`
    2. `PolylineMillingSpec`
  - escuadrado antihorario estandar:
    - `start_edge = Bottom`
    - `winding = CounterClockwise`
    - `SideOfFeature = Right`
    - herramienta `1900 / E001`
    - pasante `Extra = 1`
  - polilinea cerrada E003:
    - herramienta `1902 / E003`
    - `tool_width = 9.52`
    - `SideOfFeature = Center`
    - profundidad no pasante `target_depth = 15`
    - `Approach = Line + Down`
    - `Approach RadiusMultiplier = 4`
    - `Retract = Line + Up`
    - `Retract RadiusMultiplier = 4`.

| Archivo | Feature E003 | Sentido puntos | SHA256 PGMX |
| --- | --- | --- | --- |
| `Pieza_037.pgmx` | `Fresado_Polilinea_Cerrada_E003_Centro_Lineal4BajadaSubida_Prof15` | pedido | `27233AB83BBEECB3DD8783C594FA6CCF4E6B1A80343A7440BD1770C728FA430D` |
| `Pieza_038.pgmx` | `Fresado_Polilinea_Cerrada_E003_Centro_Lineal4BajadaSubida_Prof15_Inversa` | inverso | `24893C18C10F42CEFF0809C9BFB2AC3D34E00B10B75255A6FC44FC20EFADB6BC` |

- Validacion local con `pgmx_snapshot` y `pgmx_adapters`:
  - cada archivo tiene:
    - `features = 2`
    - `operations = 2`
    - `working_steps = 3`
    - orden real:
      1. `Escuadrado_Antihorario_E001_Estandar`
      2. fresado E003 sobre polilinea cerrada
      3. `Xn`
  - adaptador:
    - `adapted = 2`
    - `unsupported = 0`
    - `ignored = 1`
    - `squaring_millings = 1`
    - `polyline_millings = 1`
- Toolpath PGMX:
  - el corte queda en `Z = 3` porque la pieza tiene espesor `18` y la
    profundidad es `15`.
  - `Line + Down + 4` genera una entrada lineal oblicua con lead de `19.04 mm`:
    - `tool_width / 2 = 4.76`
    - `4.76 * 4 = 19.04`
  - `Pieza_037`:
    - approach: `(180.96, 50, 38) -> (200, 50, 3)`
    - trayectoria:
      `(200, 50) -> (350, 50) -> (350, 200) -> (50, 200) -> (50, 50) -> (200, 50)`
    - lift: `(200, 50, 3) -> (219.04, 50, 38)`
  - `Pieza_038`:
    - approach: `(219.04, 50, 38) -> (200, 50, 3)`
    - trayectoria:
      `(200, 50) -> (50, 50) -> (50, 200) -> (350, 200) -> (350, 50) -> (200, 50)`
    - lift: `(200, 50, 3) -> (180.96, 50, 38)`
- Archivos ISO analizados:
  - `P:\USBMIX\ProdAction\ISO\pieza_037.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_038.iso`
- Propiedades ISO:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | ---: | ---: | --- | --- |
| `pieza_037.iso` | `148` | `2303` | `3D90BCC006B9FCADC4FE5637F1253B32A332A8BC95BA880793F16B3AA8C6F3B9` | `1E913911707A8CAA0DCF8DC3714CC11F715A00DA301D1252EE10C1873FB3E241` |
| `pieza_038.iso` | `148` | `2303` | `A1F5700CA3BB036F36870F53B80D5843E1B1837E1D0BF38B17B8C4BC8F827BB1` | `8357E693AD495761ACEED20FA95829D3DDB2469D52E98F760E9195094A879D4F` |

- Bloque E003 comun:
  - herramienta:
    - `T3`
    - `M06`
    - `?%ETK[9]=3`
    - `S18000M3`
  - variables:
    - `SVL 111.500`
    - `SVR 4.760`
    - `D1`
    - `?%ETK[7]=4`
  - no aparece `G41/G42`, consistente con `SideOfFeature = Center`.
  - no aparecen arcos `G2/G3` dentro del bloque de polilinea cerrada.
- Bloque de `Pieza_037`:
  - entrada:
    - `G0 X180.960 Y50.000`
    - `G0 Z131.500`
    - `G1 X200.000 Z-15.000 F3000.000`
  - trayectoria:
    - `G1 X350.000 Z-15.000 F18000.000`
    - `G1 Y200.000 Z-15.000 F18000.000`
    - `G1 X50.000 Z-15.000 F18000.000`
    - `G1 Y50.000 Z-15.000 F18000.000`
    - `G1 X200.000 Z-15.000 F18000.000`
  - salida:
    - `G1 X219.040 Z20.000 F18000.000`
    - `G0 Z20.000`
- Bloque de `Pieza_038`:
  - entrada:
    - `G0 X219.040 Y50.000`
    - `G0 Z131.500`
    - `G1 X200.000 Z-15.000 F3000.000`
  - trayectoria:
    - `G1 X50.000 Z-15.000 F18000.000`
    - `G1 Y200.000 Z-15.000 F18000.000`
    - `G1 X350.000 Z-15.000 F18000.000`
    - `G1 Y50.000 Z-15.000 F18000.000`
    - `G1 X200.000 Z-15.000 F18000.000`
  - salida:
    - `G1 X180.960 Z20.000 F18000.000`
    - `G0 Z20.000`
- Comparacion ISO:
  - `pieza_037.iso` y `pieza_038.iso` tienen la misma estructura, cantidad de
    lineas y bytes.
  - despues del nombre de programa, cambian solo las lineas de entrada,
    dos vertices explicitados por `X` y la linea de salida.
  - las lineas con solo `Y200` y `Y50` son textualmente iguales, pero heredan
    distinto `X` modal por el sentido previo.
- Conclusion:
  - una polilinea cerrada centrada se emite como contorno nominal cerrado.
  - el cierre aparece como una ultima linea al punto inicial `(200, 50)`.
  - al estar centrada, no activa compensacion `G41/G42`.
  - invertir el sentido no cambia herramienta, variables ni estructura general;
    cambia el lado de la entrada/salida lineal y el orden efectivo del contorno.
  - la profundidad no pasante `15 mm` se expresa como `Z-15.000`, aunque el
    toolpath PGMX este en `Z = 3`.

### Ronda 35 - Piezas 039 y 040 con polilinea cerrada E003 unidireccional PH5

- Estado: postprocesado Maestro/CNC recibido y analizado.
- Solicitud:
  - sintetizar nuevamente las dos piezas de la ronda anterior agregando
    estrategia unidireccional con `PH = 5`.
- Archivos generados:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_039.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_040.pgmx`
- Parametros comunes:
  - pieza `400 x 250 x 18`
  - origen `(5, 5, 25)`
  - `ordered_machinings`:
    1. `SquaringMillingSpec`
    2. `PolylineMillingSpec`
  - escuadrado antihorario estandar:
    - `start_edge = Bottom`
    - `winding = CounterClockwise`
    - `SideOfFeature = Right`
    - herramienta `1900 / E001`
    - pasante `Extra = 1`
  - polilinea cerrada E003:
    - herramienta `1902 / E003`
    - `tool_width = 9.52`
    - `SideOfFeature = Center`
    - profundidad no pasante `target_depth = 15`
    - `Approach = Line + Down`
    - `Approach RadiusMultiplier = 4`
    - `Retract = Line + Up`
    - `Retract RadiusMultiplier = 4`
    - estrategia:
      `UnidirectionalMillingStrategySpec(connection_mode='InPiece', allow_multiple_passes=True, axial_cutting_depth=5.0, axial_finish_cutting_depth=0.0)`.

| Archivo | Base | Sentido puntos | SHA256 PGMX |
| --- | --- | --- | --- |
| `Pieza_039.pgmx` | `Pieza_037` | pedido | `750A0C22DAF953D66EAF4D300D4B9F4F96F10F9846A2FED18465D39529772F7F` |
| `Pieza_040.pgmx` | `Pieza_038` | inverso | `CBEFC126962806A39E4A6BF906A5FC11282B10B95D1F540A5FD9B0A1759CB591` |

- Validacion local con `pgmx_snapshot` y `pgmx_adapters`:
  - cada archivo tiene:
    - `features = 2`
    - `operations = 2`
    - `working_steps = 3`
    - orden real:
      1. `Escuadrado_Antihorario_E001_Estandar`
      2. fresado E003 sobre polilinea cerrada
      3. `Xn`
  - adaptador:
    - `adapted = 2`
    - `unsupported = 0`
    - `ignored = 1`
    - `squaring_millings = 1`
    - `polyline_millings = 1`
- Toolpath PGMX:
  - niveles de corte:
    - `Z = 13`
    - `Z = 8`
    - `Z = 3`
  - equivalen en ISO a:
    - `Z-5.000`
    - `Z-10.000`
    - `Z-15.000`
  - como el perfil es cerrado, la estrategia unidireccional queda con
    `connection_mode = InPiece`.
  - no hay retorno intermedio a altura segura entre pasadas.
  - entre niveles, el toolpath baja verticalmente en el punto de cierre
    `(200, 50)`.
  - `Pieza_039` mantiene el sentido:
    `(200, 50) -> (350, 50) -> (350, 200) -> (50, 200) -> (50, 50) -> (200, 50)`.
  - `Pieza_040` mantiene el sentido inverso:
    `(200, 50) -> (50, 50) -> (50, 200) -> (350, 200) -> (350, 50) -> (200, 50)`.
- Archivos ISO analizados:
  - `P:\USBMIX\ProdAction\ISO\pieza_039.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_040.iso`
- Propiedades ISO:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | ---: | ---: | --- | --- |
| `pieza_039.iso` | `160` | `2694` | `8926F7E01B7B1E6A6ADE525B0EACE1B364D898C68028EF55B5624670A7908893` | `ABE7FA29F83F611E47DA347C4EFC63F408BCF5A73FD0D22FC783477D91A7C5EE` |
| `pieza_040.iso` | `160` | `2694` | `99721AFBE8104575FCFB0C97271AC4DA05BE18378DF21F5FDF068CC6BDD07AF8` | `EC7085B265ADE7684BA890EDF43D2E726E6338238FDB135BB6D9BBB51B192748` |

- Bloque E003 comun:
  - herramienta:
    - `T3`
    - `M06`
    - `?%ETK[9]=3`
    - `S18000M3`
  - variables:
    - `SVL 111.500`
    - `SVR 4.760`
    - `D1`
    - `?%ETK[7]=4`
  - no aparece `G41/G42`.
  - respecto de `Pieza_037/038`, aparece una bajada previa:
    - `G1 Z20.000 F3000.000`
    - luego se activa `?%ETK[7]=4`
    - despues entra en diagonal hasta el primer nivel de corte.
- Bloque de `Pieza_039`:
  - entrada:
    - `G0 X180.960 Y50.000`
    - `G0 Z131.500`
    - `G1 Z20.000 F3000.000`
    - `G1 X200.000 Z-5.000 F18000.000`
  - primera pasada:
    - `G1 X350.000 Z-5.000 F18000.000`
    - `G1 Y200.000 Z-5.000 F18000.000`
    - `G1 X50.000 Z-5.000 F18000.000`
    - `G1 Y50.000 Z-5.000 F18000.000`
    - `G1 X200.000 Z-5.000 F18000.000`
  - segunda pasada:
    - `G1 Z-10.000 F18000.000`
    - repite el mismo contorno hasta `(200, 50)`.
  - tercera pasada:
    - `G1 Z-15.000 F18000.000`
    - repite el mismo contorno hasta `(200, 50)`.
  - salida:
    - `G1 X219.040 Z20.000 F18000.000`
    - `G0 Z20.000`
- Bloque de `Pieza_040`:
  - misma estructura, con entrada desde `X219.040`.
  - cada nivel recorre el contorno inverso:
    `(200, 50) -> (50, 50) -> (50, 200) -> (350, 200) -> (350, 50) -> (200, 50)`.
  - salida hacia `X180.960`.
- Comparacion ISO:
  - `pieza_039.iso` y `pieza_040.iso` tienen la misma estructura, lineas y
    bytes.
  - cambian el nombre, el lado de entrada/salida y los vertices que fijan el
    sentido en cada nivel.
  - frente a `Pieza_037/038`, `PH = 5` agrega `12` lineas y repite el contorno
    en tres niveles.
- Conclusion:
  - en una polilinea cerrada E003 centrada, unidireccional `PH = 5` no produce
    retornos a altura segura entre pasadas.
  - el postprocesador baja de nivel en el punto de cierre del perfil y recorre
    de nuevo el mismo contorno nominal.
  - las profundidades ISO son `Z-5.000`, `Z-10.000` y `Z-15.000`.
  - el sentido invertido se conserva igual que en la variante sin estrategia.

### Ronda 36 - Piezas 041 a 044 con polilinea cerrada E003 izquierda/derecha PH5

- Estado: postprocesado Maestro/CNC recibido y analizado.
- Solicitud:
  - sintetizar las mismas piezas de la ronda anterior, pero con correccion por
    derecha e izquierda.
- Archivos generados:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_041.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_042.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_043.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_044.pgmx`
- Parametros comunes:
  - pieza `400 x 250 x 18`
  - origen `(5, 5, 25)`
  - `ordered_machinings`:
    1. `SquaringMillingSpec`
    2. `PolylineMillingSpec`
  - escuadrado antihorario estandar:
    - `start_edge = Bottom`
    - `winding = CounterClockwise`
    - `SideOfFeature = Right`
    - herramienta `1900 / E001`
    - pasante `Extra = 1`
  - polilinea cerrada E003:
    - herramienta `1902 / E003`
    - `tool_width = 9.52`
    - profundidad no pasante `target_depth = 15`
    - `Approach = Line + Down`
    - `Approach RadiusMultiplier = 4`
    - `Retract = Line + Up`
    - `Retract RadiusMultiplier = 4`
    - estrategia unidireccional `PH = 5`
    - `connection_mode = InPiece`.

| Archivo | Sentido puntos | `SideOfFeature` | Tipo de offset efectivo | SHA256 PGMX |
| --- | --- | --- | --- | --- |
| `Pieza_041.pgmx` | pedido | `Right` | exterior | `EEA588E7E17590D1B5FA3FD1D8012CF6A25A383DBB0A5B868D162B1C89CAFA42` |
| `Pieza_042.pgmx` | pedido | `Left` | interior | `C89D145EC6AD2341F4964B4174FFBD9945D0EB829D4C8E2851A1D7FC9CFB555F` |
| `Pieza_043.pgmx` | inverso | `Right` | interior | `F928488C69C0ED556D6605801D5C9E9B8A32597000F5C2F7A2DF2B149586B192` |
| `Pieza_044.pgmx` | inverso | `Left` | exterior | `584143D46C2D0FB254AA966C332EC8CC1630F1FBF15F7E52AA1F573BCE917A02` |

- Validacion local con `pgmx_snapshot` y `pgmx_adapters`:
  - cada archivo tiene:
    - `features = 2`
    - `operations = 2`
    - `working_steps = 3`
    - orden real:
      1. `Escuadrado_Antihorario_E001_Estandar`
      2. fresado E003 sobre polilinea cerrada compensada
      3. `Xn`
  - adaptador:
    - `adapted = 2`
    - `unsupported = 0`
    - `ignored = 1`
    - `squaring_millings = 1`
    - `polyline_millings = 1`
  - la operacion E003 queda con:
    - `activate_cnc_correction = False`
    - estrategia:
      `UnidirectionalMillingStrategySpec(connection_mode='InPiece', allow_multiple_passes=True, axial_cutting_depth=5.0, axial_finish_cutting_depth=0.0)`.
- Toolpath PGMX:
  - todos mantienen niveles:
    - `Z = 13`
    - `Z = 8`
    - `Z = 3`
  - equivalen en ISO a:
    - `Z-5.000`
    - `Z-10.000`
    - `Z-15.000`
  - el radio de herramienta es `4.76`.
  - offsets exteriores:
    - `Pieza_041` (`Right` con sentido pedido)
    - `Pieza_044` (`Left` con sentido inverso)
    - agregan arcos de esquina en el toolpath compensado.
  - offsets interiores:
    - `Pieza_042` (`Left` con sentido pedido)
    - `Pieza_043` (`Right` con sentido inverso)
    - generan un rectangulo reducido con vertices rectos.
- Archivos ISO analizados:
  - `P:\USBMIX\ProdAction\ISO\pieza_041.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_042.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_043.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_044.iso`
- Propiedades ISO:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | ---: | ---: | --- | --- |
| `pieza_041.iso` | `172` | `3294` | `4E8F508B0E928A722064F0D5C9E92CEE3442BE9F24FDDAA194D3B579EB0DE766` | `65FE1170BC8309B67AA2192A6FC904129E55141B29E6603BB629EAA92904A873` |
| `pieza_042.iso` | `160` | `2694` | `C1EA9E8CD5EE16582888B73DE90E9568A4E33E10B3FB466A14CFD4B4298C0E07` | `EF64D21E7716E0BC8CD7E56597FB0BE39CEE2A32B048D54EE51BEBDC7085F63A` |
| `pieza_043.iso` | `160` | `2694` | `B72F302C48F8FC742BC02B5F8B842014449E91546363049A2B9F38653781196B` | `B3D443DEB951CD03D8C964D3159A38D0D084188BAFB2EEFFE7B14742B608B282` |
| `pieza_044.iso` | `172` | `3294` | `E1251414BFDBE6E076C07FE5D07B5924B4C1A27AC67962C16970F6BECD181144` | `DEAC029CE2C6F8D0A0D66668B86B5A39371417CF1721C5F2E6AE7A60484D7747` |

- Bloque E003 comun:
  - herramienta:
    - `T3`
    - `M06`
    - `?%ETK[9]=3`
    - `S18000M3`
  - variables:
    - `SVL 111.500`
    - `SVR 4.760`
    - `D1`
    - `?%ETK[7]=4`
  - no aparece `G41/G42` dentro del bloque E003.
  - la compensacion llega al ISO como geometria ya desplazada.
- Offsets exteriores:
  - `Pieza_041`:
    - entrada `G0 X180.960 Y45.240`
    - por nivel, recorre:
      - `G1 X350.000`
      - `G3 X354.760 Y50.000 I350.000 J50.000`
      - `G1 Y200.000`
      - `G3 X350.000 Y204.760 I350.000 J200.000`
      - `G1 X50.000`
      - `G3 X45.240 Y200.000 I50.000 J200.000`
      - `G1 Y50.000`
      - `G3 X50.000 Y45.240 I50.000 J50.000`
      - `G1 X200.000`
    - usa `G3` en las esquinas.
  - `Pieza_044`:
    - entrada `G0 X219.040 Y45.240`
    - mismo offset exterior con sentido inverso.
    - usa `G2` en las esquinas.
  - ambos tienen `172` lineas y `3294` bytes.
- Offsets interiores:
  - `Pieza_042`:
    - entrada `G0 X180.960 Y54.760`
    - por nivel, recorre el rectangulo reducido:
      - `X345.240`
      - `Y195.240`
      - `X54.760`
      - `Y54.760`
      - `X200.000`
  - `Pieza_043`:
    - entrada `G0 X219.040 Y54.760`
    - mismo rectangulo reducido con sentido inverso:
      - `X54.760`
      - `Y195.240`
      - `X345.240`
      - `Y54.760`
      - `X200.000`
  - no emiten arcos en esquinas.
  - ambos tienen `160` lineas y `2694` bytes, igual que las versiones
    centradas `Pieza_039/040`.
- Conclusion:
  - en polilinea cerrada E003 con `SideOfFeature = Left/Right`, el
    postprocesador no delega la compensacion al CNC mediante `G41/G42`.
  - el ISO emite la geometria compensada que ya viene en el toolpath PGMX.
  - para este contorno, `Right/Left` no se interpreta aislado sino junto con el
    sentido:
    - sentido pedido + `Right` = exterior
    - sentido pedido + `Left` = interior
    - sentido inverso + `Right` = interior
    - sentido inverso + `Left` = exterior
  - el offset exterior agrega arcos `G3` o `G2` en las esquinas segun sentido.
  - el offset interior queda como rectangulo reducido sin arcos.
  - `PH = 5` conserva la misma regla de niveles:
    `Z-5.000`, `Z-10.000`, `Z-15.000`.

### Ronda 37 - Piezas 045 y 046 con polilinea cerrada E003 bidireccional PH5

- Estado: postprocesado Maestro/CNC recibido y analizado.
- Solicitud:
  - sintetizar dos piezas similares a las anteriores, pero con correccion
    centrada y estrategia bidireccional.
- Archivos generados:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_045.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_046.pgmx`
- Parametros comunes:
  - pieza `400 x 250 x 18`
  - origen `(5, 5, 25)`
  - `ordered_machinings`:
    1. `SquaringMillingSpec`
    2. `PolylineMillingSpec`
  - escuadrado antihorario estandar:
    - `start_edge = Bottom`
    - `winding = CounterClockwise`
    - `SideOfFeature = Right`
    - herramienta `1900 / E001`
    - pasante `Extra = 1`
  - polilinea cerrada E003:
    - herramienta `1902 / E003`
    - `tool_width = 9.52`
    - `SideOfFeature = Center`
    - profundidad no pasante `target_depth = 15`
    - `Approach = Line + Down`
    - `Approach RadiusMultiplier = 4`
    - `Retract = Line + Up`
    - `Retract RadiusMultiplier = 4`
    - estrategia:
      `BidirectionalMillingStrategySpec(allow_multiple_passes=True, axial_cutting_depth=5.0, axial_finish_cutting_depth=0.0)`.

| Archivo | Sentido inicial | SHA256 PGMX |
| --- | --- | --- |
| `Pieza_045.pgmx` | pedido | `843ADD067EFD648B7C1056D9F535EA80188E847FAFB1F814C3FDC40FC1BF6DF6` |
| `Pieza_046.pgmx` | inverso | `4D071766DECDE13840450399A4F3F2C0F36EC2193DB37D75EBB65741B9864BCE` |

- Nota de archivo:
  - el hash actual de `Pieza_045.pgmx` despues del postproceso Maestro/CNC es
    distinto del hash impreso al sintetizarlo inicialmente.
  - se registra el hash actual del archivo que quedo en la carpeta de estudio.
- Validacion local con `pgmx_snapshot` y `pgmx_adapters`:
  - cada archivo tiene:
    - `features = 2`
    - `operations = 2`
    - `working_steps = 3`
    - orden real:
      1. `Escuadrado_Antihorario_E001_Estandar`
      2. fresado E003 sobre polilinea cerrada centrada
      3. `Xn`
  - adaptador:
    - `adapted = 2`
    - `unsupported = 0`
    - `ignored = 1`
    - `squaring_millings = 1`
    - `polyline_millings = 1`
  - la operacion E003 queda con:
    - `activate_cnc_correction = False`
    - estrategia bidireccional `PH = 5`.
- Toolpath PGMX:
  - niveles:
    - `Z = 13`
    - `Z = 8`
    - `Z = 3`
  - equivalen en ISO a:
    - `Z-5.000`
    - `Z-10.000`
    - `Z-15.000`
  - `Pieza_045`:
    - nivel `Z=13`: sentido pedido.
    - nivel `Z=8`: sentido inverso.
    - nivel `Z=3`: sentido pedido.
  - `Pieza_046`:
    - nivel `Z=13`: sentido inverso.
    - nivel `Z=8`: sentido pedido.
    - nivel `Z=3`: sentido inverso.
- Archivos ISO analizados:
  - `P:\USBMIX\ProdAction\ISO\pieza_045.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_046.iso`
- Propiedades ISO:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | ---: | ---: | --- | --- |
| `pieza_045.iso` | `160` | `2694` | `4C24E86F2CC782B98EFDA6E923BE6786527D0B5A35F46E088FA7D46116BC2101` | `56DEA1EB5640482B183F0CA8F45DEA79A41FA540C804951AF97955C73485B8CE` |
| `pieza_046.iso` | `160` | `2694` | `B5AC94982C989966F1AD4718E0C972205AC75995E49C2E3F593E32947C8A8DC6` | `A2EB28482E12352FCDF190D81017FA459AA8C2E0D7A5D25DC387DB478E2AD57C` |

- Bloque E003 comun:
  - herramienta:
    - `T3`
    - `M06`
    - `?%ETK[9]=3`
    - `S18000M3`
  - variables:
    - `SVL 111.500`
    - `SVR 4.760`
    - `D1`
    - `?%ETK[7]=4`
  - no aparece `G41/G42` ni `G2/G3` dentro del bloque E003.
- Bloque de `Pieza_045`:
  - entrada:
    - `G0 X180.960 Y50.000`
    - `G0 Z131.500`
    - `G1 Z20.000 F3000.000`
    - `G1 X200.000 Z-5.000 F18000.000`
  - nivel `Z-5.000`, sentido pedido:
    `(200, 50) -> (350, 50) -> (350, 200) -> (50, 200) -> (50, 50) -> (200, 50)`.
  - nivel `Z-10.000`, sentido inverso:
    `(200, 50) -> (50, 50) -> (50, 200) -> (350, 200) -> (350, 50) -> (200, 50)`.
  - nivel `Z-15.000`, sentido pedido.
  - salida:
    - `G1 X219.040 Z20.000 F18000.000`
    - `G0 Z20.000`
- Bloque de `Pieza_046`:
  - entrada:
    - `G0 X219.040 Y50.000`
    - `G0 Z131.500`
    - `G1 Z20.000 F3000.000`
    - `G1 X200.000 Z-5.000 F18000.000`
  - nivel `Z-5.000`, sentido inverso.
  - nivel `Z-10.000`, sentido pedido.
  - nivel `Z-15.000`, sentido inverso.
  - salida:
    - `G1 X180.960 Z20.000 F18000.000`
    - `G0 Z20.000`
- Comparacion ISO:
  - `Pieza_045` vs `Pieza_039`:
    - misma estructura, lineas y bytes.
    - cambian solo las lineas del nivel intermedio `Z-10.000`.
    - `Pieza_039` mantiene el mismo sentido en todos los niveles.
    - `Pieza_045` invierte el nivel intermedio.
  - `Pieza_046` vs `Pieza_040`:
    - misma regla, con sentido inicial inverso.
- Conclusion:
  - en polilinea cerrada E003 centrada, la estrategia bidireccional `PH = 5`
    si alterna el sentido por nivel.
  - no cambia la estructura general del bloque ni la cantidad de lineas frente
    a la unidireccional.
  - no aparece retorno a altura segura entre niveles.
  - las profundidades siguen siendo `Z-5.000`, `Z-10.000` y `Z-15.000`.

### Ronda 38 - Piezas 047 a 050 con circulo E004 unidireccional/bidireccional PH5

- Estado: postprocesado Maestro/CNC recibido y analizado.
- Solicitud:
  - sintetizar circulos en ambos sentidos con estrategia unidireccional y
    bidireccional.
- Archivos generados:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_047.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_048.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_049.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_050.pgmx`
- Parametros comunes:
  - pieza `400 x 250 x 18`
  - origen `(5, 5, 25)`
  - `ordered_machinings`:
    1. `SquaringMillingSpec`
    2. `CircleMillingSpec`
  - escuadrado antihorario estandar:
    - `start_edge = Bottom`
    - `winding = CounterClockwise`
    - `SideOfFeature = Right`
    - herramienta `1900 / E001`
    - pasante `Extra = 1`
  - circulo E004:
    - centro `(200, 125)`
    - radio nominal `50`
    - diametro nominal `100`
    - herramienta `1903 / E004`
    - `tool_width = 4.0`
    - `SideOfFeature = Center`
    - profundidad pasante `Extra = 0.5`
    - acercamiento y alejamiento deshabilitados
    - `PH = 5`.

| Archivo | Winding | Estrategia | SHA256 PGMX |
| --- | --- | --- | --- |
| `Pieza_047.pgmx` | `CounterClockwise` | `Unidirectional` | `2F24F93F213D0B6F10FF899DA6DB1CEA88AB7D5EA92D30E0469B7051D283924F` |
| `Pieza_048.pgmx` | `Clockwise` | `Unidirectional` | `4E7F3D64CAB1D282677F5711AE810426E531C653B2C0C9DE6606984DBAE6AF16` |
| `Pieza_049.pgmx` | `CounterClockwise` | `Bidirectional` | `56CBB5D11C7BFA3C7E9AD84DF2AE2F012169410258A4750F0A8BA0FEB125014F` |
| `Pieza_050.pgmx` | `Clockwise` | `Bidirectional` | `F6D33B28871302A024E1D49AB66107FC3B5404731211A00A43DC841B63AB2DFF` |

- Validacion local con `pgmx_snapshot` y `pgmx_adapters`:
  - cada archivo tiene:
    - `features = 2`
    - `operations = 2`
    - `working_steps = 3`
    - orden real:
      1. `Escuadrado_Antihorario_E001_Estandar`
      2. fresado circular E004 centrado
      3. `Xn`
  - adaptador:
    - `adapted = 2`
    - `unsupported = 0`
    - `ignored = 1`
    - `squaring_millings = 1`
    - `circle_millings = 1`
  - la operacion E004 queda con:
    - `activate_cnc_correction = False`
    - estrategia unidireccional o bidireccional segun archivo.
- Toolpath PGMX:
  - niveles:
    - `Z = 13`
    - `Z = 8`
    - `Z = 3`
    - `Z = -0.5`
  - equivalen en ISO a:
    - `Z-5.000`
    - `Z-10.000`
    - `Z-15.000`
    - `Z-18.500`
  - cada nivel queda como una vuelta completa del circulo, serializada en dos
    semicirculos.
- Archivos ISO analizados:
  - `P:\USBMIX\ProdAction\ISO\pieza_047.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_048.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_049.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_050.iso`
- Propiedades ISO:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | ---: | ---: | --- | --- |
| `pieza_047.iso` | `154` | `2606` | `60E58089A03AA144282486AE2E3AFF8F69DA242C12DC02C8F5484C9D29700AC7` | `C851298CE6BD8F8290DC036F673CA580120C3719E7F442C22C795E240AB80157` |
| `pieza_048.iso` | `154` | `2606` | `A678F923601A3371A909958A96C1D8EC1530A2B3D112FA9A78878C9546B85479` | `3C03D986E39D41197F6E1B5EBB4C1C9DAD88591936F2434D33654569F716B87B` |
| `pieza_049.iso` | `154` | `2606` | `2981F6C21996B2947D7E20EAC2538BD7CA4EDDD0072001E401257CBADA86F9F2` | `BECC3FB5F1C0B02BD005A2683AEDD374437577B497D344A1BF4F0DE6325860E1` |
| `pieza_050.iso` | `154` | `2606` | `1094E03268CDDC1FFB605BD5BB6DD1A8CB176184672831F42ABB3CA0A7D4FF1F` | `89F7773F1BE845B899982CF06B7D7E074936CE7BD8A338C0FD1348FBFC69A0A6` |

- Bloque E004 comun:
  - herramienta:
    - `T4`
    - `M06`
    - `?%ETK[9]=4`
    - `S18000M3`
  - variables:
    - `SVL 107.200`
    - `SVR 2.000`
    - `D1`
    - `?%ETK[7]=4`
  - no aparece `G41/G42` dentro del bloque E004, consistente con
    `SideOfFeature = Center`.
  - entrada:
    - `G0 X250.000 Y125.000`
    - `G0 Z127.200`
    - `G1 Z20.000 F2000.000`
  - salida:
    - `G1 Z20.000 F5000.000`
    - `G0 Z20.000`
- Bloques unidireccionales:
  - `Pieza_047` / antihorario:
    - niveles: `Z-5.000`, `Z-10.000`, `Z-15.000`, `Z-18.500`
    - en todos los niveles usa dos semicirculos `G3`.
  - `Pieza_048` / horario:
    - mismos niveles.
    - en todos los niveles usa dos semicirculos `G2`.
- Bloques bidireccionales:
  - `Pieza_049` / arranque antihorario:
    - `Z-5.000`: `G3`
    - `Z-10.000`: `G2`
    - `Z-15.000`: `G3`
    - `Z-18.500`: `G2`
  - `Pieza_050` / arranque horario:
    - `Z-5.000`: `G2`
    - `Z-10.000`: `G3`
    - `Z-15.000`: `G2`
    - `Z-18.500`: `G3`
- Comparacion ISO:
  - `Pieza_047` vs `Pieza_049`:
    - misma estructura, lineas y bytes.
    - cambian solo los arcos del segundo y cuarto nivel:
      - unidireccional mantiene `G3`.
      - bidireccional alterna a `G2`.
  - `Pieza_048` vs `Pieza_050`:
    - misma regla espejada:
      - unidireccional mantiene `G2`.
      - bidireccional alterna a `G3` en los niveles pares.
  - `Pieza_047` vs `Pieza_048`:
    - cambian los arcos de todos los niveles: `G3` vs `G2`.
  - `Pieza_049` vs `Pieza_050`:
    - alternancia complementaria de `G3/G2`.
- Conclusion:
  - en circulo E004 centrado con `PH = 5`, las estrategias unidireccional y
    bidireccional comparten estructura, cantidad de lineas y niveles.
  - unidireccional conserva el sentido en todas las vueltas.
  - bidireccional alterna el sentido de cada vuelta completa.
  - el ISO no usa interpolacion helicoidal; baja verticalmente al siguiente
    nivel y ejecuta una vuelta circular a profundidad constante.
  - `Extra = 0.5` sigue fijando la profundidad final `Z-18.500`.

### Ronda 39 - Piezas 051 a 058 con circulo E004 izquierda/derecha uni/bidireccional PH5

- Estado: postprocesado Maestro/CNC recibido y analizado.
- Solicitud:
  - sintetizar circulos en ambos sentidos con correccion por derecha e
    izquierda y con estrategia unidireccional y bidireccional.
- Archivos generados:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_051.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_052.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_053.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_054.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_055.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_056.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_057.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_058.pgmx`
- Parametros comunes:
  - pieza `400 x 250 x 18`
  - origen `(5, 5, 25)`
  - `ordered_machinings`:
    1. `SquaringMillingSpec`
    2. `CircleMillingSpec`
  - escuadrado antihorario estandar:
    - `start_edge = Bottom`
    - `winding = CounterClockwise`
    - `SideOfFeature = Right`
    - herramienta `1900 / E001`
    - pasante `Extra = 1`
  - circulo E004:
    - centro `(200, 125)`
    - radio nominal `50`
    - diametro nominal `100`
    - herramienta `1903 / E004`
    - `tool_width = 4.0`
    - profundidad pasante `Extra = 0.5`
    - acercamiento y alejamiento deshabilitados
    - `PH = 5`.

| Archivo | Winding | SideOfFeature | Estrategia | SHA256 PGMX |
| --- | --- | --- | --- | --- |
| `Pieza_051.pgmx` | `CounterClockwise` | `Right` | `Unidirectional` | `DB9054208A171B47EDBA8465A2822DE0A211F63C56997CD7B082247A3E267EBE` |
| `Pieza_052.pgmx` | `CounterClockwise` | `Left` | `Unidirectional` | `E63CF5377EA2C52F9DD7E1B0E0F22D04647C7CD8C2595DAC1764DA9195A16479` |
| `Pieza_053.pgmx` | `Clockwise` | `Right` | `Unidirectional` | `32596E376B32BC390F387F9D9B5676C4C6946526DD922F7A350B46B90A90872C` |
| `Pieza_054.pgmx` | `Clockwise` | `Left` | `Unidirectional` | `8F2BC3C5A2E9CD6C47380187207C1191B73932F74CF903056F9FED0B7E343E55` |
| `Pieza_055.pgmx` | `CounterClockwise` | `Right` | `Bidirectional` | `63AA63FBAFAD8A10C92F282EAFF8EE44B1E7DC75851F84ADC5BCEFEB70DF35AB` |
| `Pieza_056.pgmx` | `CounterClockwise` | `Left` | `Bidirectional` | `854110139DE82DB9A16784F20DC37EA6B912FDDB70E365F5F80BBD357872E7B9` |
| `Pieza_057.pgmx` | `Clockwise` | `Right` | `Bidirectional` | `FF2A3FE613DDEB7083A6BA9F7C5F8968661988667F08790045816CE066B09C62` |
| `Pieza_058.pgmx` | `Clockwise` | `Left` | `Bidirectional` | `2D5FD5D52C3D919AAFE8E0E65C5425A2D2486D0A696E76245F25CAAFCD60E59C` |

- Validacion local con `pgmx_snapshot` y `pgmx_adapters`:
  - cada archivo tiene:
    - `features = 2`
    - `operations = 2`
    - `working_steps = 3`
    - orden real:
      1. `Escuadrado_Antihorario_E001_Estandar`
      2. fresado circular E004 con correccion y estrategia
      3. `Xn`
  - adaptador:
    - `adapted = 2`
    - `unsupported = 0`
    - `ignored = 1`
    - `squaring_millings = 1`
    - `circle_millings = 1`
  - la operacion E004 queda con:
    - `activate_cnc_correction = False`
    - `approach.is_enabled = False`
    - `retract.is_enabled = False`
    - estrategia unidireccional o bidireccional segun archivo.
  - toolpath PGMX:
    - niveles: `Z = 13`, `Z = 8`, `Z = 3`, `Z = -0.5`
    - radio efectivo `52` para:
      - `CounterClockwise + Right`
      - `Clockwise + Left`
    - radio efectivo `48` para:
      - `CounterClockwise + Left`
      - `Clockwise + Right`.
- Archivos ISO analizados:
  - `P:\USBMIX\ProdAction\ISO\pieza_051.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_052.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_053.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_054.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_055.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_056.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_057.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_058.iso`
- Propiedades ISO:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | ---: | ---: | --- | --- |
| `pieza_051.iso` | `154` | `2606` | `5EAB5FD45FAEDF938E0FCDD6208A9A089149602A93AEEE66A194DB7FE6ACE7D0` | `7AE7E1882A0470B332E9B00F5F1AC21059335A37BE2E7C3779D3CA7B7D089504` |
| `pieza_052.iso` | `154` | `2606` | `85067A714ECA5439FB27EBF4D8D8ED73D28F157FD3283CC7242985EA351080C4` | `BE15AB87F7BE04CAD7D97225D739D5E677D4DE2C03095039D8822B585FCC0D01` |
| `pieza_053.iso` | `154` | `2606` | `047DE94BA519C02A6446A5DBBE5D311C6B521051BB463A868EC7F440DFBF9E46` | `9EFB6E1C55E4571F94FF5318D8A6E6F46DBD9B2A0AAF5BB1C019534C054A325C` |
| `pieza_054.iso` | `154` | `2606` | `9CA7990D884BB1C8DE4D9CDA9393337BF490DDD859E6FD94262E92F05220370A` | `FE14BB8BABB772A6B2E0D5D6B0C6312C27C50E4F003E98800D61FE468B29A213` |
| `pieza_055.iso` | `154` | `2606` | `809F0D50FE9A0F48FE9F8C7B40C3CA99F5ABC1A91105A37C977AE6A88450D19D` | `3AACED0FEDA2BDB7371ECC558E5AAC9A7853E64FC784434267A79775655D0837` |
| `pieza_056.iso` | `154` | `2606` | `D626D88AC8B75231A331A7EE0C5DC31ADB26298E4F7A72DB08D4CFE9ADB27DE7` | `1FD360ABFDE6DB747B108C81603BB35C3171399F5AE5478F0785B28589A6838A` |
| `pieza_057.iso` | `154` | `2606` | `B26ED31FB51ADD0092FA8DC295EA5103B6B700ED1677A8DB10C6F76B10637D70` | `7F3AF6A4344AB8418BCC1E08BB95CF816CFD7B9449CFFCE3A296CD3C105FDBC9` |
| `pieza_058.iso` | `154` | `2606` | `097A282A30F2F73C10BE3A2D13A72F2E5AA03F7F4A4F08EC537BE475E2072155` | `41E553E11F3C20D8FE9A1F78CEE834E68DF25A1955075029B214E4ABBB6816E6` |

- Bloque E004 comun:
  - herramienta:
    - `T4`
    - `M06`
    - `?%ETK[9]=4`
    - `S18000M3`
  - variables:
    - `SVL 107.200`
    - `SVR 2.000`
    - `D1`
    - `?%ETK[7]=4`
  - el bloque E004 no emite `G41/G42`.
    - el `G42` que aparece en el archivo pertenece al escuadrado E001 previo.
  - no conserva el radio nominal `50` con compensacion CNC, como ocurria en
    `Pieza_027` a `Pieza_030`.
  - emite geometria ya compensada:
    - radio `52`:
      - entrada `G0 X252.000 Y125.000`
      - semicirculos hasta `X148.000` y vuelta a `X252.000`
    - radio `48`:
      - entrada `G0 X248.000 Y125.000`
      - semicirculos hasta `X152.000` y vuelta a `X248.000`
  - no aparecen las entradas/salidas auxiliares de `1 mm` en `Y124/Y126`
    observadas en los circulos `Left/Right` sin estrategia.
  - niveles ISO:
    - `Z-5.000`
    - `Z-10.000`
    - `Z-15.000`
    - `Z-18.500`
  - no hay retorno a altura segura entre niveles.
  - no hay interpolacion helicoidal: baja verticalmente al siguiente nivel y
    luego ejecuta una vuelta completa a profundidad constante.
- Regla de radio por lado y sentido:
  - radio `52`:
    - `Pieza_051`: `CounterClockwise + Right + Unidirectional`
    - `Pieza_054`: `Clockwise + Left + Unidirectional`
    - `Pieza_055`: `CounterClockwise + Right + Bidirectional`
    - `Pieza_058`: `Clockwise + Left + Bidirectional`
  - radio `48`:
    - `Pieza_052`: `CounterClockwise + Left + Unidirectional`
    - `Pieza_053`: `Clockwise + Right + Unidirectional`
    - `Pieza_056`: `CounterClockwise + Left + Bidirectional`
    - `Pieza_057`: `Clockwise + Right + Bidirectional`
- Regla de estrategia:
  - unidireccional:
    - `Pieza_051` y `Pieza_052` mantienen `G3` en los cuatro niveles.
    - `Pieza_053` y `Pieza_054` mantienen `G2` en los cuatro niveles.
  - bidireccional:
    - `Pieza_055` y `Pieza_056` alternan `G3`, `G2`, `G3`, `G2`.
    - `Pieza_057` y `Pieza_058` alternan `G2`, `G3`, `G2`, `G3`.
- Conclusion:
  - en circulos E004 `Left/Right` con estrategia `PH = 5`, Maestro no aplica
    la misma salida que en los circulos simples `Left/Right`.
  - la combinacion con estrategia desactiva la compensacion CNC del bloque E004
    y serializa la trayectoria ya compensada.
  - el criterio de lado se conserva como offset geometrico:
    - `CounterClockwise + Right` y `Clockwise + Left` salen por radio exterior
      `52`.
    - `CounterClockwise + Left` y `Clockwise + Right` salen por radio interior
      `48`.
  - la estrategia solo modifica la secuencia de sentidos por nivel; no cambia
    lineas, bytes, herramienta, variables ni profundidades.

### Ronda 40 - Piezas 059 a 062 con escuadrado E001 uni/bidireccional PH5

- Estado: postprocesado Maestro/CNC recibido y analizado.
- Solicitud:
  - sintetizar escuadrados en ambos sentidos con estrategia unidireccional y
    bidireccional.
- Archivos generados:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_059.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_060.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_061.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_062.pgmx`
- Parametros comunes:
  - pieza `400 x 250 x 18`
  - origen `(5, 5, 25)`
  - un solo `SquaringMillingSpec` seguido de `Xn`
  - herramienta `1900 / E001`
  - `tool_width = 18.36`
  - pasante `Extra = 1`
  - acercamiento y alejamiento estandar:
    - `Arc + Quote`
    - radio multiplicador `2`
    - lado `Automatic`
  - `PH = 5`.

| Archivo | Winding | Estrategia | SHA256 PGMX |
| --- | --- | --- | --- |
| `Pieza_059.pgmx` | `CounterClockwise` | `Unidirectional` | `35AD832D4C60CB297CBFE7543DB147C414AC47BD49596A6869DBE38CA77E0EA0` |
| `Pieza_060.pgmx` | `Clockwise` | `Unidirectional` | `CDBCC98C904495E56F9595557E07462A6DE2CD8C095746B89DBEB860BD91672A` |
| `Pieza_061.pgmx` | `CounterClockwise` | `Bidirectional` | `CD92DF7F740A97102F04E643309DD1E36BEF2A192D889CCA9EFE4F2A50EC0086` |
| `Pieza_062.pgmx` | `Clockwise` | `Bidirectional` | `D07C4AEDC31BC5277991D1F0F091233A50D3A29AC68917B1D50D38EE03C07231` |

- Validacion local con `pgmx_snapshot` y `pgmx_adapters`:
  - cada archivo tiene:
    - `features = 1`
    - `operations = 1`
    - `working_steps = 2`
    - orden real:
      1. escuadrado E001
      2. `Xn`
  - adaptador:
    - `adapted = 1`
    - `unsupported = 0`
    - `ignored = 1`
    - `squaring_millings = 1`
  - la operacion E001 queda con:
    - `activate_cnc_correction = False`
    - estrategia unidireccional o bidireccional segun archivo.
  - toolpath PGMX:
    - niveles: `Z = 13`, `Z = 8`, `Z = 3`, `Z = -1`
    - coordenadas compensadas por radio E001:
      - `X = -9.18`, `0`, `200`, `400`, `409.18`
      - `Y = -9.18`, `0`, `250`, `259.18`
- Archivos ISO analizados:
  - `P:\USBMIX\ProdAction\ISO\pieza_059.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_060.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_061.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_062.iso`
- Propiedades ISO:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | ---: | ---: | --- | --- |
| `pieza_059.iso` | `138` | `2929` | `2A1C26A5752BF0CDEAC8E52A5082F5FFC664F6BA9F6610655068AC18823A61D1` | `0DF92CD8E9E71331A79D70ED673B042EC5450D1D666F890FFB3107D5F539CA74` |
| `pieza_060.iso` | `138` | `2929` | `544A4E67E09EEAFF51FAB094A1E945F822069AE1FC9A15046DBF432A0936A513` | `14EB14F67D17D807EDE09704363A789DBC7EE6B7D724D9168DBB21F105556260` |
| `pieza_061.iso` | `138` | `2925` | `6191458A365B1AB8EC0F0B4323F0835CE0FD228FAA75D947FDDFE3F26D219492` | `28736EF4747BDA6BF2C1F536E971A5679A150D21B2547F8ED9CF03FE9FBAEA52` |
| `pieza_062.iso` | `138` | `2925` | `82D8617C2ADA92FB85C8911A5D6976563180243A9C807D2F0C0DBC86AA3960C2` | `221FF792C40D9B85A7590140DF5391375FB0EC3C95092FD4BF0978F0E5E0E5B9` |

- Bloque E001 comun:
  - herramienta:
    - `T1`
    - `M06`
    - `?%ETK[6]=1`
    - `?%ETK[9]=1`
    - `S18000M3`
  - variables:
    - `SVL 125.400`
    - `SVR 9.180`
    - `D1`
    - `?%ETK[7]=4`
  - no emite `G41/G42`.
  - emite geometria ya compensada, con el radio de herramienta aplicado en las
    coordenadas:
    - borde inferior exterior `Y-9.180`
    - borde superior exterior `Y259.180`
    - borde izquierdo exterior `X-9.180`
    - borde derecho exterior `X409.180`
  - niveles ISO:
    - `Z-5.000`
    - `Z-10.000`
    - `Z-15.000`
    - `Z-19.000`
  - no hay retorno a altura segura entre niveles.
  - cada nivel completo se recorre a profundidad constante despues de una bajada
    vertical al inicio del nivel.
- Regla de sentido:
  - `Pieza_059` / unidireccional antihorario:
    - entrada `G0 X190.820 Y-18.360`
    - arco de acercamiento `G2` hasta `(200, -9.180)`
    - esquinas del contorno con `G3`
    - repite el sentido antihorario en los cuatro niveles.
  - `Pieza_060` / unidireccional horario:
    - entrada `G0 X209.180 Y-18.360`
    - arco de acercamiento `G3` hasta `(200, -9.180)`
    - esquinas del contorno con `G2`
    - repite el sentido horario en los cuatro niveles.
- Regla bidireccional:
  - `Pieza_061` / arranque antihorario:
    - `Z-5.000`: antihorario, esquinas `G3`
    - `Z-10.000`: horario, esquinas `G2`
    - `Z-15.000`: antihorario, esquinas `G3`
    - `Z-19.000`: horario, esquinas `G2`
    - salida final:
      - `G2 X190.820 Y0.000 I200.000 J0.000`
  - `Pieza_062` / arranque horario:
    - `Z-5.000`: horario, esquinas `G2`
    - `Z-10.000`: antihorario, esquinas `G3`
    - `Z-15.000`: horario, esquinas `G2`
    - `Z-19.000`: antihorario, esquinas `G3`
    - salida final:
      - `G3 X209.180 Y0.000 I200.000 J0.000`
- Comparacion frente a escuadrados E001 sin estrategia:
  - en `Pieza_018` a `Pieza_021`, el ISO usaba rectangulo nominal y
    compensacion CNC:
    - `Right -> G42`
    - `Left -> G41`
  - en `Pieza_059` a `Pieza_062`, la estrategia `PH = 5` cambia el criterio:
    - no hay `G41/G42`.
    - el bloque trabaja con coordenadas ya compensadas.
    - el radio de herramienta `SVR 9.180` queda informado, pero no se usa como
      compensacion activa CNC.
  - el acercamiento/alejamiento `Arc + Quote` se conserva, pero ajustado a la
    trayectoria compensada y al sentido final de la ultima pasada.
- Conclusion:
  - escuadrado E001 con estrategia multipasada confirma la misma tendencia que
    los circulos `Left/Right` con estrategia:
    - la estrategia desactiva la compensacion CNC del bloque de fresado.
    - el postprocesador emite geometria ya compensada.
  - unidireccional conserva el sentido en todos los niveles.
  - bidireccional alterna el sentido por nivel.
  - `PH = 5` produce niveles `-5`, `-10`, `-15` y profundidad final pasante
    `-19` por `Extra = 1`.

### Ronda 41 - Piezas 063 a 071 con fresado lineal E004 y estrategias

- Estado: postprocesado Maestro/CNC recibido y analizado.
- Solicitud:
  - volver a sintetizar la pieza con un fresado lineal vertical desde el frente
    hasta atras.
  - profundidad pasante `Extra = 0.5`.
  - herramienta `E004`.
  - acercamiento y alejamiento lineal `2` en cota.
  - variantes sin estrategia, unidireccional y bidireccional.
  - correcciones `Center`, `Right` y `Left`.
- Archivos generados:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_063.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_064.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_065.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_066.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_067.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_068.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_069.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_070.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_071.pgmx`
- Parametros comunes:
  - pieza `400 x 250 x 18`
  - origen `(5, 5, 25)`
  - `ordered_machinings`:
    1. `SquaringMillingSpec`
    2. `LineMillingSpec`
  - escuadrado antihorario estandar:
    - `start_edge = Bottom`
    - `winding = CounterClockwise`
    - `SideOfFeature = Right`
    - herramienta `1900 / E001`
    - pasante `Extra = 1`
  - fresado lineal E004:
    - geometria nominal `(200, 0) -> (200, 250)`
    - herramienta `1903 / E004`
    - `tool_width = 4.0`
    - profundidad pasante `Extra = 0.5`
    - acercamiento:
      - `Line + Quote`
      - radio multiplicador `2`
    - alejamiento:
      - `Line + Quote`
      - radio multiplicador `2`.
  - estrategia unidireccional:
    - `connection_mode = SafetyHeight`
    - `PH = 5`
    - `UH = 0`.
  - estrategia bidireccional:
    - `PH = 5`
    - `UH = 0`.

| Archivo | SideOfFeature | Estrategia | SHA256 PGMX |
| --- | --- | --- | --- |
| `Pieza_063.pgmx` | `Center` | sin estrategia | `66E78AC803106A7184E62D1106E4734530308CFCFF4EF05EC151EE30B68ED9AA` |
| `Pieza_064.pgmx` | `Right` | sin estrategia | `3D631C8520C8570D4DF7C73B33B93714DAA8A0AFA732A307EAE0C4485E36CCA4` |
| `Pieza_065.pgmx` | `Left` | sin estrategia | `DDC912D276EAE2146C926B00720F379CB5327767DB0DA4C4660A5190FAC9E98D` |
| `Pieza_066.pgmx` | `Center` | `Unidirectional` | `4A9C027ACC12ECFF4EC52BA754C16C0DBABF734E115D25DB3B0CA11AC724189A` |
| `Pieza_067.pgmx` | `Right` | `Unidirectional` | `E34884A13851A80BE8FAB6385B285068D35EEA4AE0BEC72A048B273F8190B16F` |
| `Pieza_068.pgmx` | `Left` | `Unidirectional` | `F9F35DEFFF02ABAB2C7D4BF288194470491ACB295D1B320549302F50FCB4AC3F` |
| `Pieza_069.pgmx` | `Center` | `Bidirectional` | `0F6C6A17C3FD4F085F155B115BF5B88675D9AA03D4A75112FC786DE4986D4BBF` |
| `Pieza_070.pgmx` | `Right` | `Bidirectional` | `1DC70E51FD1107C0D63F80F871E8BCCFCBC77982DF13E6798E7EA63C537E1919` |
| `Pieza_071.pgmx` | `Left` | `Bidirectional` | `F21E287AA3B43C67BC025AEFB85BADE0E6FEDD90B1BF2BEADA820D73186A3140` |

- Validacion local con `pgmx_snapshot` y `pgmx_adapters`:
  - cada archivo tiene:
    - `features = 2`
    - `operations = 2`
    - `working_steps = 3`
    - orden real:
      1. `Escuadrado_Antihorario_E001_Estandar`
      2. fresado lineal E004
      3. `Xn`
  - adaptador:
    - `adapted = 2`
    - `unsupported = 0`
    - `ignored = 1`
    - `squaring_millings = 1`
    - `line_millings = 1`
  - en la operacion E004:
    - `Pieza_063` a `Pieza_065`: `activate_cnc_correction = True`
    - `Pieza_066` a `Pieza_071`: `activate_cnc_correction = False`
  - toolpath PGMX:
    - sin estrategia:
      - un unico nivel de corte `Z = -0.5`
      - `Center` queda en `X200`
      - `Right` queda en `X202`
      - `Left` queda en `X198`
    - con estrategia:
      - niveles de corte `Z = 13`, `Z = 8`, `Z = 3`, `Z = -0.5`
      - `Right/Left` tambien quedan como coordenadas compensadas `X202/X198`
      - en unidireccional el `TrajectoryPath` incluye retornos a altura segura
        entre pasadas.
- Archivos ISO analizados:
  - `P:\USBMIX\ProdAction\ISO\pieza_063.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_064.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_065.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_066.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_067.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_068.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_069.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_070.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_071.iso`
- Propiedades ISO:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | ---: | ---: | --- | --- |
| `pieza_063.iso` | `145` | `2200` | `5A07B6ABC43B63F470DAED3AD20910EAD28FA4076458A0CE70F5F2FFD29A9FAB` | `CE0CEBBF5D72CC7A4DA1662643D905E4630B1E3ED226122A39F182D7ACDBD92C` |
| `pieza_064.iso` | `149` | `2293` | `51EB33A15034B88F0852B8F9B3077766115E00F6A181ECAC4898E14212887211` | `A95663FBDD24463B2DD54E8CBFDF337F18BCAF553175156EACD89ED9E149B66D` |
| `pieza_065.iso` | `149` | `2293` | `642123C5EC1209260A191C67FA51A9D441DB7C34B8D6763B5B75DBF3775BD9F8` | `106323B1F0C8C8E2894D4ED6DAAB3BE5332FFA2A47AAFADA799A26B6697E4F69` |
| `pieza_066.iso` | `158` | `2550` | `C47AE4D95BDC3B2EAE1478112C093CC21B4AF80CA28D4E4A1EB9D9C199D71AD0` | `5EF2E8640AD16F47E0B4572E82110678C5DE29160DCF6A996BFFB6C1C2F6856A` |
| `pieza_067.iso` | `158` | `2550` | `AC068FC9E1EF7DFB7E5DC404C46599B7373B284EE6DC155319A4B77FA0CCD74F` | `F6C79BEEC20212CFB898ECA165A5232E0ADEE72CCA6D3A112636061434EBDAE4` |
| `pieza_068.iso` | `158` | `2550` | `7FB0932ACE4F202E2FF26020DA424384C1727AAB343AB5E1D6C4418799041624` | `4999825AC9E930D9EEE34C58830DB68C78EE7B9E2D5A0309B86ED4E23695A69C` |
| `pieza_069.iso` | `152` | `2386` | `9DF20EE4AD8C071B31D79101052E55618A9B83579775F0D27E193925B30B9D35` | `3FF8CBE4E9B0B24BB82B5224CFA8709228D36D9185C3F0BC0D984DCDD06176E4` |
| `pieza_070.iso` | `152` | `2386` | `51535945BBC38DDAA92E623C6A2E262C06964F8E29507EE69CA76C7069277ACC` | `4C54CCCA5BCB2B5D5EC9F155A2E9408419915A1E1BDE9E1A5D7978734E32BE18` |
| `pieza_071.iso` | `152` | `2386` | `1D42BAAD92484142AB9C9C20186CE3FCA1C396F2E425767562F5D51898F02664` | `3C57F6249B57DB43180144114757750484543B4008EBA34CDBC6D087A188D123` |

- Bloque E004 comun:
  - herramienta:
    - `T4`
    - `M06`
    - `?%ETK[9]=4`
    - `S18000M3`
  - variables:
    - `SVL 107.200`
    - `SVR 2.000`
    - `D1`
    - `?%ETK[7]=4`
  - `Line + Quote + 2` se traduce como extension de `4 mm`:
    - antes del punto inicial: `Y-4.000`
    - despues del punto final: `Y254.000`
    - el calculo coincide con `tool_width / 2 * 2 = 4`.
- Sin estrategia:
  - `Pieza_063` / `Center`:
    - no emite `G41/G42`.
    - entrada `G0 X200.000 Y-4.000`.
    - baja directo a `Z-18.500`.
    - recorre `Y0 -> Y250 -> Y254` en `Z-18.500`.
  - `Pieza_064` / `Right`:
    - entrada auxiliar `G0 X200.000 Y-5.000`.
    - emite `G42`.
    - entra a `G1 X200.000 Y-4.000 Z20.000`.
    - recorre la linea nominal en `X200`.
    - cancela con `G40` y sale a `Y255.000`.
  - `Pieza_065` / `Left`:
    - misma estructura que `Pieza_064`.
    - cambia solo `G42` por `G41`.
  - conclusion parcial:
    - aunque el PGMX contiene `X202/X198` para `Right/Left`, el ISO sin
      estrategia conserva la linea nominal `X200` y delega la correccion al CNC.
- Estrategia unidireccional `PH = 5`:
  - no emite `G41/G42` en ningun lado.
  - emite geometria ya compensada:
    - `Pieza_066` / `Center`: `X200`
    - `Pieza_067` / `Right`: `X202`
    - `Pieza_068` / `Left`: `X198`
  - niveles:
    - `Z-5.000`
    - `Z-10.000`
    - `Z-15.000`
    - `Z-18.500`
  - conserva el sentido frente -> atras en cada pasada:
    - baja en `Y-4/Y0`
    - corta hasta `Y250`
    - sube a `Z20`
    - vuelve a `Y0` en `Z20`
    - baja al siguiente nivel.
  - en la pasada final extiende hasta `Y254` antes de subir.
- Estrategia bidireccional `PH = 5`:
  - no emite `G41/G42` en ningun lado.
  - emite geometria ya compensada:
    - `Pieza_069` / `Center`: `X200`
    - `Pieza_070` / `Right`: `X202`
    - `Pieza_071` / `Left`: `X198`
  - alterna el sentido por nivel sin retornos a altura segura:
    - `Z-5.000`: `Y0 -> Y250`
    - `Z-10.000`: `Y250 -> Y0`
    - `Z-15.000`: `Y0 -> Y250`
    - `Z-18.500`: `Y250 -> Y0`
  - en la pasada final extiende hasta `Y-4` antes de subir.
- Conclusion:
  - fresado lineal E004 confirma el patron general:
    - sin estrategia, `Right/Left` usa compensacion CNC `G42/G41` y trayectoria
      nominal.
    - con estrategia, el postprocesador desactiva `G41/G42` y emite coordenadas
      compensadas.
  - `Center` nunca usa `G41/G42`.
  - `Line + Quote + 2` si afecta el ISO: agrega las extensiones `Y-4` y `Y254`
    en sentido frente -> atras, o `Y-4` como salida final cuando la ultima
    pasada bidireccional termina atras -> frente.
  - `Unidirectional + SafetyHeight` agrega retornos a `Z20` entre niveles.
  - `Bidirectional` baja al siguiente nivel en el extremo donde termina la
    pasada anterior.

### Ronda 42 - Piezas 072 a 086 con entradas/salidas en fresados de contorno

- Estado: postprocesado Maestro/CNC recibido y analizado.
- Objetivo:
  - cubrir los ejemplos minimos necesarios para estudiar el impacto de
    acercamiento/alejamiento en fresados circulares, polilineas abiertas,
    polilineas cerradas y escuadrados.
- Modos probados:
  - `Arc + Quote`, radio `2`
  - `Line + Quote`, radio `2`
  - `Line + Down` / `Line + Up`, radio `2`
  - `Arc + Down` / `Arc + Up`, radio `2`
- Archivos generados:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_072.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_073.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_074.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_075.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_076.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_077.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_078.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_079.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_080.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_081.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_082.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_083.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_084.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_085.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_086.pgmx`
- Parametros comunes:
  - pieza `400 x 250 x 18`
  - origen `(5, 5, 25)`
  - sin estrategia multipasada
  - para circulos/polilineas:
    - escuadrado antihorario estandar primero
    - herramienta del mecanizado probado `1903 / E004`
    - `tool_width = 4.0`
    - `SideOfFeature = Center`
    - profundidad pasante `Extra = 0.5`
  - para escuadrados:
    - herramienta `1900 / E001`
    - `tool_width = 18.36`
    - `winding = CounterClockwise`
    - `SideOfFeature = Right`
    - profundidad pasante `Extra = 1`.

| Archivo | Familia | Entrada/salida | SHA256 PGMX |
| --- | --- | --- | --- |
| `Pieza_072.pgmx` | circulo E004 centro antihorario | `Arc + Quote`, radio `2` | `ACD1D13C9A33BCBFC4610AC5343489A1E7F564A1E910A1C24A6DD22843CF9890` |
| `Pieza_073.pgmx` | circulo E004 centro antihorario | `Line + Quote`, radio `2` | `146138C2C3E709B049A1EFA72CF05025EF5DC1D58935C50FB2BF4AA85DD131FF` |
| `Pieza_074.pgmx` | circulo E004 centro antihorario | `Line + Down/Up`, radio `2` | `9DA0B9A18169413427DFAAD08425D416F59FC5E7027CA7109AF487AC360D33C1` |
| `Pieza_075.pgmx` | circulo E004 centro antihorario | `Arc + Down/Up`, radio `2` | `C41EBEC9458B663EC433FC683514B8618F7D09A0DDE389B87B162C14CA259588` |
| `Pieza_076.pgmx` | polilinea abierta E004 centro | `Arc + Quote`, radio `2` | `AF55E6AC9E0A0E0905CF3CC60FF4FEFC7D45B320C37E700F66040F23F5529919` |
| `Pieza_077.pgmx` | polilinea abierta E004 centro | `Line + Quote`, radio `2` | `EBCCDE3CC8CF5E58CBAD9F42B40BAB59D559FC59F1CB7B36EA0FACDB4D553AF4` |
| `Pieza_078.pgmx` | polilinea abierta E004 centro | `Line + Down/Up`, radio `2` | `FA6025C91A85AB9352E6CC7B5245E942D361931023DCA8DF751176D7F6DCB9E9` |
| `Pieza_079.pgmx` | polilinea abierta E004 centro | `Arc + Down/Up`, radio `2` | `B69299E62C1FAD8B10596D21FC80D8134750DB96DEBA7AB6025A696A4FD395D8` |
| `Pieza_080.pgmx` | polilinea cerrada E004 centro | `Arc + Quote`, radio `2` | `65A43515AFB30272C31A8BD16F654A484138AE2ED5A20AAD8B75FE5C256E0706` |
| `Pieza_081.pgmx` | polilinea cerrada E004 centro | `Line + Quote`, radio `2` | `3122E8C8638DA7F2B5F3E36C7E5AE189FD52E421EDE546FCFAF10CA769F1FC2B` |
| `Pieza_082.pgmx` | polilinea cerrada E004 centro | `Line + Down/Up`, radio `2` | `DE1F6D52ABCE8753CF1AF63405258D2E2F7ECFA93F4A583F3FD4C4CC42506F3D` |
| `Pieza_083.pgmx` | polilinea cerrada E004 centro | `Arc + Down/Up`, radio `2` | `B7C8957011ADAD573DE7AD43073DA36927A7085B0EA609520CA299AF327D4FF7` |
| `Pieza_084.pgmx` | escuadrado E001 antihorario | `Line + Quote`, radio `2` | `120FDB253725B3FCF938F0D1A6395F52F83075C0B2DB06B901683CA49C60C210` |
| `Pieza_085.pgmx` | escuadrado E001 antihorario | `Line + Down/Up`, radio `2` | `8AE2796CBBC26D80FBE219DACF5709E1CEF2DC4C8266F723FE7A1A2FE76DE772` |
| `Pieza_086.pgmx` | escuadrado E001 antihorario | `Arc + Down/Up`, radio `2` | `FFDDCFB857AFF8525279C053EA2B2EC36132AA4CB9863314190C1C3512BD0AFE` |

- Validacion local con `pgmx_snapshot` y `pgmx_adapters`:
  - `Pieza_072` a `Pieza_083`:
    - `features = 2`
    - `operations = 2`
    - `working_steps = 3`
    - `adapted = 2`
    - `unsupported = 0`
    - `ignored = 1`
    - siempre incluye `SquaringMillingSpec` estandar + mecanizado E004.
  - `Pieza_084` a `Pieza_086`:
    - `features = 1`
    - `operations = 1`
    - `working_steps = 2`
    - `adapted = 1`
    - `unsupported = 0`
    - `ignored = 1`
    - solo incluye `SquaringMillingSpec`.
  - todos los adaptadores recuperan el `approach` y `retract` con:
    - `is_enabled = True`
    - `radius_multiplier = 2.0`
    - tipo/modo segun tabla.
- Archivos ISO analizados:
  - `P:\USBMIX\ProdAction\ISO\pieza_072.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_073.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_074.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_075.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_076.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_077.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_078.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_079.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_080.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_081.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_082.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_083.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_084.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_085.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_086.iso`
- Propiedades ISO:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | ---: | ---: | --- | --- |
| `pieza_072.iso` | `146` | `2308` | `855EEC394F754CA2CF6C88C08C9BCF2146042EB47FE76E9EC3BA9D10DA384655` | `651E640B49705D7F74632533118EECBCB041F5DD20BED920F41FE6DEC5311E00` |
| `pieza_073.iso` | `146` | `2272` | `71D8CB8815C5EC7C01237496914AD071AB1D9DBC21B9212D79C538BE2C364518` | `9A2378FEEF4A6E513D04F846B44627CA18CA3AE97889E3071072558325A1978C` |
| `pieza_074.iso` | `145` | `2237` | `23871F1BD6C6418BCB1CC7011AE5778A69B209931EFE1ABCCBE4F3160C17ACCB` | `0185D7F0C58AB621B9A3AF98ACB7237E7D51727DD3CB04F465895A38DD450080` |
| `pieza_075.iso` | `145` | `2291` | `FEB60AB815EE9C09F732ADB3E689E1A1034EC1233E009243BF5A556AE2910EA9` | `20429BB5C32553147F64F7E4624DAF212166F3476D449B26EC0F406CE1641340` |
| `pieza_076.iso` | `147` | `2301` | `A330BB77E6C407E3CDBEDF706EAA68EA4CCF31C0C7B35D884001C6593B16DD17` | `54DE05F151C16F4A390162317E5AE2C3CD0D23FDD71B1EE2B61BA5B6717E2625` |
| `pieza_077.iso` | `147` | `2266` | `6C5B7AFAE3FEF038F9796FC597BD9DBC553A761C169E7365781EA1C3C6D208A9` | `1A330E7B72D362C53596AE4B9AEAAD0AE7EB8F1990EFA4AC2634F639C67B3679` |
| `pieza_078.iso` | `146` | `2249` | `D5AC0F4B3929B28F54354BF51E7806CB6544D91531EBF91105D88F8D3E305239` | `0932D33A05B28FED6A314BD050ADF6EC78D9C7A173C5AD891BFCC7BE5B0DAD29` |
| `pieza_079.iso` | `146` | `2284` | `5F25F237B0DDCC83D4BA020B44C96B91AA3C2FB697D718E703E793CB24817A3A` | `1DF45AD1AA216F00FEEAED2CA2EFA8EB381D85DF71D5F33476B1AD185FECED1E` |
| `pieza_080.iso` | `149` | `2364` | `C812615EBFC5E0EE47A59869E1CF71E3BBCCC13819F4D606DD207A921F292A69` | `4667D4CBDAA22B17E30654F2BC19C4068429D742D63916D461C1349E17ED7B36` |
| `pieza_081.iso` | `149` | `2332` | `2093C836FFE64E530DE545202C859784C4F3473FF5706C8FFCF020C23ABFA17A` | `324C64C285E6FE4851A6A587D551969FB80F4E1B7A18A4658FDA49D32F461767` |
| `pieza_082.iso` | `148` | `2297` | `1BE75EEE14FF1EE623D0CEBE4671B00475FE8FB447F20E9B8A89FC49DF31913A` | `4F91824B47E08CCA52CF74AC0BB5666A5E53A473BADFBCF564277ECAF3E35B8A` |
| `pieza_083.iso` | `148` | `2347` | `988CBB8389ED1BF770FEE5EA9D99145CB596622CEB947A735949DD898904EA2B` | `9269D78C8C9FE430EF42E5DCED756454AC436B90E7C94F64CE0C3713D97FCEC3` |
| `pieza_084.iso` | `107` | `1650` | `EFD790FD854154ABE98387080F54335497D1AA7A7206364EE893208B471A27F5` | `0F8A1FCE6DF0E6E4B2756AB4241FA786908E3F58814ECE5E09DAE8EC3FA761B9` |
| `pieza_085.iso` | `105` | `1602` | `55A3784C860D9F3561BBC20430D0D7D814F42E0422B98468C9356876DC9696A7` | `D8DCFE9CD3F24D7CFC5E7BD6575E95258D5427D0EBE7C6C662A57E45030BA8E8` |
| `pieza_086.iso` | `105` | `1660` | `CA69DA04EA7E51406CD769B2FC216E770AD257F37936A88CCDC9223AC5B79781` | `B851543D64FC845DE901FD7CC70D9BD970FBC8EE1FFEEFF726737F4AC7B2C152` |

- Regla comun de distancia:
  - con E004 y radio multiplicador `2`, la distancia efectiva de lead es
    `4 mm` (`tool_width / 2 * 2`).
  - con E001 y radio multiplicador `2`, la distancia efectiva de lead es
    `18.36 mm` (`tool_width / 2 * 2`).
- Circulos E004 centrados:
  - en todos los casos conserva circulo nominal, sin `G41/G42`.
  - `Arc + Quote`:
    - entra en `G0 X246.000 Y121.000`.
    - baja vertical a `Z-18.500`.
    - usa arco de entrada en cota:
      `G3 X250.000 Y125.000 I246.000 J125.000`.
    - usa arco de salida en cota:
      `G3 X246.000 Y129.000 I246.000 J125.000`.
  - `Line + Quote`:
    - entra en `G0 X250.000 Y121.000`.
    - baja vertical a `Z-18.500`.
    - usa entrada lineal en cota hasta `Y125`.
    - sale linealmente en cota hasta `Y129`.
  - `Line + Down/Up`:
    - entra en `G0 X250.000 Y121.000`.
    - no hay bajada vertical separada.
    - la entrada es `G1 Y125.000 Z-18.500`.
    - la salida es `G1 Y129.000 Z20.000`.
  - `Arc + Down/Up`:
    - entra en `G0 X246.000 Y121.000`.
    - no hay bajada vertical separada.
    - el arco de entrada ya interpola Z:
      `G3 X250.000 Y125.000 Z-18.500 I246.000 J125.000`.
    - el arco de salida sube durante el arco:
      `G3 X246.000 Y129.000 Z20.000 I246.000 J125.000`.
- Polilineas abiertas E004 centradas:
  - no emiten `G41/G42`.
  - conservan la polilinea nominal:
    `(150, 0) -> (100, 150) -> (300, 100) -> (250, 250)`.
  - `Arc + Quote`:
    - entrada `G0 X147.470 Y-5.060`.
    - baja vertical a `Z-18.500`.
    - arco de entrada:
      `G3 X150.000 Y0.000 I146.205 J-1.265`.
    - arco de salida:
      `G3 X244.940 Y252.530 I246.205 J248.735`.
  - `Line + Quote`:
    - entrada `G0 X151.265 Y-3.795`.
    - baja vertical a `Z-18.500`.
    - entrada lineal a `(150, 0)`.
    - salida lineal a `(248.735, 253.795)`.
  - `Line + Down/Up`:
    - misma XY de lead que `Line + Quote`.
    - la bajada se integra en la entrada:
      `G1 X150.000 Y0.000 Z-18.500`.
    - la subida se integra en la salida:
      `G1 X248.735 Y253.795 Z20.000`.
  - `Arc + Down/Up`:
    - misma geometria XY que `Arc + Quote`.
    - el arco de entrada baja a `Z-18.500`.
    - el arco de salida sube a `Z20`.
- Polilineas cerradas E004 centradas:
  - no emiten `G41/G42`.
  - conservan el contorno nominal:
    `(200, 50) -> (350, 50) -> (350, 200) -> (50, 200) -> (50, 50) -> (200, 50)`.
  - `Arc + Quote`:
    - entrada `G0 X196.000 Y54.000`.
    - baja vertical a `Z-18.500`.
    - arco de entrada:
      `G3 X200.000 Y50.000 I200.000 J54.000`.
    - arco de salida:
      `G3 X204.000 Y54.000 I200.000 J54.000`.
  - `Line + Quote`:
    - entrada `G0 X196.000 Y50.000`.
    - baja vertical a `Z-18.500`.
    - entrada lineal hasta `X200`.
    - salida lineal hasta `X204`.
  - `Line + Down/Up`:
    - la bajada se integra en `G1 X200.000 Z-18.500`.
    - la subida se integra en `G1 X204.000 Z20.000`.
  - `Arc + Down/Up`:
    - el arco de entrada baja a `Z-18.500`.
    - el arco de salida sube a `Z20`.
- Escuadrados E001:
  - las tres variantes mantienen compensacion CNC activa:
    - `G42`
    - geometria nominal del rectangulo.
  - esto contrasta con escuadrado E001 con estrategia `PH = 5`, donde Maestro
    habia pasado a geometria compensada sin `G41/G42`.
  - `Line + Quote`:
    - entrada auxiliar `G0 X180.640 Y0.000`.
    - activa `G42`.
    - entra a `G1 X181.640 Y0.000 Z20.000`.
    - baja vertical con `G1 Z-19.000`.
    - lead lineal en cota hasta `X200`.
    - salida en cota hasta `X218.360`.
    - sube vertical y cancela `G40`.
  - `Line + Down/Up`:
    - mantiene `G42`.
    - la bajada se integra en `G1 X200.000 Z-19.000`.
    - la subida se integra en `G1 X218.360 Z20.000`.
  - `Arc + Down/Up`:
    - mantiene `G42`.
    - entrada auxiliar `G0 X181.640 Y-19.360`.
    - arco de entrada con bajada:
      `G2 X200.000 Y0.000 Z-19.000 I200.000 J-18.360`.
    - arco de salida con subida:
      `G2 X218.360 Y-18.360 Z20.000 I200.000 J-18.360`.
- Conclusion:
  - `Quote` significa que el postprocesador separa el cambio de Z:
    - baja/sube verticalmente.
    - luego ejecuta la entrada/salida en la cota de corte o de seguridad.
  - `Down/Up` integra el cambio de Z dentro de la linea o arco de
    acercamiento/alejamiento.
  - `Line` produce segmentos `G1`.
  - `Arc` produce arcos `G2/G3` con centros `I/J`.
  - en mecanizados E004 centrados no aparece compensacion CNC.
  - en escuadrado E001 sin estrategia, incluso cambiando entrada/salida,
    se conserva la regla de compensacion CNC `G42`.

### Ronda 43 - Piezas 087 a 091 con ranuras validas `SlotSide`

- Estado: postprocesado Maestro/CNC recibido y analizado.
- Objetivo:
  - cerrar los casos validos de ranuras superiores horizontales con
    `Sierra Vertical X`.
  - descartar de la investigacion las ranuras con otras orientaciones,
    orientaciones invalidas o profundidad mayor a `10 mm`, porque Maestro
    advierte el error y no genera ISO.
- Archivos generados:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_087.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_088.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_089.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_090.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_091.pgmx`
- Parametros comunes:
  - pieza `400 x 250 x 18`
  - origen `(5, 5, 25)`
  - cara `Top`
  - feature `a:SlotSide`
  - herramienta `1899 / 082` (`Sierra Vertical X`)
  - `tool_width = 3.8`
  - `end_radius = 60`
  - sin acercamiento/alejamiento explicito
  - sin estrategia multipasada.

| Archivo | Recorrido PGMX | `SideOfFeature` | Profundidad | SHA256 PGMX |
| --- | --- | --- | ---: | --- |
| `Pieza_087.pgmx` | `(50, 125) -> (350, 125)` | `Center` | `10` | `7DCEAA9981D064F590CD05464167207BC7BC7EC19CE08E4BF902424601658EE4` |
| `Pieza_088.pgmx` | `(50, 125) -> (350, 125)` | `Right` | `10` | `2B399A70248066CCFF02B71DD5E30AFD1AF4CEBB615BCF7A55F7539A1C2B0B76` |
| `Pieza_089.pgmx` | `(50, 125) -> (350, 125)` | `Left` | `10` | `8D4DA4C07B0933DDB5F6F141CA91CEC657A758A463BEE800300CAB451A0872B6` |
| `Pieza_090.pgmx` | `(50, 125) -> (350, 125)` | `Center` | `5` | `0A511A300BE5490BB19688190721EC1ABD29179AE8F0DC9FD625FF828C3923B7` |
| `Pieza_091.pgmx` | `(100, 125) -> (300, 125)` | `Center` | `10` | `133F2AC1CF0FC29DF631AD3FD1841AB97BB6234CA72F1ADF861CE937E32C68B0` |

- Validacion local con `pgmx_snapshot` y `pgmx_adapters`:
  - en los cinco archivos:
    - `features = 1`
    - `operations = 1`
    - `working_steps = 2`
    - `adapted = 1`
    - `unsupported = 0`
    - `ignored = 1`
    - `slot_millings = 1`
  - el adaptador recupera:
    - recorrido pedido
    - `SideOfFeature` pedido
    - `target_depth` pedido
    - `is_through = False`.
- Archivos ISO analizados:
  - `P:\USBMIX\ProdAction\ISO\pieza_087.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_088.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_089.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_090.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_091.iso`
- Propiedades ISO:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | ---: | ---: | --- | --- |
| `pieza_087.iso` | `92` | `1309` | `67A09257E0326F932E1D5A453F237377D1D68453DC318859FA403057C702225F` | `189AAA1F272AA17965C30A9D0ABEC625BE2C80950052CC35D8730405DCBC2DF4` |
| `pieza_088.iso` | `92` | `1309` | `C849DA70D3E2E3ACEF94990625A2B29DF87267D1D8E88F627288E3A5AFE05927` | `B079C318B78BB42F699C55BC7DE968E8ED46A0963AF7A7FE319A2F00A4EB29BD` |
| `pieza_089.iso` | `92` | `1309` | `3F7E630F4FE1888025D7BB15ED7DB13CB62CDFACD99F960905180E103434FEFE` | `6519CED4E90827FB3322F40DB90E5D6BDFCCEDB4059B205AD91A83CB074DC37B` |
| `pieza_090.iso` | `92` | `1307` | `F70F5CDA05A63DD28BCDE7EC58FACABC933954E36FADD1207FF41C51B35D0AB2` | `B2D80295E27BFDC0730921D1714F658A68FD12E5127E685D5C7D6A3A9F50B883` |
| `pieza_091.iso` | `92` | `1310` | `4C32C274FB573C137873CC503A2A8C93BC6CDD6092A36E206BF277D2E0F7B5CE` | `33C9442929D5B43EEB3BF6CE7958CADB2F5923CA2E707AE0AD67076697C80D33` |

- Bloques de ranura observados:

| ISO | Aproximacion | Bajada | Corte |
| --- | --- | --- | --- |
| `pieza_087.iso` | `G0 X350.000 Y125.000` | `G1 Z-10.000 F2000.000` | `G1 X50.000 Z-10.000 F5000.000` |
| `pieza_088.iso` | `G0 X350.000 Y123.100` | `G1 Z-10.000 F2000.000` | `G1 X50.000 Z-10.000 F5000.000` |
| `pieza_089.iso` | `G0 X350.000 Y126.900` | `G1 Z-10.000 F2000.000` | `G1 X50.000 Z-10.000 F5000.000` |
| `pieza_090.iso` | `G0 X350.000 Y125.000` | `G1 Z-5.000 F2000.000` | `G1 X50.000 Z-5.000 F5000.000` |
| `pieza_091.iso` | `G0 X300.000 Y125.000` | `G1 Z-10.000 F2000.000` | `G1 X100.000 Z-10.000 F5000.000` |

- Variables comunes observadas:
  - `?%ETK[6]=82`
  - `G17`
  - `?%ETK[17]=257`
  - `S4000M3`
  - `?%ETK[1]=16`
  - `D1` activo durante la ranura
  - `SVL 60.000` / `VL6=60.000`
  - `SVR 1.900` / `VL7=1.900`
  - `?%ETK[7]=1` durante el avance de corte
  - reset posterior de `SVL`, `SVR`, `D0` y `?%ETK[7]=0`.
- Comparaciones:
  - `pieza_087.iso` tiene el mismo cuerpo que `pieza_006.iso`
    (`body_sha256 = 189AAA1F272AA17965C30A9D0ABEC625BE2C80950052CC35D8730405DCBC2DF4`).
  - `pieza_088.iso` tiene el mismo cuerpo que `pieza_008.iso`
    (`body_sha256 = B079C318B78BB42F699C55BC7DE968E8ED46A0963AF7A7FE319A2F00A4EB29BD`).
  - `pieza_089.iso` tiene el mismo cuerpo que `pieza_009.iso`
    (`body_sha256 = 6519CED4E90827FB3322F40DB90E5D6BDFCCEDB4059B205AD91A83CB074DC37B`).
  - `Pieza_090` confirma que la profundidad no pasante se traduce
    directamente a `Z`:
    - `target_depth = 5 -> Z-5.000`
    - el largo, compensacion, `SVL`, `SVR`, herramienta y velocidades no
      cambian.
  - `Pieza_091` confirma que el largo de la ranura no cambia `SVL`:
    - `end_radius = 60 -> SVL 60.000`
    - el postprocesador sigue cortando desde el `X` mayor al `X` menor:
      `X300 -> X100`.
- Conclusion:
  - quedan cubiertas las ranuras superiores horizontales validas sobre `Top`
    con `Sierra Vertical X`.
  - `SideOfFeature = Center/Right/Left` ya esta confirmado:
    - `Center -> Y nominal`
    - `Right -> Y nominal - 1.900` para la geometria normal estudiada
    - `Left -> Y nominal + 1.900` para la geometria normal estudiada.
  - la profundidad no pasante valida hasta `10 mm` se emite como `Z` negativo
    directo.
  - el largo se expresa solo en los extremos `X` del bloque de corte.
  - `SVL` no representa largo de ranura; representa `end_radius`.
  - no queda una familia adicional de ranuras invalidas para documentar por
    ISO, porque Maestro bloquea esos casos antes del postprocesado.

### Ronda 44 - Piezas 092 a 095 con polilinea E004 `Left/Right` y `Down/Up`

- Estado: postprocesado Maestro/CNC recibido y analizado.
- Objetivo:
  - cruzar correccion `Left/Right` con acercamiento/alejamiento integrado en Z
    en una polilinea abierta E004.
  - verificar si `Down/Up` mantiene la compensacion CNC `G41/G42` o si pasa a
    geometria compensada.
- Archivos generados:
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_092.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_093.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_094.pgmx`
  - `S:\Maestro\Projects\ProdAction\ISO\Pieza_095.pgmx`
- Parametros comunes:
  - pieza `400 x 250 x 18`
  - origen `(5, 5, 25)`
  - `ordered_machinings`:
    1. escuadrado antihorario E001 estandar
    2. fresado de polilinea E004
  - polilinea nominal:
    `(150, 0) -> (100, 150) -> (300, 100) -> (250, 250)`
  - herramienta `1903 / E004`
  - `tool_width = 4.0`
  - profundidad pasante `Extra = 0.5`
  - radio de acercamiento/alejamiento `2`.

| Archivo | `SideOfFeature` | Entrada/salida | SHA256 PGMX |
| --- | --- | --- | --- |
| `Pieza_092.pgmx` | `Left` | `Line + Down/Up` | `1A3A9171EAE5F372D623FCA8CE5BB4F4B17A399790C048FEB60949968A13EAFE` |
| `Pieza_093.pgmx` | `Right` | `Line + Down/Up` | `F55AF6622E9B4D5CCDDA07A44F8758F2656801F120D36D6F963731A9110F4B25` |
| `Pieza_094.pgmx` | `Left` | `Arc + Down/Up` | `6B8416A3532E9BA7AB7CCEF542141F329B4C93FD8D597E17FB8C4CA6F4E3C04C` |
| `Pieza_095.pgmx` | `Right` | `Arc + Down/Up` | `80783995868C251BE1A8A5176068EE03C46408B2F5A84441FD6AB4163FFD6AA5` |

- Validacion local con `pgmx_snapshot` y `pgmx_adapters`:
  - en los cuatro archivos:
    - `features = 2`
    - `operations = 2`
    - `working_steps = 3`
    - `adapted = 2`
    - `unsupported = 0`
    - `ignored = 1`
    - `squaring_millings = 1`
    - `polyline_millings = 1`
  - el adaptador recupera:
    - `SideOfFeature` pedido
    - herramienta `1903 / E004`
    - pasante `Extra = 0.5`
    - `Approach = Line + Down` o `Arc + Down`
    - `Retract = Line + Up` o `Arc + Up`
    - `radius_multiplier = 2.0`.
- Archivos ISO analizados:
  - `P:\USBMIX\ProdAction\ISO\pieza_092.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_093.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_094.iso`
  - `P:\USBMIX\ProdAction\ISO\pieza_095.iso`
- Propiedades ISO:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | ---: | ---: | --- | --- |
| `pieza_092.iso` | `149` | `2329` | `F358E2D7EA574C5421604069EE18AD27ECBA86D3B61C5E85EA3ABBA15D90D511` | `D1F8751626D1A97B02DE9089BCCF17DB181AF375B2875C1A29620E381DD90A67` |
| `pieza_093.iso` | `149` | `2329` | `8BAF68F2706C39249E0376329EA0B8494AB0F6B90D192F21847E91D575B0002C` | `99E8381CFD419A1F8BEF40309FBFC048C944E8039658D241A750747354A4AA18` |
| `pieza_094.iso` | `149` | `2364` | `99779AAD391EEFCCF036F93EFA40BF4BCE4003B97F2FA416B84A3E147EF9CD53` | `B3727A5FA3145315D95E80A7D43E718C96AD3A01464B5991B1DE80B290FDE857` |
| `pieza_095.iso` | `149` | `2363` | `319AF332564974D83363A0F51259F75E740A364A68DE96654072AACAFA89493D` | `6D83DCA1975BED71043542BDCB9E5B90E5F7CF1A34A0157E901944EAA7F880D4` |

- Bloques E004 observados:

| ISO | Correccion | Entrada | Lead a profundidad | Salida |
| --- | --- | --- | --- | --- |
| `pieza_092.iso` | `G41` | `G0 X151.581 Y-4.743`; `G1 X151.265 Y-3.795 Z20.000` | `G1 X150.000 Y0.000 Z-18.500` | `G1 X248.735 Y253.795 Z20.000`; `G40`; `G1 X248.419 Y254.743 Z20.000` |
| `pieza_093.iso` | `G42` | `G0 X151.581 Y-4.743`; `G1 X151.265 Y-3.795 Z20.000` | `G1 X150.000 Y0.000 Z-18.500` | `G1 X248.735 Y253.795 Z20.000`; `G40`; `G1 X248.419 Y254.743 Z20.000` |
| `pieza_094.iso` | `G41` | `G0 X146.521 Y-5.376`; `G1 X147.470 Y-5.060 Z20.000` | `G3 X150.000 Y0.000 Z-18.500 I146.205 J-1.265` | `G3 X244.940 Y252.530 Z20.000 I246.205 J248.735`; `G40`; `G1 X243.992 Y252.214 Z20.000` |
| `pieza_095.iso` | `G42` | `G0 X156.008 Y-2.214`; `G1 X155.060 Y-2.530 Z20.000` | `G2 X150.000 Y0.000 Z-18.500 I153.795 J1.265` | `G2 X252.530 Y255.060 Z20.000 I253.795 J251.265`; `G40`; `G1 X253.479 Y255.376 Z20.000` |

- Comparaciones:
  - `pieza_092.iso` y `pieza_093.iso` difieren solo en:
    - nombre de programa.
    - `G41` vs `G42`.
  - con `Line + Down/Up`, `Left/Right` no cambia las coordenadas auxiliares:
    - el postprocesador agrega un tramo previo de `1 mm` para activar la
      compensacion antes del lead integrado.
    - luego ejecuta el mismo lead observado en la variante centrada
      `Pieza_078`.
    - despues del lead de salida, cancela `G40` y agrega otro tramo de `1 mm`
      a altura segura.
  - `pieza_094.iso` y `pieza_095.iso` difieren en:
    - nombre de programa.
    - `G41` vs `G42`.
    - coordenadas auxiliares de entrada/salida.
    - sentido de arco:
      - `Left -> G3`
      - `Right -> G2`
    - centros `I/J` de los arcos.
  - con `Arc + Down/Up`, `Left/Right` no es solo una diferencia de
    compensacion CNC: `ArcSide = Automatic` selecciona lados de arco
    espejados para entrar y salir por el lado compatible con la correccion.
  - en los cuatro casos el contorno nominal de la polilinea se conserva:
    - `G1 X100.000 Y150.000`
    - `G1 X300.000 Y100.000`
    - `G1 X250.000 Y250.000`
  - en los cuatro casos, `Extra = 0.5` vuelve a emitirse como `Z-18.500`.
- Conclusion:
  - sin estrategia multipasada, las polilineas E004 `Left/Right` siguen usando
    compensacion CNC `G41/G42` aunque la entrada/salida sea `Down/Up`.
  - `Line + Down/Up` integra la bajada/subida en segmentos `G1` y solo agrega
    tramos extra de activacion/cancelacion de compensacion.
  - `Arc + Down/Up` integra la bajada/subida en arcos `G2/G3`; para
    `Left/Right`, el postprocesador modifica lado y sentido de arco.
  - no aparece geometria de polilinea compensada; la compensacion del perfil
    principal queda delegada al CNC.

## Cierre parcial de ingenieria inversa ISO

Estado al pausar la investigacion:
- queda documentado el flujo `PGMX sintetico -> postprocesado Maestro/CNC -> ISO`
  para piezas simples, taladros verticales/laterales, ranuras, fresados,
  escuadrados y piezas con operaciones combinadas.
- los archivos de estudio principales quedaron en:
  - `S:\Maestro\Projects\ProdAction\ISO`
  - `P:\USBMIX\ProdAction\ISO`
- a partir de `Pieza_001`, las piezas de estudio usan:
  - origen fijo `(5, 5, 25)`
  - nombres ascendentes `Pieza_001`, `Pieza_002`, etc.
  - sin medidas/origen codificados en el nombre.

Reglas firmes hasta ahora:
- Cabecera ISO:
  - `DX = length + origin_x`
  - `DY = width + origin_y`
  - `DZ = depth + origin_z`
  - `BX/BY/BZ` siguen en `0` en los casos estudiados.
- Taladros verticales `Top`:
  - `ToolKey` debe quedar resuelto en PGMX para las brocas verticales conocidas.
  - `ETK[6]` identifica la broca vertical `001..007`.
  - `ETK[0]` usa mascara binaria para verticales:
    - `001 -> 1`
    - `002 -> 2`
    - `003 -> 4`
    - `004 -> 8`
    - `005 -> 16`
    - `006 -> 32`
    - `007 -> 64`
  - `SHF[X/Y/Z]` representa offsets mecanicos de la broca en el cabezal.
  - con `tool_offset_length = 77`, los taladros verticales estudiados usan
    `G0 Z115` y `G1 G9 Z77`.
  - en no pasante D8/001, la cota de corte cambia con la profundidad:
    - `target_depth = 15` -> `G1 G9 Z80`
    - pasante `18` -> `G1 G9 Z77`
  - en el caso D8/001 estudiado, `Extra = 1` no cambia el ISO respecto de
    `Extra = 0`, aunque el PGMX conserva `TrajectoryPath = 19`.
  - el feed observado parece responder a `min(descent_speed, feed_rate) * 1000`.
- Taladros laterales/frontal/posterior:
  - el PGMX sintetico debe dejar `ToolKey` vacio por defecto.
  - Maestro/postprocesador resuelve la broca real desde cara/trayectoria.
  - `ETK[6]` observado:
    - `Front -> 58`
    - `Back -> 59`
    - `Left -> 61`
    - `Right -> 60`
  - `ETK[8]` observado:
    - `Front -> 5`
    - `Back -> 4`
    - `Left -> 3`
    - `Right -> 2`
  - `ETK[0]` observado:
    - `Front/Back -> 1073741824`
    - `Left/Right -> 2147483648`
  - con `tool_offset_length = 65`, el ISO desplaza `65 mm` sobre el eje de
    perforacion.
  - espejos confirmados con agujeros no centrados:
    - `Back` espeja `X`
    - `Left` espeja `Y`
    - `Front` conserva `X`
    - `Right` conserva `Y`
- Ranuras superiores `SlotSide`:
  - casos validados:
    - `Pieza_006.pgmx -> pieza_006.iso`
    - `Pieza_007.pgmx -> pieza_007.iso`
    - `Pieza_008.pgmx -> pieza_008.iso`
    - `Pieza_009.pgmx -> pieza_009.iso`
    - `Pieza_010.pgmx -> pieza_010.iso`
    - `Pieza_011.pgmx -> pieza_011.iso`
    - `Pieza_087.pgmx -> pieza_087.iso`
    - `Pieza_088.pgmx -> pieza_088.iso`
    - `Pieza_089.pgmx -> pieza_089.iso`
    - `Pieza_090.pgmx -> pieza_090.iso`
    - `Pieza_091.pgmx -> pieza_091.iso`
  - herramienta:
    - `ToolKey.Name = 082`
    - ISO `?%ETK[6]=82`
    - `S4000M3`
  - variables especificas:
    - `SVL = end_radius`
    - `SVR = tool_width / 2`
    - `D1` activo durante el corte
    - `?%ETK[7]=1` durante el avance de ranura
  - profundidad:
    - `target_depth = 10` se emite como `G1 Z-10.000`.
    - `target_depth = 5` se emite como `G1 Z-5.000`.
    - profundidades mayores a `10 mm` quedan descartadas para ISO porque
      Maestro advierte el error y no postprocesa.
  - longitud:
    - el largo de la ranura se expresa en los extremos `X` del corte:
      - `(50, 125) -> (350, 125)` se emite como `X350 -> X50`.
      - `(100, 125) -> (300, 125)` se emite como `X300 -> X100`.
    - `SVL` no cambia con el largo; sigue representando `end_radius`.
  - direccion:
    - PGMX `(50, 125) -> (350, 125)` se emitio como corte ISO `X350 -> X50`.
    - PGMX `(350, 125) -> (50, 125)` tambien se emitio como corte ISO
      `X350 -> X50`.
    - el orden de puntos no cambia el ISO en estos dos casos.
    - la direccion unica se explica por la herramienta: la sierra gira en un
      solo sentido y debe cortar en ese sentido para proteger la superficie de
      la placa.
  - compensacion:
    - `SideOfFeature = Center` mantiene la coordenada nominal de la ranura.
    - `SideOfFeature = Right/Left` desplaza la trayectoria `tool_width / 2`
      respecto del sentido geometrico de la linea PGMX.
    - con `tool_width = 3.8`, el ISO desplaza `1.9 mm` en `Y`.
    - este desplazamiento aparece en la linea `G0 X350.000 Y...`; el corte
      lineal posterior conserva ese `Y` modal.
    - `SideOfFeature` no cambia `SHF`, `ETK`, `SVL`, `SVR`, `D1`, profundidad
      ni sentido fisico de corte.
    - para geometria normal `(50, 125) -> (350, 125)`:
      - `Right -> Y123.100`
      - `Left -> Y126.900`
- Fresados superiores con herramientas E003/E004:
  - primer caso validado:
    `Pieza_015.pgmx -> pieza_015.iso`.
  - herramienta:
    - PGMX `ToolKey = 1903 / E004`
    - ISO `T4`, `M06`, `?%ETK[9]=4`, `S18000M3`
  - herramienta E003 observada en polilinea cerrada:
    - PGMX `ToolKey = 1902 / E003`
    - ISO `T3`, `M06`, `?%ETK[9]=3`, `S18000M3`
  - variables:
    - `SVL = 107.200`, coincide con `tool_offset_length` de E004
    - `SVR = 2.000`, coincide con `tool_width / 2`
    - `?%ETK[7]=4` durante el avance de fresado
    - `D1` activo durante el corte
    - para E003:
      - `SVL = 111.500`
      - `SVR = 4.760`
  - avances:
    - bajada `F2000`
    - fresado lineal `F5000`
    - en polilinea cerrada E003 con `Line + Down + 4`, la entrada observada es
      `F3000` y el contorno/salida `F18000`.
  - profundidad:
    - `target_depth = 15` se emite como `G1 Z-15.000`.
    - aunque el toolpath PGMX queda a `Z = 3` por espesor `18`, el ISO usa
      profundidad negativa absoluta.
    - en pasante `Extra = 0.5`, el ISO emite `Z-18.500`.
  - lineas simples:
    - `Pieza_015.pgmx -> pieza_015.iso` (`SideOfFeature = Center`,
      sin estrategia, profundidad `15`)
    - `Pieza_063.pgmx -> pieza_063.iso` (`SideOfFeature = Center`,
      sin estrategia, pasante `Extra = 0.5`)
    - `Pieza_064.pgmx -> pieza_064.iso` (`SideOfFeature = Right`,
      sin estrategia, pasante `Extra = 0.5`)
    - `Pieza_065.pgmx -> pieza_065.iso` (`SideOfFeature = Left`,
      sin estrategia, pasante `Extra = 0.5`)
    - `Pieza_066.pgmx -> pieza_066.iso` (`SideOfFeature = Center`,
      unidireccional `PH = 5`)
    - `Pieza_067.pgmx -> pieza_067.iso` (`SideOfFeature = Right`,
      unidireccional `PH = 5`)
    - `Pieza_068.pgmx -> pieza_068.iso` (`SideOfFeature = Left`,
      unidireccional `PH = 5`)
    - `Pieza_069.pgmx -> pieza_069.iso` (`SideOfFeature = Center`,
      bidireccional `PH = 5`)
    - `Pieza_070.pgmx -> pieza_070.iso` (`SideOfFeature = Right`,
      bidireccional `PH = 5`)
    - `Pieza_071.pgmx -> pieza_071.iso` (`SideOfFeature = Left`,
      bidireccional `PH = 5`)
    - geometria nominal base:
      - `Pieza_015`: `(200, 50) -> (200, 200)`
      - `Pieza_063` a `Pieza_071`: `(200, 0) -> (200, 250)`
    - sin estrategia:
      - `Center`: conserva coordenada nominal y no usa `G41/G42`.
      - `Right`: conserva coordenada nominal y usa `G42`.
      - `Left`: conserva coordenada nominal y usa `G41`.
    - con estrategia `PH = 5`:
      - no usa `G41/G42`.
      - `Right` sale como coordenada compensada `X202`.
      - `Left` sale como coordenada compensada `X198`.
    - `Line + Quote + 2` agrega extension de `4 mm` en la tangente:
      - `Y-4` antes del inicio.
      - `Y254` despues del final para pasadas frente -> atras.
      - en bidireccional, la ultima pasada termina atras -> frente y extiende
        hasta `Y-4`.
    - unidireccional con `SafetyHeight` vuelve a `Z20` entre niveles.
    - bidireccional alterna el sentido por nivel sin retornos a altura segura.
    - regla general de entradas/salidas:
      - `Quote`: baja/sube verticalmente y ejecuta el lead en cota.
      - `Down/Up`: integra el cambio de Z dentro del lead.
      - `Line`: lead con `G1`.
      - `Arc`: lead con `G2/G3`.
  - polilineas abiertas:
    - `Pieza_016.pgmx -> pieza_016.iso` (`SideOfFeature = Left`)
    - `Pieza_017.pgmx -> pieza_017.iso` (`SideOfFeature = Right`)
    - `Pieza_022.pgmx -> pieza_022.iso` (`SideOfFeature = Center`, combinada
      despues de un escuadrado E001)
    - `Pieza_023.pgmx -> pieza_023.iso` (`SideOfFeature = Left`, combinada
      despues de un escuadrado E001)
    - `Pieza_024.pgmx -> pieza_024.iso` (`SideOfFeature = Right`, combinada
      despues de un escuadrado E001)
    - `Pieza_035.pgmx -> pieza_035.iso` (`SideOfFeature = Center`,
      unidireccional `PH = 5`)
    - `Pieza_036.pgmx -> pieza_036.iso` (`SideOfFeature = Center`,
      bidireccional `PH = 5`)
    - `Pieza_076.pgmx -> pieza_076.iso` (`SideOfFeature = Center`,
      `Arc + Quote`, radio `2`)
    - `Pieza_077.pgmx -> pieza_077.iso` (`SideOfFeature = Center`,
      `Line + Quote`, radio `2`)
    - `Pieza_078.pgmx -> pieza_078.iso` (`SideOfFeature = Center`,
      `Line + Down/Up`, radio `2`)
    - `Pieza_079.pgmx -> pieza_079.iso` (`SideOfFeature = Center`,
      `Arc + Down/Up`, radio `2`)
    - `Pieza_092.pgmx -> pieza_092.iso` (`SideOfFeature = Left`,
      `Line + Down/Up`, radio `2`)
    - `Pieza_093.pgmx -> pieza_093.iso` (`SideOfFeature = Right`,
      `Line + Down/Up`, radio `2`)
    - `Pieza_094.pgmx -> pieza_094.iso` (`SideOfFeature = Left`,
      `Arc + Down/Up`, radio `2`)
    - `Pieza_095.pgmx -> pieza_095.iso` (`SideOfFeature = Right`,
      `Arc + Down/Up`, radio `2`)
    - el ISO conserva la geometria nominal de la polilinea y cambia solo la
      compensacion:
      - `Left -> G41`
      - `Right -> G42`
      - `Center -> sin G41/G42`
    - `SVR = 2.000` queda como radio de herramienta para la compensacion.
    - no se emite el arco exterior del `TrajectoryPath` PGMX de `Left` como
      `G2/G3`; la resolucion de la esquina queda en el control CNC.
    - en pasante `Extra = 0.5`, el ISO emite `Z-18.500` para espesor `18`.
    - cuando la polilinea centrada empieza en el punto nominal, no aparece la
      entrada XY de `1 mm` observada en las variantes `Left/Right`.
    - cuando la polilinea usa `Left/Right`, el postprocesador agrega entrada y
      salida auxiliares de `1 mm` sobre la tangente nominal, aun si el PGMX
      tiene toolpath compensado distinto:
      - entrada observada en `Pieza_023/024`: `(150.316, -0.949) -> (150, 0)`
      - salida observada en `Pieza_023/024`: `(250, 250) -> (249.684, 250.949)`
    - con `Line + Down/Up` y `Left/Right`, conserva el mismo lead integrado que
      en `Center`, pero agrega tramos extra de `1 mm` antes de activar el lead
      y despues de cancelar `G40`:
      - entrada: `(151.581, -4.743) -> (151.265, -3.795) -> (150, 0)`.
      - salida: `(250, 250) -> (248.735, 253.795) -> (248.419, 254.743)`.
      - `Left` y `Right` solo difieren en `G41/G42`.
    - con `Arc + Down/Up` y `Left/Right`, el postprocesador tambien cambia el
      lado y sentido de los arcos:
      - `Left -> G41` y arcos `G3`.
      - `Right -> G42` y arcos `G2`.
      - las coordenadas auxiliares y centros `I/J` quedan espejados segun el
        lado de correccion.
    - con estrategia multipasada `PH = 5`, el ISO baja por niveles:
      - `Z-5.000`
      - `Z-10.000`
      - `Z-15.000`
      - `Z-18.500`
    - en unidireccional con `SafetyHeight`, el postprocesador sube a `Z20`
      entre pasadas y vuelve al inicio recorriendo la polilinea en inversa a
      altura segura.
    - en bidireccional, el postprocesador baja en el extremo donde termina la
      pasada anterior y alterna el sentido de corte sin retornos intermedios a
      altura segura.
    - en entradas/salidas centradas:
      - `Arc + Quote`: vertical a profundidad y arcos en cota.
      - `Line + Quote`: vertical a profundidad y lineas en cota.
      - `Line + Down/Up`: lineas con Z integrado.
      - `Arc + Down/Up`: arcos con Z integrado.
  - polilineas cerradas:
    - `Pieza_037.pgmx -> pieza_037.iso` (`SideOfFeature = Center`, E003,
      sentido pedido)
    - `Pieza_038.pgmx -> pieza_038.iso` (`SideOfFeature = Center`, E003,
      sentido inverso)
    - `Pieza_039.pgmx -> pieza_039.iso` (`SideOfFeature = Center`, E003,
      sentido pedido, unidireccional `PH = 5`)
    - `Pieza_040.pgmx -> pieza_040.iso` (`SideOfFeature = Center`, E003,
      sentido inverso, unidireccional `PH = 5`)
    - `Pieza_041.pgmx -> pieza_041.iso` (`SideOfFeature = Right`, E003,
      sentido pedido, unidireccional `PH = 5`)
    - `Pieza_042.pgmx -> pieza_042.iso` (`SideOfFeature = Left`, E003,
      sentido pedido, unidireccional `PH = 5`)
    - `Pieza_043.pgmx -> pieza_043.iso` (`SideOfFeature = Right`, E003,
      sentido inverso, unidireccional `PH = 5`)
    - `Pieza_044.pgmx -> pieza_044.iso` (`SideOfFeature = Left`, E003,
      sentido inverso, unidireccional `PH = 5`)
    - `Pieza_045.pgmx -> pieza_045.iso` (`SideOfFeature = Center`, E003,
      sentido pedido, bidireccional `PH = 5`)
    - `Pieza_046.pgmx -> pieza_046.iso` (`SideOfFeature = Center`, E003,
      sentido inverso, bidireccional `PH = 5`)
    - `Pieza_080.pgmx -> pieza_080.iso` (`SideOfFeature = Center`, E004,
      `Arc + Quote`, radio `2`)
    - `Pieza_081.pgmx -> pieza_081.iso` (`SideOfFeature = Center`, E004,
      `Line + Quote`, radio `2`)
    - `Pieza_082.pgmx -> pieza_082.iso` (`SideOfFeature = Center`, E004,
      `Line + Down/Up`, radio `2`)
    - `Pieza_083.pgmx -> pieza_083.iso` (`SideOfFeature = Center`, E004,
      `Arc + Down/Up`, radio `2`)
    - el ISO conserva la geometria nominal y explicita el cierre con una linea
      final al punto inicial.
    - no emite `G41/G42` para `Center`.
    - tampoco emite `G41/G42` para `Left/Right` en esta familia cerrada E003;
      la compensacion llega como coordenadas ya desplazadas.
    - `Line + Down + 4` genera una entrada oblicua desde un punto a `19.04 mm`
      del inicio, calculado como `(tool_width / 2) * 4`.
    - `Line + Up + 4` genera una salida oblicua de `19.04 mm` desde el punto
      final, que en este caso coincide con el inicio por ser un perfil cerrado.
    - invertir el sentido espeja los puntos de entrada/salida:
      - sentido pedido: entrada `X180.960`, salida `X219.040`
      - sentido inverso: entrada `X219.040`, salida `X180.960`
    - profundidad `target_depth = 15` se emite como `Z-15.000`.
    - con unidireccional `PH = 5` sobre perfil cerrado, el ISO repite el
      contorno en `Z-5.000`, `Z-10.000` y `Z-15.000`.
    - en esta familia cerrada no aparece retorno a altura segura entre niveles:
      la bajada se hace en el punto de cierre `(200, 50)` y se vuelve a recorrer
      el contorno en el mismo sentido.
    - para `Left/Right`, el offset depende del sentido:
      - sentido pedido + `Right` y sentido inverso + `Left` generan offset
        exterior con arcos de esquina.
      - sentido pedido + `Left` y sentido inverso + `Right` generan offset
        interior como rectangulo reducido sin arcos.
    - con bidireccional `PH = 5`, alterna el sentido por nivel:
      - `Z-5.000`: sentido inicial
      - `Z-10.000`: sentido opuesto
      - `Z-15.000`: vuelve al sentido inicial
    - la estrategia bidireccional no cambia cantidad de lineas ni bytes frente
      a la unidireccional centrada; solo cambia el orden de vertices del nivel
      intermedio.
    - en entradas/salidas E004 centradas, la regla `Quote` vs `Down/Up` y
      `Line` vs `Arc` coincide con la observada en lineas simples y polilineas
      abiertas.
  - circulos cerrados:
    - `Pieza_025.pgmx -> pieza_025.iso` (`CounterClockwise`, `SideOfFeature = Center`)
    - `Pieza_026.pgmx -> pieza_026.iso` (`Clockwise`, `SideOfFeature = Center`)
    - `Pieza_027.pgmx -> pieza_027.iso` (`CounterClockwise`, `SideOfFeature = Left`)
    - `Pieza_028.pgmx -> pieza_028.iso` (`CounterClockwise`, `SideOfFeature = Right`)
    - `Pieza_029.pgmx -> pieza_029.iso` (`Clockwise`, `SideOfFeature = Left`)
    - `Pieza_030.pgmx -> pieza_030.iso` (`Clockwise`, `SideOfFeature = Right`)
    - `Pieza_047.pgmx -> pieza_047.iso` (`CounterClockwise`,
      `SideOfFeature = Center`, unidireccional `PH = 5`)
    - `Pieza_048.pgmx -> pieza_048.iso` (`Clockwise`,
      `SideOfFeature = Center`, unidireccional `PH = 5`)
    - `Pieza_049.pgmx -> pieza_049.iso` (`CounterClockwise`,
      `SideOfFeature = Center`, bidireccional `PH = 5`)
    - `Pieza_050.pgmx -> pieza_050.iso` (`Clockwise`,
      `SideOfFeature = Center`, bidireccional `PH = 5`)
    - `Pieza_072.pgmx -> pieza_072.iso` (`CounterClockwise`,
      `SideOfFeature = Center`, `Arc + Quote`, radio `2`)
    - `Pieza_073.pgmx -> pieza_073.iso` (`CounterClockwise`,
      `SideOfFeature = Center`, `Line + Quote`, radio `2`)
    - `Pieza_074.pgmx -> pieza_074.iso` (`CounterClockwise`,
      `SideOfFeature = Center`, `Line + Down/Up`, radio `2`)
    - `Pieza_075.pgmx -> pieza_075.iso` (`CounterClockwise`,
      `SideOfFeature = Center`, `Arc + Down/Up`, radio `2`)
    - `Pieza_051.pgmx -> pieza_051.iso` (`CounterClockwise`,
      `SideOfFeature = Right`, unidireccional `PH = 5`)
    - `Pieza_052.pgmx -> pieza_052.iso` (`CounterClockwise`,
      `SideOfFeature = Left`, unidireccional `PH = 5`)
    - `Pieza_053.pgmx -> pieza_053.iso` (`Clockwise`,
      `SideOfFeature = Right`, unidireccional `PH = 5`)
    - `Pieza_054.pgmx -> pieza_054.iso` (`Clockwise`,
      `SideOfFeature = Left`, unidireccional `PH = 5`)
    - `Pieza_055.pgmx -> pieza_055.iso` (`CounterClockwise`,
      `SideOfFeature = Right`, bidireccional `PH = 5`)
    - `Pieza_056.pgmx -> pieza_056.iso` (`CounterClockwise`,
      `SideOfFeature = Left`, bidireccional `PH = 5`)
    - `Pieza_057.pgmx -> pieza_057.iso` (`Clockwise`,
      `SideOfFeature = Right`, bidireccional `PH = 5`)
    - `Pieza_058.pgmx -> pieza_058.iso` (`Clockwise`,
      `SideOfFeature = Left`, bidireccional `PH = 5`)
    - en `Center`, el ISO arranca en el extremo derecho nominal del circulo:
      - `G0 X250.000 Y125.000`
    - no emite `G41/G42` para `Center`.
    - para `Left/Right` sin estrategia, conserva el radio nominal y delega la
      correccion:
      - `Left -> G41`
      - `Right -> G42`
    - emite el circulo como dos semicirculos nominales con centro `I/J`:
      - antihorario: dos lineas `G3`
      - horario: dos lineas `G2`
    - para `Left/Right` sin estrategia, agrega entrada/salida auxiliar de
      `1 mm` segun el sentido:
      - antihorario: entrada `Y124`, salida `Y126`
      - horario: entrada `Y126`, salida `Y124`
    - el PGMX cambia el radio efectivo segun lado y sentido:
      - `CounterClockwise + Left` y `Clockwise + Right` -> radio `48`
      - `CounterClockwise + Right` y `Clockwise + Left` -> radio `52`
    - en los circulos `Left/Right` sin estrategia, el ISO no emite esos radios
      compensados; usa siempre el radio nominal `50` y `SVR 2.000`.
    - en los circulos `Left/Right` con estrategia `PH = 5`, el ISO emite esos
      radios compensados:
      - radio `52`: arranque `X252`, otro extremo `X148`.
      - radio `48`: arranque `X248`, otro extremo `X152`.
      - el bloque E004 no usa `G41/G42`.
      - no aparecen las entradas/salidas auxiliares de `1 mm` en `Y`.
    - en pasante `Extra = 0.5`, tambien emite `Z-18.500` para espesor `18`.
    - con estrategia unidireccional `PH = 5`, repite una vuelta completa por
      nivel y mantiene el sentido:
      - `CounterClockwise -> G3` en todos los niveles.
      - `Clockwise -> G2` en todos los niveles.
    - con estrategia bidireccional `PH = 5`, alterna el sentido de cada vuelta:
      - arranque antihorario: `G3`, `G2`, `G3`, `G2`.
      - arranque horario: `G2`, `G3`, `G2`, `G3`.
    - los niveles emitidos son:
      - `Z-5.000`
      - `Z-10.000`
      - `Z-15.000`
      - `Z-18.500`
    - con entradas/salidas explicitas:
      - `Arc + Quote`: vertical a profundidad y arcos en cota.
      - `Line + Quote`: vertical a profundidad y lineas en cota.
      - `Line + Down/Up`: lineas con Z integrado.
      - `Arc + Down/Up`: arcos con Z integrado.
  - circulos helicoidales:
    - `Pieza_031.pgmx -> pieza_031.iso` (`CounterClockwise`, `PH = 0`)
    - `Pieza_032.pgmx -> pieza_032.iso` (`Clockwise`, `PH = 0`)
    - `Pieza_033.pgmx -> pieza_033.iso` (`CounterClockwise`, `PH = 5`)
    - `Pieza_034.pgmx -> pieza_034.iso` (`Clockwise`, `PH = 5`)
    - el ISO primero baja a `Z0.000` y luego reparte la bajada en arcos.
    - con `PH = 0`, la bajada helicoidal se resuelve en una vuelta completa:
      - dos semicirculos hasta `Z-18.500`
      - una vuelta final a profundidad constante
    - con `PH = 5`, la bajada se descompone en mas semicirculos:
      - `Z-2.500`, `Z-5.000`, `Z-7.500`, `Z-10.000`, `Z-12.500`,
        `Z-15.000`, `Z-16.750`, `Z-18.500`
      - una vuelta final a profundidad constante.
    - el sentido mantiene la regla `CounterClockwise -> G3` y
      `Clockwise -> G2`.
    - los offsets `J` de la rampa helicoidal no quedan exactamente en el
      centro nominal, sino levemente desplazados y espejados segun sentido.
- Escuadrados superiores con E001:
  - casos validados:
    - `Pieza_018.pgmx -> pieza_018.iso` (`CounterClockwise`, exterior
      `Right`, sin acercamiento/alejamiento)
    - `Pieza_019.pgmx -> pieza_019.iso` (`Clockwise`, exterior `Left`,
      sin acercamiento/alejamiento)
    - `Pieza_020.pgmx -> pieza_020.iso` (`CounterClockwise`, exterior
      `Right`, `Arco 2 en cota` explicito)
    - `Pieza_021.pgmx -> pieza_021.iso` (`Clockwise`, exterior `Left`,
      `Arco 2 en cota` explicito)
    - `Pieza_059.pgmx -> pieza_059.iso` (`CounterClockwise`,
      unidireccional `PH = 5`)
    - `Pieza_060.pgmx -> pieza_060.iso` (`Clockwise`,
      unidireccional `PH = 5`)
    - `Pieza_061.pgmx -> pieza_061.iso` (`CounterClockwise`,
      bidireccional `PH = 5`)
    - `Pieza_062.pgmx -> pieza_062.iso` (`Clockwise`,
      bidireccional `PH = 5`)
    - `Pieza_084.pgmx -> pieza_084.iso` (`CounterClockwise`,
      `Line + Quote`, radio `2`)
    - `Pieza_085.pgmx -> pieza_085.iso` (`CounterClockwise`,
      `Line + Down/Up`, radio `2`)
    - `Pieza_086.pgmx -> pieza_086.iso` (`CounterClockwise`,
      `Arc + Down/Up`, radio `2`)
  - herramienta:
    - PGMX `ToolKey = 1900 / E001`
    - ISO `T1`, `M06`, `?%ETK[6]=1`, `?%ETK[9]=1`, `S18000M3`
  - variables:
    - `SVL = 125.400`
    - `SVR = 9.180`, coincide con `tool_width / 2`
    - `?%ETK[7]=4`
    - `D1` activo durante el corte
  - profundidad:
    - pasante `Extra = 1` se emite como `G1 Z-19.000` para espesor `18`.
  - compensacion y sentido sin estrategia:
    - `Right -> G42`
    - `Left -> G41`
    - el ISO conserva el winding: antihorario y horario producen recorridos
      opuestos.
    - el ISO usa el rectangulo nominal con compensacion CNC; no emite los
      arcos de esquina del toolpath compensado PGMX como `G2/G3`.
    - explicitar `Acercamiento/Alejamiento = Arco, 2, en cota` no cambia el
      cuerpo ISO frente al default del builder publico.
    - deshabilitar `Acercamiento/Alejamiento` si cambia el ISO: elimina los
      arcos `G2/G3` de entrada/salida y usa movimientos lineales cortos de
      `1 mm` alrededor de `(200, 0)`.
    - con estrategia `PH = 5`, ya no usa `G41/G42`; emite geometria exterior
      compensada:
      - `X-9.180`
      - `X409.180`
      - `Y-9.180`
      - `Y259.180`
    - la unidireccional repite el mismo sentido en `Z-5.000`, `Z-10.000`,
      `Z-15.000` y `Z-19.000`.
    - la bidireccional alterna el sentido por nivel.
    - no hay retornos a altura segura entre niveles.
    - sin estrategia, las variantes de entrada/salida mantienen `G42`.
    - `Quote` baja/sube verticalmente y deja el lead en cota.
    - `Down/Up` integra el cambio de Z en el lead.

Reglas implementadas en codigo:
- `tools/synthesize_pgmx.py` conserva `ToolKey` vacio para
  `tool_resolution="Auto"` en `Front`, `Back`, `Left` y `Right`.
- `DrillingPatternSpec` puede sintetizar `ReplicateFeature` rectangular en
  `Top`, `Front`, `Back`, `Left` y `Right`.
- `tool_resolution="Explicit"` queda disponible para forzar una herramienta
  lateral solo cuando exista un caso que lo justifique.

Pendientes directos de ISO:
- continuar patrones de huecos:
  - ya quedo validado que `ReplicateFeature` rectangular `Top` no genera un
    ISO compacto; el postprocesador expande a seis taladros individuales.
  - queda validado que `ReplicateFeature` rectangular en `Front/Back/Left/Right`
    tambien se expande a taladros individuales.
  - falta investigar si otros patrones, separaciones, herramientas o alturas
    modifican ese comportamiento.
- ranuras/canales:
  - las variantes validas sobre `Top` con `Sierra Vertical X` quedaron
    cubiertas para `Center/Right/Left`, profundidad `5/10` y largo variable.
  - las variantes invalidas por orientacion o profundidad mayor a `10 mm` se
    descartan como fuente ISO porque Maestro advierte el error y no genera
    postprocesado.
  - queda solo como pendiente eventual cruzar ranuras con operaciones
    combinadas si aparece un caso de produccion que lo requiera.
- investigar fresados:
  - lineales con otras orientaciones o entradas/salidas
  - combinaciones de entrada/salida con estrategia `PH = 5` si hace falta
    confirmar si desaparece `G41/G42` tambien en esos cruces.
  - estrategias y entradas/salidas combinadas.
- validar variables aun abiertas:
  - altura lateral distinta de `Z=9`
  - retornos intermedios `G53 Z201` con otras combinaciones de operaciones
  - si `ETK[0]` lateral se mantiene igual con mas combinaciones.

Punto de reanudacion recomendado:
1. Si se quiere cerrar el cruce actual, repetir `Pieza_092` a `Pieza_095` con
   estrategia `PH = 5`.
2. Mantener pendiente la validacion fisica/simulada de como el CNC resuelve
   esquinas nominales con compensacion activa.

## Pausa de trabajo - 2026-04-30

- Estado al pausar:
  - ultima ronda documentada: `Ronda 44`, piezas `092` a `095`.
  - quedaron analizados los ISO de polilinea abierta E004 con `Left/Right` y
    entradas/salidas `Line + Down/Up` y `Arc + Down/Up`.
  - ranuras `SlotSide` superiores validas quedan cerradas como familia de
    estudio, salvo combinaciones reales futuras.
- Proximo paso recomendado:
  - sintetizar cuatro piezas nuevas equivalentes a `Pieza_092` a `Pieza_095`,
    pero agregando estrategia `PH = 5`.
  - objetivo de esa prueba: confirmar si `Left/Right + PH = 5 + Down/Up`
    elimina `G41/G42` y pasa a coordenadas compensadas, como ya ocurrio en
    otros fresados con estrategia.
- Pendientes secundarios:
  - fresados lineales en otras orientaciones si aparece una necesidad real.
  - patrones de huecos no rectangulares o con separaciones/herramientas
    distintas.
  - altura lateral distinta de `Z = 9`.
  - retornos `G53 Z201` en combinaciones de operaciones mas complejas.
  - validacion fisica/simulada de esquinas con compensacion activa.

## Pausa de trabajo - 2026-05-02

- Contexto:
  - no hay acceso inmediato a la computadora del CNC para postprocesar con
    Maestro.
  - el usuario indico que manana se instalara Codex/Nora en la compu de
    fabrica para generar los `.pgmx`; despues el usuario postprocesara esos
    `.pgmx` con Maestro y copiara los `.iso` resultantes para continuar.
- Hallazgos nuevos ya estabilizados:
  - los `.pgmx` de estudio estan en `S:\Maestro\Projects\ProdAction\ISO`.
  - los `.iso` accesibles estan en `P:\USBMIX\ProdAction\ISO`.
  - Maestro genera localmente en `C:\PrgMaestro\USBMIX`; esa carpeta es salida,
    no fuente de configuracion faltante.
  - configuracion adicional relevante esta en `S:\Xilog Plus`.
  - el contrato CNC observado quedo promovido a `docs/iso_cnc_contract.md`.
- Reanudacion recomendada:
  - leer `docs/iso_cnc_contract.md`.
  - leer `docs/iso_minimal_fixtures_plan.md`.
  - ejecutar:

```powershell
python -m tools.studies.iso.minimal_fixtures_2026_05_03 --output-dir "S:\Maestro\Projects\ProdAction\ISO\minimal_fixtures_2026-05-03"
```

  - postprocesar esos `.pgmx` con Maestro.
  - copiar los `.iso` desde `C:\PrgMaestro\USBMIX` a
    `P:\USBMIX\ProdAction\ISO\minimal_fixtures_2026-05-03`.
- Objetivo de la tanda:
  - cerrar la formula `HG/%Or/SHF[Y]` (cumplido luego al vincular `HG` con el
    campo `H` de `fields.cfg` y el redondeo `float32`).
  - confirmar que cambios de geometria, dimensiones y `origin_y` afectan o no
    afectan `%Or`, `SHF`, `MLV` y coordenadas ISO.
  - validar offsets laterales y bloque router E004 en piezas chicas.
- Pendiente secundario:
  - despues de la tanda minima, repetir piezas equivalentes a `Pieza_092` a
    `Pieza_095` agregando estrategia `PH = 5` para cerrar el cruce
    `Left/Right + Down/Up + PH = 5`.

## Tanda minima postprocesada - 2026-05-02

- Se generaron 14 fixtures `ISO_MIN_*` en
  `S:\Maestro\Projects\ProdAction\ISO\minimal_fixtures_2026-05-03`.
- El usuario los postproceso con Maestro y copio 14 `.iso` a
  `P:\USBMIX\ProdAction\ISO\minimal_fixtures_2026-05-03`.
- La comparacion quedo consolidada en `docs/iso_minimal_fixtures_plan.md` y las
  reglas estables se copiaron a `docs/iso_cnc_contract.md`.
- Hallazgos principales:
  - `DX/DY/DZ` de cabecera siguen `dimension + origin`.
  - mover geometria solo cambia movimientos `G0/G1`.
  - cambiar `width` no mueve `%Or[Y]` ni `SHF[Y]`.
  - cambiar `length` mueve `%Or[X]` y `SHF[X]`.
  - `origin_y` cambia el `SHF[Y]` operativo:
    `-1515.600 + origin_y`.
  - `%Or[0].ofY=-1515599.976` queda constante en toda la tanda.
  - laterales D8 confirman `ETK[8]`, `ETK[6]`, mascaras `ETK[0]` y offsets
    `SHF[MLV=2]` de los spindles `58..61`.
  - E004 confirma el bloque router chico: `T4`, `ETK[9]=4`, `SVL=107.200`,
    `SVR=2.000`.
  - `PH=5` sobre linea centrada confirma pasadas por niveles, pero no cierra
    la pregunta de compensacion porque no usa `SideOfFeature=Left/Right`.
- Proximo paso recomendado:
  - generar una segunda tanda chica para cerrar compensacion con E004:
    lineas equivalentes a `Pieza_092..Pieza_095`, pero con `PH=5`, manteniendo
    `Left/Right` y entradas/salidas `Line + Down/Up` y `Arc + Down/Up`.

## Segunda tanda PH5 generada - 2026-05-02

- Se generaron 4 `.pgmx` nuevos derivados de `Pieza_092..095`, agregando
  estrategia unidireccional:
  - `connection_mode = InPiece`;
  - `axial_cutting_depth = 5.0`;
  - `axial_finish_cutting_depth = 0.0`.
- Carpeta de salida:
  `S:\Maestro\Projects\ProdAction\ISO\ph5_compensation_2026-05-03`.
- Carpeta preparada para recibir ISO postprocesados:
  `P:\USBMIX\ProdAction\ISO\ph5_compensation_2026-05-03`.

| Fixture | Base | Variable mantenida | SHA256 PGMX |
| --- | --- | --- | --- |
| `ISO_PH5_092_Left_LineDownUp.pgmx` | `Pieza_092.pgmx` | `Left + Line Down/Up` | `8f68dc2f8a35095957098797d63c78da98c6c08fbad1709929b56530fb691a45` |
| `ISO_PH5_093_Right_LineDownUp.pgmx` | `Pieza_093.pgmx` | `Right + Line Down/Up` | `cae6c698ef0e9fd1e78d66ca501b13af6d99b4b3160a8d1a81b74822dc50d3ab` |
| `ISO_PH5_094_Left_ArcDownUp.pgmx` | `Pieza_094.pgmx` | `Left + Arc Down/Up` | `f8789309231bb5306d9f5a01e403e06e320044ab94c25c41ffbd4b89c8499916` |
| `ISO_PH5_095_Right_ArcDownUp.pgmx` | `Pieza_095.pgmx` | `Right + Arc Down/Up` | `c5f433495fdda32cb3be304ed137de8302d6731d1985665a4cade0fbfc1bb843` |

- Validacion local:
  - `manifest.csv` escrito.
  - hashes del manifest contra disco: OK.
  - adaptacion de los 4 `.pgmx`: `adapted=2`, `unsupported=0`,
    `ignored=1`.
- Pendiente inmediato:
  - postprocesar esos cuatro `.pgmx` con Maestro.
  - copiar los `.iso` resultantes a
    `P:\USBMIX\ProdAction\ISO\ph5_compensation_2026-05-03`.
  - comparar contra `pieza_092..pieza_095.iso` para confirmar si
    `Left/Right + PH=5 + Down/Up` elimina `G41/G42` o mantiene compensacion CNC.

## Segunda tanda PH5 parcialmente postprocesada - 2026-05-02

- El usuario postproceso con Maestro dos de los cuatro fixtures:
  - `iso_ph5_092_left_linedownup.iso`
  - `iso_ph5_093_right_linedownup.iso`
- Los dos fixtures `Arc + Down/Up` fallaron durante el postprocesado:
  - `ISO_PH5_094_Left_ArcDownUp.pgmx`
  - `ISO_PH5_095_Right_ArcDownUp.pgmx`
- Logs copiados por el usuario:
  - `P:\USBMIX\ProdAction\ISO\ph5_compensation_2026-05-03\Log\Log20260502_093307.logx`
  - `P:\USBMIX\ProdAction\ISO\ph5_compensation_2026-05-03\Log\Log20260502_095136.logx`
- Mensaje de error comun:
  - `Imposible ejecutar el post processor debido a un error de valoracion del ejecutable.`
  - `Error al crear un punto cartesiano.`
  - `El numero del valor utilizado no es valido.`
- Stack relevante:
  - `GeomCartesianPoint..ctor(Double x, Double y, Double z)`
  - `PostProcessor.LocalToGlobal(...)`
  - `PostProcessor.WritePointOnParameters(...)`
  - `PostProcessor.MoveOnCompositeCurve(...)`
  - `PostProcessor.EvaluateToolPath()`
- Validacion local de los cuatro `.pgmx`:
  - no contienen marcadores `NaN` / `Infinity`;
  - adaptan con `adapted=2`, `unsupported=0`, `ignored=1`;
  - la unica diferencia material entre los exitosos y los fallidos es
    `Approach/Retract = Arc + Down/Up`.
- Conclusion sobre el fallo:
  - el error no parece ser un `.pgmx` corrupto ni un valor invalido escrito por
    el sintetizador.
  - Maestro/postprocesador no logra valorar el toolpath cuando se combinan:
    polilinea abierta E004, `SideOfFeature=Left/Right`, estrategia
    unidireccional `PH=5`, y entrada/salida `Arc + Down/Up`.
  - como los equivalentes sin `PH=5` (`Pieza_094/095`) si postprocesan, y los
    equivalentes con `PH=5` pero `Line + Down/Up` tambien postprocesan, el
    cruce problematico queda acotado a `Arc + Down/Up + PH=5`.

Propiedades de los ISO exitosos:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | ---: | ---: | --- | --- |
| `iso_ph5_092_left_linedownup.iso` | `177` | `3357` | `3381D3703A8FE91A14C7350FAE2E52AD2ABC1E6AC21E0966F076C646E4101EDE` | `29A15B9DA6F14E9F22CF52DCBE94FEC5F56F8C815C3521959901A2FEB3CFC715` |
| `iso_ph5_093_right_linedownup.iso` | `177` | `3354` | `F762AACFCC902F714FEDE2B6A467EF0565B69312A4E77E77E478AF5667603804` | `79A66CD5C631EA763D078A851D9567DCC92C2B6DE4D4BD170049BA6728761CCA` |

- En ambos ISO hay un `G42`, pero pertenece al escuadrado E001 inicial.
- En el bloque E004, despues de `T4`, no aparece `G41/G42`.
- `Left + Line + Down/Up + PH=5` emite geometria compensada a la izquierda del
  perfil nominal. Primeros puntos E004:
  - `G0 X149.368 Y-4.427`
  - `G1 X148.103 Y-0.632 Z-5.000`
  - `G1 X98.103 Y149.368`
  - `G2 X100.485 Y151.940 I100.000 J150.000`
  - `G1 X296.951 Y102.824`
  - `G1 X248.103 Y249.368`
- `Right + Line + Down/Up + PH=5` emite geometria compensada a la derecha del
  perfil nominal. Primeros puntos E004:
  - `G0 X153.162 Y-3.162`
  - `G1 X151.897 Y0.632 Z-5.000`
  - `G1 X103.049 Y147.176`
  - `G1 X299.515 Y98.060`
  - `G3 X301.897 Y100.632 I300.000 J100.000`
  - `G1 X251.897 Y250.632`
- Esta tanda confirma la hipotesis para `Line + Down/Up`:
  `Left/Right + PH=5` elimina la compensacion CNC `G41/G42` del bloque E004 y
  pasa a coordenadas compensadas.

## Tanda diagnostica Arc PH5 generada - 2026-05-02

- Objetivo:
  - aislar por que `Left/Right + Arc + Down/Up + PH=5` falla en Maestro con
    `Error al crear un punto cartesiano`.
  - separar si el problema viene de `Approach Arc Down`, `Retract Arc Up`,
    `ArcSide=Automatic`, la compensacion `Left/Right`, o la polilinea abierta
    con quiebres.
- Carpeta de `.pgmx`:
  `S:\Maestro\Projects\ProdAction\ISO\arc_ph5_diagnostics_2026-05-03`.
- Carpeta preparada para recibir `.iso` y logs:
  `P:\USBMIX\ProdAction\ISO\arc_ph5_diagnostics_2026-05-03`.
- Todos los fixtures:
  - usan pieza `400 x 250 x 18`, origen `(5, 5, 25)`, area `HG`;
  - usan E004, `tool_width=4.0`, pasante con `Extra=0.5`;
  - usan estrategia unidireccional `PH=5`, `connection_mode=InPiece`;
  - no incluyen escuadrado E001, para aislar el bloque E004.
- Validacion local:
  - `manifest.csv` escrito.
  - hashes del manifest contra disco: OK.
  - adaptacion de los 10 `.pgmx`: `adapted=1`, `unsupported=0`,
    `ignored=1`.
  - no se encontraron marcadores `NaN` / `Infinity`.

| Fixture | Pregunta que responde | SHA256 PGMX |
| --- | --- | --- |
| `ISO_DIAG_001_Center_Polyline_ArcDownUp_PH5.pgmx` | si `Arc Down/Up + PH5` falla aun sin compensacion lateral | `2bd09b8e461e5a882acd0ed47a5165dd84d8a18c7bfac6630f57535abe36e10a` |
| `ISO_DIAG_002_Left_Polyline_ArcDownUp_PH5_NoSquare.pgmx` | si el fallo `Left` persiste sin escuadrado previo | `4f456e6486d63ed4040592ea4dc040c2e6a569f829c7c883e023b179d5f109c7` |
| `ISO_DIAG_003_Right_Polyline_ArcDownUp_PH5_NoSquare.pgmx` | si el fallo `Right` persiste sin escuadrado previo | `f0620d3b634ad92d7b017090d96724216d0835b23c005ef1011d00a55efbdba7` |
| `ISO_DIAG_004_Left_Polyline_ArcDown_LineUp_PH5.pgmx` | aislar `Approach Arc Down` con salida lineal | `8842e41d90ef0171fbb53ca0a6f3fe6bf3942d3acf349bb715c78593e3362490` |
| `ISO_DIAG_005_Left_Polyline_LineDown_ArcUp_PH5.pgmx` | aislar `Retract Arc Up` con entrada lineal | `ee3debeb6872d8150f9a87f95f7dc04555836bbe7d302805ae6f1d13881e06b1` |
| `ISO_DIAG_006_Left_Polyline_ArcDownUp_PH5_ArcSideLeft.pgmx` | probar si `ArcSide=Left` evita el fallo de `Automatic` | `26cbb71d4df2483709dafe563862410550f651f510d30274371ac5d72f4701f7` |
| `ISO_DIAG_007_Left_Polyline_ArcDownUp_PH5_ArcSideRight.pgmx` | probar si `ArcSide=Right` evita el fallo de `Automatic` | `19d2b36071bbd71574fb2b5a7a986155800ca2f6a741c9398774aeee64285d64` |
| `ISO_DIAG_008_Left_SimpleLine_ArcDownUp_PH5.pgmx` | si el problema tambien ocurre en linea simple `Left` | `92eb1cfee434b48d81a7ed13d6d56d953e7cbdd95c6f248123bf5aa4a1ff1231` |
| `ISO_DIAG_009_Right_SimpleLine_ArcDownUp_PH5.pgmx` | si el problema tambien ocurre en linea simple `Right` | `46710697c769edd909c31c9fe84a91ef27dadeda9d2fcd8f2629148a73dc494e` |
| `ISO_DIAG_010_Left_Polyline_ArcQuote_PH5.pgmx` | control con arcos pero sin Z integrada `Down/Up` | `89761c92cf9ae0d2b6f7f9adf6428aa91f45b127e0d6651b9e51039b60dd51e8` |

- Proximo paso:
  - postprocesar los 10 `.pgmx` con Maestro.
  - copiar los `.iso` que salgan y los logs de error a
    `P:\USBMIX\ProdAction\ISO\arc_ph5_diagnostics_2026-05-03`.
  - si hay fallos, conservar nombre de fixture o timestamp de intento para
    mapear cada log al archivo probado.

## Tanda diagnostica Arc PH5 postprocesada - 2026-05-02

- El usuario postproceso la tanda diagnostica
  `arc_ph5_diagnostics_2026-05-03`.
- Solo 4 de los 10 fixtures generaron ISO:
  - `iso_diag_004_left_polyline_arcdown_lineup_ph5.iso`
  - `iso_diag_008_left_simpleline_arcdownup_ph5.iso`
  - `iso_diag_009_right_simpleline_arcdownup_ph5.iso`
  - `iso_diag_010_left_polyline_arcquote_ph5.iso`
- Los ISO y logs quedaron en:
  `P:\USBMIX\ProdAction\ISO\arc_ph5_diagnostics_2026-05-03`.
- La carpeta `Log` contiene logs acumulados de esta tanda y de intentos
  anteriores. Los errores nuevos de esta tanda siguen el mismo stack:
  - `GeomCartesianPoint..ctor(Double x, Double y, Double z)`
  - `PostProcessor.LocalToGlobal(...)`
  - `PostProcessor.WritePointOnParameters(...)`
  - `PostProcessor.MoveOnCompositeCurve(...)`
  - `PostProcessor.EvaluateToolPath()`
  - mensaje final: `El numero del valor utilizado no es valido.`

Resultado por fixture:

| Fixture | Resultado | Lectura |
| --- | --- | --- |
| `ISO_DIAG_001_Center_Polyline_ArcDownUp_PH5` | falla | el fallo no depende de `Left/Right`; tambien ocurre en `Center` |
| `ISO_DIAG_002_Left_Polyline_ArcDownUp_PH5_NoSquare` | falla | el fallo no depende del escuadrado E001 previo |
| `ISO_DIAG_003_Right_Polyline_ArcDownUp_PH5_NoSquare` | falla | idem lado derecho |
| `ISO_DIAG_004_Left_Polyline_ArcDown_LineUp_PH5` | postprocesa | `Approach Arc + Down` no es el disparador por si solo |
| `ISO_DIAG_005_Left_Polyline_LineDown_ArcUp_PH5` | falla | `Retract Arc + Up` es suficiente para disparar el fallo en polilinea abierta |
| `ISO_DIAG_006_Left_Polyline_ArcDownUp_PH5_ArcSideLeft` | falla | fijar `ArcSide=Left` no evita el fallo |
| `ISO_DIAG_007_Left_Polyline_ArcDownUp_PH5_ArcSideRight` | falla | fijar `ArcSide=Right` no evita el fallo |
| `ISO_DIAG_008_Left_SimpleLine_ArcDownUp_PH5` | postprocesa | una linea simple si tolera `Arc Down/Up + PH5` |
| `ISO_DIAG_009_Right_SimpleLine_ArcDownUp_PH5` | postprocesa | idem lado derecho |
| `ISO_DIAG_010_Left_Polyline_ArcQuote_PH5` | postprocesa | arcos con `Quote` no fallan; el problema es el `Up` integrado en Z |

Propiedades de los ISO exitosos:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | ---: | ---: | --- | --- |
| `iso_diag_004_left_polyline_arcdown_lineup_ph5.iso` | `132` | `2629` | `C25EBB9450D4EDCC0D4DC38BBD13BCEA643E016A6927D992AAB96BDF0DB2B001` | `12011DF636D93163FAA916F22284AA0AC5A48E02CB47EF08252DBEE0D4993101` |
| `iso_diag_008_left_simpleline_arcdownup_ph5.iso` | `112` | `1834` | `F2E46150C620D21C2F4AABA485FCEC3C3E1FBC35651242FCEAEA535EF28C4D2F` | `44BD281A9C98A9BE92EA0BBC732109287FC3F9CD7C880FBCD9C737E50EA4E8E6` |
| `iso_diag_009_right_simpleline_arcdownup_ph5.iso` | `112` | `1839` | `8DAA62F5A4C0F297947C832AAB792B4A40E84AC0DCADA645BEB6A3744033EF0F` | `6B981422A8C70047A66CC0AA59582C187662372E36BB3B57BECFE6C937A3F7A9` |
| `iso_diag_010_left_polyline_arcquote_ph5.iso` | `133` | `2665` | `E73030E37C1B3A15960323AF9F6DA12CF35EC3DE126EA82C6C6563EB76A0F4AA` | `38C59FF2956CBA8B5C5F4EE9591BA9507DD38554B1134D3B4416C8F4C174BC2E` |

Conclusion:

- En polilinea abierta de varios segmentos con estrategia `PH=5`,
  `Retract Arc + Up` no es postprocesable por Maestro en los casos estudiados.
- El fallo no depende de:
  - `SideOfFeature=Left/Right`;
  - `ArcSide=Automatic`;
  - el escuadrado E001 previo;
  - el `Approach Arc + Down` por si solo.
- El fallo tampoco es una prohibicion general de arcos con `PH=5`:
  - linea simple `Arc Down/Up + PH5` postprocesa;
  - polilinea abierta `Arc Quote + PH5` postprocesa.
- Regla practica para futuras sintesis postprocesables:
  - evitar `Retract Arc + Up` en polilineas abiertas de varios segmentos cuando
    se use estrategia `PH=5`.
  - usar `Retract Line + Up` o `Arc + Quote` segun el caso.

## Barrido de parqueos laterales `Z149.*` - 2026-05-02

- Objetivo:
  - cerrar el hueco del contrato ISO sobre los movimientos `G0 G53 Z149.500` y
    `G0 G53 Z149.450`.
- Corpus revisado:
  - `P:\USBMIX\ProdAction\ISO`, busqueda recursiva de `.iso`.
  - `124` archivos `.iso` despues de sumar la tanda
    `router_toolset_2026-05-03`.
- Resultado del barrido:
  - solo `pieza_002.iso`, `pieza_003.iso` y `pieza_005.iso` contienen
    `G0 G53 Z149.*`.
  - las tres piezas son familias de taladros laterales D8 en varias caras.
  - los fixtures minimos de taladro lateral de una sola cara no contienen
    `Z149.*`.
- Cruce con PGMX/adaptador:
  - `Pieza_002.pgmx`: 4 taladros laterales individuales adaptados.
  - `Pieza_003.pgmx`: 8 taladros laterales individuales adaptados.
  - `Pieza_005.pgmx`: 4 patrones de taladro lateral adaptados.
  - en los tres casos el postprocesador resuelve brocas laterales reales
    `ETK[6]=58..61` desde cara/trayectoria, con `ToolKey` PGMX vacio.

Valores observados y corregidos tras la tanda
`side_g53_z_fixtures_2026-05-03`:

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

Comparacion puntual con la ventana de Xilog Plus:

| Mandril | Lado Xilog | `Offset Z` | `SHF_Z` usado | `DZ=43` -> `DZ+40+SHF_Z` |
| ---: | ---: | ---: | ---: | ---: |
| `58` | `4` | `-66.500` | `66.500` | `149.500` |
| `59` | `5` | `-66.500` | `66.500` | `149.500` |
| `60` | `2` | `-66.450` | `66.450` | `149.450` |
| `61` | `3` | `-66.300` | `66.300` | `149.300` |

Lectura:

- `Z149.*` aparece al cambiar de grupo/herramienta con una broca lateral
  involucrada. Si el `DZ` de cabecera cambia, el mismo patron aparece como
  `Z156.*` o `Z164.*`.
- El primer grupo lateral `Front / ETK[6]=58` no emite `Z149.*` si la pieza
  empieza directamente por esa cara.
- Entre taladros de una misma cara:
  - `Front/Back` pueden usar `G0 G53 Z201.000`.
  - `Left/Right` reposicionan en plano lateral de seguridad.
- Formula observada:
  - `G53_Z_lateral = DZ_cabecera + 2*SecurityDistance + max(SHF_Z lateral
    involucrado)`.
  - `SecurityDistance=20` en Maestro, por lo que hoy equivale a `+40.000`.
  - si se entra/sale desde herramienta vertical, se usa el `SHF_Z` de la broca
    lateral;
  - si se cambia lateral a lateral, se usa la mayor cota `SHF_Z` entre la cara
    activa y la cara destino.
- La hipotesis "usar solo mandril destino" falla en cambios como `59 -> 61`:
  con `DZ=43`, el destino `61` daria `149.300`, pero Maestro emite `149.500`
  porque el lateral anterior `59` tiene `SHF_Z=66.500`.
- `spindles.cfg` explica los `SHF[Z]` por offsets fisicos de spindle:
  - `58`: `Z=-66.50` -> `SHF[Z]=66.500`;
  - `59`: `Z=-66.50` -> `SHF[Z]=66.500`;
  - `61`: `Z=-66.30` -> `SHF[Z]=66.300`;
  - `60`: `Z=-66.45` -> `SHF[Z]=66.450`.
- `Programaciones.settingsx` de Maestro declara `SecurityDistance=20`; las 81
  piezas PGMX con laterales revisadas tienen `ApproachSecurityPlane=20` y
  `RetractSecurityPlane=20`. La hipotesis mas fuerte para `40.000` es entonces
  `20 + 20`, salida/reentrada a cota segura alrededor de la pieza.
- Estado del hueco:
  - regla ISO observada cerrada para el corpus actual.
  - queda pendiente validar causalmente cambiando `SecurityDistance` o las
    cotas de seguridad de operaciones laterales.

## Barrido de herramientas router pendientes - 2026-05-02

- Objetivo:
  - verificar si el corpus ISO existente ya permitia validar `E002`, `E005`,
    `E006` o `E007` sin generar otra tanda.
- Corpus revisado:
  - `P:\USBMIX\ProdAction\ISO`, busqueda recursiva de `.iso`.
- Resultado antes de la tanda `router_toolset_2026-05-03`:
  - valores `T` de router encontrados: `T1`, `T3`, `T4`.
  - valores `?%ETK[9]` encontrados: `1`, `3`, `4`.
  - no aparecen `T2`, `T5`, `T6`, `T7` ni `?%ETK[9]=2/5/6/7`.
- Aclaracion importante:
  - si aparecen `?%ETK[6]=2/5/6/7`, pero son brocas verticales
    `002/005/006/007`.
  - no deben confundirse con fresas de router `E002/E005/E006/E007`, que se
    expresan por `Tn` y `?%ETK[9]=n`.
- Estado del hueco:
  - en ese momento las herramientas router `E002`, `E005`, `E006` y `E007`
    seguian sin ISO en el corpus.
  - se genero una tanda nueva para `E005`, `E006` y `E007`.
  - `E002` quedo separada porque no pertenece a la misma familia de fresado
    lineal.

## Tanda router tools pendientes generada - 2026-05-02

- Objetivo:
  - generar PGMX minimos para obtener ISO de las fresas router pendientes.
- Carpeta de `.pgmx`:
  `S:\Maestro\Projects\ProdAction\ISO\router_toolset_2026-05-03`.
- Carpeta preparada para recibir `.iso`:
  `P:\USBMIX\ProdAction\ISO\router_toolset_2026-05-03`.
- Geometria comun:
  - pieza `500 x 300 x 18`;
  - origen `(5, 5, 25)`;
  - area `HG`;
  - una linea centrada en Top de `(140, 150)` a `(360, 150)`;
  - `SideOfFeature=Center`;
  - profundidad pasante con `extra_depth=1.0`;
  - `Approach Line + Down` y `Retract Line + Up`.
- `E002` no se genero:
  - el catalogo la clasifica como `Sierra Horizontal`.
  - `LineMillingSpec` la rechaza correctamente con validacion fuerte porque el
    fresado lineal publico requiere herramienta de tipo fresa, o Sierra Vertical
    X en ranurado horizontal no pasante.
  - para estudiar `E002` hace falta modelar la familia correcta de sierra
    horizontal antes de generar PGMX.

Fixtures generados:

| Fixture | ToolKey | Ancho | SHA256 PGMX |
| --- | --- | ---: | --- |
| `ISO_ROUTER_205_E005_LineCenter.pgmx` | `1904 / E005` | `76` | `497ed60f43384f4aedf52f8bb9841c6e82287efb9bcddf087cc1733994e185f8` |
| `ISO_ROUTER_206_E006_LineCenter.pgmx` | `1905 / E006` | `80` | `b9e34b00e88fc12fb1a2e66475a20a11e1d02cb87e3941828e09ce9cfece6400` |
| `ISO_ROUTER_207_E007_LineCenter.pgmx` | `1906 / E007` | `17.72` | `5372922d637c3c95753184374eb90ff670560e72b95bd40e0ac1ee52efd102a0` |

- Validacion local:
  - `manifest.csv` escrito.
  - hashes del manifest contra disco: OK.
  - adaptacion de cada `.pgmx`: `adapted=1`, `unsupported=0`, `ignored=1`,
    `line_millings=1`.
- Pendiente inmediato:
  - postprocesar los tres `.pgmx` con Maestro.
  - copiar los `.iso` resultantes a
    `P:\USBMIX\ProdAction\ISO\router_toolset_2026-05-03`.
  - comparar `T`, `?%ETK[9]`, `SVL`, `SVR`, feeds, `D1` y movimientos contra
    `E001/E003/E004`.

## Tanda router tools pendientes postprocesada - 2026-05-02

- El usuario postproceso los tres fixtures de
  `router_toolset_2026-05-03`.
- ISO recibidos:
  - `iso_router_205_e005_linecenter.iso`
  - `iso_router_206_e006_linecenter.iso`
  - `iso_router_207_e007_linecenter.iso`
- Carpeta:
  `P:\USBMIX\ProdAction\ISO\router_toolset_2026-05-03`.

Propiedades:

| ISO | Lineas | Bytes | SHA256 | Body SHA256 sin primera linea |
| --- | ---: | ---: | --- | --- |
| `iso_router_205_e005_linecenter.iso` | `98` | `1421` | `0E5CB36CA41C8DD2294D4537C4DA151386A429D35617BE2A384CF69B6E29E7E2` | `8ABE2D649813F68372CC053D04E191BC06CE463DB6711B95D474B0FF3B97D9F5` |
| `iso_router_206_e006_linecenter.iso` | `98` | `1421` | `B1F98AE5E419404B9424A7DE4C9F011FE554BAE41C2D8BE6B982E97FF27C0E04` | `B229E71464FED3637AC36293B486BDCD5F458BE7A14705E975E1AC0DD5B1C546` |
| `iso_router_207_e007_linecenter.iso` | `98` | `1420` | `E1830851F24B4347512129D8678B412B8AF49A63E9D5FAB6E0B83EE30C5C34E9` | `4408093B843F6A9B1E6221841B478B5C8316954EC52CB789D51BB26047208D2B` |

Mapeo router confirmado:

| ToolKey | ISO | `SVL` | `SVR` | Feeds observados |
| --- | --- | ---: | ---: | --- |
| `1904 / E005` | `T5`, `?%ETK[9]=5` | `145.900` | `38.000` | entrada `F2000`, corte/retracta `F5000` |
| `1905 / E006` | `T6`, `?%ETK[9]=6` | `120.870` | `40.000` | entrada/corte/retracta `F2000` |
| `1906 / E007` | `T7`, `?%ETK[9]=7` | `152.100` | `8.860` | entrada `F2000`, corte/retracta `F5000` |

Reglas confirmadas:

- Las tres herramientas usan `M06`, `?%ETK[6]=1`, `?%ETK[18]=1`,
  `S18000M3`, `?%ETK[13]=1`, `?%ETK[7]=4` y `D1`.
- `SVL/VL6` coincide con `ToolOffsetLength`.
- `SVR/VL7` coincide con `tool_width / 2`.
- La entrada en `Z` usa `SVL + security_plane`:
  - `E005`: `145.900 + 20 = 165.900`;
  - `E006`: `120.870 + 20 = 140.870`;
  - `E007`: `152.100 + 20 = 172.100`.
- La trayectoria de aproximacion/retracta lineal compensa una herramienta
  completa en X:
  - `E005`: `140 - 76 = 64`, `360 + 76 = 436`;
  - `E006`: `140 - 80 = 60`, `360 + 80 = 440`;
  - `E007`: `140 - 17.72 = 122.280`, `360 + 17.72 = 377.720`.
- La profundidad de corte emitida es `Z-19.000`, correspondiente a pieza de
  `18` mm con `extra_depth=1.0`.
- Al terminar, cada ISO apaga `SVL/SVR`, resetea `?%ETK[7]`, `?%ETK[13]` y
  `?%ETK[18]`, y retorna por `G0 G53 Z201.000` y `G0 G53 X-3700.000`.

Estado:

- `E005`, `E006` y `E007` pasan a herramientas router observadas a nivel ISO.
- Esa observacion de mapeo no equivale a autorizar cualquier uso automatico de
  cada herramienta.
- `E002` sigue requiriendo modelado especifico de Sierra Horizontal antes de
  generar un PGMX valido para Maestro.

## Aclaracion operativa sobre E002/E005/E006/E007 - 2026-05-02

- `E005`:
  - es una fresa de 45 grados.
  - debe tratarse con cuidado.
  - es preferible usarla manualmente desde Maestro, en fresados manuales o en
    division/escuadrado de piezas especiales.
  - puede usarse para dividir en juegos, pero solo aplicando la regla operativa
    ya definida sobre separacion entre piezas en juego y profundidad del
    fresado.
  - para generacion automatica de trazas PGMX, permitir solo division de
    `en_juego` aplicando esa regla ya establecida.
- `E006`:
  - es una fresa de 0 grados / rectificado.
  - no debe utilizarse en la forma del fixture lineal pasante
    `ISO_ROUTER_206_E006_LineCenter`; ese caso solo sirvio para reconocer el
    bloque ISO `T6` / `?%ETK[9]=6`.
  - su uso esperado es el tratamiento de extensiones superficiales sobre la cara
    superior de la pieza.
  - puede usarse en fresados o vaciados de poca profundidad por pasada.
  - bloquear generacion automatica de trazas PGMX hasta estudiar esos casos en
    Maestro/PGMX y establecer reglas seguras.
- `E007`:
  - es una fresa de 90 grados / recta.
  - funciona del mismo modo que `E001`.
  - tiene mayor largo util, por lo que aplica a piezas de mayor espesor.
  - queda como equivalente funcional de `E001` para casos donde se requiera ese
    largo util, respetando las mismas reglas de fresado/escuadrado.
- `E002`:
  - es una sierra horizontal y debe tratarse con cuidado.
  - no tiene filo para cortar la superficie de la cara superior.
  - su recorrido debe programarse de la misma manera que un fresado de cara
    superior.
  - bloquear generacion automatica de trazas PGMX hasta modelar la familia de
    Sierra Horizontal y establecer reglas seguras.

Separacion definida:

- Las restricciones anteriores aplican a generacion automatica de trazas nuevas
  en `.pgmx`.
- Si se implementa un traductor `.pgmx -> .iso` suficientemente general, puede
  confiar en el criterio del usuario de Maestro: si la herramienta y la
  trayectoria ya estan indicadas en un `.pgmx` existente, el traductor debe
  intentar generar el `.iso` postprocesado equivalente.
- En ese modo, `E002`, `E005` y `E006` pueden generar advertencias operativas,
  pero no deben bloquearse automaticamente solo por herramienta.

## Limpieza De Generadores De Estudio - 2026-05-02

El generador puntual de la tanda minima ISO se movio desde el nivel principal de
`tools/` a:

`tools/studies/iso/minimal_fixtures_2026_05_03.py`

Motivo:

- conservar la reproducibilidad de la tanda `minimal_fixtures_2026-05-03`;
- dejar claro que no es un flujo productivo ni un generador ISO general;
- mantener el nivel principal de `tools/` para herramientas publicas o
  operativas.

Comando vigente:

```powershell
python -m tools.studies.iso.minimal_fixtures_2026_05_03 --output-dir "S:\Maestro\Projects\ProdAction\ISO\minimal_fixtures_2026-05-03"
```

La definicion de los 14 fixtures minimos no se modifico.

## Cierre Parcial De HG / `%Or[Y]` - 2026-05-02

Al revisar la ventana de configuracion de Xilog Plus y las etiquetas internas
de `Parsifal.dll`, `fields.cfg` quedo identificado como la fuente legible de
los campos de trabajo. Para los programas `HG` estudiados:

- el campo `H` tiene `Origen Y = -1515.600`;
- el `SHF[Y]` base del marco `MLV=1` usa ese valor;
- `%Or[0].ofY=-1515599.976` se explica al guardar `-1515.600` como `float32`
  (`-1515.5999755859375`) y multiplicarlo por `1000`.

Esto elimina la hipotesis de una correccion oculta desde `yzone.cfg` para ese
valor puntual. Sigue pendiente validar la regla general para areas distintas a
`HG` si aparecen en piezas reales.

## Cocina: Escuadrado + Taladros - 2026-05-03

- Se habilito la secuencia observada `E001` escuadrado + taladros
  superiores/laterales.
- El caso cubierto exige una operacion de escuadrado inicial, al menos un
  taladro superior como primera operacion de taladrado y luego solo taladros o
  patrones de taladro.
- Hallazgos volcados al emisor:
  - los taladros superiores adaptados desde Cocina pueden traer herramienta
    `0`; el emisor resuelve mandril por familia/diametro igual que el
    sintetizador PGMX (`Flat 8/15/20/35/5/4`, `Conical 5`);
  - despues de un perfil superior, el primer taladro usa setup compacto: no se
    repiten `%Or` ni el marco primario, y se omite `?%ETK[6]=1` si el mandril
    ya queda en spindle `1`;
  - los taladros superiores posteriores al perfil se ordenan por vecino mas
    cercano con distancia Manhattan desde `(0,0)`; los taladros standalone
    conservan el orden PGMX para no romper la matriz raiz;
  - los laterales se ordenan por cara (`Front/Right` ascendente,
    `Back/Left` descendente);
  - las pausas `G4F0.500` laterales dependen de cara, profundidad y si el grupo
    lateral arranco inmediatamente despues de `Top`.
- Validacion:
  - Cocina completa:
    `tmp/cocina_iso_generated_20260504_complete` -> `84 ok`, `0 diff`,
    `0 error`.
  - Matriz raiz:
    `tmp/root_iso_generated_20260504_with_096_097` -> `103 ok`, `0 diff`,
    `0 missing_reference`.
  - `Pieza_096` y `Pieza_097` validan la polilinea abierta `E003` contra
    Maestro: 100 lineas normalizadas, 0 diferencias en ambas.
