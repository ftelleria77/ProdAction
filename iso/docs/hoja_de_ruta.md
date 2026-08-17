# Hoja de ruta de la reinvestigación PGMX → ISO

**Documento VIVO.** Registra el trayecto recorrido (bitácora, abajo) y establece el camino
por delante en la medida en que los hallazgos lo van definiendo. Se actualiza en cada hito:
lo recorrido se AGREGA a la bitácora (nunca se reescribe), el mapa se REVISA (los cambios de
rumbo se anotan como decisiones con fecha). La vista visual se republica en cada hito
(artifact "Reinvestigación PGMX→ISO", URL estable).

Estados: ✅ hecho · 🔄 en curso · ⏸ esperando a Fermín · ⬜ pendiente · 🔮 futuro (sin fecha)

## Estado actual (2026-08-17)

> ⭐⭐ **A7 CERRADO ENTERO, y con una respuesta negativa que vale tanto como una positiva:
> ni un parámetro sin usar ni una geometría sin mecanizado dejan rastro en el ISO.** Los
> ocho fixtures postprocesados en el CNC dan ISO **idénticos al del programa vacío** salvo
> la línea 1, que lleva el nombre del archivo. Control cruzado: la diferencia de bytes de
> cada uno es exactamente el largo de más del nombre.
>
> ⇒ **El converter puede ignorar los parámetros y las geometrías que nadie usa.** Y todo
> lo derivado sobre la ventana «Parámetro» no sirve para *emitir* ISO: sirve para que el
> **sintetizador** fabrique `.pgmx` válidos, que es de donde salen los fixtures.
>
> ⚠️ Vale para el caso **sin uso**. Un parámetro que alimenta una cota, o una geometría
> que un mecanizado toma, es la rama **D** y no está derivado.
>
> ⏭️ Con A7 cerrado, el orden que fijó Fermín el 2026-08-13 pone **C (operaciones de
> máquina: Xn · Xmsg · Park)** como lo que sigue. La rama de dibujos quedó abierta con la
> línea derivada y siete geometrías más sin barrer.

## El estado del 2026-08-16

> ⭐⭐ **A7 se destrabó y su etapa 1 quedó CERRADA.** Los fixtures llegaron: seis `.pgmx`
> manuales de Fermín cerraron **toda la ventana «Parámetro»** —los tres tipos, las tres
> unidades, el signo, el separador decimal y la precisión— y dos más abrieron la rama de
> **dibujos** con la línea. Docs nuevos: `experiments/parametros.md` y
> `experiments/dibujos.md`.
>
> ⚖️ **DECISIÓN DE MÉTODO (Fermín, 2026-08-16): el `.pgmx` que produce nuestro
> sintetizador tiene que ser FUNCIONALMENTE idéntico al de Maestro, no byte-idéntico.**
> El byte-idéntico sigue rigiendo donde importa —el `.iso`, que es el producto del
> converter (regla 4 del CLAUDE.md)—; el `.pgmx` es la herramienta con la que fabricamos
> fixtures, y una diferencia que no cambia la pieza no es un defecto. Con esa vara:
> - el decimal truncado **SÍ** era defecto (cambia el valor) → corregido;
> - la dirección con 1 ULP **NO** lo es (5·10⁻¹⁴ mm) → documentada, no se toca.
>
> ⏭️ **Modo de trabajo en curso**: juntar la evidencia primero y hacer **todas** las
> modificaciones después, en una sola pasada.
>
> **A7 corrigió su propio planteo**: «parámetros de usuario **y** dimensiones
> paramétricas» son **un solo mecanismo** — `dx1`/`dy1`/`dz1` son parámetros comunes, y lo
> que los ata a la pieza es un `Parametrics.Expression` aparte.
>
> **Sigue pendiente el postproceso**: si un parámetro sin uso —o una geometría sin
> mecanizado— deja rastro en el ISO. Es lo único que falta para cerrar A7 entero.

## El estado del 2026-08-14

> ⭐⭐ **El esqueleto es UN DIALECTO ENTRE CUATRO, y ahora sabemos cuál.** `PostISO.dll` sabe
> emitir `ISO-OSAI(2)`, `ISO-ESAGV(2)`, `ISO-NUM` e `ISO-ORCHESTRA`; la clave que elige
> (`[CNCNAME]` de `Nci.ini`) está **vacía** en esta máquina. La guía de diagnóstico de SCM
> (`9031191610B` v4.2) cierra cuál es: en los CNC **ESA-GV** las variables `E..` «se
> transformarán en `ETK..`», y nuestro ISO usa `ETK`/`EDK` ⇒ **la Pratix es CNC ESA-GV**.
>
> Con eso, tres de los cinco tokens sin significado salen de DESCONOCIDO: **`EDK` es un bit de
> intercambio CNC→PLC** (y sus bandas confirman lo que R002 había derivado a ciegas),
> **`ETK` tiene bandas por función** —y `ETK[8]` es del **cambio de herramienta**—, y
> **`VL6`/`VL7` llevan la longitud y el radio de la herramienta**, derivados contra el
> catálogo sobre ~2.000 ISO. Detalle en `experiments/anatomia_iso.md`, B1i.
>
> ⚠️ **Primer defecto real encontrado en `emisor_iso.cfg`**: tenía `?%ETK[8]=1` congelado sin
> salvedad. No es constante. Ya está anotado en el archivo.
>
> **A7 sigue bloqueado**: los fixtures de parámetros de usuario y dimensiones paramétricas no
> están en S: ni en P: (lo más nuevo es del 08-13 08:59).

## El estado anterior (2026-08-13)

> ⭐ **Lo más importante de esos dos días**: el postproceso **tiene dos etapas**
> (`.pgmx` → XXL → PGM → ISO) y casi todo lo que veníamos investigando ocurre en la
> **segunda**, que la hace el generador de Xilog y no Maestro. Con eso encajan de golpe el
> preámbulo que sale de `NCI.CFG`, el origen que se resuelve contra `fields.cfg`, y el
> resultado más repetido del barrido: 16 de 17 opciones de la ventana Opciones no llegan al
> ISO porque actúan en la etapa 1. Y las dos PCs producen el **mismo** XXL, así que toda la
> diferencia entre máquinas vive en la etapa 2. Detalle en `experiments/emisor_iso.md`.
>
> **De las 43 líneas del ISO del programa vacío, sólo dos vienen del XXL.** Las otras 41 las
> pone la segunda etapa — configuración de máquina y emisor.

## El estado del 2026-08-12 (tarde)

La etapa 1 ya tiene su ISO de referencia y dos barridos de configuración completos (A5
parámetros de máquina, A6 ventana Opciones). El hallazgo que ordena todo lo demás: **el
esqueleto del ISO no es una plantilla fija**. Lo pueden reescribir dos de los tres orígenes
—la ventana Opciones le agrega líneas (B1d) y `NCI.CFG` le define el preámbulo entero
(B1f)—, así que ninguna de esas líneas puede vivir escrita dentro del converter.

**B1: las 43 líneas tienen origen identificado salvo `?%ETK[8]=1`.** De las que no salen del
`.pgmx` ni de un `.cfg`, ahora se sabe **qué binario las escribe** (B1g). Lo que sigue
abierto no es de dónde vienen sino **qué significan** (`MLV`, `VL6`, `VL7`, `EDK[0/1]`,
`SYN`) — y una pregunta de método: si «el emisor» es un **cuarto origen**.

A5/A6 quedaron cerrados para el programa vacío: de todo el barrido de configuración, **una
sola opción cambia el ISO de un programa sin operaciones** (el estacionamiento automático).
Frentes abiertos: el paso 0 de la serie R_OPC en oficina técnica y el experimento de las dos
PCs, que necesita un programa **con mecanizado**. Suite: 291 passed, 100% offline.

