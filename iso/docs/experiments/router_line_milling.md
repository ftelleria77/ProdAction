# Fresado lineal (router) — modelo completo derivado

Evidencia: lotes **N022** (fresas + direcciones + cambios de recorrido), **N023** (corrección de
herramienta + corrección de longitud) y **N024** (pasante/extra + rebaba), más el grupo D de N001.
Fixtures en `S:\Maestro\Projects\ProdAction\<lote>\`, ISOs de referencia en
`P:\USBMIX\ProdAction\<lote>\`. Todo byte-idéntico (157/157 al cierre 2026-07-03).

Implementación: `iso/synthesis/_router.py` (render), `iso/synthesis/_validation.py` (guardas),
`iso/synthesis/_reader.py` (hundimiento), specs en `pgmx/synthesis/milling/line.py`, lectura en
`pgmx/snapshot.py` + `pgmx/adapters.py`. Tests: `tests/test_iso_router_*.py`.

## 1. Por herramienta (N022 — E001/E002/E003/E005/E006/E007)

| Valor ISO | Fuente | Regla |
|---|---|---|
| `T{N}`, `?%ETK[9]={N}` | nombre de la fresa | N = E00N (slot ATC = nº de fresa) |
| `?%ETK[6]=1`, `?%ETK[18]=1` | cabezal | constantes del electromandril |
| `S{rpm}M3` | catálogo `spindle_speed_std` | E002 (sierra) 6000; resto 18000 |
| `G0 Z` de approach | catálogo `tool_offset_length` + security | z = TLC + sp |
| `SVL` | = TLC | corrector de longitud |
| `SVR` | `width/2 (+ rebaba)` | corrector de radio; ver §6 |
| plunge `G1 Z... F` | catálogo | `feed_default = min(descent_std, feed_std)×1000` |
| corte `G1 ... F` | catálogo | `feed_std × 1000` |
| `SHF` (MLV2) | `pheads.cfg` Cabeza 3 | del CABEZAL, no de la fresa |

**Sin distinción de tipo de herramienta** (decisión de Fermín): la sierra E002 se programa igual
que una fresa en una línea; el uso/recorrido es responsabilidad del programador de Maestro. La
validación del sintetizador se relajó para line milling (`pgmx/synthesis/milling/_common.py`).

## 2. Trayectoria (N022 — dir_x/dir_y/dir_diag/dir_xrev)

Un `G1` por tramo hasta `(end_x, end_y)`; el **sentido es implícito** (va al end). Regla de ejes:
se emiten los ejes del plano que se MUEVEN; se agrega `Z` solo cuando se mueve UN eje — la
**diagonal (X+Y) omite Z** (quirk de Maestro). `_g1_cut` en `_router.py`.

## 3. Cambios DURANTE el recorrido (N022 Vel/Prof + N028 diag/_coment — múltiples y combinados)

En el `.pgmx` son `Operation > Attributes > OperationAttribute` anclados a **UPar** (posición
paramétrica 0..1 normalizada sobre la trayectoria). El punto es `p = start + upar·(end−start)`.

- **Cambio de velocidad** (`SpeedAttribute(UPar, Speed m/min)`): la línea se parte en `p`; el
  tramo posterior corre a `F = Speed×1000`. (Vel: `G1 X98 F5000` → `G1 X280 F1000`.)
- **Cambio de profundidad** (`DepthAttribute(UPar, Depth mm)`): **rampa lineal** hasta `Depth`,
  alcanzándola en `p` — el G1 interpola X y Z juntos — y sigue. (Prof: `G1 X85 Z-5` → `G1 X280 Z-5`.)
- **Múltiples/combinados** (N028 _coment: 2 rampas + 2 velocidades): lista de eventos ordenada por
  UPar; un G1 por tramo; el feed de un tramo es el vigente al ENTRAR; la rampa arranca en el evento
  ANTERIOR (semántica "plana entre eventos"). Diagonal: la rampa emite `G1 X Y Z` (§regla Z).

**Hallazgo N032/N033 (curvas partidas)**: Maestro ALMACENA en el TrajectoryPath una
`GeomCompositeCurve` partida en cada evento, con la Z interpolada linealmente ENTRE eventos de
profundidad (p.ej. −12.167 en X85 del _coment)… pero **el ISO NO la sigue**: postprocesa desde los
atributos de la operación con la semántica plana de arriba (Z−13 en X85, byte-validado). El
converter deriva de los atributos semánticos; la AUTORÍA (§16) replica la forma almacenada.

## 4. Corrección de herramienta (N023 — side_of_feature Left/Right)

El control compensa el **radio del corrector SVR** vía **G41 (Left) / G42 (Right)**; las
coordenadas del corte NO cambian (no es offset CAM). El lado es **relativo al avance** (la línea
invertida con Left sigue G41).

Estructura (diferencias vs. Center):
```
G0 X{lead-in} Y{...}          ← 1 mm ANTES del start sobre la dirección
G0 Z{TLC+sp}
D1 / SVL / SVR
?%ETK[7]=4                    ← se muda ANTES del G41
G41|G42
G1 X{start} Y{start} Z{sp} F{plunge}   ← lead-in: engancha la corrección en el plano de seguridad
G1 Z{-prof} F{plunge}
<corte>                       ← coordenadas nominales
G1 Z{sp} F{corte}             ← retracción en G1 (no G0)
G40
G1 X{lead-out} Y{...} Z{sp} F{corte}   ← 1 mm DESPUÉS del end
D0 ...
```
El preamble gana `?%ETK[7]=0` tras el segundo G40. El **lead de 1 mm es constante del ciclo**
(idéntico con E004 w=4 y E001 w=18.36 → Tier D, no derivable de la herramienta).

## 5. Pasante y profundidad extra (N024 — th_e0/e2/e4)

`z_corte = -(espesor + extra_depth)` (−18/−20/−22). El fresado **SÍ pasa la cara inferior**
(corta al spoilboard), a diferencia del taladro vertical (que para en la mesa e ignora extra).
Límite de hundimiento **inclusivo**: espesor+extra ≤ SinkingLength (18+4 = 22 = sink E004, OK).
Guarda defensiva en `_reader.read_pgmx`.

## 6. Rebaba (N024 — *_reb2 / *_rebm2, hechos en Maestro)

En el fresado **lineal** la rebaba es **`<SideOffset>` del ManufacturingFeature** (¡NO
`AllowanceSide`, que queda 0! — en Vaciado sí es AllowanceSide: el mapeo es por familia).
Efecto: **`SVR = width/2 + rebaba`** (reb2 → 4.0; rebm2 → 0.0). Si el resultado es **0**, las
líneas `SVR`/`VL7` se **OMITEN** (setup y teardown). Ortogonal a G41/G42 (validada en
Center/Left/Right/xrev con ±2, 8 fixtures).

## 7. Corrección de longitud (N023 — *_long, hechos en Maestro)

Flag **`<IsPrecise>`** del ManufacturingFeature. El recorrido se **acorta el radio de la fresa
(width/2) en ambos extremos**: el centro viaja `[start + r·dir, end − r·dir]` → el **filo** cubre
exactamente el segmento programado. E004 ±2, E001 ±9.18. Con G41/G42, el lead-in/out de 1 mm se
calcula sobre los extremos ya acortados. Validada en líneas a eje, ambos sentidos, con y sin
compensación.

## 8. Multipasada en Z (N025 + N027 — estrategias Uni/Bidireccional)

Pasadas `z_i = -min(i·cd, total_desbaste)`: pasos de `axial_cutting_depth`, la última del desbaste
lleva el resto. Con **terminación** (`axial_finish_cutting_depth`): desbaste hasta `total − finish`
+ **una pasada final** a total (bi_cd4_f2: −4/−8/−10/−12). **Bidireccional**: alterna el sentido y
desciende en el extremo donde quedó. **Unidireccional**: siempre start→end; entre pasadas retrae y
vuelve en G1 a feed de corte — `Automatic` ≡ `SafetyHeight` (retorno a security); **`InPiece`**
retorna a `z_pasada + MillingRetractDistance` (**sourced de `Programaciones.settingsx`**, =10).
Quirk: bajada inicial `G1 Z{security}` a feed de PLUNGE; descensos por pasada a feed de CORTE.

## 9. Approach/Retract programables (N026 + N027 — leads)

`lead = (width/2) × radius_multiplier`. ⚠️ El default del RM con lead **habilitado es 2.0**
(no 1.2): el fixture "rm2" de N026 no variaba nada — lección: verificar en el XML que el fixture
realmente varió el parámetro. Confirmado con rm3 (lead 6) y E001 (lead 18.36).
- **Arco tangente**: `Automatic` ≡ `Right` (byte-idéntico) → centro a `rot90ccw(û)`, **G3**;
  `Left` → `rot90cw(û)`, **G2**. Validado en +X/+Y/−X.
- **Approach**: `?%ETK[7]=4` antes del plunge (+ `?%ETK[7]=0` en el preamble); plunge en el punto
  exterior y lead **a profundidad** hasta el start. La **velocidad del lead** (speed>0, ×1000)
  aplica al plunge Y al lead (sentinel −1 = sin velocidad).
- **Retract**: lead-out a profundidad desde el end + retracción en **G1** (reemplaza el G0 Z).
- **Overlap INERTE** en líneas abiertas (0/0.25/5 → ISO idéntico): se ignora.

## 10. Guardas fail-loud (estado 2026-07-05; combos sin fixture de referencia)

DERIVADAS de los cuerpos completos de N029/N034/N035 (byte-validadas, ver §10b):
- **estrategia + lado** ✅ (Bi N029; Uni y ZigZag N035): ACC=false forzado → coordenadas
  desplazadas estilo CAD, sin G41, con las pasadas/strokes normales;
- **lado C.N. + leads** ✅: lead de contorno con G41/G42; 1 mm sobre la TANGENTE (arco) o û
  (línea); el lado explícito del arco se IGNORA (N035 arcleft): siempre el lado LIBRE (G41→G3,
  G42→G2); Lineal en approach ✅; En bajada = arco helicoidal SIN plunge ✅; En subida = arco
  ascendente con Z, sin G1 Z aparte ✅; velocidad propia (semántica N026) ✅;
- **estrategia + leads** ✅ (N034 9/9 + N035): arco r = **(w/2)×(RM−1)** — ≤0 lo OMITE (rm1,
  rm05) —, lados espejados (Automatic≡Right→G2; con lado, Automatic SIGUE el lado: Left→G3);
  Lineal (approach) usa w/2×RM; En bajada/subida = RAMPAS rectas de largo `lead` (no arcos);
  **la velocidad del approach PISA el feed de TODO el cuerpo** (N035 mp_app_sp); ZigZag + leads
  ancla el arco en la SUPERFICIE (Z0); triple mp+lado+leads: el arco sigue el lado sobre las
  coordenadas desplazadas; sin reset ?%ETK[7]=0 en preamble (solo single-pass con G41/approach).
DERIVADAS en N036 (cierre total, 29/29 byte-idéntico):
- **CAD + combos**: rebaba (desplazamiento usa w/2, la rebaba solo suma al SVR), cambios de
  recorrido (la retracción sale al feed VIGENTE), pasante, y leads estilo-ESTRATEGIA (arco
  (RM−1), Automatic sigue el lado, sin reset de preamble);
- **invertir + combos**: cambios (UPar sobre el recorrido invertido), longitud (acorta y después
  invierte), rebaba;
- **cambios de recorrido**: con longitud (¡el UPar corre sobre el recorrido ACORTADO! long_vel:
  X98.8 = 22+0.3·256) y con lado C.N. (feed vigente en la salida compensada);
- **pasante**: con estrategia (pasos de cd hasta espesor+extra) y con leads;
- **ZigZag**: diagonal ✅, último hueco = 0 ✅ (UNA sola pasada plana final; ambos regenerados en
  Maestro), y TODAS las variantes de lead calzan las fórmulas de multipasada (línea en superficie,
  bajada en rampa desde security+lead, subida, velocidad que pisa el cuerpo INCLUSO el descenso
  inicial — zz_app_sp F3000 en el G1 Z20);
- **leads residuales**: alejamiento Lineal (línea a profundidad más allá del end, con o sin G41),
  velocidad del alejamiento (SOLO lead-out + retracción — asimetría con el approach), Lineal En
  bajada (la línea del lead DESCIENDE desde security, sin plunge — con G41 y en estrategia),
  triple con lado Right y triple con velocidad;
- **estrategia sin multipaso** ≡ fresado plano (strat_single regenerado; el adapter la anula);
- **multi-fresado en un programa**: lado C.N. (¡doble ?%ETK[7]=0 tras la salida compensada!),
  estrategia y approach — el triple G0 de la transición apunta al punto de APROXIMACIÓN del op
  entrante (el exterior del lead) y ancla en la última posición FÍSICA del saliente; un op con
  leads C.N. también agrega el ?%ETK[7]=0 extra en su teardown no-último.

DERIVADAS tras REGENERAR en Maestro (2026-07-07 — los eco previos MENTÍAN):
- **CAD + longitud** ✅ (cad_long regenerado: SÍ acorta ±w/2, X22→278 sobre y102);
- **CAD + invertir** ✅ (inv_cad: SÍ invierte, 280→20 sobre las coordenadas desplazadas);
- **invertir + estrategia** ✅ (inv_mp: las pasadas alternan desde el extremo intercambiado).
El orden del render (longitud → desplazamiento → invertir → estrategia) los produce natural.

GUARDAS RESTANTES:
- **PERMANENTES por decisión de Maestro**: estrategia + cambios de recorrido ("No es posible
  aplicar una estrategia a un trabajo con atributos asociados", N036 mp_vel).
- **Sin fixture (residuales finas)**: cambios de recorrido + leads (agujero detectado en N036);
  triple lado+estrategia+lead no Arco/En cota; alejamiento programable en multi-fresado;
  CAD + lead fuera de la forma base (Arco/En cota/Automatic/sin velocidad).
- **Permanentes estructurales**: caras laterales (sin herramental), degeneradas (corrector
  negativo, recorrido ≤ ancho, terminación ≥ total, pa/pr≤0), enums desconocidos, topes de
  Avanz./Rotación (Maestro clampa al guardar), Allowance≠0.

Resto vigente:
- Cambios de recorrido combinados con lado, corrección de longitud, multipasada o CAD; UPar ∉ (0,1).
- CAD + rebaba/longitud/leads/pasante; Invertir trabajo + cambios/estrategia/longitud/rebaba/CAD.
- ZigZag sobre diagonal; ZigZag con pa/pr/uh ≤ 0; terminación ≥ profundidad total; multipasada +
  pasante; leads + pasante; estrategia sin `allow_multiple_passes` (modo una-pasada).
- Avanz./Rotación sobre el tope de la herramienta (defensiva: Maestro clampa AL GUARDAR el pgmx
  al `feed_rate_max` de CADA herramienta — E004→5, E003→18 m/min).
- Rebaba que deja el corrector negativo; `Allowance*` ≠ 0; recorrido degenerado (largo ≤ ancho);
  hundimiento: profundidad efectiva > SinkingLength.

LEVANTADAS con fixtures (ya soportadas): diagonal con rampa/velocidad, múltiples cambios y ambos
tipos juntos (N028), longitud+rebaba (acorte usa width/2, NO el SVR), pasante+lado,
invertir+leads, CAD en diagonal (N029/N030).

## 10b. Hallazgo metodológico (N029 revisitado, 2026-07-05): eco vs. genuino

Al derivar los combos se verificó qué es eco del archivo y qué es regla de Maestro:
- Los 3 pgmx problemáticos estaban INTACTOS (XML nuestro byte a byte; Maestro solo agregó el
  .epl) — no hubo modificación involuntaria previa al postproceso.
- **El TrajectoryPath almacenado SÍ se postprocesa tal cual** (N032/N033) — por eso mp_side_l
  muestra las coordenadas desplazadas de nuestra curva (que coinciden con la convención Maestro,
  cross-validada por th_side_l vía inversión G41 y por los CAD de N023 hechos en UI).
- **Los leads se RECALCULAN del spec al postprocesar** — la curva Approach almacenada se IGNORA
  (prueba: rm3 tenía almacenado un arco equivocado r4/−y y el ISO salió r6/+y/G3, la regla
  derivada). Consecuencia: los fixtures de leads sintetizados son referencias genuinas aunque
  nuestra autoría de la curva Approach tenga quirks.

## 11. Multi-fresa en un programa (N028 — cambio de herramienta entre pasadas)

Con la MISMA fresa, la transición entre pasadas es `G17 / MLV=2 / triple G0` (N001 D002). Con
fresa DISTINTA (validado en ambos sentidos y mezclado con transición misma-fresa):
```
?%ETK[7]=0 / G0 Z{sp} / D0 / SVL 0 / VL6=0 / SVR 0 / VL7=0     ← teardown estilo no-última
MLV=0 / G0 G53 Z{park} / MLV=2 / ?%ETK[13]=0 / ?%ETK[18]=0 / M5
MLV=0 / G0 G53 Z{park}                                          ← DOBLE park Z
MLV=0 / T{n} / SYN / M06 / ?%ETK[9]={n} / ?%ETK[18]=1 / S{rpm}M3  ← header ATC SIN ?%ETK[6]
G17 / MLV=2 / ?%ETK[13]=1                                       ← SIN re-setup de SHF/Or
G0 X{start} Y{start} / G0 Z{TLC_nueva + sp} / D1 ...
```
Guarda: varios fresados + leads programables → fail-loud (transición con lead sin fixture).

## 12. Corrección CAD (N023 _CAD + N030 diagonal — ActivateCNCCorrection=false con lado)

El CAD desplaza las COORDENADAS (no usa G41/G42 ni leads ni preamble-reset): cada punto se corre
`radio×normal(lado)` — izquierda = rot90ccw(û) — y la entrada/salida en Z es estilo security
(la misma de las estrategias multipaso; ambos escriben ACC=false en el pgmx). El SVR no cambia.
Válido en cualquier dirección (diagonal incluida). Combos → §10.

## 13. Estrategia ZigZag (N025 zigzag_pa2_pr3_uh1)

Baja a Z0 (superficie) y corta EN RAMPA alternando el sentido — la ida baja `pasada avance`, la
vuelta `pasada retorno` — clavado en (total − último hueco); luego la pasada del último hueco a
−total y UNA pasada final plana. `Overlap`/`Cutmode` sin efecto observado en línea. Helicoidal
sobre línea NO existe: Maestro falla en GenerateToolpath (probado en UI).

## 14. Avanz./Rotación por operación (N028 F3_S12K + diag_vel5)

`Technology/Feedrate|Spindle` de la operación: `F = Avanz×1000` SOLO en el corte (el plunge sigue
con `feed_default`); `S{rpm}M3` antes del G17 (misma fresa) o en el header del cambio de
herramienta. Maestro clampa AL GUARDAR al `feed_rate_max`/`spindle_max` de cada herramienta.
Teardown pre-cambio: `?%ETK[7]=0` va al FINAL del bloque ⇔ hay cambio de herramienta Y la
operación entrante trae Avanz./Rotación (9 transiciones consistentes).

## 15. Datos avanzados (N023 _invert + N028 desactivado/comentado)

- **Invertir trabajo** (`IsGeomSameDirection=false` en el feature): swap de extremos + flip del
  lado FÍSICO (Left→G42); con leads, el arco también flipea (G3↔G2). Validado en Center y lados.
- **Condición** (IsEnabled=false vía expresión): la operación se OMITE del ISO por completo.
- **Comentario**: inerte en el ISO.
- **Cota de seguridad**: ya modelada (§5, security_plane por operación).

## 16. Autoría pgmx forma-Maestro (N031 5/5 → N032 0/4 → N033 4/4 ✅ CERRADA)

Todo el espacio §1-15 es AUTORABLE por el sintetizador (fixtures sin toggles manuales en Maestro).
Modelo derivado del FALLO de N032 (los 4 ISO salieron planos):
- **Maestro postprocesa el toolpath ALMACENADO, no regenera desde la estrategia**: el zigzag va
  como strokes en la `GeomCompositeCurve` del TrajectoryPath (entrada en SUPERFICIE → el Approach
  mide `security`, no `security+prof`). Los cambios on-route van como curva partida (§3) con
  `SpeedAttribute` a nivel toolpath anclado por `ElementKey` al segmento que arranca en su UPar
  (la profundidad es pura geometría: sin atributo de toolpath).
- Lo probado en N031 (rebaba/longitud/invertir/CAD/Avanz-Rotación) son features que el
  POSTPROCESADOR aplica sobre el path almacenado — por eso pasaron con curva plana.
- **`OperationAttribute` en namespace equivocado se ignora EN SILENCIO** (DataContract): elemento
  y escalares en `…MachiningDataModel`, `Key`/`Name` y hojas de claves en `…Utility`, Key con ID
  real reservado; `ElementKey` op-level = 0/System.Object.
Red de regresión offline: `test_pgmx_authoring_structural.py` (subárbol Operation autorado ==
real de Maestro, mod IDs). Validación final: **N033 postprocesado TAL CUAL = 4/4 byte-idéntico**
(2026-07-05) — todo fixture futuro del fresado lineal sale del sintetizador sin tocar Maestro.

## Fuera de alcance

**Fresado en caras laterales**: este CNC no tiene herramental para fresar caras laterales (existe
un agregado instalable, no disponible). El fail-loud del converter (plane ≠ Top) es correcto y
permanente. El trabajo de canto con la E002 (sierra horizontal) se programa DESDE CARA SUPERIOR:
traza cercana al borde, la sierra entra por el canto sin bajar sobre la cara — es fresado lineal
Top normal (§1-2); la traza es responsabilidad del programador de Maestro.

## Pendiente

Derivar las 3 interacciones re-guardadas de N029 con cuerpos completos (multipaso+lado,
lado+leads, multipaso+leads); ZigZag diagonal y uh=0 (ya sintetizables vía §16). Microuniones:
rotas en esta versión de Maestro — candidata a implementación propia post-paridad.

## Experimento-01 ELP/SCS (2026-08-03) — PREDICCIÓN REGISTRADA, esperando los ISO

Par de Fermín en `Programas Manuales\Experimento-01\`:
`Fresado_perimetral_Fresado Lineal_Unidirecional_ELP.pgmx` (En La Pieza) y `..._SCS.pgmx`
(Salida Cota Seguridad). **Analizados antes de tener los ISO** — los dos `.pgmx` son
idénticos salvo un campo: `UnidirectionalMillingStrategySpec.connection_mode`
(`InPiece` vs `SafetyHeight`).

Cada archivo tiene DOS operaciones: (1) *Fresado perimetral* — contorno cerrado, Right,
pasante +1, leads Arco RM=2 En cota; (2) *Fresado Lineal* — una recta (8,290)→(292,290),
ciego −10, Avanz. 2, con la estrategia Unidireccional y **«Habilitar multipaso» APAGADO**
(`allow_multiple_passes=False`, `axial_cutting_depth=0`); su `TrajectoryPath` almacenado
tiene UN solo miembro.

**Predicción falsable (registrada 2026-08-03, ANTES de postprocesar)**: los dos ISO serán
**idénticos entre sí salvo la línea de comentario `% archivo.pgm`** — es decir, el
`connection_mode` es INVISIBLE acá. Razón: la conexión gobierna el retorno ENTRE PASADAS,
y con multipaso apagado hay una sola pasada. Además N036 (`strat_single`) ya derivó que
una estrategia con multipaso apagado **≡ sin estrategia** (cuerpo idéntico al fresado
plano), y por eso el adapter la anula (`_dc_replace(spec, milling_strategy=None)`).
**Si los ISO difieren, esa regla de N036 se cae** y hay que revisarla.

**Lo que estos fixtures SÍ aportan de nuevo**: son los primeros con DOS FAMILIAS de router
en un mismo programa (contorno cerrado → polilínea + línea). Hoy el converter los rechaza
fail-loud por la guarda [B] de *familias mezcladas* — con sus ISO se deriva esa transición
y la guarda se levanta. Cada operación por separado YA pasa validación.

### Matriz 2×2 completa (2026-08-03): + ELP_MP5 / SCS_MP5

Fermín completó el lote a cuatro archivos — misma pieza, misma recta, variando dos ejes:

| archivo | AllowMultiplePasses | AxialCuttingDepth | conexión |
|---|---|---|---|
| `_ELP` | false | **5** | `Straghtline` (En la pieza) |
| `_ELP_MP5` | true | 5 | `Straghtline` |
| `_SCS` | false | **5** | `LiftShiftPlunge` (Salida cota seg.) |
| `_SCS_MP5` | true | 5 | `LiftShiftPlunge` |

**Hallazgo 1 — Maestro CONSERVA «Profundidad de hueco» con el multipaso APAGADO.** Los dos
sin MP traen `AllowMultiplePasses=false` CON `AxialCuttingDepth=5`. Nuestro
`build_unidirectional_milling_strategy_spec` PROHIBÍA esa combinación (`ValueError`), así
que la LECTURA de estos archivos reales **crasheaba**: una regla de AUTORÍA inventada
aplicada al lado de lectura. Corregido — `_extract_milling_strategy_spec_from_operation`
construye las dataclasses Uni/Bi directo, sin la validación del builder: **el snapshot debe
reflejar el archivo**. La guarda sigue vigente para la autoría (decidir si se relaja
también ahí es de Fermín).

**Hallazgo 2 — N036 CONFIRMADA sin necesidad del ISO.** Con `AMP=false` (y cd=5 residual)
la trayectoria ALMACENADA es de UNA sola pasada, a la profundidad final: `_ELP` y `_SCS`
guardan exactamente lo mismo (1 miembro, z=8). O sea que Maestro IGNORA el cd cuando el
checkbox está apagado — la predicción de arriba (ISO idénticos salvo el comentario) se
sostiene ya con la evidencia del `.pgmx`.

**Hallazgo 3 — la conexión, visible y coherente con N025.** Con `AMP=true` la trayectoria
trae las 2 pasadas (z_pieza 13 → 8, o sea ISO −5 y −10) y el retorno entre ellas las
discrimina:

| variante | retorno entre pasadas (z de pieza) | en ISO | regla |
|---|---|---|---|
| `_ELP_MP5` (En la pieza) | 23 | **+5** | z_pasada + `MILLING_RETRACT` (−5+10) |
| `_SCS_MP5` (Salida cota seg.) | 48 | **+30** | la cota de SEGURIDAD |

Ambas calzan con el modelo ya derivado en N025 (`_multipass_cuts`): retorno a
`z + MILLING_RETRACT` (=10, `Programaciones.settingsx MillingRetractDistance`) en InPiece,
y a `security` en SafetyHeight. **Estos fixtures lo CONFIRMAN en contexto nuevo** (y N025
`uni_piece` ya descartaba la lectura alternativa «superficie + 5»: con pasada −8 el
retorno era +2, no +5).

### DERIVADO con los ISO (2026-08-03): MP5 byte-idénticos

**Predicción CONFIRMADA**: los ISO de `_ELP` y `_SCS` (sin multipaso) son idénticos salvo
el comentario del nombre. N036 se sostiene.

**`_ELP_MP5` y `_SCS_MP5` convierten BYTE-IDÉNTICO.** Lo derivado:

1. **La transición entre familias no aporta nada propio**: es exactamente el bloque de
   CAMBIO DE HERRAMIENTA de N028 (E001→E004). La guarda [B] de familias mezcladas quedó
   levantada para polilínea + línea con cambio de fresa.
2. **Alejamiento en op NO-última**: cierra normal (arco, `G1 Z`, `G40`, 1 mm) y recién ahí
   arranca el cambio de fresa. Guarda [A3] levantada para ese caso; con la MISMA fresa
   sigue sin fixture.
3. **El reset EXTRA `?%ETK[7]=0`** de la salida compensada no-última (N036 two_side) **NO
   va cuando cambia la herramienta**: ahí queda uno solo.
4. **`%DONTCARESPEEDV=1`** (marcador nuevo): se emite en el teardown de una op cuando
   ALGUNA op POSTERIOR tiene multipasada con conexión a COTA DE SEGURIDAD — el traslado
   entre pasadas va por el aire. Con «En la pieza» no aparece; con el multipaso apagado
   tampoco (no hay traslado real).
5. **Feeds del multipaso con override de Avanz** (lo que ningún lote previo podía ver,
   porque sin override el feed del catálogo y el efectivo coinciden): el **plunge inicial**
   a la primera pasada y el **traslado por el aire** (SafetyHeight) usan el feed de CORTE
   del CATÁLOGO; las pasadas y el traslado «en la pieza» usan el efectivo (el override).

### ⭐ HITO (2026-08-03): primera EJECUCIÓN EN MÁQUINA de un ISO del converter

Fermín ejecutó los cuatro fixtures en el CNC. Tres corrieron bien; **`SCS_MP5` abortó** con
`Alarma 67: Assegnazione a registro inesistente`, parándose justo antes del cambio de
herramienta. Causa: `%DONTCARESPEEDV=1`, la única línea que ese ISO tiene de más.

**Es una instrucción MAL FORMADA de Maestro**, no config faltante de la máquina:
- el manual de Xilog documenta `SET DONTCARE=1` (sintaxis `SET`, sin `%` ni sufijo
  `SPEEDV`) — suprime el aviso «No existe cota de seguridad encima de la pieza» para el
  trabajo SIGUIENTE, justo lo que Maestro quiere al trasladar por encima de la pieza;
  `%NOMBRE=valor` es, en cambio, asignación a un REGISTRO;
- `DONTCARESPEEDV` no existe en el manual ni en `S:\Xilog Plus` (búsqueda recursiva);
- barrido completo: aparece **1 sola vez en TODO `P:\USBMIX`** (el archivo que falló) y
  **0 veces en `S:\Maestro\Projects`** — ni un `.pgm` de fábrica la usa;
- el manual exige que entre `SET DONTCARE=1` y el trabajo no haya otras instrucciones:
  Maestro mete ~20 líneas en el medio.

**Decisión de Fermín: el converter la OMITE.** Se generó
`P:\...\Experimento-01\scs_mp5_nora.iso` con nuestro converter (146 líneas contra 147,
resto idéntico línea a línea, cp1252 + CRLF) y **se ejecutó en el CNC sin errores**.

Lo que esto cambia: hasta acá la única vara era *byte-idéntico contra Maestro*. Este caso
mostró que esa vara y *ejecutable en la máquina* pueden CONTRADECIRSE — y manda la máquina.
El byte-idéntico sigue siendo el método de derivación (es lo que hace falsables las
reglas), pero deja de ser el fin en sí mismo. Las divergencias deliberadas viven en
`iso.synthesis.compare.DELIBERATE_OMISSIONS`, se reportan siempre y nunca perdonan otras
diferencias. Tests: `test_dontcarespeedv_se_omite_a_proposito`.

### Experimento pendiente: `solo_fresado_lineal_unidireccional_scs_mp5.pgmx`

Generado por NOSOTROS (2026-08-03, a pedido de Fermín) en `Experimento-01\`: el MISMO
fresado lineal del `SCS_MP5` — línea (8,290)→(292,290), E004, Right, ciego −10, Avanz 2,
ACC=false, Unidireccional/SafetyHeight con cd=5 — pero como **ÚNICA operación**, sin el
perimetral. Verificado: estrategia, tecnología, ACC, profundidad y **trayectoria almacenada
IDÉNTICAS** a las de la op original (5 miembros, con las subidas a Z=48).

**Pregunta que aísla**: `%DONTCARESPEEDV=1` aparecía en el teardown de la op ANTERIOR.
Sin op anterior, ¿dónde va — o no va?

**Predicción registrada ANTES de postprocesar**: como el traslado por encima de la pieza
sigue existiendo, Maestro debería emitirla igual, en algún punto previo al trabajo (¿tras
el preámbulo?). Si la emite, su ISO volverá a abortar con la Alarma 67 — y el nuestro no,
porque la omitimos siempre. Si NO la emite, el flag depende de que haya una op previa
donde colgarla, y eso acota todavía más el bug de Maestro.

**CONFIRMADA** (Fermín renombró a `SOLO_Unidirecional_SCS_MP5.pgmx` y postprocesó): Maestro
emite `%DONTCARESPEEDV=1` igual, sin op previa — la pone en el **PREÁMBULO**, entre el 2º y
el 3er par `?%ETK[8]=1`/`G40`. Es decir: la línea no cuelga del teardown de la op anterior;
va en el hueco de instrucciones previas al primer trabajo (**el mismo slot donde va el park
del Xn-al-INICIO**, ver `xn_operacion_nula.md`). El bug es sistemático: aparece siempre que
hay multipasada con conexión a cota de seguridad, y solo cambia de lugar según haya o no
una op antes.

Nuestro converter lo convierte **`funcionalmente_identico`**: 101 líneas de Maestro → 100
nuestras, 0 deltas numéricos, 0 diferencias estructurales — solo la línea inválida omitida.
Emitido para ejecutar como `P:\...\Experimento-01\solo_scs_mp5_nora.iso` (cp1252 + CRLF).

**PRUEBA CRUZADA EN MÁQUINA (2026-08-03) — la causa es única y suficiente.** Se ejecutaron
los dos ISO del MISMO `.pgmx`:

| ISO | origen | resultado en el CNC |
|---|---|---|
| `solo_unidirecional_scs_mp5.iso` | Maestro | **ABORTA** (misma alarma) |
| `solo_scs_mp5_nora.iso` | nuestro converter | **ejecuta perfecto** |

Con el par anterior (`scs_mp5`) da el mismo resultado: **2 de 2 ISO de Maestro abortan, 2
de 2 nuestros ejecutan**, y los archivos son idénticos salvo esa línea. Queda demostrado
que `%DONTCARESPEEDV=1` es causa **única y suficiente** del fallo, y que omitirla es
suficiente para que el programa corra. Refuerzo adicional: nuestro `solo_scs_mp5_nora.iso`
no contiene NINGUNA instrucción que no estuviera ya en `scs_mp5_nora.iso` (verificado línea
a línea), así que no hay otra variable en juego.

**Caso conocido NO derivado (registrado, no escondido)**: `_ELP`/`_SCS` sin multipaso
convierten con UN delta — el plunge va a F5000 (catálogo) en el ISO y a F2000 (feed de
plunge) en el nuestro. Pasa solo con estrategia DECLARADA + multipaso apagado + override
de Avanz: el adapter anula la estrategia (N036 `strat_single`) y el converter pierde la
señal; N028 (override SIN estrategia) sí emite F2000, así que la regla no se puede tocar
sin un lote que separe «hay estrategia» de «hay override». Fijado en
`test_sin_multipaso_queda_un_delta_de_feed_conocido`.

## Hallazgo transversal (N022 Vel/Prof + N007)

El comentario `% x.pgm` del ISO usa el **nombre del archivo** `.pgmx`, no el `piece_name` interno
(`_reader` usa `path.stem`).
