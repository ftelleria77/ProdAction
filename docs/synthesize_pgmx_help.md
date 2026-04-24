# Ayuda `tools.synthesize_pgmx`

Esta guia deja por escrito como usar la API publica de `tools/synthesize_pgmx.py`,
en que orden conviene llamarla y que reglas de trabajo seguimos para no perder el
hilo de lo ya validado en Maestro.

Estado de hito actual:
- sintetizador Maestro `v1.2`
- constante publica de version: `tools.synthesize_pgmx.SYNTHESIZER_VERSION`

## 1. Alcance actual

La API publica actual sirve para sintetizar `.pgmx` a partir de un baseline Maestro.
Ese baseline puede venir en cualquiera de estos formatos:
- `.pgmx`
- `Pieza.xml` con sus archivos asociados (`Pieza.epl`, `def.tlgx`)
- carpeta que contenga `Pieza.xml`

Opcionalmente tambien se puede pasar un `source_pgmx_path` como plantilla de
serializacion. Ese path acepta los mismos formatos.

Casos publicos soportados hoy:
- lectura de estado basico de pieza (`read_pgmx_state`)
- lectura y clasificacion de geometria base (`read_pgmx_geometries`)
- compensacion geometrica reusable (`build_compensated_toolpath_profile`)
- fresado lineal abierto (`LineMillingSpec`)
- fresado sobre polilinea lineal abierta o cerrada (`PolylineMillingSpec`)
- fresado circular cerrado (`CircleMillingSpec`)
- escuadrado exterior del contorno de pieza (`SquaringMillingSpec`)
- taladro puntual sobre punto (`DrillingSpec`)
- control de profundidad pasante/no pasante
- estrategias publicas `Unidireccional` y `Bidireccional` para:
  - linea simple via `LineMillingSpec`
  - polilinea lineal abierta o cerrada via `PolylineMillingSpec`
  - circulo cerrado via `CircleMillingSpec`
  - escuadrado via `SquaringMillingSpec`
- estrategia publica `Helicoidal` para:
  - circulo cerrado via `CircleMillingSpec`
- `Approach` y `Retract` con reglas ya volcadas desde Maestro y ya unificadas
  sobre la tangente de entrada/salida del toolpath efectivo
- `Area` de Parametros de Maquina, con `HG` por defecto

Casos que no deben asumirse como API publica estable si no estan documentados aqui:
- familias de feature distintas de `GeneralProfileFeature` y `RoundHole`
- cualquier mecanizado que no este construido con
  `LineMillingSpec`, `PolylineMillingSpec`, `CircleMillingSpec`,
  `SquaringMillingSpec` o `DrillingSpec`

Importante:
- la sintesis completa de feature + operation sigue expuesta hoy por
  `LineMillingSpec`, `PolylineMillingSpec`, `CircleMillingSpec`,
  `SquaringMillingSpec` y `DrillingSpec`
- la capa de compensacion sigue resolviendo lineas, arcos, circulos y curvas
  compuestas abiertas/cerradas como base de estas familias publicas

## 2. Flujo recomendado

Orden recomendado para usar el sintetizador:

1. Elegir un `baseline_path` limpio.
2. Si ya existe un caso manual estudiado en Maestro para esa misma familia, pasar tambien `source_pgmx_path`.
3. Leer o definir la pieza.
4. Construir la profundidad.
5. Construir `Approach` y `Retract`.
6. Construir uno o mas mecanizados (`LineMillingSpec`, `PolylineMillingSpec`,
   `CircleMillingSpec`, `SquaringMillingSpec` y/o `DrillingSpec`).
7. Construir el `PgmxSynthesisRequest`.
8. Ejecutar `synthesize_request(...)`.

Regla practica:
- `baseline_path` define el contenedor base.
- `source_pgmx_path` no reemplaza al baseline: solo aporta serializacion ya observada en Maestro cuando coincide con la familia del mecanizado.
- En este repo, el baseline principal versionado vive en `tools/maestro_baselines/Pieza.xml`
  y se completa con `Pieza.epl` y `def.tlgx`.
- `build_synthesis_request(...)` y la CLI usan `tools/maestro_baselines` como
  baseline por defecto si no se indica otro.
- Los `.pgmx` manuales de ingeniería inversa viven en `archive/maestro_examples`.
- la taxonomia de familias geometricas vive en `docs/pgmx_geometry_registry.md`

## 3. API publica

### `read_pgmx_state(path: Path) -> PgmxState`

Lee de un baseline Maestro:
- nombre de pieza
- largo
- ancho
- espesor
- origen X/Y/Z
- `execution_fields`

Usos tipicos:
- tomar dimensiones reales antes de sintetizar
- clonar el estado de una pieza manual
- evitar hardcodear origen y espesor

Nota importante:
- `origin_x/origin_y/origin_z` corresponde a `WorkpieceSetup/Placement`
- ese origen posiciona el setup en Maestro, pero no implica que las curvas de
  `Geometries`, `TrajectoryPath`, `Approach` o `Lift` vengan trasladadas en ese
  mismo sistema global

### `read_pgmx_geometries(path: Path) -> tuple[GeometryProfileSpec, ...]`

Lee la seccion `Geometries` de un baseline Maestro y clasifica cada geometria base sin depender
del nombre del archivo.

Casos identificados hoy:
- `Point`
- `LineVertical`
- `LineHorizontal`
- `Circle_CounterClockwise`
- `Circle_Clockwise`
- `OpenPolyline`
- `ClosedPolylineCornerStart_*`
- `ClosedPolylineMidEdgeStart_*`
- `ClosedPolylineMidEdgeStartRounded_*`

Regla importante:
- para curvas trimadas no hay que asumir `8 0 longitud`
- en varios casos horarios Maestro serializa con parametros negativos o invertidos
- la lectura correcta usa `origin + direction * param_start/param_end`