## El mapa: troncos y ramificaciones

El orden DENTRO de cada tronco y el orden entre troncos es dinámico: lo deciden los
hallazgos. Lo único fijo es el método (regla de la época): fixtures propios de variación
controlada (serie R), byte-idéntico o fail-loud, nomenclatura genérica de Maestro.

### A. Configuración de programa — 🔄 en curso (etapa 1)
- A1. Programa vacío, lote R001 (7 variaciones: base, dims, origen XY, origen Z, campo EF,
  Xn, variable) — ✅ generado · ⏸ postproceso
- A2. Repaso opción por opción contra la UI de Maestro (capturas) — ⏸ capturas
- A3. Opciones que el synth no varía (offset de pieza, repeticiones, ciclo continuo, espejo
  tecnológico, opciones de mesa/mecánica) → gemelos manuales, una opción por archivo — ⬜
- A4. Fases (workplans) y orígenes múltiples — 🔮
- A5. **Parámetros de máquina** (serie R_PM) — ✅ **29 fixtures manuales (2026-08-10)**:
  16 llegan al ISO (14 mueven `V`, 2 mueven `T`), 12 no llegan y 1 rompe el postproceso
  (`Combiflex`). **Todas las diferencias caen en la línea del header**, ninguna toca el
  resto del esqueleto. Resultados en `experiments/parametros_de_maquina.md`. Falta sólo
  `Repeticiones`, que quedó fuera del barrido.
- A6. **Opciones de la aplicación** (serie R_OPC, el TERCER origen) — ✅ **17 fixtures
  manuales (2026-08-10/12)** para el programa vacío. **Una sola opción cambia el ISO**: el
  **estacionamiento automático al terminar**, que le agrega dos líneas. El resto no llega
  —las cuatro de acercamiento y alejamiento, la compatibilidad tecnológica, el
  estacionamiento por cambio de fase (probado con 2 y 3 fases) y, el 08-12, las **dos de
  prioridad 1** (`IsAreaScm`, `IsZetaScm`) más `IsBottomPlaneMachining` y
  `IsCheckCollisionEnabled`. Resultados en `experiments/opciones_de_aplicacion.md`.
  Quedan para cuando haya mecanizado: la familia que gobierna trazas e `IsMM`.
  > ⬇️ **`PostFileFormat`, de baja prioridad (2026-08-14).** Se había propuesto un fixture
  > barato (postprocesar el vacío con `XXL` y con `PGM`) para confirmar que la cadena es una
  > sola y el selector sólo decide dónde se detiene. **Confirmaría un modelo que ya no nos
  > importa**: el converter va de `.pgmx` a `.iso` y no emite ninguno de los otros dos
  > formatos. Queda anotado, no priorizado.

> ✅ **CUMPLIDO el 2026-08-12**: las dos opciones de `Parámetros → Post` (`IsAreaScm`,
> `IsZetaScm`) se barrieron y **ninguna llega al ISO del programa vacío**. La fórmula del
> origen de B1c no depende del tope de referencia; la notación de Z necesita una
> profundidad de trabajo, que un programa sin operaciones no tiene.
>
> ✅ **PASO 0 HECHO el 2026-08-12, con un resultado que nadie esperaba.** Oficina técnica
> **no genera ISO**: genera XXL + PGM + INF, y ahí apareció que el postproceso tiene **dos
> etapas** (`emisor_iso.md`). Respuestas: el barrido **no** se puede mudar a oficina técnica
> —sigue en el CNC—, y el experimento de las dos PCs hay que replantearlo, porque si una de
> las dos no emite ISO no hay dos ISO que comparar. La comparación posible es **en XXL**.

- A7. **Parámetros de usuario y dimensiones paramétricas** (Fermín, 2026-08-13) —
  ✅ **ETAPA 1 CERRADA el 2026-08-16** con seis fixtures manuales: la ventana «Parámetro»
  quedó mapeada entera a `.pgmx` y fijada offline en
  `tests/test_pgmx_parametric_variables.py`. Detalle en `experiments/parametros.md`.
  Queda abierta sólo la etapa 2 (si deja rastro en el ISO). Lo de abajo es el planteo
  original, que la evidencia corrigió: son **un solo mecanismo**, no dos temas.
  ⏸ el fixture lo arma él, incorporando las dos cosas al `manual_base`. Es el paso previo a las
  operaciones de máquina. Preguntas que abre: ¿un parámetro sin usar deja rastro? (R001 lo
  dejó abierto); ¿una dimensión definida por expresión llega al ISO **resuelta** o como
  expresión? ~~¿en qué etapa se resuelve — Maestro o el generador?~~ **RETIRADA (2026-08-14):
  no es relevante para el converter.** Si el ISO trae un número, el converter lo calcula
  desde el `.pgmx`; si trae una expresión, la copia. La etapa donde ocurra no cambia ni una
  línea de lo que hay que emitir — y era la única de las tres que necesitaba el XXL.
  > **La pista, leída (2026-08-14).** `aDXV`/`aDYVa`/`aDZVb`/`aFLDVc` no son cuatro nombres:
  > son dos opcodes pegados —`a` = cadena con byte de longitud, `V` = referencia a variable
  > con byte de índice—. Leído bien: **`DX`→slot 0x60, `DY`→0x61, `DZ`→0x62, `FLD`→0x63**, y
  > el DWORD en `0x78` de la cabecera vale **4**. Idéntico en los `.pgm` de las dos PCs.
  >
  > Y **no las pone Maestro**: el `.xxl` (16 líneas) no declara ninguna variable, así que las
  > **inyecta el compilador XXL/PGM** — etapa 2. El manual ya lo tenía escrito
  > (`09_13_reglas_estacionamiento.md`, Apéndice B): son las **variables predefinidas de sólo
  > lectura** del lenguaje (`DX DY DZ BX BY BZ FLD` + pi). Curiosidad: materializa cuatro de
  > las siete — `BX/BY/BZ` no aparecen.
  >
  > **Predicción falsable para cuando lleguen los fixtures**: el vocabulario de Xilog son tres
  > cosas distintas (`PAR` = parámetro, `L` = variable con expresión, `D` = alias), los `PAR`
  > van **detrás** del encabezamiento y `DX/DY/DZ` son de **sólo lectura** ⇒ el `H DX=` del
  > XXL **no puede** llevar una expresión, y la dimensión tendría que llegar **resuelta en la
  > etapa 1**. El discriminador es una sola línea: qué dice `H DX=` en el `.xxl`.
  >
  > ⚠️ **Incongruencia a resolver antes de modelar** (regla 1): «parámetro» significa tres
  > cosas — el panel **«Parámetros»** de Maestro, el tag `parametric_variables` / namespace
  > `Parametrics` del `.pgmx`, y las instrucciones `PAR`/`L`/`D` de Xilog. Cuál emite Maestro
  > cambia qué tiene que preservar el converter.
  >
  > Qué hace falta: los `.pgmx` y sus `.iso`, nada más. Al 08-14 no están en S: ni en P:.
  >
  > ⚠️ **Corrección (2026-08-14)**: acá decía que hacían falta también los `.xxl`. Contradecía
  > la decisión de Fermín del 08-13 —«la trazabilidad de los ISO y los archivos XXL quedan
  > fuera del método»— y era innecesario: las dos preguntas que sí importan se contestan
  > mirando el `.pgmx` y el `.iso`. La tercera, la que necesitaba el XXL, quedó retirada.

