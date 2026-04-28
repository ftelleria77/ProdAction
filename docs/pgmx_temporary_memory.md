# Memoria Temporal PGMX

Este archivo registra hallazgos temporales durante el analisis incremental de
una pieza manual en Maestro para luego ampliar o corregir:

- `tools/synthesize_pgmx.py`
- `docs/synthesize_pgmx_help.md`
- `docs/pgmx_geometry_registry.md`

## Caso En Curso

- Pieza base: `archive/maestro_examples/Pieza.pgmx`
- Baseline usado: `tools/maestro_baselines/Pieza.xml`
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

### Ronda 11 - Geometrias `GeomCartesianPoint` por cara

- Estado: completado
- Archivos relevados:
  - `archive/maestro_examples/Pieza_PuntoCentral_CaraSuperior.pgmx`
  - `archive/maestro_examples/Pieza_PuntoCentral_CaraDelantera.pgmx`
  - `archive/maestro_examples/Pieza_PuntoCentral_CaraDerecha.pgmx`
  - `archive/maestro_examples/Pieza_PuntoCentral_CaraTrasera.pgmx`
  - `archive/maestro_examples/Pieza_PuntoCentral_CaraIzquierda.pgmx`
- Hallazgos comunes:
  - los 5 archivos contienen exactamente `1` geometria
  - esa geometria es `GeomCartesianPoint`
  - `read_pgmx_geometries(...)` ya los clasifica como `Point`
  - no hay `Features`
  - no hay `Operations`
  - no hay mecanizado asociado: son solo puntos geometricos de referencia
- Coordenadas observadas:
  - `CaraSuperior`:
    - plano `Top`
    - dimensiones del plano `300 x 300`
    - punto local `(150, 150, 0)`
  - `CaraDelantera`:
    - plano `Front`
    - dimensiones del plano `300 x 18`
    - punto local `(150, 9, 0)`
  - `CaraDerecha`:
    - plano `Right`
    - dimensiones del plano `300 x 18`
    - punto local `(150, 9, 0)`
  - `CaraTrasera`:
    - plano `Back`
    - dimensiones del plano `300 x 18`
    - punto local `(150, 9, 0)`
  - `CaraIzquierda`:
    - plano `Left`
    - dimensiones del plano `300 x 18`
    - punto local `(150, 9, 0)`
- Regla importante para futura spec:
  - en las 4 caras laterales el punto local coincide numericamente
  - la cara real no sale de `(x, y, z)` solamente; sale de la combinacion:
    - `plane_id` / `plane_name`
    - coordenadas locales dentro de ese plano
- Impacto sobre codigo:
  - `tools/synthesize_pgmx.py` ya inventaria este caso:
    - `build_point_geometry_profile(...)`
    - lectura de `GeomCartesianPoint` en `read_pgmx_geometries(...)`
  - aun no existe una ruta publica de sintesis que escriba `GeomCartesianPoint`
    dentro de un `.pgmx` de salida
- Impacto para futura abstraccion:
  - si se crea una spec publica de punto, debera modelar al menos:
    - `plane_name`
    - `point_x`
    - `point_y`
    - `point_z`
  - no conviene modelar la cara solo como coordenadas 3D globales; Maestro lo
    serializa como geometria local a un plano

### Ronda 12 - Taladros `RoundHole` sobre `GeomCartesianPoint`

- Estado: completado
- Archivos relevados:
  - `archive/maestro_examples/Pieza_PuntoCentral_CaraSuperior_D8_P15.pgmx`
  - `archive/maestro_examples/Pieza_PuntoCentral_CaraDelantera_D8_P28.pgmx`
  - `archive/maestro_examples/Pieza_PuntoCentral_CaraDerecha_D8_P28.pgmx`
  - `archive/maestro_examples/Pieza_PuntoCentral_CaraTrasera_D8_P28.pgmx`
  - `archive/maestro_examples/Pieza_PuntoCentral_CaraIzquierda_D8_P28.pgmx`
- Hallazgos comunes:
  - cada archivo contiene:
    - `1` geometria `GeomCartesianPoint`
    - `1` feature `a:RoundHole`
    - `1` operation `a:DrillingOperation`
    - `1` workstep en `MainWorkplan`
  - la feature referencia el punto via `GeometryID`
  - la feature referencia la operacion via `OperationIDs`
  - el workstep referencia la misma `OperationID`
  - por lo tanto, el centro del taladro no se modela como circulo ni como
    contorno: se modela como un punto geometrico
- Geometria / cara / nombre:
  - `CaraSuperior_D8_P15`:
    - plano `Top`
    - punto `(150, 150, 0)`
    - `Diameter = 8`
    - `Depth.StartDepth = 15`
    - `Depth.EndDepth = 15`
  - `CaraDelantera_D8_P28`:
    - plano `Front`
    - punto `(150, 9, 0)`
    - `Diameter = 8`
    - `Depth.StartDepth = 28`
    - `Depth.EndDepth = 28`
  - `CaraDerecha_D8_P28`:
    - plano `Right`
    - punto `(150, 9, 0)`
    - `Diameter = 8`
    - `Depth.StartDepth = 28`
    - `Depth.EndDepth = 28`
  - `CaraTrasera_D8_P28`:
    - plano `Back`
    - punto `(150, 9, 0)`
    - `Diameter = 8`
    - `Depth.StartDepth = 28`
    - `Depth.EndDepth = 28`
  - `CaraIzquierda_D8_P28`:
    - plano `Left`
    - punto `(150, 9, 0)`
    - `Diameter = 8`
    - `Depth.StartDepth = 28`
    - `Depth.EndDepth = 28`
- Parametros observados de la feature:
  - `i:type = a:RoundHole`
  - `BottomCondition = a:FlatHoleBottom`
  - `Diameter` vive en la feature
  - `Depth` vive en la feature
- Parametros observados de la operacion:
  - `i:type = a:DrillingOperation`
  - `ApproachSecurityPlane = 20`
  - `RetractSecurityPlane = 20`
  - `StartPoint = (0, 0, 0)`
  - `Technology = MillingTechnology` con:
    - `Feedrate = 0`
    - `CutSpeed = 0`
    - `Spindle = 0`
  - `ToolKey` queda vacio:
    - `ID = 0`
    - `Name = ""`
- Regla importante para futura spec:
  - el centro de perforacion efectivo no sale de `Operation/StartPoint`
  - el punto objetivo sale del `GeometryID` de la feature `RoundHole`
  - `StartPoint = (0,0,0)` parece actuar como placeholder y no como ubicacion
    real del taladro
- Impacto para futura abstraccion publica:
  - una futura spec de taladro debera modelar al menos:
    - `plane_name`
    - `center_x`
    - `center_y`
    - `diameter`
    - `depth`
    - `bottom_condition`
    - `approach_security_plane`
    - `retract_security_plane`
    - `tool_id` / `tool_name` opcionales
  - conviene separar:
    - la geometria puntual (`GeomCartesianPoint`)
    - la feature logica (`RoundHole`)
    - la operacion (`DrillingOperation`)
- Observacion abierta:
  - no esta claro aun si Maestro permite dejar `ToolKey` vacio como estado valido
    definitivo o si luego resuelve la herramienta en otra etapa del flujo
  - antes de exponer una spec publica de taladro conviene relevar al menos un
    caso manual equivalente con herramienta explicita

### Ronda 13 - Asignacion de herramienta unica en taladros laterales

- Estado: completado
- Archivos relevados:
  - `archive/maestro_examples/Pieza_PuntoCentral_CaraDelantera_D8_P28_058.pgmx`
  - `archive/maestro_examples/Pieza_PuntoCentral_CaraTrasera_D8_P28_059.pgmx`
  - `archive/maestro_examples/Pieza_PuntoCentral_CaraDerecha_D8_P28_060.pgmx`
  - `archive/maestro_examples/Pieza_PuntoCentral_CaraIzquierda_D8_P28_061.pgmx`
- Comparacion relevante:
  - cada uno se comparo contra su version anterior sin herramienta explicita:
    - `CaraDelantera_D8_P28`
    - `CaraTrasera_D8_P28`
    - `CaraDerecha_D8_P28`
    - `CaraIzquierda_D8_P28`
  - en los 4 casos, el unico cambio observado en el XML es `Operation/ToolKey`
  - no cambian:
    - `GeomCartesianPoint`
    - `RoundHole`
    - `Diameter`
    - `Depth`
    - `BottomCondition`
    - `ApproachSecurityPlane`
    - `RetractSecurityPlane`
    - `StartPoint`
    - `Technology`
    - `Workstep`
