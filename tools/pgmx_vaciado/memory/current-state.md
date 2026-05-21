# PGMX Vaciado

Ultima actualizacion: 2026-05-16

## Objetivo

Abrir una investigacion separada para mecanizados `.pgmx` que todavia no estan
soportados por las herramientas actuales y que vamos a estudiar bajo el concepto
operativo de `Vaciado`.

`Vaciado` nombra, por ahora, un mecanizado de remocion de material en un area
interior. No se asume todavia que exista un unico tipo XML Maestro con ese
nombre. La clasificacion debe salir de evidencia: feature, operacion,
geometria, profundidad, estrategia, toolpath y salida ISO cuando exista.

## Carpeta Externa De Evidencia

Raiz de trabajo:

```text
S:\Maestro\Projects\ProdAction\PGMX
```

Subcarpetas:

- `manual/`: ejemplos hechos en Maestro o ajustados a mano.
- `generated/`: ejemplos sinteticos creados por herramientas tentativas.
- `_analysis/`: reportes generados por los inspectores del laboratorio.

Los `.pgmx` de esta carpeta son corpus de investigacion, no fixtures estables
del repo. La memoria del repo debe registrar que se genero, que se observo y que
decision se tomo.

## Separacion De Responsabilidades

- Este laboratorio puede tener codigo incompleto o especulativo.
- Vive bajo `tools/pgmx_vaciado/` para quedar junto al nucleo PGMX del repo,
  pero los modulos productivos no deben importarlo como dependencia estable.
- Una regla solo se migra a `tools/pgmx_snapshot.py`,
  `tools/pgmx_adapters.py`, `tools/synthesize_pgmx.py`,
  `core/pgmx_processing.py` o `iso_state_synthesis/` cuando tenga evidencia
  suficiente.
- La sintesis automatica de `.pgmx` y la traduccion de un `.pgmx` existente a
  ISO siguen siendo problemas separados.

## Datos Minimos A Capturar

Para cada ejemplo de `Vaciado` se debe registrar:

- ruta del `.pgmx`;
- si fue manual o generado;
- tipo XML de `ManufacturingFeature`;
- tipo XML de `Operation`;
- geometria referenciada;
- plano/cara;
- profundidad inicial/final y profundidad de operacion;
- herramienta y tecnologia embebida;
- toolpaths presentes y curvas asociadas;
- estrategia de fresado;
- acercamiento y alejamiento;
- si Maestro puede postprocesarlo a ISO;
- diferencia frente a mecanizados existentes como linea, perfil, ranura o
  escuadrado.

## Hipotesis Iniciales

- `Vaciado` puede aparecer como una variante de fresado de area, no
  necesariamente como un nombre literal.
- El criterio importante puede ser la combinacion `geometria cerrada +
  estrategia + toolpath interior`, no solo el tipo de feature.
- Los no soportados observados en Haeublein con `Fresado...` y
  `Perfilado(1)(1)` pueden aportar ejemplos, pero no deben mezclarse
  automaticamente con `Vaciado` sin evidencia.
- La primera tarea es leer y dibujar correctamente el `.pgmx`; la emision ISO
  viene despues.

## Primeras Herramientas

- `tools.pgmx_vaciado.scan_samples`: cataloga `.pgmx` de la carpeta externa y
  genera un CSV/Markdown con los tipos y atributos relevantes.

## Evidencia Inicial

### `Vaciado_000.pgmx`

Archivo base generado en `S:\Maestro\Projects\ProdAction\PGMX`.

- Pieza `400 x 300 x 40`.
- Origen `(5, 5, 25)`.
- Sin mecanizados.
- Sin `Xn`.

### `manual/Vaciado_001.pgmx`

Primer ejemplo manual de vaciado.

- Nombre interno de pieza corregido a `Vaciado`.
- Feature: `a:ClosedPocket`, nombre `Vaciado`.
- Operacion: `a:BottomAndSideRoughMilling`.
- Plano: `Top`.
- Herramienta: `E001`, `tool_id=1900`, diametro embebido `18.36`.
- Profundidad del feature: `10`.
- Fondo: `a:PlanarPocketBottomCondition`.
- Geometria nominal: rectangulo cerrado `400 x 300`, puntos
  `(0,0) -> (400,0) -> (400,300) -> (0,300) -> (0,0)`.
- Toolpaths materializados: `Approach`, `TrajectoryPath`, `Lift`.
- `TrajectoryPath`: `95` puntos, `Z=30`, rango de centro de herramienta
  `X 9.18..390.82`, `Y 9.18..290.82`.
- Estrategia XML: `b:ContourParallel`.

Campos observados en `ContourParallel`:

- `InsideToOutSide=true`.
- `IsInternal=true`.
- `Cutmode=Climb`.
- `RotationDirection=CounterClockwise`.
- `RadialCuttingDepth=9.18`.
- `Overlap=0.5`.
- `StrokeConnectionStrategy=LiftShiftPlunge`.

### `manual/Vaciado_002.pgmx`

Segundo ejemplo manual.

- Misma pieza `400 x 300 x 40`, origen `(5, 5, 25)`, area `HG`.
- Feature y operacion iguales a `Vaciado_001`: `ClosedPocket` +
  `BottomAndSideRoughMilling`.
- Profundidad del feature: `5`.
- Geometria nominal equivalente al rectangulo completo, pero la secuencia
  arranca en `(200,0)` y cierra volviendo a `(200,0)`.
- `Approach`: `X=200`, `Y=146.88`, `Z 60 -> 35`.
- `TrajectoryPath`: `96` puntos, `Z=35`, rango de centro de herramienta
  `X 9.18..390.82`, `Y 9.18..290.82`.
- Estrategia XML igual a `Vaciado_001`: `b:ContourParallel` con
  `RadialCuttingDepth=9.18`, `Overlap=0.5`, `InsideToOutSide=true`.

Lectura preliminar: el punto inicial de la geometria nominal influye en el
punto de entrada y agrega un punto a la trayectoria, pero no cambia la
estrategia ni el rango efectivo del vaciado.

### `manual/Vaciado_003.pgmx`

Tercer ejemplo manual.

- Misma pieza `400 x 300 x 40`, origen `(5, 5, 25)`, area `HG`.
- Feature y operacion iguales a los anteriores: `ClosedPocket` +
  `BottomAndSideRoughMilling`.