### G. Dibujos (geometrías) — 🔄 ARRANCÓ (2026-08-16, doc `dibujos.md`)
Rama nueva, abierta por los fixtures de línea. Un dibujo es **geometría sin `Feature`**: no
crea mecanizado y **no deja rastro en el ISO** hasta que un mecanizado la toma.
- G1. **Línea** — ✅ derivada: nodo `GeomTrimmedCurve`, `_serializationGeometryDescription`
  decodificado (tipo · intervalo · curva base · punto · dirección, en `.17g`), los dos
  caminos de cálculo de la dirección, y la geometría **paramétrica** vía
  `Parametrics.Expression`. 11 fixtures.
- G2. Las otras **siete geometrías** de la pestaña Dibujar (arco, círculo, elipse,
  polilínea, rectángulo, punto, texto) — ⬜
- G3. Los otros **métodos** de la barra contextual, el checkbox «Coordenadas absolutas» en
  `true`, y qué otras propiedades admiten expresión — ⬜

### B. Anatomía del ISO — 🔄 ARRANCÓ (2026-08-10, doc `anatomia_iso.md`)
- B1. Partes del archivo del programa vacío: atribuir CADA línea a **uno de TRES** orígenes —
  configuración de programa (`.pgmx`), configuración de máquina (snapshot del CNC) o
  **configuración global de la aplicación (ventana Opciones)**. El tercero apareció el
  2026-08-09 y no estaba previsto — 🔄 **esqueleto de 43 líneas ya mapeado** (gemelo manual);
  **13 de ellas quedaron atribuidas a `NCI.CFG` el 2026-08-12** (B1f: el preámbulo y el reset
  se copian literales del archivo de máquina). Quedan ~8 líneas en DESCONOCIDO, todas del
  bloque de origen y del teardown
- B2. Con cada operación nueva: qué líneas agrega, origen de cada parámetro y valor — 🔮
- B3. Ruido del emisor (milésimas, case, f32): re-derivar con evidencia R propia — 🔮

### C. Operaciones de máquina — ⏭️ **SIGUE DESPUÉS DE A7** (Xn · Xmsg · Park · Iso)
Orden fijado por Fermín el 2026-08-13: primero A7 (parámetros de usuario y dimensiones
paramétricas), después estas, y recién después los mecanizados. El lab de la época anterior
queda congelado; la instancia nueva se crea oportunamente.

Lo que ya se sabe sin haber empezado: el `Xn` mete **ocho líneas** entre el `G40` y el `SYN`
(B1b), en el mismo punto donde el estacionamiento automático mete las suyas (B1d). Ese punto
del archivo es donde van las operaciones de máquina. Y las cinco Funciones C.N. de la UI ya
están mapeadas: `Xn` = «Operación nula», `Xmsg` = «Impresión mensaje», `Park` =
«Aparcamiento», más **Palpación** y **Corte con cuchilla**, que no modelamos.


### D. Mecanizados — 🔮 (una operación por vez, cada parámetro variado de forma controlada)

> **RUTINA PERMANENTE (Fermín, 2026-08-10)**: el barrido de parámetros de máquina **no se
> hace una vez y se archiva**. Se repite sobre **cada mecanizado básico** a medida que se
> estudian, porque la sospecha es que esos parámetros no sólo mueven líneas del esqueleto
> sino que **cambian el comportamiento de los mecanizados**. Cada etapa de D incluye su
> pasada de A5.
- Perforado (vertical, lateral, patrones) — 🔮
- Fresados (línea, arco, círculo, polilínea, contorno) — 🔮
- Canal (sierra) — 🔮
- Vaciado — 🔮 (el lab pgmx congelado se recrea oportunamente)
- El ORDEN de estas ramas se define por hallazgos, no está prefijado.

### E. Configuración de máquina — 🔄
- ✅ **Ciclo de refresco del snapshot** (requisito 2026-08-04) — **hecho el 2026-08-12**:
  `iso/machine_config.py` con `verificar` y `refrescar`, y la selección de qué entra al
  snapshot escrita en una tabla, no en la memoria de quien copie. Verificado contra una copia
  completa de la PC del CNC: **93 de 93 archivos coinciden**.
- E1. ✅ **CERRADO 2026-08-12.** El `UI00.exe.Config` del CNC estaba desde el 08-10 y ahora
  se sumó `Maestro\Settings\` (3 archivos, incluida la plantilla de fábrica
  `default.settingsx`). El snapshot quedó en **93 archivos, todos verificados contra la
  copia real del CNC**.
- E2b. ⚠️ **Procedencia corregida** (2026-08-12): dos archivos del snapshot venían de la PC de
  **oficina técnica**, no del CNC — `Maestro.rel` (decía `…1010`; el CNC tiene `…1009`) y
  `LXLVIEW.INI` (que en el CNC no existe). No fue descuido: el snapshot se armaba desde los
  shares `S:\Xilog Plus` y `S:\Maestro`, y el primero **sí** refleja al CNC (81 de 82
  byte-idénticos) pero el segundo no. Ahora hay herramienta y el manifest declara la fuente
  real.
- E3. ✅ **Lo que pide el emisor y no tenemos** (2026-08-12): `PostISO.cfg`, `Script.cfg` y
  `Motorplid.cfg` **tampoco existen en el CNC** — no son fuente, cerrado. `PviBeR.msg` es un
  archivo de mensajes por idioma, no de emisión.
- E4. ✅ **El cuarto origen, hecho archivo** (decisión de Fermín, 2026-08-13): las líneas que
  pone el emisor **no se escriben dentro del converter**, viven en
  `data/machine_config/emisor_iso.cfg` —el esqueleto completo con `<marcadores>`, en el
  formato `$CLAVE … $` de los `.cfg` de Xilog— y las lee `iso/emisor.py`. Verificado
  byte a byte contra el ISO de referencia (`tests/test_iso_emisor.py`).
- E6. ✅ **El dialecto del control, identificado** (2026-08-14): el esqueleto es uno de los
  **cuatro** que sabe emitir `PostISO.dll`, y el nuestro es **`ISO-ESAGV(2)`** — la Pratix
  tiene **CNC ESA-GV**. La clave que lo elige (`[CNCNAME]` de `Nci.ini`) está vacía: se emite
  el default. Anotado en la procedencia de `emisor_iso.cfg`. Detalle en `emisor_iso.md`.
- E5. **¿Se registran también los binarios del emisor?** — ⏸ decisión pendiente. El archivo
  dice *qué* emite; su encabezado dice *quién* en prosa. Formalizarlo sería sumar el sha256
  de los cuatro DLL al manifest — ⬜
- E2. **Separar «default al crear» de «lectura al postprocesar»**, clave por clave: las dos
  PCs difieren en `RadiusMultiplier` (4 vs 2) y `SecurityDistance` (20 vs 30). Doc:
  `experiments/configuracion_aplicacion.md` — ⏸ necesita el experimento de las dos PCs

### F. Origen X-CAB — ⏳ DIFERIDO hasta terminar la reinvestigación (2026-08-10)
- Los `.pgmx` de X-CAB (vía XConverter) son un tercer origen VIVO y **son alcance del
  converter**. Se estudian DESPUÉS de cerrar la serie R: primero la anatomía derivada,
  después los archivos de otra autoría. Registro en `circuito_pgmx.md` — ⏳

### Cierre — 🔮
1. Repaso del plan (`plan_cierre_converter.md`, untracked) con las specs de la reinvestigación
2. Construcción del converter definitivo
3. Corrección de la app (re-habilitar exportación ISO)
4. App de conversión por lotes (proyectos con carpetas y múltiples piezas)

## Preguntas abiertas

- ~~¿Maestro postprocesa un programa sin operaciones, o lo rechaza?~~ **RESPONDIDA
  (2026-08-10): SÍ.** El esqueleto existe — 43 líneas, 666 bytes. El gris de `Post` en la
  captura de la cinta era por el archivo sin guardar.
- **¿El `UI00.exe.Config` de la PC que POSTPROCESA cambia el ISO?** Se sabe (2026-08-10) que
  los configs de las dos PCs **difieren en dos claves que tocan la traza**:
  `RadiusMultiplier` (CNC 4 · oficina 2) y `SecurityDistance` (CNC 20 · oficina 30). Falta
  el experimento que separa «default al crear» de «lectura al postprocesar»: un `.pgmx` con
  UNA operación de fresado con lead automático, postprocesado en las dos PCs.
- ¿El origen de la pieza aparece en el ISO vacío? ¿Dónde?
- ~~¿Una variable de usuario sin uso deja rastro en el ISO?~~ **RESPONDIDA (2026-08-17):
  NO.** Los cinco ISO de parámetros y los tres de líneas son idénticos al del programa
  vacío salvo la línea 1 (el nombre del archivo). Ni un parámetro sin usar ni una
  geometría sin mecanizado llegan al ISO ⇒ el converter puede ignorarlos.
- ¿Qué opciones de programa muestra la UI que el XML de la plantilla no expone (o al revés)?

## Bitácora del trayecto

### 2026-08-17 — El postproceso contesta que NO, y eso cierra A7
Fermín postprocesó en el CNC las dos tandas: cinco fixtures de parámetros y tres de líneas.

- ⭐⭐ **Los ocho ISO son idénticos al del programa vacío**, salvo la línea 1 con el nombre
  del archivo. 43 líneas, mismo contenido. **Ni un parámetro sin usar ni una geometría sin
  mecanizado dejan rastro en el ISO.**
- ✅ **Control cruzado independiente del diff**: la diferencia de **bytes** de cada ISO
  contra el del vacío es **exactamente** el largo de más del nombre. Ni un byte suelto.
- ⇒ **Consecuencia para el converter**: puede ignorar parámetros y geometrías sin uso.
- ⇒ **Consecuencia metodológica**: lo derivado sobre la ventana «Parámetro» no alimenta la
  emisión de ISO; alimenta al **sintetizador**, que es la fábrica de fixtures. El trabajo
  vale por eso, no por el ISO.
- ⚠️ **Sólo vale para el caso sin uso.** El parámetro que alimenta una cota y la geometría
  que un mecanizado toma son rama D, y no están derivados.
- **Tercera línea** (`linea_3`): la 2 con X e Y intercambiadas — (50,50)→(220,350),
  60,461°. Mismos cosenos directores dados vuelta; `d/|d|` la reproduce igual.

**Y a la tarde, la geometría paramétrica** (ocho fixtures más, `dibujos.md` §7):

- ⭐ **`Parametrics.Expression` es el mecanismo general de Maestro**, no algo de la pieza:
  `GeomTrimmedCurve#1927.EndY = 'dx1 - Distancia'` tiene la misma forma que
  `WorkPiece#1917.Length = 'dx1'`. Ata **(objeto, propiedad) → fórmula de texto**. Mapeo
  del panel: `Xi`→`StartX`, `Yi`→`StartY`, `Xf`→`EndX`, `Yf`→`EndY`.