- Regla observada:
  - seleccionar la herramienta lateral en Maestro no recompone el taladro
  - solo reemplaza `ToolKey` desde:
    - `ID = 0`
    - `ObjectType = System.Object`
    - `Name = ""`
  - hacia una referencia explicita a `ScmGroup.XCam.ToolDataModel.Tool.CuttingTool`
- Mapeo cara -> herramienta observada:
  - `Front`:
    - `ToolKey.ID = 1895`
    - `ToolKey.Name = 058`
  - `Back`:
    - `ToolKey.ID = 1896`
    - `ToolKey.Name = 059`
  - `Right`:
    - `ToolKey.ID = 1897`
    - `ToolKey.Name = 060`
  - `Left`:
    - `ToolKey.ID = 1898`
    - `ToolKey.Name = 061`
- Concordancia con `tools/tool_catalog.csv`:
  - `1895 / 058` -> `Broca Plana Cara Delantera Ø8mm`
  - `1896 / 059` -> `Broca Plana Cara Trasera Ø8mm`
  - `1897 / 060` -> `Broca Plana Cara Derecha Ø8mm`
  - `1898 / 061` -> `Broca Plana Cara Izquierda Ø8mm`
  - las 4 herramientas comparten, segun catalogo:
    - `diameter = 8`
    - `sinking_length = 30`
    - `feed_rate_std = 3`
    - `spindle_speed_std = 6000`
- Restriccion funcional informada por usuario:
  - en cada cara lateral, la herramienta elegida es la unica disponible para ese
    trabajo
  - no es posible hacer huecos de otros diametros en esa cara
  - tampoco es posible hacer fresados con otras herramientas sobre esa misma cara
- Implicacion importante para futura spec:
  - en taladros laterales, la herramienta no deberia modelarse como parametro
    libre por defecto
  - la futura abstraccion puede derivar o validar automaticamente `ToolKey`
    desde:
    - `plane_name`
    - `diameter`
  - para el caso hoy relevado, la regla concreta queda:
    - `Front + D8 -> 058 / 1895`
    - `Back + D8 -> 059 / 1896`
    - `Right + D8 -> 060 / 1897`
    - `Left + D8 -> 061 / 1898`
- Salvedad:
  - esta regla de unicidad esta relevada solo para los taladros laterales
    observados en esta pieza
  - no debe extrapolarse aun a la cara superior ni a otros diametros sin casos
    manuales adicionales

### Ronda 14 - Cara superior con varios huecos y sin herramienta elegida

- Estado: completado
- Archivo relevado:
  - `archive/maestro_examples/Pieza_CaraSuperior_VariosDiametros.pgmx`
- Estructura general observada:
  - `7` geometrías `GeomCartesianPoint`
  - `7` features `a:RoundHole`
  - `7` operations `a:DrillingOperation`
  - `7` worksteps en `MainWorkplan`
  - todas las geometrías viven en el plano `Top`
- Regla estructural por hueco:
  - cada hueco agrega exactamente:
    - `1` punto geometrico
    - `1` feature `RoundHole`
    - `1` operation `DrillingOperation`
    - `1` workstep asociado
  - los IDs avanzan en bloques de 4 por hueco:
    - `geometry`
    - `operation`
    - `feature`
    - `workstep`
- Huecos observados:
  - `Broca Plana 8mm`:
    - punto `(100, 200, 0)`
    - `Diameter = 8`
    - `BottomCondition = FlatHoleBottom`
    - `Depth = 15`
  - `Broca Plana 5mm`:
    - punto `(164, 200, 0)`
    - `Diameter = 5`
    - `BottomCondition = FlatHoleBottom`
    - `Depth = 15`
  - `Broca Plana 4mm`:
    - punto `(196, 200, 0)`
    - `Diameter = 4`
    - `BottomCondition = FlatHoleBottom`
    - `Depth = 15`
  - `Broca Plana 35mm`:
    - punto `(132, 200, 0)`
    - `Diameter = 35`
    - `BottomCondition = FlatHoleBottom`
    - `Depth = 15`
  - `Broca Lanza 5mm`:
    - punto `(228, 200, 0)`
    - `Diameter = 5`
    - `BottomCondition = ConicalHoleBottom`
    - `TipAngle = 0`
    - `TipRadius = 0`
    - `Depth = 15`
  - `Broca Plana 15mm`:
    - punto `(100, 168, 0)`
    - `Diameter = 15`
    - `BottomCondition = FlatHoleBottom`
    - `Depth = 15`
  - `Broca Plana 20mm`:
    - punto `(100, 136, 0)`
    - `Diameter = 20`
    - `BottomCondition = FlatHoleBottom`
    - `Depth = 15`
- Parametros comunes observados en las 7 operaciones:
  - `ToolKey` vacio:
    - `ID = 0`
    - `ObjectType = System.Object`
    - `Name = ""`
  - `ApproachSecurityPlane = 20`
  - `RetractSecurityPlane = 20`
  - `StartPoint = (0, 0, 0)`
  - `Technology` con:
    - `Feedrate = 0`
    - `CutSpeed = 0`
    - `Spindle = 0`
  - `Operation/Name` vacio
- Parametros comunes observados en las 7 features:
  - `Feature/Name` no queda vacio
  - el nombre de la feature expresa la broca esperada:
    - `Broca Plana 8mm`
    - `Broca Plana 5mm`
    - `Broca Plana 4mm`
    - `Broca Plana 35mm`
    - `Broca Lanza 5mm`
    - `Broca Plana 15mm`
    - `Broca Plana 20mm`
  - `Diameter` vive en la feature
  - `BottomCondition` vive en la feature
  - `Depth` vive en la feature
- Relacion con `tools/tool_catalog.csv`:
  - el archivo cubre las 7 brocas verticales observadas en el catalogo:
    - `001` -> plana `8`
    - `002` -> plana `15`
    - `003` -> plana `20`
    - `004` -> plana `35`
    - `005` -> plana `5`
    - `006` -> plana `4`
    - `007` -> conica / lanza `5`
- Hallazgo clave para futura spec:
  - en cara superior, `diameter` solo no alcanza para resolver la broca
  - hay al menos un caso ambiguo:
    - `Diameter = 5`
    - puede ser:
      - `Broca Plana 5mm`
      - `Broca Lanza 5mm`
  - por lo tanto, una futura spec de taladro superior no deberia modelar solo:
    - `plane_name`
    - `diameter`
    - `depth`
  - debera modelar tambien al menos una semantica de fondo / familia de broca:
    - `flat`
    - `conical`
    - o un `drill_family`
- Desambiguacion observada para los dos `D5`:
  - la diferencia no aparece en `Operation`
  - ambos usan `DrillingOperation` con `ToolKey` vacio
  - la diferencia efectiva vive en la `Feature`:
    - `Broca Plana 5mm` -> `BottomCondition xsi:type = a:FlatHoleBottom`
    - `Broca Lanza 5mm` -> `BottomCondition xsi:type = a:ConicalHoleBottom`
  - el caso conico agrega ademas:
    - `TipAngle = 0`
    - `TipRadius = 0`
  - por ahora no aparece en este archivo una tercera variante `abocinada`
- Decision de diseÃ±o provisional para el sintetizador:
  - si el usuario no indica otra cosa, un hueco debe sintetizarse como
    `plano`
  - si el usuario declara que el hueco es `pasante`, la preferencia por
    defecto pasa a ser `conico` / `punta de lanza`
  - regla funcional aportada por usuario:
    - los huecos pasantes tambien pueden hacerse con brocas `planas` de
      cualquier diametro
    - esa alternativa es posible, aunque no sea la mas aconsejable
  - restriccion actual del toolset observado:
    - solo existe una broca conica relevada
    - esa broca es la de `5 mm`
  - implicacion para la futura resolucion de herramienta:
    - `through = true` debe preferir `conico` cuando exista una broca lanza
      compatible
    - si no existe una broca conica compatible para ese diametro, un hueco
      pasante sigue siendo valido con broca `plana`
    - por lo tanto, `through = true` no debe fallar automaticamente por no
      encontrar una broca conica del mismo diametro
    - en cambio, una solicitud explicita de `conico` si debera validarse contra
      el toolset disponible