- Profundidad del feature: `3`.
- Geometria nominal: rectangulo completo, arrancando en `(0,300)` y recorriendo
  `(400,300) -> (400,0) -> (0,0) -> (0,300)`.
- `Approach`: `X=146.88`, `Y=153.12`, `Z 60 -> 37`.
- `TrajectoryPath`: `95` puntos, `Z=37`, rango de centro de herramienta
  `X 9.18..390.82`, `Y 9.18..290.82`.
- `Lift`: `X=9.18`, `Y=153.12`, `Z 37 -> 60`.
- Estrategia XML igual a `Vaciado_001` y `Vaciado_002`: `b:ContourParallel`
  con `RadialCuttingDepth=9.18`, `Overlap=0.5`, `InsideToOutSide=true`,
  `RotationDirection=CounterClockwise`.

Lectura preliminar: invertir/rotar el arranque del contorno nominal cambia el
punto de entrada, el punto de salida y el orden de los tramos internos, pero
mantiene la misma estrategia, herramienta, offsets efectivos y cantidad general
de pasadas.

### `manual/Vaciado_004.pgmx` A `manual/Vaciado_009.pgmx`

Tanda manual para aislar el efecto de la herramienta sobre el mismo vaciado.

Constantes de la tanda:

- Pieza `400 x 300 x 40`, origen `(5, 5, 25)`, area `HG`.
- Feature: `a:ClosedPocket`.
- Operacion: `a:BottomAndSideRoughMilling`.
- Geometria nominal: rectangulo cerrado `400 x 300`, arrancando en `(0,0)`.
- Profundidad del feature: `10`.
- Estrategia XML: `b:ContourParallel`.
- Campos constantes de estrategia: `Overlap=0.5`, `InsideToOutSide=true`,
  `IsInternal=true`, `Cutmode=Climb`,
  `RotationDirection=CounterClockwise`,
  `StrokeConnectionStrategy=LiftShiftPlunge`.
- Sin boss geometry: `BossGeometryList` y `BossList` vacios.

| archivo | herramienta | diametro | radio | RadialCuttingDepth | puntos trayectoria | rango X/Y efectivo |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `Vaciado_004.pgmx` | `E002` | `100` | `50` | `50` | `15` | `X 50..350`, `Y 50..250` |
| `Vaciado_005.pgmx` | `E003` | `9.52` | `4.76` | `4.76` | `185` | `X 4.76..395.24`, `Y 4.76..295.24` |
| `Vaciado_006.pgmx` | `E004` | `4` | `2` | `2` | `447` | `X 2..398`, `Y 2..298` |
| `Vaciado_007.pgmx` | `E005` | `76` | `38` | `38` | `17` | `X 38..362`, `Y 38..262` |
| `Vaciado_008.pgmx` | `E006` | `80` | `40` | `40` | `17` | `X 40..360`, `Y 40..260` |
| `Vaciado_009.pgmx` | `E007` | `17.72` | `8.86` | `8.86` | `95` | `X 8.86..391.14`, `Y 8.86..291.14` |

Lectura preliminar: en esta tanda, `RadialCuttingDepth` coincide exactamente
con el radio de la herramienta embebida. El rango efectivo del centro de
herramienta tambien queda desplazado hacia adentro por ese mismo radio. La
cantidad de puntos crece cuando baja el radio/paso radial.

### `manual/Vaciado_010.pgmx` A `manual/Vaciado_017.pgmx`

Tanda manual basada en `Vaciado_008.pgmx` para aislar parametros de la
estrategia `Paralela al perfil/contorno` y un parametro operativo adicional.

Constantes de la tanda:

- Pieza `400 x 300 x 40`, origen `(5, 5, 25)`, area `HG`.
- Feature: `a:ClosedPocket`.
- Operacion: `a:BottomAndSideRoughMilling`.
- Herramienta: `E006`, diametro `80`, radio `40`.
- Estrategia XML: `b:ContourParallel`.
- `RadialCuttingDepth=40`, coincidente con el radio de herramienta.
- `Overlap=0.5`.

Cambios aislados contra `Vaciado_008.pgmx`:

| archivo | parametro Maestro | cambio XML observado |
| --- | --- | --- |
| `Vaciado_010.pgmx` | Direccion del recorrido = Horario | `RotationDirection: CounterClockwise -> Clockwise` |
| `Vaciado_011.pgmx` | Conexion entre huecos = En la pieza | `StrokeConnectionStrategy: LiftShiftPlunge -> Straghtline` |
| `Vaciado_012.pgmx` | Direccion de vaciado = Desde afuera hacia adentro | `InsideToOutSide: true -> false` |
| `Vaciado_013.pgmx` | Habilitar helicoidal = true | `IsHelicStrategy: false -> true` |
| `Vaciado_014.pgmx` | Habilitar multipaso = true | `AllowMultiplePasses: false -> true`, `AxialCuttingDepth=5`, `AxialFinishCuttingDepth=10` |
| `Vaciado_015.pgmx` | Rebaba / despeje al contorno | `AllowanceSide: 0 -> 20` |
| `Vaciado_016.pgmx` | Rebaba / despeje al contorno negativo | `AllowanceSide: 0 -> -20` |
| `Vaciado_017.pgmx` | Sobreposicion % = 25 | `Overlap: 0.5 -> 0.25` |

Lectura preliminar: `Rebaba` no pertenece a `MachiningStrategy`; Maestro lo
guarda como `AllowanceSide` en la operacion. Debe tratarse como parametro de
`BottomAndSideRoughMilling`, no como parte de `ContourParallel`. El valor puede
ser positivo o negativo.

Observacion de trayectoria materializada:

- `Vaciado_010`, `011`, `013` y `014` conservan `17` puntos y rango efectivo
  `X 40..360`, `Y 40..260`, `Z=30`.
- `Vaciado_012` conserva el mismo rango efectivo, pero sube a `19` puntos al
  cambiar la direccion de vaciado.
- `Vaciado_015` conserva `17` puntos, pero el rango efectivo pasa a
  `X 60..340`, `Y 60..240`: radio herramienta `40` + `AllowanceSide=20`.