### `build_point_geometry_profile(...)`, `build_line_geometry_profile(...)`, `build_circle_geometry_profile(...)`, `build_composite_geometry_profile(...)`

Estas helpers no crean aun un mecanizado completo por si solas, pero dejan lista
la capa geometrica que va a usarse en futuras familias puntuales, cerradas y circulares.

Complementos utiles:
- `build_line_geometry_primitive(...)`
- `build_arc_geometry_primitive(...)`

Referencia detallada de familias y reglas de identificacion:
- `docs/pgmx_geometry_registry.md`

### `build_compensated_toolpath_profile(...) -> GeometryProfileSpec`

Firma simplificada:

```python
build_compensated_toolpath_profile(
    profile,
    *,
    side_of_feature=None,
    tool_width,
    z_value=None,
)
```

Objetivo:
- tomar una geometria nominal ya clasificada o construida
- aplicar la compensacion de `SideOfFeature`
- devolver el perfil efectivo que debe seguir el centro de la herramienta

Casos ya volcados al codigo:
- lineas
- arcos
- circulos
- polilineas abiertas
- polilineas cerradas con esquinas vivas
- polilineas cerradas con esquinas redondeadas y otras curvas compuestas tangentes

Reglas practicas:
- no mueve la geometria nominal del feature; construye la trayectoria compensada
- `z_value` permite bajar la trayectoria a la cota real de mecanizado
- en circulos, el toolpath sale como `GeomCompositeCurve` de 2 semicircunferencias,
  que es como Maestro serializa `TrajectoryPath`

### `build_milling_depth_spec(...) -> MillingDepthSpec`

Firma simplificada:

```python
build_milling_depth_spec(
    is_through: bool | None = None,
    *,
    target_depth: float | None = None,
    extra_depth: float | None = None,
)
```

Reglas:
- si no se pasa nada, queda pasante con `extra_depth=0`
- si `is_through=True`, `extra_depth` representa `Extra`
- si `is_through=False`, hay que indicar `target_depth`
- en no pasante, `target_depth` puede valer `0` para reflejar el estado manual
  neutro/default que Maestro guarda cuando un fresado recien creado todavia no
  tiene profundidad efectiva
- `extra_depth` no aplica a fresados no pasantes
- antes de sintetizar, el modulo valida contra `tools/tool_catalog.csv` que la
  profundidad total no supere `sinking_length` de la herramienta:
  - no pasante -> `target_depth`
  - pasante -> `espesor + extra_depth`

Regla validada en Maestro para la serializacion:
- no pasante:
  - `BottomCondition = GeneralMillingBottom`
  - `Depth.StartDepth = target_depth`
  - `Depth.EndDepth = target_depth`
  - no agrega expresiones extra sobre el feature
  - `cut_z = espesor - target_depth`
  - Maestro tambien puede guardar `target_depth = 0` como estado manual inicial;
    en ese caso la trayectoria queda en `cut_z = espesor`
- pasante:
  - `BottomCondition = ThroughMillingBottom`
  - `Depth.StartDepth = espesor_actual`
  - `Depth.EndDepth = espesor_actual`
  - agrega dos expresiones sobre el feature para ligar `StartDepth/EndDepth` al `DepthName` real de la pieza
  - `OvercutLength = extra_depth`
  - `cut_z = -extra_depth`

### `build_approach_spec(...) -> ApproachSpec`

Firma simplificada:

```python
build_approach_spec(
    enabled: bool | None = None,
    *,
    approach_type: str | None = None,
    mode: str | None = None,
    radius_multiplier: float | None = None,
    speed: float | None = None,
    arc_side: str | None = None,
)
```

Defaults relevantes:
- sin parametros: `Approach` deshabilitado
- si se habilita sin mas detalle: completa defaults coherentes observados en Maestro

Valores ya validados:
- `approach_type`: `Line`, `Arc`
- `mode`: `Down`, `Quote`
- `arc_side`: `Automatic`

### `build_retract_spec(...) -> RetractSpec`

Firma simplificada:

```python
build_retract_spec(
    enabled: bool | None = None,
    *,
    retract_type: str | None = None,
    mode: str | None = None,
    radius_multiplier: float | None = None,
    speed: float | None = None,
    arc_side: str | None = None,
    overlap: float | None = None,
)
```

Defaults relevantes:
- sin parametros: `Retract` deshabilitado
- si se habilita sin mas detalle: completa defaults coherentes observados en Maestro

Valores ya validados:
- `retract_type`: `Line`, `Arc`
- `mode`: `Up`, `Quote`
- `arc_side`: `Automatic`

### `build_unidirectional_milling_strategy_spec(...) -> UnidirectionalMillingStrategySpec`

Construye la estrategia publica `Unidireccional`.

Firma simplificada:

```python
build_unidirectional_milling_strategy_spec(
    *,
    connection_mode=None,
    allow_multiple_passes=None,
    axial_cutting_depth=None,
    axial_finish_cutting_depth=None,
)
```

Notas:
- `connection_mode` admite:
  - `Automatic`
  - `SafetyHeight` / `SalidaCota`
  - `InPiece` / `EnLaPieza`
- en `LineMillingSpec`, `Automatic` cae en `SafetyHeight`
- en `PolylineMillingSpec` cerrado y en `SquaringMillingSpec`, `Automatic`
  cae en `InPiece`
- si `axial_cutting_depth > 0` o `axial_finish_cutting_depth > 0`, la helper
  activa `allow_multiple_passes=True` automaticamente
- si no se indica nada, devuelve una estrategia valida sin multipaso

### `build_bidirectional_milling_strategy_spec(...) -> BidirectionalMillingStrategySpec`

Construye la estrategia publica `Bidireccional`.

Firma simplificada:

```python
build_bidirectional_milling_strategy_spec(
    *,
    allow_multiple_passes=None,
    axial_cutting_depth=None,
    axial_finish_cutting_depth=None,
)
```