- Diferencia importante frente al caso lateral:
  - en laterales, la herramienta parecia derivable desde `cara + diametro`
  - en superior, la geometria y la feature ya expresan mas informacion antes de
    elegir herramienta:
    - nombre de feature
    - tipo de fondo
  - por eso la futura resolucion de herramienta para superior deberia derivarse
    desde algo como:
    - `diameter + bottom_condition`
    - o `diameter + drill_family`
- Observacion secundaria:
  - el orden de `Worksteps` no coincide exactamente con el orden de las
    features en XML ni con el orden numerico de IDs
  - por ahora no hay evidencia suficiente para afirmar la regla de orden, asi
    que no conviene sintetizar asumiendo una ordenacion fuerte sin mas casos

### Ronda 15 - Cara superior con huecos pasantes y `Extra`

- Estado: completado
- Archivos relevados:
  - `archive/maestro_examples/Pieza_CaraSuperior_VariosDiametros_Pasantes_Extra0.pgmx`
  - `archive/maestro_examples/Pieza_CaraSuperior_VariosDiametros_Pasantes_Extra1.pgmx`
- Regla comun observada en ambos archivos:
  - se conservan los mismos `7` puntos, `7` features, `7` operaciones y `7`
    worksteps del caso base
  - se conservan posiciones, nombres de feature y diametros
  - en los `7` huecos:
    - `BottomCondition` pasa a `a:ThroughHoleBottom`
    - `Depth/StartDepth = 18`
    - `Depth/EndDepth = 18`
  - `18` coincide con el espesor de la pieza (`dz1 = 18`)
  - `ToolKey` sigue vacio en las `7` `DrillingOperation`
  - no aparece un nodo XML explicito llamado `Extra`
- Hallazgo clave sobre la semantica `through`:
  - al pasar a `ThroughHoleBottom`, la feature ya no distingue por
    `BottomCondition` entre broca `plana` y broca `lanza`
  - por ejemplo, los dos `D5` quedan con el mismo `BottomCondition`:
    - `Broca Plana 5mm` -> `a:ThroughHoleBottom`
    - `Broca Lanza 5mm` -> `a:ThroughHoleBottom`
  - en este estado, la diferencia de familia de broca queda solo en el
    `Feature/Name` y, potencialmente, en la herramienta elegida despues
- Diferencia observada entre `Extra0` y `Extra1`:
  - la diferencia no vive en `Feature/Depth`, `CuttingDepth` ni `ToolKey`
  - la diferencia vive dentro de
    `Operation/ToolpathList/Toolpath/BasicCurve/_serializationGeometryDescription`
  - patron constante en los `7` huecos:
    - `Approach` es igual en ambos casos:
      - `8 0 20`
      - `1 x y 38 0 0 -1`
    - con `Extra0`:
      - `TrajectoryPath = 8 0 18`
      - `1 x y 18 0 0 -1`
      - `Lift = 8 0 38`
      - `1 x y 0 0 0 1`
    - con `Extra1`:
      - `TrajectoryPath = 8 0 19`
      - `1 x y 18 0 0 -1`
      - `Lift = 8 0 39`
      - `1 x y -1 0 0 1`
- Interpretacion provisional:
  - `Extra` parece afectar la extension efectiva del toolpath por debajo de la
    cara opuesta
  - `Extra = 0` retrae desde la cota inferior `z = 0`
  - `Extra = 1` retrae desde `z = -1`
  - la profundidad declarada en la feature sigue siendo el espesor nominal de
    la pieza (`18`); el extra no se refleja aumentando `Depth`
- Implicacion para la futura spec:
  - `through` debe modelarse por separado de `bottom_condition`
  - `drill_family` tambien debe modelarse por separado de `bottom_condition`,
    porque en huecos pasantes `ThroughHoleBottom` no alcanza para distinguir
    `plana` vs `lanza`
  - si se quiere sintetizar el comportamiento manual completo, habra que
    modelar tambien un parametro tipo `extra_through_depth`

### Ronda 16 - Cara superior con herramientas ya seleccionadas

- Estado: completado
- Archivo relevado:
  - `archive/maestro_examples/Pieza_CaraSuperior_VariosDiametros_HerramientaSeleccionada.pgmx`
- Comparado contra:
  - `archive/maestro_examples/Pieza_CaraSuperior_VariosDiametros.pgmx`
- Mapeo de herramientas observado:
  - `Broca Plana 8mm` -> `ToolKey = 1888 / 001`
  - `Broca Plana 5mm` -> `ToolKey = 1892 / 005`
  - `Broca Plana 4mm` -> `ToolKey = 1893 / 006`
  - `Broca Plana 35mm` -> `ToolKey = 1891 / 004`
  - `Broca Lanza 5mm` -> `ToolKey = 1894 / 007`
  - `Broca Plana 15mm` -> `ToolKey = 1889 / 002`
  - `Broca Plana 20mm` -> `ToolKey = 1890 / 003`
- Relacion con `tools/tool_catalog.csv`:
  - coincide exactamente con el catalogo vertical observado:
    - `001` plana vertical `D8`
    - `002` plana vertical `D15`
    - `003` plana vertical `D20`
    - `004` plana vertical `D35`
    - `005` plana vertical `D5`
    - `006` plana vertical `D4`
    - `007` conica vertical `D5`
- Regla observada en `6` de `7` huecos:
  - Maestro solo actualiza `Operation/ToolKey`
  - no cambian:
    - geometria
    - profundidad
    - `ToolpathList`
    - `BottomCondition`
- Excepcion importante:
  - en `Broca Lanza 5mm`, ademas de asignar `ToolKey = 1894 / 007`, Maestro
    cambia la `Feature`:
    - antes: `BottomCondition = a:ConicalHoleBottom`
    - despues: `BottomCondition = a:FlatHoleBottom`
    - desaparecen `TipAngle = 0` y `TipRadius = 0`
  - pese a ese cambio, los toolpaths de la operacion quedan iguales al caso
    anterior sin herramienta seleccionada
- Hallazgo clave para la futura spec:
  - en cara superior, la familia de broca no puede inferirse siempre desde
    `BottomCondition`
  - el caso manual `Broca Lanza 5mm` muestra que, una vez elegida la
    herramienta `007`, la semantica `conica / lanza` puede quedar expresada por
    `ToolKey` y por `Feature/Name`, aunque `BottomCondition` termine siendo
    `FlatHoleBottom`
  - por lo tanto, la futura spec deberia modelar explicitamente
    `drill_family`, sin depender solo de `bottom_condition`

### Ronda 17 - Implementacion de `DrillingSpec`

- Estado: completado
- Cambios aplicados en `tools/synthesize_pgmx.py`:
  - se agrego la spec publica `DrillingSpec`
  - se agrego la helper publica `build_drilling_spec(...)`
  - `build_synthesis_request(...)`, `synthesize_request(...)` y
    `synthesize_pgmx(...)` ya aceptan `drillings`
  - el sintetizador ya escribe:
    - `GeomCartesianPoint`
    - `RoundHole`
    - `DrillingOperation`
    - `MachiningWorkingStep`
- Alcance validado de la implementacion:
  - caras soportadas en V1:
    - `Top`
    - `Front`
    - `Back`
    - `Right`
    - `Left`
  - familias soportadas en V1:
    - `Flat`
    - `Conical`
  - `Countersunk / Abocinado` sigue fuera de alcance por falta de casos
    manuales relevados
- Reglas ya volcadas al codigo:
  - `through` reutiliza `MillingDepthSpec`, pero en taladros:
    - `BottomCondition = ThroughHoleBottom`
    - `Depth` se liga al espesor util de la cara
    - `Extra` extiende `TrajectoryPath`
  - el espesor util depende de la cara:
    - `Top -> dz1`
    - `Front/Back -> dy1`
    - `Right/Left -> dx1`
  - el toolpath del taladro se sintetiza como:
    - `Approach`: plano de seguridad -> cara de entrada
    - `TrajectoryPath`: cara de entrada -> profundidad efectiva
    - `Lift`: profundidad efectiva -> plano de seguridad
  - `tool_resolution` soporta:
    - `None`
    - `Auto`
    - `Explicit`
  - `Auto` ya resuelve:
    - verticales `001..007`
    - laterales `058..061`
  - caso especial ya incorporado:
    - `Top + D5 + Conical + herramienta seleccionada (007)` normaliza la
      feature a `FlatHoleBottom`, conservando la semantica conica por
      `ToolKey` y `Feature/Name`
