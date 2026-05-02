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
- `emitter.py` emite solo la cabecera ISO validada.
- `comparator.py` compara ISO Maestro vs candidato con normalizacion simple.
- `cli.py` ofrece comandos de inspeccion, cabecera y comparacion.

## Proximo Paso

Definir e implementar el MVP operativo por familias, empezando por cabecera y
marco `HG`, despues taladros superiores y laterales simples.