- `Vaciado_016` sube a `23` puntos y el rango efectivo pasa a `X 20..380`,
  `Y 20..280`: radio herramienta `40` + `AllowanceSide=-20`.
- `Vaciado_017` mantiene `17` puntos y rango `X 40..360`, `Y 40..260`, pero
  cambia `Overlap` de `0.5` a `0.25` (`25%` en UI/reporte).

## Soporte En Codigo

Avance 2026-05-16:

- `tools.synthesize_pgmx` ya expone `PocketMillingSpec` y
  `build_pocket_milling_spec(...)` como spec publica de lectura/adaptacion para
  `Vaciado`.
- La spec representa `ClosedPocket + BottomAndSideRoughMilling +
  ContourParallel`, con contorno, herramienta, profundidad, approach/retract,
  estrategia, `AllowanceBottom`, `AllowanceSide`, `effective_contour_offset` y
  `radial_step`.
- `tools.pgmx_adapters` ya adapta `ClosedPocket` en plano `Top` con operacion
  `BottomAndSideRoughMilling` y estrategia `ContourParallel` hacia
  `PocketMillingSpec`.
- Validacion real: `manual/Vaciado_001.pgmx` a `manual/Vaciado_019.pgmx`
  entran como `pocket_milling` con `1` entrada adaptada y `0` unsupported cada
  uno.
- `tools.pgmx_vaciado.scan_samples` corrio contra
  `S:\Maestro\Projects\ProdAction\PGMX` y genero el catalogo vigente en
  `_analysis`.
- Se genero una muestra de adaptacion en
  `S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_018_adaptation.json`.
- La serializacion productiva sigue bloqueada explicitamente:
  `synthesize_request(...)` con `PocketMillingSpec` levanta
  `NotImplementedError`. Esto es intencional hasta cerrar la generacion de
  geometria, operacion, estrategia y toolpaths.
- Se agrego `tools.pgmx_vaciado.contour_parallel` como generador experimental
  puro de trayectoria rectangular `ContourParallel` y comparador contra corpus.
  Resultado inicial cerrado: `manual/Vaciado_001.pgmx` a
  `manual/Vaciado_017.pgmx` comparan `17/17` exactos en secuencia XY contra
  Maestro. El reporte vigente queda en
  `S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_contour_parallel_comparison.md`
  y el CSV en
  `S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_contour_parallel_comparison.csv`.
- Avance 2026-05-17: el mismo generador ahora materializa trayectoria
  `X/Y/Z` multipaso. `manual/Vaciado_001.pgmx` a `manual/Vaciado_019.pgmx`
  comparan `19/19` exactos contra Maestro. Quedaron cubiertos
  `Vaciado_018` (`LiftShiftPlunge`, subidas a `Z=60`) y `Vaciado_019`
  (`Straghtline`, conexiones internas sin subir a seguridad).

## Huecos Del Lector Actual

- `tools.pgmx_snapshot.py` ya representa `b:ContourParallel` como
  `ContourParallelMillingStrategySpec`.
- `ClosedPocket` ya se representa a nivel semantico mediante
  `PocketMillingSpec`, pero la serializacion productiva de
  `BottomAndSideRoughMilling` y sus toolpaths todavia no esta implementada.
- Ya hay ejemplos manuales para confirmar los valores XML de `En la pieza`,
  `Desde afuera hacia adentro`, helicoidal y multipaso.
- Falta incorporar la generacion automatica estable de `Vaciado`: feature,
  operacion, estrategia, toolpaths y curvas internas.

## Mapeo UI / XML De `Paralela Al Perfil`

`Paralela al perfil` y `Paralela al contorno` se tratan como el mismo concepto
de Maestro: `MachiningStrategy i:type="b:ContourParallel"`.

| UI Maestro | XML | Lectura estable |
| --- | --- | --- |
| Direccion del recorrido | `RotationDirection` | `Clockwise` / `CounterClockwise` |
| Conexion entre huecos | `StrokeConnectionStrategy` | `LiftShiftPlunge` = salida a cota de seguridad, `Straghtline` = en la pieza |
| Direccion de vaciado | `InsideToOutSide` | `true` = dentro hacia afuera, `false` = afuera hacia adentro |
| Sobreposicion % | `Overlap` | valor XML decimal: `0.5` = `50%`, `0.25` = `25%` |
| Habilitar helicoidal | `IsHelicStrategy` | `false` / `true` |
| Habilitar multipaso | `AllowMultiplePasses` | `false` / `true` |
| Profundidad de hueco | `AxialCuttingDepth` | `0` observado; con multipaso ejemplo `5` |
| Ultimo hueco | `AxialFinishCuttingDepth` | `0` observado; con multipaso ejemplo `10` |

Campos auxiliares preservados: `Cutmode`, `IsInternal`,
`RadialCuttingDepth`, `RadialFinishCuttingDepth`, `AllowsBidirectional` y
`AllowsFinishCutting`.

Parametro operativo relacionado:

| UI Maestro | XML | Lectura estable |
| --- | --- | --- |
| Rebaba / distancia de despeje al contorno | `AllowanceSide` | valor de operacion; ejemplos `20` y `-20` |

### `manual/Vaciado_018.pgmx`

Ejemplo manual similar a `Vaciado_014.pgmx`, pero con mayor profundidad de
vaciado.

Datos observados:

- Feature: `a:ClosedPocket`.
- Operacion: `a:BottomAndSideRoughMilling`.
- Profundidad del feature: `25`.
- Estrategia XML igual a `Vaciado_014`: `b:ContourParallel`.
- `AllowMultiplePasses=true`.
- `AxialCuttingDepth=5`.
- `AxialFinishCuttingDepth=10`.
- `RadialCuttingDepth=40`.
- `Overlap=0.5`.
- `AllowanceSide=0`.

Diferencia central contra `Vaciado_014`:

- `Vaciado_014` tiene un solo recorrido de corte en `Z=30`.
- `Vaciado_018` materializa varias cotas dentro del mismo `TrajectoryPath`:
  `Z=35`, `Z=30`, `Z=25`, `Z=15`, con traslados intermedios por `Z=60`.
- El `TrajectoryPath` de `Vaciado_018` tiene `74` puntos.
- Los rangos XY de corte se mantienen en `X 40..360`, `Y 40..260`.

Secuencia observada en `TrajectoryPath`:

