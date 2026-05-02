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
- La configuracion dimensional de Maestro/Xilog debe ser fuente primaria para
  herramientas, campos de trabajo y coordenadas propias de la maquina.

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
  - ranura lineal horizontal `082` en `Top`, con correcciones `Left`/`Right`;
  - fresado lineal `E004` en `Top`, horizontal o vertical, incluido PH5 con
    pasadas multiples.
- `comparator.py` compara ISO Maestro vs candidato con normalizacion simple.
- `cli.py` ofrece comandos de inspeccion, cabecera y comparacion.
- `machine_config/` contiene el snapshot inicial de configuracion:
  - `snapshot/maestro/Cfgx` desde `S:\Maestro\Cfgx`;
  - `snapshot/maestro/Tlgx` desde `S:\Maestro\Tlgx`;
  - `snapshot/xilog_plus` con archivos `.cfg`, `.ini`, `.str`, `.tab`, `.tlg`
    y `.txt` desde `S:\Xilog Plus`;
  - `snapshot/manifest.csv` con hashes SHA256.
- `machine_config/loader.py` lee configuracion dimensional desde el snapshot:
  herramientas verticales `001..007`, taladros laterales D8 y ranura `082`
  desde `maestro/Tlgx/def.tlgx`; offsets de cabezal para `E004` desde
  `xilog_plus/Cfg/pheads.cfg`; `safe_z` desde `xilog_plus/Cfg/Params.cfg`.
- El parking X del cierre ISO se lee del paso administrativo `Xn` del `.pgmx`
  (`Reference/X/Y` capturados en `tools.pgmx_snapshot`). `Params.cfg` queda como
  fallback de maquina si faltara `Xn.X`.
- El emitter consume esos lectores y ya no mantiene tablas propias para largos,
  offsets, velocidades, avances ni mapeos por `tool_id` de las familias
  soportadas. Los valores ISO observados sin fuente inequivoca permanecen
  centralizados como politica en el loader.

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
- `ISO_MIN_020..023` comparan igual contra Maestro:
  - `ISO_MIN_020_LineE004_Base`: 94 lineas normalizadas contra 94;
  - `ISO_MIN_021_LineE004_Y60`: 94 lineas normalizadas contra 94;
  - `ISO_MIN_022_LineE004_PH5`: 108 lineas normalizadas contra 108;
  - `ISO_MIN_023_LineE004_OriginY10`: 94 lineas normalizadas contra 94;
  - 0 diferencias en todos los casos.
- `Pieza_006..015` comparan igual contra Maestro:
  - `Pieza_006..011`: ranura `082`, 90 lineas normalizadas contra 90;
  - `Pieza_012..014`: taladro superior, 84 lineas normalizadas contra 84;
  - `Pieza_015`: fresado lineal vertical `E004`, 94 lineas normalizadas contra 94;
  - 0 diferencias en todos los casos.
- Tras migrar las constantes dimensionales del emitter al loader de
  `machine_config/snapshot`, la misma matriz `ISO_MIN_001..006`,
  `ISO_MIN_010..013`, `ISO_MIN_020..023`, `Pieza`, `Pieza_001..015` y
  `Pieza_004_Repeticiones` vuelve a comparar exacta: 0 diferencias.
- Tras conectar `Xn.X` como parking X de cierre ISO, esa misma matriz vuelve a
  comparar exacta: 0 diferencias. En el corpus Cocina, `_source_park_x` lee
  valores variables confirmados como `-2500`, `-2292` y `-3700`; el corpus aun
  no compara completo porque requiere familias pendientes como escuadrados,
  polilineas y combinaciones de ranura/fresado.
- El 2026-05-02 se genero una tanda para investigar el origen de los parqueos
  intermedios `G0 G53 Z149.xxx` en taladros laterales:
  - generador reproducible:
    `tools/studies/iso/side_g53_z_fixtures_2026_05_03.py`;
  - `.pgmx` escritos en
    `S:\Maestro\Projects\ProdAction\ISO\side_g53_z_fixtures_2026-05-03`;
  - carpeta destino preparada para ISO Maestro:
    `P:\USBMIX\ProdAction\ISO\side_g53_z_fixtures_2026-05-03`;
  - matriz: 20 piezas, 10 con `400x300x25` y origen `(5,5,25)`, 10 con
    `400x300x18` y origen `(10,10,40)`;
  - cada pieza adapto con `unsupported=0`.

## Proximo Paso

Postprocesar en Maestro la tanda `side_g53_z_fixtures_2026-05-03`, copiar los
ISO resultantes a la carpeta `P:` preparada y comparar los `G0 G53 Z149.xxx`
contra dimensiones, origen, cara destino y posicion lateral. Luego avanzar con
`Pieza_016+`; la siguiente frontera detectada son polilineas `E004` y luego
escuadrados `E001`.