Notas:
- comparte el mismo par axial:
  - `axial_cutting_depth` (`PH`)
  - `axial_finish_cutting_depth` (`UH`)
- si alguno de los dos es mayor que cero, la helper activa
  `allow_multiple_passes=True` automaticamente
- el `StrokeConnectionStrategy` queda fijado por ahora a `Straghtline`, que es
  lo observado en los casos manuales relevados

### `build_helical_milling_strategy_spec(...) -> HelicalMillingStrategySpec`

Construye la estrategia publica `Helicoidal`.

Firma simplificada:

```python
build_helical_milling_strategy_spec(
    *,
    axial_cutting_depth=None,
    allows_finish_cutting=None,
    axial_finish_cutting_depth=None,
)
```

Notas:
- por ahora esta familia queda validada solo para `CircleMillingSpec`
- `axial_cutting_depth` mapea a `PH`
- `allows_finish_cutting` mapea a `Habilitar pasada final`
- `axial_finish_cutting_depth` mapea a `UH`
- si no se indica nada:
  - `axial_cutting_depth = 0`
  - `allows_finish_cutting = True`
  - `axial_finish_cutting_depth = 0`
- si `allows_finish_cutting = False`, no se admite
  `axial_finish_cutting_depth > 0`
- en XML Maestro esta familia se serializa como `b:HelicMilling`

### `build_xn_spec(...) -> XnSpec`

Construye la spec publica `Xn`.

Firma simplificada:

```python
build_xn_spec(
    *,
    reference=None,
    x=None,
    y=None,
)
```

Notas:
- representa la operacion nula final del workplan
- no crea ni `feature` ni `operation`; solo agrega un `Executable i:type="Xn"`
- `reference` admite `Absolute/Absoluto` o `Relative/Relativo`
- si no se indica nada, usa los defaults operativos:
  - `reference = Absolute`
  - `x = -3700`
  - `y = nil`
- cuando `y = nil`, el sintetizador serializa
  `GeometryID = {ID=0, ObjectType=nil}`
- cuando `y` tiene valor, el sintetizador serializa `GeometryID = nil`
- el `Xn` sintetizado se escribe al final de `MainWorkplan/Elements`

### `build_line_milling_spec(...) -> LineMillingSpec | None`

Construye un fresado lineal de dos puntos.

Firma simplificada:

```python
build_line_milling_spec(
    line_x1,
    line_y1,
    line_x2,
    line_y2,
    line_feature_name,
    line_tool_id,
    line_tool_name,
    line_tool_width,
    line_security_plane,
    line_side_of_feature=None,
    line_is_through=None,
    line_target_depth=None,
    line_extra_depth=None,
    line_approach_enabled=None,
    line_approach_type=None,
    line_approach_mode=None,
    line_approach_radius_multiplier=None,
    line_approach_speed=None,
    line_approach_arc_side=None,
    line_retract_enabled=None,
    line_retract_type=None,
    line_retract_mode=None,
    line_retract_radius_multiplier=None,
    line_retract_speed=None,
    line_retract_arc_side=None,
    line_retract_overlap=None,
    line_milling_strategy=None,
)
```

Notas:
- si los cuatro puntos llegan en `None`, devuelve `None`
- si se informa la linea, hay que informar los cuatro valores
- `line_side_of_feature` admite `Center`, `Right`, `Left`
- `line_milling_strategy` admite:
  - `build_unidirectional_milling_strategy_spec(...)`
  - `build_bidirectional_milling_strategy_spec(...)`
  - `Helicoidal` no queda validada para linea simple
- la capa publica de estrategias para linea simple ya esta validada en:
  - `PH/UH`
  - `Central/Right/Left`
  - `Approach/Retract` lineales sobre multipaso

### `build_polyline_milling_spec(...) -> PolylineMillingSpec`

Construye un fresado sobre polilinea lineal abierta o cerrada.

Firma simplificada:

```python
build_polyline_milling_spec(
    points,
    feature_name=None,
    tool_id=None,
    tool_name=None,
    tool_width=None,
    security_plane=None,
    side_of_feature=None,
    is_through=None,
    target_depth=None,
    extra_depth=None,
    approach_enabled=None,
    approach_type=None,
    approach_mode=None,
    approach_radius_multiplier=None,
    approach_speed=None,
    approach_arc_side=None,
    retract_enabled=None,
    retract_type=None,
    retract_mode=None,
    retract_radius_multiplier=None,
    retract_speed=None,
    retract_arc_side=None,
    retract_overlap=None,
    milling_strategy=None,
)
```

Notas:
- necesita al menos dos puntos
- no admite segmentos de longitud cero
- si el ultimo punto coincide con el primero, la polilinea se interpreta como
  contorno cerrado
- la capa publica de estrategias sobre `PolylineMillingSpec` ya cubre
  polilineas lineales abiertas y cerradas
- para una sola recta sigue conviniendo `LineMillingSpec`, porque hace mas
  explicita la intencion del mecanizado
- `milling_strategy` admite:
  - `build_unidirectional_milling_strategy_spec(...)`
  - `build_bidirectional_milling_strategy_spec(...)`
  - `Helicoidal` no queda validada para polilinea lineal

### `build_circle_milling_spec(...) -> CircleMillingSpec`

Construye un fresado circular cerrado sobre `Top`.

Firma simplificada:

```python
build_circle_milling_spec(
    *,
    center_x,
    center_y,
    radius,
    winding=None,
    feature_name=None,
    tool_id=None,
    tool_name=None,
    tool_width=None,
    security_plane=None,
    side_of_feature=None,
    is_through=None,
    target_depth=None,
    extra_depth=None,
    approach_enabled=None,
    approach_type=None,
    approach_mode=None,
    approach_radius_multiplier=None,
    approach_speed=None,
    approach_arc_side=None,
    retract_enabled=None,
    retract_type=None,
    retract_mode=None,
    retract_radius_multiplier=None,
    retract_speed=None,
    retract_arc_side=None,
    retract_overlap=None,
    milling_strategy=None,
)
```

