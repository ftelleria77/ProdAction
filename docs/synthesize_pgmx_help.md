# Ayuda `tools.synthesize_pgmx`

Esta guia deja por escrito como usar la API publica de `tools/synthesize_pgmx.py`,
en que orden conviene llamarla y que reglas de trabajo seguimos para no perder el
hilo de lo ya validado en Maestro.

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
- fresado sobre polilinea abierta (`PolylineMillingSpec`)
- control de profundidad pasante/no pasante
- `Approach` y `Retract` con reglas ya volcadas desde Maestro y ya unificadas
  sobre la tangente de entrada/salida del toolpath efectivo
- `Area` de Parametros de Maquina, con `HG` por defecto

Casos que no deben asumirse como API publica estable si no estan documentados aqui:
- escuadrados cerrados como tipo propio
- familias de feature distintas de `GeneralProfileFeature`
- cualquier mecanizado que no este construido con `LineMillingSpec` o `PolylineMillingSpec`

Importante:
- la sintesis completa de feature + operation sigue expuesta hoy por `LineMillingSpec`
  y `PolylineMillingSpec`
- la nueva capa de compensacion ya sabe resolver lineas, arcos, circulos y curvas
  compuestas abiertas/cerradas, aunque esas familias todavia no tengan un
  `...MillingSpec` publico propio

## 2. Flujo recomendado

Orden recomendado para usar el sintetizador:

1. Elegir un `baseline_path` limpio.
2. Si ya existe un caso manual estudiado en Maestro para esa misma familia, pasar tambien `source_pgmx_path`.
3. Leer o definir la pieza.
4. Construir la profundidad.
5. Construir `Approach` y `Retract`.
6. Construir uno o mas mecanizados (`LineMillingSpec` y/o `PolylineMillingSpec`).
7. Construir el `PgmxSynthesisRequest`.
8. Ejecutar `synthesize_request(...)`.

Regla practica:
- `baseline_path` define el contenedor base.
- `source_pgmx_path` no reemplaza al baseline: solo aporta serializacion ya observada en Maestro cuando coincide con la familia del mecanizado.
- En este repo, el baseline principal versionado vive en `archive/maestro_baselines/Pieza.xml`
  y se completa con `Pieza.epl` y `def.tlgx`.
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

### `read_pgmx_geometries(path: Path) -> tuple[GeometryProfileSpec, ...]`

Lee la seccion `Geometries` de un baseline Maestro y clasifica cada curva base sin depender
del nombre del archivo.

Casos identificados hoy:
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

### `build_line_geometry_profile(...)`, `build_circle_geometry_profile(...)`, `build_composite_geometry_profile(...)`

Estas helpers no crean aun un mecanizado completo por si solas, pero dejan lista
la capa geometrica que va a usarse en futuras familias cerradas y circulares.

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
- `extra_depth` no aplica a fresados no pasantes

Regla validada en Maestro para la serializacion:
- no pasante:
  - `BottomCondition = GeneralMillingBottom`
  - `Depth.StartDepth = target_depth`
  - `Depth.EndDepth = target_depth`
  - no agrega expresiones extra sobre el feature
  - `cut_z = espesor - target_depth`
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
)
```

Notas:
- si los cuatro puntos llegan en `None`, devuelve `None`
- si se informa la linea, hay que informar los cuatro valores
- `line_side_of_feature` admite `Center`, `Right`, `Left`

### `build_polyline_milling_spec(...) -> PolylineMillingSpec`

Construye un fresado sobre polilinea abierta.

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
)
```

Notas:
- la polilinea debe ser abierta
- necesita al menos dos puntos
- no admite segmentos de longitud cero

### `build_synthesis_request(...) -> PgmxSynthesisRequest`

Es el ensamblador del pedido completo.

Firma simplificada:

```python
build_synthesis_request(
    baseline_path,
    output_path,
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
)
```

Reglas:
- si no se indica `execution_fields`, usa `HG` por defecto
- si no se pasa `piece`, toma el estado desde `source_pgmx_path` o desde el baseline
- se pueden combinar varios mecanizados lineales y por polilinea en un mismo request
- `baseline_path` y `source_pgmx_path` aceptan `.pgmx`, `Pieza.xml` o carpeta contenedora

### `synthesize_request(request) -> PgmxSynthesisResult`

Es la funcion principal del flujo programatico.

Hace:
- carga el baseline
- hidrata mecanizados si hay `source_pgmx_path`
- aplica el estado de pieza
- inserta features, operaciones, worksteps y toolpaths
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
- antihorario con `SideOfFeature=Right`:
  - `Approach`: `270 -> 360`
  - `Lift`: `0 -> 90`
- horario con `SideOfFeature=Left`:
  - `Approach`: `90 -> 180`
  - `Lift`: `180 -> 270`

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
from tools.synthesize_pgmx import read_pgmx_state

state = read_pgmx_state(Path("archive/maestro_baselines/Pieza.xml"))
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
    baseline_path=Path("archive/maestro_baselines/Pieza.xml"),
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
    baseline_path=Path("archive/maestro_baselines/Pieza.xml"),
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

## 6. Reglas de trabajo para no perder el hilo

Estas reglas aplican cada vez que se trabaja con esta herramienta:

- Antes de inferir una regla nueva, revisar esta guia y los README del repo.
- Toda la generacion `.pgmx` del repo debe resolverse desde `tools/synthesize_pgmx.py`.
- El baseline principal versionado del repo es `archive/maestro_baselines/Pieza.xml`
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
