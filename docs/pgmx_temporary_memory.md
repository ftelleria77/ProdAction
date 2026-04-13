# Memoria Temporal PGMX

Este archivo registra hallazgos temporales durante el analisis incremental de
una pieza manual en Maestro para luego ampliar o corregir:

- `tools/synthesize_pgmx.py`
- `docs/synthesize_pgmx_help.md`
- `docs/pgmx_geometry_registry.md`

## Caso En Curso

- Pieza base: `archive/maestro_examples/Pieza.pgmx`
- Baseline usado: `archive/maestro_baselines/Pieza.xml`
- Dimensiones: `300 x 300 x 18`
- Origen: `0,0,0`

## Objetivo

Reconstruir paso a paso:

1. taxonomia de la geometria cerrada creada manualmente
2. serializacion del escuadrado/fresado asociado
3. reglas de correccion de herramienta
4. reglas de `Approach` y `Retract`

## Rondas

### Ronda 1 - Pieza base sin mecanizados

- Estado: completado
- Archivo: `archive/maestro_examples/Pieza.pgmx`
- Observado:
  - pieza sintetizada sin mecanizados
  - origen `0,0,0`
  - `execution_fields = HG`
- Pendiente:
  - el usuario agregara una geometria cerrada con inicio en el medio

### Ronda 2 - Geometria cerrada manual

- Estado: completado
- Archivo esperado: `archive/maestro_examples/Pieza.pgmx`
- A relevar:
  - clasificacion segun `read_pgmx_geometries(...)`
  - `classification_key`
  - `start_mode`
  - `winding`
  - geometria serializada
  - coincidencia o discrepancia con `docs/pgmx_geometry_registry.md`
- Memoria de hallazgos:
  - `read_pgmx_geometries(...)` devuelve una sola geometria.
  - `classification_key = ClosedPolylineMidEdgeStart_CounterClockwise`
  - `geometry_type = GeomCompositeCurve`
  - `family = ClosedPolylineMidEdgeStart`
  - `is_closed = True`
  - `start_mode = MidEdge`
  - `winding = CounterClockwise`
  - `has_arcs = False`
  - `primitive_count = 5`
  - `bounding_box = (0, 0, 300, 300)`
  - La serializacion observada queda compuesta por 5 segmentos:
    - tramo 1: `(150,0) -> (300,0)`
    - tramo 2: `(300,0) -> (300,300)`
    - tramo 3: `(300,300) -> (0,300)`
    - tramo 4: `(0,300) -> (0,0)`
    - tramo 5: `(0,0) -> (150,0)`
  - El arranque cae en el medio del lado inferior y la salida del ultimo tramo es
    tangente con la entrada del primero, en linea con `start_mode = MidEdge`.
  - No se observan discrepancias con la taxonomia actual.

### Ronda 3 - Escuadrado con E001

- Estado: completado
- Archivo esperado: `archive/maestro_examples/Pieza.pgmx`
- A relevar:
  - feature
  - operation
  - `ToolpathList`
  - `TrajectoryPath`
  - profundidad
  - compensacion
  - concordancia con helpers internos y docs
