# PGMX Vaciado

Ultima actualizacion: 2026-06-03

Nota arquitectonica: `Vaciado` queda como nombre historico del corpus. El
destino final del mecanizado es `pgmx.synthesis.milling.pocket`
(`ClosedPocket`/pocket milling). La memoria y las herramientas utiles viven
ahora en `pgmx.machining_lab.pocket_milling`; `pgmx.vaciado_lab` queda como
fachada historica durante la transicion.

## Objetivo

Abrir una investigacion separada para mecanizados `.pgmx` que todavia no estan
soportados por las herramientas actuales y que vamos a estudiar bajo el concepto
operativo de `Vaciado`.

## Memoria Temporal Activa

- Reconstruccion V2 de `Vaciado`: leer
  `pgmx/machining_lab/pocket_milling/memory/vaciado-v2-rebuild.md` antes de avanzar con el
  nuevo motor o con decisiones sobre la estrategia de sintesis.

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
- Vive bajo `pgmx/machining_lab/pocket_milling/`. Las rutas
  `pgmx.vaciado_lab.*` y `tools.pgmx_vaciado.*` se mantienen solo como
  fachadas historicas de comandos/imports durante la transicion.
- Una regla solo se migra a `pgmx.snapshot`, `pgmx.adapters`,
  `pgmx.synthesis`, `pgmx.processing` o `iso_state_synthesis/` cuando tenga
  evidencia suficiente.
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

## Actualizacion 2026-05-21 - Regla Multi-Vuelta

- Se codifico un segundo caso controlado de sintesis con semilla central:
  `Vaciado_031_E001`. El paso radial efectivo es
  `diametro_herramienta * (1 - overlap) = 18.36 * 0.5 = 9.18 mm`.
- La regla observada separa los offsets en dos familias. Las vueltas completas
  alrededor de la semilla son los multiplos del paso que no superan la mitad
  del claro vertical (`50 mm`): `9.18`, `18.36`, `27.54`, `36.72` y
  `45.9`. Las vueltas parciales son los multiplos siguientes que superan esa
  mitad vertical pero todavia caben contra la mitad del claro horizontal
  (`75 mm`): `55.08`, `64.26` y `73.44`.
- Maestro encadena todo en una sola `TrajectoryPath`: primero lobulos
  parciales izquierdos descendentes, luego rectangulos exteriores completos
  descendentes, despues lobulos parciales derechos ascendentes y finalmente
  vueltas completas alrededor de la semilla en sentido descendente. El punto
  angular de arranque de las vueltas internas queda fijado por la interseccion
  de la vuelta parcial minima (`55.08`) con el borde inferior del bolsillo.
- La serializacion generada usa arcos Maestro reales para todos los tramos
  circulares, incluyendo las vueltas internas y los lobulos parciales. La
  validacion compara la secuencia de `152` puntos y los `43` arcos contra
  `manual/Vaciado_031_E001.pgmx`.
- `Vaciado_031_E005` se identifico luego como una frontera distinta: no tiene
  lobulos parciales completos, sino micro-puente sin lobulo parcial. Esa
  subregla queda registrada mas abajo.

## Actualizacion 2026-05-21 - Micro-Puente Multi-Vuelta

- La regla multi-vuelta tambien quedo validada para `Vaciado_031_E003`
  (`paso_radial = 4.76 mm`). Este caso usa `10` vueltas completas
  (`4.76..47.6`), `5` lobulos parciales dentro del medio claro horizontal
  (`52.36..71.4`) y un micro-puente adicional en `76.16 mm`, apenas por encima
  del medio claro horizontal de `75 mm`.
- El micro-puente agrega arcos cortos de radio `76.16` en los cuadrantes donde
  el offset ya no puede formar un lobulo parcial completo. La traza resultante
  conserva una sola `TrajectoryPath`, pero repite el lobulo parcial maximo para
  conectar los microarcos superior/inferior del lado derecho y cierra con un
  microarco superior izquierdo.
- `tools.synthesize_pgmx` ahora sintetiza `Vaciado_031_E001` y
  `Vaciado_031_E003` con arcos Maestro reales. Los artefactos externos
  regenerados son:
  `S:\Maestro\Projects\ProdAction\PGMX\generated\Vaciado_031_E001_synth.pgmx`
  y
  `S:\Maestro\Projects\ProdAction\PGMX\generated\Vaciado_031_E003_synth.pgmx`.

## Actualizacion 2026-05-21 - Vuelta De Borde

- La subregla pendiente quedo identificada y codificada: cuando una vuelta
  completa cae exactamente sobre la mitad del claro vertical (`50 mm`), Maestro
  la trata como `vuelta de borde`, no como una vuelta interna con angulo beta.
- En `Vaciado_031_E002` la vuelta de borde es el caso minimo: arranca en
  `(75,75)`, entra a la semilla por `(225,75)`, ejecuta la vuelta redondeada de
  radio `50`, vuelve a `(225,75)` y recien despues completa el rectangulo
  exterior de `r=50`.
- En `Vaciado_031_E004` la misma vuelta de borde aparece dos veces: primero
  antes del rectangulo exterior de `r=50`, y luego otra vez antes de las
  vueltas internas `48..2`. Despues de esas vueltas internas Maestro baja por
  el borde derecho inferior de la semilla (`x=225`) hasta `r=50`, ejecuta los
  lobulos parciales derechos, cierra por el rectangulo exterior de borde y
  finalmente sube por el ancla izquierda para cerrar el lobulo parcial/maximo y
  el micro-puente.
- El umbral de serializacion de la esquina superior derecha tambien queda
  fijado: si el tramo desde la interseccion parcial hasta el punto diagonal de
  45 grados es muy corto (caso `r=58` en E004), Maestro lo serializa como linea
  y no como arco, aunque el punto diagonal exista en la secuencia.
- Artefactos regenerados y validados contra Maestro:
  `Vaciado_031_E001_synth.pgmx`, `Vaciado_031_E002_synth.pgmx`,
  `Vaciado_031_E003_synth.pgmx` y `Vaciado_031_E004_synth.pgmx`.

## Actualizacion 2026-05-21 - Micro-Puente Sin Lobulo Parcial

- `Vaciado_031_E005` cierra la frontera entre la vuelta base y la ruta
  multi-vuelta. Tiene `paso_radial = 38 mm`, una vuelta completa interna de
  `38 mm` y un siguiente offset de `76 mm`, apenas por encima del medio claro
  horizontal (`75 mm`).
- Como no hay offset intermedio entre `50 mm` y `75 mm`, no aparecen lobulos
  parciales completos. Maestro genera cuatro microarcos de `r=76` alrededor de
  las esquinas de la semilla y conecta la vuelta completa de `r=38` usando el
  mismo angulo del microarco superior izquierdo.
- `Vaciado_031_E007` confirma que la regla comun de `E001` no depende del
  diametro exacto: con `paso_radial = 8.86 mm` vuelve a dar `5` vueltas
  completas, `3` lobulos parciales y ninguna vuelta de borde ni micro-puente.
- La serie `Vaciado_031_E001..E007` queda sintetizada y validada contra
  Maestro. Longitudes/arcos:
  `E001=152/43`, `E002=15/5`, `E003=332/90`, `E004=741/189`,
  `E005=49/10`, `E006=5+10/5`, `E007=152/43`.
