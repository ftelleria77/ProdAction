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
  - polilinea abierta `E004` standalone en `Top`, con compensacion
    `Left`/`Right`.
  - escuadrado `E001` standalone en `Top`, con cualquier borde de arranque
    (`Bottom`, `Top`, `Left`, `Right`), winding horario/antihorario y sin
    leads o con leads `Arc/Quote` observados.
  - secuencia `E001` escuadrado + polilinea abierta `E004` en `Top`.
  - secuencia `E001` escuadrado + taladros superiores + ranura horizontal
    `082` en `Top`, validada en fondos simples de Cocina.
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
  `xilog_plus/Cfg/pheads.cfg`; origen Y del marco `HG` desde el campo `H` de
  `xilog_plus/Cfg/fields.cfg`; `safe_z` desde `xilog_plus/Cfg/Params.cfg`.
- El parking X/Y del cierre ISO se lee del paso administrativo `Xn` del
  `.pgmx` (`Reference/X/Y` capturados en `tools.pgmx_snapshot`). `Params.cfg`
  queda como fallback de maquina si faltara `Xn.X`.
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
- Tras leer `HG` desde `fields.cfg`, la relacion pendiente quedo cerrada para
  el corpus actual: `SHF[Y]=-1515.600` sale de `Y0` del campo `H`, y
  `%Or[0].ofY=-1515599.976` es ese mismo valor almacenado como `float32` y
  multiplicado por `1000`.
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
- La tanda fue postprocesada en Maestro y comparada contra el emisor para el
  contrato puntual de `G0 G53 Z...`: los 20 fixtures nuevos y `Pieza_002`,
  `Pieza_003`, `Pieza_005` coinciden en esas lineas. La regla refinada es
  `G53_Z_lateral = DZ_cabecera + 2*SecurityDistance + max(SHF_Z lateral
  involucrado)`.
  Con `DZ=43` eso explica `149.300`, `149.450` y `149.500`; con `DZ=50`
  produce `156.450/156.500`; con `DZ=58` produce `164.450/164.500`.
- Recomparacion contra la ventana de Xilog Plus: mandriles `58/59/60/61`
  tienen `Offset Z=-66.500/-66.500/-66.450/-66.300`, que explican
  `149.500/149.450/149.300` como `DZ+2*20+(-Offset Z)`. La regla sigue usando
  `max` porque en transiciones lateral-a-lateral debe considerar tambien el
  lateral anterior: `59 -> 61` con `DZ=43` emite `149.500`, no `149.300`.
- `SecurityDistance=20` esta en `Maestro/Cfgx/Programaciones.settingsx`, y las
  81 piezas PGMX con laterales revisadas tienen `ApproachSecurityPlane=20` y
  `RetractSecurityPlane=20`. El loader ya calcula la holgura lateral como
  `2 * SecurityDistance`; queda pendiente probar causalmente un valor distinto.
- La ventana `GENDATA` de Xilog Plus contiene varios `40.000`, pero sus
  etiquetas corresponden a velocidades de referencia de arcos/discontinuidades,
  no a una holgura `Z`.
- `Pieza_016..017` comparan igual contra Maestro: polilinea abierta `E004` con
  compensacion `Left` y `Right`, 100 lineas normalizadas contra 100, 0
  diferencias.
- `Pieza_018..021` comparan igual contra Maestro: escuadrado `E001`
  antihorario/horario, sin leads y con leads `Arc/Quote`, 103/105 lineas
  normalizadas segun variante, 0 diferencias.
- `Pieza_022..024` comparan igual contra Maestro: secuencia `E001`
  escuadrado + polilinea abierta `E004` `Center`/`Left`/`Right`, 142/147
  lineas normalizadas, 0 diferencias.
- La matriz `Pieza`, `Pieza_001..024`, `Pieza_004_Repeticiones`,
  `Pieza_DosHuecos`, `Pieza_DosHuecos_Origen_5_5_25`, `Pieza_Hueco8` y
  `Pieza_Hueco8_Origen_5_5_25` compara exacta: 30 piezas, 0 diferencias.
