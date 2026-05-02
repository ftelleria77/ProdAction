# Memoria Actual - Generacion ISO

## Objetivo

Crear un subsistema separado para la futura traduccion `.pgmx -> .iso`, sin
mezclarlo con la app principal ni con `cnc_traceability/`.

## Estado Inicial

- El contrato CNC/ISO observado vive en `docs/iso_cnc_contract.md`.
- La memoria historica larga vive en `docs/iso_synthesis_temporary_memory.md`.
- La lectura/adaptacion PGMX ya existe en:
  - `tools/pgmx_snapshot.py`;
  - `tools/pgmx_adapters.py`.
- La politica de herramientas especiales ya esta documentada en
  `docs/iso_cnc_contract.md`.

## Implementacion Creada

- `pgmx_source.py` carga `.pgmx` mediante los adaptadores existentes y agrega
  advertencias para `E002`, `E005` y `E006`.
- `emitter.py` emite la cabecera ISO validada y los primeros bloques operativos
  MVP:
  - pieza sin operaciones;
  - taladros superiores (`Top DrillingSpec` y patrones `DrillingPatternSpec`)
    con herramientas verticales `001..007`;
  - taladros laterales D8 individuales y por patron (`Left`, `Right`, `Front`,
    `Back`).
- `comparator.py` compara ISO Maestro vs candidato con normalizacion simple.
- `cli.py` ofrece comandos de inspeccion, cabecera y comparacion.

## Validacion

- `ISO_MIN_001..006` comparan igual contra Maestro:
  - 84 lineas normalizadas contra 84;
  - 0 diferencias;
  - cubren taladro superior base, movimiento X/Y, cambio de largo/ancho y
    cambio de `origin_y`.
- `ISO_MIN_010..013` comparan igual contra Maestro:
  - `Left` y `Back`: 97 lineas normalizadas contra 97;
  - `Right` y `Front`: 88 lineas normalizadas contra 88;
  - 0 diferencias.
- Las piezas de `S:\Maestro\Projects\ProdAction\ISO` comparan igual contra sus
  ISO Maestro en `P:\USBMIX\ProdAction\ISO`:
  - `Pieza`: 49 lineas normalizadas contra 49;
  - `Pieza_001`: 202 lineas normalizadas contra 202;
  - `Pieza_002`: 169 lineas normalizadas contra 169;
  - `Pieza_003`: 226 lineas normalizadas contra 226;
  - `Pieza_004`: 144 lineas normalizadas contra 144;
  - `Pieza_004_Repeticiones`: 144 lineas normalizadas contra 144;
  - `Pieza_005`: 284 lineas normalizadas contra 284;
  - 0 diferencias en todos los casos.

## Proximo Paso

Avanzar con fresado lineal seguro usando `ISO_MIN_020..023`.
