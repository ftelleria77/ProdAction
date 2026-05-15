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
- Configuracion de Maestro/Xilog: `iso_generation/machine_config/snapshot`.

## Politica De Configuracion De Maquina

El generador ISO debe usar los archivos de configuracion de Maestro y de la
maquina como fuente dimensional para herramientas, cabezales, offsets, campos de
trabajo, coordenadas de parqueo y parametros propios de operacion:

- `S:\Maestro\Cfgx`;
- `S:\Maestro\Tlgx`;
- `S:\Xilog Plus`.

El repo mantiene un snapshot inicial en `iso_generation/machine_config/snapshot`
y un script de sincronizacion en
`iso_generation/machine_config/sync_machine_config.ps1`. Cuando la maquina se
calibra, ese snapshot debe reemplazarse desde las rutas fuente. Las constantes
inferidas de ISO Maestro no deben crecer como fuente definitiva; si un valor
esta disponible en configuracion, el codigo debe leerlo desde el snapshot o
fallar explicitamente hasta que exista el lector correspondiente.

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
- casos especiales de `PH=5` fuera del fresado lineal `E004` ya observado;
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
patron en `Left`, `Right`, `Front` y `Back`. Tambien cubre ranura lineal
horizontal `082` en `Top` con correcciones laterales observadas, y fresado
lineal `E004` en `Top` horizontal o vertical, con corte simple y estrategia PH5
observada con pasadas multiples. Tambien cubre, como operaciones standalone,
polilinea abierta `E004` en `Top` con compensacion `Left`/`Right`, candidato de
polilinea abierta `E003` validada contra Maestro, y escuadrado `E001`
en `Top` empezando por `Bottom`, `Top`, `Left` o `Right`,
horario/antihorario, sin leads o con los leads `Line/Arc` observados. Tambien
cubre circulos `E004` centro/izquierda/derecha, horario/antihorario, PH5 y
helicoidal; polilineas abiertas `E004` con PH5 y leads `Line/Arc`; y
polilineas cerradas `E003/E004` con leads, PH5, offset lateral explicito y
arcos de esquina compensados. La combinacion soportada principal es `E001`
escuadrado seguido de perfiles superiores `E004`/`E003` observados, la
secuencia observada `E001 + taladros Top + ranura 082` de fondos simples de un
corpus real y los laterales `Lado_derecho`/`Lado_izquierdo` con polilineas `E001`,
ranura `082`, taladros Top antes/despues de la ranura y un grupo lateral. Las
demas combinaciones entre familias y las demas familias deben fallar
explicitamente hasta que se agreguen al MVP.

Nota de deuda tecnica: parte de `emitter.py` todavia contiene constantes
aprendidas por comparacion ISO. La regla nueva exige migrar esas constantes a
lectores sobre `machine_config/snapshot` antes de consolidar mas familias como
comportamiento estable.

La primera validacion compara `ISO_MIN_001..006` y `ISO_MIN_010..013` contra
los ISO Maestro postprocesados con normalizacion de nombre de programa, espacios
y lineas vacias.

La segunda validacion compara las piezas de `S:\Maestro\Projects\ProdAction\ISO`
contra sus ISO Maestro en `P:\USBMIX\ProdAction\ISO`: `Pieza`, `Pieza_001`,
`Pieza_002`, `Pieza_003`, `Pieza_004`, `Pieza_004_Repeticiones` y `Pieza_005`.
Todas comparan con 0 diferencias normalizadas.

La tercera validacion compara `ISO_MIN_020..023` contra Maestro:
fresado lineal `E004` base, variacion de `Y`, estrategia PH5 y cambio de
`origin_y`. Todos comparan con 0 diferencias normalizadas.

La cuarta validacion compara `Pieza_006..015` contra Maestro. Cubre ranuras
`082` con sentido directo/inverso y correcciones `Left`/`Right`, taladros
superiores no pasantes y pasantes con/sin extra, y fresado lineal `E004`
vertical no pasante. Todas comparan con 0 diferencias normalizadas.

La quinta validacion compara `Pieza_016..024` contra Maestro. Cubre polilinea
abierta `E004` con compensacion `Left`/`Right`, escuadrado `E001`
antihorario/horario sin leads, escuadrado `E001` antihorario/horario con leads
`Arc/Quote`, y la secuencia `E001` escuadrado + polilinea abierta `E004`
`Center`/`Left`/`Right`. Todas comparan con 0 diferencias normalizadas. La
matriz `Pieza`, `Pieza_001..024`, `Pieza_004_Repeticiones`,
`Pieza_DosHuecos`, `Pieza_DosHuecos_Origen_5_5_25`, `Pieza_Hueco8` y
`Pieza_Hueco8_Origen_5_5_25` compara exacta.

La sexta validacion compara toda la matriz raiz
`S:\Maestro\Projects\ProdAction\ISO\Pieza*.pgmx` contra
`P:\USBMIX\ProdAction\ISO`. En el barrido
`tmp/root_iso_generated_20260504_with_096_097`, los 103 archivos con ISO Maestro
de referencia comparan con 0 diferencias normalizadas. Esta validacion cubre
`Pieza_025..097`: circulos `E004`, polilineas abiertas/cerradas `E003/E004`,
escuadrados con leads `Line/Arc`, estrategias PH5 y combinaciones `E001` +
perfil superior.

Un corpus real se usa como validacion sin depender del CNC: carpetas
equivalentes en `S:\Maestro\Projects\ProdAction\ISO` y
`P:\USBMIX\ProdAction\ISO`. En el barrido
`tmp/real_corpus_iso_generated_20260504_complete`, el emisor genera y compara
exacto 84/84 ISO. La cobertura actual incluye escuadrados standalone `E001`,
escuadrados con taladros superiores/laterales observados, taladrado lateral de
una unica cara inmediatamente despues del perfil, 6 fondos simples con
`E001 + taladros Top + ranura 082` y 12 laterales `Lado_derecho`/
`Lado_izquierdo` con polilineas `E001`, ranura `082`, taladros Top
antes/despues de la ranura y un grupo lateral, mas los 7 `fajx` con `E001` +
taladros `Top` y laterales `Left/Right` intercalados, las 7 polilineas `E001`
de Torre/Alacena y el fresado lineal `E001` de `Divisor_Horiz`.

Los `WorkingStep` deshabilitados se ignoran para emision ISO y tambien se
marcan como vistos para no reinyectarlos como features huerfanas. Ese
comportamiento replica el corpus real, donde Maestro no postprocesa esos pasos aunque
las features sigan presentes en el `.pgmx`.

`Pieza_096` y `Pieza_097` replican la polilinea abierta de `Pieza_016..017`
cambiando la herramienta a `E003`; los `.pgmx` adaptan con `unsupported=0`, el
emisor genera candidato ISO y ambos comparan exactos contra Maestro: 100 lineas
normalizadas, 0 diferencias.