- El emisor ya acepta polilinea abierta standalone con `E003` ademas de `E004`
  usando los datos de herramienta del snapshot (`T3`, `SVL=111.500`,
  `SVR=4.760`). `Pieza_096` (`Left`) y `Pieza_097` (`Right`) ya fueron
  postprocesadas por Maestro y comparan exactas: 100 lineas normalizadas, 0
  diferencias en ambas.
- En la matriz raiz `S:\Maestro\Projects\ProdAction\ISO\Pieza*.pgmx`, todo
  archivo con par Maestro en `P:\USBMIX\ProdAction\ISO` compara exacto. El
  barrido `tmp/root_iso_generated_20260504_with_096_097` queda en `103 ok`,
  `0 diff`, `0 missing`, `0 error`.
- El emisor nativo ya cubre, en secuencia con `E001` cuando corresponde:
  circulos `E004` centro/izquierda/derecha, horario/antihorario, helicoidal,
  PH5 unidireccional/bidireccional y leads `Line/Arc`; polilineas abiertas
  `E004` con PH5 y leads `Line/Arc`; polilineas cerradas `E003/E004` con leads
  `Line/Arc`, PH5, offset lateral explicito y arcos de esquina cuando Maestro
  compensa por fuera; y escuadrados `E001` con leads `Line/Arc` en modos
  `Quote` y `Down/Up`.
- En el corpus Cocina, el emisor genera y compara exacto 84/84 piezas:
  escuadrados standalone, secuencias `E001` escuadrado + taladros superiores,
  secuencias con taladrado lateral de una unica cara tras perfil, y piezas que
  tenian `WorkingStep` deshabilitados que Maestro no postprocesa. Tambien
  cubre 6 fondos simples con `E001 + taladros Top + ranura 082` y 12 laterales
  `Lado_derecho`/`Lado_izquierdo` con polilineas `E001`, ranura `082`,
  taladros Top antes/despues de la ranura y un grupo lateral. Tambien cubre
  los 7 `fajx` con `E001` + taladros `Top` y laterales `Left/Right`
  intercalados, las 7 polilineas `E001` de Torre/Alacena y el fresado lineal
  `E001` de `mod 6 - Torre horno/Divisor_Horiz`. El barrido queda en
  `tmp/cocina_iso_generated_20260504_complete`: `84 ok`, `0 diff`, `0 error`.
- Para `E001 + taladros`, el emisor replica las reglas observadas de Cocina:
  herramientas verticales automaticas por familia/diametro cuando el PGMX trae
  herramienta `0`; transicion compacta de perfil superior a taladrado;
  reordenamiento Manhattan de taladros superiores solo cuando vienen despues de
  perfil; orden lateral por cara; y pausas `G4F0.500` dependientes de cara,
  profundidad y si el grupo lateral arranca luego de `Top`.
- El adaptador ignora `WorkingStep` deshabilitados y no los reinyecta como
  features huerfanas; esto evita emitir operaciones que Maestro deja fuera del
  ISO en Cocina.
- El adaptador de escuadrado conserva ahora la coordenada real de arranque
  cuando el perfil `.pgmx` no empieza exactamente en el centro del borde; esto
  cierra el caso `mod 5 - Bajo despensero/Tapa_despensero`.

## Proximo Paso

Sin acceso al CNC/Maestro, seguir desarrollando contra pares existentes
`S:\Maestro\Projects\ProdAction\ISO` y `P:\USBMIX\ProdAction\ISO`. La matriz
raiz `Pieza*.pgmx` ya quedo cerrada contra todos los pares disponibles y el
corpus Cocina tambien queda cerrado contra sus 84 pares.

- siguiente frente recomendado: elegir un nuevo corpus real con pares Maestro
  para abrir la proxima familia que no este cubierta por el contrato.