Notas:
- `center_x`, `center_y` y `radius` son obligatorios
- `radius` debe ser mayor que cero
- `winding` admite `CounterClockwise/Antihorario` o `Clockwise/Horario`
- `side_of_feature` admite `Center`, `Right`, `Left`
- en `CircleMillingSpec`, `side_of_feature` no reescribe la geometria nominal:
  conserva el circulo base y desplaza el radio efectivo del toolpath segun
  winding + `tool_width / 2`
- la capa publica de estrategias sobre `CircleMillingSpec` ya cubre:
  - contornos cerrados con multipaso `Unidireccional`
  - contornos cerrados con multipaso `Bidireccional`
  - desbaste `Helicoidal` con vuelta final opcional
- `milling_strategy` admite:
  - `build_unidirectional_milling_strategy_spec(...)`
  - `build_bidirectional_milling_strategy_spec(...)`
  - `build_helical_milling_strategy_spec(...)`

### `build_squaring_milling_spec(...) -> SquaringMillingSpec`

Construye un escuadrado exterior del contorno real de la pieza.

Firma simplificada:

```python
build_squaring_milling_spec(
    *,
    start_edge=None,
    winding=None,
    feature_name=None,
    tool_id=None,
    tool_name=None,
    tool_width=None,
    security_plane=None,
    is_through=None,
    target_depth=None,
    extra_depth=None,
    approach_enabled=None,
    approach_type=None,
    approach_mode=None,
    approach_radius_multiplier=None,
    approach_speed=None,
    approach_arc_side=None,
    retract_enabled=None,
    retract_type=None,
    retract_mode=None,
    retract_radius_multiplier=None,
    retract_speed=None,
    retract_arc_side=None,
    retract_overlap=None,
    milling_strategy=None,
)
```

Notas:
- no recibe puntos: toma el contorno desde `length` y `width` de la pieza del request
- `start_edge` admite `Bottom/Right/Top/Left` y equivalentes en espanol
- `winding` admite `CounterClockwise/Antihorario` o `Clockwise/Horario`
- deriva automaticamente la compensacion exterior:
  - `CounterClockwise -> SideOfFeature = Right`
  - `Clockwise -> SideOfFeature = Left`
- defaults validados si no se pasa nada:
  - herramienta `E001` / `tool_id = 1900` / `tool_width = 18.36`
  - pasante con `Extra = 1`
  - `Approach = Arc + Quote`, radio x2, `Automatic`
  - `Retract = Arc + Quote`, radio x2, `Automatic`
- hoy esta validado contra 8 casos manuales:
  - 4 bordes de arranque `MidEdgeStart`
  - 2 sentidos de recorrido (`CounterClockwise` y `Clockwise`)
- `milling_strategy` admite:
  - `build_unidirectional_milling_strategy_spec(...)`
  - `build_bidirectional_milling_strategy_spec(...)`
  - `Helicoidal` no queda validada para escuadrado
- decision de diseno actual:
  - para escuadrados con multipaso, la estrategia preferida es
    `Unidireccional`
  - en `Unidireccional` cerrado, el default `Automatic` se resuelve como
    `EnLaPieza`
- la geometria y el mecanizado efectivo coinciden con los casos manuales
  relevados; la parametrizacion interna de algunas curvas puede no quedar
  serializada byte a byte igual si no se parte de una plantilla manual

### `build_drilling_spec(...) -> DrillingSpec`

Construye un taladro puntual asociado a un `GeomCartesianPoint`.

Firma simplificada:

```python
build_drilling_spec(
    *,
    center_x,
    center_y,
    diameter,
    feature_name=None,
    plane_name=None,
    security_plane=None,
    is_through=None,
    target_depth=None,
    extra_depth=None,
    drill_family=None,
    tool_resolution=None,
    tool_id=None,
    tool_name=None,
)
```

Alcance validado hoy:
- caras soportadas: `Top`, `Front`, `Back`, `Right`, `Left`
- geometria base: `GeomCartesianPoint`
- feature: `RoundHole`
- operacion: `DrillingOperation`

Reglas publicas de la spec:
- `center_x/center_y` son coordenadas locales al plano indicado
- `diameter` es obligatorio
- `target_depth` / `is_through` / `extra_depth` reutilizan la semantica de
  `build_milling_depth_spec(...)`
- `feature_name` por defecto queda como `Taladrado`
- `drill_family` admite:
  - `Flat`
  - `Conical`
- `Countersunk/Abocinado` queda fuera de alcance por ahora porque todavia no hay
  un caso manual validado

Defaults y reglas derivadas:
- si no se indica `plane_name`, usa `Top`
- si no se indica `security_plane`, usa `20`
- si no se indica `drill_family`, por defecto queda `Flat`
- excepcion relevante:
  - si el hueco es pasante sobre `Top` y el diametro es `5`, la helper prefiere
    `Conical`
  - para el resto de los casos, si no se indica familia, queda `Flat`

Profundidad efectiva por cara:
- `Top` usa `dz1`
- `Front` y `Back` usan `dy1`
- `Right` y `Left` usan `dx1`

Regla validada en Maestro para la serializacion:
- no pasante:
  - `Depth.StartDepth = target_depth`
  - `Depth.EndDepth = target_depth`
  - no agrega expresiones si el taladro no es pasante
- pasante:
  - `BottomCondition = ThroughHoleBottom`
  - `Depth.StartDepth/EndDepth` queda igual al espesor util de la cara
  - agrega 2 expresiones sobre `Depth.StartDepth/EndDepth` hacia la variable
    correspondiente:
    - `dz1` en `Top`
    - `dy1` en `Front/Back`
    - `dx1` en `Right/Left`
  - `extra_depth` no aumenta el `Depth` declarado; extiende el `TrajectoryPath`
    por fuera de la cara opuesta