- Memoria de hallazgos:
  - La geometria base sigue siendo `ClosedPolylineMidEdgeStart_CounterClockwise`.
  - Se observa `1` feature, `1` operation y `1` workstep.
  - Feature:
    - `Name = Fresado`
    - `i:type = a:GeneralProfileFeature`
    - `GeometryID = 1932`
    - `SideOfFeature = Center`
    - `SweptShape.Width = 18.36`
    - `BottomCondition = a:GeneralMillingBottom`
    - `Depth.StartDepth = 0`
    - `Depth.EndDepth = 0`
  - Operation:
    - herramienta `E001`
    - `tool_id = 1900`
    - `Approach.IsEnabled = false`
    - `ApproachType = Line`
    - `ApproachMode = Down`
    - `Retract.IsEnabled = false`
    - `RetractType = Line`
    - `RetractMode = Up`
  - Toolpaths:
    - `TrajectoryPath` usa `GeomCompositeCurve` con `5` segmentos y coincide con el
      contorno nominal en cota `Z = 18`, consistente con correccion `Center`.
    - `Approach` es una linea vertical de `(150, 0, 38)` a `(150, 0, 18)`.
    - `Lift` es una linea vertical de `(150, 0, 18)` a `(150, 0, 38)`.
  - Coincidencias con documentacion actual:
    - `SideOfFeature = Center` coincide con la regla documentada para que la
      trayectoria permanezca sobre la geometria nominal.
    - `Approach.IsEnabled = false` y `Retract.IsEnabled = false` coinciden con la
      regla documentada de toolpath vertical de entrada y salida.
  - Discrepancia encontrada:
    - Maestro permite guardar un fresado no pasante con profundidad `0`:
      `BottomCondition = GeneralMillingBottom`, `Depth.StartDepth = 0`,
      `Depth.EndDepth = 0`.
    - La documentacion actual no describe este caso.
    - El codigo actual tampoco lo acepta al hidratar una plantilla:
      `_extract_polyline_milling_template(...)` falla porque
      `build_milling_depth_spec(is_through=False, target_depth=0)` dispara
      `ValueError("La profundidad no pasante debe ser mayor que cero.")`.

### Ronda 4 - Correccion + Approach + Retract

- Estado: completado
- Archivo esperado: `archive/maestro_examples/Pieza.pgmx`
- A relevar:
  - `SideOfFeature`
  - `Approach`
  - `Retract`
  - punto y tangente de entrada/salida
  - curvas verticales, lineales o en arco
  - concordancia con `_build_generated_approach_curve*`
  - concordancia con `_build_generated_lift_curve*`
- Memoria de hallazgos:
  - Se mantiene `1` feature, `1` operation y `1` workstep.
  - La feature ahora queda como fresado pasante:
    - `SideOfFeature = Right`
    - `BottomCondition = a:ThroughMillingBottom`
    - `Depth.StartDepth = 18`
    - `Depth.EndDepth = 18`
    - `OvercutLength = 1`
  - Las expresiones de profundidad agregadas por Maestro enlazan:
    - `Depth.StartDepth -> dz1`
    - `Depth.EndDepth -> dz1`
  - Esto coincide con la regla documentada para pasante + `Extra`.
  - Compensacion observada:
    - sobre un contorno `ClosedPolylineMidEdgeStart_CounterClockwise`
    - con `SideOfFeature = Right`
    - la trayectoria cae al exterior del contorno, como describe la documentacion
    - `TrajectoryPath` queda como `GeomCompositeCurve` con `9` miembros:
      - `5` tramos lineales
      - `4` arcos tangentes de cuarto de circunferencia en los vertices convexos
  - `Approach` observado:
    - habilitado
    - `ApproachType = Arc`
    - `ApproachMode = Quote`
    - `RadiusMultiplier = 2`
    - `Speed = -1`
    - `ApproachArcSide = Automatic`
    - curva observada: `GeomCompositeCurve` de `2` miembros
      - linea vertical
      - arco `270 -> 360`
    - coincide con la regla documentada para antihorario + `SideOfFeature = Right`
  - `Retract` observado:
    - habilitado
    - `RetractType = Arc`
    - `RetractMode = Quote`
    - `RadiusMultiplier = 2`
    - `Speed = -1`
    - `RetractArcSide = Automatic`
    - curva observada: `GeomCompositeCurve` de `2` miembros
      - arco `0 -> 90`
      - linea vertical
    - coincide con la regla documentada para salida `Arc + Quote`
  - Concordancia con codigo:
    - `_extract_polyline_milling_template(...)` ahora hidrata correctamente este
      archivo manual.
    - El template extraido devuelve:
      - `MillingDepthSpec(is_through=True, extra_depth=1.0)`
      - `ApproachSpec(is_enabled=True, approach_type='Arc', mode='Quote', radius_multiplier=2.0, speed=-1.0, arc_side='Automatic')`
      - `RetractSpec(is_enabled=True, retract_type='Arc', mode='Quote', radius_multiplier=2.0, speed=-1.0, arc_side='Automatic', overlap=0.0)`
    - `_hydrate_polyline_milling_spec(...)` acepta este caso y reutiliza la
      serializacion observada como plantilla exacta.
  - No se observaron discrepancias nuevas en esta ronda.

