# PGMX Vaciado

Ultima actualizacion: 2026-05-15

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

## Huecos Del Lector Actual

- `tools.pgmx_snapshot.py` ya representa `b:ContourParallel` como
  `ContourParallelMillingStrategySpec`.
- Todavia falta representar `ClosedPocket` como spec de sintesis estable y
  serializar `BottomAndSideRoughMilling`. En esta etapa la estrategia se
  soporta solo para lectura.
- Ya hay ejemplos manuales para confirmar los valores XML de `En la pieza`,
  `Desde afuera hacia adentro`, helicoidal y multipaso.
- Falta incorporar un spec estable de `Vaciado` que agrupe feature,
  operacion, estrategia, allowances y toolpaths.

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
- El soporte es de lectura/catalogacion; la sintesis productiva de
  `Vaciado/ClosedPocket` todavia debe fallar explicitamente.
- El corpus manual observado llega hasta `manual/Vaciado_019.pgmx`.
- El catalogo externo vigente esta en
  `S:\Maestro\Projects\ProdAction\PGMX\_analysis`.
- La carpeta `tools/pgmx_vaciado/` conserva la memoria y el scanner del
  laboratorio.

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

1. Ampliar `tools.pgmx_snapshot.py` para exponer una lectura mas completa de
   `ClosedPocket` y `BottomAndSideRoughMilling`.
2. Ampliar `tools.pgmx_adapters.py` con un adaptador semantico de `Vaciado`
   basado en el snapshot.
3. Agregar en `tools.synthesize_pgmx.py` un spec publico de `Vaciado`, todavia
   sin serializacion productiva.
4. Mantener `tools.pgmx_vaciado` como laboratorio reproducible hasta que las
   reglas pasen a modulos estables.

## Plan De Trabajo

1. Crear ejemplos manuales minimos en Maestro dentro de `manual/`.
2. Ejecutar `py -3 -m tools.pgmx_vaciado.scan_samples`.
3. Comparar snapshots entre ejemplos que cambien una sola variable.
4. Identificar el modelo minimo de datos para representar `Vaciado`.
5. Probar generacion automatica en `generated/`.
6. Migrar soporte de lectura/adaptacion/dibujo/sintesis a los modulos
   existentes.
7. Recien despues estudiar la traduccion ISO del nuevo mecanizado.