- ⭐⭐ **La geometría se guarda RESUELTA y la fórmula vive aparte** ⇒ **el converter lee el
  número y NO necesita evaluar expresiones nunca.** Cierra la pregunta que A7 tenía
  retirada.
- ⚠️ **Maestro escribe con ruido de ~10⁻¹³**, y no es nuestro: lo confirma su propia UI (el
  tooltip de un campo que muestra `50,000` dice `Value: 49,9999999999997`). Entra **al
  escribir** —con el modelo limpio en `50` exacto, el archivo salió con
  `49.99999999999996`— y **también por el teclado**: tipear `50` dio tres valores distintos
  en tres intentos. ⇒ **El byte-idéntico en el `.pgmx` no es caro: es inalcanzable**, y
  Maestro no lo alcanza consigo mismo. La decisión del 08-16 queda blindada.
- ⇒ **Aviso para el converter**: nunca comparar coordenadas por igualdad ni asumir números
  redondos. Pendiente de verificar si los seis usos de tolerancia `1e-15` reciben valores
  leídos de un `.pgmx` (el ruido los desborda 300 veces) o sólo calculados por nosotros.
- 🔍 **DOS reglas propias refutadas por el fixture siguiente, en el mismo día**:
  1. «Maestro calcula la dirección con una sola redondeada y nuestro `dx/double(L)` está 1
     ULP corrido» → **falso**: tiene **dos caminos** —uno al dibujar, otro al editar o
     resolver fórmulas— y **el nuestro es el segundo**. Se retira el «defecto de 1 ULP» y
     la lista de siete lugares a corregir: no hay nada que corregir.
  2. «El ruido está compensado: el extremo restringido sale exacto» → **falso**: los
     triángulos 3-4-5 lo rompen con las cuatro fórmulas puestas. Los casos exactos fueron
     suerte del redondeo. En ese fixture **nuestro sintetizador es más exacto que Maestro**.
  📌 Con punto flotante, tres observaciones no hacen una regla: hay que ir a buscar el caso
  que *debería* romperla.
- ⚠️ Corregida además una **mala lectura mía**: se había escrito que `linea` y `linea_2` se
  hicieron igual. No: la primera se **dibujó** y la segunda salió de **editarla**, y Fermín
  lo había dicho desde el primer mensaje. Esa diferencia es justamente la de los dos
  caminos.

### 2026-08-16 — A7 se destraba, y el `.pgmx` deja de perseguir el byte
Los shares volvieron y Fermín hizo los fixtures en Maestro, mirando yo la ventana en vivo
(capturas de la UI disparadas contra la ventana de Maestro, `PrintWindow`).

- ⚖️ **DECISIÓN DE MÉTODO: el `.pgmx` del sintetizador va FUNCIONALMENTE idéntico, no
  byte-idéntico.** El byte a byte queda donde es el producto: el `.iso`. Reclasifica lo
  encontrado hoy en defecto real (el decimal) y cosmético (el ULP de la dirección).
- ⏭️ **Modo de trabajo**: juntar toda la evidencia y hacer las modificaciones después.
- ✅ **La ventana «Parámetro» quedó mapeada entera**: `Decimal`→`Double`/`b:double`,
  `Entero`→`Integer`/`b:int`, `Booleano`→`Boolean`/`b:boolean` (valor en **minúscula**);
  `Longitud`→`Lenght` (**con el typo de SCM**), `Velocidad`→`Speed`,
  `Adimensional`→`UnitLess`. Punto decimal, signo, y **sin redondear**.
- ⭐ **A7 era un solo tema, no dos.** Las dimensiones de la pieza YA son parámetros
  (`dx1`/`dy1`/`dz1`, misma tabla, misma estructura); lo que las ata a la pieza es un
  `Parametrics.Expression` que apunta a `WorkPiece.Length` con la expresión `dx1`.
- 🐛 **Un defecto real del sintetizador, encontrado por un fixture**: `_compact_number`
  redondea a 6 decimales y Maestro **no redondea** (`12,3456789` quedó `12.3456789`).
  Corregido **sólo** en el `Value` del parámetro (`_parameter_value_text`), que es donde
  hay evidencia; los otros **153 usos** quedan como deuda anotada. Nadie había derivado
  nunca ese truncado: era un predefinido de la época anterior, igual que `Integer` y
  `Speed` — que sí resultaron correctos.
- ⚠️ **El corpus no podía delatarlo**: de los 55 `.pgmx` de autoría de Maestro que
  tenemos, el **único** número con 7+ decimales es el que se tipeó para el fixture.
  Punto ciego de la regla 5, otra vez.
