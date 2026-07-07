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

GUARDAS RESTANTES:
- **Pendientes de REGENERACIÓN en Maestro** (los fixtures N036 son ECO de nuestra trayectoria y
  no prueban el comportamiento real): CAD+longitud (cad_long), CAD+invertir (inv_cad),
  invertir+estrategia (inv_mp) — regenerar el recorrido y re-postprocesar para derivarlas.
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

## Hallazgo transversal (N022 Vel/Prof + N007)

El comentario `% x.pgm` del ISO usa el **nombre del archivo** `.pgmx`, no el `piece_name` interno
(`_reader` usa `path.stem`).
