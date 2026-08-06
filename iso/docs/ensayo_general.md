# Ensayo general — corrida del corpus real contra el converter

> Primera corrida: 2026-08-05, rama `iso_converter` (HEAD `b20a9ab` + F0.1 sin commitear),
> herramienta `iso/synthesis/corpus.py` (F0.2). Es la tarea F0.3 del
> [plan de cierre](plan_cierre_converter.md): los 5 corpus de `Investigación previa\`
> convertidos y clasificados contra sus ISO de Maestro. Detalle por archivo en los
> JSONL de la corrida (scratchpad de la sesión; regenerables con el CLI en ~1 min).

## Números

| Corpus | .pgmx | byte | funcional | diferente | fail-loud | sin_iso | ambiguo |
|---|---|---|---|---|---|---|---|
| ISO (histórico `Pieza*`/estudios) | 441 | 127 | 7 | 123 | 148 | 36 | 0 |
| Haeublein (Prod 25-09-04) | 135 | 15 | 14 | 43 | 63 | 0 | 0 |
| DeMarco (Prod 25-11-05) | 384 | 40 | 28 | 106 | 167 | 4 | 39 |
| Cazaux (Prod 26-01-01) | 104 | 6 | 0 | 63 | 35 | 0 | 0 |
| Vargas (Prod-2026-01) | 69 | 0 | 0 | 4 | 2 | 8 | 55 |
| **Total** | **1133** | **188** | **49** | **339** | **415** | **48** | **94** |

Aparte, los 19 lotes de la era drilling (N001–N021): **143/143 byte-idéntico** (+2
huérfanos `sin_iso` conocidos) — quedó fijado como red e2e permanente
(`tests/test_iso_drilling_e2e.py`, F0.4).

## Hallazgos, por peso

### 1. El orden de taladros es la causa dominante de los `diferente` (~300 archivos)

Diff de `Cazaux\Baño\Vanitory\Faja frontal.pgmx` (262 vs 254 líneas): **los mismos
agujeros en otro orden** — Maestro arranca en X34 (vecino más cercano desde el origen),
nosotros en X846 (orden fuente). Bloques enteros de taladro corridos + un
`?%ETK[8]=1/G40` de transición que aparece/desaparece con el orden. Es B-BH-002 tal
cual la describió el emisor viejo. **Confirma F3.1 como la tarea de mayor impacto del
plan**: los ~300 `cantidad de líneas distinta` esperan mayormente eso.

### 2. El fail-loud #1 era del ADAPTER: polilínea de 1 segmento (~162) — F0.8 HECHA

`No se pudo construir el PolylineSpec: Una polilínea de perfil necesita al menos 2
segmentos` — 121 DeMarco + 24 Haeublein + 10 Cazaux + 7 ISO. Diagnóstico: la UI de
Maestro serializa una recta suelta de dos formas (`GeomTrimmedCurve`, o
`GeomCompositeCurve` de UN miembro-recta cuando se dibuja como polilínea de un tramo);
el adapter solo enrutaba la primera a `LineSpec`. **Fix aplicado (2026-08-05)**: la
composite-de-1-recta enruta a `LineSpec` (`pgmx/adapters.py`, rama de recta simple).
Resultado de la re-corrida: los 162 ya no mueren en el adapter, pero **TODOS caen a la
guarda siguiente** (familias mezcladas o leads de polilínea) — los programas reales son
cadenas. Consecuencias: (a) la equivalencia composite-1-recta ≡ recta queda como
hipótesis SIN validación byte hasta que N053/N056 caigan (ahí se valida en masa, gratis);
(b) N056 y N053 suben aún más: familias mezcladas pasó de 13→18 (ISO) y 0→24 (Haeublein
visibles), leads de polilínea 15→19 (Cazaux).

### 3. El ranking real de lotes del backlog

| Guarda golpeada | Archivos | Lote del plan |
|---|---|---|
| polilínea + acercamiento Arco no En cota/Automatic (+velocidad propia) | ~84 | **N053** (confirmado top) |
| canal con lado Right/Left | ~47 | **N055** (SUBE — era cola) |
| familias de router mezcladas | ~27 | **N056** (confirmado) |
| vaciado + acercamiento Arc/Quote | 15 | **M-02** (confirmado) |
| sierra combinada con fresado/taladros | 11 | **N059** (confirmado) |
| patrón de taladros con separaciones no uniformes (adapter) | 5 | nueva variante para N057 o F0.8 |
| alejamiento programable en fresado no-último | 4 | N054 |
| polilínea + estrategia multipasada | 1 | M-04 (a demanda, como estaba) |

Los combos de círculo/arco (N051/N052) **no aparecen** en el corpus real: bajan de
prioridad, exactamente el ajuste que el plan preveía hacer con este ensayo.

### 4. CONTRADICCIÓN de evidencia: mayúsculas del comentario `% nombre.pgm`

- Producción (Cazaux 2026-01): `Faja frontal.pgmx` → `% Faja frontal.pgm` — **preserva**.
- Nuestros manuales (2026-05+): `Galceado.pgmx` → `% galceado.pgm` — **minusculiza**
  (verificado también en `Galceado_Ar3Cota`, `N_V_e001_d9_Isla_manual`,
  `Fresado Lineal_Unidirecional_ELP`).

Ambos son salidas reales de Maestro. **RESUELTO (Fermín, 2026-08-05)**: los archivos se
crean en la PC de oficina técnica y se postprocesan en la PC del CNC — y como los
fixtures actuales también pasan por ahí, el case del comentario CAMBIÓ entre versiones
del emisor (producción 2026-01 preserva; salidas 2026-05+ minusculizan). Es ruido del
emisor, como las milésimas — no una regla derivable. **Decisión aplicada**: el converter
sigue al oráculo vivo (minusculiza); `compare.py` clasifica el case-distinto del
comentario como `funcionalmente_identico` y lo reporta (`comment_case_diffs`; solo
comentarios `% ` — el case de un registro sigue siendo estructural). Tests:
`tests/test_iso_compare.py`. Efecto medido: **Cazaux 63→36 `diferente`,
0→27 funcionales**.

### 5. Pairing ambiguo (94 archivos, casi todo Vargas + DeMarco)

Nombres repetidos entre subcarpetas (varios `Trasera.pgmx`) sin espejo exacto en P: —
el runner no adivina (correcto), pero puede mejorar: match por subruta más cercana.
Mejora del runner pendiente; Vargas quedó casi entero sin clasificar por esto.

### 6. Lo que YA está bien

188 byte-idénticos + 49 funcionalmente idénticos de archivos de producción que el
converter NUNCA había visto — incluidos 28 DeMarco y 14 Haeublein absorbiendo el ruido
de milésimas exactamente como `compare.py` fue diseñado. Toda la era drilling intacta.

### 7. F3.1 HECHA (2026-08-05): B-BH-002 portada y byte-validada en su primer caso real

La regla del orden de taladros verticales quedó portada del emisor viejo a
`iso/synthesis/_reader.py` (`_ordered_top_drills`): ToolKey explícito → orden fuente;
auto → vecino más cercano desde el origen; excepción S055 (4 agujeros/una fresa/
profundidades mixtas tras fresado → max-X/min-Y); bloques por contigüidad FUENTE con
`preceded_by_milling` pegajoso; patrón+autos mezclados → orden fuente (sin evidencia).
Tests unitarios `tests/test_iso_top_drill_order.py` (7). Suite completa 703 — cero
regresión (los fixtures N son explícitos, la regla no los toca).

**Validación real**: el bloque de taladros de `Faja frontal` ya sale byte-correcto
(diff 164→111 líneas; lo que queda es TODO de laterales). Efecto en veredictos:
Haeublein 43→42 `diferente`, DeMarco 106→102 (+4 funcionales). El movimiento es chico
porque casi todos los archivos con taladros verticales auto TAMBIÉN tienen laterales —
**la máscara ahora es B-BH-005 (F3.2)**: rotación de tandas, cota Left espejada, pausas
`G4F0.500`, intercalado side→top→side, y el bloque `?%ETK[8]/G40` de transición.
Tiebreaker equidistante: sigue pendiente de los `Pieza_215..218` (tanda B2).

### 8. F3.2a HECHA (2026-08-05): el orden de CARAS era otro artefacto del corpus propio

**Cuarto punto ciego por construcción descubierto**: la `FACE_PRIORITY` fija
(Front>Left>Right>Back) nunca se probó contra una fuente que la contradijera, porque el
sintetizador PRE-ORDENA las caras al serializar (`_apply_drills`) — testigo:
`N_B008_left_then_front.pgmx`, autorado Left→Front pero serializado Front→Left. La
refutó Cazaux `Faja frontal` (fuente Right→Left, ISO Right→Left). **Regla portada**
(`converter._sort_side_drills`): caras en ORDEN DE APARICIÓN de la fuente (corridas
contiguas; repetidas se funden en su primera aparición) + ROTACIÓN DE TANDA (≥3 corridas,
misma cara al inicio y al final → la última pasa adelante), acotada a Front/Back
(Cazaux rota Back→Front→Back; Haeublein NO rota Right→Left→Right — hipótesis con dos
puntos, el ensayo la re-mide). B007 dentro de cara intacto. Tests
`test_iso_side_drill_order.py` (5). Suite 708, cero regresión.

### 9. Cero negativo del park (2026-08-05): +32 byte-idénticos en DeMarco

`park_y = −Xn.y` con `Xn.y=0` emitía `Y-0.000`; Maestro escribe `Y0.000` (misma regla
del cero negativo que el manual Rebaba_negativa). Fix de una línea en `_preamble.py`
(`+ 0.0`). Efecto: **DeMarco 40→72 byte_identico** (los 32 `funcionalmente_identico`
que tenían SOLO ese delta pasaron a byte).

### 10. Lo que le queda a `Faja frontal` (la disección de F3.2b)

Con orden de taladros y de caras correctos, el diff restante (~109 líneas) se descompone
en CINCO reglas de transición derivables, cada una pendiente de derivación multi-archivo
(Cazaux tiene ~36 similares — no sobreajustar a uno, lección del emisor viejo):

1. **`?%ETK[8]=1 + G40` tras router COMPENSADO** antes del bloque de taladros (nuestros
   lotes nunca combinaron router compensado + taladros).
2. **Cambio de cara LIVIANO Right→Left** (solo `MLV=2×2 + SHF x3`, sin `?%ETK[6]`, sin
   re-park G53, sin máscara, sin S M3 — comparten máscara `2147483648` y grupo de
   velocidad) vs nuestro bloque completo de cambio de cara.
3. **`G4F0.500` entre agujeros laterales en programas MIXTOS** (la condición derivada era
   "solo programas side-only"; Cazaux la muestra con router+top presentes).
4. **Bloque de restauración lateral del footer**: presencia + fórmula del `SHF[Y]`
   (`-1510.600` = origen −1515.6 + origin_y 5, no −1515.6 + DY).
5. ~~Cero negativo del park~~ → HECHA (§9).

## Próximos pasos (en orden)

1. **F0.8** — adapter: polilínea de 1 segmento (~162 archivos). Código nuestro.
2. **F3.1** — portar el orden de taladros del emisor viejo (~300 archivos).
3. Pregunta del case a Fermín (§4) — una respuesta, posiblemente un fix de 1 línea.
4. Runner: pairing por subruta más cercana → re-clasificar Vargas/DeMarco.
5. Re-priorizar B2: **N053 + N055 + N056** (el corpus real las pide); N051/N052 a la cola.
6. Re-correr el ensayo tras cada uno — los números de arriba son la línea de base.
