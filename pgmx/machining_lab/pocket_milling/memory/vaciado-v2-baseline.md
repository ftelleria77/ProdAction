# Vaciado V2 - Matriz Base De Evidencia

Ultima actualizacion: 2026-05-31

## Alcance

Esta matriz congela la linea base conocida antes de escribir el motor nuevo de
`Vaciado`. El objetivo es que el desarrollo V2 tenga un mapa claro de casos,
topologias, variantes de estrategia, soporte heredado y pendientes reales.

Fuentes usadas:

- `tools/pgmx_vaciado/memory/current-state.md`.
- `tests/test_pgmx_vaciado.py`.
- `tools/pgmx_vaciado/trace_engine.py`.
- `tools/synthesize_pgmx.py`.
- Memoria temporal `tools/pgmx_vaciado/memory/vaciado-v2-rebuild.md`.
- Corpus externo `S:\Maestro\Projects\ProdAction\PGMX`.
- Reportes regenerados en
  `S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_v2_baseline_2026_05_31`.

Validacion de esta corrida:

- Se recupero acceso a `S:` y `P:` remapeando las unidades persistentes contra
  `\\gateway.mobile.local\SCM Group` y
  `\\gateway.mobile.local\Produccion`.
- Se uso Python real desde
  `C:\Users\fermi\AppData\Local\Python\bin\python3.exe`; los aliases
  `py`/`python` de `WindowsApps` siguen siendo no confiables.
- `python3 -B -m unittest tests.test_pgmx_vaciado`: `57` tests, `OK`.
- `tools.pgmx_vaciado.scan_samples`: `232` filas catalogadas.
- `tools.pgmx_vaciado.trace_primitives`: `78` casos manuales, `77` adaptados y
  `1` `snapshot_only`; `14499` primitivas.

## Reportes Generados

- Catalogo:
  `S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_v2_baseline_2026_05_31\vaciado_pgmx_catalog.csv`.
- Resumen de catalogo:
  `S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_v2_baseline_2026_05_31\vaciado_pgmx_catalog_summary.md`.
- Casos de primitivas:
  `S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_v2_baseline_2026_05_31\vaciado_trace_case_summary.csv`.
- Primitivas:
  `S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_v2_baseline_2026_05_31\vaciado_trace_primitives.csv`.
- Estudio:
  `S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_v2_baseline_2026_05_31\vaciado_trace_primitives_study.md`.

## Resumen Mecanico

- Corpus manual: `78` archivos `Vaciado_*.pgmx`.
- Corpus generado: `80` archivos `Vaciado_*.pgmx`.
- Scanner total: `232` filas.
- Estados del scanner: `231` `ok`, `1` `empty_workplan`.
- Candidatos: `158` `named_vaciado`, `73` `non_milling`, `1` vacio.
- Operacion de vaciado observada: `a:BottomAndSideRoughMilling` (`158`).
- Feature de vaciado observada: `a:ClosedPocket` (`158`).
- Geometrias de casos manuales: `77` `a:GeomCompositeCurve`, `1`
  `a:GeomCircle`.
- Primitivas manuales: `10681` lineas y `3818` arcos.

Ejes de estrategia observados en casos manuales:

| Eje | Valores |
| --- | --- |
| `tool_width` | `4` (7), `9.52` (7), `17.72` (7), `18.36` (12), `76` (7), `80` (31), `100` (7) |
| `allowance_side` | `0` (75), `20` (2), `-20` (1) |
| `overlap` | `0.5` (77), `0.25` (1) |
| `rotation_direction` | `CounterClockwise` (77), `Clockwise` (1) |
| `stroke_connection_strategy` | `LiftShiftPlunge` (51), `Straghtline` (27) |
| `inside_to_outside` | `True` (51), `False` (27) |
| `is_helic_strategy` | `False` (76), `True` (2) |
| `allow_multiple_passes` | `False` (75), `True` (3) |

## Convenciones

Estados:

- `legacy_exact`: el codigo viejo ya lo sintetiza/valida exacto segun memoria
  o tests versionados.
- `legacy_partial`: hay soporte para variantes o subcasos, pero no para toda la
  familia.
- `pending_v2`: queda como objetivo del motor nuevo.
- `snapshot_only`: esta caracterizado para lectura/analisis, pero no entra al
  contrato polilineal actual.

Topologias:

- `rectangular_no_islands`.
- `rectangular_partial_or_outside_board`.
- `single_seed_balanced`.
- `single_seed_unbalanced`.
- `two_seed_symmetric`.
- `right_wall_seed`.
- `multi_seed_hybrid`.
- `non_polyline_outer`.

