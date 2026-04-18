# Ayuda `tools.pgmx_adapters`

Este modulo toma un `.pgmx` existente, lo pasa por `tools.pgmx_snapshot` y
trata de convertir cada mecanizado al subconjunto publico del sintetizador.

La idea es tener un puente practico para:

- refactorizar piezas manuales hacia specs reutilizables
- detectar rapido que partes ya pueden sintetizarse y cuales no
- construir un `PgmxSynthesisRequest` a partir del material soportado

## API publica

- `adapt_pgmx_snapshot(snapshot) -> PgmxAdaptationResult`
- `adapt_pgmx_path(path) -> PgmxAdaptationResult`
- `adaptation_to_dict(result) -> dict`
- `write_pgmx_adaptation_json(result, output_path, indent=2) -> Path`

Ademas, `PgmxAdaptationResult` expone:

- `entries`
- `adapted_entries`
- `unsupported_entries`
- `ignored_entries`
- `working_step_entries`
- `orphan_feature_entries`
- `line_millings`
- `polyline_millings`
- `squaring_millings`
- `drillings`
- `build_synthesis_request(output_path, baseline_path=None, source_pgmx_path=None, strict=False)`

## Que representa cada entrada

Cada `PgmxAdaptationEntry` representa una unidad de trabajo del `.pgmx`:

- si existe `WorkingStep`, la entrada nace del workplan y conserva su orden
- si una feature no aparece en el workplan, queda agregada al final como
  `entry_source = "feature"`

Campos importantes:

- `order_index`: posicion estable dentro del resultado
- `entry_source`: `working_step` o `feature`
- `status`: `adapted`, `unsupported` o `ignored`
- `spec_kind`: familia sintetizable detectada
- `spec`: dataclass publica del sintetizador cuando la adaptacion tuvo exito
- `reasons`: motivos concretos cuando no pudo adaptarse
- `warnings`: observaciones no bloqueantes

Las entradas `ignored` representan steps administrativos o de control que no
describen un mecanizado publico reutilizable. No bloquean
`build_synthesis_request(..., strict=True)`.

## Mapeos soportados hoy

- `RoundHole` + `DrillingOperation` -> `DrillingSpec`
- `GeneralProfileFeature` + `BottomAndSideFinishMilling` -> `LineMillingSpec`
  cuando la geometria es una recta simple
- `GeneralProfileFeature` + `BottomAndSideFinishMilling` -> `PolylineMillingSpec`
  cuando la geometria es una curva compuesta sin arcos
- `GeneralProfileFeature` + `BottomAndSideFinishMilling` -> `SquaringMillingSpec`
  cuando el contorno coincide con el perimetro completo de la pieza sobre `Top`

## Limitaciones actuales

- el fresado publico soportado sigue limitado a `Top` para linea, polilinea y
  escuadrado
- no existe todavia `CircleMillingSpec`
- curvas con arcos dentro de un perfil compuesto quedan marcadas como
  `unsupported`
- allowances distintos de cero no tienen representacion publica
- si `ApproachSecurityPlane` y `RetractSecurityPlane` difieren, la entrada
  queda `unsupported` porque la API publica solo expone uno
- `MachineFunctions` se preservan como `warning`, no como spec publico

## Uso programatico

Detectar que partes de una pieza ya son reusables:

```python
from pathlib import Path

from tools.pgmx_adapters import adapt_pgmx_path

result = adapt_pgmx_path(Path("archive/maestro_examples/Tapa.pgmx"))

print("adapted:", len(result.adapted_entries))
print("unsupported:", len(result.unsupported_entries))

for entry in result.entries:
    print(entry.order_index, entry.feature_name, entry.status, entry.spec_kind)
```

Construir un request listo para el sintetizador:

```python
from pathlib import Path

from tools.pgmx_adapters import adapt_pgmx_path

result = adapt_pgmx_path(Path("archive/maestro_examples/Tapa.pgmx"))
request = result.build_synthesis_request(
    Path("tmp/tapa_refactor.pgmx"),
    strict=True,
)
```

Si `strict=True`, el metodo falla cuando existe al menos una entrada
`unsupported`. Las entradas `ignored` no bloquean. Eso sirve para pipelines
donde queres garantizar que toda la geometria mecanizable ya entra dentro del
subset publico.

## Nota de orden y fidelidad

`entries` conserva el orden del workplan, pero `build_synthesis_request(...)`
arma el request en las cuatro familias publicas del sintetizador:

- `line_millings`
- `polyline_millings`
- `squaring_millings`
- `drillings`

Eso significa que hoy el adaptador sirve para:

- refactorizar geometria soportada a specs reutilizables
- explicar con precision lo no soportado
- re-sintetizar el subset publico soportado

Pero no garantiza aun reconstruir un workplan Maestro arbitrario con mezcla
intercalada de familias distintas.

## CLI

Imprimir la adaptacion en stdout:

```powershell
python -m tools.pgmx_adapters archive\maestro_examples\Tapa.pgmx
```

Guardar la adaptacion como JSON:

```powershell
python -m tools.pgmx_adapters archive\maestro_examples\Tapa.pgmx --output tmp\tapa_adaptation.json
```

## Flujo recomendado

1. Leer el `.pgmx` con `read_pgmx_snapshot(...)` cuando necesites inspeccion
   total o debugging profundo.
2. Pasar ese snapshot por `adapt_pgmx_snapshot(...)` para saber que subset ya
   puede refactorizarse.
3. Si el resultado es suficiente, usar `build_synthesis_request(...)`.
4. Si todavia hay entradas `unsupported`, usar `reasons` y `warnings` como
   backlog tecnico para ampliar el sintetizador.
