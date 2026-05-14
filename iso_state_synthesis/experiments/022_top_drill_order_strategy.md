# Estrategia De Ordenamiento De Top Drills

Fecha: 2026-05-14

Objetivo: revisar todos los ejemplos accesibles para separar diferencias reales
de ordenamiento de huecos superiores (`B-BH-002`) de diferencias de extraccion,
conteo o herramienta.

## Corpus Revisado

Herramienta base:

```powershell
py -3 -m tools.studies.iso.top_drill_corpus_order_analysis_2026_05_13
```

Corridas principales:

- DeMarco:
  - PGMX: `S:\Maestro\Projects\ProdAction\Prod 25-11-05 DeMarco`
  - ISO: `P:\USBMIX\ProdAction\Prod 25-11-05 DeMarco`
  - completos comparables: `224`
  - orden crudo PGMX: `1/224`
  - orden candidato actual: `215/224`
  - `neither_matches`: `9`
- Cazaux:
  - PGMX: `S:\Maestro\Projects\ProdAction\Prod 26-01-01 Cazaux`
  - ISO: `P:\USBMIX\ProdAction\Prod 26-01-01 Cazaux`
  - completos comparables: `60`
  - orden candidato actual: `60/60`
- ISO/Cocina:
  - PGMX: `S:\Maestro\Projects\ProdAction\ISO\Cocina`
  - ISO: `P:\USBMIX\ProdAction\ISO\Cocina`
  - completos comparables: `47`
  - orden candidato actual: `47/47`
- Agregado `S:\Maestro\Projects\ProdAction` contra `P:\USBMIX\ProdAction`:
  - PGMX/ISO revisados: `964`
  - filas con evidencia top drill: `606`
  - completos comparables: `453`
  - orden crudo PGMX: `106/453`
  - orden candidato actual: `442/453`
  - `count_mismatch` + `multiset_mismatch`: `153`
  - `neither_matches`: `11`

Los `count_mismatch` y `multiset_mismatch` no deben mezclarse con ordenamiento:
primero hay que resolver por que Maestro omite o replica huecos respecto del
PGMX. En especial aparecen muchos casos con PGMX `8` e ISO `0` o `4`.

## Observacion Principal

Maestro no sigue siempre el orden crudo de `WorkingStep`. En los comparables,
el orden crudo solo explica `106/453`, y gran parte de esos son bloques con
herramienta explicita donde el orden del PGMX parece conservarse.

Tampoco alcanza una regla lexicografica simple por `X` o por `Y`. La regla que
mejor explica los bloques automaticos observados es:

1. Si el bloque top drill trae herramienta explicita en todos los pasos,
   conservar el orden PGMX.
2. Si el bloque automatico tiene exactamente `4` huecos, una sola herramienta
   efectiva y profundidades mixtas, arrancar en maximo `X` y minimo `Y`, luego
   continuar por vecino mas cercano. Esta es la regla ya registrada en
   `019_b_bh_002_cazaux_top_drill_corner_start.md`.
3. Para el resto de bloques automaticos, elegir el primer hueco por menor
   distancia desde la posicion de arranque conocida. En el primer bloque, la
   mejor aproximacion observada es distancia al origen `(0, 0)`.
4. Luego continuar por vecino mas cercano, con desempate estable por
   `(X, Y, herramienta, step_id)`.

Esta hipotesis hibrida explica `451/453` comparables en el corpus agregado:
mejora los `9` residuos de DeMarco y no regresa ningun caso que ya estaba
explicado por la regla actual.

## Casos Que Mejora La Hipotesis

La mejora viene de cambiar el primer punto automatico desde `min X, min Y` a
`menor distancia al origen` en bloques sin herramienta explicita y fuera de la
excepcion de `4` huecos con profundidades mixtas.

Casos DeMarco que pasan a coincidir:

- `Prod 25-11-05 DeMarco\Cocina\mod 20 - Alacena baja Rinconera\TabiqueF6.pgmx`
- `Prod 25-11-05 DeMarco\Cocina\Parte 2\mod 30- Alacena altas\TabiqueF6.pgmx`
- `Prod 25-11-05 DeMarco\Cocina\Parte 2\mod 33 - Alcena cafe\Lat_Der.pgmx`
- `Prod 25-11-05 DeMarco\Cocina\Parte 2\mod 33 - Alcena cafe\Lat_Izq.pgmx`
- `Prod 25-11-05 DeMarco\Cocina\Parte 2\mod 33 - Alcena cafe\Puerta_Der.pgmx`
- `Prod 25-11-05 DeMarco\Garage\mod 1\TabiqueF6.pgmx`
- `Prod 25-11-05 DeMarco\Vestidor\mod 1,2,3\Lat_Izq.pgmx`
- `Prod 25-11-05 DeMarco\Vestidor\mod 7\TabiqueF6.pgmx`
- `Prod 25-11-05 DeMarco\Vestidor\mod 8\Lat_Izq.pgmx`