- Verificaciones locales ejecutadas:
  - compilacion de `tools/synthesize_pgmx.py`
  - sintesis de:
    - taladro superior sin herramienta
    - taladro lateral frontal con herramienta auto-resuelta
    - taladro superior pasante con `Extra = 1`
    - taladro superior `Conical D5` con y sin herramienta seleccionada

### Ronda 18 - Archivo manual con huecos en varias caras

- Estado: completado
- Archivo relevado:
  - `archive/maestro_examples/Pieza_Huecos_VariasCaras.pgmx`
- Estado de pieza observado:
  - `Length = 300`
  - `Width = 300`
  - `Depth = 18`
  - `WorkpieceSetup/Placement = (0, 0, 0)`
- Inventario manual:
  - `8` `GeomCartesianPoint`
  - `8` `RoundHole`
  - `8` `DrillingOperation`
  - `8` `MachiningWorkingStep`
  - `1` `MainWorkplan`
- Distribucion por cara:
  - `Top`:
    - `Hueco15_01` en `(32, 33, 0)` con `D15 x 15`
    - `Hueco15_02` en `(268, 33, 0)` con `D15 x 15`
    - `Hueco15_03` en `(268, 267, 0)` con `D15 x 15`
    - `Hueco15_04` en `(32, 267, 0)` con `D15 x 15`
  - `Front`:
    - `HuecoDelantero08_01` en `(32, 9, 0)` con `D8 x 28`
    - `HuecoDelantero08_02` en `(268, 9, 0)` con `D8 x 28`
  - `Back`:
    - `HuecoTrasero08_01` en `(32, 9, 0)` con `D8 x 28`
    - `HuecoTrasero08_02` en `(268, 9, 0)` con `D8 x 28`
- Parametros comunes observados:
  - `BottomCondition = FlatHoleBottom` en los `8` huecos
  - `ToolKey` vacio en las `8` operaciones:
    - `ID = 0`
    - `ObjectType = System.Object`
    - `Name = ""`
  - `ApproachSecurityPlane = 20`
  - `RetractSecurityPlane = 20`
  - `StartPoint = (0, 0, 0)`
  - `Technology = (Feedrate = 0, CutSpeed = 0, Spindle = 0)`
- Hallazgo estructural clave:
  - Maestro serializa un archivo valido con mecanizados en varias caras dentro
    de un solo `MainWorkplan`
  - no aparecen `MainWorkplan` adicionales
  - no aparecen `Setup` o `WorkpieceSetup` extra por cara
  - la cara de cada hueco se expresa por:
    - `Geometries/GeomCartesianPoint/PlaneID`
    - y por la orientacion del `ToolpathList`
- Patron de `ToolpathList` observado por cara:
  - `Top`:
    - `Approach` arranca en `z = dz1 + 20`
    - `TrajectoryPath` arranca en `z = dz1`
    - `Lift` arranca en `z = dz1 - depth`
    - orientacion `(0, 0, -1)` para entrada/corte y `(0, 0, 1)` para salida
  - `Front`:
    - `Approach` arranca en `y = -20`
    - `TrajectoryPath` arranca en `y = 0`
    - `Lift` arranca en `y = depth`
    - orientacion `(0, 1, 0)` para entrada/corte y `(0, -1, 0)` para salida
  - `Back`:
    - `Approach` arranca en `y = dy1 + 20`
    - `TrajectoryPath` arranca en `y = dy1`
    - `Lift` arranca en `y = dy1 - depth`
    - orientacion `(0, -1, 0)` para entrada/corte y `(0, 1, 0)` para salida
- Implicacion directa para el sintetizador:
  - queda descartada la hipotesis de que `Top + Front + Back` en un unico
    `MainWorkplan` sea invalido para Maestro
  - el cierre observado en el archivo sintetizado anterior no puede explicarse
    solo por mezclar caras en un mismo proyecto
- Variables que siguen abiertas frente al archivo sintetizado que fallo:
  - origen no nulo (`WorkpieceSetup/Placement = (5, 5, 25)`)
  - `ToolKey` auto-resuelto en un archivo multicara
  - alguna diferencia secundaria en la serializacion XML no presente en este
    caso manual
- Observacion secundaria:
  - el orden de los `Worksteps` no necesita agruparse por cara
  - en el ejemplo manual queda:
    - primero `Top`
    - luego `Front`
    - luego `Back`
  - ademas, el par trasero no queda ordenado estrictamente por ID numerico
    dentro del `MainWorkplan`

### Ronda 19 - Variantes multicara con `Left/Right` y con origen no nulo

- Estado: completado
- Archivos relevados:
  - `archive/maestro_examples/Pieza_Huecos_VariasCaras.pgmx`
  - `archive/maestro_examples/Pieza_Huecos_VariasCarasV2.pgmx`
  - `archive/maestro_examples/Pieza_Huecos_VariasCaras_Origen_5_5_25.pgmx`
- Comparacion `V1` vs `V2`:
  - `V1` contiene `8` taladros:
    - `4` en `Top`
    - `2` en `Front`
    - `2` en `Back`
  - `V2` contiene `16` taladros:
    - `8` en `Top`
    - `2` en `Front`
    - `2` en `Back`
    - `2` en `Left`
    - `2` en `Right`
- Hallazgo nuevo para sintesis:
  - `V2` completa el patron manual de toolpaths para `Left` y `Right`
  - `Left`:
    - centro local observado:
      - `(236, 9, 0)`
      - `(64, 9, 0)`
    - `Approach` arranca en `x = -20`
    - `TrajectoryPath` arranca en `x = 0`
    - `Lift` arranca en `x = depth`
    - orientacion:
      - entrada/corte `(1, 0, 0)`
      - salida `(-1, 0, 0)`
  - `Right`:
    - centro local observado:
      - `(236, 9, 0)`
      - `(64, 9, 0)`
    - `Approach` arranca en `x = dx1 + 20`
    - `TrajectoryPath` arranca en `x = dx1`
    - `Lift` arranca en `x = dx1 - depth`
    - orientacion:
      - entrada/corte `(-1, 0, 0)`
      - salida `(1, 0, 0)`
- Regla generalizada de taladros laterales ahora respaldada manualmente:
  - caras con avance positivo desde `0`:
    - `Front`
    - `Left`
  - caras con avance negativo desde el extremo opuesto:
    - `Back`
    - `Right`
  - formulas observadas:
    - `Front`:
      - seguridad `-20`
      - entrada `0`
      - salida `depth`
    - `Back`:
      - seguridad `span + 20`
      - entrada `span`
      - salida `span - depth`
    - `Left`:
      - seguridad `-20`
      - entrada `0`
      - salida `depth`
    - `Right`:
      - seguridad `span + 20`
      - entrada `span`
      - salida `span - depth`
  - donde `span` vale:
    - `dy1` para `Front/Back`
    - `dx1` para `Left/Right`
- Seleccion de herramienta observada en `V2`:
  - los `4` taladros superiores iniciales `D15` tienen `ToolKey = 1889 / 002`
  - los `2` taladros `Front D8` tienen `ToolKey = 1895 / 058`
  - los `2` taladros `Back D8` tienen `ToolKey = 1896 / 059`
  - los `4` taladros superiores agregados y los `4` laterales `Left/Right`
    quedaron con `ToolKey` vacio
- Implicacion importante:
  - `ToolKey` es estrictamente por operacion
  - en un mismo archivo multicara pueden convivir:
    - taladros equivalentes con herramienta seleccionada
    - taladros equivalentes con `ToolKey` vacio
  - por lo tanto, la futura spec debe mantener `tool_resolution` por taladro,
    no por archivo ni por cara completa
- Diferencia geometrica entre `V1` y `V2`:
  - `V2` no solo agrega caras laterales
  - tambien reubica el primer conjunto de huecos:
    - de `32/268` a `64/236`
  - y agrega un segundo marco superior:
    - `(33,64)`
    - `(33,236)`
    - `(267,236)`
    - `(267,64)`
  - esto confirma que Maestro no impone una sola convencion de orden o de
    simetria en el `MainWorkplan`; refleja el orden de creacion manual
- Comparacion `V1` vs `Origen_5_5_25`:
  - conservan exactamente:
    - las `8` geometrías
    - las `8` features
    - las `8` operaciones
    - todos los `ToolpathList`
    - todos los `ToolKey`
  - la unica diferencia funcional observada es:
    - `WorkpieceSetup/Placement._xP = 5`
    - `WorkpieceSetup/Placement._yP = 5`
    - `WorkpieceSetup/Placement._zP = 25`