| tramo | Z | puntos | rango XY |
| --- | ---: | ---: | --- |
| pase 1 | `35` | `17` | `X 40..360`, `Y 40..260` |
| transicion | `60` | `2` | `X=120`, `Y 40..120` |
| pase 2 | `30` | `17` | `X 40..360`, `Y 40..260` |
| transicion | `60` | `2` | `X=120`, `Y 40..120` |
| pase 3 | `25` | `17` | `X 40..360`, `Y 40..260` |
| transicion | `60` | `2` | `X=120`, `Y 40..120` |
| pase final | `15` | `17` | `X 40..360`, `Y 40..260` |

Lectura preliminar: `AllowMultiplePasses` no genera necesariamente multiples
`ToolpathList`; Maestro puede materializar los pases de profundidad dentro de
un unico `TrajectoryPath`, intercalando salidas a cota de seguridad. Para
sintetizar vaciado multipaso habra que modelar la secuencia Z ademas de la
traza XY de anillos.

### `manual/Vaciado_019.pgmx`

Ejemplo manual similar a `Vaciado_018.pgmx`, pero con `Conexion entre huecos =
En la pieza`.

Diferencia XML contra `Vaciado_018`:

- `StrokeConnectionStrategy: LiftShiftPlunge -> Straghtline`.
- El resto de los escalares de feature, operacion y estrategia se mantienen.

Diferencia de traza:

- `Vaciado_018` usa `LiftShiftPlunge`: entre niveles sube a `Z=60`, se mueve
  en XY y baja al siguiente nivel.
- `Vaciado_019` usa `Straghtline`: entre niveles vuelve en XY hasta el punto de
  inicio del anillo interior y baja verticalmente dentro de la pieza, sin pasar
  por `Z=60`.
- `Vaciado_018` tiene `74` puntos en `TrajectoryPath` y cotas
  `15,25,30,35,60`.
- `Vaciado_019` tiene `71` puntos en `TrajectoryPath` y cotas
  `15,25,30,35`.
- Ambos conservan la misma longitud XY aproximada (`9680`) y el mismo rango de
  corte `X 40..360`, `Y 40..260`.

Secuencia observada en `Vaciado_019`:

| tramo | Z | puntos | rango XY |
| --- | ---: | ---: | --- |
| pase 1 + retorno | `35` | `18` | `X 40..360`, `Y 40..260` |
| pase 2 + retorno | `30` | `18` | `X 40..360`, `Y 40..260` |
| pase 3 + retorno | `25` | `18` | `X 40..360`, `Y 40..260` |
| pase final | `15` | `17` | `X 40..360`, `Y 40..260` |

Lectura preliminar: `StrokeConnectionStrategy` puede no modificar la traza en
un vaciado de un solo nivel, como `Vaciado_011`, pero si modifica claramente
las transiciones internas de un vaciado multipaso.

## Avance Del Scanner Tentativo

- `tools.pgmx_vaciado.scan_samples` usa la estrategia estable del snapshot y
  conserva fallback crudo para estrategias futuras no modeladas.
- El CSV registra herramienta, diametro, radio, `ContourParallel`, cantidad de
  puntos de trayectoria, rangos efectivos `X/Y/Z`, allowances y la
  sobreposicion en porcentaje.

## Punto De Reanudacion

Linea de trabajo abierta: modelar `Vaciado` como mecanizado estable a partir
de ejemplos Maestro `ClosedPocket + BottomAndSideRoughMilling +
ContourParallel`.

Estado actual:

- El lector estable ya representa `b:ContourParallel` como
  `ContourParallelMillingStrategySpec`.
- El adaptador estable ya representa `Vaciado/ClosedPocket` como
  `PocketMillingSpec`.
- La sintesis productiva ya emite el subset rectangular `PocketMillingSpec`
  sobre `Top`: feature `ClosedPocket`, operacion
  `BottomAndSideRoughMilling`, estrategia `ContourParallel`,
  `AllowanceSide/Bottom`, toolpaths y curvas internas.
- El corpus manual observado llega hasta `manual/Vaciado_019.pgmx`.
- El catalogo externo vigente esta en
  `S:\Maestro\Projects\ProdAction\PGMX\_analysis`.
- La carpeta `tools/pgmx_vaciado/` conserva la memoria y el scanner del
  laboratorio.
- La trayectoria rectangular `ContourParallel` ya esta modelada en
  `tools.pgmx_vaciado.contour_parallel` y reproduce `17/17` ejemplos manuales
  (`Vaciado_001..017`) en XY y `19/19` (`Vaciado_001..019`) en `X/Y/Z`
  contra Maestro.
- Se genero la tanda `generated/Vaciado_001_synth.pgmx` ..
  `generated/Vaciado_019_synth.pgmx`; los 19 archivos se readaptan como un
  unico `pocket_milling`, sin unsupported, y sus trayectorias `X/Y/Z` son
  exactas contra el generador validado.

Hipotesis de traza vigente:

- La trayectoria base son anillos rectangulares concentricos.
- Offset efectivo al contorno: `radio_herramienta + AllowanceSide`.
- Paso entre anillos: `diametro_herramienta * (1 - Overlap)`.
- `RotationDirection` invierte el sentido de cada anillo.
- `InsideToOutSide` cambia el orden de anillos.
- `StrokeConnectionStrategy` puede no modificar un vaciado de un solo nivel,
  pero en multipaso define si las transiciones internas suben a seguridad
  (`LiftShiftPlunge`) o bajan dentro de la pieza (`Straghtline`).
- En multipaso, Maestro puede materializar todas las capas dentro de un unico
  `TrajectoryPath`, con o sin cotas de seguridad intermedias.

Siguiente paso recomendado:

1. Diseniar la serializacion productiva de `PocketMillingSpec`: feature
   `ClosedPocket`, operacion `BottomAndSideRoughMilling`, estrategia
   `ContourParallel`, `AllowanceSide/Bottom`, toolpaths y curvas internas.
2. Generar una primera tanda en `S:\Maestro\Projects\ProdAction\PGMX\generated`
   para comparar contra los manuales.
3. Recién despues quitar el bloqueo `NotImplementedError` de la sintesis
   productiva.

## Tareas Pendientes Registradas