- Artefactos regenerados:
  `S:\Maestro\Projects\ProdAction\PGMX\generated\Vaciado_031_E001_synth.pgmx`
  hasta
  `S:\Maestro\Projects\ProdAction\PGMX\generated\Vaciado_031_E007_synth.pgmx`.

## Actualizacion 2026-05-22 - Vuelta Base Multiple Separada

- Se avanzo sobre `Vaciado_027_E006`, primer caso fuera de `031` soportado
  por sintesis con semilla. La semilla resuelta sigue siendo el nucleo
  `175..225 x 125..175`, pero el contorno del bolsillo es mayor
  (`-50..450 x -50..350`), por lo que caben dos vueltas base completas antes
  de llegar al medio claro minimo.
- La regla queda separada de la multi-vuelta de `031`: con `paso_radial =
  40 mm`, Maestro genera dos `TrajectoryPath`. La primera contiene los
  rectangulos exteriores para `r=40` y `r=80`; la segunda concatena las vueltas
  redondeadas de la semilla para esos mismos radios (`r=40` y `r=80`).
- La serializacion productiva se habilito de forma estrecha para semillas
  resueltas de `50 x 50`, centradas y con `paso_radial = 40 mm`. Esto permite
  `Vaciado_027_E006` y conserva bloqueados casos como `022`, donde la semilla
  fisica es `100 x 100` y responde a otra regla.
- Artefacto regenerado y validado:
  `S:\Maestro\Projects\ProdAction\PGMX\generated\Vaciado_027_E006_synth.pgmx`.
  La comparacion contra Maestro da `12 + 20` puntos exactos y `10` arcos
  iguales.
- Validacion extra contra el archivo abierto y re-guardado por Maestro:
  se preservo el archivo Maestro y se regenero la misma pieza con el mismo
  nombre en carpeta temporal. El ZIP no queda identico a nivel bytes por
  serializacion/compresion, pero las entradas coinciden y el XML parseado no
  presenta diferencias estructurales. La unica diferencia textual previa era
  `-0` contra `0` en dos angulos de arco; se normalizo el angulo casi cero a
  `0.0` en sintesis.
- Antes del cierre se genero la serie completa
  `Vaciado_027_E001_synth.pgmx` .. `Vaciado_027_E007_synth.pgmx` en
  `S:\Maestro\Projects\ProdAction\PGMX\generated`. Para `E001..E005` y `E007`
  se uso la traza Maestro como plantilla validada porque la regla generativa
  `outside-to-inside` todavia no esta cerrada. La comparacion efectiva contra
  los manuales da longitudes `273`, `42`, `515`, `1185`, `68`, `12+20`,
  `273`, con delta XYZ `0.0` y arcos iguales en los siete casos.
- Proximo objetivo: reemplazar esa sintesis por plantilla en `Vaciado_027`
  por sintesis generativa pura. Falta deducir y codificar la regla
  `outside-to-inside` completa para una semilla resuelta, incluyendo el barrido
  del marco exterior, la entrada a lobulos parciales, las repeticiones de
  microarcos en los casos chicos (`E003/E004`) y el cierre especial de `E005`.

## Actualizacion 2026-05-27 - Contrato De Parametros Para Vaciado

- Correccion conceptual: la traza que se esta estudiando reproduce el metodo
  que usa Maestro para estos casos, pero no debe tratarse como la unica forma
  posible de realizar un vaciado.
- Para llegar a una generacion completa de traza, el modelo no puede depender
  solo de ejemplos rectangulares o de una semilla puntual. La entrada del
  generador debe representar todos los parametros y geometrias que definen el
  vaciado.
- Parametros y datos geometricos que deben quedar en el contrato de generacion:
  - polilinea cerrada exterior con punto inicial;
  - polilineas cerradas internas con punto inicial;
  - profundidad de vaciado;
  - rebaba/despeje al contorno;
  - diametro de herramienta;
  - direccion del recorrido: horaria o antihoraria;
  - conexion entre huecos: salida a cota de seguridad o en la pieza;
  - direccion del vaciado: adentro hacia afuera o afuera hacia adentro;
  - sobreposicion de trazas;
  - estrategia helicoidal habilitada o deshabilitada;
  - multipaso habilitado o deshabilitado;
  - profundidad de hueco y ultimo hueco cuando multipaso esta habilitado.
- Implicacion de diseno: la sintesis generativa debe separar el contrato
  geometrico/productivo del algoritmo concreto de trayectoria. Maestro puede ser
  el primer modo validado, pero el modelo debe permitir luego otras estrategias
  de vaciado sin reescribir la representacion del mecanizado.
- Antes de extender `Vaciado_027` mas alla de la plantilla validada, conviene
  revisar `PocketMillingSpec` y el generador de trayectoria para asegurar que
  estos campos existan de forma explicita, o que se documente cual queda
  pendiente y por que.

## Actualizacion 2026-05-27 - Auditoria Del Contrato En Codigo

- `PocketMillingSpec` ya conserva la polilinea exterior como
  `contour_points`. El punto inicial queda preservado por el orden de la tupla.
- Las polilineas internas existen en dos niveles:
  - `boss_contours` conserva las islas fisicas de `BossGeometryList`;
  - `boss_route_seeds` conserva las referencias de ruteo de `BossList.GeometryID`.
  Esta separacion sigue siendo necesaria porque Maestro puede rutear con una
  semilla distinta de la isla fisica.
- La profundidad de vaciado esta en `depth_spec`, y el XML de `ClosedPocket`
  se serializa con `Depth.StartDepth/EndDepth`.
- La rebaba/despeje esta en `allowance_side`; `allowance_bottom` tambien se lee
  y serializa aunque todavia no sea parte central de la regla de traza.
- El diametro de herramienta esta representado por `tool_width`.
- La estrategia `ContourParallelMillingStrategySpec` ya contiene:
  `rotation_direction`, `stroke_connection_strategy`, `inside_to_outside`,
  `overlap`, `is_helic_strategy`, `allow_multiple_passes`,
  `axial_cutting_depth` y `axial_finish_cutting_depth`, ademas de campos
  auxiliares como `radial_cutting_depth`.
- El generador rectangular sin islas ya usa direccion de recorrido, direccion
  de vaciado, rebaba, diametro, sobreposicion y multipaso. Las transiciones
  multipaso respetan `LiftShiftPlunge` contra `Straghtline`.
- El soporte productivo con islas sigue acotado: hay reglas controladas para
  semillas rectangulares resueltas de `50 x 50` en casos `031` y `027_E006`,
  pero no hay todavia un generador general para polilineas internas multiples.
- `is_helic_strategy` se lee y se serializa, pero no tiene una generacion de
  traza propia para `Vaciado`; por ahora es un parametro modelado, no una regla
  geometrica implementada.
- Se endurecio la hidratacion por plantilla de `Vaciado`: una traza Maestro
  validada solo puede reutilizarse si coinciden contorno exterior, islas,
  semillas resueltas, profundidad, cota de seguridad, herramienta, rebaba y la
  estrategia completa. Esto evita que la plantilla oculte cambios de parametros
  que deberian modificar la traza.
