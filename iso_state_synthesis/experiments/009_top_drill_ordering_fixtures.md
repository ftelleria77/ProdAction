# Experimento 009 - Ordenamiento De Top Drill Mixto

## Objetivo

Identificar que orden le da Maestro a series de huecos en cara superior cuando
conviven brocas `005`, `002` y `001`.

La tanda separa tres variables:

- orden fuente dentro del `.pgmx`;
- posicion geometrica de los huecos;
- contexto previo antes del bloque superior: sin router, `line_milling` o
  perfil `E001`.

No cambia el emisor. Sirve para decidir luego si
`iso_state_synthesis/pgmx_source.py::_ordered_top_drill_block` debe ordenar por
bandas horizontales, por cercania al trabajo previo, por orden fuente o por una
regla compuesta.

## Generador

```powershell
py -3 -m tools.studies.iso.top_drill_ordering_fixtures_2026_05_13 `
  --output-dir "S:\Maestro\Projects\ProdAction\ISO"
```

Archivos generados:

- `S:\Maestro\Projects\ProdAction\ISO\Pieza_209.pgmx`
- `S:\Maestro\Projects\ProdAction\ISO\Pieza_210.pgmx`
- `S:\Maestro\Projects\ProdAction\ISO\Pieza_211.pgmx`
- `S:\Maestro\Projects\ProdAction\ISO\Pieza_212.pgmx`
- `S:\Maestro\Projects\ProdAction\ISO\Pieza_213.pgmx`
- `S:\Maestro\Projects\ProdAction\ISO\Pieza_214.pgmx`
- `S:\Maestro\Projects\ProdAction\ISO\Pieza_209_214_TBH001_top_order_manifest.csv`

ISO esperados despues de postprocesar con Maestro:

- `P:\USBMIX\ProdAction\ISO\pieza_209.iso`
- `P:\USBMIX\ProdAction\ISO\pieza_210.iso`
- `P:\USBMIX\ProdAction\ISO\pieza_211.iso`
- `P:\USBMIX\ProdAction\ISO\pieza_212.iso`
- `P:\USBMIX\ProdAction\ISO\pieza_213.iso`
- `P:\USBMIX\ProdAction\ISO\pieza_214.iso`

## Geometria Aislada

La tanda usa una distribucion inspirada en `S016`, con dos bandas horizontales y
un bloque derecho separado:

| etiqueta | herramienta esperada | X | Y |
| --- | --- | ---: | ---: |
| `A` | `002` | `33` | `32` |
| `B` | `005` | `250.5` | `60` |
| `C` | `005` | `450.5` | `60` |
| `D` | `005` | `450.5` | `532` |
| `E` | `005` | `250.5` | `532` |
| `F` | `002` | `33` | `553` |
| `G` | `001` | `741` | `53` |
| `H` | `001` | `773` | `53` |
| `I` | `001` | `773` | `562` |
| `J` | `001` | `741` | `562` |

Orden sospechado desde `S016`:

`A -> B -> C -> D -> E -> F -> G -> H -> I -> J`

Los fixtures `Pieza_209` y `Pieza_211..214` escriben el `.pgmx` en orden fuente
intencionalmente mezclado:

`H -> A -> E -> C -> G -> F -> B -> J -> D -> I`

`Pieza_210` usa el orden inverso del sospechado para probar si Maestro respeta
el orden fuente.

## Casos

| pieza | contexto | foco |
| --- | --- | --- |
| `Pieza_209` | solo top drill | orden Maestro sin trabajo previo |
| `Pieza_210` | solo top drill | control de dependencia del orden fuente |
| `Pieza_211` | linea `E001` izquierda -> derecha antes del top drill | influencia de salida router a la derecha |
| `Pieza_212` | linea `E001` derecha -> izquierda antes del top drill | influencia de salida router a la izquierda |
| `Pieza_213` | perfil `E001` horario con `Arc+Quote` antes del top drill | contexto de perfil real previo |
| `Pieza_214` | perfil `E001` antihorario con `Arc+Quote` antes del top drill | control de sentido de perfil |

## Analisis

Despues de generar los ISO con Maestro:

```powershell
py -3 -m tools.studies.iso.top_drill_ordering_fixtures_2026_05_13 `
  --analyze-only `
  --manifest "S:\Maestro\Projects\ProdAction\ISO\Pieza_209_214_TBH001_top_order_manifest.csv"
