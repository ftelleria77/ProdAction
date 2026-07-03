# Experimentos del converter PGMX→ISO — índice de lotes

Método: fixtures (sintetizador pgmx o Maestro a mano, 1 variable por pieza) → postproceso en
Maestro → derivar la regla del ISO crudo → implementar → regresión byte-idéntica. Fixtures en
`S:\Maestro\Projects\ProdAction\<lote>\`, ISOs en `P:\USBMIX\ProdAction\<lote>\`. Generadores en
`iso/machining_lab/nNNN_*/generate.py`.

**Principio rector (Fermín): el converter no tiene constantes internas para traza/recorrido/
profundidad** — todo sale de la config de máquina (snapshot en `iso/data/machine_config/`), del
catálogo (`pgmx/data/tool_catalog.csv` = def.tlgx) o de la operación (`.pgmx`). Las excepciones
son constantes del CICLO del postprocesador Maestro (documentadas como tales, Tier D).

| Lote | Pregunta | Regla derivada | Dónde vive |
|---|---|---|---|
| **N001** | formato ISO completo (24 baselines) | preamble/epilogue, bloques por familia, transiciones | `analysis.md` en `n001/`; todo `iso/synthesis/` |
| N002/N003 | — | **DESCARTADOS** (config Maestro vieja; no usar como referencia) | — |
| **N004** | taladro top por diámetro | tabla TOP_TOOL (etk6 por Ø); invariante `etk0 = 2^(etk6-1)` | `_machine.py`, `test_iso_top_tool.py` |
| **N005** | top pasante | `z_cut = tlc` (para en la MESA; ignora extra_depth) | `_top_drill.py` |
| **N006** | peck/multi-step top | n pasos iguales; re-aproximación `+1.0` (ciclo Maestro) | `_top_drill.py`, `test_iso_top_peck.py` |
| **N007** | broca cónica | discrimina `BottomCondition/IsFlat`; tool 007; `% x.pgm` = nombre de ARCHIVO | `_machine.py`, adapter, `test_pgmx_drill_family.py` |
| **N008** | patrones de perforado | expansión row-major a taladros individuales | `_reader.expand_drilling_pattern` |
| **N009/N010** | feed/spindle override top | `F=min(feed×1000, max)`, `S=min(spindle, max)`; topes del catálogo | `_machine.effective_top_feed_spindle` |
| **N011** | side drill features | `cut = ∓TLC_CUT ± depth` (¡depende de la profundidad!); peck lateral no existe; pasante lateral = dimensión cruzada ≤ sinking | `_side_drill.py`, `test_iso_side_features.py` |
| **N012** | cut lateral por cara | la fórmula del cut vale en las 4 caras | ídem |
| **N013** | límite de hundimiento top | efectiva (pasante→espesor) ≤ SinkingLength, borde inclusivo | `_reader.py`, MaxSinkTest |
| **N014** | security plane lateral | el approach usa `security_plane` de la operación (piso 5) | `_side_drill._hole_coords` |
| **N015** | park del footer | `G53 X = Xn.x`, `Y = -Xn.y` (de la operación nula Xn); Z de Params.cfg | `_reader._xn_park`, `test_iso_xn_park.py` |
| **N016/N017** | g53 de transición Top→Side | `g53 = DZ + 20 + max(head_tlc, max(sp+shf_z))` — piso = ToolOffsetLength del tool que se retrae; bloque SHF solo Left/Back | `_machine.side_transition_g53_z`, `test_iso_side_g53.py` |
| **N018** | origen de trabajo Or[0] | `ofX[pre] = -DX×1000`; `ofX[blk] = -(DX+ox)×1000`; `ofY = float32(field_y)×1000` (¡el .976 es float32, no calibración!) | `_machine.or_ofx/or_ofy` |
| **N019/N020/N021** | campos de trabajo (grilla 2×2) | modelo near/far por eje; EDK 13/10 sigue X; caras idénticas en los 4 campos; orígenes de `fields.cfg` | `_machine.py` (or_*/shf_*/side_shf/edk_field), `test_iso_field.py` |
| **N022** | router: fresas + dirección + cambios en recorrido | ver [router_line_milling.md](router_line_milling.md) §1-3 | `_router.py`, `test_iso_router_path_changes.py` |
| **N023** | corrección de herramienta y de longitud | ver [router_line_milling.md](router_line_milling.md) §4 y §7 | `_router.py`, `test_iso_router_side.py`, `test_iso_router_precise.py` |
| **N024** | pasante/extra + rebaba | ver [router_line_milling.md](router_line_milling.md) §5-6 | `_router.py`, `test_iso_router_depth_finish.py` |

## Constantes del ciclo Maestro (Tier D — se replican, no se sourcean)

Investigadas a fondo (el hogar de los defaults es `maestro/Cfgx/Programaciones.settingsx` →
`UI00.exe.Config`; ahí vive p.ej. `SecurityDistance=20`, el default del security_plane):
- peck `+1.0` (re-aproximación, N006) — confirmada constante en 5 variantes.
- `SIDE_APPROACH_FLOOR = 5` (mínimo del plano de seguridad lateral, N016).
- lead-in/out de la corrección `1.0 mm` (N023) — idéntico en E004 y E001.
- `SECURITY_SIDE = 20` del g53 — sourced de `pheads.cfg` (Cabeza 1, Config1 Z = −20).

## Multi-campo (pendular EF/HG)

La cama es una grilla 2×2 de áreas (AB/DC/EF/HG) con origen en `fields.cfg`. Solo HG está
calibrado hoy; EF/AB/DC emiten con la config actual (stale) y entran solos al recalibrar +
re-snapshotear. El campo se lee de `<ExecutionFields>` del `.pgmx`. Ver el detalle del modelo
near/far en los comentarios de `_machine.py`.