- ✅ **Los `ID`**: arrancan en el primer libre **del archivo** al abrirlo y avanzan dentro
  de la sesión; un `ID` liberado **se reutiliza** al reabrir. Nuestro `_reserve_ids`
  coincide partiendo de un archivo recién abierto.
- ✅ **Nomenclatura**: Maestro usa **las dos** palabras — panel y diálogo dicen
  «Parámetro», el tooltip del botón dice «Crear una nueva variable». No hay bando que
  elegir, hay sinónimo que documentar. «Variable de usuario» sí es nombre nuestro.
- ⭐ **Arrancó la rama de dibujos** (`experiments/dibujos.md`): una línea es un
  `GeomTrimmedCurve` en `<Geometries>` y **no crea `Feature`**. Decodificado el
  `_serializationGeometryDescription` (tipo · intervalo · curva base · punto · dirección
  unitaria, todo en `.17g`), y derivada la regla de la dirección: `d/|d|` con **una sola
  redondeada**. El sintetizador reproduce la línea byte a byte salvo 1 ULP cuando el
  ángulo es notable.
- 🔍 **Dos hipótesis mías refutadas por evidencia, en el día**: que Maestro sacaba la
  dirección de `cos`/`sin` del ángulo (era un artefacto de mirar sólo el caso de 45°), y
  que el default de Unidad física era `Adimensional` (es **`Longitud`**; el
  `Adimensional` se había visto con el Tipo ya en Booleano).
- 🧰 **Herramienta**: la suite pasó a correrse con **pytest**, declarado en
  `requirements-dev.txt` + `pytest.ini`. El comando que documentaba `docs/` —
  `unittest discover`— **daba falso verde**: no recolecta los 11 tests escritos como
  funciones sueltas de `test_pgmx_reader.py`. Suite: **319 passed, 306 subtests**.

### 2026-08-14 — El control tiene nombre, y con eso `EDK`/`ETK` tienen diccionario
Día sin fixtures nuevos: A7 quedó bloqueado y el trabajo se fue a cerrar significados.

- ⭐⭐ **La Pratix es CNC ESA-GV, y el esqueleto es el dialecto `ISO-ESAGV(2)`.** `PostISO.dll`
  declara **cuatro** dialectos y `Nci.ini` tiene la clave que los elige (`[CNCNAME]`) **vacía**.
  Lo resuelve la *Guía de Diagnóstico* de SCM `9031191610B` v4.2: en los CNC ESA-GV las
  variables `E..` «se transformarán en `ETK..`», agrupa `RD110s-TV-Pratix`, y documenta
  `ETK103` como parámetro de RD110 con CNC ESA-GV. Nuestro ISO usa `ETK`/`EDK`.
- ✅ **`EDK` = bit de intercambio del CNC al PLC**, bandas `0-5` / `10-13` / `20-21`. La banda
  10-13 es **exactamente** el juego de mitades de mesa que R002 había derivado sin el manual —
  la evidencia propia y la documentación se confirman entre sí. Y el `.0` es el **bit**.
- ✅ **`ETK` tiene bandas por función**, y `?%ETK[8]` cae en la del **cambio de herramienta**
  (`ETK 6-12`). Eso explica que alterne 1 y 2 en los ISO con mecanizado. ⚠️ **Estaba congelado
  en 1 en `emisor_iso.cfg`**: primer defecto real encontrado en el archivo del cuarto origen.
- ✅ **`VL6`/`VL7` son la longitud y el radio de la herramienta.** Copian a `SVL`/`SVR`, que se
  cargan con `D1` y se anulan con `D0`. Cruzados contra `tool_catalog.csv` sobre ~2.000 ISO
  del taller: **ocho herramientas, coincidencias al centésimo en los dos campos**. Cuando la
  rama D emita mecanizados, esas dos líneas salen del catálogo (regla 4). Excepción anotada:
  la Sierra Vertical X recibe `SVR 1.900` y no el radio de su disco.
- `MLV` pasa a **hipótesis fundada** (nivel de transformación: el 0 lleva el `%Or`, el 1 el
  `SHF`, y el teardown limpia la pila). `SYN` queda como hipótesis **con mecanismo**.
- ✅ **`M58` = «LLAMADA VACÍO GENERAL»**, confirmado por el fabricante — coincide con el
  comentario italiano del `NCI.CFG`.
- ✅ **El XConverter no tiene NADA del esqueleto**: 28 binarios barridos (incluidos los de
  `C:\SPAI` y `Xconverter.exe.new`, que el barrido de B1g no alcanzaba), 20 patrones, cero
  coincidencias, con control positivo de 9/20 en `PlPathFilter32.dll`. El cuarto origen se
  sostiene. Y `Xconverter.exe.new` resultó ser un **lanzador hecho en el taller**, no una
  versión nueva: cierra la pregunta 4 de `circuito_pgmx.md`.
- **Método**: dos respuestas de IA externas se contrastaron contra la evidencia. La primera
  daba expansiones inventadas para las cinco siglas y quedó refutada en tres. La segunda
  acertó `EDK`/`ETK`/`MLV`/`SYN` y erró `SVL`/`SVR` (los llamó sobrematerial), lo que se
  detectó **porque el catálogo dice otra cosa**. Los números del taller mandan sobre cualquier
  prosa; los ejemplos que una IA «cita» hay que verificar que existan.
- ⚠️ El manual de SCM lleva prohibición de divulgación: **no se copia al repo**, se cita por
  código y capítulo.
- ⛔ **DECISIÓN DE ALCANCE (Fermín, 2026-08-14): el XXL y el PGM se cierran como línea de
  trabajo.** El converter va de `.pgmx` a `.iso` **directamente**; no usa Winxiso ni el
  XConverter, y no emite ninguno de esos dos formatos. Lo que sigue en pie es **qué emite**
  el emisor (rama B) — eso es lo que hay que reproducir byte a byte. Lo que se cierra es el
  estudio de los formatos intermedios, de cómo se invoca Winxiso, y del XConverter salvo por
  el único costado que importa: **produce `.pgmx` de entrada** (rama F, diferida).
  - Se retira la regla «si estaba en el XXL, nace en la etapa 1»: razona a través de un
    intermedio que no emitimos y **evita el fixture**, que es el método.
  - Auditado hallazgo por hallazgo: **ninguno de los que sostienen el converter salió del
    XXL/PGM**. La fórmula del origen es de R002, el dialecto y las plantillas de los binarios
    del emisor, `VL6`/`VL7` del catálogo, `EDK`/`ETK` del manual de SCM. El XXL aportó
    relato, no evidencia.
  - Corregida de paso una contradicción propia: A7 pedía «los `.pgmx` **y sus `.xxl`**», en
    contra de la decisión del 08-13. Arranca con `.pgmx` + `.iso`.
- 🔍 **La cadena de dos etapas, re-verificada a pedido de Fermín.** Objetó —con razón— que
  `.iso`/`.xxl`/`.pgm` son los tres valores de `PostFileFormat`, o sea formatos de salida
  elegibles, y que el tramo `PGM → ISO` estaba **inferido** de que los archivos aparecieran
  juntos. Al ir a verificarlo apareció evidencia dura: `Winxiso.exe` trae su propia ayuda de
  línea de comando con una modalidad por tramo —**`-c [PGM -> ISO]`**, `-o [XXL -> PGM]`—.
  La cadena queda DERIVADA y las dos lecturas se unifican: **es una sola cadena y el selector
  decide dónde se detiene**. Queda el fixture que lo confirma (`PostFileFormat` = XXL / PGM),
  barato y sin necesidad de mecanizado.

