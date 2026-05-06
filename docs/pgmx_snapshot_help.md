# Ayuda `tools.pgmx_snapshot`

Este modulo expone una lectura integral de un `.pgmx` existente para usarlo como base de inspeccion, refactorizacion hacia el sintetizador y futuras modificaciones puntuales.

## API publica

- `read_pgmx_snapshot(path, include_xml_text=False) -> PgmxSnapshot`
- `snapshot_to_dict(snapshot) -> dict`
- `write_pgmx_snapshot_json(snapshot, output_path, indent=2) -> Path`

El snapshot incluye:

- estado general de pieza (`PgmxState`).
- `WorkPiece`.
- variables y expresiones.
- planos y placements.
- geometrias con perfil clasificado cuando aplica.
- features con refs, profundidad cruda e inferida, incluso cuando la familia no tiene `SweptShape`.
- features de canal con perfil, extremos, sobrecortes y angulo cuando aplica.
- features de repeticion con `ReplicationPattern` y `BaseFeature` cuando aplica.
- operaciones con herramienta, approach, retract, estrategia y toolpaths.
- `def.tlgx` embebido en el `.pgmx`, con herramientas, largos, velocidades y componentes de spindle cuando el contenedor lo incluye.
- working steps en el orden real del workplan.
- working steps resueltos, vinculando cada paso con feature, operacion, geometria y plano cuando esos datos existen.

## Uso programatico

```python
from pathlib import Path

from tools.pgmx_snapshot import read_pgmx_snapshot

snapshot = read_pgmx_snapshot(Path("archive/maestro_examples/Tapa.pgmx"))

print(snapshot.state)
print(snapshot.feature_by_id["2204"])
print(snapshot.operation_by_id["2203"])
print(snapshot.working_steps[-2].name)
print(snapshot.working_steps[-1].runtime_type)
print(snapshot.working_steps[-1].reference)
print(snapshot.working_steps[-1].x, snapshot.working_steps[-1].y)

for item in snapshot.resolved_working_steps:
    print(
        item.index,
        item.step.name,
        item.step.runtime_type,
        item.feature.feature_type if item.feature else "-",
        item.operation.operation_type if item.operation else "-",
        item.geometry.geometry_type if item.geometry else "-",
        item.plane.plane_type if item.plane else "-",
    )
```

Para patrones de huecos, `feature.replication_pattern` expone la definicion de repeticion y `feature.base_feature` expone el `RoundHole` base:

```python
for feature in snapshot.features:
    if feature.replication_pattern:
        print(
            feature.name,
            feature.replication_pattern.number_of_columns,
            feature.replication_pattern.number_of_rows,
            feature.replication_pattern.spacing,
            feature.replication_pattern.row_spacing,
            feature.base_feature.diameter if feature.base_feature else None,
        )
```

En taladros pasantes, `feature.depth_spec.extra_depth` se infiere desde la longitud del `TrajectoryPath` cuando Maestro deja `Operation/OvercutLength` en `0`. Por ejemplo, en una pieza de `18 mm`, un `RoundHole` pasante con `TrajectoryPath = 19` se expone como `extra_depth = 1`.

Si el `.pgmx` incluye `def.tlgx`, el snapshot lo toma como fuente primaria de herramientas para ese trabajo:

```python
print(snapshot.tooling_entry_name)
for tool in snapshot.embedded_tools:
    print(tool.name, tool.tool_offset_length, tool.technology.spindle_speed_standard)

for spindle in snapshot.embedded_spindles:
    print(spindle.spindle, spindle.ref_tool_id, spindle.translation_x, spindle.translation_z)
```

Los `working_steps` exponen tambien `runtime_type`, `reference`, `x` e `y`. En el paso administrativo final `Xn`, esos campos permiten leer directamente la posicion nula/parking definida por Maestro, por ejemplo `runtime_type = "Xn"`, `reference = "Absolute"`, `x = -3700`, `y = None` o `0`.

Si hace falta serializarlo para inspeccion externa:

```python
from pathlib import Path

from tools.pgmx_snapshot import read_pgmx_snapshot, write_pgmx_snapshot_json

snapshot = read_pgmx_snapshot(Path("archive/maestro_examples/Tapa.pgmx"))
write_pgmx_snapshot_json(snapshot, Path("tmp/tapa_snapshot.json"))
```

El JSON generado por `snapshot_to_dict(...)` y `write_pgmx_snapshot_json(...)` incluye una clave derivada `resolved_working_steps`. Esa clave no duplica ningun dato del `.pgmx`: solo cruza referencias para facilitar inspeccion y adaptacion hacia `tools.synthesize_pgmx`.

## CLI

Volcar un snapshot a stdout:

```powershell
python -m tools.pgmx_snapshot archive\maestro_examples\Tapa.pgmx
```

Guardar el snapshot en JSON:

```powershell
python -m tools.pgmx_snapshot archive\maestro_examples\Tapa.pgmx --output tmp\tapa_snapshot.json
```

Incluir tambien el XML crudo:

```powershell
python -m tools.pgmx_snapshot archive\maestro_examples\Tapa.pgmx --include-xml-text
```

## Nota de alcance

El snapshot no reemplaza al XML original: lo normaliza y resuelve relaciones entre entidades para trabajo de ingenieria. Si aparece un campo nuevo no mapeado todavia, el archivo fuente sigue siendo la referencia final.