- Implicacion directa para el sintetizador:
  - un origen no nulo no traslada:
    - `GeomCartesianPoint`
    - `RoundHole`
    - `ToolpathList`
  - solo modifica la colocacion de la pieza en
    `MainWorkplan/Setup/WorkpieceSetup/Placement`
  - esto refuerza la regla ya observada en otras familias:
    - el origen afecta el setup, no la geometria local del mecanizado

### Ronda 20 - Correccion del orden multicara en el sintetizador

- Estado: completado
- Cambio aplicado en `tools/synthesize_pgmx.py`:
  - `_apply_drillings(...)` ahora ordena los taladros por prioridad de plano
    antes de escribirlos al `.pgmx`
- Prioridad aplicada:
  - `Top`
  - `Front`
  - `Back`
  - `Left`
  - `Right`
- Justificacion:
  - en todos los ejemplos manuales multicara relevados, Maestro agrupa los
    taladros por cara dentro de un unico `MainWorkplan`
  - antes, el sintetizador preservaba el orden de entrada del usuario, que
    podia mezclar caras arbitrariamente
- Efecto practico:
  - los `Worksteps`, `Features`, `Operations` y `Geometries` de taladros
    multicara ahora se escriben siguiendo el patron manual observado
  - dentro de cada cara se preserva el orden relativo de entrada
- Regeneracion realizada:
  - `archive/maestro_examples/Pieza_420x350x18_DobleCamlock_Delantero.pgmx`
  - el archivo regenerado ahora queda con el orden:
    - `Top`
    - `Top`
    - `Front`
    - `Front`

### Ronda 21 - Serializacion raw de toolpaths de taladrado

- Estado: completado
- Hallazgo concreto al comparar el sintetico
  `Pieza_420x350x18_DobleCamlock_Delantero.pgmx` contra los manuales validos:
  - los nodos `Operation/ToolpathList/.../_serializationGeometryDescription`
    sinteticos estaban perdiendo el formato raw exacto de Maestro
  - el sintetizador recortaba espacios finales y el salto de linea final
  - ejemplo sintetico previo:
    - `8 0 20\\n1 32 33 38 0 0 -1`
  - ejemplo manual valido:
    - `8 0 20\\n1 64 33 38 0 0 -1 \\n`
- Causa localizada:
  - `_normalize_curve_serialization_text(...)` hacia `strip()` y `rstrip()`
    sobre cada linea
  - eso alteraba la serializacion exacta generada por
    `_build_maestro_line_serialization(...)` y
    `_build_maestro_arc_serialization(...)`
- Correccion aplicada en `tools/synthesize_pgmx.py`:
  - ahora se normalizan solo los finales de linea `CRLF/CR -> LF`
  - se preservan los espacios finales de cada linea
  - se preserva el salto final cuando el raw original lo trae
- Resultado inmediato:
  - el `.pgmx` de doble Camlock fue regenerado con los toolpaths de taladro en
    formato raw compatible con los ejemplos manuales relevados
  - `py -3 -m py_compile tools\\synthesize_pgmx.py` sigue pasando

### Ronda 22 - Namespace faltante en ToolpathList al reutilizar un baseline sintetico

- Estado: completado
- Caso observado:
  - `archive/maestro_examples/Pieza_320x260x18_EscuadradoAntihorario_DobleCamlockIzquierdo.pgmx`
  - Maestro rechazaba el archivo al abrirlo con:
    - `SerializationException`
    - `Toolpath` con tipo `b:CutterLocationTrajectory`
    - prefijo `b` no reconocido en ese punto del XML
- Causa localizada:
  - `_finalize_pgmx_xml_bytes(...)` solo agregaba `xmlns:b` a `ToolpathList`
    si no existia ningun `ToolpathList` correcto en todo el documento
  - en archivos combinados que parten de un baseline ya sintetico, algunos
    `ToolpathList` quedaban bien y otros no
  - el caso concreto afectaba al `ToolpathList` del escuadrado heredado del
    baseline, mientras los taladros nuevos ya traian su declaracion correcta
- Correccion aplicada en `tools/synthesize_pgmx.py`:
  - se reemplazo la logica global por una normalizacion por ocurrencia
  - ahora cada nodo de estos tipos recibe `xmlns:b` si le falta:
    - `ToolpathList`
    - `Head`
    - `MachineFunctions`
    - `StartPoint`
    - `ToolKey`
- Verificacion:
  - el archivo regenerado ya no contiene ningun `<ToolpathList>` sin
    `xmlns:b="http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel"`
  - `py -3 -m py_compile tools\\synthesize_pgmx.py` sigue pasando

### Ronda 23 - Tags autocerrados rotos por la normalizacion de namespaces

- Estado: completado
- Caso observado en
  `C:\\Program Files (x86)\\Scm Group\\Maestro\\log\\Log20260415_165037.logx`:
  - Maestro rechazo el archivo con XML invalido:
    - `Se esperaba el token '>', pero se encontro ' '`
  - el error ocurria al deserializar `BottomAndSideFinishMilling`
- Causa localizada:
  - la correccion anterior agregaba `xmlns:b` por regex sobre tags como
    `Head` y `MachineFunctions`
  - en tags autocerrados, el namespace se insertaba despues de `/`
  - ejemplo roto observado:
    - `<Head i:nil="true" / xmlns:b="...">`
    - `<MachineFunctions / xmlns:b="...">`
- Correccion aplicada:
  - la rutina `ensure_prefixed_namespace_attr(...)` ahora detecta
    autocierre por separado y reconstruye correctamente:
    - `<Head i:nil="true" xmlns:b="..." />`
    - `<MachineFunctions xmlns:b="..." />`
- Conclusión importante para el sintetizador:
  - en este caso el problema no fue el uso de `DrillingSpec` o
    `SquaringMillingSpec`
  - el problema estaba en la capa de serializacion/finalizacion XML del
    sintetizador

### Ronda 24 - Baseline versionado movido a `tools` y documentacion de specs

- Estado: completado
- Cambio operativo:
  - la carpeta `archive/maestro_baselines` se movio a
    `tools/maestro_baselines`
  - ese baseline versionado pasa a ser la ubicacion canonica del repo
- Cambio en codigo:
  - `tools/synthesize_pgmx.py` ahora expone:
    - `DEFAULT_BASELINE_DIR`
    - `DEFAULT_BASELINE_XML_PATH`
  - `build_synthesis_request(...)` usa `DEFAULT_BASELINE_DIR` si no se indica
    `baseline_path`
  - la CLI `python -m tools.synthesize_pgmx` tambien usa
    `tools/maestro_baselines` por defecto cuando no se pasa `--baseline`
- Cambio en documentacion:
  - `README.md` ya resume la nueva ubicacion canonica
  - `docs/synthesize_pgmx_help.md` ahora deja mas claro el flujo de specs:
    - pieza en `build_synthesis_request(...)`
    - escuadrado en `SquaringMillingSpec`
    - cada hueco en `DrillingSpec`
    - ejecucion en `synthesize_request(...)`
  - la guia tambien agrega un ejemplo completo de pieza escuadrada con doble
    camlock lateral usando el baseline por defecto

### Ronda 25 - Pieza base 400x400x18 con origen no nulo

- Estado: completado
- Objetivo:
  - trabajar fuera del flujo principal
  - sintetizar una pieza simple sin mecanizados
  - fijar un caso minimo con origen no nulo para futuras comparaciones
- Archivo generado:
  - `archive/maestro_examples/Pieza_400x400x18_Origen_5_5_25.pgmx`
- Solicitud usada en `tools.synthesize_pgmx`:
  - `piece_name = Pieza_400x400x18_Origen_5_5_25`
  - `length = 400`
  - `width = 400`
  - `depth = 18`
  - `origin_x = 5`
  - `origin_y = 5`
  - `origin_z = 25`
- Verificacion con `tools.pgmx_snapshot.read_pgmx_snapshot(...)`:
  - `snapshot.state.length = 400.0`
  - `snapshot.state.width = 400.0`
  - `snapshot.state.depth = 18.0`
  - `snapshot.state.origin = (5.0, 5.0, 25.0)`
  - `workpiece = (400.0, 400.0, 18.0)`
  - `geometries = 0`
  - `features = 0`
  - `operations = 0`
  - `working_steps = 1`
  - `resolved_working_steps = 1`
