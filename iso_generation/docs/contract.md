# Contrato De Generacion ISO

## Proposito

`iso_generation/` es el laboratorio operativo para convertir conocimiento ISO
observado en codigo mantenible.

Su responsabilidad inicial es:

- leer un `.pgmx` existente;
- construir un snapshot/adaptacion usando `tools.pgmx_snapshot` y
  `tools.pgmx_adapters`;
- aplicar la politica de advertencias para herramientas sensibles;
- emitir solo bloques ISO cuyo contrato este documentado y validado;
- comparar el candidato contra ISO Maestro con normalizacion explicita.

No debe:

- generar trazas PGMX nuevas;
- modificar `.pgmx` de entrada;
- preparar archivos en `USBMIX`;
- marcar piezas como mecanizadas;
- conectarse a `cnc_traceability/` hasta que el MVP ISO sea confiable;
- emitir un `.iso` operativo parcial como si fuera productivo.

## Fuentes De Verdad

- Contrato observado: `docs/iso_cnc_contract.md`.
- Memoria historica: `docs/iso_synthesis_temporary_memory.md`.
- Snapshot PGMX: `tools/pgmx_snapshot.py`.
- Adaptacion PGMX: `tools/pgmx_adapters.py`.
- Toolset normalizado: `tools/tool_catalog.csv`.

## Politica De Herramientas

Hay dos fronteras distintas:

- Generacion automatica de trazas PGMX:
  - `E002` bloqueada hasta modelar Sierra Horizontal;
  - `E006` bloqueada hasta estudiar rectificado/vaciados superficiales;
  - `E005` permitida solo para division `en_juego` con regla establecida;
  - `E007` permitida como equivalente funcional de `E001`.
- Traduccion ISO de un `.pgmx` existente:
  - no bloquear `E002`, `E005` o `E006` solo por herramienta si la traza ya fue
    definida por Maestro o por un usuario competente de Maestro;
  - advertir sobre herramientas sensibles;
  - respetar la herramienta/trayectoria indicada cuando el contrato ISO este
    generalizado.

## MVP Del Traductor

El primer MVP debe emitir y comparar:

- cabecera ISO;
- marco `HG`;
- taladros superiores;
- taladros laterales simples;
- fresados lineales seguros;
- herramientas `E001`, `E003`, `E004`, `E007`;
- advertencias, no bloqueos automaticos, para `E002`, `E005`, `E006` en
  traduccion de PGMX existente.

Familias posteriores:

- escuadrado;
- polilineas;
- circulos;
- casos especiales de `PH=5`;
- Sierra Horizontal `E002`;
- rectificados/vaciados con `E006`.

## Comparacion

El comparador debe poder:

- normalizar o ignorar la primera linea de programa;
- normalizar espacios y lineas vacias;
- comparar lineas normalizadas;
- exponer diferencias concretas;
- evolucionar luego hacia comparacion por bloques operativos y variables ISO.

## Estado De Emision

El primer paso operativo implementado cubre cabecera, marco `HG`, cierre
estandar, piezas sin operaciones, bloques de taladros superiores
(`Top DrillingSpec` y patrones `DrillingPatternSpec`) con herramientas
verticales `001..007`, y bloques de taladros laterales D8 individuales y por
patron en `Left`, `Right`, `Front` y `Back`. Las demas familias deben fallar
explicitamente hasta que se agreguen al MVP.

La primera validacion compara `ISO_MIN_001..006` y `ISO_MIN_010..013` contra
los ISO Maestro postprocesados con normalizacion de nombre de programa, espacios
y lineas vacias.

La segunda validacion compara las piezas de `S:\Maestro\Projects\ProdAction\ISO`
contra sus ISO Maestro en `P:\USBMIX\ProdAction\ISO`: `Pieza`, `Pieza_001`,
`Pieza_002`, `Pieza_003`, `Pieza_004`, `Pieza_004_Repeticiones` y `Pieza_005`.
Todas comparan con 0 diferencias normalizadas.