- Validacion agregada: `tests.test_pgmx_vaciado` comprueba que cambiar
  direccion de recorrido, rebaba o profundidad bloquea la hidratacion de la
  traza de plantilla.

## Actualizacion 2026-05-27 - Revision Parametrica Del Corpus Manual

- Se reviso nuevamente el corpus completo
  `S:\Maestro\Projects\ProdAction\PGMX\manual`.
- Archivos `Vaciado_*.pgmx` encontrados: `77`.
- Adaptados como `PocketMillingSpec`: `76`.
- Reportes generados:
  - `S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_parameter_trace_contract_2026_05_27\vaciado_manual_parameter_trace_catalog.csv`;
  - `S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_parameter_trace_contract_2026_05_27\vaciado_manual_parameter_trace_review.md`;
  - `S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_parameter_trace_contract_2026_05_27\vaciado_parameter_impact_study.md`.
- Parametros confirmados en el corpus:
  - geometria exterior con punto inicial;
  - geometrias internas fisicas `BossGeometryList`;
  - semillas de ruta `BossList.GeometryID`;
  - profundidad de vaciado;
  - `AllowanceSide` / rebaba lateral;
  - diametro de herramienta;
  - direccion de recorrido;
  - conexion entre huecos;
  - direccion de vaciado;
  - sobreposicion;
  - helicoidal;
  - multipaso con `AxialCuttingDepth` y `AxialFinishCuttingDepth`.
- Impactos confirmados:
  - `paso_radial = diametro * (1 - overlap)`;
  - el primer offset efectivo responde a `radio_herramienta + AllowanceSide`;
  - `RotationDirection` cambia sentido/orden, no necesariamente cantidad de
    puntos;
  - `InsideToOutSide` cambia orden de barrido y enlaces entre vueltas;
  - `StrokeConnectionStrategy` pesa especialmente en multipaso o huecos
    separados;
  - multipaso puede vivir dentro de una sola `TrajectoryPath` con multiples
    niveles Z;
  - con islas, el contorno fisico y la semilla de ruta deben conservarse como
    datos separados.
- Caso especial nuevo: `Vaciado_035.pgmx` es `ClosedPocket` con geometria
  circular `GeomCircle`, `AllowanceSide=20`, `InsideToOutSide=false` e
  `IsHelicStrategy=true`. El adaptador actual no lo convierte a
  `PocketMillingSpec` porque el soporte inicial exige `GeomCompositeCurve`
  cerrado. La traza observada usa arcos circulares a Z constante y un enlace
  radial; aunque el flag helicoidal esta activo, no aparece una rampa Z
  helicoidal en `TrajectoryPath`.
- Implicacion: el contrato de vaciado debe poder evolucionar de polilineas
  cerradas hacia contornos cerrados con arcos/circulos, o documentar una
  conversion explicita a polilinea cuando se quiera mantener ese limite.

## Actualizacion 2026-05-27 - Primitivas De Traza Maestro

- Se agrego el analizador de laboratorio
  `tools/pgmx_vaciado/trace_primitives.py` para descomponer las
  `TrajectoryPath` Maestro de `Vaciado_*.pgmx` en primitivas `Line`/`Arc`,
  clasificarlas contra el contorno exterior, semillas de ruta e islas, y
  producir un resumen reproducible.
- Ejecucion sobre el corpus manual completo:
  `py -3 -m tools.pgmx_vaciado.trace_primitives --output-dir S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_trace_primitives_2026_05_27`.
- Artefactos generados:
  - `S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_trace_primitives_2026_05_27\vaciado_trace_case_summary.csv`;
  - `S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_trace_primitives_2026_05_27\vaciado_trace_primitives.csv`;
  - `S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_trace_primitives_2026_05_27\vaciado_trace_primitives_study.md`.
- Resultado global: `77` casos, `76` adaptados como bolsillo y
  `1` caso `snapshot_only` (`Vaciado_035.pgmx` circular). Se extrajeron
  `14448` primitivas: `10648` lineas y `3800` arcos.
- La mezcla de relaciones confirma que los casos con islas no deben modelarse
  solo como offsets del contorno exterior. En el corpus aparecen `3794` arcos
  clasificados como `route_seed_corner_arc`; es decir, sus centros caen en las
  esquinas de la semilla resuelta de ruta, no necesariamente en las esquinas de
  la isla fisica.
- Gramatica candidata de traza Maestro registrada por el informe:
  1. normalizar el contorno y conservar su punto inicial;
  2. calcular `effective_offset = tool_radius + AllowanceSide`;
  3. calcular `radial_step = tool_width * (1 - overlap)`;
  4. generar familias de offsets del contorno exterior cuando no hay islas;
  5. con islas, usar `BossList.GeometryID` como semilla de ruteo separada de
     `BossGeometryList`;
  6. aplicar `InsideToOutSide` al orden de vueltas y puentes;
  7. aplicar `RotationDirection` al sentido/orientacion de las vueltas;
  8. aplicar `StrokeConnectionStrategy` en transiciones de niveles o huecos
     separados;
  9. representar multipaso como secuencias de niveles Z dentro de una o mas
     `TrajectoryPath`.
- `Vaciado_035.pgmx` queda caracterizado aunque no adapte a polilinea:
  circulo nominal de radio `125`, herramienta `E006` de diametro `80`,
  `AllowanceSide=20`, `radial_step=40`; Maestro genera radios de traza
  `65` y `25`, coherentes con `125 - (40 + 20)` y una reduccion por paso
  radial. El flag helicoidal esta activo, pero las primitivas quedan a Z
  constante en la trayectoria observada.
- Para `Vaciado_027_E006`, el analizador confirma el checkpoint generativo:
  `12+20` puntos, `20` lineas, `10` arcos, y `10/10` arcos ligados a esquinas
  de semilla de ruta. Para `Vaciado_027_E004`, la misma regla escala a
  `1185` puntos, `852` lineas y `332` arcos, todos ligados a la semilla.
- El informe deja como casos foco tambien `Vaciado_027_E002` y
  `Vaciado_027_E005`: `E002` tiene `42` puntos, `30` lineas y `11` arcos
  con radios de semilla `50/100`; `E005` tiene `68` puntos, `51` lineas y
  `16` arcos con radios `38/76/114`. Estos dos son buenos candidatos para
  cerrar primero la regla `outside-to-inside` generalizada.
- Proxima frontera practica: convertir esta gramatica candidata en una
  implementacion generativa pura para `outside-to-inside` en `Vaciado_027`,
  usando el CSV de primitivas como oraculo de orden, radios, enlaces y cambios
  de familia. La hidratacion por plantilla queda solo como red de seguridad
  validada, no como explicacion de la traza.

## Actualizacion 2026-05-27 - Esqueleto General Del Motor De Traza

- Se creo `tools/pgmx_vaciado/trace_engine.py` como punto de entrada general
  para el futuro motor de vaciado por contornos paralelos. El modulo no esta
  nombrado ni acotado a `Vaciado_027`: acepta un `PocketMillingSpec` y
  devuelve un `ContourParallelTracePlan`.
