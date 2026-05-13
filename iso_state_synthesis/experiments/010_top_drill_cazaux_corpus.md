# Top Drill Order - Cazaux Corpus

Fecha: 2026-05-13

## Objetivo

Extender la mini tanda `Pieza_209..214` con un corpus real mas amplio para
separar dos escenarios:

- PGMX sinteticos con `Operation.ToolKey` explicito;
- PGMX reales de Maestro con `Operation.ToolKey` vacio y herramienta resuelta
  desde el diametro/husillo embebido.

## Corpus

- PGMX: `S:\Maestro\Projects\ProdAction\Prod 26-01-01 Cazaux`
- ISO: `P:\USBMIX\ProdAction\Prod 26-01-01 Cazaux`
- Pares detectados: `104/104`
- Reportes generados:
  - `S:\Maestro\Projects\ProdAction\Prod 26-01-01 Cazaux\_analysis\top_drill_order_corpus_analysis.csv`
  - `S:\Maestro\Projects\ProdAction\Prod 26-01-01 Cazaux\_analysis\top_drill_order_corpus_summary.md`

Comando:

```powershell
py -3 -m tools.studies.iso.top_drill_corpus_order_analysis_2026_05_13
```

## Resultado De Orden

Despues de resolver herramientas automaticas desde el tooling embebido, el
corpus queda asi:

| estado | cantidad |
| --- | ---: |
| `candidate_matches` | 58 |
| `neither_matches` | 2 |
| `count_mismatch` | 34 |
| `no_top_drill` | 10 |

Los `60` casos comparables tienen la misma multiconjuncion de huecos en PGMX e
ISO. En esos casos:

- orden crudo del PGMX vs Maestro: `0/60`;
- regla candidata vs Maestro: `58/60`.

Todos los `94` casos con evidencia top drill tienen `top_tool_key_mode=auto`.
Esto distingue Cazaux de la mini tanda `Pieza_209..214`, donde los bloques
tienen herramienta explicita y Maestro conserva el orden fuente.

## Regla Aplicada

`iso_state_synthesis/pgmx_source.py::_ordered_top_drill_block` queda con regla
condicional:

- si todos los pasos del bloque `top_drill` tienen `Operation.ToolKey.name`
  explicito, conservar el orden fuente;
- si el bloque viene automatico, ordenar por vecino mas cercano arrancando en
  la menor coordenada `(X,Y)`.

Esta regla reemplaza la heuristica anterior de columnas/bandas por menor
recorrido para el caso automatico. La heuristica vieja queda encapsulada como
referencia local, pero ya no es la seleccion activa.

## Residuales De Orden

Solo quedan dos casos comparables donde el orden difiere:

- `Cocina\mod 8 - Abierto\Lat_Der.pgmx`
- `Cocina\mod 8 - Abierto\Lat_Izq.pgmx`

Ambos son bloques chicos de `4` huecos `005`. Maestro arranca en `005@516,50`,
mientras la regla `(X,Y)` minima arranca en el hueco de menor `X`. Estos dos
casos parecen necesitar una regla secundaria de arranque, no una regla distinta
para todo el bloque.

Los `34` `count_mismatch` no se usan para decidir orden:

- `25` casos tienen `8` top drills en PGMX y `0` en ISO;
- `9` casos tienen `8` top drills en PGMX y `4` en ISO.

## Validacion

Compilacion:

```powershell
py -3 -m py_compile `
  iso_state_synthesis\pgmx_source.py `
  tools\studies\iso\top_drill_corpus_order_analysis_2026_05_13.py `
  tools\studies\iso\top_drill_ordering_fixtures_2026_05_13.py
```

Comparaciones exactas:

| corpus | resultado |
| --- | ---: |
| `Pieza_209..214` | `6/6` |
| raiz `Pieza*` | `217/222` |
| `Cocina` | `68/84` |
| `Prod 26-01-01 Cazaux` | `62/104` |

La mejora relevante frente al estado previo es:

- mini tanda `Pieza_209..214`: `2/6` exactos -> `6/6`;
- raiz `Pieza*`: `213/222` -> `217/222`;
- `Cocina`: `65/84` -> `68/84`;
- orden Cazaux comparable: regla candidata `58/60`, con solo dos residuales de
  arranque.

## Lectura

La regla general provisional no es "Maestro siempre conserva el orden fuente"
ni "Maestro siempre optimiza geometricamente":

- con herramienta explicita en el PGMX, el orden fuente es autoridad;
- con herramienta automatica/embebida, Maestro ignora el orden crudo y ejecuta
  una ordenacion geometrica tipo vecino mas cercano.

El proximo refinamiento puntual es entender por que los dos `mod 8 - Abierto`
arrancan por menor `Y`/zona derecha en vez de menor `(X,Y)`.

## Seguimiento Por Bloques

La clasificacion posterior por bloques y transiciones quedo registrada en
`iso_state_synthesis/experiments/011_block_transition_cazaux_strategy.md`. Esa
ficha separa:

- `62` exactos;
- `20` casos solo con delta menor de cabecera `%Or`;
- `22` residuales operativos agrupados por `B-*` / `T-*`.