- Verificacion directa del XML dentro del `.pgmx`:
  - entrada XML: `Pieza_400x400x18_Origen_5_5_25.xml`
  - `WorkpieceSetup/Placement/_xP = 5`
  - `WorkpieceSetup/Placement/_yP = 5`
  - `WorkpieceSetup/Placement/_zP = 25`
  - `WorkPiece/Length = 400`
  - `WorkPiece/Width = 400`
  - `WorkPiece/Depth = 18`
  - variables: `dx1 = 400`, `dy1 = 400`, `dz1 = 18`
- Hallazgo:
  - una pieza sin mecanizados conserva solo el workstep final `Xn`
  - `pgmx_snapshot.resolved_working_steps` resuelve ese paso como:
    - `step = Xn`
    - `feature = None`
    - `operation = None`
    - `geometry = None`
    - `plane = None`
  - para una pieza sin geometria ni mecanizado, el origen no nulo queda
    expresado exclusivamente en `WorkpieceSetup/Placement`

### Ronda 26 - Canal lineal manual sobre pieza con origen no nulo

- Estado: completado
- Archivos estudiados:
  - `archive/maestro_examples/Pieza_400x400x18_Origen_5_5_25_CanalCentral.pgmx`
  - `archive/maestro_examples/Pieza_400x400x18_Origen_5_5_25_CanalDerecha.pgmx`
  - `archive/maestro_examples/Pieza_400x400x18_Origen_5_5_25_CanalIzquierda.pgmx`
- Punto de partida:
  - los tres archivos conservan la pieza base:
    - `length = 400`
    - `width = 400`
    - `depth = 18`
    - `origin = (5, 5, 25)`
  - el origen sigue estando solo en `WorkpieceSetup/Placement`
- Estructura comun:
  - `geometries = 1`
  - `features = 1`
  - `operations = 1`
  - `working_steps = 2`
  - workplan:
    - paso 1: `Canal`, resuelto por `pgmx_snapshot` a feature, operacion,
      geometria y plano `Top`
    - paso 2: `Xn`, sin feature, operacion, geometria ni plano
- Geometria nominal del canal:
  - tipo: `GeomTrimmedCurve`
  - clasificacion: `LineHorizontal`
  - plano: `Top`
  - serializacion:
    - `8 0 400`
    - `1 400 390 0 -1 0 0`
  - puntos nominales:
    - inicio `(400, 390, 0)`
    - fin `(0, 390, 0)`
  - la geometria nominal corre de derecha a izquierda sobre `Y = 390`
- Feature:
  - tipo: `a:SlotSide`
  - nombre: `Canal`
  - `BottomCondition = a:GeneralMillingBottom`
  - profundidad: `StartDepth = 10`, `EndDepth = 10`
  - `depth_spec = MillingDepthSpec(is_through=False, target_depth=10)`
  - `MaterialPosition = Left`
  - `SideOffset = 0`
  - `IsGeomSameDirection = true`
  - `IsPrecise = false`
  - perfil barrido:
    - `SweptShape = a:SquareUProfile`
    - `Width = 3.8`
    - `FirstAngle = 0`
    - `FirstRadius = 0`
    - `SecondAngle = 0`
    - `SecondRadius = 0`
  - extremos:
    - dos `a:WoodruffSlotEndType`
    - `Radius = 60` en ambos extremos
  - `OvercutLenghtInput = 0`
  - `OvercutLenghtOutput = 0`
  - `Angle = 1.5707963267948966`
- Operacion:
  - tipo: `a:BottomAndSideFinishMilling`
  - `ToolKey = 1899 / 082`
  - `ActivateCNCCorrection = false`
  - `ToolpathPriority = true`
  - `ApproachSecurityPlane = 20`
  - `RetractSecurityPlane = 20`
  - `HeadRotation = 0`
  - `Technology = MillingTechnology`, con feed/cut/spindle en `0`
  - `Approach = BaseApproachStrategy`, deshabilitado
  - `Retract = BaseRetractStrategy`, deshabilitado
  - `MachiningStrategy = nil`
  - `AllowanceBottom = 0`
  - `AllowanceSide = 0`
- Toolpaths efectivos:
  - siempre hay tres curvas:
    - `Approach`
    - `TrajectoryPath`
    - `Lift`
  - aunque `Approach` y `Retract` esten deshabilitados como estrategias, el
    XML mantiene curvas verticales de bajada y subida
  - como `depth = 18` y profundidad de canal `10`, la trayectoria mecanizante
    queda en `Z = 8`
  - la cota de seguridad queda en `Z = 38`, que coincide con `18 + 20`
- Comparacion de lado:
  - `CanalDerecha`:
    - `SideOfFeature = Right`
    - trayectoria efectiva en `Y = 391.9`
    - offset efectivo contra geometria nominal: `+1.9`
  - `CanalIzquierda`:
    - `SideOfFeature = Left`
    - trayectoria efectiva en `Y = 388.1`
    - offset efectivo contra geometria nominal: `-1.9`
  - `CanalCentral`:
    - `SideOfFeature = Center`
    - trayectoria efectiva en `Y = 390.0`
    - offset efectivo contra geometria nominal: `0.0`
    - XML interno distinto de `CanalDerecha` y de `CanalIzquierda`
- Hallazgos:
  - para una linea nominal que va de `(400,390)` a `(0,390)`,
    `SideOfFeature = Right` desplaza el toolpath hacia `Y+`
  - `SideOfFeature = Left` desplaza el toolpath hacia `Y-`
  - `SideOfFeature = Center` mantiene el toolpath sobre la geometria nominal
  - el desplazamiento observado es `tool_width / 2 = 3.8 / 2 = 1.9`
    para `Right` y `Left`; para `Center` es `0`
  - la compensacion cambia la trayectoria efectiva, no la geometria nominal
  - ahora si quedan tres estados distintos:
    - `Center`: trayectoria nominal
    - `Right`: trayectoria desplazada `+1.9` en `Y`
    - `Left`: trayectoria desplazada `-1.9` en `Y`
- Mejora aplicada a `tools/pgmx_snapshot.py`:
  - se agrego `PgmxSlotEndConditionSnapshot`
  - `PgmxFeatureSnapshot` ahora expone:
    - `overcut_input`
    - `overcut_output`
    - `swept_shape_type`
    - `first_angle`
    - `first_radius`
    - `second_angle`
    - `second_radius`
    - `slot_angle`
    - `end_conditions`
  - esto evita depender del XML crudo para estudiar canales `SlotSide`

### Ronda 27 - Canal erroneo sobre pieza con origen no nulo

- Estado: completado
- Revision:
  - el archivo fue corregido despues del primer analisis para usar profundidad
    `10`
  - esta ronda refleja la lectura vigente del archivo corregido
- Archivo estudiado:
  - `archive/maestro_examples/Pieza_400x400x18_Origen_5_5_25_CanalErroneo.pgmx`
- Comparado contra:
  - `Pieza_400x400x18_Origen_5_5_25_CanalCentral.pgmx`
  - `Pieza_400x400x18_Origen_5_5_25_CanalDerecha.pgmx`
  - `Pieza_400x400x18_Origen_5_5_25_CanalIzquierda.pgmx`
- Punto de partida comun:
  - conserva pieza base `400 x 400 x 18`
  - conserva origen `(5, 5, 25)`
  - conserva una estructura de mecanizado:
    - `geometries = 1`
    - `features = 1`
    - `operations = 1`
    - `working_steps = 2`
  - conserva feature `a:SlotSide` llamado `Canal`
  - conserva operacion `a:BottomAndSideFinishMilling`
  - conserva herramienta `1899 / 082`
  - conserva perfil:
    - `SweptShape = a:SquareUProfile`
    - `Width = 3.8`
    - dos extremos `a:WoodruffSlotEndType`
    - `Radius = 60`
    - `Angle = 1.5707963267948966`
- Diferencias contra los canales validos:
  - geometria nominal:
    - validos: `LineHorizontal`
    - erroneo: `LineVertical`
  - serializacion geometrica del erroneo:
    - `8 0 400`
    - `1 390 0 0 0 1 0`
  - puntos nominales del erroneo:
    - inicio `(390, 0, 0)`
    - fin `(390, 400, 0)`
  - en los validos, la linea nominal era:
    - inicio `(400, 390, 0)`
    - fin `(0, 390, 0)`
  - lado:
    - erroneo: `SideOfFeature = Center`
  - profundidad:
    - el archivo corregido coincide con los validos:
      - `StartDepth = 10`
      - `EndDepth = 10`
      - `MillingDepthSpec(is_through=False, target_depth=10)`