- Cuando `Vaciado_018/019` esten exactos, diseniar la serializacion productiva
  de `PocketMillingSpec`: feature `ClosedPocket`, operacion
  `BottomAndSideRoughMilling`, estrategia `ContourParallel`, toolpaths y
  curvas internas.
- Mantener bloqueada la sintesis productiva con `NotImplementedError` hasta
  que el XML generado pueda validarse contra Maestro.

## Plan De Trabajo

1. Crear ejemplos manuales minimos en Maestro dentro de `manual/`.
2. Ejecutar `py -3 -m tools.pgmx_vaciado.scan_samples`.
3. Comparar snapshots entre ejemplos que cambien una sola variable.
4. Identificar el modelo minimo de datos para representar `Vaciado`.
5. Probar generacion automatica en `generated/`.
6. Migrar soporte de lectura/adaptacion/dibujo/sintesis a los modulos
   existentes.
7. Recien despues estudiar la traduccion ISO del nuevo mecanizado.

## Actualizacion 2026-05-17

- Se implemento la serializacion productiva inicial de `PocketMillingSpec`
  para Vaciado rectangular sobre `Top`.
- La tanda `generated/Vaciado_001_synth.pgmx` ..
  `generated/Vaciado_019_synth.pgmx` se genero desde `Vaciado_000.pgmx` y se
  readapto correctamente: `19/19` con un unico `pocket_milling`, `0`
  unsupported y trayectoria `X/Y/Z` exacta.
- La validacion de herramienta de `PocketMillingSpec` conserva la validacion de
  profundidad, pero no aplica el filtro estricto de fresado de perfil porque
  `Vaciado_004` usa `E002 (1901)` catalogada como `Sierra Horizontal` y Maestro
  la acepta para este caso.
- El primer intento fallaba al abrir en Maestro con error de deserializacion:
  el log `C:\Program Files (x86)\Scm Group\Maestro\Log\Log20260517_010134.logx`
  indicaba que `ClosedPocket` estaba en el namespace `Milling`. Se corrigio
  para emitir `ManufacturingFeature i:type="a:ClosedPocket"` con namespace
  `ScmGroup.XCam.MachiningDataModel`, igual que los manuales.
- Se regenero `generated/Vaciado_001_synth.pgmx` .. `019_synth.pgmx` despues de
  esa correccion y el roundtrip interno sigue en `19/19`.
- Ante un segundo error de Maestro sin `logx` nuevo, se comparo el bloque
  `ClosedPocket` campo por campo. Los campos propios del bolsillo
  (`BossGeometryList`, `BossList`, `BoundaryGeometryList`, `OrthogonalRadius`,
  `PlanarRadius`, `Slope`) estaban en `ProjectModule`; el manual los emite en
  `ScmGroup.XCam.MachiningDataModel`. Se corrigio y se genero
  `generated/Vaciado_001_synth_closedpocket_fields.pgmx` para prueba aislada.
- `generated/Vaciado_001_synth_closedpocket_fields.pgmx` abrio correctamente
  en Maestro y fue guardado sin modificaciones. La copia guardada por Maestro
  pesa mas porque reserializa namespaces/prefijos, pero `def.tlgx` y `.epl`
  quedan identicos y la comparacion semantica del XML contra una generacion
  fresca de Codex da `0` diferencias.
- Se limpio `S:\Maestro\Projects\ProdAction\PGMX\generated` y se regenero la
  serie canonica `Vaciado_001_synth.pgmx` .. `Vaciado_019_synth.pgmx` con los
  hallazgos de namespaces incorporados. Roundtrip automatico: `19/19` ok, un
  unico `pocket_milling`, `0` unsupported y trayectoria `X/Y/Z` exacta.
- Se abrieron los 19 generados en Maestro y se guardaron encima sin cambios.
  Luego se genero una serie fresca paralela en
  `S:\Maestro\Projects\ProdAction\PGMX\_analysis\compare_after_maestro_save`
  y se comparo archivo por archivo contra los guardados por Maestro.
  Resultado: XML semanticamente equivalente `19/19`, `def.tlgx` identico
  `19/19`, `.epl` identico `19/19`. Maestro solo reserializa prefijos y
  declaraciones de namespace, aumentando el XML entre `3561` y `7017` bytes
  y el ZIP entre `548` y `691` bytes.
- Reportes de esta comparacion:
  `S:\Maestro\Projects\ProdAction\PGMX\_analysis\compare_after_maestro_save\maestro_save_diff_summary.md`
  y `maestro_save_diff_summary.csv`.
- Regla de dominio aclarada: los vaciados solo se hacen en plano `Top` porque
  el CNC no cuenta con herramientas para trabajos de vaciado en otras caras.
  Esto deja de ser una limitacion pendiente y pasa a ser una restriccion
  esperada del modelo.
- Tarea actual: seguir aprendiendo sobre `Vaciado`, especialmente geometria de
  borde no rectangular y vaciados con isla. Nuevos manuales para estudiar:
  `manual/Vaciado_020.pgmx`, `manual/Vaciado_021.pgmx` y
  `manual/Vaciado_022.pgmx`.
- Correccion de modelo: `PocketMillingSpec` ahora conserva `boss_contours`
  leidos desde `BossGeometryList`. `Vaciado_022` se adapta con una isla
  rectangular `150..250 x 100..200` y ya no se pierde esa informacion.
- Guardrail productivo: la sintesis de `PocketMillingSpec` ahora falla
  explicitamente si hay `boss_contours` o si el contorno no coincide con el
  rectangulo completo de la pieza. Esto evita generar PGMX incorrectos para
  `Vaciado_020`, `021` y `022` hasta resolver esos modelos. La serie estable
  `Vaciado_001..019` sigue generando sin fallos.
- Se corrigieron `manual/Vaciado_023.pgmx` .. `026` para usar herramienta
  `E006`/`1905`/`80mm`, y se agregaron `manual/Vaciado_032.pgmx` .. `035` con
  las mismas geometrías pero herramienta chica `E001`/`1900`/`18.36mm`.
  Escaneo actualizado: no hay anomalías estructurales en `023..035`.
  Pares comparables:
  `023/032`, `024/033`, `025/034`, `026/035`. La herramienta chica conserva
  la geometría, usa `RadialCuttingDepth=9.18` y genera muchas más pasadas:
  `47`, `29`, `47`, `59` puntos contra `5`, `5`, `5`, `11` con E006.
  Reporte:
  `S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_023_035\vaciado_023_035_tool_comparison.md`.