Familia de broca y `BottomCondition`:
- `Flat` sin herramienta seleccionada:
  - `BottomCondition = FlatHoleBottom`
- `Conical` sin herramienta seleccionada:
  - `BottomCondition = ConicalHoleBottom`
  - agrega `TipAngle = 0`
  - agrega `TipRadius = 0`
- `through`:
  - fuerza `BottomCondition = ThroughHoleBottom`
- caso especial validado:
  - en `Top + D5 + Conical`, una vez elegida la herramienta `007`, Maestro deja
    la familia conica expresada por `ToolKey` y por `Feature/Name`, pero
    normaliza `BottomCondition` a `FlatHoleBottom`

Resolucion de herramienta:
- `tool_resolution="None"`:
  - deja `ToolKey` vacio (`ID=0`, `ObjectType=System.Object`, `Name=""`)
- `tool_resolution="Auto"`:
  - superior:
    - `Flat D8 -> 001 / 1888`
    - `Flat D15 -> 002 / 1889`
    - `Flat D20 -> 003 / 1890`
    - `Flat D35 -> 004 / 1891`
    - `Flat D5 -> 005 / 1892`
    - `Flat D4 -> 006 / 1893`
    - `Conical D5 -> 007 / 1894`
  - laterales:
    - `Front D8 -> 058 / 1895`
    - `Back D8 -> 059 / 1896`
    - `Right D8 -> 060 / 1897`
    - `Left D8 -> 061 / 1898`
- `tool_resolution="Explicit"`:
  - usa `tool_id/tool_name` dados por el usuario
  - valida que existan en `tools/tool_catalog.csv`

Reglas practicas relevantes:
- el centro efectivo del taladro vive en `Feature/GeometryID`, no en
  `Operation/StartPoint`
- el `Approach` va desde el plano de seguridad hasta la cara de entrada
- `TrajectoryPath` va desde la cara de entrada hasta la profundidad efectiva
- `Lift` vuelve desde la profundidad efectiva hasta el mismo plano de seguridad
- la validacion contra `tools/tool_catalog.csv` aplica solo cuando la
  herramienta queda resuelta a una herramienta real; si `ToolKey` queda vacio,
  no hay chequeo de `sinking_length`

### `build_synthesis_request(...) -> PgmxSynthesisRequest`

Es el ensamblador del pedido completo.

Firma simplificada:

```python
build_synthesis_request(
    baseline_path=None,
    output_path=...,
    *,
    source_pgmx_path=None,
    piece=None,
    piece_name=None,
    length=None,
    width=None,
    depth=None,
    origin_x=None,
    origin_y=None,
    origin_z=None,
    execution_fields=None,
    line_millings=None,
    polyline_millings=None,
    circle_millings=None,
    squaring_millings=None,
    drillings=None,
    ordered_machinings=None,
    machining_order=None,
    xn=None,
)
```

Reglas:
- si no se indica `baseline_path`, usa `tools/maestro_baselines`
- si no se indica `execution_fields`, usa `HG` por defecto
- si no se pasa `piece`, toma el estado desde `source_pgmx_path` o desde el baseline
- se pueden combinar mecanizados lineales, por polilinea abierta, circulares,
  de escuadrado y de taladrado en un mismo request
- `ordered_machinings` permite insertar una secuencia exacta de specs publicos
  (`LineMillingSpec`, `PolylineMillingSpec`, `CircleMillingSpec`,
  `SquaringMillingSpec`, `DrillingSpec`) preservando ese orden de worksteps
- `machining_order` permite definir el orden de aplicacion de familias de
  mecanizado; por defecto es `line`, `polyline`, `circle`, `squaring`,
  `drilling`
- `xn` permite configurar el `Xn` final del workplan
- si no se indica `xn`, la request usa `build_xn_spec()` por defecto
- `baseline_path` y `source_pgmx_path` aceptan `.pgmx`, `Pieza.xml` o carpeta contenedora
- si se indican `origin_x/origin_y/origin_z`, se actualiza
  `WorkpieceSetup/Placement`
- cambiar el origen no traslada automaticamente las curvas internas del `.pgmx`;
  esas curvas siguen expresadas en coordenadas locales de pieza

### `synthesize_request(request) -> PgmxSynthesisResult`

Es la funcion principal del flujo programatico.

Hace:
- carga el baseline
- hidrata mecanizados si hay `source_pgmx_path`
- aplica el estado de pieza
- inserta features, operaciones, worksteps y toolpaths
- inserta o reemplaza el `Xn` final en `MainWorkplan/Elements`
- si la request no trae `xn`, usa `build_xn_spec()` por defecto
- escribe el `.pgmx`
- devuelve `output_path`, `piece`, `sha256` y el resumen de mecanizados pedidos

### `synthesize_pgmx(...) -> PgmxState`

Wrapper historico para llamadas antiguas.

Usarlo solo si hace falta compatibilidad.
Para codigo nuevo conviene:

```python
request = build_synthesis_request(...)
result = synthesize_request(request)
```

## 4. Reglas ya validadas en Maestro

### Generales

- `Area` usa `HG` por defecto.
- Antes de escribir el `.pgmx`, la seguridad de profundidad se valida contra
  `tools/tool_catalog.csv`:
  - no pasante: `target_depth <= sinking_length`
  - pasante: `espesor + Extra <= sinking_length`
  - si la herramienta no existe en el catalogo, la sintesis falla
- Si `Approach.IsEnabled=false`, Maestro conserva un toolpath vertical de entrada.
- Si `Retract.IsEnabled=false`, Maestro conserva un toolpath vertical de salida.
- `SideOfFeature` nunca mueve la geometria nominal del feature; solo la trayectoria
  efectiva de la herramienta.
- Las reglas de `Approach` y `Retract` ya quedaron unificadas sobre el toolpath
  efectivo:
  - toman `entry_point` y tangente de entrada para `Approach`
  - toman `exit_point` y tangente de salida para `Retract`
  - por eso la misma regla sirve para linea, polilinea abierta, escuadrado,
    contorno cerrado redondeado, arco o circulo compensado