### Ronda 5 - Integracion en codigo y documentacion

- Estado: completado
- Cambios aplicados:
  - `tools/synthesize_pgmx.py` ahora admite `target_depth = 0` en
    `build_milling_depth_spec(...)` para reflejar el estado manual neutro que
    Maestro guarda en fresados no pasantes recien creados.
  - `docs/synthesize_pgmx_help.md` ahora documenta explicitamente:
    - el caso `GeneralMillingBottom + StartDepth/EndDepth = 0`
    - el caso manual validado de escuadrado antihorario con `E001`
  - `README.md` ahora resume este caso manual como patron validado.
- Verificacion:
  - `build_milling_depth_spec(is_through=False, target_depth=0)` devuelve
    `MillingDepthSpec(is_through=False, target_depth=0.0, extra_depth=0.0)`.
  - `_extract_depth_spec_from_template(...)` ya no falla cuando encuentra un
    feature manual con profundidad `0`.
  - `_extract_polyline_milling_template(...)` sigue hidratando correctamente el
    caso pasante + `Extra = 1` con `Approach Arc + Quote` y `Retract Arc + Quote`.
  - `py -3 -m compileall main.py app core tools` compila sin errores.

### Ronda 6 - Variantes validas de escuadrado antihorario

- Estado: completado
- Archivos relevados:
  - `archive/maestro_examples/Pieza_Escuadrado_Antihorario_BordeDerecho.pgmx`
  - `archive/maestro_examples/Pieza_Escuadrado_Antihorario_BordeSuperior.pgmx`
  - `archive/maestro_examples/Pieza_Escuadrado_Antihorario_BordeIzquierdo.pgmx`
- Hallazgos comunes:
  - las tres piezas vuelven a clasificar como
    `ClosedPolylineMidEdgeStart_CounterClockwise`
  - en los tres casos el mecanizado queda como:
    - herramienta `E001` / `tool_id = 1900` / `tool_width = 18.36`
    - `SideOfFeature = Right`
    - pasante con `Extra = 1`
    - `Approach = Arc + Quote`, `RadiusMultiplier = 2`,
      `ArcSide = Automatic`
    - `Retract = Arc + Quote`, `RadiusMultiplier = 2`,
      `ArcSide = Automatic`
  - `TrajectoryPath` vuelve a salir como `GeomCompositeCurve` con:
    - `5` tramos lineales
    - `4` arcos tangentes de cuarto de circunferencia
  - `_extract_polyline_milling_template(...)` hidrata correctamente los tres
    archivos, sin discrepancias nuevas de lectura
- Diferencia relevante:
  - lo que cambia no es la familia de geometria ni la configuracion del fresado,
    sino el borde donde cae el arranque en medio de lado:
    - `BordeDerecho`: arranque en el medio del lado derecho
    - `BordeSuperior`: arranque en el medio del lado superior
    - `BordeIzquierdo`: arranque en el medio del lado izquierdo
  - `TrajectoryPath`, `Approach` y `Lift` rotan rigidamente con esa eleccion
    del borde de arranque
  - por lo tanto, el patron de escuadrado antihorario valido no depende de una
    cara fija de la pieza; depende de la tangente de entrada/salida del
    toolpath efectivo
- Impacto sobre documentacion:
  - la descripcion actual del caso `Escuadrado antihorario con E001` quedo
    demasiado atada al caso base con arranque en borde inferior
  - las referencias a cuadrantes fijos como
    `Approach 270 -> 360` y `Lift 0 -> 90` no son universales para todo
    `ClosedPolylineMidEdgeStart_CounterClockwise + SideOfFeature = Right`
  - esos cuadrantes rotan con la tangente local del toolpath
