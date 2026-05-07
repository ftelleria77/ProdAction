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

Salida inicial del generador:

- carpeta:
  `S:\Maestro\Projects\ProdAction\ISO\router_compensation_tool_mirror_fixtures_2026-05-07`;
- `manifest.csv`;
- 24 archivos `.pgmx` generados;
- 4 archivos `E002` no generados por validacion preventiva del sintetizador.

Revision posterior: los 4 `.pgmx` `E002` fueron agregados manualmente por el
usuario en la misma carpeta.

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

Herramientas presentes despues de la correccion manual:

- `E001`
- `E002`
- `E003`
- `E004`
- `E005`
- `E006`
- `E007`

Motivo: el sintetizador automatico de `.pgmx` mantiene validaciones
preventivas y bloquea `E002` porque el catalogo la clasifica como
`Sierra Horizontal`. Para el conversor ISO, si Maestro acepta el `.pgmx`, no se
debe bloquear por herramienta.

## Validacion Local

- `py -3 -m py_compile` del generador: correcto.
- Revision estructural de los 28 `.pgmx`: 28/28 correctos.
- `inspect-pgmx --summary` sobre los 28 `.pgmx`: 28/28 correctos.
- `emit-candidate` sobre los 28 `.pgmx`: 28/28 correctos.

## Validacion Contra Maestro

Los ISO de Maestro quedaron disponibles en:

`P:\USBMIX\ProdAction\ISO\router_compensation_tool_mirror_fixtures_2026-05-07`

Los ISO candidatos fueron generados en:

`S:\Maestro\Projects\ProdAction\ISO\router_compensation_tool_mirror_fixtures_2026-05-07\candidate_iso`

Reporte:

`S:\Maestro\Projects\ProdAction\ISO\router_compensation_tool_mirror_fixtures_2026-05-07\validation_report.csv`

Resultado del barrido:

- 28/28 `Resultado: igual`;
- 0 `Sin candidato`;
- 0 `Resultado: distinto`.

## Pendiente

1. Registrar si las diferencias, en una variante futura, son regla real por
   herramienta o limitacion del emisor.