### Compensacion: lineas

- `Center`: la trayectoria coincide con la linea nominal.
- `Right`: la trayectoria se desplaza `tool_width / 2` sobre la normal derecha
  del sentido geometrico de la linea.
- `Left`: la trayectoria se desplaza `tool_width / 2` sobre la normal izquierda.
- La regla esta centralizada en `build_compensated_toolpath_profile(...)` y es la
  misma que hoy usa la sintesis lineal.

### Compensacion: polilineas abiertas

- `Center`: la trayectoria coincide con la polilinea nominal.
- `Right` / `Left`: cada tramo se offsetea por `tool_width / 2`.
- En una esquina exterior para el lado elegido, Maestro agrega un arco tangente
  centrado en el vertice nominal.
- En una esquina interior para el lado elegido, Maestro recorta y une por
  interseccion de los segmentos offset.
- Esta regla ya esta reutilizada por la sintesis actual de `PolylineMillingSpec`.

### Compensacion: polilineas cerradas con esquinas vivas

- `Center`: la trayectoria coincide con el contorno nominal.
- Si la compensacion cae hacia el interior del contorno:
  - Maestro offsetea cada lado hacia adentro
  - resuelve las esquinas por interseccion
  - no agrega arcos
- Si la compensacion cae hacia el exterior:
  - Maestro offsetea hacia afuera
  - agrega un arco tangente de cuarto de circunferencia en cada vertice convexo
- La correspondencia interior/exterior depende del winding:
  - antihorario: `Right = exterior`, `Left = interior`
  - horario: `Right = interior`, `Left = exterior`

### Compensacion: curvas compuestas con esquinas redondeadas

- Las lineas se desplazan en paralelo como en una polilinea abierta.
- Los arcos conservan centro y sentido, pero su radio efectivo cambia segun:
  - `effective_radius = nominal_radius + offset_distance * normal_sign`
- Si el perfil original es tangente, la compensacion mantiene esa tangencia y no
  necesita insertar arcos extra.
- Esta es la regla usada para contornos cerrados redondeados y para futuras
  curvas compuestas tangentes.

### Compensacion: arcos y circulos

- En un arco simple, el radio efectivo cambia con la misma regla que en las
  curvas compuestas redondeadas.
- En un circulo:
  - antihorario: `Right = exterior`, `Left = interior`
  - horario: `Right = interior`, `Left = exterior`
- Maestro serializa `TrajectoryPath` del circulo como `GeomCompositeCurve` de
  2 semicircunferencias; el helper publica ya devuelve esa forma.

### Escuadrado antihorario con E001

Caso manual relevado en Maestro sobre una geometria:

- `ClosedPolylineMidEdgeStart_CounterClockwise`
- arranque en medio de lado
- sin arcos nominales

Regla importante:

- la serializacion observada del mecanizado no depende de las dimensiones
  absolutas de la pieza ni de su origen global
- depende de la familia geometrica, el winding, la correccion, la herramienta,
  la configuracion de profundidad/entrada/salida y el borde donde cae el
  `MidEdgeStart`
- hoy estan validadas 4 orientaciones equivalentes del mismo patron:
  - arranque en borde inferior
  - arranque en borde derecho
  - arranque en borde superior
  - arranque en borde izquierdo
- en las cuatro, la familia geometrica sigue siendo
  `ClosedPolylineMidEdgeStart_CounterClockwise`
- lo que rota es la tangente local de entrada/salida del toolpath efectivo

Configuracion relevada:

- herramienta `E001` (`tool_id = 1900`, `tool_width = 18.36`)
- `SideOfFeature = Right`
- pasante con `Extra = 1`
- `Approach = Arc + Quote`, `RadiusMultiplier = 2`, `ArcSide = Automatic`
- `Retract = Arc + Quote`, `RadiusMultiplier = 2`, `ArcSide = Automatic`

Serializacion observada:

- `BottomCondition = ThroughMillingBottom`
- `Depth.StartDepth/EndDepth` quedan ligados al `DepthName` real de la pieza
- `OvercutLength = 1`
- `TrajectoryPath` sale como `GeomCompositeCurve` con:
  - `5` tramos lineales
  - `4` arcos tangentes de cuarto de circunferencia en los vertices convexos
- para un contorno antihorario con `SideOfFeature = Right`, la compensacion cae
  al exterior del contorno
- `Approach` sale como `linea vertical + arco`
- `Lift` sale como `arco + linea vertical`
- los cuadrantes absolutos del arco no son fijos:
  - rotan con la tangente local de entrada/salida
  - en los 4 casos relevados aparecen dos serializaciones equivalentes:
    - `Approach 270 -> 360` y `Lift 0 -> 90`
    - `Approach 90 -> 180` y `Lift 180 -> 270`
- cambiar `origin_x/origin_y/origin_z` no altera estas curvas; solo mueve
  `WorkpieceSetup/Placement`

Uso practico:

- este patron ya quedo expuesto por `build_squaring_milling_spec(...)`
- el builder publico cubre:
  - `CounterClockwise + Right`
  - `Clockwise + Left`
  - los 4 bordes posibles de `MidEdgeStart`
- si hace falta clonar una serializacion manual puntual, `source_pgmx_path`
  sigue pudiendo usarse como referencia operativa aparte

### `Approach Line + Down`

- usa una sola recta oblicua
- parte desde `entry_point - direction * (tool_width / 2 * radius_multiplier)`
- termina en el punto de entrada del toolpath
- `direction` es la tangente de entrada del toolpath efectivo, no la de la
  geometria nominal sin compensar

### `Retract Line + Up`

- usa una sola recta oblicua
- parte en el punto de salida del toolpath
- termina en `exit_point + direction * (tool_width / 2 * radius_multiplier)`
- `direction` es la tangente de salida del toolpath efectivo

