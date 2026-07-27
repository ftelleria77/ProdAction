# Galceado / Perfilado / Escuadrado — RESUELTO (Eje B etapa 4)

Operación de la UI: botón **Galceado**, panel **Perfilado**. Fresado de un CONTORNO CERRADO
(el borde de la pieza o una geometría dibujada).

**Conclusión: el Galceado NO es una feature nueva del ISO. Es una RUTA DE AUTORÍA distinta hacia
el mismo mecanizado que ya emitimos.** Derivado del lote N043_contour (4 archivos hechos por
Fermín en `S:\Maestro\Projects\ProdAction\Programas Manuales\Lote N043_contour - *.pgmx`).

## El experimento (N043): cuatro rutas, el mismo resultado

Fermín generó el MISMO mecanizado (rectángulo 300×300 del perímetro, E003 Ø9.52, ciego −9)
por cuatro caminos distintos de la UI:

| archivo | feature en el .pgmx | ContourType | ACC | ISO |
|---|---|---|---|---|
| `Galceado-Perfilado - Pieza` | `ContourFeature` | `Workpiece` | true | **A** |
| `Galceado-Perfilado - Geometría` | `ContourFeature` | `Geometry` | true | **A** |
| `Fresado-Escuadrado - CN` | `GeneralProfileFeature` | — | true | **A** |
| `Fresado-Escuadrado - CAD` | `GeneralProfileFeature` | — | false | **B** |

**Los tres primeros son BYTE-IDÉNTICOS entre sí** (única diferencia: el comentario `% archivo.pgm`).

De ahí salen dos hechos duros:

1. **`ContourType` es INVISIBLE en el ISO.** Pieza y Geometría dan el mismo byte. Es una
   comodidad de AUTORÍA (de dónde sale el contorno: del perímetro o de una geometría dibujada);
   para cuando el .pgmx está escrito, la geometría ya está resuelta y el postprocesador no
   vuelve a mirar el `ContourType`.
2. **El TIPO DE FEATURE es INVISIBLE.** `ContourFeature` y `GeneralProfileFeature` con la misma
   geometría y el mismo ACC dan el mismo byte. El Galceado es una ruta de UI, no un mecanizado.

Lo ÚNICO que cambia el ISO es **`ActivateCNCCorrection`** — la dicotomía CAD/C.N. que ya
teníamos derivada del fresado LINEAL (N023 `_CAD`, N036 `cad_*`).

## Dos errores míos que este lote corrigió

**Error 1** (análisis inicial): dije que el estilo lo decidía el `ContourType`.
**Error 2** (análisis "corregido"): dije que lo decidía el ACC, y que el ACC salía del `ContourType`.

Los dos venían del mismo pecado: comparar las dos ops de `Galceado.pgmx` como si solo
difirieran en `ContourType`, cuando en realidad **op1 tenía una estrategia ZigZag y op2 no**.
Y "la estrategia fuerza ACC=false (CAD)" es una regla que **ya habíamos derivado** en N029/N035
para el fresado lineal. El `ContourType` nunca tuvo nada que ver.

El panel de Perfilado **no expone Corrección** (confirmado por Fermín: Datos avanzados solo tiene
Invertir trabajo / Condición / Comentario / Cota de seguridad) y **siempre emite ACC=true**. Por
eso hizo falta la ruta `Fresado-Escuadrado`, que sí la expone: es la única forma de fabricar el
caso CAD de un contorno cerrado.

## Estilo A — ACC=true (C.N.): YA LO EMITIMOS

Es EXACTAMENTE la polilínea cerrada de N042: nominal + G42 + lead de 1 mm.

