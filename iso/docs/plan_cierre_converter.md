# Plan de cierre — Converter PGMX→ISO

> Para revisión de Fermín, 2026-08-04. Rama `iso_converter`, HEAD `b20a9ab`, suite 683
> verde. Insumo: auditoría de 8 frentes (sintetizador, converter, corpus, intentos
> previos, docs propios, docs SCM, matriz de cobertura, preguntas abiertas) + ronda de
> verificación adversarial en 3 lentes (evidencia, ejecutabilidad, completitud).
> Nada de este plan se ejecuta hasta que lo apruebes.

---

## 0. Qué significa "terminado" (propuesta a confirmar)

El converter está terminado cuando:

1. **Todo `.pgmx` real de producción convierte** con veredicto `byte_identico` o
   `funcionalmente_identico` (deltas documentados, `compare.py`), **o rebota fail-loud
   con una guarda justificada** (detector de casos fuera de alcance declarado).
2. **Cero conversiones silenciosamente incorrectas**: ningún caso donde el ISO salga
   "convertible" pero distinto de lo que Maestro habría emitido (orden de taladros,
   operaciones dropeadas, etc.).
3. **El set de control final** (`Investigación previa\PGMX\`, 213 `.pgmx` intactos) se
   postprocesa en masa y pasa la vara del punto 1.
4. La documentación del subsistema queda al día (la "fuente de verdad" no miente).

La vara NO incluye (propuesto como fuera de alcance de este cierre, sección 5):
multi-pieza, campos pendulares EF, microuniones, fresado en caras laterales,
expresiones paramétricas.

---

## 1. Diagnóstico en una página

**Lo que hay.** 9 familias convierten en su forma base, ~234 comparaciones e2e
byte-idénticas en la suite, 429 fixtures N001–N049 + manuales + Experimento-01.
El postprocesador COPIA lo almacenado (pockets, CAD) y recalcula leads C.N. — esa
asimetría está derivada y fixtureada (envenenados N046/N047). Dos ISO nuestros
ejecutaron en el CNC real donde los de Maestro abortan.

**Los agujeros, por gravedad:**

| # | Agujero | Gravedad | Evidencia |
|---|---|---|---|
| 1 | **Xmsg/Park/Iso se PIERDEN en silencio**: el adapter los deja `ignored` y el reader no los rebota. Un `.pgmx` real con "Girar pieza" convierte sin esa operación. | Viola la regla 4 — HOY | `pgmx/adapters.py:1806-1826`, `iso/synthesis/_reader.py:233-240` |
| 2 | **Orden de taladros no portado**: con ToolKey `auto` (60/60 Cazaux) Maestro reordena (vecino más cercano; arranque según milling previo) y el converter emite en orden fuente. El corpus N no puede detectarlo: todos llevan ToolKey explícito (punto ciego por construcción, mismo mecanismo que el Xn de CLAUDE.md §5). Ídem side drills: rotación de tandas e intercalado side→top→side. | ISO incorrecto en silencio | emisor viejo `iso_state_synthesis/pgmx_source.py`; S042/S055; experiments/024 |
| 3 | **~660 pares reales nunca corridos** contra el converter nuevo (Cocina 84, Cazaux 104, DeMarco ~338, Haeublein 135). Incluyen agujeros ya conocidos y nunca explicados (2 Vargas con recorrido perímetro/banda). Es el diagnóstico más barato del proyecto y define el backlog real. | Diagnóstico faltante | cero menciones en `iso/` (grep) |
| 4 | **Etapa 5 abierta**: pasante, Avanz./Rotación, círculo pleno, islas (N050), otros modos de lead. Los leads Línea En bajada/subida ya cerraron (Experimento-01). | Guardas fail-loud (correctas) | `_validation.py:594-731` |
| 5 | **~60 guardas de combos sin fixture** en círculo/arco/polilínea/línea/canal + familias mezcladas (las producciones reales MEZCLAN familias; hoy eso rebota). | Fail-loud (correcto) | matriz de cobertura |
| 6 | **Eje C sin derivar**: el flujo real de dos caras (cara A → Xn + Xmsg "girar" → cara B → Xn) jamás fue emitido por ningún converter. Caso real esperando: Vargas `Lat_Der_Cajon_Inf.pgmx`. | Flujo productivo de Fermín | `xn_operacion_nula.md:76-85` |
| 7 | **Taladros sin red e2e**: la era drilling se valida solo offline con ground-truth horneado; una regresión no se vería contra P:. Los pares existen en disco. | Red de regresión | informe corpus |
| 8 | **Deuda documental**: `synthesize_pgmx_help.md` v1.6 atrasado en 8 frentes; `docs/README.md` apunta la generación ISO al subsistema VIEJO; `iso/docs/README.md` describe carpetas vacías; una memoria índice obsoleta (machine config "pendiente" cuando está cerrada). | La regla 2 pierde valor | informe docs |

**El dato nuevo de la auditoría**: el dialecto ISO que emitimos (registros `%ETK`,
`MLV`, `G53`, footer) tiene **cero cobertura** en los manuales transcriptos — pero
`Xilog_Plus_WinXiso.chm` (el entorno de ejecución ISO, instalado en
`Country\Spa\`, no transcripto) es el candidato n°1 a documentarlo. Y
`Languages\es-ES\Post.xml` revela las etapas internas del postprocesador
(`AutomaticMainWorkplanPark`, `GenerateCNToolpath`, `AutomaticFinalPark`…) —
vocabulario oficial para lo que venimos derivando a ciegas.

---

## 2. Las fases

Regla de oro heredada del emisor viejo (lección validada): **cada regla nueva se
valida contra TODOS los corpus antes de conservarla** — una regla que arregla un
corpus puede romper otro (pasó con Cocina 84→30 y con la cota Left de Cazaux).

### F0 — Red de seguridad y diagnóstico (yo sola; arranca apenas apruebes)

| Tarea | Qué es | Salida |
|---|---|---|
| F0.1 | **Guarda Xmsg/Park/Iso** en `_reader`: rebotar steps `ignored` con `runtime_type` ∈ {Xmsg, Park, Iso} con mensaje que diga qué falta. | Agujero #1 cerrado; prerequisito del Eje C |
| F0.2 | **Runner de corpus para `compare.py`** (hoy compara de a pares): recorre un árbol de pares .pgmx/.iso, clasifica byte/funcional/diferente/fail-loud/error y emite informe. | Herramienta del ensayo general y del cierre |
| F0.3 | **Ensayo general**: correr el runner sobre los 4 corpus reales (~660 pares) + corpus histórico `Investigación previa\ISO` (222). Solo lectura de red. De paso cierra dos preguntas heredadas: la prioridad de caras laterales (Q24) y la re-clasificación de los residuales `header_only`/`precision_only` con la hipótesis float32 (Q26). | **El backlog REAL**: qué agujeros golpean archivos de producción y cuáles son teóricos |
| F0.4 | **Red e2e de taladros**: tests byte contra los pares existentes N001/N004–N021 en S:/P: (cp1252, patrón de los e2e nuevos). | Agujero #7 cerrado sin fixtures nuevos |
| F0.5 | **Transcribir `Xilog_Plus_WinXiso.chm`** (y `Testine.chm` si aporta) a `pgmx/docs/` + inspección del snapshot de config (spindles/pheads) buscando la procedencia de las constantes de la sierra (`ETK[17]=257`, `ETK[1]=16`, `G4F1.200`). Si no aparecen en ninguna de las dos fuentes → cierre honesto como Tier D (precedente: peck +1). | Semántica del dialecto ISO; procedencia sierra saldada en un sentido o el otro |
| F0.6 | **Deuda documental**: actualizar `synthesize_pgmx_help.md` (firmas, ArcSpec, multifase, sentinel `DEFAULT_XN`, solo-lectura de PocketSpec), `pgmx_adapters_help.md`, índices de `docs/` e `iso/docs/`, docstrings desactualizados (`_machine_config.py:6-8`), purgar leftovers ya respondidos (Cutmode en fila N048 del índice y en el comentario de `_validation.py:661` — cerrado POR AUSENCIA en la UI el 2026-07-29), y actualizar la memoria índice de machine config (dice "pendiente" algo que está cerrado). | Regla 2 confiable de nuevo |
| F0.7 | **Ciclo de refresco de config** (requisito de Fermín, 2026-08-04: la config de máquina y herramientas se lee SIEMPRE de los archivos extraídos de la PC del CNC; tras calibración, configuración o herramienta nueva, se re-extraen y se sobreescriben en la carpeta del repo). Estado verificado: los `.cfg` YA se leen del snapshot en runtime (`_machine_config.py` → `iso/data/machine_config/snapshot/`) — sobreescribir funciona. **La brecha: `tool_catalog.csv` (`pgmx/data/`) es un derivado A MANO del `def.tlgx`, sin generador** — una herramienta nueva NO llega al converter sobreescribiendo archivos. Tareas: (a) eliminar el paso manual (leer `def.tlgx` del snapshot directo, o regenerador automático del CSV); (b) comando de refresco: regenera el `manifest.csv` (SHA256, hoy sin script) y reporta QUÉ cambió respecto del anterior (herramienta nueva, offset movido, campo recalibrado); (c) instructivo de extracción para Fermín (qué archivos, de dónde en la PC del CNC, a qué carpeta); (d) corregir `iso/data/README.md`, que describe una estructura vieja. | Sobreescribir archivos = converter actualizado, sin tocar código |

F0.3 puede reordenar el resto del plan: si el ensayo muestra que (p.ej.) la sierra
mezclada golpea 40 archivos y los combos de círculo ninguno, F3 sube y N051 baja.
El plan asume el orden por valor esperado; el ensayo lo corrige con datos.

### F1 — Cierre del Vaciado (etapa 5)

Los pendientes declarados + lo que la matriz destapó. Mezcla de fixtures manuales
tuyos (la traza almacenada ES la incógnita — regla 5) y una decisión de alcance.

- **M-01 Círculo pleno** (2-3 fixtures): vaciado con contorno circular sin isla.
  Único caso donde memoria y código divergían: el anillo ya cierra funcional;
  falta el pleno (arco de vuelta completa, `_router.py:1488-1491`).
- **M-02 Pasante + modos de lead** (4): pasante; acercamiento Arco; **alejamiento
  En cota** (es la guarda de retract, distinta de la de approach); lead con
  velocidad.
- **M-03 Avanz./Rotación** (1-2): valores cargados en «Parámetros de trabajo».
- **N050 Islas** (5-6, según decisión D1): isla circular en rectángulo; esquinas
  redondeadas con isla; anillo descentrado; contorno en L; DOS vaciados en un
  programa.
- **Milésima del anillo** (2-3, opcional, se suma a la misma sesión): otros
  radio/centro/fresa para confirmar patrón o no-determinismo del emisor.

Todos con instructivo paso a paso (sección 3, tarea **B4**). Sobre
`AllowanceBottom` hay una contradicción interna a resolver primero (captura C1,
sección 3 — se resuelve mirando las 11 capturas que YA hiciste, no dibujando).

### F2 — Lotes de combos sintetizables (N051–N059)

Los knobs ya son autorables; la incógnita es solo el ISO → los genera el
sintetizador y vos SOLO postprocesás (regla 5a). **F2.0: la generación la hago
yo, después del informe del ensayo F0.3** (así no te hago postprocesar lotes que
el ensayo despriorice) — **te aviso cuando cada tanda esté en S: con su
`INSTRUCCIONES.md`**, como N044–N049. Ninguna sesión tuya arranca antes de ese
aviso.

| Lote | Contenido | ~# | Levanta |
|---|---|---|---|
| N051_circulo_combos | leads En bajada/subida, con velocidad, lado explícito, alejamiento Lineal, **lead Lineal+corrección**, corrección+estrategia, helicoidal horario / +terminación / +leads, **terminación en Uni y en Bi**, Uni+leads, estrategia+pasante | 14 | 12 guardas |
| N052_arco_combos | corrección Int/Ext, leads, estrategia Uni/Bi, **estrategia+lado** | 10 | familia entera de combos |
| N053_polilinea_extremos_arco | 1er/último segmento en arco + corrección/leads; modos de lead C.N. restantes | 10 | 6 guardas — la clase de perfil que traen los reales |
| N054_linea_colas | corrector negativo, CAD+lead variantes, cambios de recorrido+leads, clamps Avanz./Rotación, triples | 12 | 7 guardas |
| N055_canal_combos | leads, rebaba, lado, posición de material Right (+radio final/ángulo si captura C4 confirma que son editables) | 8 | 4-5 guardas |
| N056_familias_mezcladas | sierra+taladro, sierra+línea, línea+círculo, círculo+polilínea, arco+línea, vaciado+línea, alejamiento en op no-última | 10 | crítico: las producciones reales mezclan |
| N057_xn_y_taladros | `xn=None` con taladros/side/mixtos; `extra_depth` en ciego; **patrón de taladros en caras laterales** (pendiente declarado del sintetizador) | 10 | 3 guardas estructurales |
| N058_delta_feed_y_vacios | estrategia declarada sin multipaso vs override de Avanz. (el único delta numérico conocido, hoy en test como divergencia consciente); programas vacíos con y sin Xn | 7 | Q08 + Q27 |
| N059_sierra_transiciones | transiciones top↔canal, lateral↔canal y canal→canal (generadores ya existentes: `tools/studies/iso/tbh007_008_*.py`; evidencia vieja: 18 casos DeMarco) — **es el lote de F3.3** | 8 | sierra mezclada real |

Total ≈ 89 fixtures. Riesgo de sorpresa concentrado en N053 (anclaje de leads en
tangentes de arco — geometría no derivada), N056 y N059 (resets ETK en
transiciones nuevas, zona con historia).

### F3 — Herencia del emisor viejo: orden y sierra

El conocimiento validado sobre ~660 pares reales que el converter nuevo NO tiene:

- **F3.1 Orden de taladros verticales** (B-BH-002): portar la regla de
  `iso_state_synthesis/pgmx_source.py::_ordered_top_drill_block` (ToolKey
  explícito→orden fuente; auto→vecino más cercano, arranque según milling previo).
  El tiebreaker equidistante lo dirimen los `Pieza_215..218` — ya generados,
  viven en `S:\Maestro\Projects\ProdAction\Investigación previa\ISO\` y **nunca
  se postprocesaron** (tarea B2).
- **F3.2 Orden y partición de laterales** (B-BH-005/PGMX-ORD-003): rotación de
  tandas con cara repetida, cota fija Left espejada, pausas `G4F0.500`
  condicionales, y el intercalado side→top→side (el converter hoy asume familias
  monolíticas). Se porta la evidencia y se valida contra el ensayo F0.3.
- **F3.3 Sierra mezclada**: derivar las transiciones con el lote N059 (tabla F2,
  tanda B5) + la memoria vieja como mapa (T-BH-005..009).

Advertencia honesta: el emisor viejo validaba con comparación NORMALIZADA, no
byte a byte. Portar una regla ≠ confiar en ella: cada una se re-valida con la
vara nueva (`compare.py`) sobre los corpus reales.

### F4 — Eje C: el flujo de dos caras

EL flujo productivo tuyo. Depende de F0.1 (sin la guarda, los fixtures con Xmsg
se convertirían perdiendo la operación).

- **M-07 Lote multifase** (3 fixtures manuales, instructivo en B6): (a) Xn al
  inicio + taladros; (b) Xn al inicio + router compensado; (c) el flujo completo
  cara A → Xn + Xmsg «Girar pieza» → cara B → Xn final.
- **F4.2 Derivación**: dónde emite el postprocesador los Xn intermedios y el
  Xmsg (¿pausa? ¿mensaje? ¿park intermedio?). Nadie lo sabe hoy — por eso el
  lote es manual (regla 5b).
- **F4.3 Implementación**: render de Xmsg + varios Xn posicionales + fases;
  autoría de varios Xn para fabricar regresión sintética.
- **F4.4 Validación real**: convertir el Vargas `Lat_Der_Cajon_Inf.pgmx` y
  comparar contra su ISO.

Acá también vive la decisión D2 (default del Xn en autoría).

### F5 — Ensayo final y set de control

1. Re-correr el runner sobre TODO (corpus reales + históricos + N-lotes).
2. Clasificar cada `diferente` restante: bug nuestro / ruido documentable /
   fuera de alcance declarado.
3. **Gatillo de Fermín (D4)**: postproceso EN MASA del set de control final
   (213 `.pgmx` de `Investigación previa\PGMX\` — intactos desde la decisión
   2026-07-28) y corrida final del runner.
4. Informe de cierre: cobertura, divergencias deliberadas (hoy una:
   `%DONTCARESPEEDV=1`), guardas-detectores vigentes, y qué quedó explícitamente
   afuera.

---

## 3. Tus tareas, en orden

Agrupadas por tipo de sesión para que no saltes de contexto. Cada tanda de
postproceso llega con su `INSTRUCCIONES.md` (como N044+); acá va el resumen y el
ORDEN. Regla general del postproceso: abrir el `.pgmx`, NO tocar nada,
postprocesar a `P:\USBMIX\ProdAction\<lote>\` con el mismo nombre (los casos con
otro destino lo dicen explícito).

### B1 — Decisiones (5 minutos, cuando leas este plan)
Las cuatro de la sección 4. D1 condiciona N050; D4 condiciona F5.

### B2 — Tanda de postproceso 1 (~40 archivos, 1-2 sesiones)
**Arranca cuando te avise que los lotes están generados** (F2.0, después del
ensayo F0.3). **Bloquea: F2 y F3.1.** Contenido:
- N051 + N052 + N053 (34), a `P:\USBMIX\ProdAction\<lote>\`.
- `Pieza_215..218` (4, tiebreaker del orden): ya están en
  `S:\Maestro\Projects\ProdAction\Investigación previa\ISO\`; postprocesarlos a
  `P:\USBMIX\ProdAction\Investigación previa\ISO\` como el resto de ese corpus.
- 2 huérfanos históricos sin ISO: `N011\N_SD_through_front.pgmx` y
  `N019\N_FG_left_ef.pgmx`.

### B3 — Capturas UI (3 pantallas, 10 minutos; C1 ANTES de B4)
1. **C1** — hay una contradicción interna a resolver: el relevamiento F1 quedó
   declarado COMPLETO ("sin preguntas de UI abiertas", `vaciado.md:297`), pero la
   guarda de `AllowanceBottom` (`_validation.py:640`) sigue preguntando si la UI
   lo expone. Mirá tus 11 capturas del 2026-07-29 (o la ventana Vaciado directo):
   ¿hay algún control de demasía/rebaba **de fondo** (campo XML
   `AllowanceBottom`), con el nombre que sea? Si NO existe → la guarda queda
   detector permanente y se purga el comentario. Si existe → un fixture más en B4.
2. **C3** — Fresado: ¿algún control de demasía distinto de la «Rebaba»
   (SideOffset)? (campos XML `AllowanceSide/Bottom` de línea, `_validation.py:138`).
3. **C4** — Canal: ¿el «radio final» y el «ángulo» del canal son editables en la
   ventana, o fijos de la sierra? (decide la mitad condicional de N055).

(La captura de Cutmode que pedía el borrador NO va: ya la respondiste POR
AUSENCIA el 2026-07-29 — la guarda queda detector y el leftover se purga en F0.6.)

### B4 — Sesión de dibujo en Maestro: Vaciado (F1; ~13-16 programas)
**Después de C1** (decide si se suma un fixture de AllowanceBottom). La traza
almacenada es la incógnita: estos los dibujás VOS en Maestro, con **Aceptar +
Guardar** (materializa el TrajectoryPath) y postproceso en la misma sesión.
Guardalos en `Programas Manuales\` (o una subcarpeta de lote manual, como los
gemelos de N047) y postprocesá al espejo en P:. Pieza baseline 300×300×18, E001,
como los gemelos de N047, salvo indicación:

1. **M-01a**: Vaciado, contorno círculo (centro ≈150,150, r=50), sin islas,
   ciego −9, leads deshabilitados. **M-01b**: ídem con r≈15 (menor al diámetro
   de E001, 18.36 — pocket de un solo anillo). **M-01c** (si la UI lo acepta):
   r≈5 (menor al radio de la fresa, 9.18).
2. **M-02a**: rectangular baseline con «Pasante» tildado. **M-02b**: ciego con
   Acercamiento Arco. **M-02c**: **Alejamiento En cota**. **M-02d**: lead con
   velocidad propia cargada.
3. **M-03**: rectangular baseline con Avanz. y Rotación cargados en «Parámetros
   de trabajo» (p.ej. 4 m/min / 15000 rpm).
4. **N050** (según D1): a) rectángulo con isla circular; b) esquinas redondeadas
   con isla rectangular; c) anillo con isla descentrada; d) contorno en L;
   e) DOS vaciados en el mismo programa.
5. **Milésima** (opcional): 2 anillos más con otro radio/centro/fresa.
6. **M-08** (1 programa, es de Fresado no de Vaciado, pero entra en la misma
   sesión): línea con estrategia + lado + C.N. activado en la UI — el objetivo
   es SOLO confirmar si Maestro fuerza CAD al aceptar (si lo fuerza, esa guarda
   pasa a prohibición permanente documentada).

### B5 — Tanda de postproceso 2 (~55 archivos, 2 sesiones)
**Después de C4** (decide la mitad de N055) **y de mi aviso de generación**.
Contenido: N054 + N055 + N056 + N057 + N058 + N059. N056 y N059 son las de mayor
valor para el corpus real (familias mezcladas y sierra).

### B6 — Sesión de dibujo en Maestro: Eje C (F4; 3 programas)
**Después de F0.1** (te aviso). Pieza baseline; en cada programa: dibujar,
**Aceptar + Guardar**, y postprocesar en la misma sesión. Guardar en
`Programas Manuales\` (subcarpeta EjeC si preferís) y espejo en P::
1. Taladros verticales + **Xn al inicio** del workplan.
2. Perimetral compensado + **Xn al inicio**.
3. El flujo completo: mecanizado cara A → **Xn** → **Xmsg «Girar pieza»** (paro
   con espera de inicio) → mecanizado cara B → **Xn final**. Como lo harías en
   producción real — esa ES la referencia.

### B7 — Sesiones a demanda (M-04/M-05/M-06)
Variantes de CAD, ZigZag CAD y estrategia-sobre-polilínea: **solo si el ensayo
general (F0.3) muestra que archivos reales las golpean**. Rinde bajo por unidad
y máxima probabilidad de sorpresa — no conviene hacerlas de antemano. Te las
pido puntualmente con instructivo si hacen falta.

### B8 — Postproceso masivo final (F5, gatillo D4)
Los 213 del set de control, cuando declares el gatillo. Confirmado por Fermín
(2026-08-04): **Maestro postprocesa de a una pieza** — no hay lote. Al ritmo
histórico (máx. 32 por sesión) son ~7 sesiones. El gatillo puede dispararse en
tandas (el ISO de referencia no depende de cuándo se postprocesa, solo de la
config de máquina, hoy sin drift); la corrida del runner sí es de un saque al
final. Cómo repartirlo queda a tu criterio con D4.

**Camino crítico**: B1 → [yo: F0 + generación de lotes] → B2 (habilita F2+F3.1)
y, en paralelo, C1 → B4 (habilita F1). B5 espera C4 + generación. B6 espera
F0.1. B7 espera el informe del ensayo. B8 espera todo lo demás.

---

## 4. Decisiones que te pido (D1–D4)

| # | Decisión | Contexto | Mi recomendación |
|---|---|---|---|
| D1 | **Alcance de islas** (Q06): ¿islas circulares y contornos en L entran en el cierre, o quedan como detector? | La UI las expone (captura 9ª); el corpus del lab solo tiene rectangulares. 75% del set de control final es Vaciado — probable que aparezcan. | Entran (N050 completo). Si el postproceso destapa un modelo de traza nuevo, se re-evalúa. |
| D2 | **Default del Xn en autoría** (Q14): nuestro default escribe un Xn; el de Maestro, ninguno. | Invertirlo rompe la regeneración de los 346 fixtures históricos. | Posponer a F4: decidirlo con la evidencia de M-07 en la mano, no antes. |
| D3 | **Regla 4 del CLAUDE.md** (Q29iii): ¿se reescribe con el matiz "byte-idéntico es el método; ejecutable manda"? | Hoy hay UNA divergencia deliberada documentada. | Reescribirla al cierre (F5), con la lista final de divergencias como anexo. |
| D4 | **Gatillo del set de control final** (Q28): ¿cuándo se declara "terminado" y se postprocesan los 213? | Decisión tuya del 2026-07-28. | Tras F3 cerrada y el ensayo F5.1 limpio. |

---

## 5. Fuera de alcance propuesto (confirmás vos)

- **Multi-pieza** (Q15): workstream siguiente. La doc SCM ya está mapeada
  (`04_4_programa_multiple.md` + `.mix` real de ejemplo).
- **La app de conversión por lotes** (objetivo de producto declarado por Fermín,
  2026-08-04): una aplicación que convierta proyectos enteros — varias carpetas,
  múltiples piezas — de un saque. Es EL "para qué" de este cierre: reemplaza el
  postproceso pieza-por-pieza de Maestro. No es parte de este plan, pero ordena
  sus prioridades (por eso N056/familias mezcladas y el Eje C pesan tanto), y el
  runner de F0.2 es su embrión.
- **Campos pendulares EF/AB/DC** (Q16): requiere recalibrar EF en la máquina
  (paso físico) + re-snapshot + fixtures. Workstream propio.
- **Microuniones** (Q10): post-paridad; primera feature más allá de Maestro
  (el atributo está roto en esta versión); validación EN máquina, sin oráculo.
- **Expresiones paramétricas** (guarda `_validation.py:100`): requieren un motor
  de evaluación — workstream propio. Consecuencia honesta: los 4 `.pgmx`
  paramétricos del set de control final quedarán fail-loud justificado.
- **Fresado en caras laterales / abocinado / Ø sin herramienta**: hardware.
- **Xmsg con Variable/Input** (Q17): esperar caso real (tu criterio previo).
- **Motores de síntesis del lab** (Q07: Vaciado_031/035, comando de lote): no
  bloquean el converter (que COPIA lo almacenado); frente PGMX aparte.

---

## 6. Riesgos y cómo los acota el plan

1. **Maestro contradice una regla portada del emisor viejo** (F3): mitigado
   porque TODO se re-valida byte a byte contra los corpus reales; la memoria
   vieja es mapa, no evidencia.
2. **Los leads anclados en arcos** (N053) pueden traer geometría nueva:
   lote chico y temprano, con derivación dedicada.
3. **El Eje C puede revelar estructura ISO nueva** (bloques de fase): por eso
   va con lote manual y derivación propia ANTES de implementar.
4. **El ensayo general puede destapar volumen** (cientos de `diferente`): es el
   objetivo — mejor ahora que en el postproceso masivo final. El plan se
   re-prioriza con ese informe (es un documento, lo vas a ver).
5. **La validación de cota Z que `%DONTCARESPEEDV` suprimía** (Q29ii): al
   omitirla, el CN queda a cargo del chequeo «no existe cota de seguridad encima
   de la pieza». Los 2/2 corrieron sin aviso, pero no hay derivación general.
   Mitigación: F0.5 (¿el CHM documenta el equivalente ISO de `SET DONTCARE=1`?)
   y, si querés cerrarlo del todo, una prueba controlada en máquina (tu llamada
   — no la agendo sin tu ok).
6. **Ruido de milésimas**: ya domado (`compare.py` + tolerancia 0.005 +
   omisiones deliberadas reportadas siempre).
7. **La config cambia a mitad del plan** (calibración, herramienta nueva): los
   ISO de referencia valen para la config con la que se postprocesaron. F0.7
   vuelve trivial el refresco (sobreescribir + comando de chequeo) y el
   `manifest.csv` con hashes delata y FECHA cada cambio — si un corpus se
   postprocesó bajo config vieja, se sabe cuál.

---

## 7. Tablero de cierre

Métricas que definen "terminado" (se actualizan en cada informe):

- Guardas levantadas / totales (hoy: ~119 en `_validation.py` + 24 en
  reader/converter/render; objetivo: cada una byte-validada, detector
  documentado, o prohibición con evidencia).
- Corpus reales: X/~660 en `byte_identico`+`funcionalmente_identico`+
  fail-loud-justificado (hoy: sin correr).
- Set de control final: X/213 (hoy: 0, esperando gatillo).
- e2e en suite: ~234 byte + red de taladros (hoy: sin red).
- Divergencias deliberadas documentadas: 1 (`%DONTCARESPEEDV=1`).
- Deuda documental: 17 ítems detectados (hoy: 0 saldados).