- Impacto sobre codigo:
  - el codigo ya esta modelado de forma mas general que la documentacion actual:
    - `_profile_entry_exit_context(...)`
    - `_build_quote_arc_entry_curve(...)`
    - `_build_generated_lift_curve(...)`
  - estas funciones resuelven `Approach` y `Retract` desde la tangente efectiva
    del toolpath, no desde un borde absoluto de la pieza

### Ronda 7 - Mismo escuadrado con origen `(5, 5, 25)`

- Estado: completado
- Archivos relevados:
  - `archive/maestro_examples/Pieza_Escuadrado_Antihorario_BordeInferior.pgmx`
  - `archive/maestro_examples/Pieza_Escuadrado_Antihorario_BordeDerecho.pgmx`
  - `archive/maestro_examples/Pieza_Escuadrado_Antihorario_BordeSuperior.pgmx`
  - `archive/maestro_examples/Pieza_Escuadrado_Antihorario_BordeIzquierdo.pgmx`
- Hallazgo principal:
  - el cambio de origen a `(5, 5, 25)` no modifica la geometria nominal ni la
    trayectoria del fresado
  - `read_pgmx_state(...)` devuelve correctamente:
    - `origin_x = 5`
    - `origin_y = 5`
    - `origin_z = 25`
  - pero las curvas manuales siguen expresadas en coordenadas locales de pieza
    exactamente igual que en el caso con origen `0, 0, 0`
- Observacion de serializacion:
  - la geometria base sigue en el mismo marco local:
    - borde inferior: arranque `(150, 0, 0)`
    - borde derecho: arranque `(300, 150, 0)`
    - borde superior: arranque `(150, 300, 0)`
    - borde izquierdo: arranque `(0, 150, 0)`
  - `TrajectoryPath`, `Approach` y `Lift` conservan exactamente las mismas
    coordenadas observadas en el caso con origen `0, 0, 0`
  - en particular:
    - `cut_z` sigue quedando en `-1` para pasante + `Extra = 1`
    - `clearance_z` sigue quedando en `38` con `security_plane = 20`
  - el origen nuevo solo aparece en
    `WorkpieceSetup/Placement = (5, 5, 25)`
- Lectura de codigo que explica el comportamiento:
  - `read_pgmx_state(...)` toma el origen desde
    `WorkpieceSetup/Placement`
  - `_apply_piece_state(...)` escribe `origin_x/origin_y/origin_z` solo en ese
    `WorkpieceSetup/Placement`
  - las curvas de geometria y toolpath se construyen en coordenadas locales de
    pieza, sin sumar el origen global
  - `_toolpath_cut_z(...)` depende solo de `depth_spec`
  - `clearance_z` se calcula como `state.depth + security_plane`
- Conclusion operativa:
  - el origen de pieza en Maestro funciona como posicionamiento del setup, no
    como traslacion embebida de la geometria ni del toolpath dentro del `.pgmx`
  - por eso la futura spec publica no deberia mezclar:
    - orientacion/borde de arranque del contorno
    - origen global de setup

### Ronda 8 - Correccion de documentacion

- Estado: completado
- Archivos actualizados:
  - `docs/synthesize_pgmx_help.md`
  - `README.md`
- Cambios volcados:
  - `read_pgmx_state(...)` ahora aclara que `origin_x/origin_y/origin_z`
    corresponde a `WorkpieceSetup/Placement`
  - `build_synthesis_request(...)` ahora aclara que cambiar el origen no
    traslada automaticamente `Geometries`, `TrajectoryPath`, `Approach` ni
    `Lift`
  - el caso `Escuadrado antihorario con E001` ahora explicita:
    - las 4 orientaciones validas segun el borde del `MidEdgeStart`
    - que la familia sigue siendo
      `ClosedPolylineMidEdgeStart_CounterClockwise`
    - que `Approach` y `Lift` rotan con la tangente local del toolpath
    - que el origen global solo mueve `WorkpieceSetup/Placement`
  - la seccion general `Arc + Quote` ahora evita cuadrantes globales fijos y
    queda expresada en funcion de la tangente local del toolpath efectivo