```
G0 X-1.000 Y0.000                     ← lead-in 1mm antes del arranque (0,0), sobre −û del 1er seg
D1 / SVL 111.500 / SVR 4.760
?%ETK[7]=4
G42
G1 X0.000 Y0.000 Z30.000 F3000.000    ← engancha G42 en el arranque, a security
G1 Z-9.000 F3000.000                  ← plunge a feed de PLUNGE
G1 X300.000 Z-9.000 F18000.000        ← contorno NOMINAL (0,0)→(300,0)→(300,300)→(0,300)→(0,0)
G1 Y300.000 / G1 X0.000 / G1 Y0.000
G1 Z30.000 F18000.000
G40
G1 X0.000 Y-1.000 Z30.000 F18000.000  ← lead-out 1mm sobre +û del último seg
```

**Verificado empíricamente**: desactivando `_detect_squaring_signature` en el adapter (para que
el escuadrado caiga a la rama polilínea), nuestro converter emite este CUERPO **byte-idéntico**,
sin tocar una sola línea del render. Contorno CCW + `SideOfFeature=Right` ⇒ el offset cae AFUERA
⇒ "Externo". Confirma lo que dijo Fermín: por debajo es izquierda/derecha; Externo/Interno es la
etiqueta amigable del lazo cerrado.

## Estilo B — ACC=false (CAD): lo único nuevo son los ARCOS DE ESQUINA

```
G0 X-4.760 Y0.000                                ← arranque YA offseteado (r=4.76), sin lead
G1 Z30.000 F3000.000                             ← baja a security a feed de PLUNGE
?%ETK[7]=4
G1 Z-9.000 F18000.000                            ← plunge a feed de CORTE (¡no de plunge!)
G3 X0.000 Y-4.760 I0.000 J0.000 F18000.000       ← ARCO en la esquina (0,0)
G1 X300.000 Z-9.000 F18000.000                   ← borde inferior offseteado (Y=−4.76)
G3 X304.760 Y0.000 I300.000 J0.000               ← arco esquina (300,0)
G1 Y300.000 Z-9.000                              ← derecha (X=304.76)
G3 X300.000 Y304.760 I300.000 J300.000           ← arco esquina (300,300)
G1 X0.000 Z-9.000                                ← arriba (Y=304.76)
G3 X-4.760 Y300.000 I0.000 J300.000              ← arco esquina (0,300)
G1 Y0.000 Z-9.000                                ← izquierda (X=−4.76), cierra
G1 Z30.000 F18000.000
G0 Z30.000
```

**Modelo**: polígono OFFSETEADO r hacia el lado de la corrección, con un CUARTO DE ARCO en cada
vértice convexo (**radio = radio de fresa, centro = el vértice NOMINAL**, sentido G3 para este
caso), SIN G41/G42 ni leads. Es el estilo CAD del lineal (N023/N036) + la esquina — que en una
recta sola no existe, por eso nunca la vimos.

El arranque `(-4.76, 0)` NO es arbitrario: el arranque nominal `(0,0)` es un VÉRTICE, y el offset
de un vértice es un ARCO. El path empieza donde TERMINA el borde izquierdo offseteado (el
segmento previo, dirección −y, Right ⇒ −x ⇒ X=−4.76) y el primer G3 recorre el arco de esa
esquina hasta el inicio del borde inferior offseteado (dirección +x, Right ⇒ −y ⇒ Y=−4.76).

Detalles del estilo CAD a fijar con más fixtures:
- El plunge a profundidad va a feed de **corte**, no de plunge (el descenso a security sí va a
  feed de plunge). Coincide con lo visto en la op1 de `Galceado.pgmx`.
- El preámbulo CAD **omite** el `?%ETK[7]=0` que sí aparece en el de C.N.
- Falta ver la esquina CÓNCAVA (offset hacia adentro): ¿arco cóncavo, o esquina viva?

## ⚠️ Hallazgo ORTOGONAL: el footer sin `Xn` (bug real de producción)

Al comparar aparecieron 2 líneas de diferencia que NO son del contorno:

