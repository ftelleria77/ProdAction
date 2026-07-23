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
| **N025** | estrategias multipasada Uni/Bi + ZigZag | ver [router_line_milling.md](router_line_milling.md) §8 y §13 | `_router.py`, `test_iso_router_depth_finish.py`, `test_iso_router_cad_zigzag.py` |
| **N026/N027** | leads programables (tipos/modos/velocidades/lados) + terminación | ver [router_line_milling.md](router_line_milling.md) §9 | `_router.py`, `test_iso_router_multipass_leads.py` |
| **N028** | multi-fresa + Avanz./Rotación + cambios múltiples/diagonal + desactivado/comentado | ver [router_line_milling.md](router_line_milling.md) §3, §11, §14-15 | `_router.py`, `test_iso_router_path_changes.py` |
| **N029** | combos finos + CAD/invertir | levantadas invertir+leads, longitud+rebaba (w/2, no SVR), pasante+lado; DERIVADAS con cuerpos completos (2026-07-05): multipaso+lado (desplazadas sin G41) y lado+leads (tangente del arco, Automatic=lado libre); multipaso+leads → N034 | `test_iso_router_combos.py`, [router_line_milling.md](router_line_milling.md) §10-10b |
| **N034** | multipaso + leads: matriz de desambiguación | **9/9 byte-idéntico**: radio (w/2)×(RM−1) — RM=1 omite el arco —, lados espejados, salida sobre la última pasada, sin reset de preamble; leads se RECALCULAN del spec (rm3 lo prueba) | `test_iso_router_multipass_leads.py`, [router_line_milling.md](router_line_milling.md) §10 |
| **N035** | cierre de guardas del fresado lineal | **14/14 byte-idéntico**: Uni/ZigZag+lado, ZigZag+leads (ancla en superficie), triple mp+lado+leads (Automatic sigue el lado), Lineal/En bajada (rampa o helicoidal)/En subida/velocidad (pisa el feed del cuerpo)/RM<1/arco explícito ignorado con G41 | `test_iso_router_multipass_leads.py`, `test_iso_router_combos.py` |
| **N036** | cierre TOTAL de guardas fixtureables | **32/32 byte-idéntico** (los 3 eco derivados tras REGENERAR: el acorte/swap/pasadas invertidas SÍ aplican — los eco mentían): CAD+combos, invertir+combos, UPar sobre recorrido acortado/invertido, feed vigente en salidas, pasante+estrategia/leads, ZigZag diagonal/uh0, alejamiento Lineal/velocidad, multi-fresado; **estrategia+cambios = PROHIBIDO por Maestro** (permanente) | `test_iso_router_combos.py` (GuardClosingN036Test), [router_line_milling.md](router_line_milling.md) §10 |
| **N037** | **Eje B: Canal con la Sierra Vertical X (082)** | **9/9 byte-idéntico a la primera**: header sin ATC (ETK[6]=82, ETK[17]=257, ETK[1]=16, SHF mandril con w/2 restado en Y), sentido NORMALIZADO a −x, ETK[7]=1, transición doble-G0, epílogo con dwell | `_saw.py`, `test_iso_saw_saw.py`, [saw_channel.md](saw_channel.md) |
| **N038** | **Eje B: Círculos (baseline Center)** | **10/10 byte-idéntico a la primera**: op de familia ROUTER; entrada por el ESTE (cx+r, cy); 360° = DOS semicírculos G3/G2 con I/J ABSOLUTOS al centro; pasante ✓; cierra donde empezó (ancla de transición); línea+círculo mezclados → guarda | `_router.py` (dispatch), `test_iso_circle.py` |
| **N039** | **Eje B: combos del círculo** | **12/12 byte-idéntico**: TODAS las reglas de línea aplican con û = TANGENTE de entrada ((0,±1) según giro) — corrección Int/Ext C.N. (G41/G42, activación 1mm sobre la tangente), leads single-pass/estrategia, triple con G41; Bi ALTERNA el giro por pasada, Uni repite SIN conexiones (cerrado); **HELICOIDAL FUNCIONA** (falló en líneas): cd/vuelta en medias vueltas con J descentrado ±(hypot(r,dz/2)−r) + vuelta plana final | `_router.py` (_circle_*), `test_iso_circle.py` |
| **N040** | **Eje B: arcos sueltos (autoría nueva + baseline)** | **10/10 byte-idéntico a la primera** (autoría pgmx estrenada y validada vía Maestro): op de familia ROUTER; entrada por el START real; UN G3 (CCW) / G2 (CW) al end con I/J ABSOLUTOS al centro; pasante ✓; `two` = transición triple-G0 (prev=fin del arco); familias del router mezcladas → guarda | `pgmx/synthesis/milling/arc.py`, `_router.py` (is_arc), `test_iso_arc.py`, `test_pgmx_arc_authoring.py` |
| **N041** | **Eje B: polilíneas mixtas (rectas + arcos)** | **10/10 byte-idéntico** (autoría PolylineSpec estrenada + validada vía Maestro): op de familia ROUTER; UN G-code por segmento en orden (recta = G1, arco = G3/G2 con I/J al centro); abierto y cerrado (espejo Estante); recta-pura (Polyline) y mixta son la MISMA familia "poly" (transicionan byte-idéntico); `_g1_cut` con tolerancia sub-micrón (ruido de arco reconstruido) | `poly_profile.py`, `_router.py` (is_poly), `test_iso_poly_profile.py`, `test_pgmx_arc_authoring.py` |
| **N042** | **Eje B: polilíneas — corrección + entrada** | **11/11 byte-idéntico** (abiertas y cerradas): corrección izq/der = modelo de la LÍNEA generalizado (G41/G42 + coords NOMINALES + lead-in 1mm sobre 1er segmento, lead-out sobre último; el control empalma las esquinas — sin arcos en el ISO); acercamiento = arco tangente anclado al 1er vértice; sentido invertido voltea G3↔G2 y el lado físico; punto inicial en medio de segmento parte en 2 G1 colineales. CAMINO 1 confirmado (autoría guarda nominal, Maestro regenera) | `_router.py` (_poly_body/_poly_entry_xy), `test_iso_poly_profile.py` |
| **N043** | **Eje B etapa 4: Galceado/Perfilado/Escuadrado** | **4/4 byte-idéntico** (hechos a MANO por Fermín, `Programas Manuales/`): el Galceado NO es feature nueva del ISO — ContourFeature ≡ GeneralProfileFeature, ContourType invisible; SOLO cambia el ACC. Estilo A (C.N.) = la polilínea cerrada de N042; estilo B (CAD) = polígono offseteado + cuarto de arco por esquina (centro=vértice, F en todo, plunge a feed de corte, sin reset de preamble). Trajo además el footer sin Xn y que Maestro escribe ISO en ANSI/cp1252 | [galceado_perfilado.md](galceado_perfilado.md), `_router.py` (_poly_cad_*), `test_iso_galceado.py` |
| **N044** | **Eje B etapa 4: pendientes del Galceado** | **11/13 byte-idéntico** (2 fail-loud subdeterminados): CN leads LÍNEA compensados (En cota/bajada/subida) + forma EN-JUEGO (ContourSpec→polilínea del perímetro, arranque a mitad de borde) + CAD estilo B GENERAL (offset r=w/2 + arco de ángulo cualquiera en convexa / **esquina VIVA en cóncava** — respuesta a la pregunta estrella; Right→G3, Left→G2, interno CW=todo vivo). Fail-loud: cad_leads (lead CAD radio w/2, 1 fixture) y cad_zigzag (ZigZag+CAD cerrado, spec+render sin derivar) | `_router.py` (_poly_cad_moves/_poly_body), `_reader.py` (_contour_to_polyline), `test_iso_galceado.py` |
| **N030** | modos de lead En bajada/subida + CAD diagonal + long diagonal | arco helicoidal de bajada; lead-out ascendente + G0 Z | `_router.py`, `test_iso_router_multipass_leads.py` |
| **N031** | autoría pgmx A (rebaba/longitud/invertir/CAD/F-S) | 5/5 byte-idéntico: features de postprocesador — autorables con curva plana | `pgmx/synthesis`, `test_pgmx_authoring_e2e.py` |
| **N032** | autoría pgmx B (zigzag/atributos "mínimos") | **0/4 — falló adrede**: Maestro postprocesa el toolpath ALMACENADO; ns equivocado se ignora en silencio | [router_line_milling.md](router_line_milling.md) §16 |
| **N033** | autoría pgmx C (forma-Maestro completa) | curvas partidas + strokes zigzag + ns/keys correctos; **4/4 byte-idéntico a través de Maestro — autoría CERRADA** | `test_pgmx_authoring_structural.py`, `test_pgmx_authoring_e2e.py` |

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