- Pendiente real: agregar test automatizado de roundtrip para fijar la
  cobertura estable y extender el laboratorio con los casos `020..022`.
- Avance posterior: se agrego `tests/test_pgmx_vaciado.py` como cobertura
  automatizada del hito actual. La prueba sintetiza/readapta
  `Vaciado_001..019` desde `Vaciado_000.pgmx` y compara las trayectorias
  `X/Y/Z` contra el generador rectangular validado. Tambien fija los guardrails:
  `Vaciado_020` y `021` deben fallar por contorno distinto del rectangulo
  completo, y `Vaciado_022` debe conservar una isla `150..250 x 100..200` pero
  seguir fallando por `BossGeometryList` no productivo.
- Avance posterior: se resolvio el primer bloque del plan, contornos
  rectangulares parciales sin islas. El generador `ContourParallel` ahora usa
  el bbox real del contorno en lugar de asumir siempre `0..length/0..width`.
  Esto cubre tambien contornos que exceden los limites de la pieza: Maestro
  aplica el offset contra el bbox del contorno, no contra el tablero. La
  comparacion amplia `Vaciado_001..035` queda `29/35` exacta; los no exactos
  son `022` y `027..031`, todos asociados a islas o geometria especial.
- La sintesis productiva de `PocketMillingSpec` ya acepta contornos
  rectangulares parciales sin islas. Casos cubiertos por test:
  `Vaciado_001..021`, `023..026` y `032..035`, comparando la traza generada
  contra la traza manual de Maestro. El guardrail que queda activo es
  `BossGeometryList`/islas.

## Plan Para Terminar El Estudio De Vaciados

Objetivo actual: cerrar el modelo productivo de `Vaciado` sin perder
informacion de Maestro y sin generar PGMX incompletos.

1. Tests automatizados ya fijados para el hito estable:
   - `Vaciado_001..021`, `023..026` y `032..035`: sintetizan, readaptan y
     reproducen la traza manual exacta.
   - `Vaciado_022`: se adapta conservando `boss_contours`, pero la sintesis
     falla explicitamente por islas.
2. Ampliar tests cuando existan reglas productivas nuevas:
   - `Vaciado_027..031`: corpus pendiente para una o varias islas.
3. Resolver islas:
   - modelar `BossGeometryList` y `BossList` de forma productiva;
   - estudiar offsets alrededor de una isla (`022`, `027`, `028`);
   - estudiar multiples islas (`029`, `030`, `031`);
   - entender segmentos diagonales/tangenciales y corredores entre exterior e
     islas.
4. Recien despues levantar los guardrails de sintesis:
   - primero para islas rectangulares simples;
   - luego para multiples islas;
   - mantener bloqueados arcos, poligonos no rectangulares y casos sin corpus.
5. Cuando el PGMX este estable, retomar la traduccion ISO del nuevo mecanizado.

## Actualizacion 2026-05-18

- Se corrigio la lectura auxiliar del laboratorio para no quedarse solo con el
  primer `TrajectoryPath` de una operacion. Esto importa para islas: Maestro
  puede materializar varias ternas `Approach/TrajectoryPath/Lift` dentro del
  mismo `BottomAndSideRoughMilling`.
- El scanner de `tools.pgmx_vaciado.scan_samples` ahora resume todas las
  trayectorias de una operacion. En el corpus con islas queda visible:
  `Vaciado_022=42`, `Vaciado_027=12+20=32`, `Vaciado_028=52`,
  `Vaciado_029=64`, `Vaciado_030=27`, `Vaciado_031=5+10=15`.
- `tests/test_pgmx_vaciado.py` fija el corpus pendiente de islas:
  `Vaciado_022`, `027` y `028` conservan una isla rectangular
  `150..250 x 100..200`; `Vaciado_029..031` conservan dos islas
  `75..125 x 125..175` y `275..325 x 125..175`.
- La sintesis productiva sigue bloqueada para `BossGeometryList`/islas. El
  nuevo test verifica explicitamente que esos seis casos se adaptan sin perder
  geometria, pero levantan `NotImplementedError` al sintetizar.
- Proximo paso recomendado: derivar reglas productivas de trayectoria para
  islas antes de serializarlas. Separar primero los casos con multiples
  trayectorias (`027`, `031`) de los casos con una sola trayectoria
  (`022`, `028`, `029`, `030`) y estudiar como `BossList` condiciona el orden
  de contornos y los puentes internos.
- Se agrego `tools.pgmx_vaciado.island_analysis` y se genero el reporte:
  `S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_islands_analysis\vaciado_islands_analysis.md`.
  El reporte confirma que `Vaciado_027` es el mejor caso de arranque: una
  isla rectangular, dos trayectorias separadas, y la primera trayectoria
  comparte los primeros `6` puntos con el generador rectangular sin islas.
  Luego Maestro modifica el puente hacia el segundo anillo y corta la
  trayectoria exterior. La segunda trayectoria alrededor de la isla tiene
  bbox `X 95..305`, `Y 45..255` y puntos diagonales/intermedios, por lo que
  no debe implementarse todavia como un rectangulo simple expandido.
- Decision de continuidad: no agregar generador experimental de islas hasta
  explicar la trayectoria secundaria de `Vaciado_027` y contrastarla contra
  `Vaciado_031`. El guardrail de `BossGeometryList` permanece activo.
- Avance posterior: el reporte de islas ahora detecta estructura de offsets.
  En `Vaciado_027`, la secuencia 2 se parte en `10+10` puntos: la segunda
  vuelta es un offset radial exterior exacto de `40 mm` respecto de la primera
  (`max delta 0`). Ademas, la primera vuelta de esa secuencia coincide
  exactamente en XY con la secuencia 2 de `Vaciado_031`. Esto sugiere dos
  reglas separadas: primero generar una vuelta base de isla/corredor, y luego
  aplicar repeticiones por `radial_step` hacia afuera cuando hay espacio.
- Proximo frente concreto: explicar como se construye esa vuelta base de `10`
  puntos antes de escribir generacion productiva. No alcanza con expandir el
  bbox de `BossGeometryList`: la vuelta base incorpora diagonales y puntos de
  transicion que tambien aparecen en configuraciones con dos islas.