- Toolpath efectivo del erroneo:
  - `Approach`:
    - `(390, 0, 38)` -> `(390, 0, 8)`
  - `TrajectoryPath`:
    - `(390, 0, 8)` -> `(390, 400, 8)`
  - `Lift`:
    - `(390, 400, 8)` -> `(390, 400, 38)`
- Restriccion CNC / herramienta:
  - el programa no es ejecutable en CNC con la herramienta seleccionada
  - la herramienta `1899 / 082` figura en `tools/tool_catalog.csv` como
    `Sierra Vertical X`
  - para esta familia, la regla ya documentada en `tools/synthesize_pgmx.py`
    acepta solamente ranurados lineales horizontales, sobre `Top`, no pasantes
  - `CanalErroneo` pide una trayectoria vertical sobre `Top`, desde
    `(390, 0, 8)` hasta `(390, 400, 8)`
  - por criterio de maquina, no hay herramienta disponible que pueda realizar
    ese recorrido como fue programado
  - por lo tanto, este caso debe clasificarse como geometria invalida para
    sintesis/adaptacion, no como una variante corregible por seleccion de
    herramienta
- Comparacion con `CanalCentral`:
  - ambos usan `SideOfFeature = Center`
  - `CanalCentral` mantiene trayectoria sobre la geometria nominal horizontal
    en `Y = 390`, a `Z = 8`
  - `CanalErroneo` mantiene trayectoria sobre la geometria nominal vertical
    en `X = 390`, a `Z = 8`
- Hallazgos:
  - con la profundidad corregida, el error ya no esta en la profundidad ni en
    la compensacion lateral
  - el canal erroneo fue creado como linea vertical `X = 390` en lugar de
    linea horizontal `Y = 390`
  - la trayectoria mecanizante queda ahora a la misma profundidad que los
    canales validos: `Z = 8`
  - la longitud vertical del approach/lift baja/sube `30` mm (`38 -> 8`),
    igual que en los canales validos
  - para sintetizar o adaptar canales, el interprete debe validar juntos:
    - orientacion/geometria nominal
    - profundidad efectiva
    - `SideOfFeature`
    - toolpath resultante
    - compatibilidad entre tipo de herramienta y orientacion del recorrido

### Ronda 28 - Spec publica para ranuras `SlotSide`

- Estado: completado
- Objetivo:
  - volcar los hallazgos de canales manuales a la API publica del sintetizador
  - evitar que una ranura vertical con `Sierra Vertical X` sea tratada como
    programa valido
  - sintetizar una pieza de prueba `Fondo` con ranura horizontal real
- Cambios aplicados en `tools/synthesize_pgmx.py`:
  - `SYNTHESIZER_VERSION` sube a `1.3`
  - se agrego `SlotMillingSpec`
  - se agrego `build_slot_milling_spec(...)`
  - `PgmxSynthesisRequest` y `PgmxSynthesisResult` ahora aceptan
    `slot_millings`
  - `synthesize_request(...)` hidrata, valida y aplica ranuras `SlotSide`
  - `machining_order` incorpora la familia `slot`
  - la feature generada es `a:SlotSide`, con:
    - `ObjectType = ScmGroup.XCam.MachiningDataModel.Milling.SlotSide`
    - `SweptShape = a:SquareUProfile`
    - `Width = 3.8`
    - dos extremos `a:WoodruffSlotEndType`
    - `Radius = 60`
    - `Angle = 1.5707963267948966`
  - la herramienta default de la spec es `1899 / 082`
  - la validacion de tipo de herramienta exige que `SlotMillingSpec` use
    `Sierra Vertical X`
  - para `Sierra Vertical X`, el sintetizador rechaza recorridos no
    horizontales, planos distintos de `Top` y ranuras pasantes
- Cambios aplicados en `tools/pgmx_adapters.py`:
  - `SlotSide` horizontal se adapta como `SlotMillingSpec`
  - `SlotSide` vertical queda `unsupported`
  - `CanalCentral` adapta como:
    - `adapted = 1`
    - `slot_millings = 1`
  - `CanalErroneo` queda:
    - `unsupported = 1`
    - razon: `SlotSide` con `Sierra Vertical X` requiere una recta horizontal
      sobre `Top`; el recorrido vertical no es ejecutable en CNC
- Documentacion actualizada:
  - `README.md`
  - `docs/synthesize_pgmx_help.md`
  - `docs/pgmx_adapters_help.md`
- Archivo sintetizado:
  - no se piso el `archive/maestro_examples/Fondo.pgmx` existente
  - se genero:
    `archive/maestro_examples/Fondo_349p1x580x18_Origen_5_5_25_Ranura.pgmx`
- Solicitud de sintesis:
  - `piece_name = Fondo`
  - `length = 349.1`
  - `width = 580`
  - `depth = 18`
  - `origin = (5, 5, 25)`
  - ranura:
    - inicio `(7.55, 570)`
    - fin `(341.55, 570)`
    - profundidad no pasante `10`
    - herramienta `1899 / 082`
- Verificacion con `tools.pgmx_snapshot.read_pgmx_snapshot(...)`:
  - `state.piece_name = Fondo`
  - `state.length = 349.1`
  - `state.width = 580`
  - `state.depth = 18`
  - `state.origin = (5, 5, 25)`
  - `geometries = 1`
  - `features = 1`
  - `operations = 1`
  - `working_steps = 2`
  - `resolved_working_steps = 2`
  - feature:
    - `feature_type = a:SlotSide`
    - `depth_spec = MillingDepthSpec(is_through=False, target_depth=10)`
    - `tool_width = 3.8`
    - `slot_angle = 1.5707963267948966`
    - extremos `a:WoodruffSlotEndType`, radio `60`
  - geometria:
    - `family = LineHorizontal`
    - inicio `(7.55, 570, 0)`
    - fin `(341.55, 570, 0)`
  - toolpaths:
    - `Approach`: `(7.55, 570, 38)` -> `(7.55, 570, 8)`
    - `TrajectoryPath`: `(7.55, 570, 8)` -> `(341.55, 570, 8)`
    - `Lift`: `(341.55, 570, 8)` -> `(341.55, 570, 38)`
- Validaciones ejecutadas:
  - `py -3 -m py_compile tools\synthesize_pgmx.py tools\pgmx_adapters.py tools\pgmx_snapshot.py`
  - sintesis programatica de `Fondo_349p1x580x18_Origen_5_5_25_Ranura.pgmx`
  - lectura del `.pgmx` sintetizado con `pgmx_snapshot`
  - prueba negativa de ranura vertical:
    - resultado esperado: `ValueError`
    - mensaje: `Sierra Vertical X solo permite lineas horizontales`
  - `git diff --check` sobre codigo y documentacion actualizados

### Ronda 29 - Comparacion `Fondo_Original` vs `Fondo_Girado`

- Estado: completado
- Archivos estudiados:
  - `archive/maestro_examples/Fondo_Original.pgmx`
  - `archive/maestro_examples/Fondo_Girado.pgmx`
- Correccion previa al analisis:
  - `tools/pgmx_snapshot.py` asumía `SweptShape` en todas las features
  - `RoundHole` no tiene `SweptShape`, por lo que `Fondo_Original.pgmx`
    rompia la lectura normalizada
  - se corrigio el snapshot para tolerar features sin `SweptShape`
  - `docs/pgmx_snapshot_help.md` queda actualizado con esa regla
- Estructura comun:
  - `piece_name = Fondo`
  - `origin = (5, 5, 25)`
  - `depth = 18`
  - `planes = 6`
  - `geometries = 10`
  - `features = 10`
  - `operations = 10`
  - `working_steps = 11`
  - `resolved_working_steps = 11`
  - workplan:
    - `LAV_1`: escuadrado exterior
    - `XBO_1` a `XBO_8`: taladros superiores
    - `LAV_2`: ranura `SlotSide`
    - `XN`: paso administrativo final
- Transformacion observada:
  - `Fondo_Girado` es `Fondo_Original` rotado 90 grados
  - dimensiones:
    - original: `length = 580`, `width = 349.1`
    - girado: `length = 349.1`, `width = 580`
  - mapeo local validado:
    - `x_girado = 349.1 - y_original`
    - `y_girado = x_original`
  - el mapeo transforma todos los puntos de taladro y la ranura