## Matriz Por Familia

| Casos | Topologia V2 | Estrategia / ejes observados | Estado heredado | Resolvedores o ruta vieja | Objetivo V2 |
| --- | --- | --- | --- | --- | --- |
| `Vaciado_000` | `fixture_empty_board` | pieza base sin mecanizados | `legacy_exact` como plantilla | plantilla de sintesis | mantener como semilla de generacion |
| `Vaciado_001..019` | `rectangular_no_islands` | punto inicial, profundidad, herramienta, `RotationDirection`, `StrokeConnectionStrategy`, `InsideToOutSide`, multipaso, `AllowanceSide`, `Overlap` | `legacy_exact` | `_build_contour_parallel_xyz_path` / generador rectangular | primera meta V2; demostrar ortogonalidad de estrategia |
| `Vaciado_020..021` | `rectangular_partial_or_outside_board` | contorno rectangular parcial o fuera del tablero | `legacy_exact` | generador rectangular con bbox real del contorno | cubrir con offsets de contorno, no con dimensiones de tablero |
| `Vaciado_023..026` | `rectangular_partial_or_outside_board` | herramienta grande `E006`, contornos parciales/especiales | `legacy_exact` | generador rectangular con bbox real del contorno | matriz de contraste por herramienta |
| `Vaciado_032..034` | `rectangular_partial_or_outside_board` | mismas geometrias que `023..025` con herramienta chica `E001` | `legacy_exact` | generador rectangular con bbox real del contorno | validar que herramienta/overlap solo recalculan offsets |
| `Vaciado_022` | `single_seed_balanced` o `single_seed_physical_island` | isla fisica y semilla coinciden en `150..250 x 100..200` | `legacy_partial` | selected near-miss variants y resolvedores `single_seed_large_single_partial_offsets` / `single_seed_dense_bridge_offsets` | clasificar si es topologia propia o caso de semilla balanceada grande |
| `Vaciado_027`, `Vaciado_027_E001..E007` | `single_seed_balanced` | semilla de ruta central `175..225 x 125..175`; offsets completos, parciales, puentes, densos; varias herramientas | `legacy_exact` | `single_seed_bridge_offsets`, `single_seed_single_partial_offsets`, `single_seed_dense_bridge_offsets`, `single_seed_dense_partial_offsets`, `outer_complete_offsets`, `internal_complete_offsets` | segunda meta V2; una semilla balanceada sin nombres por caso |
| `Vaciado_028`, `Vaciado_028_E001..E007` | `single_seed_unbalanced` | semilla rectangular desplazada; clearances no balanceados; versiones izquierda/derecha | `legacy_exact` | `single_seed_unbalanced_left_*`, `single_seed_unbalanced_right_*`, maestroizacion derecha | segunda meta V2; clearances asimetricos como dato geometrico |
| `Vaciado_029`, `Vaciado_029_E001..E007` | `two_seed_symmetric` | dos islas/semillas simetricas; cruce entre islas; puentes; lobulos densos y progresivos | `legacy_exact` | `two_seed_symmetric_bridge_offsets`, `two_seed_large_bridge_offsets`, `two_seed_dense_bridge_offsets`, `two_seed_separate_dense_offsets`, `two_seed_progressive_dense_offsets` | tercera meta V2; eventos de cruce y puente entre semillas |
| `Vaciado_030`, `Vaciado_030_E001..E007` | `right_wall_seed` | semilla de ruta contra pared derecha; base con islas fisicas separadas de semilla resuelta; `InsideToOutSide=True` | `legacy_exact` | `single_seed_right_wall_inside_out_offsets` | tercera meta V2; contacto con pared como evento, no como caso |
| `Vaciado_031_E001..E007` | `single_seed_balanced` con corredor central | semilla central `175..225 x 125..175`; vueltas completas, vuelta de borde, lobulos parciales, micro-puente | `legacy_exact` para variantes | helpers single-seed/multiloop y artefactos con arcos Maestro | usar como evidencia para eventos reutilizables |
| `Vaciado_031` base | `multi_seed_hybrid` | dos islas fisicas y semilla/corredor central de ruta; dos trayectorias `5+10` en base | `pending_v2` | parcialmente explicado por variantes `031_E00x` | cuarta meta V2; cerrar sin parche por nombre de caso |
| `Vaciado_035` | `non_polyline_outer` | `GeomCircle`, `AllowanceSide=20`, `InsideToOutSide=false`, `IsHelicStrategy=true`, trayectoria circular a Z constante | `snapshot_only` | analizador de primitivas; fuera de `PocketMillingSpec` polilineal | quinta meta V2; decidir curvas nativas o polilinizacion |