- El esqueleto ya separa capas:
  - normalizacion de contorno exterior, punto inicial, bbox, winding y forma
    rectangular;
  - normalizacion de contornos internos fisicos y semillas de ruta resueltas;
  - contrato de parametros (`tool_width`, `AllowanceSide`, `effective_offset`,
    `radial_step`, direccion, conexion, overlap, helicoidal y multipaso);
  - familias de offsets del contorno exterior;
  - familias de offsets por contorno interno/semilla, con offsets completos,
    parciales y puente cercano;
  - plan de profundidades Z para multipaso.
- La API publica inicial es
  `generate_contour_parallel_pocket_trace(spec, surface_z=...)`. Por ahora
  devuelve `trajectory_sequences=()` y `pending_stages`, porque todavia faltan
  el motor de offset geometrico real, el resolvedor topologico, el ordenador de
  recorrido, los conectores y el emisor de `TrajectoryPath`.
- Validacion agregada:
  - caso sintetico sin corpus: preserva punto inicial, calcula
    `effective_offset`, `radial_step`, offsets exteriores y niveles Z;
  - `Vaciado_027_E005`: extrae la familia interna general con offsets
    `38/76` y puente `114` desde el contrato real, sin hardcodear el nombre
    del archivo en el motor.
- Pruebas: `py -3 -m unittest tests.test_pgmx_vaciado` pasa con `15` tests.
- Proximo paso de codigo: hacer que el `TracePlan` pueda emitir primitivas
  2D abstractas (`Line`/`Arc`) antes de serializar PGMX. Esa capa debe usar
  los casos foco `Vaciado_027_E002`, `E005` y `E006` como oraculos, pero la
  implementacion debe seguir viviendo en el motor general.

## Actualizacion 2026-05-27 - Primitivas Abstractas Del Motor

- `ContourParallelTracePlan` ahora incluye `primitive_sequences`, una capa
  abstracta 2D independiente de la serializacion XML. Cada
  `TracePrimitiveSequence2D` contiene primitivas `TracePrimitive2D` de tipo
  `Line` o `Arc`, con propietario (`outer`, `internal:n`), offset, puntos,
  centro, radio y orientacion cuando aplica.
- El motor emite bucles completos para contornos rectangulares exteriores y
  bucles redondeados para semillas internas rectangulares. Para semillas, el
  bucle completo usa cuatro centros de esquina y divide la esquina superior
  derecha en dos arcos, reproduciendo la estructura abstracta observada en
  Maestro (`5` arcos por radio completo).
- Para bolsillos con internas, los bucles exteriores abstractos se acotan por
  el medio claro minimo frente a las semillas internas. Esto evita generar
  offsets exteriores que ya invaden la zona de ruteo de la isla; por ejemplo,
  `Vaciado_027_E006` queda en offsets exteriores `40/80` e internos `40/80`.
- La capa todavia no resuelve el orden global Maestro, puentes, lobulos
  parciales ni serializacion PGMX. Esos puntos siguen en `pending_stages`
  como topologia, recorrido, conectores y emisor de toolpath.
- Validacion actual:
  - caso sintetico sin corpus: emite dos bucles rectangulares de `4` lineas
    con offsets `15/30`;
  - `Vaciado_027_E005`: emite bucles exteriores `38/76`, bucles internos
    `38/76`, `5` arcos por bucle interno y centros de arco en las cuatro
    esquinas de la semilla `175..225 x 125..175`; conserva el puente pendiente
    `114`.
- Pruebas: `py -3 -m unittest tests.test_pgmx_vaciado` pasa con `15` tests.
- Proximo paso de codigo: construir el resolvedor topologico que conecte estas
  primitivas abstractas en el orden Maestro, empezando por el caso sin lobulos
  parciales (`E002/E006`) y dejando el puente `E005` como siguiente extension.

## Actualizacion 2026-05-27 - Resolvedor Topologico De Bucles Completos

- `ContourParallelTracePlan` ahora incluye `resolved_sequences`, una capa que
  conecta las primitivas abstractas en secuencias topologicas antes de llegar
  al emisor PGMX.
- Se implemento la primera regla resuelta de forma general: contorno exterior
  rectangular, una semilla rectangular, direccion `outside-to-inside`
  (`InsideToOutSide=false`), conexion `Straghtline`, offsets internos
  completos, sin lobulos parciales y sin puente.
- Para esa configuracion el motor produce dos secuencias:
  - `outer_complete_offsets`: conecta los bucles exteriores completos con las
    lineas de enlace entre offsets;
  - `internal_complete_offsets`: concatena los bucles redondeados de la
    semilla y agrega la linea de enlace entre radios.
- Validacion agregada con `Vaciado_027_E006`: la secuencia exterior queda con
  `11` lineas, de `(-10,310)` a `(30,270)`; la secuencia interna queda con
  `9` lineas y `10` arcos, de `(135,125)` a `(95,125)`. Esto replica la
  particion topologica `12 + 20` observada en Maestro, aunque todavia no se
  serializa a `TrajectoryPath`.
- Para `Vaciado_027_E005`, el motor conserva las familias `38/76` y el puente
  `114`, pero no genera `resolved_sequences`; mantiene
  `topology_resolver`, `traversal_orderer` y `connector_planner` como etapas
  pendientes. Esto evita tratar el caso de puente como si fuera un bucle
  completo simple.
- Para `Vaciado_027_E002`, el nuevo analisis muestra que no es un caso simple:
  tiene un offset parcial (`100`) y una sola `TrajectoryPath` que mezcla
  contorno exterior, enlaces y arcos de semilla. Queda como frontera separada
  junto con los lobulos parciales.
- Pruebas: `py -3 -m unittest tests.test_pgmx_vaciado` pasa con `16` tests.
- Proximo paso de codigo: agregar un emisor 3D/PGMX para
  `resolved_sequences` o, antes de serializar, construir una comparacion
  directa entre `resolved_sequences` y las primitivas Maestro de
  `trace_primitives.csv`.

## Actualizacion 2026-05-27 - Pipeline Completo Para Bucles Completos

- El pipeline del motor general queda cerrado para la regla resuelta de
  bucles completos:
  `PocketMillingSpec -> ContourParallelTracePlan -> primitive_sequences ->
  resolved_sequences -> trajectory_sequences -> CurveSpec PGMX`.
- `generate_contour_parallel_pocket_trace(...)` ahora llena
  `trajectory_sequences` 3D cuando `resolved_sequences` esta completo. En el
  caso soportado ya no quedan `pending_stages`, y `can_emit_trajectory`
  devuelve `True`.
- `tools.synthesize_pgmx` ahora consulta el motor general antes de caer en los
  helpers historicos de semillas. Si el plan no tiene pendientes, usa sus
  `trajectory_sequences` y serializa las primitivas `Line`/`Arc` resueltas a
  `GeomCompositeCurve`, preservando arcos Maestro en lugar de degradarlos a
  lineas.
- Validacion de ruteo: el test de `Vaciado_027_E006` parchea
  `_build_single_seed_base_loop_xyz_sequences` para fallar si se usa. La
  sintesis sigue pasando, por lo que esa pieza ya fluye por el motor general.
- Validacion efectiva contra Maestro para `Vaciado_027_E006`:
  - longitudes `12 + 20`;
  - XYZ exacto contra el manual;
  - arcos equivalentes contra el manual;
  - conteo de primitivas por trayectoria `((11, 0), (9, 10))`, igual al
    manual.