| | `Xn` en el .pgmx | footer `M5` | footer `G0 G53 X{park}` |
|---|---|---|---|
| Fixtures N001–N042 (346) | **SÍ** (todos) | sí | sí |
| N043 + `Galceado.pgmx` (hechos a mano) | **NO** | **no** | **no** |

**Los 346 fixtures tienen `Xn` porque los generé yo con nuestro sintetizador, que siempre lo
escribe.** Un .pgmx hecho a mano en Maestro no lo tiene — y sin `Xn`, Maestro NO emite ni `M5`
ni el park X en el footer. Nuestro converter los emite SIEMPRE.

O sea: **el footer está mal para todo archivo hecho a mano**, que son justamente los de
producción real. El corpus nunca lo pudo ver porque está enteramente auto-generado. (El `M5` de
`galceado.iso` es el del CAMBIO DE HERRAMIENTA, no el del footer; su footer tampoco lo tiene.)

Matiza N015: "sin Xn, el default de Maestro" se derivó sin ningún fixture sin `Xn`.

## Implementación (Eje B etapa 4) — HECHA (2026-07-23, 4/4 byte-idéntico, suite 598)

1. **Adapter** ✅: `ContourFeature` va a la MISMA rama que `GeneralProfileFeature` (el tipo es
   invisible; la geometría ya llega resuelta en el XML — no hace falta derivarla del panel). El
   `ContourType` no viaja a la spec.
2. **Escuadrado** ✅ (decisión de Fermín: el `ContourSpec` SE CONSERVA como spec de AUTORÍA de
   En-Juego; el converter unifica). El intercept `_detect_squaring_signature` ahora exige la
   forma que `ContourSpec` puede representar: **arranque a MITAD del borde** (la forma canónica
   de En-Juego — los N043 arrancan en una esquina y `ContourSpec` los re-autoraría con otra
   geometría), **ACC=true** (no tiene campo de corrección: el Escuadrado-CAD perdía el
   `ActivateCNCCorrection=false` EN SILENCIO) y **estrategia None/Uni/Bi**. Todo lo demás cae a
   la rama polilínea, que ganó el campo `activate_cnc_correction` (espejo de la línea; la
   serialización sale sola de `_build_line_operation`).
3. **Render** ✅: A (ACC=true) era la polilínea cerrada de N042 — byte-idéntico sin tocar nada.
   B (ACC=false): `_poly_cad_chain`/`_poly_cad_body` en `_router.py` — offset r=w/2 por borde +
   cuarto de arco por vértice (I/J absolutos al vértice nominal, F en todos los movimientos),
   entrada por el fin del último borde offseteado, plunge a feed de CORTE, sin reset de preamble
   (el predicado de `converter.py` ya excluía ACC=false por getattr). SOLO la forma fixtureada:
   cerrado, rectas, CCW+Right (offset exterior), esquinas convexas a 90° — el resto fail-loud
   (`_validate_polyline_cad`).
4. **Footer sin Xn** ✅ (ya estaba, era pi_converter).
5. `Galceado.pgmx` (ZigZag+CAD en op1, leads Line/Down+Up en op2, cambio E001→E003): sigue
   PENDIENTE como caso de transición — fail-loud con mensaje, ver "Pendientes".
- Tests: `tests/test_iso_galceado.py` (render golden offline + guardas + adapter + e2e 4/4).
- ⚠️ Maestro escribe el ISO en **ANSI (cp1252)**, no UTF-8 — visible recién con "Geometría"
  (lotes previos ASCII puro). Leer referencias con cp1252.

## N044 DERIVADO 11/13 (2026-07-23) — leads Línea + forma En-Juego + CAD estilo B general

