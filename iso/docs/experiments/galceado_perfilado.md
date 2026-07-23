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