### 2026-08-13 (tarde) — El cuarto origen deja de ser una pregunta y pasa a ser un archivo
Tres definiciones de Fermín, y la construcción de la segunda.

- ❌ **Descartada la trazabilidad de los ISO y los archivos XXL.** El XXL sirvió para
  entender la cadena y ahí termina su rol; no se guarda por fixture.
- ✅ **El cuarto origen es un archivo nuestro**: `data/machine_config/emisor_iso.cfg`, con el
  **esqueleto completo** del ISO y `<marcadores>` donde entran el header, el origen, los
  bloques de `NCI.CFG` y el cuerpo. Formato `$CLAVE … $`, el de los `.cfg` de Xilog, con
  prefijo `$EMI_` para no confundirse nunca con las claves de SCM.
  - **La regla del `;` prestada del `NCI.CFG` resuelve el problema de los espacios finales**:
    `G71 ;` → `"G71 "`. Escritos al desnudo, el primer editor que recorte espacios rompería
    el byte-idéntico en silencio; así quedan visibles y a prueba de editor.
  - `tests/test_iso_emisor.py` rearma el ISO del programa vacío desde el archivo y lo compara
    **byte a byte** con el de referencia. Y comprueba que un valor faltante **explota** en vez
    de completarse solo: la regla 4 en código. Suite **302**.
- ⏭️ **Orden fijado**: A7 (parámetros de usuario y dimensiones paramétricas) → C (operaciones
  de máquina) → D (mecanizados).

### 2026-08-13 — Las dos PCs producen el MISMO intermedio
El CNC postprocesó el mismo programa base guardando los cuatro archivos de la cadena.

- ⭐ **La etapa 1 es idéntica entre las dos máquinas.** Los `.xxl` (522 bytes cada uno)
  difieren en **dos líneas** —la versión de Maestro (`1009` en el CNC, `1010` en oficina) y
  la fecha— y los `.pgm` (1.655 bytes) en **catorce bytes**, todos dentro de esas mismas dos
  cadenas. ⇒ **Toda la diferencia entre las dos PCs vive en la etapa 2**, la que oficina
  técnica no puede completar. Para el programa vacío, el experimento de las dos PCs queda
  respondido: **la máquina donde se prepara el programa no cambia nada.**
- ✅ **El postproceso es repetible**: el ISO del CNC de hoy es idéntico al del 08-10 salvo la
  línea 1, con los 17 fixtures del barrido de opciones en el medio.
- **La versión de Maestro se pierde en el paso a ISO**: el XXL la escribe, el ISO no la lleva
  en ninguna línea. Se propuso guardar el `.xxl` junto a cada ISO para conservar esa firma y
  **Fermín lo descartó (2026-08-13)**: la trazabilidad de los ISO y los XXL quedan fuera del
  método.
- **De las 43 líneas del ISO, sólo dos tienen antecedente en el XXL** (el header y el
  origen). Las otras 41 nacen en la segunda etapa. Para un programa vacío, el ISO es casi por
  completo producto de la configuración de máquina y del emisor.
- Evidencia en `evidencia/paso0_cnc/`, junto a `paso0_oficina_tecnica/`.

### 2026-08-12 (cierre) — El paso 0 no dio ISO, y por eso mostró la etapa intermedia
Fermín postprocesó el programa base en la PC de **oficina técnica**. No salió ningún `.iso`:
salieron un `.xxl`, un `.pgm` y un `.inf`. El «fallo» resultó ser el hallazgo estructural
más grande de la etapa.

- ⭐⭐ **El postproceso tiene DOS etapas**: `.pgmx` → **XXL** → PGM → **ISO**. Maestro produce
  el XXL (16 líneas, texto legible); el **generador de Xilog** lo traduce a ISO (43 líneas).
- **El origen se resuelve en la SEGUNDA etapa**: Maestro escribe `O X=0 Y=0 Z=0` —el origen
  del programa tal cual— y los `−400.000` / `−1515.600` de `fields.cfg` los pone el
  generador. Toda la fórmula de B1c pertenece a esa etapa, no a Maestro.
- ✅ **Confirmada la hipótesis de `R`**: el XXL escribe `R=1` y el ISO no lo lleva. La
  omisión de las repeticiones ocurre en el paso a ISO. Ídem `/"def"`, el equipamiento. Y el
  **orden de los campos del header cambia** entre los dos formatos.
- ⇒ **Explica el resultado que más se repitió en el barrido**: las opciones de la ventana
  Opciones actúan en la etapa 1, y sólo llegan al ISO las que Maestro alcanza a escribir en
  el XXL. Por eso 16 de 17 no llegaron.
- ⇒ ~~**El XXL es un intermedio observable**: cuando una línea del ISO no se entienda, se
  puede preguntar si ya estaba en el XXL, y eso dice en qué etapa nace.~~ **RETIRADA COMO
  MÉTODO el 2026-08-14** (decisión de Fermín): razona a través de un intermedio que no
  emitimos, y evita el fixture. Ver `experiments/emisor_iso.md`.
- **Consecuencia práctica**: el barrido **no se puede mudar a oficina técnica** —esa
  instalación no genera ISO, y no es de hoy: hay temporales de marzo de 2025 con el mismo
  patrón—. Sigue haciéndose en el CNC. Y el experimento de las dos PCs para las claves de
  traza hay que replantearlo: si una no emite ISO, habría que comparar en XXL.
- Evidencia versionada en `evidencia/paso0_oficina_tecnica/`. Doc: `emisor_iso.md`.

### 2026-08-12 (noche) — La copia completa del CNC: el emisor es un origen
Fermín copió a `S:\Copia CNC` las carpetas enteras de `C:\Archivos de programa\SCM Group`
de la PC del CNC. Cuatro cosas salieron de ahí.

- ⭐ **Los seis binarios del generador ISO DIFIEREN entre las dos PCs.** El CNC tiene la
  build del **2011-11-18**; oficina técnica, la del **2011-10-14**. `nci32.dll` además pesa
  4 KB más y su tabla de cadenas cambió: **las plantillas del header en formato PGM están
  sólo en la versión de oficina técnica**. ⇒ La pregunta de «tres o cuatro orígenes» queda
  respondida en los hechos: **hay dos emisores conviviendo**, y la evidencia de un ISO vale
  contra la build que lo produjo. Doc nuevo: `experiments/emisor_iso.md`. Sube el valor del
  paso 0, que ahora tiene un motivo concreto para poder dar distinto.
- ⚠️ **El snapshot tenía procedencia mezclada**, y lo delató el archivo que declara la
  versión: `Maestro.rel` decía `1.00.006.1010` (oficina técnica) cuando el CNC tiene
  `1.00.006.1009`. También `LXLVIEW.INI`, que en el CNC no existe. Causa: el snapshot se
  armaba desde los shares, y `S:\Xilog Plus` **sí** refleja al CNC (81 de 82 byte-idénticos)
  pero `S:\Maestro` no. Corregido, y ahora hay herramienta: **`iso/machine_config.py`** con
  `verificar` y `refrescar`, y la selección escrita en una tabla. **93 de 93 verificados.**
