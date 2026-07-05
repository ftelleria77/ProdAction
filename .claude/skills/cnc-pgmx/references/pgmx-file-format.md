# Formato del archivo .pgmx (en disco)

Un `.pgmx` **NO es texto plano**: es un **ZIP** (magic `PK\x03\x04`). `grep` directo no sirve — hay
que descomprimir (o leer con `zipfile`). Re-derivar esto cada vez es la trampa a evitar.

## Entradas del ZIP
- **`<nombre>.xml`** — el modelo de datos de mecanizado (lo importante). XML, namespace
  `http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel`.
- **`<nombre>.epl`** — normalmente vacío.
- **`def.tlgx`** — catálogo de herramientas embebido (= fuente de `pgmx/data/tool_catalog.csv`).

## Dónde vive cada dato en el XML
- **Campo de trabajo elegido en Maestro**: `<...ExecutionFields>HG</...>` dentro de
  `XilogHeaderParameters`. Valores `AB/DC/EF/HG` (áreas del 2×2 de la cama del Pratix S15).
  Determina el origen y el espejado de direcciones. (En ProdAction lo lee
  `iso/synthesis/_reader._execution_field`.)
- **Placement / origen de la pieza**: nodos `Placement` con `_xP/_yP/_zP` (y `_xN/_xVx`, etc.).
- **Header**: `DX/DY/DZ` (dimensiones), `BX/BY/BZ`.
- Los prefijos de namespace se asignan solos (`ns4:`, `ns6:`) → en XPath usar `{*}`/local-name,
  NO hardcodear prefijos. Los `xsi:type="b:..."` son strings literales (no se reescriben).

## Leer (código ProdAction)
- `pgmx.snapshot.read_pgmx_snapshot(path, *, include_xml_text=False)` → `PgmxSnapshot`
  (dataclasses frozen: `.state` con piece_name/length/width/depth/origin_*, `.machine_operations`).
- `pgmx.adapters.adapt_pgmx_path(path)` → `PgmxAdaptationResult` con `.snapshot` y `.adapted_entries`
  (specs ya traducidas). Es la puerta que usa el converter ISO (`iso/synthesis/_reader.read_pgmx`).

Lectura cruda puntual (sin pipeline, p. ej. un solo campo):
```python
import zipfile, re
with zipfile.ZipFile(path) as z:
    xml = z.read(next(n for n in z.namelist() if n.endswith(".xml"))).decode("utf-8", "replace")
field = re.search(r"<[^>]*ExecutionFields>([^<]*)</", xml).group(1)
```
Inspección manual: `unzip -o -q archivo.pgmx -d /tmp/x && grep ... /tmp/x/*.xml`.

## Escribir / sintetizar
- Specs en `pgmx/synthesis/` (`DrillingSpec`, `DrillingPatternSpec`, `LineMillingSpec`,
  `SlotMillingSpec`, `ParkSpec`, …; API pública en `pgmx/synthesis/__init__.py`).
- `pgmx.synthesis.common.program.build_synthesis_request(...)` → `PgmxSynthesisRequest`.
- `synthesize_request(request)` → `PgmxSynthesisResult` (hidrata specs → XML → ZIP `.pgmx`).
- Ejemplos vivos: `iso/machining_lab/nNNN_*/generate.py` y `pgmx/machining_lab/`.

## Flujo completo
```
.pgmx (ZIP) → read_pgmx_snapshot → PgmxSnapshot → adapt_pgmx_path → specs
            → build_synthesis_request → synthesize_request → .pgmx (ZIP) nuevo
```
