# 024 - Haeublein Corpus Examples

Fecha: 2026-05-15

## Objetivo

Agregar el corpus real `Prod 25-09-04 Haeublein` al estudio de bloques,
transiciones y reglas de excepcion.

Corpus:

- PGMX: `S:\Maestro\Projects\ProdAction\Prod 25-09-04 Haeublein`
- ISO: `P:\USBMIX\ProdAction\Prod 25-09-04 Haeublein`
- Reportes: `S:\Maestro\Projects\ProdAction\Prod 25-09-04 Haeublein\_analysis`

## Resultado Inicial

Comando principal:

```powershell
py -3 -m tools.studies.iso.block_transition_corpus_analysis_2026_05_13 --pgmx-root 'S:\Maestro\Projects\ProdAction\Prod 25-09-04 Haeublein' --iso-root 'P:\USBMIX\ProdAction\Prod 25-09-04 Haeublein' --output-dir 'S:\Maestro\Projects\ProdAction\Prod 25-09-04 Haeublein\_analysis'
```

Salida:

```text
Analyzed 135 PGMX/ISO rows.
exact: 104
operational_diff: 5
unsupported_candidate: 26
```

Los no soportados se agrupan asi:

| motivo | casos |
| --- | ---: |
| Perfil `E001` indica arco pero el PGMX no trae primitiva `Arc` | 16 |
| Etapa no soportada `Perfilado(1)(1)` | 5 |
| Etapas no soportadas `Fresado...` | 5 |

## Operativos

Los `5` operativos son diferencias `G0/G0`, sin nuevos frentes de transicion:

| frente | casos | lectura |
| --- | ---: | --- |
| `block:B-BH-002` | 4 | orden de huecos superiores |
| `block:B-BH-005` | 1 | orden de tandas laterales |

Casos:

| pieza | frente | Maestro | candidato |
| --- | --- | --- | --- |
| `Cocina\mod 11 - Torre 2 p vidrio\Lat_Der.pgmx` | `B-BH-002` | `G0 X736.000 Y421.000 Z115.000` | `G0 X100.000 Y421.000 Z115.000` |
| `Cocina\mod 12 - Torre 1 p vidrio\Lat_Der.pgmx` | `B-BH-002` | `G0 X736.000 Y421.000 Z115.000` | `G0 X100.000 Y421.000 Z115.000` |
| `Cocina\mod 16,17 - Bajos puertas + cajones\TabiqueF6.pgmx` | `B-BH-002` | `G0 X237.500 Y60.000` | `G0 X507.000 Y32.000` |
| `Cocina\mod 18,19 - Torre 2 p vidrio\Lat_Der.pgmx` | `B-BH-002` | `G0 X736.000 Y409.000 Z115.000` | `G0 X100.000 Y409.000 Z115.000` |
| `Cocina\mod 16,17 - Bajos puertas + cajones\Divisor_Horiz1.pgmx` | `B-BH-005` | `G0 X558.000 Y20.000` | `G0 X558.000 Y140.000` |

## Orden Top Drill

Comando:

```powershell
py -3 -m tools.studies.iso.top_drill_corpus_order_analysis_2026_05_13 --pgmx-root 'S:\Maestro\Projects\ProdAction\Prod 25-09-04 Haeublein' --iso-root 'P:\USBMIX\ProdAction\Prod 25-09-04 Haeublein' --output-dir 'S:\Maestro\Projects\ProdAction\Prod 25-09-04 Haeublein\_analysis'
```

Salida:

```text
Analyzed 135 PGMX/ISO rows.
candidate_matches: 74
count_mismatch: 43
neither_matches: 4
no_top_drill: 14
```

Los `4` `neither_matches` son exactamente los `B-BH-002` operativos. Todos
tienen `top_tool_key_mode=auto`, por lo que no pertenecen a la excepcion de
orden fuente con `tool_key` explicito.

Lecturas iniciales:

- Los tres `Lat_Der` largos (`mod 11`, `mod 12`, `mod 18,19`) siguen una banda
  superior que Maestro recorre por `418/736/833/1054` antes de volver hacia
  extremos, mientras el vecino mas cercano del candidato salta de `418` a
  `100`.
- `TabiqueF6.pgmx` activa la excepcion actual de `4` huecos, una herramienta
  efectiva y profundidades mixtas, pero Haeublein muestra que esa regla no es
  universal: Maestro arranca en `X237.5 Y60`, no en `max X/min Y`.

## Orden Side Drill

`Divisor_Horiz1.pgmx` activa la regla actual de rotar tandas laterales cuando
la misma cara abre y cierra el bloque. En Cazaux, el patron observado era:

```text
Back -> Front -> Back
```

En Haeublein aparece:

```text
Right -> Left -> Right
```

Maestro conserva el primer `Right` en `Y20`; el candidato rota la tanda final y
arranca en `Y140`. Esto indica que la rotacion no debe ser una regla global
para cualquier cara repetida. Como minimo, debe acotarse por patron de caras o
por otra senal contextual todavia no aislada.

## Reglas Activadas En Haeublein

Sobre los `109` candidatos soportados, se activan `9` reglas existentes y
afectan `78` archivos unicos:

| regla | archivos |
| --- | ---: |
| `EMIT-TOP-001` | 72 |
| `PGMX-GEO-002` | 28 |
| `EMIT-ROUTER-001` | 24 |
| `EMIT-ROUTER-002` | 24 |
| `PGMX-ORD-004` | 5 |
| `EMIT-CLOSE-001` | 5 |
| `PGMX-ORD-002` | 1 |
| `PGMX-ORD-003` | 1 |
| `EMIT-TXH001-SIDE` | 1 |

## Plan

1. Estudiar `B-BH-002` Haeublein como nuevo frente de orden top drill, separado
   de los casos DeMarco marcados como `precision_only`.
2. Revisar la excepcion `PGMX-ORD-002`: el predicado actual
   `4 huecos / una herramienta / profundidades mixtas` es demasiado amplio.
3. Revisar `PGMX-ORD-003`: la rotacion de tandas laterales debe conservar Cazaux
   `Back -> Front -> Back`, pero no debe rotar el caso Haeublein
   `Right -> Left -> Right`.
4. Mantener fuera de este frente los `26` no soportados; corresponden a
   operaciones de fresado/perfilado o perfiles `E001` con arco declarado sin
   primitiva `Arc`.