## Ejes De Estrategia A Cruzar

Estos ejes no son topologias. Deben aplicarse como politicas generales sobre
las topologias soportadas:

| Eje | Evidencia actual | Efecto esperado en V2 |
| --- | --- | --- |
| `tool_width` | series `E001..E007` | recalcula radio, paso y puede cambiar eventos por umbral |
| `Overlap` | `Vaciado_017` y series con `overlap=0.5` | define `radial_step = tool_width * (1 - overlap)` |
| `AllowanceSide` | `Vaciado_015`, `016`, `035` | desplaza primer offset efectivo |
| `RotationDirection` | `Vaciado_010` | cambia orientacion de primitivas y serializacion |
| `InsideToOutSide` | `Vaciado_012`, right-wall | cambia orden de offsets/recorrido |
| `StrokeConnectionStrategy` | `Vaciado_011`, `018`, `019` | define conectores entre huecos o niveles |
| `AllowMultiplePasses` | `Vaciado_014`, `018`, `019` | genera capas Z dentro de una o mas trayectorias |
| `IsHelicStrategy` | `Vaciado_013`, `035` | pendiente; no asumir helicoidal real sin evidencia Z |

## Eventos Geometricos Iniciales

| Evento | Evidencia | Nota V2 |
| --- | --- | --- |
| `complete_offset` | rectangulares, `027`, `031` | vuelta completa alrededor de contorno o semilla |
| `partial_offset` | `027`, `028`, `031` | offset que ya no puede cerrar vuelta completa |
| `bridge_between_seed_and_outer` | `027`, `028`, `031` | conecta semilla con recorrido exterior |
| `bridge_between_seeds` | `029` | aparece al superar medio claro entre islas |
| `wall_contact` | `030` | recorte contra pared derecha del bolsillo |
| `seed_crossing` | `029` | interseccion de offsets de dos semillas |
| `terminal_lobe` | `027`, `028`, `029`, `031` | lobulo final cuando el offset supera un umbral |
| `maestro_serialization_cut` | `029_E005`, `031_E004`, right-wall | corte de arcos/lineas para equivalencia XML Maestro |

## Resolvedores Viejos A Reubicar

Estos nombres no deben filtrarse al diseno V2 como casos finales. Sirven como
mapa de migracion hacia eventos/topologias:

- `single_seed_bridge_offsets`.
- `single_seed_single_partial_offsets`.
- `single_seed_large_single_partial_offsets`.
- `single_seed_dense_bridge_offsets`.
- `single_seed_dense_partial_offsets`.
- `single_seed_unbalanced_left_partial_offsets`.
- `single_seed_unbalanced_left_terminal_partial_offsets`.
- `single_seed_unbalanced_left_early_dense_offsets`.
- `single_seed_unbalanced_left_dense_partial_offsets`.
- `single_seed_unbalanced_left_extended_dense_offsets`.
- `single_seed_unbalanced_left_repeated_partial_offsets`.
- `single_seed_unbalanced_right_terminal_partial_offsets`.
- `single_seed_unbalanced_right_*` por espejo/maestroizacion.
- `two_seed_symmetric_bridge_offsets`.
- `two_seed_large_bridge_offsets`.
- `two_seed_dense_bridge_offsets`.
- `two_seed_separate_dense_offsets`.
- `two_seed_progressive_dense_offsets`.
- `single_seed_right_wall_inside_out_offsets`.
- `outer_complete_offsets`.
- `internal_complete_offsets`.

## Pendientes De Evidencia

1. Restaurar acceso directo al corpus externo `S:\Maestro\Projects\ProdAction\PGMX`.
2. Resolver Python local para ejecutar `tests.test_pgmx_vaciado`.
3. Generar una matriz mecanica desde el corpus cuando `S:` este disponible:
   caso, herramienta, diametro, overlap, allowance, estrategia, islas fisicas,
   semillas de ruta, cantidad de `TrajectoryPath`, puntos, lineas, arcos y
   estado de soporte.
4. Confirmar si `Vaciado_022` se debe clasificar como semilla balanceada grande
   o como topologia separada.
5. Confirmar el alcance minimo para declarar equivalente el nuevo motor V2.