## Actualizacion 2026-05-19

- Revision de serie completa actual: `manual/Vaciado_001.pgmx` ..
  `manual/Vaciado_035.pgmx`. La comparacion contra el generador rectangular
  actual queda exacta en `29/35`; los unicos no exactos son `022` y
  `027..031`, todos asociados a `BossGeometryList`/islas.
  Reportes regenerados:
  `S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_001_035_trace_review\vaciado_contour_parallel_comparison.md`
  y
  `S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_001_035_trace_review\islands\vaciado_islands_analysis.md`.
- Se fijo la primera regla explicativa de la vuelta base compartida por
  `Vaciado_027` y `Vaciado_031`. Los `10` puntos no salen del bbox completo
  de `BossGeometryList`: son un contorno redondeado de radio `40` construido
  sobre un nucleo rectangular `X 175..225, Y 125..175`.
- En `Vaciado_027`, ese nucleo es el bbox de la isla `150..250 x 100..200`
  reducido `25 mm` por lado. En `Vaciado_031`, el mismo nucleo aparece como
  corredor central entre las dos islas `75..125 x 125..175` y
  `275..325 x 125..175`, con margenes laterales de `50 mm` y el mismo tramo
  `Y 125..175`.
- Correccion importante de lectura: el nucleo no solo se infiere desde la
  trayectoria. En el XML, `BossGeometryList` conserva la isla fisica, pero
  `BossList/GeometryID` puede resolver a otra geometria que Maestro usa como
  semilla de ruteo. Casos vistos:
  - `Vaciado_022`: `BossList` coincide con la isla fisica `150..250 x 100..200`.
  - `Vaciado_027`: `BossList` resuelve al nucleo `175..225 x 125..175`.
  - `Vaciado_028`: `BossList` resuelve a `275..325 x 125..175`.
  - `Vaciado_029`: `BossList` coincide con las dos islas fisicas.
  - `Vaciado_030`: un ref de `BossList` no resuelve y el otro resuelve a
    `325..375 x 125..175`.
  - `Vaciado_031`: un ref de `BossList` no resuelve y el otro resuelve al
    nucleo `175..225 x 125..175`.
- La trayectoria de `Vaciado_027` confirma dos capas: primera vuelta base con
  radio `40`, segunda vuelta por offset radial exterior exacto de `40 mm`.
  `Vaciado_031` conserva solo la vuelta base como segunda trayectoria.
- Se agregaron helpers de laboratorio en `tools.pgmx_vaciado.island_analysis`
  para generar e inferir esa vuelta redondeada desde el nucleo, resolver las
  geometrias de `BossList`, y tests que fijan la coincidencia exacta contra
  `Vaciado_027` y `Vaciado_031`.
- El guardrail productivo para `BossGeometryList` sigue activo. La regla nueva
  explica la vuelta base comun, pero todavia faltan reglas de orden/puente y
  mezcla con trayectoria exterior para `Vaciado_022`, `028`, `029` y `030`.
- Antes de volcar esto a generacion productiva, el modelo publico deberia
  preservar dos conceptos separados: contorno fisico de isla
  (`BossGeometryList`) y contorno/semilla de ruteo (`BossList.GeometryID`).

## Actualizacion 2026-05-20

- Correccion conceptual del estudio de trazas: cuando se habla del paso radial
  entre vueltas no debe decirse que la regla primaria es "igual al radio de
  herramienta". La magnitud correcta es:
  `paso_radial = diametro_herramienta * (1 - overlap)`.
- En las variantes `Vaciado_022_E00x` y `Vaciado_027_E00x`, `overlap=0.5`.
  Por eso el paso radial observado coincide numericamente con el radio de
  herramienta, pero solo como consecuencia del `50%` de superposicion.
- Para futuras reglas y generacion productiva, los radios/offsets sucesivos
  deben expresarse como multiplos del paso radial efectivo, no necesariamente
  como multiplos del radio de herramienta.
- Regla clave hallada en `Vaciado_029_E00x`: con dos islas/semillas activas,
  Maestro genera offsets alrededor de cada isla como multiplos del paso radial
  efectivo. Mientras el offset no supera la mitad del claro entre islas, las
  islas se comportan como obstaculos separados. Cuando el offset supera esa
  mitad de claro, los offsets se intersectan y Maestro recorta la zona entre
  islas usando puntos de interseccion de circunferencias como puentes.
- Evidencia numerica de `Vaciado_029_E006`: claro entre islas `150 mm`, mitad
  de claro `75 mm`, paso radial efectivo `40 mm`. El offset `80 mm` supera
  `75 mm`; la interseccion de arcos superiores queda en
  `x=200`, `y=175 + sqrt(80^2 - 75^2) = 202.838822`, punto que aparece
  exactamente en la traza. La interseccion inferior da
  `y=125 - sqrt(80^2 - 75^2) = 97.161178`, tambien presente.
- Revision de `Vaciado_030_E00x`: las variantes de cambio de herramienta
  reescriben `BossGeometryList` como una sola semilla de ruta
  `X 325..375, Y 125..175`, y `BossList.GeometryID=10748` resuelve a la misma
  geometria. El caso base `Vaciado_030.pgmx` conserva dos islas fisicas
  `X 75..125, Y 125..175` y `X 275..325, Y 125..175`, mas un ref no resuelto
  `13322` y la semilla de ruta `10748`. `Vaciado_030_E006.pgmx` reproduce
  exactamente la traza base.
- En `Vaciado_030_E00x`, todas las herramientas quedan en una sola
  `TrajectoryPath`. La semilla esta pegada al lado derecho del bolsillo
  exterior, por eso las vueltas se recortan contra la pared y los arcos de
  mayor herramienta quedan dominados por las esquinas izquierdas de la semilla
  `(325,125)` y `(325,175)`. Las esquinas derechas `(375,125)` y `(375,175)`
  solo aportan arcos cuando el paso efectivo es chico; con E002/E005/E006 ya
  no aparecen como centros de arco en la traza. La variante E004, con paso
  `2 mm`, deja ver centros adicionales `(203,125)` y `(203,175)`; queda como
  detalle fino de esqueleto/recorte para revisar antes de generar este caso.
