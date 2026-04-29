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
- Proximo paso externo:
  - abrir `Pieza_004.pgmx` en la PC del CNC.
  - postprocesar y guardar el ISO como `pieza_004.iso`.
  - comparar si el postprocesador reconoce algun patron de repeticion o si
    emite seis taladros individuales con la broca `001`.

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

Reglas implementadas en codigo:
- `tools/synthesize_pgmx.py` conserva `ToolKey` vacio para
  `tool_resolution="Auto"` en `Front`, `Back`, `Left` y `Right`.
- `tool_resolution="Explicit"` queda disponible para forzar una herramienta
  lateral solo cuando exista un caso que lo justifique.

Pendientes directos de ISO:
- terminar `Pieza_004`:
  - postprocesar `pieza_004.iso`
  - confirmar si el postprocesador reconoce patrones de huecos o emite seis
    taladros individuales con la broca `001`.
- investigar patrones de huecos:
  - separaciones horizontales/verticales
  - agrupacion por herramienta
  - recorridos entre huecos
  - posibles optimizaciones o comandos compactos del postprocesador.
- investigar ranuras/canales:
  - ranuras validas sobre `Top`
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
1. Postprocesar `Pieza_004.pgmx` como `pieza_004.iso`.
2. Comparar contra la ronda 18.
3. Registrar si hay patron ISO compacto o seis bloques de taladro individuales.
4. Luego pasar a ranuras/canales.
