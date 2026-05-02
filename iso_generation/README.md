# Generacion ISO

Subsistema experimental para estudiar y construir la futura traduccion
`.pgmx -> .iso` de ProdAction.

No reemplaza a Maestro ni al postprocesador. Por ahora organiza la frontera de
trabajo: leer `.pgmx` existentes, adaptar lo que ya entiende el snapshot PGMX,
emitir solo reglas ISO ya validadas y comparar contra ISO Maestro.

## Estructura

| Ruta | Rol |
| --- | --- |
| `pgmx_source.py` | Lector/adaptador desde `tools.pgmx_snapshot` y `tools.pgmx_adapters`. |
| `emitter.py` | Emision ISO experimental para las familias ya validadas. |
| `comparator.py` | Normalizacion y comparacion Maestro vs candidato. |
| `cli.py` | CLI de inspeccion, cabecera y comparacion. |
| `docs/contract.md` | Contrato del subsistema y MVP previsto. |
| `memory/current-state.md` | Estado vivo de este subsistema. |

## Comandos

Desde la raiz del repo:

```powershell
python -m iso_generation --help
python -m iso_generation inspect-pgmx ruta\pieza.pgmx
python -m iso_generation emit-header ruta\pieza.pgmx
python -m iso_generation emit ruta\pieza.pgmx --output candidato.iso
python -m iso_generation compare maestro.iso candidato.iso
```

## Frontera Actual

- Lee y adapta PGMX mediante APIs existentes.
- Advierte sobre herramientas sensibles `E002`, `E005` y `E006`.
- Emite cabecera ISO con la regla validada:
  `DX=length+origin_x`, `DY=width+origin_y`, `DZ=depth+origin_z`, area `-HG`.
- Emite los primeros bloques operativos MVP:
  - pieza sin operaciones;
  - taladros superiores (`Top DrillingSpec` y patrones `DrillingPatternSpec`)
    con herramientas verticales `001..007`;
  - taladros laterales D8 individuales y patrones en `Left`, `Right`, `Front`
    y `Back`.
- Validado por comparacion exacta contra Maestro para `ISO_MIN_001..006`,
  `ISO_MIN_010..013`, `Pieza`, `Pieza_001`, `Pieza_002`, `Pieza_003`,
  `Pieza_004`, `Pieza_004_Repeticiones` y `Pieza_005`.
- No se conecta con `cnc_traceability/` hasta tener un MVP confiable.
