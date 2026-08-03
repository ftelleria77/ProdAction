# Vaciado (pocket milling) — Eje B etapa 5 (EN CURSO, 2026-07-28 — baseline CERRADO)

Operación de la UI: botón **Vaciado** del ribbon. Remoción de material en un área interior
cerrada, con o sin islas. En el `.pgmx`: `ClosedPocket` + `BottomAndSideRoughMilling` +
estrategia `ContourParallel` («Paralela al perfil/contorno»).

**Objetivo de la etapa: la traducción PGMX→ISO.** El lado PGMX (lectura, adaptación y
síntesis de trazas) ya está muy avanzado por el laboratorio
`pgmx/machining_lab/pocket_milling/` — este documento NO lo repite: registra qué de eso nos
sirve, cuáles son las incógnitas PROPIAS del ISO, y el plan de lotes para derivarlas.

## Lo que YA está derivado (lado PGMX — fuentes)

Fuentes, en orden: `pgmx/machining_lab/pocket_milling/memory/current-state.md` (la memoria
grande del lab, corpus `Vaciado_001..035` + variantes `E001..E007`),
`memory/vaciado-v2-rebuild.md` (taxonomía y contrato V2), `docs/synthesize_pgmx_help.md`
(§`build_pocket_spec`), `pgmx.synthesis.milling.pocket` / `pocket_contract` /
`pocket_trace` / `pocket_rectangular`.

- **Modelo XML**: feature `a:ClosedPocket` (campos propios: `BossGeometryList`, `BossList`,
  `BoundaryGeometryList`, `OrthogonalRadius`, `PlanarRadius`, `Slope`), operación
  `a:BottomAndSideRoughMilling`, estrategia `b:ContourParallel`. Solo plano `Top`
  (restricción de dominio: el CNC no tiene herramental de vaciado en otras caras).
- **Mapeo UI↔XML de la estrategia** (tabla completa en el lab): Dirección del recorrido =
  `RotationDirection`; Conexión entre huecos = `StrokeConnectionStrategy`
  (`LiftShiftPlunge` = sube a cota de seguridad / `Straghtline` [sic] = en la pieza);
  Dirección de vaciado = `InsideToOutSide`; Sobreposición % = `Overlap` (0.5 = 50%);
  Habilitar helicoidal = `IsHelicStrategy`; Habilitar multipaso = `AllowMultiplePasses` +
  Profundidad de hueco (`AxialCuttingDepth`) + Último hueco (`AxialFinishCuttingDepth`).
  **Rebaba** = `AllowanceSide` de la OPERACIÓN (no de la estrategia), admite ±.
- **Reglas de traza** (byte-exactas contra Maestro a nivel `.pgmx`):
  `paso_radial = diámetro × (1 − Overlap)`; offset efectivo al contorno = radio +
  `AllowanceSide`; anillos concéntricos con eventos (offset completo/parcial, puente entre
  islas por intersección de circunferencias, lóbulos terminales, contacto con pared,
  micro-empalmes); isla FÍSICA (`BossGeometryList`) ≠ SEMILLA de ruteo
  (`BossList.GeometryID`) — Maestro puede rutear contra una semilla distinta de la isla.
- **Multipaso**: Maestro materializa TODAS las cotas dentro de un único `TrajectoryPath`
  (con subidas a seguridad entre niveles si `LiftShiftPlunge`, o descensos en pieza si
  `Straghtline`).
- **Motor generativo validado**: `pocket_trace`/`pocket_rectangular` reproducen EXACTO el
  `TrajectoryPath` de Maestro para: rectangulares con/sin multipaso, contornos parciales
  (bbox real), semilla balanceada (027) y descentrada (028), dos islas con puentes (029),
  right-wall (030), corredor (031 E001..E007). ⇒ **el sintetizador puede fabricar fixtures
  de vaciado cuya traza NO es la incógnita** (regla 5: fixtures sintetizados legítimos).
- **Frentes PGMX abiertos** (no bloquean la etapa ISO): `Vaciado_031` base,
  `Vaciado_035` (contorno circular; helicoidal activo pero traza a Z constante),
  comando productivo de lote.

## Decisión de arranque (Fermín, 2026-07-28)