## Casos Restantes

Quedan `2` comparables que la hipotesis no explica:

- `Prod-2026-01 - Vargas\Cocina\Mod.5 - BM-ES-PC-250\Lat_Der_Cajon_Inf.pgmx`
- `Prod-2026-01 - Vargas\Cocina\Mod.5 - BM-ES-PC-250\Lat_Izq_Cajon_Inf.pgmx`

Patron observado:

```text
Maestro:
002@33,32 -> 002@33,218 -> 005@32,241 -> 005@432,241 -> 002@431,218 -> 002@431,32
```

Esto no es vecino mas cercano estricto. Desde `005@32,241`, el punto
`002@431,218` queda levemente mas cerca que `005@432,241`, pero Maestro elige
continuar por la banda superior con la herramienta `005` antes de bajar por el
lado derecho. La regla faltante parece ser un recorrido de perimetro o banda
exterior para patrones rectangulares de cajon, no un cambio de seleccion de
broca.

## Estrategia Recomendada

1. Implementar una mejora acotada en `_ordered_top_drill_block`:
   - no devolver el orden crudo solo porque el archivo tenga una unica familia;
   - conservar bloques con herramienta explicita;
   - conservar la excepcion de `4` huecos, una herramienta y profundidades
     mixtas;
   - reemplazar el arranque `min X/min Y` por arranque por distancia al origen
     para bloques automaticos generales.
2. Validar con:
   - Cazaux completo;
   - ISO/Cocina;
   - DeMarco;
   - agregado `S:\Maestro\Projects\ProdAction`;
   - raiz `Pieza*`, porque contiene bloques con herramienta explicita.
3. Dejar los dos Vargas como frente separado antes de codificar una regla de
   perimetro. Esa regla debe probarse contra todo el agregado porque puede
   competir con vecino mas cercano.

## Implementacion

Se ajusto `iso_state_synthesis/pgmx_source.py`:

- `_ordered_resolved_working_steps` ya no devuelve el orden crudo cuando la
  unica familia real es `top_drill`; ahora esos bloques tambien pasan por
  `_ordered_top_drill_block`.
- `_ordered_top_drill_block` conserva:
  - herramientas explicitas en orden PGMX;
  - bloques de `<=2` huecos ordenados por `(X, Y, herramienta, step_id)`;
  - la excepcion de `4` huecos automaticos, una herramienta efectiva y
    profundidades mixtas, con arranque `max X/min Y`.
- Para bloques automaticos generales se agrego `start_at_origin=True` en
  `_ordered_top_drill_nearest_neighbor`.
- `_top_drill_origin_start_key` elige el primer hueco por
  `distancia((0, 0), (X, Y))`, con desempate `(X, Y, herramienta, step_id)`.

## Validacion Posterior

Compilacion:

```powershell
py -3 -m py_compile iso_state_synthesis\pgmx_source.py
```

Orden top drill:

- DeMarco: `224/224` comparables explicados (`223` `candidate_matches` +
  `1` `raw_and_candidate_match`); antes habia `9` `neither_matches`.
- Cazaux: `60/60` comparables explicados; estable.
- ISO/Cocina: `47/47` comparables explicados; estable.
- Agregado `S:\Maestro\Projects\ProdAction`: `451/453` comparables
  explicados; quedan solo los `2` Vargas con patron de perimetro/banda
  exterior.

Comparacion ISO completa:

- DeMarco: `283` exactos, `2` `header_only`, `51` diferencias operativas,
  `2` `unsupported_candidate`, `46` sin ISO. Antes de esta mejora estaban en
  `274` exactos y `60` diferencias operativas.
- Cazaux: `82` exactos, `22` `header_only`; estable.
- ISO/Cocina: `84` exactos; estable.
- Raiz `Pieza*`: `217` exactos, `5` diferencias operativas; estable.

Primeros frentes restantes en DeMarco despues de esta mejora:

- `stage:slot_milling_prepare`: `18`
- `transition:T-XH-002`: `10`
- `block:B-BH-007`: `7`
- `block:B-RH-002`: `6`
- `block:B-BH-002`: `5`
- `transition:T-BH-003`: `4`
- `block:B-BH-005`: `1`

## Hipotesis De Fondo

El criterio de Maestro parece estar mas cerca de "arrancar desde la posicion
actual del cabezal y minimizar recorrido" que de "ordenar siempre por una
columna/fila fija". En el primer bloque top drill, cuando no hay posicion
previa util, el origen `(0, 0)` explica mejor el arranque que `min X/min Y`.
Cuando ya hay trabajos previos, el siguiente paso razonable es usar el ultimo
`G0/G1` conocido como origen dinamico del bloque en vez de una constante.