### Ronda 9 - Escuadrado horario en las 4 orientaciones

- Estado: completado
- Archivos relevados:
  - `archive/maestro_examples/Pieza_Escuadrado_Horario_BordeInferior.pgmx`
  - `archive/maestro_examples/Pieza_Escuadrado_Horario_BordeDerecho.pgmx`
  - `archive/maestro_examples/Pieza_Escuadrado_Horario_BordeSuperior.pgmx`
  - `archive/maestro_examples/Pieza_Escuadrado_Horario_BordeIzquierdo.pgmx`
- Hallazgos comunes:
  - las cuatro piezas clasifican como
    `ClosedPolylineMidEdgeStart_Clockwise`
  - el origen sigue en `(5, 5, 25)` y no modifica las curvas internas
  - en los cuatro casos el mecanizado queda como:
    - herramienta `E001` / `tool_id = 1900` / `tool_width = 18.36`
    - `SideOfFeature = Left`
    - pasante con `Extra = 1`
    - `Approach = Arc + Quote`, `RadiusMultiplier = 2`,
      `ArcSide = Automatic`
    - `Retract = Arc + Quote`, `RadiusMultiplier = 2`,
      `ArcSide = Automatic`
  - `TrajectoryPath` vuelve a salir como `GeomCompositeCurve` con:
    - `5` tramos lineales
    - `4` arcos tangentes de cuarto de circunferencia
  - `cut_z` sigue en `-1`
  - `clearance_z` sigue en `38`
- Regla geometrica/funcional:
  - este caso es la version simetrica del escuadrado antihorario validado antes
  - la combinacion equivalente para compensacion exterior queda:
    - antihorario -> `SideOfFeature = Right`
    - horario -> `SideOfFeature = Left`
  - por eso el contorno compensado queda sobre la misma envolvente exterior,
    pero recorrido en sentido inverso
- Variantes por borde de arranque:
  - `BordeInferior`: arranque `(150, 0, 0)` y primer tramo hacia la izquierda
  - `BordeDerecho`: arranque `(300, 150, 0)` y primer tramo hacia abajo
  - `BordeSuperior`: arranque `(150, 300, 0)` y primer tramo hacia la derecha
  - `BordeIzquierdo`: arranque `(0, 150, 0)` y primer tramo hacia arriba
  - igual que en antihorario, lo que rota es la tangente local de
    entrada/salida
- `Approach` y `Lift` observados:
  - siguen el mismo patron local `linea vertical + arco` / `arco + linea vertical`
  - vuelven a aparecer dos serializaciones equivalentes segun la orientacion
    local:
    - `Approach 90 -> 180` y `Lift 180 -> 270`
    - `Approach 270 -> 360` y `Lift 0 -> 90`
  - no dependen de una cara global fija de la pieza
- Concordancia con codigo/docs:
  - coincide con la taxonomia de
    `ClosedPolylineMidEdgeStart_Clockwise`
  - coincide con la regla general ya documentada para resolver
    `Approach`/`Retract` desde la tangente local del toolpath efectivo
  - `_extract_polyline_milling_template(...)` hidrata correctamente los cuatro
    archivos sin discrepancias nuevas
- Impacto para la futura spec:
  - la abstraccion publica no deberia modelar solo
    `CounterClockwise + Right`
  - conviene expresar el escuadrado exterior como una combinacion coherente de:
    - winding del contorno
    - lado efectivo de compensacion
    - borde/orientacion del `MidEdgeStart`

### Ronda 10 - Implementacion de `SquaringMillingSpec`