- Escuadrado exterior `LAV_1`:
  - ambos usan:
    - `GeneralProfileFeature`
    - `BottomAndSideFinishMilling`
    - herramienta `1900 / E001`
    - `tool_width = 18.36`
    - `SideOfFeature = Left`
    - pasante con `Extra = 1`
    - `Approach Arc + Quote`, habilitado
    - `Retract Arc + Quote`, habilitado
    - `MachineFunction = PneumaticHood`
  - adaptacion:
    - original: `SquaringMillingSpec(start_edge=Right, winding=Clockwise)`
    - girado: `SquaringMillingSpec(start_edge=Top, winding=Clockwise)`
- Taladros:
  - ambos tienen 8 `RoundHole` sobre `Top`
  - `XBO_1` a `XBO_4`:
    - diametro `8`
    - profundidad no pasante `13`
  - `XBO_5` a `XBO_8`:
    - diametro `5`
    - profundidad no pasante `15`
  - las operaciones conservan `ToolKey` vacio:
    - `ID = 0`
    - `ObjectType = System.Object`
    - `Name = ""`
  - el adaptador los conserva como `DrillingSpec` con
    `tool_resolution = None`
- Ranura `LAV_2`:
  - ambos usan:
    - `feature_type = a:SlotSide`
    - herramienta `1899 / 082`
    - `Sierra Vertical X`
    - `Width = 3.8`
    - profundidad no pasante `10`
    - dos extremos `a:WoodruffSlotEndType`, radio `60`
    - `SideOfFeature = Right`
    - `MaterialPosition = Left`
  - `Fondo_Original`:
    - geometria nominal `LineVertical`
    - inicio `(570, 341.55, 0)`
    - fin `(570, 7.55, 0)`
    - toolpath efectivo:
      - `(568.1, 341.55, 8)` -> `(568.1, 7.55, 8)`
    - offset efectivo: `-1.9` en `X`
    - no es ejecutable con `Sierra Vertical X`
  - `Fondo_Girado`:
    - geometria nominal `LineHorizontal`
    - inicio `(7.55, 570, 0)`
    - fin `(341.55, 570, 0)`
    - toolpath efectivo:
      - `(7.55, 568.1, 8)` -> `(341.55, 568.1, 8)`
    - offset efectivo: `-1.9` en `Y`
    - es compatible con `Sierra Vertical X`
- Resultado del adaptador:
  - `Fondo_Original`:
    - `adapted = 9`
    - `unsupported = 1`
    - `ignored = 1`
    - `squaring_millings = 1`
    - `drillings = 8`
    - `slot_millings = 0`
    - no soportado: `LAV_2`, porque `SlotSide` con `Sierra Vertical X`
      requiere una recta horizontal sobre `Top`
  - `Fondo_Girado`:
    - `adapted = 10`
    - `unsupported = 0`
    - `ignored = 1`
    - `squaring_millings = 1`
    - `drillings = 8`
    - `slot_millings = 1`
- Hallazgo para sintesis:
  - para esta pieza, el giro correcto no debe tratarse como rotacion de
    `WorkpieceSetup/Placement`
  - se debe transformar la geometria local y tambien intercambiar dimensiones
  - para recuperar ejecutabilidad CNC, la ranura debe quedar horizontal en el
    sistema local final
  - regla practica: antes de emitir `SlotMillingSpec`, si el recorrido sale
    vertical, hay que evaluar una variante girada con el mapeo
    `(x, y) -> (width_original - y, x)`
- Validaciones ejecutadas:
  - `py -3 -m py_compile tools\pgmx_snapshot.py tools\synthesize_pgmx.py tools\pgmx_adapters.py`
  - lectura de ambos archivos con `read_pgmx_snapshot(...)`
  - adaptacion de ambos archivos con `adapt_pgmx_path(...)`

### Ronda 30 - Reparacion automatica de `SlotSide` vertical invalido

- Se implemento en `core/pgmx_processing.py` un flujo reusable para:
  - resolver la ruta real del PGMX asociado a una pieza
  - detectar `SlotSide` vertical sobre `Top` con herramienta `Sierra Vertical X`
  - sintetizar una variante girada 90 grados antihorario
  - reemplazar el PGMX original solo despues de validar el temporal generado
- La transformacion usada para la reparacion es:
  - dimensiones: `length_final = width_original`, `width_final = length_original`
  - puntos Top: `(x, y) -> (width_original - y, x)`
  - borde inicial de escuadrado: `Bottom -> Right -> Top -> Left -> Bottom`
- La reparacion conserva el orden del `MainWorkplan` usando
  `ordered_machinings`.
- La ventana de inspeccion de modulos ahora:
  - avisa cuando una fila tiene una ranura no ejecutable
  - marca el programa con `!`
  - ofrece `Corregir PGMX` para sintetizar y sobreescribir el archivo rotado
- Validaciones ejecutadas:
  - `py -3 -m py_compile app\ui.py core\pgmx_processing.py tools\pgmx_snapshot.py tools\synthesize_pgmx.py tools\pgmx_adapters.py`
  - deteccion: `Fondo_Original.pgmx -> 1`, `Fondo_Girado.pgmx -> 0`
  - reparacion sobre copia temporal de `Fondo_Original.pgmx`
  - resultado validado: `349.1 x 580 x 18`, `unsupported = 0`,
    `slot_millings = 1`, ranura horizontal `y = 570`

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
- Resuelta: la capa publica ya lee y escribe `GeomCartesianPoint`, y la V1 de
  `DrillingSpec` ya sintetiza `RoundHole + DrillingOperation +
  MachiningWorkingStep`.
- Resuelta parcialmente: en los taladros laterales, el estado con `ToolKey`
  vacio es previo a la seleccion de herramienta; una vez elegida la unica
  herramienta valida por cara, Maestro solo actualiza `Operation/ToolKey`.
- Abierta: falta decidir si la futura spec de taladro lateral debe:
  - derivar automaticamente `ToolKey` desde cara + diametro
  - o permitir override manual con validacion fuerte
- Abierta: en cara superior, `diameter` no alcanza para resolver la herramienta;
  al menos `D5` es ambiguo entre broca plana y broca lanza.
- Resuelta: Maestro si admite huecos en varias caras dentro de un unico
  `MainWorkplan`; `Pieza_Huecos_VariasCaras.pgmx` lo demuestra con `Top +
  Front + Back`.
- Resuelta parcialmente: un origen no nulo por si solo no explica el fallo del
  archivo sintetizado multicara; `Pieza_Huecos_VariasCaras_Origen_5_5_25.pgmx`
  muestra un caso manual valido donde solo cambia `WorkpieceSetup/Placement`.
- Abierta: sigue pendiente aislar que combinacion adicional hizo caer el
  archivo sintetizado multicara previo; despues de relevar casos manuales, la
  variable mas sospechosa pasa a ser `ToolKey` ya resuelto en ese contexto, o
  alguna diferencia secundaria de serializacion XML.

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
- para taladros laterales, evaluar si la spec publica debe resolver la
  herramienta en forma automatica con una tabla cerrada por cara:
  - `Front -> 058 / 1895`
  - `Back -> 059 / 1896`
  - `Right -> 060 / 1897`
  - `Left -> 061 / 1898`
- relevar casos manuales adicionales antes de generalizar:
  - cara superior con herramienta explicita
  - diametros distintos de `8`
  - operaciones laterales que no sean taladro
- para taladros superiores, evaluar una spec que modele ademas de `diameter`:
  - `bottom_condition`
  - `drill_family`
  - o una referencia de broca mas explicita
- relevar un caso manual multicara con herramienta ya seleccionada para
  confirmar si Maestro sigue aceptando `ToolKey` resuelto sin ajustes extra
- relevar un caso manual multicara con origen no nulo para desacoplar el efecto
  de `WorkpieceSetup/Placement`
- para taladros superiores, considerar como defaults de la futura spec:
  - `bottom_condition = flat` cuando no se indique otra cosa
  - si `through = true`, preferir `conical` cuando exista herramienta
    compatible
  - permitir fallback a `flat` para huecos pasantes de cualquier diametro
  - validar una solicitud explicita de `conical` contra la disponibilidad real
    del toolset
- relevar el mismo archivo superior despues de elegir herramienta en cada hueco
  para confirmar si Maestro vuelve a cambiar solo `Operation/ToolKey` o si en
  vertical tambien ajusta algo mas segun la familia de broca