- La guarda historica de islas se actualizo: los casos no soportados siguen
  lanzando `NotImplementedError`, pero `Vaciado_027` base ya se acepta como
  caso resuelto por motor general.
- Frontera actual despues de cerrar el pipeline:
  - `E006` / bucles completos: cerrado hasta PGMX;
  - `E005` / puente `114`: familia detectada, topologia pendiente;
  - `E002` / parcial `100` y mezcla en una sola `TrajectoryPath`: topologia
    pendiente;
  - `E003/E004` / lobulos parciales densos: topologia pendiente.
- Validacion corrida:
  - `py -3 -m unittest tests.test_pgmx_vaciado` -> `16` tests OK;
  - `py -3 -m tools.pgmx_vaciado.trace_primitives --output-dir S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_trace_primitives_2026_05_27`
    -> `77` casos y `14448` primitivas.

## Actualizacion 2026-05-27 - Paso 1 Cerrado: Puente Y Parcial Simple

- Se cerro el primer bloque del plan de finalizacion del sintetizador:
  `outside-to-inside` con una semilla rectangular balanceada, cubriendo:
  - bucles completos sin puente (`Vaciado_027_E006`);
  - puente simple sin lobulos parciales (`Vaciado_027_E005`, puente `114`);
  - un offset parcial simple (`Vaciado_027_E002`, parcial `100`).
- `trace_engine.py` ahora tiene resolvedores topologicos para:
  - `single_seed_bridge_offsets`: conecta los bucles exteriores, inserta los
    cuatro microarcos de puente y recorre los bucles internos partidos por el
    angulo radial del puente;
  - `single_seed_single_partial_offset`: mezcla el contorno exterior, los
    lobulos parciales izquierdo/derecho y el bucle interno completo en una
    sola `TrajectoryPath`.
- Validacion directa contra Maestro:
  - `Vaciado_027_E005`: `68` puntos, `51` lineas, `16` arcos, XYZ exacto;
  - `Vaciado_027_E002`: `42` puntos, `30` lineas, `11` arcos, XYZ exacto;
  - `Vaciado_027_E006`: sigue cerrado con `12 + 20` puntos.
- La misma regla balanceada tambien cubre `Vaciado_022` base (`42` puntos)
  con XYZ y conteo de primitivas iguales a Maestro.
- Se agrego una guarda importante: las reglas de parcial/puente requieren
  clearances balanceados izquierda/derecha y abajo/arriba. Esto mantiene
  `Vaciado_028` bloqueado, porque la semilla de ruta esta descentrada y su
  topologia no coincide con la regla balanceada.
- Pruebas: `py -3 -m unittest tests.test_pgmx_vaciado` pasa con `17` tests.
- Frontera siguiente: `Vaciado_027_E003/E004`, donde hay multiples lobulos
  parciales densos. Despues de eso se puede declarar cerrada la serie
  `Vaciado_027_E001..E007` sin depender de plantilla para explicar la traza.

## Actualizacion 2026-05-27 - Paso 2 Iniciado: Lobulos Parciales Densos

- Se empezo el siguiente bloque sobre `Vaciado_027_E003/E004`: el motor ya
  extrae correctamente las familias densas, pero las mantiene pendientes hasta
  cerrar el orden exacto de Maestro.
- Oraculos fijados en pruebas:
  - `Vaciado_027_E003`: `18` offsets completos hasta `85.68`, parciales
    `90.44/95.2/99.96/104.72/109.48`, puente `114.24`, `515` puntos,
    `375` lineas y `139` arcos.
  - `Vaciado_027_E004`: `43` offsets completos hasta `86`, parciales
    `88..112` en paso `2`, puente `114`, `1185` puntos, `852` lineas y
    `332` arcos.
- Se probo un port directo del helper historico multiloop como candidato, pero
  no queda conectado al pipeline: reproduce muchas familias de arcos, aunque
  arranca desde el ancla inferior y no desde los bucles exteriores iniciales
  de Maestro; ademas omite conectores densos que aparecen en `E003/E004`.
- Proximo subpaso: construir la gramatica `outside-to-inside` densa desde el
  CSV de primitivas: prefijo de bucles rectangulares exteriores, barrido
  izquierdo de parciales, microconectores/puente, bucles internos completos,
  barrido derecho de parciales y cierre de puente.

## Actualizacion 2026-05-27 - Paso 2 Cerrado: Serie 027 Generativa

- Se cerro la gramatica densa `outside-to-inside` para una semilla rectangular
  balanceada:
  - `single_seed_dense_partial_offsets` cubre los densos sin puente
    (`Vaciado_027_E001` y `E007`);
  - `single_seed_dense_bridge_offsets` cubre los densos con puente
    (`Vaciado_027_E003` y `E004`).
- Los microconectores extra se calculan geometricamente desde el siguiente
  radio posterior al maximo parcial o al puente, conservando la regla general
  `paso_radial = diametro_herramienta * (1 - overlap)`.
- Validacion directa contra Maestro:
  - `E001`: `273` puntos, `200` lineas, `72` arcos, XYZ exacto;
  - `E003`: `515` puntos, `375` lineas, `139` arcos, XYZ exacto;
  - `E004`: `1185` puntos, `852` lineas, `332` arcos, XYZ exacto;
  - `E007`: `273` puntos, `196` lineas, `76` arcos, XYZ exacto.
- La serie `Vaciado_027_E001..E007` ya sintetiza sin hidratar la plantilla del
  manual y con los helpers historicos de semilla parcheados para fallar si se
  usan. Esto cubre:
  - denso sin puente (`E001`, `E007`);
  - parcial simple (`E002`);
  - denso con puente (`E003`, `E004`);
  - puente simple (`E005`);
  - bucles completos separados (`E006`).
- Proxima frontera practica: levantar la regla desde una semilla rectangular
  balanceada unica hacia casos no balanceados o multiples islas
  (`Vaciado_028..031`) sin perder esta suite como oraculo.

## Actualizacion 2026-05-27 - Plan De Cierre Del Sintetizador De Vaciados

La ejecucion del plan sigue incompleta. Este es el registro consolidado del
plan formulado para cerrar el sintetizador generativo de `Vaciado`, lo ya
ejecutado y lo que queda pendiente.

Objetivo general:

- Sintetizar trazas de vaciado `ClosedPocket + BottomAndSideRoughMilling +
  ContourParallel` desde parametros y geometria, sin depender de hidratacion
  de trayectorias Maestro como explicacion de la traza.
- Mantener Maestro como oraculo de validacion para el corpus manual, pero
  separar el contrato del vaciado del algoritmo puntual de recorrido.
- Preservar el modelo para futuras variantes de vaciado: polilineas externas e
  internas, punto inicial, profundidad, rebaba, herramienta, direccion de
  recorrido, conexion entre huecos, direccion de vaciado, sobreposicion,
  helicoidal y multipaso.

Plan completo y estado:

1. Auditar el contrato de parametros y geometria.
   - Estado: ejecutado.
   - Se confirmo en codigo y corpus que el contrato actual conserva contorno
     exterior con punto inicial, profundidad, `AllowanceSide`, diametro de
     herramienta, `RotationDirection`, `StrokeConnectionStrategy`,
     `InsideToOutSide`, `Overlap`, `IsHelicStrategy`, `AllowMultiplePasses`,
     `AxialCuttingDepth` y `AxialFinishCuttingDepth`.
   - Tambien se separaron islas fisicas (`BossGeometryList`) de semillas de
     ruteo (`BossList.GeometryID`), porque Maestro puede rutear contra una
     semilla distinta de la geometria fisica.