- Cierre del detalle `Vaciado_030_E004`: los centros `(203,125)` y
  `(203,175)` no representan una semilla nueva. Aparecen una sola vez cada uno
  con radio `2 mm`, igual al paso radial efectivo. Son empalmes de transicion
  en el primer offset que cruza la zona de esquina de la semilla derecha: para
  offset `124`, la recta vertical esperada queda en `x=325-124=201`, y el
  microarco de radio `2` queda centrado en `x=203`. En el offset siguiente
  (`122`), la interseccion con la esquina `(325,125)` ya sigue la formula
  `x=325 - sqrt(122^2 - 3^2) = 203.036891`; con offset `120`, Maestro vuelve a
  serializar arcos explicitos centrados en `(325,125)` y `(325,175)` de radio
  `120`. Por lo tanto estos centros extra son un artefacto de empalme/tolerancia
  en un caso de paso muy chico, no una regla topologica aparte.
- Revision de `Vaciado_031_E00x`: las variantes materializan una sola semilla
  central `X 175..225, Y 125..175`, tambien coincidente entre
  `BossGeometryList` y `BossList.GeometryID=10748`. El caso base
  `Vaciado_031.pgmx` conserva dos islas fisicas y usa esa semilla central como
  corredor de ruta; `Vaciado_031_E006.pgmx` reproduce exactamente la traza
  base en dos trayectorias de `5 + 10` puntos.
- Regla de cierre para `Vaciado_031_E00x`: el claro vertical desde la semilla
  central hasta el bolsillo `Y 25..275` es `100 mm`, por lo tanto la mitad de
  claro es `50 mm`. Las vueltas completas alrededor de la semilla aparecen
  mientras el offset efectivo no supera `50 mm`. Cuando el siguiente offset
  supera ese umbral, Maestro intenta una vuelta parcial/puente si todavia hay
  geometria valida. E005 (`paso 38`) genera una vuelta parcial a `76 mm` y
  queda en una sola trayectoria; E006 (`paso 40`) conserva solo la vuelta base
  de `40 mm` y separa el rectangulo exterior de la vuelta de isla.
- Conclusion operativa agregada por `030/031`: para islas no alcanza con
  serializar el contorno fisico. El modelo de lectura/generacion debe retener
  dos conceptos: `BossGeometryList` como isla fisica y `BossList.GeometryID`
  como semilla de ruta. En variantes editadas por herramienta, Maestro puede
  materializar directamente esa semilla en `BossGeometryList`, pero no debe
  confundirse con la evidencia fisica del caso base.

## Actualizacion 2026-05-20 - Volcado A Codigo

- La separacion `BossGeometryList` / `BossList.GeometryID` ya quedo en el
  modelo estable. `tools.synthesize_pgmx` expone `PocketBossRouteSeedSpec` y
  `PocketMillingSpec.boss_route_seeds`; cada semilla conserva `geometry_id`,
  `object_type`, `name` y `contour_points` cuando la geometria resuelve.
- `tools.pgmx_adapters` ahora llena `boss_route_seeds` al adaptar
  `ClosedPocket + BottomAndSideRoughMilling + ContourParallel`. Los refs no
  resueltos se preservan como semilla sin `contour_points`, en vez de
  descartarse.
- `tools.pgmx_vaciado.island_analysis.resolved_boss_ref_xy_contours(...)`
  quedo como wrapper del nuevo dato estable cuando la adaptacion produce
  `PocketMillingSpec`.
- La sintesis productiva sigue bloqueada para `BossGeometryList` o semillas
  `BossList.GeometryID`. El cambio de codigo actual es de modelo/lectura y
  guardrail: evita perder la semilla de ruteo antes de implementar la
  generacion completa de trayectorias con islas.
- Tests fijados: `tests.test_pgmx_vaciado` comprueba las semillas resueltas de
  `022`, `027`, `028`, `030` y `031`, las variantes `030/031_E00x`, el caso
  exacto `E006`, la regla de paso radial efectivo y el micro-empalme de
  `Vaciado_030_E004`.

## Actualizacion 2026-05-21

- Primer soporte controlado de sintesis con isla/semilla para `Vaciado`:
  `Vaciado_031_E006` ya se genera desde `PocketMillingSpec` y reproduce
  exactamente las dos `TrajectoryPath` de Maestro (`5 + 10` puntos).
- La compuerta sigue siendo estricta: solo se permite una semilla resuelta de
  `BossList.GeometryID`, materializada tambien como unico `BossGeometryList`,
  centrada en el bolsillo y en la condicion donde corresponde solo la vuelta
  base. Los casos `027`, `029` y `030` siguen bloqueados para sintesis
  productiva hasta codificar sus offsets/puentes/recortes.
- La trayectoria generada para el caso soportado se divide en:
  1. rectangulo exterior offseteado por el centro de herramienta;
  2. vuelta base redondeada sobre la semilla `X 175..225, Y 125..175` con
     radio igual al paso radial efectivo (`40 mm` en E006).
- La serializacion ya escribe `BossGeometryList` y `BossList` en el `.pgmx`
  generado para el caso soportado, no solo la trayectoria. Se genero un
  artefacto externo para inspeccion manual:
  `S:\Maestro\Projects\ProdAction\PGMX\generated\Vaciado_031_E006_synth.pgmx`.
- Validacion local: `py -3 -m unittest tests.test_pgmx_vaciado` queda en `9`
  tests OK. La suite tambien fija que `Vaciado_027_E006` permanece bloqueado
  hasta implementar la segunda vuelta por offset. El artefacto generado
  re-adaptado conserva secuencias `5 + 10` exactas contra
  `manual/Vaciado_031_E006.pgmx`.
- Correccion posterior del mismo hito: la primera implementacion comparaba
  puntos muestreados y por eso podia generar la vuelta de isla como poligono.
  Se corrigio `TrajectoryPath` para serializar la vuelta base con arcos Maestro
  reales. La validacion ahora compara tambien centros/radios de arcos contra
  el original: `(175,175,R40)`, `(225,175,R40)` dos veces, `(225,125,R40)` y
  `(175,125,R40)`. Se regenero
  `S:\Maestro\Projects\ProdAction\PGMX\generated\Vaciado_031_E006_synth.pgmx`
  con esa correccion.
