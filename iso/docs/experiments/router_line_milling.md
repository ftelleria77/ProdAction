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

## 3. Cambios DURANTE el recorrido (N022 — N_RT_E001_Vel / N_RT_E001_Prof, hechos en Maestro)

En el `.pgmx` son `Operation > Attributes > OperationAttribute` anclados a **UPar** (posición
paramétrica 0..1 normalizada sobre la trayectoria). El punto es `p = start + upar·(end−start)`.
La autoría del sintetizador NO los serializa (solo lectura): los `.pgmx` los genera Maestro.

- **Cambio de velocidad** (`SpeedAttribute(UPar, Speed m/min)`): la línea se parte en `p`; el
  tramo posterior corre a `F = Speed×1000`. (Vel: `G1 X98 F5000` → `G1 X280 F1000`.)
- **Cambio de profundidad** (`DepthAttribute(UPar, Depth mm)`): **rampa lineal** desde la
  profundidad de la operación (el plunge inicial) hasta `Depth`, alcanzándola en `p` — el G1
  interpola X y Z juntos — y sigue plano. (Prof: `G1 X85 Z-5` → `G1 X280 Z-5`.)

En el `.pgmx` la trayectoria queda partida en segmentos serializados; el converter NO los parsea:
deriva la geometría de los atributos semánticos (validado byte-a-byte).

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

## 8. Guardas fail-loud (combos sin fixture de referencia)

- Más de un cambio de velocidad/profundidad; ambos tipos juntos; UPar ∉ (0,1).
- Cambio de profundidad, corrección de herramienta o corrección de longitud sobre **diagonal**.
- Corrección de herramienta con **varias pasadas** en el programa; combinada con cambios de recorrido.
- Rebaba que deja el corrector negativo (width/2 + rebaba < 0); `Allowance*` ≠ 0 en línea.
- Corrección de longitud + rebaba (¿acorte por w/2 o por SVR?); + cambios de recorrido (UPar
  ambiguo); recorrido degenerado (largo ≤ ancho de fresa).
- Hundimiento: profundidad efectiva > SinkingLength de la fresa.

## Pendiente

Estrategias multipasada Z (roughing), fresado en caras laterales, multi-fresa en un programa,
autoría de las features solo-lectura en el sintetizador, y los combos de arriba (con fixtures).

## Hallazgo transversal (N022 Vel/Prof + N007)

El comentario `% x.pgm` del ISO usa el **nombre del archivo** `.pgmx`, no el `piece_name` interno
(`_reader` usa `path.stem`).