### `Arc + Quote`

- radio efectivo: `tool_width / 2 * (radius_multiplier - 1)`
- entrada: `linea vertical + arco`
- salida: `arco + linea vertical`
- la eleccion del semiplano del arco sale de la tangente de entrada/salida y del
  `SideOfFeature` ya resuelto sobre la trayectoria efectiva
- el cuadrante absoluto no es fijo:
  - rota con la tangente local del toolpath efectivo
  - por eso no conviene documentarlo como borde inferior/derecho/etc. sino como
    regla local sobre `entry_point`, `exit_point` y sus tangentes
- en los casos manuales validados de
  `ClosedPolylineMidEdgeStart_CounterClockwise + SideOfFeature=Right` se
  observaron dos variantes equivalentes segun la orientacion local:
  - `Approach 270 -> 360` y `Lift 0 -> 90`
  - `Approach 90 -> 180` y `Lift 180 -> 270`
- la misma logica sigue aplicando a otros sentidos (`Clockwise`) y otras
  correcciones a traves de la tangente local y del lado efectivo ya resuelto

### `Retract Arc + Up`

- radio efectivo: `tool_width / 2 * (radius_multiplier - 1)`
- el arco vive en el plano vertical definido por la direccion de salida y `Z`
- la direccion usada es la tangente de salida del toolpath efectivo
- antihorario:
  - arco `0 -> 90`, luego linea vertical
- horario:
  - arco `180 -> 270`, luego linea vertical

## 5. Ejemplos de uso

### Ejemplo minimo: leer una pieza

```python
from pathlib import Path
from tools.synthesize_pgmx import DEFAULT_BASELINE_XML_PATH, read_pgmx_state

state = read_pgmx_state(DEFAULT_BASELINE_XML_PATH)
```

### Ejemplo minimo: compensar una geometria nominal

```python
from tools.synthesize_pgmx import (
    build_circle_geometry_profile,
    build_compensated_toolpath_profile,
)

circulo = build_circle_geometry_profile(200, 200, 200, winding="Antihorario")
toolpath = build_compensated_toolpath_profile(
    circulo,
    side_of_feature="Right",
    tool_width=17.72,
    z_value=-2.0,
)
```

`toolpath` sale como curva compuesta de 2 semiarcos, lista para serializar como
`TrajectoryPath`.

### Ejemplo minimo: linea central pasante

```python
from pathlib import Path
from tools.synthesize_pgmx import (
    build_line_milling_spec,
    build_synthesis_request,
    synthesize_request,
)

line = build_line_milling_spec(
    line_x1=200.0,
    line_y1=0.0,
    line_x2=200.0,
    line_y2=400.0,
    line_feature_name="DIVISION_CENTRAL",
    line_tool_id="1903",
    line_tool_name="E004",
    line_tool_width=4.0,
    line_security_plane=20.0,
    line_side_of_feature="Center",
    line_is_through=True,
    line_extra_depth=0.5,
)

request = build_synthesis_request(
    output_path=Path("archive/maestro_examples/Pieza_sintetizada.pgmx"),
    piece_name="Pieza",
    length=400.0,
    width=400.0,
    depth=25.0,
    origin_x=5.0,
    origin_y=5.0,
    origin_z=25.0,
    line_millings=[line],
)

result = synthesize_request(request)
print(result.output_path)
print(result.sha256)
```

### Ejemplo minimo: linea central con estrategia `Unidireccional`

```python
from pathlib import Path
from tools.synthesize_pgmx import (
    build_line_milling_spec,
    build_synthesis_request,
    build_unidirectional_milling_strategy_spec,
    synthesize_request,
)

line = build_line_milling_spec(
    line_x1=400.0,
    line_y1=0.0,
    line_x2=400.0,
    line_y2=760.0,
    line_feature_name="LINEA_CENTRAL",
    line_tool_id="1901",
    line_tool_name="E004",
    line_tool_width=4.0,
    line_security_plane=20.0,
    line_side_of_feature="Center",
    line_is_through=True,
    line_extra_depth=1.0,
    line_milling_strategy=build_unidirectional_milling_strategy_spec(
        connection_mode="InPiece",
        axial_cutting_depth=5.0,
        axial_finish_cutting_depth=10.0,
    ),
)

request = build_synthesis_request(
    output_path=Path("archive/maestro_examples/Pieza_linea_unidireccional.pgmx"),
    piece_name="Pieza",
    length=800.0,
    width=760.0,
    depth=18.0,
    origin_x=5.0,
    origin_y=5.0,
    origin_z=9.0,
    line_millings=[line],
)

result = synthesize_request(request)
print(result.output_path)
```

### Ejemplo minimo: polilinea abierta con tool side compensation

```python
from pathlib import Path
from tools.synthesize_pgmx import (
    build_polyline_milling_spec,
    build_synthesis_request,
    synthesize_request,
)

polyline = build_polyline_milling_spec(
    points=[
        (250.0, 0.0),
        (125.0, 250.0),
        (375.0, 250.0),
        (250.0, 500.0),
    ],
    feature_name="Fresado",
    tool_id="1902",
    tool_name="E003",
    tool_width=9.52,
    side_of_feature="Right",
    is_through=True,
    extra_depth=0.5,
)

request = build_synthesis_request(
    output_path=Path("archive/maestro_examples/Pieza_polilinea.pgmx"),
    piece_name="Pieza",
    length=500.0,
    width=500.0,
    depth=18.0,
    origin_x=5.0,
    origin_y=5.0,
    origin_z=9.0,
    polyline_millings=[polyline],
)

result = synthesize_request(request)
print(result.output_path)
```

### Ejemplo minimo: polilinea cerrada con estrategia `Bidireccional`

