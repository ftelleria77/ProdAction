# Registro de Geometrias PGMX

Esta nota fija como identificar las familias geometricas manuales guardadas en
`archive/maestro_baselines` y que API usar para leerlas o reconstruirlas.

## API publica nueva

En `tools.synthesize_pgmx` quedaron disponibles:

- `read_pgmx_geometries(path)`
- `GeometryPrimitiveSpec`
- `GeometryProfileSpec`
- `build_line_geometry_primitive(...)`
- `build_arc_geometry_primitive(...)`
- `build_line_geometry_profile(...)`
- `build_circle_geometry_profile(...)`
- `build_composite_geometry_profile(...)`
- `build_compensated_toolpath_profile(...)`

Objetivo:
- inspeccionar un `.pgmx` sin mirar el nombre del archivo
- clasificar su geometria con una clave estable
- dejar serializadores base para `GeomTrimmedCurve`, `GeomCircle` y `GeomCompositeCurve`
- dejar tambien una capa unica de compensacion geometrica ya alineada con Maestro

## Reglas de identificacion

### 1. `GeomTrimmedCurve`

Se identifica por `i:type="a:GeomTrimmedCurve"` y un bloque raw de dos lineas:

```text
8 <param_start> <param_end>
1 <origin_x> <origin_y> <origin_z> <dir_x> <dir_y> <dir_z>
```

Regla importante:
- no hay que asumir `8 0 <length>`
- en varios casos horarios Maestro usa parametros negativos o invertidos
- para recuperar los puntos reales hay que evaluar:
  - `start = origin + direction * param_start`
  - `end = origin + direction * param_end`

Clasificacion:
- `LineVertical`: `x` constante
- `LineHorizontal`: `y` constante
- `Line`: cualquier otra recta

### 2. `GeomCircle`

Se identifica por `i:type="a:GeomCircle"` y una sola linea raw:

```text
2 <cx> <cy> <cz> <nx> <ny> <nz> <ux> <uy> <uz> <vx> <vy> <vz> <radius>
```

Reglas:
- el radio sale del ultimo valor
- el sentido sale del signo de `nz`
- `nz > 0` -> `CounterClockwise`
- `nz < 0` -> `Clockwise`

### 3. `GeomCompositeCurve`

Se identifica por `i:type="a:GeomCompositeCurve"` y una lista de miembros en
`_serializingMembers`.

Cada miembro se parsea de forma individual:
- `body[0] == 1` -> segmento lineal
- `body[0] == 2` -> arco

Clasificacion:
- `OpenPolyline`: todos los miembros son lineas y el perfil no cierra
- `OpenCompositeCurve`: mezcla de lineas/arcos y el perfil no cierra
- `ClosedPolylineCornerStart`: cierra, no tiene arcos y el arranque cae en esquina
- `ClosedPolylineMidEdgeStart`: cierra, no tiene arcos y el arranque cae en medio de lado
- `ClosedPolylineMidEdgeStartRounded`: cierra, tiene arcos y el arranque cae en medio de lado
- `ClosedPolylineRounded`: fallback cerrado con arcos si no se detecta arranque en medio

Reglas auxiliares:
- `is_closed`: el inicio del primer miembro coincide con el final del ultimo
- `start_mode=MidEdge`: la tangente de salida del ultimo miembro coincide con la
  tangente de entrada del primero
- `start_mode=Corner`: las tangentes no coinciden
- `winding`: sale del area firmada del recorrido muestreado
- `corner_radii`: radios unicos de los miembros tipo arco

## Familias manuales registradas

| Archivo | `classification_key` | Observacion |
| --- | --- | --- |
| `Pieza_LineaVertical.pgmx` | `LineVertical` | recta vertical simple |
| `Pieza_LineaHorizontal.pgmx` | `LineHorizontal` | recta horizontal simple |
| `Pieza_CirculoCentral_200_Antihorario.pgmx` | `Circle_CounterClockwise` | circulo centro `(200,200)` radio `200` |
| `Pieza_CirculoCentral_200_Horario.pgmx` | `Circle_Clockwise` | mismo circulo con normal invertida |
| `Pieza_PolilineaAbierta.pgmx` | `OpenPolyline` | 3 segmentos lineales |
| `Pieza_PolilineaCerrada_InicioEsquina_Antihorario.pgmx` | `ClosedPolylineCornerStart_CounterClockwise` | cerrado, arranque en esquina |
| `Pieza_PolilineaCerrada_InicioEsquina_Horario.pgmx` | `ClosedPolylineCornerStart_Clockwise` | mismo contorno, recorrido inverso |
| `Pieza_PolilineaCerrada_InicioMedio_Antihorario.pgmx` | `ClosedPolylineMidEdgeStart_CounterClockwise` | cerrado, arranque en medio de lado |
| `Pieza_PolilineaCerrada_InicioMedio_Horario.pgmx` | `ClosedPolylineMidEdgeStart_Clockwise` | mismo contorno, recorrido inverso |
| `Pieza_PolilineaCerrada_InicioMedio_EsquinaR10_Antihorario.pgmx` | `ClosedPolylineMidEdgeStartRounded_CounterClockwise` | mismo contorno con esquinas `R10` |
| `Pieza_PolilineaCerrada_InicioMedio_EsquinaR10_Horario.pgmx` | `ClosedPolylineMidEdgeStartRounded_Clockwise` | mismo contorno con esquinas `R10`, recorrido inverso |

## Uso rapido

Leer y clasificar un archivo:

```python
from pathlib import Path
from tools.synthesize_pgmx import read_pgmx_geometries

profiles = read_pgmx_geometries(Path("archive/maestro_baselines/Pieza_LineaVertical.pgmx"))
print(profiles[0].classification_key)
```

Construir perfiles geometricos para sintesis futura:

```python
from tools.synthesize_pgmx import (
    build_arc_geometry_primitive,
    build_circle_geometry_profile,
    build_composite_geometry_profile,
    build_line_geometry_primitive,
    build_line_geometry_profile,
)

linea = build_line_geometry_profile(200, 0, 200, 400)
circulo = build_circle_geometry_profile(200, 200, 200, winding="Antihorario")
contorno = build_composite_geometry_profile(
    [
        build_line_geometry_primitive(200, 100, 290, 100),
        build_arc_geometry_primitive(290, 100, 300, 110, 290, 110, winding="Antihorario"),
    ]
)
```

## Consecuencia para la sintesis

Antes de este registro, la sintesis quedaba demasiado acoplada a linea abierta
o polilinea abierta. A partir de ahora:

- la identificacion de geometria vive en codigo, no en los nombres de archivo
- las curvas horarias y antihorarias se leen con la misma logica
- ya existe una capa geometrica reusable para futuras familias cerradas y circulares
- la compensacion por `SideOfFeature` ya esta centralizada para:
  - lineas
  - arcos
  - circulos
  - polilineas abiertas
  - polilineas cerradas con esquinas vivas
  - polilineas cerradas redondeadas y otras curvas compuestas tangentes