2. Revisar nuevamente el corpus manual y documentar el impacto de parametros.
   - Estado: ejecutado.
   - Se revisaron `77` archivos `Vaciado_*.pgmx` en
     `S:\Maestro\Projects\ProdAction\PGMX\manual`; `76` adaptan como
     `PocketMillingSpec` y `Vaciado_035` quedo como caso circular especial.
   - Quedaron reportes en
     `S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_parameter_trace_contract_2026_05_27`.
   - Se reafirmo la regla general
     `paso_radial = diametro_herramienta * (1 - overlap)`.

3. Extraer primitivas de traza Maestro para usar como oraculo geometrico.
   - Estado: ejecutado.
   - Se agrego `tools/pgmx_vaciado/trace_primitives.py`.
   - La corrida sobre el corpus extrajo `14448` primitivas:
     `10648` lineas y `3800` arcos.
   - Los reportes quedaron en
     `S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_trace_primitives_2026_05_27`.

4. Crear el esqueleto general del motor de traza.
   - Estado: ejecutado.
   - Se agrego `tools/pgmx_vaciado/trace_engine.py` con la API
     `generate_contour_parallel_pocket_trace(spec, surface_z=...)`.
   - El motor ya separa contrato de parametros, familias de offsets,
     primitivas abstractas, topologia resuelta, trayectorias 3D y etapas
     pendientes.

5. Implementar primitivas abstractas 2D.
   - Estado: ejecutado.
   - `ContourParallelTracePlan` ya incluye `primitive_sequences`.
   - El motor emite bucles rectangulares exteriores y bucles redondeados para
     semillas rectangulares, preservando arcos como primitivas.

6. Resolver la topologia de bucles completos y emitir PGMX.
   - Estado: ejecutado.
   - El pipeline
     `PocketMillingSpec -> TracePlan -> primitive_sequences ->
     resolved_sequences -> trajectory_sequences -> CurveSpec PGMX` ya cierra
     para bucles completos.
   - `Vaciado_027_E006` valida exacto contra Maestro con `12 + 20` puntos,
     `20` lineas y `10` arcos, sin usar helpers historicos de semilla.

7. Cerrar puente simple y parcial simple para una semilla rectangular
   balanceada.
   - Estado: ejecutado.
   - `Vaciado_027_E005` valida exacto con puente `114`.
   - `Vaciado_027_E002` valida exacto con parcial `100`.
   - La misma regla cubre `Vaciado_022` base.
   - La regla queda intencionalmente guardada por clearances balanceados para
     no aceptar falsos positivos en semillas descentradas como `Vaciado_028`.

8. Cerrar lobulos parciales densos para la serie `Vaciado_027`.
   - Estado: ejecutado.
   - `Vaciado_027_E001`, `E003`, `E004` y `E007` validan exactos.
   - La serie `Vaciado_027_E001..E007` queda generativa para una semilla
     rectangular balanceada, sin hidratacion de plantilla y con tests que
     fallan si se usan helpers historicos.

9. Generar la mayor tanda posible con el sintetizador actual.
   - Estado: ejecutado como checkpoint, no como cierre final.
   - Se generaron en
     `S:\Maestro\Projects\ProdAction\PGMX\generated` los casos que el
     sintetizador actual puede emitir y validar.
   - Resultado: `48` archivos `Vaciado_*_synth.pgmx` validados exactos contra
     Maestro.
   - Dos intentos escritos pero no validados (`Vaciado_022_E002_synth.pgmx` y
     `Vaciado_028_E002_synth.pgmx`) fueron eliminados para no dejar salidas
     invalidas.
   - Quedaron `26` casos no soportados y `1` caso saltado (`Vaciado_035`).

10. Generalizar desde una semilla rectangular balanceada hacia semilla unica
    descentrada.
    - Estado: pendiente.
    - Caso guia recomendado: `Vaciado_028_E002`, porque el motor actual puede
      generar una forma cercana pero no valida la estructura Maestro.
    - Necesidad tecnica: modelar clearances no balanceados, orden de recorrido
      asimetrico y mezcla correcta entre contorno exterior, semilla y parciales.

11. Generalizar hacia multiples islas/semillas.
    - Estado: pendiente.
    - Casos guia: serie `Vaciado_029` y serie `Vaciado_030`.
    - Necesidad tecnica: resolver crecimiento simultaneo de offsets por isla,
      detectar puentes cuando un offset supera medio claro entre islas y usar
      puntos de interseccion de circulos/offsets como geometria de enlace.

12. Cerrar la serie `Vaciado_031`.
    - Estado: parcial.
    - `Vaciado_031_E001..E007` ya se generan exactos en la tanda actual.
    - `Vaciado_031.pgmx` base sigue no soportado y debe estudiarse como caso
      separado antes de declararlo cerrado.

13. Incorporar contornos no polilineales / circulares.
    - Estado: pendiente.
    - Caso guia: `Vaciado_035.pgmx`.
    - Necesidad tecnica: decidir si el contrato acepta curvas/arcos de forma
      nativa o si el adaptador debe convertir contornos curvos a polilineas
      bajo una tolerancia explicita.
    - Observacion actual: el flag helicoidal esta activo en `Vaciado_035`, pero
      la trayectoria observada queda a Z constante; no alcanza para inferir una
      regla helicoidal general.

14. Endurecer validacion de lote y ergonomia de generacion.
    - Estado: pendiente.
    - Agregar un comando reproducible para regenerar todos los vaciados
      soportados, comparar contra Maestro y no dejar archivos invalidos.
    - El comando debe reportar generados exactos, mismatches, no soportados y
      saltados, de modo que la carpeta `generated` sea un checkpoint confiable.

Estado actual del frente:

- Cerrado: generacion pura para vaciados rectangulares sin islas, multipaso
  rectangular, y serie `Vaciado_027_E001..E007` con una semilla rectangular
  balanceada.
- Parcial: `Vaciado_031` porque sus variantes `E001..E007` validan, pero el
  caso base no.
- Pendiente: semillas descentradas (`Vaciado_028`), multiples islas
  (`Vaciado_029`/`Vaciado_030`), contornos circulares (`Vaciado_035`) y un
  comando productivo de generacion/validacion de lote.

## Actualizacion 2026-05-28 - Cierre De Vaciado_028 Descentrado

La familia de semilla unica rectangular descentrada queda cerrada para el caso
guia `Vaciado_028` y para sus variantes `E001..E007`, incluyendo la familia
original con isla desplazada hacia la derecha y la familia sintetica/manual con
isla desplazada hacia la izquierda.

Correccion implementada:

- El motor de traza ya no acepta el espejo geometrico simple como regla Maestro
  para el caso derecho no balanceado.
- Se agrego una maestroizacion especifica del recorrido no balanceado derecho:
  reflexion vertical del caso izquierdo, reanclaje de prefijos completos al
  punto inicial de la polilinea exterior Maestro, y ajuste de los arcos de
  esquina para reproducir la segmentacion top-right/bottom-left observada.
