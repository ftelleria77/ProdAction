# Ayuda `tools.pgmx_snapshot`

Este modulo expone una lectura integral de un `.pgmx` existente para usarlo
como base de inspeccion, refactorizacion hacia el sintetizador y futuras
modificaciones puntuales.

## API publica

- `read_pgmx_snapshot(path, include_xml_text=False) -> PgmxSnapshot`
- `snapshot_to_dict(snapshot) -> dict`
- `write_pgmx_snapshot_json(snapshot, output_path, indent=2) -> Path`

El snapshot incluye:

- estado general de pieza (`PgmxState`)
- `WorkPiece`
- variables y expresiones
- planos y placements
- geometrias con perfil clasificado cuando aplica
- features con refs, profundidad cruda e inferida
- operaciones con herramienta, approach, retract, estrategia y toolpaths
- working steps en el orden real del workplan

## Uso programatico

```python
from pathlib import Path

from tools.pgmx_snapshot import read_pgmx_snapshot

snapshot = read_pgmx_snapshot(Path("archive/maestro_examples/Tapa.pgmx"))

print(snapshot.state)
print(snapshot.feature_by_id["2204"])
print(snapshot.operation_by_id["2203"])
print(snapshot.working_steps[-2].name)
```

Si hace falta serializarlo para inspeccion externa:

```python
from pathlib import Path

from tools.pgmx_snapshot import read_pgmx_snapshot, write_pgmx_snapshot_json

snapshot = read_pgmx_snapshot(Path("archive/maestro_examples/Tapa.pgmx"))
write_pgmx_snapshot_json(snapshot, Path("tmp/tapa_snapshot.json"))
```

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

El snapshot no reemplaza al XML original: lo normaliza y resuelve relaciones
entre entidades para trabajo de ingenieria. Si aparece un campo nuevo no mapeado
todavia, el archivo fuente sigue siendo la referencia final.
