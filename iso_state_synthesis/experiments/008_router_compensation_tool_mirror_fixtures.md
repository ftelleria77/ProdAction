# Experimento 008 - Espejos De Compensacion Por Herramienta Router

Fecha: 2026-05-07

## Proposito

Confirmar que las reglas de compensacion `OpenPolyline` con `SideOfFeature`
`Left/Right` y leads `Line/Arc` en modo `Down/Up` generalizan a las demas
herramientas `E00x`.

Este experimento parte de los casos ya validados:

- `Pieza_092`: `Left`, `Line/Down-Up`;
- `Pieza_093`: `Right`, `Line/Down-Up`;
- `Pieza_094`: `Left`, `Arc/Down-Up`;
- `Pieza_095`: `Right`, `Arc/Down-Up`.

## Generador

Generador reproducible:

```powershell
py -3 -m tools.studies.iso.router_compensation_tool_mirror_fixtures_2026_05_07 `
  --output-dir "S:\Maestro\Projects\ProdAction\ISO\router_compensation_tool_mirror_fixtures_2026-05-07"
```

Salida:

- carpeta:
  `S:\Maestro\Projects\ProdAction\ISO\router_compensation_tool_mirror_fixtures_2026-05-07`;
- `manifest.csv`;
- 24 archivos `.pgmx` generados;
- 4 archivos `E002` no generados por validacion preventiva del sintetizador.

## Matriz

Recorrido comun:

- placa `400 x 250 x 18`;
- origen `X=5`, `Y=5`, `Z=25`;
- `OpenPolyline`: `(150,0) -> (100,150) -> (300,100) -> (250,250)`;
- pasante con `extra_depth=0.5`;
- `radius_multiplier=2.0`;
- `overcut_length=0.5`, derivado de la profundidad pasante.

Fixtures:

| Codigo | Compensacion | Acercamiento | Alejamiento |
| --- | --- | --- | --- |
| `OPEN_POLY_LEFT_LINE_DU_R2` | `Left` / `G41` | `Line + Down` | `Line + Up` |
| `OPEN_POLY_RIGHT_LINE_DU_R2` | `Right` / `G42` | `Line + Down` | `Line + Up` |
| `OPEN_POLY_LEFT_ARC_DU_R2` | `Left` / `G41` | `Arc + Down` | `Arc + Up` |
| `OPEN_POLY_RIGHT_ARC_DU_R2` | `Right` / `G42` | `Arc + Down` | `Arc + Up` |

Herramientas generadas:

- `E001`
- `E003`
- `E004`
- `E005`
- `E006`
- `E007`

Herramienta pendiente manual:

- `E002`

Motivo: el sintetizador automatico de `.pgmx` mantiene validaciones
preventivas y bloquea `E002` porque el catalogo la clasifica como
`Sierra Horizontal`. Para el conversor ISO, si Maestro acepta el `.pgmx`, no se
debe bloquear por herramienta.

## Validacion Local

- `py -3 -m py_compile` del generador: correcto.
- `inspect-pgmx --summary` sobre los 24 generados: 24/24 correctos.
- `emit-candidate` sobre los 24 generados: 24/24 correctos.

## Pendiente

1. Crear manualmente, si corresponde, las 4 piezas `E002` equivalentes.
2. Procesar/exportar desde Maestro los ISO de todos los `.pgmx` disponibles.
3. Correr `compare-candidate` contra los ISO de Maestro.
4. Registrar si las diferencias, en caso de aparecer, son regla real por
   herramienta o limitacion del emisor.