- El caso terminal parcial de `E006` se resuelve con una regla directa para la
  topologia Maestro observada.

Evidencia manual usada:

- `S:\Maestro\Projects\ProdAction\PGMX\manual\Vaciado_028_left_manual.pgmx`.
- `S:\Maestro\Projects\ProdAction\PGMX\generated\Vaciado_028_E001_left_manual.pgmx`
  hasta `Vaciado_028_E007_left_manual.pgmx`.

Salidas regeneradas en `S:\Maestro\Projects\ProdAction\PGMX\generated`:

- `Vaciado_028_left_synth.pgmx`.
- `Vaciado_028_E001_left_synth.pgmx` hasta
  `Vaciado_028_E007_left_synth.pgmx`.

Validacion de geometria efectiva contra Maestro:

- Base: longitud `(52,)`, primitivas `((33, 18),)`.
- `E001`: longitud `(260,)`, primitivas `((185, 74),)`.
- `E002`: longitud `(40,)`, primitivas `((28, 11),)`.
- `E003`: longitud `(525,)`, primitivas `((381, 143),)`.
- `E004`: longitud `(1238,)`, primitivas `((899, 338),)`.
- `E005`: longitud `(63,)`, primitivas `((42, 20),)`.
- `E006`: longitud `(52,)`, primitivas `((33, 18),)`.
- `E007`: longitud `(285,)`, primitivas `((205, 79),)`.

Validacion de repo:

- `py -3 -m unittest tests.test_pgmx_vaciado`: `41` tests, `OK`.
- `git diff --check`: sin errores; solo avisos de normalizacion `LF -> CRLF`
  en `tests/test_pgmx_vaciado.py` y
  `tools/pgmx_vaciado/trace_engine.py`.

Estado actualizado del frente:

- Cerrado: semilla unica rectangular descentrada `Vaciado_028` izquierda y
  derecha, base y `E001..E007`.
- Sigue pendiente: multiples islas (`Vaciado_029`/`Vaciado_030`), contornos
  circulares/no polilineales (`Vaciado_035`), el caso base pendiente de
  `Vaciado_031`, y el comando productivo de regeneracion/validacion de lote.

## Actualizacion 2026-05-29 - Primer Cierre Multi-Isla Vaciado_029

Se habilito la primera regla generativa exacta para multiples islas:
`Vaciado_029` base, `Vaciado_029_E002`, `Vaciado_029_E005` y
`Vaciado_029_E006`.

Alcance cerrado:

- Dos islas rectangulares simetricas.
- `InsideToOutside=True` con conexion `LiftShiftPlunge`.
- Radio completo `40` y primer radio de puente `80` para base/`E006`.
- Radio completo `38` y primer radio de puente `76` para `E005`, con un
  corte de serializacion Maestro adicional en el arco superior derecho.
- Radio completo `50` y primer radio de puente `100` para `E002`, con
  topologia separada: primero puente inferior interno, luego isla derecha,
  isla izquierda y finalmente barrido exterior.
- Puente superior e inferior entre islas con puntos de interseccion:
  `(200, 202.838822)` y `(200, 97.161178)`.
- Conectores hacia los loops completos de isla:
  `(52.5, 208.071891)` y `(237.5, 188.919411)`.

Salidas regeneradas en `S:\Maestro\Projects\ProdAction\PGMX\generated`:

- `Vaciado_029_synth.pgmx`.
- `Vaciado_029_E002_synth.pgmx`.
- `Vaciado_029_E005_synth.pgmx`.
- `Vaciado_029_E006_synth.pgmx`.

Validacion contra Maestro:

- Base y `E006` validan exactos con longitud `(64,)`.
- `E002` valida exacto con longitud `(45,)`.
- `E005` valida exacto con longitud `(65,)` por el corte extra de arco.
- Primitivas base/`E006`: `((39, 24),)` para lineas y arcos.
- Primitivas `E002`: `((25, 19),)` para lineas y arcos.
- Primitivas `E005`: `((39, 25),)` para lineas y arcos.
- `py -3 -m unittest tests.test_pgmx_vaciado`: `47` tests, `OK`.
- `git diff --check`: sin errores; solo avisos de normalizacion `LF -> CRLF`
  en los archivos editados.

Frontera que sigue abierta:

- La serie `Vaciado_029_E001`, `E003` y `E004` sigue pendiente.
- `Vaciado_029_E007` se cierra en la actualizacion siguiente de este mismo
  checkpoint.
- `Vaciado_030` y el caso base multi-isla de `Vaciado_031` siguen como frentes
  separados.

## Actualizacion 2026-05-29 - Cierre Denso Multi-Isla Vaciado_029_E007

Se agrego la regla generativa `two_seed_dense_bridge_offsets` para
`Vaciado_029_E007`.

Alcance cerrado:

- Dos islas rectangulares simetricas `75..125 x 125..175` y
  `275..325 x 125..175`.
- `InsideToOutside=True` con conexion `LiftShiftPlunge`.
- Offsets completos densos `8.86`, `17.72`, `26.58`, `35.44`, `44.3`,
  `53.16` y `62.02`.
- Radio de transicion `70.88`, radio de puente `79.74` y lobulos Maestro
  superiores/inferiores con radios `88.6` y `97.46`.
- Puntos de puente y cortes de serializacion Maestro preservados:
  `(200, 202.082607)`, `(200, 77.830518)`,
  `(187.649661, 237.649661)` y `(193.181818, 68.420855)`.

Salida regenerada en `S:\Maestro\Projects\ProdAction\PGMX\generated`:

- `Vaciado_029_E007_synth.pgmx`.

Validacion contra Maestro:

- Longitud `(357,)`.
- Primitivas `((213, 143),)` para lineas y arcos.
- Secuencia XYZ igual dentro de tolerancia `1e-6`; las diferencias exactas son
  solo representacion flotante de los mismos puntos Maestro.
- Arcos y conteo de primitivas iguales a Maestro.
- `py -3 -m unittest tests.test_pgmx_vaciado`: `49` tests, `OK`.
- `git diff --check`: sin errores; solo avisos de normalizacion `LF -> CRLF`
  en los archivos editados.

Frontera que sigue abierta:

- En `Vaciado_029` quedan pendientes `E001`, `E003` y `E004`.
- `Vaciado_030`, el caso base multi-isla de `Vaciado_031`,
  `Vaciado_035` y el comando productivo de regeneracion/validacion de lote
  siguen como frentes separados.

## Actualizacion 2026-05-29 - Cierre Separado Denso Vaciado_029_E001

Se agrego la regla generativa `two_seed_separate_dense_offsets` para
`Vaciado_029_E001`.

Alcance cerrado:

- Dos islas rectangulares simetricas `75..125 x 125..175` y
  `275..325 x 125..175`.
- `InsideToOutside=True` con conexion `LiftShiftPlunge`.
- Offsets completos densos `9.18`, `18.36`, `27.54`, `36.72`, `45.9` y
  `55.08`.
- Radios parciales `64.26` y `73.44` antes del primer cruce entre islas.
- Primer radio que cruza el claro `82.62`, con lobulos superiores/inferiores
  adicionales `91.8` y `100.98`.