```python
from pathlib import Path
from tools.synthesize_pgmx import (
    build_bidirectional_milling_strategy_spec,
    build_polyline_milling_spec,
    build_synthesis_request,
    synthesize_request,
)

closed_polyline = build_polyline_milling_spec(
    points=[
        (150.0, 0.0),
        (0.0, 0.0),
        (0.0, 300.0),
        (300.0, 300.0),
        (300.0, 0.0),
        (150.0, 0.0),
    ],
    feature_name="CONTORNO",
    tool_id="1900",
    tool_name="E001",
    tool_width=18.36,
    side_of_feature="Left",
    is_through=True,
    extra_depth=1.0,
    approach_enabled=False,
    retract_enabled=False,
    milling_strategy=build_bidirectional_milling_strategy_spec(
        axial_cutting_depth=5.0,
        axial_finish_cutting_depth=10.0,
    ),
)

request = build_synthesis_request(
    output_path=Path("archive/maestro_examples/Pieza_polilinea_cerrada_bidireccional.pgmx"),
    piece_name="Pieza",
    length=300.0,
    width=300.0,
    depth=18.0,
    origin_x=5.0,
    origin_y=5.0,
    origin_z=25.0,
    polyline_millings=[closed_polyline],
)

result = synthesize_request(request)
print(result.output_path)
```

### Ejemplo completo: pieza escuadrada con doble camlock lateral

```python
from pathlib import Path
from tools.synthesize_pgmx import (
    build_drilling_spec,
    build_squaring_milling_spec,
    build_synthesis_request,
    synthesize_request,
)

request = build_synthesis_request(
    output_path=Path(
        "archive/maestro_examples/"
        "Pieza_450x320x18_EscuadradoAntihorario_DobleCamlockIzquierdoDerecho_64.pgmx"
    ),
    piece_name="Pieza_450x320x18_EscuadradoAntihorario_DobleCamlockIzquierdoDerecho_64",
    length=450,
    width=320,
    depth=18,
    origin_x=5,
    origin_y=5,
    origin_z=25,
    squaring_millings=(
        build_squaring_milling_spec(
            winding="Antihorario",
        ),
    ),
    drillings=(
        build_drilling_spec(
            feature_name="Camlock Superior Izquierdo Delantero",
            plane_name="Top",
            center_x=33,
            center_y=64,
            diameter=15,
            target_depth=15,
            tool_resolution="Auto",
        ),
        build_drilling_spec(
            feature_name="Camlock Superior Izquierdo Trasero",
            plane_name="Top",
            center_x=33,
            center_y=256,
            diameter=15,
            target_depth=15,
            tool_resolution="Auto",
        ),
        build_drilling_spec(
            feature_name="Camlock Superior Derecho Delantero",
            plane_name="Top",
            center_x=417,
            center_y=64,
            diameter=15,
            target_depth=15,
            tool_resolution="Auto",
        ),
        build_drilling_spec(
            feature_name="Camlock Superior Derecho Trasero",
            plane_name="Top",
            center_x=417,
            center_y=256,
            diameter=15,
            target_depth=15,
            tool_resolution="Auto",
        ),
        build_drilling_spec(
            feature_name="Camlock Izquierdo Delantero",
            plane_name="Left",
            center_x=64,
            center_y=9,
            diameter=8,
            target_depth=28,
            tool_resolution="Auto",
        ),
        build_drilling_spec(
            feature_name="Camlock Izquierdo Trasero",
            plane_name="Left",
            center_x=256,
            center_y=9,
            diameter=8,
            target_depth=28,
            tool_resolution="Auto",
        ),
        build_drilling_spec(
            feature_name="Camlock Derecho Delantero",
            plane_name="Right",
            center_x=64,
            center_y=9,
            diameter=8,
            target_depth=28,
            tool_resolution="Auto",
        ),
        build_drilling_spec(
            feature_name="Camlock Derecho Trasero",
            plane_name="Right",
            center_x=256,
            center_y=9,
            diameter=8,
            target_depth=28,
            tool_resolution="Auto",
        ),
    ),
)

result = synthesize_request(request)
print(result.output_path)
print(result.sha256)
```

Lectura conceptual del ejemplo:
- la pieza se define en el `request`
- el escuadrado completo vive en un `SquaringMillingSpec`
- cada hueco vive en un `DrillingSpec`
- `tool_resolution="Auto"` deja que el sintetizador resuelva la herramienta
  correcta segun cara, diametro y familia observada
- como no se indica `baseline_path`, se usa `tools/maestro_baselines`

## 6. Reglas de trabajo para no perder el hilo

Estas reglas aplican cada vez que se trabaja con esta herramienta:

- Antes de inferir una regla nueva, revisar esta guia y los README del repo.
- Toda la generacion `.pgmx` del repo debe resolverse desde `tools/synthesize_pgmx.py`.
- El baseline principal versionado del repo es `tools/maestro_baselines/Pieza.xml`
  junto con `Pieza.epl` y `def.tlgx`.
- Los estudios manuales y casos de comparación deben guardarse en `archive/maestro_examples`.
- Las salidas sintéticas de prueba también conviene escribirlas en `archive/maestro_examples`.
- Si el usuario pide solo generar una pieza, no cambiar codigo.
- Si ya existe un caso manual estudiado, usarlo como `source_pgmx_path` antes de inventar serializacion nueva.
- No asumir que un caso "parecido" ya quedo resuelto: confirmar si la familia publica es linea o polilinea.
- Para reglas de correccion geometrica, usar primero `build_compensated_toolpath_profile(...)`
  y recien despues decidir si hace falta una API publica nueva de mecanizado.
- Cuando aparezca un fallo de Maestro, revisar primero:
  - serializacion XML final
  - `xsi:type` y namespaces
  - referencias internas
  - si el caso se esta construyendo con la familia correcta (`LineMillingSpec` vs `PolylineMillingSpec`)

## 7. Fuente de verdad

La fuente principal para el uso del sintetizador pasa a ser este archivo:

- `docs/synthesize_pgmx_help.md`

Los README del repo solo deberian resumir y apuntar aqui.