```

El analizador produce:

`S:\Maestro\Projects\ProdAction\ISO\Pieza_209_214_TBH001_top_order_analysis.csv`

Columnas principales:

- `source_order`: orden dentro del `.pgmx`;
- `candidate_order`: orden actual de `_ordered_top_drill_block`;
- `maestro_order`: orden extraido del ISO de Maestro;
- `maestro_matches_source`;
- `maestro_matches_candidate`;
- `maestro_matches_suspected`.

## Resultado Con ISO Maestro

ISO disponibles el 2026-05-13:

- `Pieza_209`: Maestro conserva el orden fuente mezclado. El candidato tambien
  coincide porque no reordena cuando todo el archivo es `top_drill`.
- `Pieza_210`: Maestro conserva el orden fuente inverso. Confirma que en esta
  tanda no impone la serpentina sospechada cuando el `.pgmx` trae otro orden.
- `Pieza_211`: con linea `E001` izquierda -> derecha previa, Maestro conserva
  el orden fuente mezclado; el candidato actual reordena y falla.
- `Pieza_212`: con linea `E001` derecha -> izquierda previa, Maestro conserva
  el orden fuente mezclado; el candidato actual reordena y falla.
- `Pieza_213`: con perfil `E001` horario previo, Maestro conserva el orden
  fuente mezclado; el candidato actual reordena y falla.
- `Pieza_214`: con perfil `E001` antihorario previo, Maestro conserva el orden
  fuente mezclado; el candidato actual reordena y falla.

Resumen del CSV:

| grupo | piezas | Maestro vs fuente | Maestro vs candidato | Maestro vs orden sospechado |
| --- | --- | --- | --- | --- |
| solo `top_drill` | `209..210` | `2/2` | `2/2` | `0/2` |
| router previo -> `top_drill` | `211..214` | `4/4` | `0/4` | `0/4` |

El resultado local de `compare-candidate` antes de cambiar reglas fue:

- `Pieza_209..210`: `2/2` exactos;
- `Pieza_211..214`: `0/4` exactos, con diferencias masivas desde la primera
  preparacion de broca porque el candidato empieza por otro hueco.

## Lectura

La mini tanda no demuestra que Maestro ordene siempre por geometria. En estos
PGMX sinteticos, Maestro respeta el orden de `WorkingStep` del archivo aun con
router previo.

Esto corrige la interpretacion inicial de `S016`: la secuencia en bandas de
`Cocina / Lado_derecho` puede ser el orden ya presente en ese `.pgmx`, no una
optimizacion geometrica impuesta siempre por Maestro.

Tambien se probo localmente una regla global de preservar orden fuente en
`_ordered_top_drill_block`. La tanda nueva quedaba `6/6` exacta y la matriz
raiz quedaba `217/222` exacta, pero `Cocina` caia a `30/84`; por eso no se
mantiene ese cambio como regla global.

Estado estable conservado despues de esa prueba:

- matriz raiz `Pieza*`: `213/222` exactos; residuales `Pieza_181..185` y
  `Pieza_211..214`;
- `Cocina`: `65/84` exactos.

## Estado

Evidencia abierta. La conclusion util por ahora es que el orden ejecutable de
`top_drill` depende de mas informacion que la geometria aislada:

- en PGMX sinteticos `Pieza_209..214`, el orden fuente es autoridad;
- en `Cocina`, la heuristica por recorrido todavia explica mas casos que
  preservar orden fuente crudo.

Proximo paso recomendado: comparar en detalle el orden de `WorkingStep` crudo y
el orden ISO de una pieza real residual de `Cocina` para ubicar que metadato del
`.pgmx` distingue ambos escenarios antes de cambiar `_ordered_top_drill_block`.

## Seguimiento

El seguimiento con el corpus real Cazaux quedo registrado en
`iso_state_synthesis/experiments/010_top_drill_cazaux_corpus.md`. La diferencia
hallada fue `ToolKey` explicito vs herramienta automatica/embebida:

- bloques explicitos: conservar orden fuente;
- bloques automaticos: ordenar por vecino mas cercano desde `(X,Y)` minimo.