- Puntos caracteristicos preservados:
  `(200, 57.383727)`, `(200, 242.616273)`,
  `(172.727273, 81.971463)` y `(377.062857, 107.02042)`.

Salida regenerada en `S:\Maestro\Projects\ProdAction\PGMX\generated`:

- `Vaciado_029_E001_synth.pgmx`.

Validacion contra Maestro:

- Longitud `(306,)`.
- Primitivas `((179, 126),)` para lineas y arcos.
- Secuencia XYZ igual dentro de tolerancia `1e-6`.
- Arcos y conteo de primitivas iguales a Maestro.
- `py -3 -m unittest tests.test_pgmx_vaciado`: `51` tests, `OK`.
- `git diff --check`: sin errores; solo avisos de normalizacion `LF -> CRLF`
  en los archivos editados.

Frontera que sigue abierta:

- En `Vaciado_029` quedan pendientes `E003` y `E004`.
- `E003` y `E004` comparten una familia densa progresiva con mas radios
  parciales antes/despues del puente que `E001` y `E007`; deben cerrarse como
  siguiente regla, no como publicacion del checkpoint.

## Actualizacion 2026-05-29 - Cierre Progresivo Denso Vaciado_029_E003_E004

Se agrego la regla generativa `two_seed_progressive_dense_offsets` para
`Vaciado_029_E003` y `Vaciado_029_E004`.

Alcance cerrado:

- Dos islas rectangulares simetricas `75..125 x 125..175` y
  `275..325 x 125..175`.
- `InsideToOutside=True` con conexion `LiftShiftPlunge`.
- Familia progresiva densa con radios completos, radios separados bajo el
  claro entre islas, puentes completos hasta el limite vertical y lobulos
  terminales altos.
- `E003`: offsets completos `4.76..61.88`, primer puente en `76.16`,
  puente completo maximo `85.68` y lobulos altos `90.44`, `95.2`, `99.96`.
- `E004`: offsets completos `2..62`, primer puente en `76`, puente completo
  maximo `86` y lobulos altos `88`, `90`, `92`, `94`, `96`, `98`, `100`,
  `102`.
- Puntos caracteristicos preservados:
  `E003` `(200, 188.24181)`, `(200, 58.916707)`,
  `(185.584909, 235.584909)`, `(196.052632, 77.119044)`;
  `E004` `(200, 187.288203)`, `(200, 55.869688)`,
  `(185.811183, 235.811183)`, `(198.295455, 80.013598)`.

Salidas regeneradas en `S:\Maestro\Projects\ProdAction\PGMX\generated`:

- `Vaciado_029_E003_synth.pgmx`.
- `Vaciado_029_E004_synth.pgmx`.

Validacion contra Maestro:

- `E003`: longitud `(653,)`; primitivas `((395, 257),)` para lineas y arcos.
- `E004`: longitud `(1478,)`; primitivas `((904, 573),)` para lineas y arcos.
- Secuencias XYZ iguales dentro de tolerancia `1e-6`.
- Arcos y conteo de primitivas iguales a Maestro.
- `py -3 -m unittest tests.test_pgmx_vaciado`: `55` tests, `OK`.

Frontera que sigue abierta:

- La familia `Vaciado_029` queda cerrada para base y `E001..E007`.
- `Vaciado_030`, el caso base multi-isla de `Vaciado_031`,
  `Vaciado_035` y el comando productivo de regeneracion/validacion de lote
  siguen como frentes separados.

## Actualizacion 2026-05-30 - Cierre Right-Wall Vaciado_030

Se agrego la regla generativa `single_seed_right_wall_inside_out_offsets` para
`Vaciado_030` base y `Vaciado_030_E001..E007`.

Alcance cerrado:

- Base con dos islas fisicas `75..125 x 125..175` y
  `275..325 x 125..175`, mas semilla de ruta resuelta `10748`
  en `325..375 x 125..175`.
- Variantes `E001..E007` con `BossGeometryList` materializado como la semilla
  lateral derecha `325..375 x 125..175`.
- Estrategia `InsideToOutside=True` con conexion `LiftShiftPlunge`.
- Regimen right-wall con radios grandes recortados por la izquierda, radios
  intermedios contra pared derecha, radios estrechos con esquinas derechas y
  la transicion de `E004` en centros `(203,125)` y `(203,175)` con radio `2`.
- La seleccion de trazas del motor usa las semillas de ruta resueltas para no
  desplazar la isla no resuelta del caso base.
- La serializacion productiva conserva `BossGeometryList` fisico separado de
  las referencias de semilla en `BossList`.

Salidas regeneradas en `S:\Maestro\Projects\ProdAction\PGMX\generated`:

- `Vaciado_030_synth.pgmx`.
- `Vaciado_030_E001_synth.pgmx`.
- `Vaciado_030_E002_synth.pgmx`.
- `Vaciado_030_E003_synth.pgmx`.
- `Vaciado_030_E004_synth.pgmx`.
- `Vaciado_030_E005_synth.pgmx`.
- `Vaciado_030_E006_synth.pgmx`.
- `Vaciado_030_E007_synth.pgmx`.

Validacion contra Maestro:

- Base: longitud `(27,)`; primitivas `((20, 6),)`.
- `E001`: longitud `(155,)`; primitivas `((122, 32),)`.
- `E002`: longitud `(18,)`; primitivas `((13, 4),)`.
- `E003`: longitud `(311,)`; primitivas `((248, 62),)`.
- `E004`: longitud `(745,)`; primitivas `((587, 157),)`.
- `E005`: longitud `(27,)`; primitivas `((20, 6),)`.
- `E006`: longitud `(27,)`; primitivas `((20, 6),)`.
- `E007`: longitud `(162,)`; primitivas `((129, 32),)`.
- Secuencias XYZ, arcos y conteos iguales a Maestro para base y variantes.
- Sintesis validada desde `Vaciado_000.pgmx`, con helpers legacy bloqueados.
- `py -3 -m unittest tests.test_pgmx_vaciado`: `57` tests, `OK`.

Frontera que sigue abierta:

- Caso base multi-isla de `Vaciado_031`.
- `Vaciado_035` circular/non-polyline.
- Comando productivo de regeneracion/validacion de lote.

## Actualizacion 2026-06-02 - Reactivacion De Tests De Vaciado

Se retiro la pausa global por variable de entorno
`PRODACTION_ENABLE_VACIADO_TESTS` en las suites de Vaciado.

Alcance:

- `tests.test_pgmx_vaciado_v2` corre por defecto como smoke del contrato V2.
- `tests.test_pgmx_vaciado` corre por defecto como smoke del laboratorio y del
  motor de trazas.
- Los casos dependientes del corpus externo conservan sus guardias locales
  `_external_corpus_available()` para poder saltarse si la evidencia Maestro no
  esta montada.
- La reactivacion de tests no cambia el caracter experimental de
  `pgmx.vaciado_lab`; el punto de integracion productivo objetivo es
  `pgmx.synthesis.milling.pocket`, y el contrato/laboratorio historico debe
  migrar hacia pocket milling.

Validacion local:

- `py -3 -m unittest tests.test_pgmx_vaciado_v2`: `8` tests, `OK`.
- `py -3 -m unittest tests.test_pgmx_vaciado`: `57` tests, `OK`.