El corpus histórico (hoy en `S:\Maestro\Projects\ProdAction\Investigación previa\PGMX\` —
la memoria del lab apunta a la ruta vieja; **no se corrige**) queda INTACTO como **set de
control final**: cuando el converter esté terminado, se postprocesa en masa y valida el
trabajo completo. El desarrollo arranca con **lotes propios** (N047+), la metodología de
todo el workstream: fixtures del sintetizador + postproceso Maestro + derivación
byte-idéntica o fail-loud.

**Nota de UI (Fermín, 2026-07-28)**: el campo de trabajo predeterminado de Maestro es **AB**
— hay que seleccionar HG a mano en «Parámetros de máquinas». Consecuencias: los programas
manuales pueden venir en cualquier campo (los gemelos de N047 salieron en AB sin querer y
se CONSERVAN así: cubren campo AB + footer sin Xn para pockets), y todo lote manual futuro
debe revisar el campo antes de comparar.

## Las incógnitas PROPIAS del ISO (nada de esto tiene referencia todavía)

En P: no existe NINGÚN `.iso` de vaciado. Todo lo siguiente está por derivar:

1. **¿El postprocesador COPIA el `TrajectoryPath` almacenado o regenera?** Todo indica
   copia (N032/N033: Maestro postprocesa lo almacenado; el multipaso ya viene materializado
   adentro), pero se dirime con un ENVENENADO estilo N046 antes de construir nada encima.
2. **Header/familia**: ¿el vaciado es familia ROUTER (mismo header/transición/teardown) o
   trae bloques propios? ¿ETK[7]? ¿Convive con otras familias en un programa?
3. **Entrada**: el `.pgmx` almacena ternas `Approach`/`TrajectoryPath`/`Lift` (¡puede haber
   VARIAS por operación — islas!). ¿Cómo se emiten: G0/G1, plunge a qué feed, qué pasa con
   el `Approach` almacenado?
4. **Cuerpo**: G1/G2/G3 por primitiva del anillo; reglas de palabra Z y de F (¿las mismas
   del ZigZag CAD — Z solo si el redondeo cambia, F en todo?); las subidas a seguridad
   intermedias del multipaso (¿G0 o G1? ¿a qué cota — la de seguridad de la op o la del
   `TrajectoryPath` almacenado?).
5. **Feeds**: mapeo de feed de corte/plunge del catálogo vs Technology embebida; ¿la
   velocidad varía entre anillos/niveles?
6. **Transiciones**: entre las trayectorias de una misma op (islas), entre vaciados, y
   vaciado + otras familias; cambio de herramienta.
7. **Teardown/footer**: ¿retract propio? ¿emite `Lift` almacenado o G0 Z estándar?

## Plan de lotes

- **F2+F3a — `N047_vaciado_baseline`** (~12, incluye los envenenados como N046):
  - 2 ENVENENADOS (primero en importancia: definen la arquitectura del render):
    vaciado rectangular simple con UNA coordenada de un anillo del `TrajectoryPath`
    almacenado corrompida (geométricamente válida), postprocesar SIN ABRIR en Maestro.
    Veneno emitido ⇒ copia (el render lee lo almacenado, como el ZigZag CAD); veneno
    ausente ⇒ recalcula (el render deriva del motor `pocket_trace`, que ya es exacto).
  - ~10 baseline: rectangular pleno, barrido de herramientas (E001/E003/E004/E006/E007 +
    E002/E005 grandes), 2 profundidades ciegas + 1 caso multipaso simple. Deriva: header,
    entrada, cuerpo, feeds, teardown, footer.
- **F3b — `N048_vaciado_estrategia`** (~12): un parámetro por fixture contra el baseline —
  Horario, Straghtline vs LiftShiftPlunge (CON multipaso, que es donde difieren),
  Desde afuera hacia adentro, Overlap 25%, helicoidal, multipaso cd/uh, Rebaba +20/−20,
  AllowanceBottom, pasante si la UI lo permite.
- **F3c — `N049_vaciado_contornos`** (~6): contornos parciales (bbox), arranque en
  distintos puntos del contorno (incl. mitad de borde), contorno que excede la pieza.
- **F3d — `N050_vaciado_islas`** (~10): las 5 topologías cerradas (027/028/029/030/031)
  con 2 herramientas cada una — acá aparecen las trayectorias MÚLTIPLES por operación.
- **Manuales de control** (2-3, los hace Fermín en Maestro sin pasar por el sintetizador):
  el contrapeso de circularidad, como `Galceado_Ar3Cota` en la etapa 4.

Cada lote: derivar → byte-idéntico o fail-loud → documentar acá → tests.

## N047 DERIVADO 13/13 (2026-07-28) — el baseline del vaciado, byte-idéntico

13 fixtures (11 sintetizados + 2 gemelos manuales), TODOS byte-idénticos. Suite 653.

### Los envenenados: el postprocesador COPIA la trayectoria almacenada

`poison_xy` (vértice de anillo corrido +4/+3) y `poison_z` (vértice levantado +1.5) salieron
al ISO CON el veneno (`X80.160 Y79.160`, `Z-7.500`), con el archivo sano limpio. Misma
semántica que el CAD con ACC=false (N046). Consecuencia de arquitectura: **el converter LEE
los TrajectoryPath del `.pgmx`** (`PocketSpec.stored_trajectories`, campo de SOLO lectura
que cablea el adapter, plural porque las islas materializan varias ternas) y los emite —
no recalcula. Nota: a diferencia de los envenenados de N046 (donde recalculamos leads y el
veneno nos delata la divergencia), acá los envenenados convierten byte-idéntico: ambos
lados copian. Son la prueba viva de la semántica — si el render pasara a recalcular, son
los primeros que rompen.

### Los gemelos manuales: cuerpo idéntico + dos reglas de regalo

Dibujados por Fermín en Maestro desde cero (mismos parámetros que `e003_d9` y
`e006_mp_d12`). El CUERPO del mecanizado salió **byte-idéntico al sintetizado** — los dos
puntos ciegos de nuestra autoría quedaron descartados: ni `RadialCuttingDepth=0` ni la
falta de curvas Approach/Lift afectan el ISO (coherente con la copia: el postprocesador usa
el TrajectoryPath, lo demás no lo mira). Diferencias solo ambientales, que se volvieron
evidencia:

1. **Alias de campo "A" → AB**: sin tocar «Parámetros de máquinas», Maestro escribe
   `ExecutionFields=A` (el área default) y su PROPIO postproceso emite el header `-AB` con
   los orígenes del campo AB. El reader mapea solo ese alias; el resto sigue fail-loud.
   Primer vaciado validado fuera de HG, de paso.
2. **Footer sin Xn para pockets**: los manuales no traen Xn → sin `M5`/park X (regla N043),
   y el vaciado cuenta como familia router para la guarda de programas sin Xn.

### El modelo (familia ROUTER + copia)

- Header/transición/teardown estándar del router (`T{n}`/SYN/M06, D1/`SVL`=TLC,
  `SVR`=w/2, teardown D0/G61); PocketSpec entra a `render_router` como una familia más
  (sin `side_of_feature` ni ACC: camino neutro).
- Entrada: `G0` al PRIMER punto de la trayectoria almacenada (anillo más interno con
  dentro→afuera) + `G0 Z{TLC+sec}`.
- Cuerpo (`_pocket_body`): `G1 Z{sec}` a feed de PLUNGE (`feed_default`) → `?%ETK[7]=4`
  (posición estilo multipasada, SIN reset de preamble) → TODO lo demás a feed de CORTE
  (`feed_std`×1000): plunge al primer nivel, un G1 por miembro con la regla de `_g1_cut`
  (borde a un eje repite Z; tramos Z-puros emiten solo Z), y en multipaso las transiciones
  de nivel — subida a security, traslado y bajada — que vienen como miembros de la MISMA
  trayectoria (así materializa LiftShiftPlunge). Retracción final `G1 Z{sec}` a feed de
  corte + `G0 Z` del teardown.
- Z: ISO_z = z_almacenada − ESPESOR (coordenadas de PIEZA, z=0 en la base — igual que el
  ZigZag CAD; el gemelo AB con el mismo origen de pieza lo confirma).
- Validación de render: miembros solo RECTA, cadena CONEXA, nivel final == −profundidad;
  cualquier desvío → fail-loud. Guardas de spec (`_validate_pocket`): solo la forma
  fixtureada (rectángulo a ejes con colineales tolerados, estrategia default ± multipaso,
  ciego, sin leads/rebaba/islas, UNA trayectoria); programa: un solo vaciado, sin mezclar
  familias.

Tests: `tests/test_iso_vaciado.py` (render + guardas offline, e2e 13/13). Implementación:
`_router._pocket_body`, `_validation._validate_pocket`, `_reader` (ruteo + alias de campo),
`adapters._stored_trajectory_primitives_all`.

**Siguiente: N048 (estrategia) — los parámetros no-default hoy guardados.**

## N048 DERIVADO 8/8 (2026-07-29) — los parámetros de la estrategia, LEVANTADOS

Un parámetro aislado por fixture contra el baseline (E003 salvo la rebaba, que va con E006
como Vaciado_015/016 — con E003 la −20 daría offset efectivo negativo, caso que ninguna UI
produce). **8/8 byte-idéntico con solo LEVANTAR las guardas**: ningún parámetro toca las
convenciones de emisión (feeds/orden/G-codes) — todos están MEDIADOS por la trayectoria
almacenada, que ambos lados copian. Suite 657.

| fixture | parámetro UI | qué mostró |
|---|---|---|
| `horario` | Dirección del recorrido | mismos anillos, giro invertido — solo la trayectoria |
| `afuera_adentro` | Dirección de vaciado | arranca por el anillo EXTERNO — solo el orden |
| `overlap25` | Sobreposición 25% | paso 7.14, menos anillos — solo la trayectoria |
| `helicoidal` | Habilitar helicoidal | **flag INVISIBLE**: ni la trayectoria almacenada ni el ISO cambian (cuerpo == baseline; Vaciado_013 ya lo vio a nivel .pgmx) |
| `mp_e003` / `straghtline_mp` | Conexión entre huecos | difieren SOLO en multipaso: transiciones a security (48) vs DENTRO de la pieza — ambas como miembros de la trayectoria |
| `reb_p20` / `reb_m20` | Rebaba ±20 | anillos corridos (60..240 / 20..280) — solo la trayectoria |

Guardas que QUEDAN en `_validate_pocket`: pasante, leads, **AllowanceBottom** (¿la UI lo
expone? — pregunta del checklist; el manual opcional no se hizo), **Cutmode ≠ Climb** (todo
el corpus trae Climb, sin UI conocida), islas/semillas (N050), contornos no rectangulares
(N049), varias trayectorias, multi-vaciado por programa.

Tests: `EndToEndN048Test` (8/8 + helicoidal-invisible) + guardas actualizadas en
`PocketGuardsTest`. **Siguiente: N049 (contornos parciales) y N050 (islas); los manuales
opcionales (pasante / AllowanceBottom) y las capturas de UI siguen pendientes.**

## Capturas de la UI (2026-07-29) — la ventana Vaciado, mapeada

Dos capturas de Fermín (la ventana con `N_V_e001_d9.pgmx` abierto + el detalle de
Estrategia). Lo que fijan:

**Datos vaciado**: Anchura corte (solo lectura, de la herramienta) / Profundidad / Rebaba
(= `AllowanceSide` de la operación — confirmado que vive acá y no en la estrategia) /
**checkbox «Pasante»** — ¡el vaciado pasante EXISTE en la UI! (fixture pendiente; ¿al
tildarlo aparece «extra profundidad» como en Fresado? — por ver).

**Datos tecnológicos**: herramienta + «Parámetros de trabajo»: **Avanz. y Rotación (rpm)**
— el vaciado admite overrides de Technology. Consecuencia inmediata (2026-07-29):
`PocketSpec` ganó `feedrate`/`spindle` de solo lectura cableados por el adapter y
`_validate_pocket` los RECHAZA si vienen cargados — antes un vaciado real con Avanz.
convertía con el feed del catálogo EN SILENCIO. Fixture pendiente para derivar la regla
(esperable: la semántica N009/N028 del router).

**Estrategia**: dropdown «Paralela al perfil», panel «Paralela al contorno» (los dos
nombres para lo mismo, como decía el lab). El panel mapea 1:1 con la tabla UI↔XML del lab:
Dirección del recorrido (Horaria/Antihoraria) = `RotationDirection`; Conexión entre huecos
(«Salida a cota de seguridad»/«En la pieza») = `StrokeConnectionStrategy`; Dirección de
vaciado (adentro↔afuera) = `InsideToOutSide`; Sobrep. (%) = `Overlap`; Habilitar
helicoidal/multipaso + Profundidad hueco/Último hueco = los cuatro campos restantes.
**Respuesta por AUSENCIA**: `RadialCuttingDepth`, `RadialFinishCuttingDepth`, `Cutmode`,
`AllowsBidirectional` y `AllowsFinishCutting` NO tienen control en el panel — son campos
internos que ninguna autoría de UI puede variar. La guarda Cutmode≠Climb queda como
detector de archivos fuera de autoría real, y esos campos dejan de ser preguntas abiertas.

**Acercamiento/Alejamiento** (tercera captura, 2026-07-29): el vaciado expone leads
programables con el MISMO vocabulario que Fresado — Habilitar, 3 íconos de tipo,
«Entrada»/«Salir» (dropdown, «Lineal» visible), «Multipl. radio» (default 2),
«Acercamiento»/«Alejamiento» modo («En cota» visible), «Velocidad», y «Sobreposición» solo
del lado Alejamiento. Mapea a los `ApproachSpec`/`RetractSpec` que `PocketSpec` ya carga
(el adapter ya los lee) — la guarda de leads es correcta y el lote que los derive tiene
vocabulario conocido. Pregunta para ese lote: con la semántica de copia, ¿el lead viaja en
el Approach/Lift almacenado, se recalcula, o ambos (asimetría ACC estilo N046)?

**Datos avanzados** (cuarta captura, 2026-07-29): Condición (=`is_enabled_expr`, «True»),
Comentario, y **Cota de seguridad** (=`security_plane`, 30 en nuestro fixture ✓). A
diferencia de Fresado y Perfilado, **NO tiene «Invertir trabajo»** — coherente: el sentido
del vaciado es la «Dirección del recorrido» de la estrategia, no una inversión del
recorrido. `PocketSpec` no necesita el campo.

**Datos máquina** (quinta y sexta captura, 2026-07-29): mismas Funciones máquina que la
ventana Fresado — Jerk/Jerk3D, Campana neumática (Automática/Posición alta) y auxiliar,
Frenos ejes rotativos (Eje A), Desenrollado cabezal 5 ejes, Soplador, Palpador electrónico
(Offset/Compresión/Ganancia), Regulación de velocidad CN — más Datos cabezales
(Automático ✓). Aplica la MISMA decisión de Fermín de 2026-07-04 para Fresado: sin
relevancia para nuestro uso, quedan en defaults (muchas ni están instaladas en el CNC) —
fuera de alcance.

**Dropdown de estrategias ABIERTO** (séptima captura, 2026-07-29): **UNA sola opción —
«Paralela al perfil»**. No existen otras estrategias de vaciado en esta versión de
Maestro. Consecuencias: (a) el frente de estrategias del vaciado queda **100% CERRADO**
con N048 — no hay opciones que el corpus no pueda haber visto; (b) `ContourParallel` como
único tipo de estrategia de `PocketSpec` no es una simplificación nuestra: es la realidad
de la UI; (c) cualquier `.pgmx` con otra estrategia en un `ClosedPocket` es fuera de
autoría real.

**Pasante tildado** (octava captura, 2026-07-29): al tildarlo, «Profundidad» se fuerza al
ESPESOR (18, solo lectura) y APARECE «Extra profundidad» (default 0) — la misma semántica
del Fresado (N024: profundidad efectiva = espesor + extra). `MillingDepthSpec`
(is_through/extra_depth) ya lo modela tal cual; la guarda del pasante queda hasta que haya
fixture ISO (esperable: trayectoria almacenada a −(espesor+extra) y el render que ya copia
— probablemente solo levantar la guarda, como N048).

**Cómo se dibuja una ISLA** (novena captura, 2026-07-29): la isla es una SEGUNDA
geometría dibujada — **polígono O CÍRCULO** — y el mecanizado se genera con las dos
geometrías seleccionadas (de ahí salen `BossGeometryList`/`BossList` del XML). Tres datos
para N050:
1. **Las islas circulares EXISTEN en la UI** — el corpus del lab solo tiene rectangulares:
   decisión de alcance pendiente para N050 (las guardas actuales rechazan miembros de arco
   en la trayectoria, así que una isla circular hoy es fail-loud correcto).
2. La trayectoria alrededor de la isla trae **esquinas REDONDEADAS = miembros de ARCO**
   incluso con isla rectangular (el lab ya los tenía: arcos Maestro reales de radio = paso
   radial) → N050 exige extender `_pocket_body` a arcos (G2/G3 con I/J, presumiblemente al
   centro absoluto como toda la familia router).
3. En la vista, con isla la estrategia quedó Horaria + Desde afuera hacia adentro —
   combinación a incluir en N050 tal como la UI la propone.

**Décima captura (2026-07-29): el círculo vale en los DOS roles** — contorno exterior E
isla (`N_V_e001_d9_Isla_manual`: anillo entre dos círculos, corona de anillos concéntricos
con conector radial a la entrada). Implicancia clave para el converter: como el ISO COPIA
la trayectoria almacenada, los vaciados circulares NO necesitan el motor circular que el
lab dejó pendiente (`Vaciado_035`) — al converter le alcanza con LEER y emitir arcos. Los
bloqueos reales son solo: (a) el ADAPTER no representa contornos con arcos (hoy caen
unsupported → fail-loud correcto), (b) `_pocket_body` no emite miembros de arco, (c) las
guardas de forma. Y la AUTORÍA de fixtures circulares es MANUAL por regla 5 (nuestro
sintetizador no los emite; la traza la genera Maestro).

**Undécima captura (2026-07-29): rebaba negativa MÁS ALLÁ del radio**
(`N_V_e001_d9_Vaciado_Rebaba_negativa_manual`: E006, Rebaba −75 → offset efectivo
40−75=−35, el recorrido SOBREPASA el contorno hacia afuera). CORRIGE una suposición del
diseño de N048 ("offset efectivo negativo = caso que ninguna UI produce" — FALSO: la UI lo
permite). Dato estructural: al salir del polígono, las esquinas del anillo exterior se
REDONDEAN — ARCOS en la trayectoria almacenada aun sin islas ni círculos (la misma
geometría del offset exterior del CAD, N043). Es el caso de ARCO más simple para el lote
que extienda `_pocket_body` a G2/G3; hoy cae en el fail-loud de miembro Arc (correcto).
Con la guarda de AllowanceSide levantada en N048, el agujero queda cubierto justamente por
ese fail-loud del render — no hay camino silencioso.

**RELEVAMIENTO F1 COMPLETO: 11 capturas, la ventana Vaciado entera + dropdown + Pasante +
isla rectangular y circular + rebaba negativa fuerte. Sin preguntas de UI abiertas.**
Pendientes de lote: N049 contornos parciales, N050 arcos en trayectoria (rebaba negativa
fuerte como caso mínimo + islas rectangulares con el motor como referencia cruzada +
circulares manuales), manuales del pasante y Avanz./Rotación.

## N049 DERIVADO 7/7 (2026-07-30) — contornos, la red que confirmó

Parciales (centrado/esquina/banda), arranque a mitad de borde, contorno horario
(trayectoria idéntica — winding del contorno nominal invisible al postprocesador),
contorno que EXCEDE la pieza, y el caso borde de pocos anillos (E006 con span 40).
**7/7 byte-idéntico DIRECTO, sin levantar nada** — el render copia lo almacenado y el
contorno solo gatea validación. Confirmado: no hay convenciones ocultas por contorno.

## MANUALES DE ARCOS (2026-07-30) — isla rectangular + rebaba negativa, byte-idénticos

Los dos manuales de Fermín (regla 5: la traza la genera Maestro) estrenaron los ARCOS en
la trayectoria del vaciado y derivaron cuatro reglas nuevas:

1. **Arcos**: G3 (normal +z) / G2 (−z), X/Y del fin almacenado, palabra Z solo si el
   redondeo cambia, F siempre. **I/J: el emisor NO copia el centro almacenado — lo
   REAJUSTA a los endpoints redondeados a 3 decimales** (radio = dist(fin redondeado,
   centro almacenado); candidato más cercano al almacenado). Lo delató el ruido
   `I225.001 J224.999` de los anillos de la isla con centro almacenado exacto 225.0; la
   matriz de 7 hipótesis dio 27/27 arcos solo con esta (`_pocket_arc_center`).
2. **Multi-trayectoria** (isla): cada trayectoria almacenada se emite como una PASADA de
   misma fresa (N028): teardown no-último (ETK[7]=0 PRIMERO + G0 Z + D0/SVL/VL6/SVR/VL7)
   + G17/MLV=2 + triple G0 (ancla en el fin de la anterior, entrada ×2) + setup D1 +
   plunge completo. Dos trayectorias fixtureadas; >2 sigue guardado.
3. **Xn AL INICIO** (la rebaba lo trajo de contrabando — el Xn quedó antes del Vaciado):
   el park se emite en el PREAMBLE entre el 2º y el 3er par ETK[8]/G40, con la forma
   `G61/MLV=0/D0/G0 G53 Z/G0 G53 X/G64` y **SIN M5** (el husillo aún no giró); el footer
   va sin M5/park (como sin-Xn). Primer fixture del **Xn POSICIONAL** (Eje C): el reader
   ahora lee la posición del paso Xn en `working_steps` — al final = modelo N015, al
   inicio = preamble (solo router-only), en el MEDIO = fail-loud. Convertía MAL EN
   SILENCIO antes de esto.
4. **Cero negativo**: la trayectoria almacenada trae −0.0 y Maestro emite `0.000` — el
   pocket normaliza todo valor que redondea a cero (`_pos3`).

Guardas nuevas/levantadas: isla RECTANGULAR y rebaba negativa (arcos planos) LEVANTADAS;
arco inclinado, isla no rectangular (circular muestreada), >2 trayectorias, Xn al medio,
Xn-inicio fuera de router-only, Xn-inicio + router compensado → fail-loud.

**El vaciado CIRCULAR con isla circular sigue SIN adaptar** (contorno `GeomCircle`, no
composite): fail-loud correcto en el adapter. Es EL pendiente de la etapa — requiere que
el adapter/spec representen contornos circulares (el render ya emite arcos; el fixture y
su ISO ya están en Programas Manuales). Suite 664.

## VACIADO CIRCULAR (2026-07-31) — representación LISTA; una milésima lo deja guardado

El adapter/spec ya LEEN el círculo: `PocketSpec.contour_circle` (cx, cy, r — sin fabricar
polilínea; `contour_points` queda vacío) y `PocketSpec.boss_circles` (un círculo dibujado
se serializa como composite de 2 arcos concéntricos y el adapter lo reconoce — los
`sampled_points` NO son la isla real). La AUTORÍA los rechaza (`NotImplementedError` en
`_append_pocket`: solo lectura, los fixtures circulares se dibujan en Maestro — regla 5).
De regalo: `Vaciado_035` del corpus del lab (el circular/helicoidal pendiente desde mayo)
ya adapta limpio.

**Pero el anillo NO se declara derivado**: el fixture convierte 143/144 líneas y la que
falta es una MILÉSIMA subdeterminada. `G2 X209.524 Y209.524` (línea 91): Maestro emite
`I150.000 J150.001` y nuestro reajuste da `J150.0004`. Se demostró que ese centro **no es
equidistante de los endpoints redondeados** (dist 84.1800 vs 84.1793) — o sea que NINGÚN
ajuste geométrico sobre los datos del `.pgmx` puede producirlo. Se barrió: fit de 2 puntos
(20 variantes: endpoints exactos/redondeados × 5 fuentes de radio × 2 órdenes aritméticos
× 2 modos de redondeo), circuncentro por 3 puntos (peor: 19/47), y float32 (mucho peor:
cancelación catastrófica en cuerdas casi diametrales). El reajuste actual explica 46/47
arcos de los 3 fixtures con arcos; el que resiste es ruido interno del emisor en un caso
borde (a 0.0005 del corte de redondeo).

Regla 4: antes que aproximar, RECHAZO — `_validate_pocket` deja el contorno circular
fail-loud con el diagnóstico. **Para dirimir hacen falta más fixtures circulares** (2-3
anillos manuales con otro radio/centro/herramienta): más muestras del wobble confirman un
patrón o confirman que esa milésima es irreproducible — y en ese caso la decisión es de
Fermín (sería la primera vez que el byte-idéntico choca con no-determinismo del emisor).
Suite 665 (ahora TAMBIÉN corren los 57 tests del corpus del lab: `EXTERNAL_ROOT` ya
apuntaba a `Investigación previa\PGMX` y la VPN responde — Vaciado_035 re-fixtureado como
"adapta + autoría bloqueada").

## LA MILÉSIMA, RESUELTA POR DATO DE DOMINIO (Fermín, 2026-07-31) — comparador funcional

**Confirmación de Fermín**: Maestro comete errores de cálculo del orden de las MILÉSIMAS
de milímetro — suma o resta algunas milésimas a los parámetros sin razón aparente
(probablemente manejo de coma flotante). La máquina tiene precisión del orden de la
DÉCIMA de milímetro, así que ese ruido es invisible en el mecanizado. La consecuencia
metodológica, pedida por él: al comparar ISOs (Maestro vs converter) hay que poder
IDENTIFICAR esa clase de diferencia — "no byte-idéntico pero probablemente funcionalmente
idéntico".

Implementado: **`iso/synthesis/compare.py`** — clasifica una comparación en
`byte_identico` / `funcionalmente_identico` / `diferente`:
- *funcionalmente idéntico* = mismo ESQUELETO (mismas líneas; los enteros — G2/G3, T{n},
  índices ETK, S — son esqueleto, nunca valores tolerables) con deltas numéricos
  ≤ tolerancia (default 0.005 mm: 20× debajo de la precisión de máquina, arriba del ruido
  observado ±0.001). Cada delta queda REPORTADO — se identifica, no se esconde.
- CLI para la validación masiva del corpus de control:
  `py -m iso.synthesis.compare generado.iso referencia.iso`.

Con eso, **el ANILLO CIRCULAR queda DERIVADO (funcionalmente)**: la guarda se levantó
(forma fixtureada: anillo concéntrico, círculo + una isla circular) y su e2e afirma
`funcionalmente_identico` con EXACTAMENTE un delta de 0.001 en el `J` conocido. El
byte-idéntico sigue siendo el estándar de derivación de todos los lotes; el comparador
entra cuando el byte falla, para separar ruido del emisor de diferencias reales.
Suite 670. Pendientes de la etapa: manuales de pasante y Avanz./Rotación.

## EXPERIMENTO-01 (2026-08-03) — esquinas redondeadas + LEADS, esperando su ISO

`Programas Manuales\Experimento-01\vaciado_interior_esquinas_redondas.pgmx` (Fermín):
DOBLE frente en un fixture — (a) contorno de **rectángulo con esquinas REDONDEADAS**
(5 rectas + 4 arcos r=25, arranque a mitad de borde, E001, ciego −9, una trayectoria de
59 rectas + 8 arcos plana a −9), y (b) **LEADS habilitados** (Acercamiento Line «En
bajada» RM=2, Alejamiento Line «En subida» RM=2) con curvas `Approach`/`Lift`
MATERIALIZADAS en el toolpath — va a responder la pregunta abierta del relevamiento: ¿el
lead del vaciado se emite desde lo almacenado o se recalcula?

Preparado (2026-08-03): el adapter/spec ya representan el contorno con arcos
(`PocketSpec.contour_primitives`, solo lectura, sin aplanar a puntos; autoría bloqueada);
la conversión queda fail-loud por DOS guardas (leads sin fixture + contorno con arcos sin
ISO). Cuando el ISO esté en `P:\USBMIX\ProdAction\Programas Manuales\Experimento-01\`, la
derivación esperable: leer también las curvas Approach/Lift almacenadas, emitirlas donde
el ISO diga, y levantar ambas guardas para la forma fixtureada. Suite 671.

## Experimento-01 (2026-08-03) — SÍNTESIS de contorno con esquinas redondeadas

`Programas Manuales\Experimento-01\vaciado_interior_esquinas_redondas.pgmx`: vaciado con
contorno rectilíneo de **esquinas redondeadas** (rect. 50..250, R25, arranque a mitad del
borde inferior), E001, ciego −9, leads **Line En bajada / En subida RM=2**. Pregunta de
Fermín: *¿podés sintetizar esa pieza?* — **Sí.** El propio fixture es el oráculo (trae la
trayectoria que calculó Maestro): sintetizando desde los parámetros de la UI, los TRES
toolpaths salen EXACTOS — `Approach` (1), `TrajectoryPath` (**67/67**, 59 rectas + 8
arcos) y `Lift` (1) — y el `.pgmx` generado se re-adapta limpio.

**Modelo de trayectoria derivado** (`_rounded_contour_trajectory_primitives`):
- anillos con offset inicial `w/2 + Rebaba` y paso `w×(1−Overlap)`, mientras el anillo
  tenga área (offset < mitad del lado menor);
- recorrido **dentro→afuera**, cada anillo arrancando y cerrando en `(start_x, y0+d)`;
- cada anillo REPITE la forma del contorno con radio de esquina **R−d**; cuando `R−d ≤ 0`
  la esquina es **VIVA** (el anillo es un rectángulo) — por eso solo los 2 anillos
  externos conservan arcos (8 = 4+4) y los 8 internos son rectangulares;
- entre anillos, un **conector recto** sobre `x = start_x`.

**Leads lineales** (`_pocket_lead_offset_xy`, primer vaciado con leads del proyecto — los
78 manuales del corpus del lab van todos con lead deshabilitado = descenso vertical): el
acercamiento arranca a `(w/2)×RM` ANTES del inicio sobre la dirección de avance y baja
inclinado hasta la cota de corte; el alejamiento es su espejo hacia adelante. Sin lead
habilitado (u otro tipo/modo) el descenso sigue siendo VERTICAL — el corpus entero quedó
intacto (verificado archivo por archivo).

**Representación**: `PocketSpec.contour_primitives` (rectas + arcos tal cual el `.pgmx`;
`contour_points` queda vacío) — el adapter ya no rechaza contornos de polilínea con arcos.
Lo NO fixtureado (Horario, afuera→adentro, multipaso sobre contorno con arcos, formas de
contorno distintas de la derivada) → `NotImplementedError`. Tests:
`VaciadoRoundedCornersSynthesisTests`. Suite 674.

## Checklist de capturas de la UI de Maestro (F1 — para Fermín)

Para nomenclatura y criterio (regla 3). De la ventana **Vaciado**:

1. La ventana completa con TODAS las secciones desplegadas (como hicimos con Fresado:
   Datos vaciado / Datos tecnológicos / Estrategia / Acercamiento-Alejamiento / Datos
   avanzados / Datos máquina — los nombres EXACTOS de cada sección y campo).
2. El **dropdown de estrategias** abierto: el corpus solo vio «Paralela al perfil» —
   ¿ofrece otras (raster/zigzag de área/etc.)? Cada opción no vista es un agujero que el
   corpus no puede cubrir por construcción.
3. El panel de la estrategia «Paralela al perfil» completo (para cruzar contra la tabla
   UI↔XML del lab y ver si quedó algún campo sin mapear: `RadialFinishCuttingDepth`,
   `AllowsBidirectional`, `AllowsFinishCutting`, `Cutmode` no tienen UI conocida).
4. ¿La ventana expone **C.N./CAD** (ActivateCNCCorrection) como el Fresado, o no lo
   muestra como el Perfilado? (Cambia qué casos son fabricables por cada ruta.)
5. Cómo se **dibuja una isla**: la secuencia UI (geometría interna → ¿cómo se asocia al
   vaciado?) y el nombre que usa Maestro para isla/semilla en pantalla.
6. **Profundidad**: ¿el vaciado admite pasante? ¿Extra profundidad? ¿Perfilado/acabado
   lateral o de fondo como opción aparte?
7. Datos avanzados y Datos máquina del vaciado (¿mismo contenido que en Fresado?).