- Estado: completado
- Cambios aplicados en codigo:
  - se agrego la spec publica `SquaringMillingSpec`
  - se agrego el builder `build_squaring_milling_spec(...)`
  - `build_synthesis_request(...)`, `synthesize_request(...)` y
    `synthesize_pgmx(...)` ya aceptan `squaring_millings`
  - la geometria nominal del escuadrado se sintetiza desde:
    - `length`
    - `width`
    - `winding`
    - `start_edge`
  - la compensacion exterior se deriva automaticamente como:
    - `CounterClockwise -> Right`
    - `Clockwise -> Left`
- Defaults publicos volcados:
  - herramienta `E001` / `tool_id = 1900` / `tool_width = 18.36`
  - pasante con `Extra = 1`
  - `Approach = Arc + Quote`, `RadiusMultiplier = 2`, `ArcSide = Automatic`
  - `Retract = Arc + Quote`, `RadiusMultiplier = 2`, `ArcSide = Automatic`
- Verificacion:
  - `py -3 -m compileall tools/synthesize_pgmx.py` compila sin errores
  - se sintetizaron las 8 variantes manuales relevantes:
    - 4 bordes `MidEdgeStart`
    - 2 windings
  - la verificacion geometrica/funcional dio coincidencia en:
    - estado de pieza y origen
    - clasificacion geometrica
    - lado efectivo de compensacion
    - profundidad
    - configuracion de `Approach` y `Retract`
    - geometria efectiva de `Geometry`, `TrajectoryPath`, `Approach` y `Lift`
- Salvedad tecnica importante:
  - la spec publica nueva reproduce la geometria y el mecanizado efectivo de los
    casos manuales, pero no necesariamente la serializacion byte a byte de todas
    las curvas
  - en algunas variantes:
    - cambian `member_keys` internos
    - cambian parametrizaciones equivalentes de algunas lineas/arcos
    - cambia la base `u/v` de algunos arcos manteniendo el mismo arco efectivo
  - esto no altera la geometria relevada ni las reglas funcionales validadas

## Discrepancias Acumuladas

- Resuelta: Maestro guarda un estado manual valido de fresado no pasante con
  profundidad `0`, y ahora ese caso ya esta cubierto por
  `docs/synthesize_pgmx_help.md` y por la validacion de
  `build_milling_depth_spec(...)`.
- No se detectaron discrepancias nuevas en el caso manual de escuadrado
  antihorario con `E001`.
- Resuelta: la documentacion del caso `Escuadrado antihorario con E001` ya no
  usa cuadrantes absolutos fijos; ahora lo expresa desde la tangente local del
  toolpath efectivo y deja asentadas las 4 orientaciones validadas.
- Resuelta: la documentacion ya explicita que `origin_x/origin_y/origin_z`
  modifica `WorkpieceSetup/Placement`, pero no traslada las curvas internas del
  `.pgmx`.
- No se detectaron discrepancias nuevas en el caso horario; el comportamiento
  observado encaja con la generalizacion por tangente local y con la taxonomia
  geometrica ya existente.
- Resuelta: el escuadrado exterior ya no depende solo de plantillas manuales;
  ahora existe una spec publica dedicada.
- Abierta pero acotada: la nueva spec publica no garantiza serializacion XML
  byte a byte identica a todos los ejemplos manuales, aunque si reproduce la
  geometria y el mecanizado efectivo observados.

## Acciones Pendientes Para Codigo/Docs

- si esa spec publica abstrae un escuadrado por alto nivel, debera modelar
  tambien el borde de arranque o una orientacion equivalente; los casos manuales
  muestran cuatro serializaciones validas del mismo contorno antihorario segun
  donde cae el `MidEdgeStart`
- esa spec tambien debera modelar la combinacion entre winding del contorno y
  lado efectivo de compensacion exterior:
  - `CounterClockwise + Right`
  - `Clockwise + Left`
- si mas adelante hace falta clonar exactamente una serializacion manual
  determinada, estudiar una capa opcional de hidratacion exacta para
  `SquaringMillingSpec`
- si aparecen variantes manuales adicionales, ampliar el caso documentado con
  mas combinaciones de herramienta, correccion y estrategias de entrada/salida
