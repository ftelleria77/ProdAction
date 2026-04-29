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

## Cierre parcial de ingenieria inversa ISO

Estado al pausar la investigacion:
- queda documentado el flujo `PGMX sintetico -> postprocesado Maestro/CNC -> ISO`
  para piezas simples, taladros verticales y taladros laterales.
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
  - direccion:
    - PGMX `(50, 125) -> (350, 125)` se emitio como corte ISO `X350 -> X50`.
    - PGMX `(350, 125) -> (50, 125)` tambien se emitio como corte ISO
      `X350 -> X50`.
    - el orden de puntos no cambia el ISO en estos dos casos.
    - la direccion unica se explica por la herramienta: la sierra gira en un
      solo sentido y debe cortar en ese sentido para proteger la superficie de
      la placa.
    - queda pendiente confirmar si `side_of_feature`/compensacion modifica el
      lado mecanizado o los offsets.
  - compensacion:
    - `SideOfFeature = Center` mantiene la coordenada nominal de la ranura.
    - `SideOfFeature = Right/Left` desplaza la trayectoria `tool_width / 2`
      respecto del sentido geometrico de la linea PGMX.
    - con `tool_width = 3.8`, el ISO desplaza `1.9 mm` en `Y`.
    - este desplazamiento aparece en la linea `G0 X350.000 Y...`; el corte
      lineal posterior conserva ese `Y` modal.
    - `SideOfFeature` no cambia `SHF`, `ETK`, `SVL`, `SVR`, `D1`, profundidad
      ni sentido fisico de corte.
- Fresados superiores con E004:
  - primer caso validado:
    `Pieza_015.pgmx -> pieza_015.iso`.
  - herramienta:
    - PGMX `ToolKey = 1903 / E004`
    - ISO `T4`, `M06`, `?%ETK[9]=4`, `S18000M3`
  - variables:
    - `SVL = 107.200`, coincide con `tool_offset_length` de E004
    - `SVR = 2.000`, coincide con `tool_width / 2`
    - `?%ETK[7]=4` durante el avance de fresado
    - `D1` activo durante el corte
  - avances:
    - bajada `F2000`
    - fresado lineal `F5000`
  - profundidad:
    - `target_depth = 15` se emite como `G1 Z-15.000`.
    - aunque el toolpath PGMX queda a `Z = 3` por espesor `18`, el ISO usa
      profundidad negativa absoluta.
  - geometria:
    - PGMX `(200, 50) -> (200, 200)`
    - ISO aproxima en `G0 X200.000 Y50.000`
    - ISO corta `G1 Y200.000 Z-15.000`
  - polilineas abiertas:
    - `Pieza_016.pgmx -> pieza_016.iso` (`SideOfFeature = Left`)
    - `Pieza_017.pgmx -> pieza_017.iso` (`SideOfFeature = Right`)
    - el ISO conserva la geometria nominal de la polilinea y cambia solo la
      compensacion:
      - `Left -> G41`
      - `Right -> G42`
    - `SVR = 2.000` queda como radio de herramienta para la compensacion.
    - no se emite el arco exterior del `TrajectoryPath` PGMX de `Left` como
      `G2/G3`; la resolucion de la esquina queda en el control CNC.
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
  - compensacion y sentido:
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
- investigar ranuras/canales:
  - variantes de ranuras validas sobre `Top`
  - ranuras invalidas por herramienta/recorrido
  - relacion entre geometria PGMX, herramienta y salida ISO.
- investigar fresados:
  - lineales
  - circulares
  - polilineas abiertas/cerradas
  - escuadrados
  - estrategias y entradas/salidas.
- validar variables aun abiertas:
  - altura lateral distinta de `Z=9`
  - retornos intermedios `G53 Z201`
  - si `ETK[0]` lateral se mantiene igual con mas combinaciones.

Punto de reanudacion recomendado:
1. Variar estrategia o pasar a polilinea cerrada E001/E004 para comparar contra
   el escuadrado.
2. Postprocesar y revisar si la estructura ISO sigue usando rectangulo nominal
   con `G41/G42` o si cambia por estrategia/geometria.
3. Mantener pendiente la validacion fisica/simulada de como el CNC resuelve
   esquinas nominales con compensacion activa.