- ✅ **E1 cerrado**: `Maestro\Settings\` incorporado (3 archivos, con la plantilla de fábrica
  `default.settingsx`).
- ✅ **El barrido de opciones no dejó rastro en producción** — la verificación que el propio
  método pedía. De 172 claves del `UI00.exe.Config` cambiaron 11, y diez son el historial de
  archivos recientes; la única real es `IsCamViewEnabled`, que no toca el ISO. **Las 17
  opciones del barrido volvieron todas a su valor.**
- ✅ `PostISO.cfg`, `Script.cfg` y `Motorplid.cfg` **tampoco existen en el CNC**: no son
  fuente. E3 cerrado.

### 2026-08-12 (tarde) — Las dos de prioridad 1 no llegan, y el resto del esqueleto tiene emisor
- **`IsAreaScm` e `IsZetaScm` no cambian el ISO del vacío** (fixtures `ctr_scm`, `npt_scm`;
  las dos claves valían `False` en el CNC, así que el cambio fue real). El de `IsAreaScm` es
  el resultado fuerte: el origen está en el vacío y **no se movió** ⇒ la fórmula de B1c no
  depende del tope de referencia. El de `IsZetaScm` es débil: gobierna la **profundidad de
  trabajo**, y sin operaciones no hay ninguna — `SHF[Z]` es el origen, no una profundidad.
  Tampoco llegan `IsBottomPlaneMachining` ni `IsCheckCollisionEnabled`.
- **Barrido de los 7.683 archivos de las dos instalaciones** (ASCII + UTF-16) buscando las
  plantillas `printf` de las líneas sin origen. Resultado en `anatomia_iso.md` B1g:
  - el **teardown (30–42) es del módulo de MESA** (`PlPathFilter32.dll`, entre travesaños y
    ventosas) y se emite entero — por eso aparece el `MLV=2` de un nivel que nunca se usó;
  - el bloque de puesta a punto y el `SYN` los escribe **`PostISO.dll`**, con **dos
    plantillas distintas de `EDK`**: una de índice fijo (líneas 14–15) y otra de índice
    variable (líneas 30 y 42) — que hasta hoy se leían como la misma cosa;
  - **`%Or[0].of*` no existe como literal en ningún archivo**: se compone en runtime;
  - **no existe `G70`** en ningún emisor, sólo `G71` ⇒ se debilita la hipótesis `IsMM`.
- ⚠️ **Queda planteada una pregunta de fondo: ¿los orígenes son tres o cuatro?** Estas
  líneas no salen del programa, ni de la máquina, ni de la aplicación: las escribe el
  **binario del emisor**. Decisión pendiente de Fermín; cambia cómo se escribe el converter.
- **¿Los DLL leen alguna fuente que no miramos?** (pregunta de Fermín). No hay fuente
  escondida, pero sí **30 claves `$…` que el emisor consulta y que ningún archivo define**:
  `$MA_*` (mesa), `$PM_*` (macros de archivo/bloque/ciclo) y `$KEY_G%d`/`$KEY_M%d` (**la
  traducción de cada código G y M**). Son puntos de extensión vacíos ⇒ **el esqueleto es
  fijo porque nuestra config no los define**, no porque el emisor no pueda emitir otra cosa.
  El emisor hasta tiene su propio fail-loud: `;G%d: CORRISPONDENZA NON TROVATA!`.
- Tres archivos que los DLL nombran **no existen en esta PC** (`PostISO.cfg`, `Script.cfg`,
  `Motorplid.cfg`): hay que ver si están en el CNC. Y `Nci.ini` —config del generador, que ya
  estaba en el snapshot y nunca miramos— es **byte-idéntico entre las dos PCs**, igual que
  `NCI.CFG`: lo que difiere entre máquinas es la **aplicación**, no el **generador**.

### 2026-08-12 — Trece líneas del esqueleto estaban escritas en un archivo que ya teníamos
- **El preámbulo (3–8) y el reset de registros (23–29) salen LITERALES de `NCI.CFG`**, un
  archivo del snapshot de la máquina, en sus bloques `$GEN_INIT` y `$GEN_END`. Verificado con
  `iso/machining_lab/verificar_nci.py` y fijado offline en `tests/test_iso_nci_skeleton.py`.
- **La regla de emisión es una sola, de dos pasos**: cortar la línea en el primer `;` y
  desdoblar `%%`→`%`. Con eso quedan explicadas **las dos líneas vacías** del preámbulo (son
  comentarios enteros: una línea comentada no desaparece, deja su lugar) y **el espacio final
  de `M58 `**, que es el que separaba el comentario en el `.CFG`.
- **`NCI_ORI.CFG` (la versión de fábrica) trae otro preámbulo** (`M150`) y un `$GEN_END` con
  una línea más ⇒ **el preámbulo es configuración de la instalación, no protocolo**. Es B1d
  por un segundo camino: el esqueleto lo pueden reescribir DOS de los tres orígenes.
- `$GEN_END` **no** cierra el archivo: quedan 14 líneas después. El emisor lo inserta en el
  medio de su propio cierre.
- Del manual de Xilog (Apéndice B, regla 2: estaba escrito): **`BX/BY/BZ` es la traslación de
  la pieza respecto al TOPE** —sale de DESCONOCIDO—, `HEADER(n)` cierra el juego de letras
  del header, y `FIELD(a,n)` confirma posición por posición la lectura de `fields.cfg`
  (y agrega un **origen Z por campo** que todavía no miramos).
- `M58` queda con significado: **habilita el bloqueo de la pieza** (`abilita controllo vuoto`).

### 2026-08-10 (noche) — Los dos barridos de configuración
- **Parámetros de máquina, 29 fixtures manuales.** 16 llegan al ISO (14 mueven `V`, 2
  mueven `T`), 12 no llegan y 1 rompe el postproceso (`Combiflex`, con un error de Winxiso
  que habla del **área**). **Todas las diferencias caen en la línea del header.** Dos
  patrones: el número del `.pgmx` y el del ISO **no son el mismo** (traducción en el
  medio), y **el modo se pierde** — manual/automático/semiautomático de cada familia dan
  el mismo `V`.
- **Ventana Opciones, 13 fixtures.** Una sola opción cambia el ISO de un programa vacío:
  el **estacionamiento automático al terminar**, que agrega dos líneas entre el `G40` y el
  `SYN` — el mismo lugar donde el `Xn` mete su bloque. Confirma la hipótesis del 09 que
  estaba en suspenso. Y otra vez **el modo de paro no llega**: los tres dan ISOs
  idénticos.
- ⇒ **El esqueleto de 43 líneas no es «el esqueleto»**: es el esqueleto con esta
  configuración de aplicación. El converter no puede tratarlo como plantilla fija.
- **Las fases vacías no dejan rastro**: 2 y 3 fases emiten lo mismo que 1.
- **Relevamiento de los manuales de SCM** (191 hallazgos, sin interpretar): el preámbulo y
  el cierre del ISO están **escritos literalmente** en `NCI.CFG`, un archivo que ya está en
  nuestro snapshot (`$GEN_INIT` y `$GEN_END`).
- **Bug nuestro encontrado por el lote**: el sintetizador escribía el `Name` de una
  variable en el namespace equivocado y Maestro no podía abrir el archivo. Arreglado, con
  test que compara el namespace resuelto. El test viejo usaba un comodín y por eso daba
  verde con el XML roto.

### 2026-08-10 (tarde) — R001 y R002 postprocesados: el origen queda derivado
- **Un bug NUESTRO, encontrado por el lote**: Maestro no pudo abrir
  `R_PV_variable_usuario.pgmx` («El valor no puede ser nulo. Nombre del parámetro: key»).
  El sintetizador escribía el `Name` de una variable en el namespace de `Parametrics`;
  va en `Utility`. Nadie lo detectó antes porque **el test usaba una regex con prefijo
  comodín y el adapter lee con wildcard de namespace**: nuestro lector es tolerante donde
  Maestro es estricto. Arreglado, con test que compara el namespace resuelto. Suite 283.
- **R001 mató dos hipótesis**: el header `;H DX/DY/DZ` no son las dimensiones de la pieza
  sino **dimensión + origen** (la envolvente ocupada), y `BX/BY/BZ` **no** es el origen.
- **R002 (11 fixtures de áreas) cerró la fórmula del origen, verificada 11/11**:
  `SHF[eje] = campo(1ª letra del área, eje) − D_eje` **sólo si `campo(eje) == 0`**. La
  coordenada del campo es el tope: si está en 0, la pieza cuelga hacia el negativo; si ya
  es negativa, la esquina es el tope y la medida no entra. Lo que parecían dos reglas
  (X restaba, Y no) era una sola con el cero como condición.
- Además: **manda la primera letra del área** (`CD` ≠ `DC`), un área de una letra se
  normaliza (`A` → `-AB`), y el índice de `?%EDK[n]` marca la **mitad de mesa** (10
  izquierda, 13 derecha), no la fila.
- `fields.cfg` parseado bien (bloques cerrados por una separadora con la letra): dos filas
  de cuatro campos de 1843×1555. **Sus coordenadas son de calibración y difieren entre sí
  por milímetros** — redondearlas rompe el byte-idéntico.

### 2026-08-10 — El primer ISO de la reinvestigación, y el sintetizador validado
- **A2 cerrado casi entero.** Siete capturas nuevas: el panel **Pieza** (donde nace un
  programa) y la ventana **Parámetros de máquina**, que resultó ser la que faltaba. Entre
  las dos cerraron nueve filas del inventario. Quedan tres sin ubicar
  (`WorkpieceOffsetX/Y/Z`, `ContinuousCycle`, `IsRelatedToOppositeSideStop`).
- Nomenclatura de la UI: el campo de ejecución se llama **«Área»**; las dimensiones,
  **DX/DY/DZ**; y las cinco Funciones C.N. confirman **Xn = «Operación nula»**, **Xmsg =
  «Impresión mensaje»**, **Park = «Aparcamiento»** — desde la UI, sin la época congelada.
  Aparecen dos cosas que no modelamos: **`Palpación`** y **`Corte con cuchilla`**.
- **Gemelo manual + experimento de dos PCs** (Fermín): el `.pgmx` creado en oficina técnica
  y re-guardado en el CNC queda **byte-idéntico** (mismo CRC), y sus ISO difieren sólo en el
  nombre del archivo. Re-guardar no imprime nada de la instalación. **Falta** el experimento
  que sí importa: postprocesar el mismo `.pgmx` en las dos PCs.
- **Maestro postprocesa un programa vacío** ⇒ el esqueleto existe y **B1 arrancó**:
  43 líneas mapeadas en `anatomia_iso.md`, con DERIVADO / HIPÓTESIS / DESCONOCIDO explícito.
  El origen sale de `fields.cfg` (área H, −1515.60) y la **precisión simple** del emisor
  quedó derivada con evidencia propia (`ofY = −1515599.976`).
- **Control de circularidad OK (regla 5)**: el `.pgmx` manual y el sintetizado tienen los
  mismos tags, en las mismas cantidades, con los mismos valores; sólo difiere el estilo de
  serialización. El sintetizador queda validado como fábrica de fixtures de la etapa 1.
- Hallazgo lateral: **`def.tlgx` viaja dentro del `.pgmx`** (73.449 bytes, mismo CRC en los
  dos archivos). El catálogo de herramientas no hay que ir a buscarlo a la PC.
- Corregido un dato del 09: el snapshot **no** tiene 3 archivos sino **91**; los tres eran
  los que leía el converter viejo. E1 se achica a sumar `UI00.exe.Config` y `Settings\`.
- **El config del CNC, por fin.** Fermín extrajo el `UI00.exe.Config` de la PC que
  postprocesa; ya está en el snapshot (`maestro_ui/`, con manifest). Comparado contra el de
  oficina técnica: **25 claves con valor distinto, y dos tocan la traza** —
  `RadiusMultiplier` (4 vs 2) y `SecurityDistance` (20 vs 30). Las otras doce sensibles
  coinciden. Doc: `experiments/configuracion_aplicacion.md`. De paso quedó cerrada la duda
  del 09: aquella ventana Opciones era la de **oficina técnica** con las rutas todavía en
  default de fábrica, no la del CNC.

### 2026-08-06 — El rumbo nuevo
- Tras ejecutar parte del plan de cierre de la época anterior, Fermín lo revisa y decide
  VOLVER ATRÁS ("no me gustó como quedó"): re-especificar antes de reconstruir. La ejecución
  completa queda preservada en `respaldo/ejecucion-plan-f0-f3`.
- Directiva de la reinvestigación metódica: empezar desde un `.pgmx` VACÍO, repasar toda la
  configuración (con capturas de la UI si hace falta), programas crecientes variando cada
  parámetro de forma controlada, anatomía del ISO en paralelo, y regla de nomenclatura
  genérica (términos de Maestro; nunca proyectos de producción ni fixtures).

### 2026-08-07 — Limpieza del repositorio y preparación
- Serie N archivada por Fermín en `Investigacion iso_converter\` de AMBAS raíces (S: y P:);
  repo reapuntado (80 archivos) y `iso_converter` congelada verde (683 passed, tip 260f340).
- Rama **`reinvestigacion`** creada desde `main`. Congelados fuera del árbol: converter
  viejo (`iso/synthesis`), sus 20 tests, labs N001–N042, estudios ISO, docs de la época,
  `iso_state_synthesis` completo (la app queda con exportación ISO deshabilitada CON AVISO
  por pieza), `test_pgmx_pocket`, y los labs pgmx (`aparcamiento`, `machine_operations`,
  `pocket_milling`).
- Auditoría de la suite pedida por Fermín: 28 de los 33 subtests leían fixtures viejos
  (`Vaciado_NNN` de `Investigación previa`) tras un `skipUnless` silencioso → retirados.
  Resultado: **282 passed, 5 subtests, 100% offline**.
- Lote **R001** generado (7 `.pgmx` de variación controlada + INSTRUCCIONES con gemelo
  manual) y doc del experimento `programa_vacio.md` con el inventario completo de la
  configuración de programa del `.pgmx`.
- CLAUDE.md regla 2 actualizada a la época nueva (aprobado por Fermín).
- Esta hoja de ruta creada.

### 2026-08-09 — Arrancan las capturas de la UI (A2) y aparece un tercer origen
- Definido dónde viven las capturas: **repo Nora**, partidas por la regla del propio repo
  («datos por máquina = memoria; oficio = skills»). La VENTANA va a
  `skills/cnc-scm-maestro/references/pantallas/`; los VALORES de la Pratix, a
  `memory/machines/pratix-s15/pantallas/`. Se llaman **pantallas**, no fotos ni capturas
  («captura» ya significa snapshot de config en `iso/data/`). Hasta hoy no se había guardado
  ni una imagen: las 7 de Vaciado del 29-jul se perdieron, sobrevive sólo su prosa.
- 20 capturas: el Editor en frío + la ventana **Opciones** completa, nodo por nodo.
  Transcripción en `cnc-scm-maestro/references/opciones-de-maestro.md`.
- **Hallazgo que cambia B1**: la dicotomía programa/máquina no alcanza. La ventana Opciones
  es un TERCER origen — global de la aplicación, fuera del `.pgmx` — y de ahí salen el
  formato de salida (ISO vs PGM), el tope de referencia, la notación de Z negativa, el
  «Paso de retroacción en los fresados» (10) y el estacionamiento automático al terminar.
  Detalle y consecuencias en `experiments/programa_vacio.md`.
- Respondida una fila del inventario: `IsMM` = Opciones → Idioma → «Unidad de medida».
- Abierto: si la instalación capturada es la que postprocesa de verdad (sus rutas son las de
  fábrica, no `S:`), o si es una copia de escritorio.