13 fixtures en `S:\...\N044_galceado_combos\` (generador `iso/machining_lab/n044_galceado_combos/`).
**11/13 byte-idéntico**, 2 fail-loud por subdeterminación. Tests en `test_iso_galceado.py`, suite 602.

**CN leads LÍNEA compensados** (`app_line`, `app_line_down`, `ret_line`, `ret_line_up`,
`leads_line_down_up`) ✅: lead-in/out lineal al punto exterior (start∓lead·û, lead=w/2×RM); "En
cota" = plunge vertical + línea plana; "En bajada"/"En subida" = rampa (baja/sube en el mismo
movimiento, sin G1 Z aparte). El 1 mm del G40 sigue sobre û. `_poly_body` compensado ganó la rama
Line (approach/retract) + la rama retract Arco.

**Forma EN-JUEGO** (`enjuego`, `enjuego_noleads`) ✅ — RESPUESTA al contour de la App: un
`ContourSpec` se MAPEA a la polilínea del perímetro en el reader (`_contour_to_polyline`, usa
`_build_squaring_outline_points`) y se renderiza como perfil cerrado. Arranca a MITAD del borde
inicial, con o sin leads Arco. `ContourSpec` sigue siendo la spec de AUTORÍA de la App (decisión
de Fermín); esto es solo la traducción de LECTURA del converter.

**CAD estilo B GENERALIZADO** (`cad_concava`, `cad_interno`, `cad_cw_left`, `cad_chaflan`) ✅ —
`_poly_cad_moves` reescrito general: cada borde offseteado r=w/2 (Right=rot90cw/arcos G3,
Left=rot90ccw/arcos G2); cada vértice por el giro cruzado con el lado:
- offset que abre HUECO (Right+giro-izq / Left+giro-der) → **ARCO** (centro=vértice nominal, del
  punto entrante al saliente — un cuarto en 90°, el ángulo del giro en general: el chaflán a 45°
  da un octavo);
- offset que SUPERPONE → **ESQUINA VIVA** (intersección de las rectas offseteadas, sin arco).
- **RESPUESTA a la pregunta estrella**: la esquina CÓNCAVA es **VIVA** (cad_concava: el fondo de
  la muesca; cad_interno: CW+Right = todo interior = todo vivo, rectángulo simple sin arcos).
- Fase de arranque: vértice inicial arco → primero con Right, último con Left; vivo → arranca ahí.

**Fail-loud (2/13, subdeterminados con 1 fixture)**:
- `cad_leads`: el lead CAD usa un cuarto de arco de radio **w/2** (≠ el lead de la línea, w/2×RM)
  anclado tangencialmente al arranque de la traza offseteada — un solo fixture no fija cómo entra RM.
- `cad_zigzag`: ZigZag en contorno CERRADO CAD (= op1 de `Galceado.pgmx`). `build_polyline_spec` ni
  siquiera admite ZigZag hoy (solo Uni/Bi), y el render del zigzag sobre el perfil offseteado no
  está derivado. El adapter lo deja unsupported (fail-loud correcto).

Con N044 quedan destrabables el contour de En-Juego (ya) y, cuando se cierren cad_leads/cad_zigzag
con más fixtures, `Galceado.pgmx` completo (transición + cambio de herramienta).

## N045 DERIVADO 9/9 (2026-07-27) — el LEAD del contorno CAD

Lote para desambiguar los 2 fail-loud de N044, cada uno atado a un solo fixture. El de leads
cerró; el de zigzag no llegó a hacerse (ver "lo que quedó pendiente").

**Pregunta**: N044 midió el lead CAD con RM=2 y le salió radio `w/2` — que NO es el `w/2×RM` del
lead de la línea. ¿El radio es `w/2` fijo y RM no entra, o escala? Un solo fixture no lo fija.

**Respuesta (barrido de RM con la misma fresa + barrido de fresa con la misma RM)**: el lead CAD
usa **las mismas fórmulas que ya teníamos derivadas para estrategia/multipasada** (N034/N035):

| fixture | fresa (w) | RM | lead observado | fórmula |
|---|---|---|---|---|
| `cad_leads_rm1` | E003 (9.52) | 1 | **sin arco** (G0 directo al arranque) | (w/2)×(RM−1) = 0 |
| `cad_leads_rm2` | E003 (9.52) | 2 | r = 4.760 | (w/2)×(RM−1) |
| `cad_leads_rm3` | E003 (9.52) | 3 | r = 9.520 | (w/2)×(RM−1) |
| `cad_leads_e001` | E001 (18.36) | 2 | r = 9.180 | (w/2)×(RM−1) |
| `cad_leads_e004` | E004 (4.0) | 2 | r = 2.000 | (w/2)×(RM−1) |
| `cad_leads_line` | E003 (9.52) | 2 | largo = 9.520 | **(w/2)×RM** (el lineal NO lleva el −1) |

O sea: lo que N044 leyó como "radio `w/2` ≠ `w/2×RM`" era `(w/2)×(RM−1)` evaluado justo en RM=2,
donde ambas dan lo mismo. Las dos dependencias quedan separadas: escala con la fresa por `w/2` y
con RM por `(RM−1)` en arco / `RM` en línea — la misma asimetría arco-vs-línea ya registrada en
`router_line_milling.md` §10 para la estrategia.

**Anclaje**: el lead se ancla a la traza **OFFSETEADA**, no a la nominal — punto de arranque de
la traza CAD y su **tangente** ahí (en el rectángulo: fin del borde izquierdo offseteado,
`(−w/2, 0)`, tangente `(0,−1)`). Geometría idéntica a `_mp_lead_arc`: `Automatic` sigue el lado
del offset (Right → G2 / rot90cw), centro a `lead` perpendicular al avance. En el contorno cerrado
entrada y salida caen en el MISMO punto, así que ambos arcos comparten centro y juntos dibujan un
semicírculo: entra por un lado, sale por el otro.

**Orden en el ISO**: `G1 Z{sec}` (plunge feed) → `?%ETK[7]=4` → `G1 Z−prof` (feed de CORTE) →
**lead-in** → cuerpo offseteado → **lead-out** → `G1 Z{sec}` a feed de corte (el `G0 Z` del
teardown queda). Todo el lead va a feed de corte.

Implementación: `_cad_lead_moves` / `_cad_lead_end` / `_cad_lead_dirs` en `_router.py`, reusando
`_mp_lead`/`_mp_lead_arc`/`_mp_arc_side`. La guarda B4 de leads se reemplazó por
`_validate_cad_lead`. **9/9 byte-idéntico; suite 603.**

**Validación cruzada**: el `N_G_cad_leads` de N044 —el fixture que planteó la pregunta— ahora
cierra byte-idéntico con la regla derivada acá, sin tocarlo (test
`test_cad_leads_de_n044_cierra_con_la_regla_de_n045`).

### ⚠️ Punto ciego de este lote: no prueba que Maestro RECALCULE el lead

Los 9 `.pgmx` se postprocesaron **tal cual salieron del sintetizador**: no se les hizo el paso de
abrir la operación en Maestro, Aceptar (regenerar) y Guardar. Se auditó el ZIP: la traza almacenada
es idéntica a la generada y los `cad_zz` siguen con `ACC=true` sin estrategia.

Para el CUERPO CAD eso no cambia nada (ya venía byte-validado desde N043, cuyo fixture es un
programa manual de Fermín). Para el LEAD sí queda una hipótesis sin cerrar: la curva `Approach`
**almacenada** coincide con lo que emitió el ISO en los 3 casos (arco r=4.76 en rm2, r=9.52 en
rm3, recta 9.52 en line), así que **el lote no distingue si Maestro recalculó el lead del spec o
copió nuestra curva**. Si copió, estaríamos confirmando nuestra propia fórmula.

Contrapeso: la fórmula no se inventó para el CAD — sale de `_mp_lead`/`_mp_lead_arc`, derivadas de
ISOs genuinos en N034/N035; y N029 mostró que los leads se recalculan del spec ignorando la curva
almacenada (al menos con ACC=true).

**Test barato que lo dirime (pendiente)**: un fixture **envenenado** — autorar la curva `Approach`
almacenada con un radio deliberadamente equivocado, dejando el RM del spec correcto. Si el ISO sale
con el radio correcto, Maestro recalcula y todo el lote queda confirmado; si sale con el radio
envenenado, el converter tiene que LEER la curva almacenada en vez de recalcularla. Es el patrón
que hizo prueba por accidente en N029 (`rm3`: almacenado r4/−y equivocado → ISO r6/+y correcto).
No requiere tocar Maestro: se genera y se postprocesa.

### Lo que quedó pendiente: el ZigZag CAD

Los 3 `cad_zz` (−9 / −13 / pasante) salieron del generador en CN sin estrategia, para que la
estrategia ZigZag se agregara en Maestro (que además fuerza `ACC=false` sola). Eso no se hizo, así
que se postprocesaron como contorno CN: **byte-idénticos, pero no cubren el zigzag**. Valen como
regresión de profundidad/pasante en contorno cerrado compensado. `cad_zigzag` sigue fail-loud.

## N046 (2026-07-27) — el fixture ENVENENADO: en CAD manda la curva ALMACENADA

Lote para dirimir el punto ciego de N045: ¿Maestro **recalcula** el lead del spec o **copia** la
curva almacenada? Método: sintetizar normal y envenenar SOLO la curva del lead-in (radio/largo
deliberadamente equivocado, pero geométricamente válida: sigue cerrando tangente en el arranque
de la traza), dejando el RM del spec correcto y **el lead-out intacto como control interno**.

| | almacenado (envenenado) | lo que el spec RM=2 implica | **lo que emitió Maestro** |
|---|---|---|---|
| `poison_arc` | arco r=**12.0**, centro x=−16.76 | r=4.76, centro x=−9.52 | **r=12.0** (`G0 X-16.760 Y12.000`, `I-16.760`) |
| `poison_line` | recta largo **25.0** | largo 9.52 | **largo 25.0** (`G0 X-4.760 Y25.000`) |

**Veredicto: Maestro COPIA la curva almacenada.** Y el control interno lo vuelve incontestable —
en el MISMO ISO, el lead-out (que quedó sano) salió correcto: `G2 X-9.520 Y-4.760 I-9.520` con
r=4.76 en `poison_arc`, largo 9.52 en `poison_line`. Entrada envenenada + salida sana en el mismo
archivo: no hay lectura alternativa.

### Qué corrige esto

1. **La regla del lead de N045 NO está confirmada.** Los 9/9 byte-idénticos son reales, pero
   miden que *nuestro converter reproduce lo que nuestro sintetizador escribió* — Maestro solo
   copió el intermediario. La fórmula (w/2)×(RM−1) sale de `_mp_lead`, derivada en contexto de
   estrategia/C.N.; **cuál es la fórmula de Maestro para el lead CAD sigue sin saberse**.
   El CUERPO CAD no está afectado: viene de N043, cuyo fixture es un programa manual de Fermín.
2. **Matiza la nota de N029** ("los leads se RECALCULAN del spec; la curva Approach almacenada es
   IGNORADA ⇒ fixtures de leads sintetizados = referencias genuinas"). Eso vale con **ACC=true**
   (C.N., donde Maestro regenera y compensa). Con **ACC=false (CAD) es al revés**: la curva
   almacenada manda, como el TrajectoryPath de N032/N033. Coherente con el modelo general —
   Maestro postprocesa lo almacenado y no regenera desde la estrategia.
3. **Consecuencia de diseño**: en CAD el converter debería **LEER** la curva del lead del `.pgmx`
   en vez de recalcularla. Hoy recalcula: byte-idéntico con `.pgmx` de nuestra autoría, apuesta
   con uno hecho a mano en Maestro. El lado de lectura ya existe (`PgmxToolpathSnapshot.curve`).
   Los 2 envenenados quedan como el fixture de regresión de ese cambio: hoy el converter los
   convierte pero NO byte-idéntico (emite 4.76/9.52 donde el ISO trae 12/25).

### Lo que hace falta para cerrarlo de verdad

Un fixture de **autoría manual**: el galceado CAD con lead dibujado en Maestro (RM=2 y RM=3), sin
pasar por el sintetizador. Ahí la curva la calcula Maestro y recién se puede comparar su fórmula
con la nuestra. Es exactamente el caso de la regla 5 (la traza ES la incógnita ⇒ el fixture lo
hace Fermín). Si coincide con (w/2)×(RM−1), el recálculo actual queda validado para cualquier
origen; si no, hay que leer la curva.

### ZigZag CAD: ahora sí hay lote

Los 3 `zz` volvieron con la estrategia agregada (`ZigZagMilling`, ACC=false forzado por la
estrategia). El converter los rechaza fail-loud en el ADAPTER (`build_polyline_spec` no admite
ZigZag). Para derivarlos hay que extender spec + normalizador + adapter y después el render.

## Galceado_Ar3Cota (2026-07-27) — la primera referencia GENUINA del contorno con leads

Fermín dibujó en Maestro un galceado de autoría **100% manual** (pieza 300×300×18 origen 0/0/0,
contorno de pieza, E003, sin estrategia, acercamiento y alejamiento **Arco RM=3 En cota**, ciego −9,
cota de seguridad 30). Salió en **C.N. (`ACC=true`)**, no en CAD — así que NO responde la pregunta
del lead CAD, pero trae dos cosas grandes.

### 1. El converter lo convierte BYTE-IDÉNTICO (104 líneas)

Es la primera vez que el contorno compensado **con leads** se valida contra un archivo donde la
traza y el lead los calculó Maestro y no nuestro sintetizador. El modelo de N042/N044 queda
confirmado sin circularidad: lead-in = arco tangente **anclado al vértice nominal** `(0,0)`,
`G42` (Right), 1 mm de activación antes y 1 mm de salida tras el `G40`, coordenadas nominales.

Radio observado: **14.280 = (w/2)×RM** (4.76×3) — la fórmula single-pass, no la de estrategia.
`G2 X0.000 Y0.000 I0.000 J-14.280` entrando, `G2 X-14.280 Y-14.280 I-14.280 J0.000` saliendo.

### 2. Con ACC=true Maestro IGNORA la curva almacenada — y guarda otra cosa

| | radio | posición |
|---|---|---|
| **almacenado** en el `.pgmx` | **9.520** = (w/2)×(RM−1) | centro (−14.28, 0), ni siquiera toca el arranque del contorno |
| **emitido** al ISO | **14.280** = (w/2)×RM | centro (0, −14.28), anclado al vértice |

Confirma N029 con evidencia fresca y manual: con `ACC=true` el lead se **recalcula del spec** y la
curva guardada se descarta (de hecho Maestro guarda ahí algo que no usa). Junto con N046 —donde con
`ACC=false` el ISO copió el veneno— queda fijada la asimetría:

| | curva almacenada del lead | qué emite el ISO |
|---|---|---|
| **ACC=true** (C.N.) | se IGNORA | recalculado del spec: (w/2)×RM |
| **ACC=false** (CAD) | MANDA | copia literal de lo almacenado |

### Qué dice esto sobre el lead CAD (pista, no conclusión)

Maestro guardó el lead con **(w/2)×(RM−1)** — la misma fórmula que escribe nuestro sintetizador y
que nuestro converter espera en CAD. Si en CAD guardara con esa misma fórmula, entonces (por N046,
que copia lo almacenado) el ISO CAD tendría radio (w/2)×(RM−1) y N045 quedaría confirmado.

**Pero no alcanza para darlo por cerrado**: acá la curva guardada es la de un caso donde Maestro
NO la usa (está mal anclada, es prácticamente un placeholder), y en CAD el lead se ancla a la traza
**offseteada**, no al vértice nominal. Nada garantiza que la calcule igual cuando sí la va a usar.

**Lo que falta es ahora un toggle**: el MISMO programa con la corrección de herramienta en **CAD**
en vez de C.N., guardado y postprocesado. Ahí la curva la calcula Maestro sabiendo que es la que se
va a ejecutar, y se compara contra `(w/2)×(RM−1)=9.52` (nuestra regla) vs `(w/2)×RM=14.28`.
Tests: `EndToEndManualLeadsTest` (byte + la asimetría almacenado/emitido). Suite 605.

## Fresado_perimetral_Ar3Cota CAD/CN (2026-07-27) — el LEAD CAD, CONFIRMADO. Pregunta CERRADA

Fermín hizo el par que faltaba, por la ruta del **Fresado** (que sí expone C.N./CAD — la ventana
del Galceado no lo mostró en los intentos previos): el mismo fresado perimetral (300×300×18,
E003, Right, ciego −9, sec 30, sin estrategia, acercamiento y alejamiento **Arco RM=3 En cota**)
en dos versiones que solo difieren en la corrección: `_CN.pgmx` (ACC=true) y `_CAD.pgmx`
(ACC=false). Autoría 100% manual: ni la traza ni los leads pasaron por nuestro sintetizador.

### Veredicto: la regla de N045 era CORRECTA

En el ISO CAD: `G0 X-14.280 Y9.520` → plunge → `G2 X-4.760 Y0.000 I-14.280 J0.000` —
**radio 9.520 = (w/2)×(RM−1)**, anclado tangente al arranque de la traza OFFSETEADA `(−4.76, 0)`.
Exactamente lo que emite nuestro `_cad_lead_*`. **Ambos convierten BYTE-IDÉNTICO** (CAD 105
líneas, CN 104). La circularidad de N045/N046 queda rota: esta vez la curva la calculó Maestro.

### El modelo completo del lead, ahora coherente

Los dos `.pgmx` almacenan **la MISMA curva de lead**: r=(w/2)×(RM−1) sobre la traza offseteada.
Maestro SIEMPRE guarda el lead en su forma CAD; lo que decide el ACC es qué se ejecuta:

| | curva almacenada | ISO emitido |
|---|---|---|
| **ACC=false (CAD)** | (w/2)×(RM−1) sobre la offseteada | **la copia tal cual** (N046) → (w/2)×(RM−1) |
| **ACC=true (C.N.)** | la misma | la IGNORA y recalcula single-pass: **(w/2)×RM** sobre el vértice nominal + G42 |

Esto también explica el "placeholder mal anclado" de `Galceado_Ar3Cota` (C.N.): no estaba mal
anclado — estaba anclado a la traza offseteada, que en C.N. no es la que se ejecuta.

### Consecuencia de diseño (cierra la de N046)

El recálculo del converter (`_cad_lead_*`) queda VALIDADO para todo el corpus legítimo: Maestro
mismo escribe la curva con nuestra fórmula, así que recalcular y leer-la-almacenada coinciden en
cualquier archivo bien formado (autoría Maestro o nuestra). Los envenenados de N046 quedan como
documentación de la semántica de copia (con almacenado corrupto el converter diverge de Maestro
— aceptable: es un archivo que ninguna autoría real produce).

Tests: `EndToEndManualLeadsTest` (4 fixtures manuales byte + asimetría CAD/CN). Suite 607.
**Galceado/Escuadrado etapa 4: lo único abierto es el ZigZag CAD** (los 3 zz de N046 esperan
spec+adapter+render) y, detrás, `Galceado.pgmx` completo (transición + cambio de herramienta).
