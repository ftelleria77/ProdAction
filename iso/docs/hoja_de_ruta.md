# Hoja de ruta de la reinvestigación PGMX → ISO

**Documento VIVO.** Registra el trayecto recorrido (bitácora, abajo) y establece el camino
por delante en la medida en que los hallazgos lo van definiendo. Se actualiza en cada hito:
lo recorrido se AGREGA a la bitácora (nunca se reescribe), el mapa se REVISA (los cambios de
rumbo se anotan como decisiones con fecha). La vista visual se republica en cada hito
(artifact "Reinvestigación PGMX→ISO", URL estable).

Estados: ✅ hecho · 🔄 en curso · ⏸ esperando a Fermín · ⬜ pendiente · 🔮 futuro (sin fecha)

## Estado actual (2026-08-25)

> ⭐⭐ **La reinvestigación terminó de rodear la traza y está por entrar en ella.** En una
> semana se cerraron las dos ramas que faltaban antes de los mecanizados:
>
> - **G (dibujos)**: las ocho geometrías de la UI caben en **cinco tipos de nodo**, y
>   polígono/polilínea/rectángulo son **el mismo**. Y lo que la trababa quedó resuelto:
>   **Maestro REUTILIZA la geometría dibujada** cuando un mecanizado la toma — un nodo, dos
>   dueños. El `Texto` tampoco es una familia nueva: son contornos.
> - **C (operaciones de máquina)**: `Xn`, `Xmsg` y `Park` derivados de punta a punta, con
>   `.pgmx` **y** `.iso` de cada caso — la primera rama con el par completo.
>
> ⭐ **Y la traza va en coordenadas de PIEZA**, no de máquina: con el origen movido a
> (100,50), la geometría y la traza salen idénticas y el origen entra por el bloque
> `SHF`/`%Or`. Con origen (0,0) las dos lecturas coincidían; ahora están separadas. Es lo que
> el converter necesita para mapear un dibujo a la traza.
>
> ⚠️ **Lo que falta es la rama D — los mecanizados**, que es donde vive la mayor parte de un
> ISO real. Y un hueco que la acompaña: el **número del `Xmsg`** resultó ser un **conteo** que
> cada elemento anterior incrementa — y el 25 se derribó la parte cómoda de esa idea: el
> incremento **no es un número por tipo de operación, es una fórmula por tipo**
> (`Xmsg` = `largo(texto) + 7`). Así que cada mecanizado que se estudie tiene que aportar **su
> fórmula** —no su número— o no habrá byte-idéntico en programas con mensaje.
>
> **El converter todavía no existe, y es a propósito**: `iso/` son 312 líneas —el archivo del
> emisor, el snapshot y las rutas— y ninguna convierte. Se construye una vez, sobre evidencia.
> Suite **357 passed**, 100% offline.

## El estado del 2026-08-17

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
> ⏭️ **CAMBIO DE ORDEN (Fermín, 2026-08-18): se antepone la rama G — dibujos y
> sintetizador — a C.** La pregunta «¿el sintetizador puede generar todos los tipos de
> dibujos?» dio **no**, y la auditoría destapó algo más serio que el conteo: de las cinco
> geometrías que sabe emitir, **sólo la línea está respaldada por fixtures de la época
> nueva**. El arco, el círculo y la polilínea se validan por roundtrip contra nosotros
> mismos, y su única ancla externa es de la **serie N, época congelada**.
>
> Como el sintetizador es la **fábrica de fixtures** de toda la reinvestigación, esa duda se
> hereda a todo lo que produzca — incluidos C y D. Detalle en `experiments/dibujos.md` §9,
> plan de fixtures en §11.

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
  Xn, variable) — ✅ **generado y postprocesado** (los seis ISO están en
  `P:\USBMIX\ProdAction\R001_programa_vacio\`; B1b y B1c derivan de ellos). *El estado decía
  «⏸ postproceso» desde el 08-10; corregido el 08-27.*
- A2. Repaso opción por opción contra la UI de Maestro (capturas) — ⏸ capturas
- A3. Opciones que el synth no varía (offset de pieza, repeticiones, ciclo continuo, espejo
  tecnológico, opciones de mesa/mecánica) → gemelos manuales, una opción por archivo — ⬜
- A4. Fases (workplans) y orígenes múltiples — 🔮
- A5. **Parámetros de máquina** (serie R_PM) — ✅ **29 fixtures manuales (2026-08-10)**:
  16 llegan al ISO (14 mueven `V`, 2 mueven `T`), 12 no llegan y 1 rompe el postproceso
  (`Combiflex`). **Todas las diferencias caen en la línea del header**, ninguna toca el
  resto del esqueleto. Resultados en `experiments/parametros_de_maquina.md`.
  ~~Falta sólo `Repeticiones`~~ — **cerrado el 2026-08-22**: no llega al ISO, con testigo
  interno. El barrido A5 no tiene huecos.
  > ⚠️ **Pero doce de sus resultados son negativos SIN testigo** (anotado el 08-27): los
  > parámetros de máquina no viven en el `.pgmx`, y este lote no lleva capturas — 0 de 29.
  > Se leen como **probables**. Ver `iso/docs/fixtures.md` §4.
- A6. **Opciones de la aplicación** (serie R_OPC, el TERCER origen) — ✅ **17 fixtures
  manuales (2026-08-10/12)** para el programa vacío. **Una sola opción cambia el ISO**: el
  **estacionamiento automático al terminar**, que le agrega dos líneas. El resto no llega
  —las cuatro de acercamiento y alejamiento, la compatibilidad tecnológica, el
  estacionamiento por cambio de fase (probado con 2 y 3 fases) y, el 08-12, las **dos de
  prioridad 1** (`IsAreaScm`, `IsZetaScm`) más `IsBottomPlaneMachining` y
  `IsCheckCollisionEnabled`. Resultados en `experiments/opciones_de_aplicacion.md`.
  Queda para cuando haya mecanizado la familia que gobierna trazas. **`IsMM` ya se midió el
  2026-08-22 — no llega**, pero es un negativo **sin testigo**: ni el `.pgmx` ni el ISO
  cambian, así que ninguno prueba que la opción estaba puesta. Se lee como *probable*.
  Nueve de los 17 fixtures del lote tienen captura de la ventana; los otros ocho, no.
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

### G. Dibujos (geometrías) — 🔄 **SE ANTEPONE A C** (decisión de Fermín, 2026-08-18)
Rama abierta el 2026-08-16 por los fixtures de línea. Un dibujo es **geometría sin
`Feature`**: no crea mecanizado y **no deja rastro en el ISO** hasta que un mecanizado la toma.

> **Por qué se antepone a C**: el sintetizador es la **fábrica de fixtures** de toda la
> reinvestigación, y la auditoría mostró que de las geometrías que sabe emitir **sólo la línea
> estaba respaldada por fixtures de la época nueva**. El arco, el círculo y la polilínea se
> validaban por *roundtrip contra nosotros mismos*, ancladas en la serie N — época congelada,
> declarada no-fuente. Esa duda se hereda a todo lo que el sintetizador produzca, C y D
> incluidos.

- G1. **Línea** — ✅ derivada (11 fixtures): nodo `GeomTrimmedCurve`,
  `_serializationGeometryDescription` decodificado (tipo · intervalo · curva base · punto ·
  dirección, en `.17g`), los dos caminos de cálculo de la dirección, y la geometría
  **paramétrica** vía `Parametrics.Expression`
- G2. **Lote «Rama G»: 88 fixtures manuales, ocho familias** (2026-08-19) — ✅ estructura
  derivada (`dibujos.md`). Lo principal:
  - los tipos: `GeomTrimmedCurve` (línea y arco), `GeomCircle`, **`GeomEllipse`** —que no
    teníamos—, `GeomCompositeCurve` y `GeomCartesianPoint`
  - **el espacio final es por código de curva**, dentro y fuera de compuestos: recta `1`
    **con** (130 casos), cónicas `2` y `3` **sin** (53)
  - **`N̂z = +1` antihorario · `−1` horario** (8/8) y barrido angular siempre positivo (20/20)
  - **polígono, polilínea y rectángulo son EL MISMO nodo**: una sola firma estructural en los
    32 compuestos ⇒ la herramienta de la UI **se pierde** en el archivo
- G3. **Auditoría del sintetizador** — ✅ (`dibujos.md` §9): **no sabe hacer dibujos** —la API
  sólo acepta mecanizados, no hay `geometries=`— y cubre **cinco de ocho** tipos
- G4. **Texto** — ✅ **NO es una familia nueva** (2026-08-22): son **seis
  `GeomCompositeCurve`**, o sea Maestro convierte el texto a contornos. ⇒ las ocho geometrías
  de la UI caben en **cinco tipos de nodo**, y el barrido de familias queda **cerrado**
- G7. **La reutilización, resuelta** — ✅ (2026-08-22): `linea_01_fresada` tiene **una sola**
  geometría y el `Feature` apunta a ella por ID. **Maestro comparte el nodo, no lo duplica** —
  un dibujo, dos dueños. Es lo que trababa la rama
- G8. **El origen de la pieza** — ✅ (2026-08-24): vive en `<b:_xP>`/`<b:_yP>`, y **la
  geometría y la traza son relativas a él** — el origen entra por `SHF`/`%Or`. La traza va en
  **coordenadas de pieza**
- G9. **`GeomCircle.Radius`** — ✅ el radio se ata a un parámetro con el mismo
  `Parametrics.Expression` que las coordenadas de la línea
- G10. **`PlaneID`** — ✅ una geometría en otra cara apunta a otro `Plane` (1920 contra 1918)
- G5. **Corrección del sintetizador** — 🔄 **primera pasada hecha (2026-08-19)**: sacado el
  espacio final sobrante de los dos builders de arco, y **fijada la regla contra archivos de
  Maestro** en `tests/test_pgmx_dibujos_geometria.py` (11 fixtures versionados en
  `evidencia/dibujos_rama_g/`, suite sigue offline). La línea, el arco y el círculo ahora
  reproducen a Maestro **byte a byte**. Queda: `GeomEllipse` y decidir si el punto y los
  compuestos entran por una API de dibujos o siguen colgando de mecanizados
- G6. **Lo que queda abierto** — ⏸ `Name`, la `Z` fuera del plano, las otras cuatro caras y
  los otros métodos de la barra contextual. ⛔ **`<a:IsAbsolute>` queda DESCARTADO** (Fermín,
  2026-08-25): el checkbox «Coordenadas absolutas» resultó ser un modo de visualización que no
  se guarda, y el tag vale `false` en los 89 dibujos sin llegar al ISO. No se genera fixture

### H. Importación DXF — 🔮 futuro (idea de Fermín, 2026-08-19)

Entre las herramientas de dibujo de Maestro está la **importación de archivos `.dxf`**. Abre
un camino que vale estudiar: **dibujar en AutoCAD y salir a la máquina**. Son dos mitades
distintas y conviene no mezclarlas.

- H1. **¿Qué hace la importación DXF de Maestro?** — ⬜ Si importa geometrías, el resultado
  cae en `<Geometries>`: exactamente lo que la rama G está derivando. Lo decide un fixture
  barato — el mismo dibujo hecho a mano y importado de un DXF, y comparar los nodos.
  > ⇒ Si Maestro lo hace, **es un origen más de `.pgmx`**, como X-CAB (`circuito_pgmx.md`):
  > archivos de otra autoría que el converter va a tener que aceptar. Eso lo vuelve alcance,
  > no sólo comodidad.
- H2. **¿Puede nuestro sintetizador leer DXF directamente?** — ⬜ `.dxf` → `.pgmx` sin pasar
  por Maestro. Valor doble: una fábrica de fixtures mucho más rápida que dibujar a mano, y un
  camino de producción real.

**Lo que ya está en el repo y nunca se miró:**

| | |
|---|---|
| `pgmx/docs/xilog_plus_pgm/06_6_importacion_dxf.md` | 396 líneas. Documenta la importación DXF **del editor de Xilog Plus**, que produce **PGM**, no `.pgmx` ⇒ **fuera de alcance** por la decisión del 08-14. Sirve como **referencia de qué necesita una importación**, no como camino |
| `iso/data/machine_config/snapshot/xilog_plus/Cfg/cad.cfg` | **está en el snapshot**, 116 líneas de valores posicionales. Es la config de esa importación, con los valores de esta instalación |
| `pgmx/docs/maestro_scripting/` | **no menciona DXF** — el camino de Maestro no está documentado en lo que tenemos |
| nuestro código | **no toca DXF** en ningún lado |

Un dato del manual de Xilog que sirve para las dos mitades: la importación necesita
**auto-join con tolerancia** (default 0,01 mm) para decidir si dos elementos que casi se
tocan pertenecen al mismo perfil. *«Si su valor es demasiado pequeño, la importación se
produce de modo errado, generando demasiados perfiles disjuntos… si es demasiado grande,
perfiles que deben quedar diferentes podrían ser encolados.»* Es **el mismo problema de
tolerancia** que la rama G encontró al decidir si un compuesto está cerrado — y ahí también
hay que justificar el número con evidencia, no elegirlo.

> **Prerrequisito: la rama G.** Un DXF trae líneas, arcos, círculos, elipses y polilíneas —
> justo las geometrías que G está derivando. Sin saber cómo las escribe Maestro no hay a qué
> traducir.

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

### C. Operaciones de máquina — 🔄 **ARRANCÓ** (2026-08-20, doc `operaciones_maquina.md`)
Las cinco Funciones C.N. de la UI: `Xn` = «Operación nula», `Xmsg` = «Impresión mensaje»,
`Park` = «Aparcamiento», más **Palpación** y **Corte con cuchilla**, que no modelamos.

⭐ **Primera rama con el par completo**: `.pgmx` **y** su `.iso`. Los dibujos no llegaban al
ISO; estas sí, así que por primera vez se puede derivar la emisión de punta a punta.

- C1. **`Xn`** — 🔄 **28 fixtures manuales de Fermín (2026-08-20)** con sus 27 ISO. Derivado:
  - el bloque va entre el `G40` y el `SYN` (confirma B1b): **ocho líneas sin herramienta,
    quince con** —el cambio de herramienta agrega `T`, `SYN`, `M06` y un segundo cierre—
  - **`Reference`**: `Absolute` va tal cual · `Relative` **suma el `SHF` del eje**
  - **`Speed`**: `F = Speed × 1000`, y `Speed=0` cambia `G1` por `G0`
  - **`Tool`**: `E00n` → `T n`, más el bloque de cambio
  - **`Y`**: opcional —«sin `Y`» se escribe `<Y i:nil="true"/>`, distinto de `<Y>0</Y>`—, y
    **el signo se invierte**, que no está explicado
  - ⭐ **`Z201.000` ya tiene origen**: es `AP_PARKQTA` del eje Z en `Params.cfg`
    (configuración de máquina, no constante). Cierra el hueco que `emisor_iso.cfg` declaraba
  - y de paso queda explicado el número mágico `X_PARK = -3700.0` de la época anterior: el
    `AP_MINQUOTA` del eje X es `-3702.000`, así que era **un valor tipeado dos milímetros
    adentro del tope**, no algo derivable
- C2. **`Xmsg`** — 🔄 derivado (2026-08-22/24): dos líneas, y **el texto NO viaja al ISO**.
  Su número resultó ser un **conteo** —cada elemento anterior lo incrementa: +13 un `Xmsg`,
  +45 un `Xn`, confirmados en los dos campos—. 🚧 **Sigue bloqueando el byte-idéntico** hasta
  tener la tabla de incrementos de cada mecanizado
- C3. **`Park`** — ✅ derivado (2026-08-22): **es lo mismo que el estacionamiento automático**
  de la ventana Opciones, y **depende del campo** (`%ax0.pa21` en HG, `%ax0.pa31` en A). Su
  campo `Stop` no llega al ISO
- C4. **Varios `Xn` en un programa** — ✅ (2026-08-22): **sí se pueden**, cada uno emite su
  cuerpo y el orden se respeta. El `?%ETK[8]=1` + `G40` son **preámbulo del bloque**, no del
  `Xn`; el primero cuesta **seis** líneas y los siguientes **cinco**
- C5. **Corrección del sintetizador** — 🔄 **PARCIAL (2026-09-07)**, y el resto **vuelve a
  esperar a que estén estudiados todos los mecanizados** (Fermín, 2026-09-07 — misma decisión
  que la de abajo, reafirmada).

  **Hecho**, todo verificado contra los fixtures del lote D2:

  | | |
  |---|---|
  | `pgmx/tlgx.py` | lector de `def.tlgx`, la fuente real de los datos de herramienta. Cierra la brecha F0.7 |
  | el catálogo del sintetizador | deja de salir del CSV: **`def.tlgx`**, y la herramienta se resuelve **por nombre** |
  | «la herramienta decide» | ancho, radio y tipo de extremo, y el modo de corrección |
  | `Corrección en longitud` | con su acortamiento `√(p·(2r−p))` |
  | `Invertir` · `Canto a canto` · `Extra dist.` | con su geometría |

  **Dos defectos reales encontrados de paso**: el `tool_id` hardcodeado —en el `ChannelSpec` y
  en el mapa de brocas, con IDs que ya no existen— y el `ActivateCNCCorrection` en `true`
  cuando la sierra lo tiene en `false`. Suite 357 → 397.

  ⏸ **Pendiente**: la **rampa** (`Profundidad final`) y el **`Pasante` como expresión**. La
  rampa está bloqueada por un defecto latente de `build_line_geometry_profile` —con dos `Z`
  distintas la dirección sale plana— que vive en código **compartido** con el fresado, el arco
  y el círculo: el arreglo necesita fixtures de esos usos, y por eso espera a que la rama D
  esté completa. Detalle en `experiments/canal.md`.

- C5 (planteo original) — ⬜ **cuando estén estudiados todos los tipos de
  operación** (decisión de Fermín, 2026-08-20). `XnSpec` ya modela los seis campos; lo que
  falta verificar es la emisión, y hay una divergencia anotada en el `GeometryID`

### D. Mecanizados — 🔮 (una operación por vez, cada parámetro variado de forma controlada)

> **RUTINA PERMANENTE (Fermín, 2026-08-10)**: el barrido de parámetros de máquina **no se
> hace una vez y se archiva**. Se repite sobre **cada mecanizado básico** a medida que se
> estudian, porque la sospecha es que esos parámetros no sólo mueven líneas del esqueleto
> sino que **cambian el comportamiento de los mecanizados**. Cada etapa de D incluye su
> pasada de A5.
> ✅ **CUMPLIDO el 2026-09-07.** La traza de fresado quedó consolidada en
> **`experiments/fresado.md`** y el **`B2` de `anatomia_iso.md` está abierto**, con las tres
> familias de emisión comparadas. Lo de abajo es el aviso original.
>
> ⚠️ **La rama D ya tiene evidencia, archivada bajo otra rama** (anotado el 2026-08-27). La
> primera traza de mecanizado de la época nueva —`linea_01_fresada`— está documentada en
> **`dibujos.md` §13.1**, porque vino en el lote de dibujos:
> el cuerpo del fresado, que la traza **no es** la geometría (agrega posicionamiento, bajada
> en Z y salida), que `SVL`/`SVR` salen del catálogo y que `S…M3` sale de
> `spindle_speed_std`. Y su incremento del conteo (`+206`) está en `operaciones_maquina.md`
> §17.2. **Falta consolidarlo en un doc de la rama D y abrir el `B2` de `anatomia_iso.md`**,
> que hoy no existe.

- Perforado (vertical, lateral, patrones) — ✅ **DERIVADO (2026-09-03)**. Lote D1: **158
  `.pgmx`** en doce grupos, del programa vacío en los ocho campos hasta la alternancia entre las
  cinco caras. Cota, huso, orden, patrones, pasadas, transición entre caras y rechazos
  predecibles. Detalle en `experiments/perforado.md`
- Fresados (línea, arco, círculo, polilínea, contorno) — 🔄 **ABIERTO**, doc
  `experiments/fresado.md` (2026-09-07). Tiene **un solo fixture**, heredado del lote de
  dibujos: la línea con la `E001`. Y una derivación que vale: **su bloque es el MISMO que el
  del canal con fresa** ⇒ la familia de emisión la decide la herramienta, no la operación.
  **Es el lote grande que falta** — cuatro geometrías sin probar, más estrategia, acercamiento
  y pasadas
- **Canal** — ✅ **CERRADO (2026-09-07)**, doc `experiments/canal.md`. Quince grupos, 85
  `.pgmx` y 65 `.iso`, con la pasada de A5 hecha **y con testigo**. **Son dos bloques distintos según el cabezal de la
  herramienta**, y el `.pgmx` guarda las dos geometrías —nominal y corregida— para que el
  converter elija según `ActivateCNCCorrection`. Lo de abajo es cómo arrancó. Va
  detrás del perforado porque **es el mismo cabezal** (`def.tlgx` declara la `082` como
  `XilogBoringUnitTool`). Nomenclatura fijada por Fermín: en la UI se llama **`Canal`**, y está
  en el grupo `Fresado` de la cinta. Nueve predicciones falsables sacadas de la configuración
  —huso, máscara en `ETK[1]`, `SHF`, `SVL`/`SVR`, cara única— y una que **cierra la excepción
  del `SVR 1.900`** que `anatomia_iso.md` le había dejado a esta rama. ✅ **Grupo 1 hecho el
  2026-09-03: el bloque son 52 líneas y las ocho predicciones comprobables aciertan**; el
  sentido de corte lo pone el postproceso, no el `.pgmx`. ⛔ el Grupo 2 resultó **imposible**
  —sin herramienta no hay canal— y el desplegable destapó que **el canal acepta las siete
  herramientas del electromandril**, o sea dos formas de bloque (Grupo 11). ⏸ los grupos 3 a
  11 esperan a Fermín, **en campo `HG`** — en `A` la sierra se pasa del tope del eje X
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
- ~~¿El origen de la pieza aparece en el ISO vacío? ¿Dónde?~~ **RESPONDIDA (2026-08-10),
  anotada acá el 08-27.** Sí: en el bloque `%Or[0].of*` (micras) y `SHF[*]` (mm) de las
  líneas 11–19. B1c dejó la fórmula verificada 11/11 con el lote R002:
  `SHF[eje] = campo(primera letra del área, eje) − D_eje`, y la resta **sólo** cuando la
  coordenada del campo vale cero.
- ~~¿Una variable de usuario sin uso deja rastro en el ISO?~~ **RESPONDIDA (2026-08-17):
  NO.** Los cinco ISO de parámetros y los tres de líneas son idénticos al del programa
  vacío salvo la línea 1 (el nombre del archivo). Ni un parámetro sin usar ni una
  geometría sin mecanizado llegan al ISO ⇒ el converter puede ignorarlos.
- ¿Qué opciones de programa muestra la UI que el XML de la plantilla no expone (o al revés)?

## Bitácora del trayecto

### 2026-09-09 — Grupo 8: la matriz 7×7 de fresas, auditada y esperando ISO
Fermín lo llevó mucho más lejos del pedido: **56 archivos**, con **las siete fresas contra las
siete** más las combinaciones con canal y con taladro. Todavía **sin postprocesar**, así que
esto es la auditoría y las predicciones — el mismo orden que en el canal, donde la
configuración acertó ocho de ocho antes del primer ISO.

- ✅ **56 de 56 verificados**, leyendo el **orden del workplan** y no el de `<Operations>`, que
  es un catálogo. Con 49 combinaciones de dos herramientas hechas en una hora, era el lote con
  más riesgo de un «guardar como» pisado.
- ⭐ **Y aparece un segundo lugar donde el archivo se afirma a sí mismo**: Maestro **nombra y
  numera los pasos del workplan con su herramienta** (`Fresado 1 - E001`, `Canal 2 - 082`,
  `Taladrado 1 - D8P`). Sirve para auditar sin leer el `ToolKey`.
- ⚠️ **Tres cosas para arreglar antes de gastar 56 postprocesos**:
  - ⛔ **el canal quedó a profundidad 0** (`SlotSide.Depth = 0`, el estado neutro) en los dos
    archivos que lo llevan ⇒ no corta, y **el par no mediría la transición entre cabezales**,
    que es justamente lo que tiene que decidir;
  - 📌 **dos pares son duplicados exactos**, verificado por XML completo:
    `E001_D8P_fresado_taladro` = `E001_top_D8P_fresado_taladro_top` y `E004_dos_paralelos` =
    `E004_E004_dos_paralelos` ⇒ son **54 programas distintos**, no 56.
- 📋 **Predicciones escritas** (`fresado.md` §24.4): la diagonal con **un solo** `T`/`M06` y 71
  líneas; los 42 fuera de la diagonal con **dos** cambios de herramienta y todos sus números
  del catálogo; la matriz **simétrica en contenido** (`A_B` y `B_A` con los mismos bloques
  invertidos); y las dos transiciones **entre cabezales** (canal `?%ETK[7]=1`, taladro `=3`)
  con `G0 G53 Z201.000` en el medio.
- ✅ **CERRADO el mismo día**: Fermín corrigió las tres cosas y postprocesó los **54**. De las
  siete predicciones, **seis se cumplen y una se cae**.
  - ✅ **El cambio de herramienta queda cerrado con 49 combinaciones**: la diagonal con **un
    solo** `T`/`M06` (7 de 7) y **71 líneas exactas**; las 42 restantes con **dos** cambios y
    86 líneas; y **98 bloques comprobados contra `def.tlgx` con cero discrepancias**.
  - ⭐⭐ **El costo de una segunda operación, con fórmula**: `+20` con la misma fresa, `+35` con
    otra ⇒ **el cambio de herramienta cuesta 15 líneas**. Y no depende de si comparten la
    geometría.
  - ⭐⭐ **Las tres transiciones, medidas**: misma fresa **5 líneas** (por arriba, sin parar el
    husillo, con un `G0` **repetido** que resulta sistemático); otra fresa **13** (con `M5` y
    dos `G0 G53 Z201.000`); **otro cabezal 15** — y ésta es **idéntica para el canal y para el
    taladro**, con `G61`/`G64` y sin `M5`. ⇒ **la transición la decide el CABEZAL**, no la
    operación que sigue: la misma regla que el bloque.
  - ❌ **La predicción que se cae: la matriz NO es simétrica.** El bloque de una herramienta
    mide 48 líneas si va primero y 56 si va segundo — el primero trae el preámbulo de origen y
    `?%ETK[6]`, el segundo la transición. ⇒ **no hay un «bloque por herramienta» reutilizable**:
    hay uno de apertura y uno de continuación, y la herramienta sólo decide los números.


### 2026-09-09 — Grupo 7: el TERCER ORIGEN queda cerrado, con dos archivos
Dos archivos nada más, pero Fermín **cruzó** la `Cota de seguridad` del programa contra la
`Distancia de seguridad` de la ventana `Opciones`, y dejó **una captura de la ventana por cada
postproceso**.

- ⭐⭐⭐ **La ventana `Opciones` NO se lee al postprocesar.** El archivo que pide `Cota de
  seguridad = 30` se postprocesó con la opción en **20** y el ISO emitió `Z125`/`Z30`; el que
  pide **25** se postprocesó con la opción en **30** y emitió `Z120`/`Z25`. **El ISO siguió al
  archivo las dos veces**, y en el segundo caso el valor de la opción era *mayor*, así que no
  se puede confundir con un mínimo o un tope.
  - ✅ **Es el «experimento de las dos PCs»** que `configuracion_aplicacion.md` tenía planteado
    desde el 2026-08-09, hecho — y **sin necesitar la segunda máquina**: alcanzó con cambiar la
    opción entre dos postprocesos.
  - ✅ **Negativo con testigo**: las capturas registran el valor exacto de la ventana en cada
    corrida, así que es *derivado*, no *probable* (`fixtures.md` §4).
  - ✅ **La hipótesis de `fresado.md` §4bis pasa a derivada**, y con ella el patrón del §21.8:
    el tercer origen da **defaults que Maestro congela en el `.pgmx`** al crear la operación.
  - ⇒ **El converter no necesita `UI00.exe.Config`** para la cota de seguridad ni para el
    multiplicador del radio. ⚠️ Sin generalizar a las 175 claves: `PostFileFormat` sí actúa en
    el postproceso.
- ✅ **Y la cota de seguridad queda con variación aislada**: 20 · 25 · 30 sobre la misma
  herramienta, `Z = ToolOffsetLength + cota` y salida `Z = cota`. El diff entre dos de ellos son
  **exactamente dos líneas**. Lo que §4bis había derivado con un par que movía tres cosas.
- ⭐ **Las capturas dieron la traducción de las cuatro claves** de `Opciones > Parámetros >
  Acercamiento y alejamiento`. La que importa: `MillingRetractDistance` = **«Paso de
  retroacción en los fresados»**, que describe literalmente el retorno entre pasadas donde
  apareció el `10` sin procedencia.
  - ⇒ **El fixture del pendiente se abarata y cambia de forma**: hay que **crear** un
    `uni_EP_ph5` con esa opción en 15 (no postprocesar uno viejo, porque el valor se congela al
    crear) y mirar si la traza guardada trae `8 0 15`. Se ve **sin postprocesar**.


### 2026-09-08 (cierre) — Grupo 6: el acercamiento sale con fórmula, y la UI fuerza CAD con multipaso
27 archivos más (se pidieron 6) y los dos `corr_len` rehechos. 28 de 28 verificados.

- ⭐⭐ **El tamaño del acercamiento y del alejamiento es `RadiusMultiplier × SVR`**, exacto en
  diez puntos (multiplicadores 1,5 · 2 · 4, en lineal y en arco, de entrada y de salida). Los
  dos factores tienen procedencia —el `.pgmx` y el catálogo—: **ni una constante interna**.
- ⭐⭐ **`Bajada`/`Subida` es una RAMPA y `Cota` son dos movimientos.** Con arco, la rampa es
  una **hélice** (`G3 … Z-10 …` en un solo bloque). Una línea de diferencia en el ISO.
- ⭐⭐ **El `Automático` del lado del arco va CRUZADO respecto de la corrección**: `Corrección
  izquierda` produce el arco del lado `Derecho` y viceversa. Es físicamente correcto —el arco
  entra por donde no está el material— y es una trampa de nomenclatura de manual: un converter
  que asuma `Left → Left` **entra por el lado equivocado**.
- ⭐ **El `1 mm` de `G41`/`G42` no es «en X»: se recorre por la TANGENTE del primer
  movimiento.** Con arco de entrada sale en `Y`. Acota lo que el canal §21 había dejado como
  constante.
- ⛔ **El `Solape` no llega al ISO** sobre una línea abierta, con testigo interno. Queda
  probarlo en un contorno cerrado, que es donde tiene sentido.
- ⭐⭐ **Dato de Fermín: con multipaso, la UI FUERZA `Corrección CAD`** — al aceptar, cambia la
  selección sola. Contesta la pregunta que habían dejado los grupos 4 y 5, y da tres reglas
  duras: **multipaso ⇒ nunca `G41`/`G42`**, multipaso ⇒ siempre modo largo, y la combinación
  «multipaso + C.N.» **no existe** (un `.pgmx` con las dos no lo produjo Maestro).
- ✅ **El acortamiento de `Corrección en longitud` es el RADIO**, derivado ahora con dos
  profundidades: los `corr_len` estaban a 18 por un cambio involuntario y rehechos a 10 dan lo
  mismo. La fórmula del canal era del **disco**.
- 📌 **Y dos números que el converter no tiene que ir a buscar al tercer origen**: el
  `RadiusMultiplier` del `.pgmx` (default 1,2) no es el de `UI00.exe.Config`, y el `Speed = -1`
  del acercamiento significa «del catálogo», como el `0` de `Technology/Feedrate`.


### 2026-09-08 (noche) — Grupos 4 y 5: aparece de dónde sale la línea que aborta la máquina
26 pares más, y Fermín los armó **cruzando** en vez de barrer uno por uno — el cruce es lo que
hizo hablar a los dos grupos. 26 de 26 verificados por atributo.

- ⭐⭐⭐ **`%DONTCARESPEEDV=1` la emite «Salida a cota de seguridad» con multipaso.** Es la línea
  que hace abortar el ISO de Maestro en el CNC (Alarma 67) y que el hito del 2026-08-03 había
  encontrado sin saber su origen — el archivo de aquel día se llamaba `scs_mp5`, o sea
  **S**alida a **C**ota de **S**eguridad, **m**ulti**p**aso **5**: era este mismo caso. Aparece
  en los cinco archivos con `LiftShiftPlunge` + multipaso y en ninguno de los otros diez.
- ⭐⭐ **`SVR` no es el radio del cuerpo: es el radio de COMPENSACIÓN** = cuerpo + `Rebaba`. Con
  `Rebaba = 2` sale `SVR 4.000` / `VL7=4.000`, en CAD y en C.N. Acota `canal.md` §19, que se
  derivó con `SideOffset = 0` en todos los casos. Y desmiente una sospecha: con C.N. la traza
  no cambia con la rebaba, pero **no se pierde** — entra por el `SVR`.
- ⭐⭐ **`ActivateCNCCorrection = false` cambia la ESTRUCTURA del bloque**: agrega tres
  movimientos y **la bajada al material pasa de `DescentSpeed` a avance de corte**. Aislado con
  el par `corr_len_CN`/`corr_len_CAD`, que difieren sólo en el flag. Con `true` **y** lado, el
  bloque toma su tercera forma, la del `G41`/`G42`.
- ⭐⭐ **La fórmula del acortamiento de `IsPrecise` era del DISCO**: con fresa el acortamiento es
  el **radio** (2 mm por punta), y `√(p·(2r−p))` es directamente inaplicable — con `p=18` y
  `r=2` el radicando es negativo.
- ⭐ **El reparto de pasadas y el `Último hueco`**: sin `UH`, pasos de `PH` con el resto al
  final; con `UH`, desbaste hasta `profundidad − UH` y una pasada final. Control fino: `ph4` y
  `ph4_uh2` salen **byte-idénticos** porque el reparto ya coincidía ⇒ el `UH` **no agrega un
  movimiento propio**.
- ⭐⭐ **El `Bidireccional` no vuelve en vacío**: profundiza en el extremo y corta de vuelta. Y
  por eso no tiene `Conexión entre huecos` — los cuatro guardan `Straghtline` sin que nadie lo
  eligiera, que es **lo que el sintetizador ya hacía**, ahora verificado.
- ✅ **`Conexión entre huecos` = `StrokeConnectionStrategy`** (`Salida a cota de seguridad` =
  `LiftShiftPlunge`, `En la pieza` = `Straghtline`), y **el mapeo del sintetizador es
  correcto**, verificado contra el código. Lo que no tiene respaldo es el `Automatic` que
  usamos de default —**no existe en la ventana**— y que resolvemos como «perfil cerrado ⇒
  `InPiece`»: es una regla heredada, sin fixture de esta época, y elige el modo que deja la
  fresa volviendo a 2 mm de la superficie.
- ✅ **La estrategia sin multipaso no llega al ISO** (negativo con testigo interno: los `.pgmx`
  sí difieren). Y 🐞 **el bug de `StepDepth` no está en la cadena**: el ISO emite `4·4·2`, igual
  que el archivo; la divergencia (`3,33 × 3`) es del control al ejecutar.
- ⚠️ **Un `10` que el converter todavía NO puede escribir**: el retorno de «En la pieza» sube
  10 mm, y 10 es a la vez la profundidad total del fixture y **`MillingRetractDistance` de la
  ventana `Opciones`**. Si fuera lo segundo sería **la primera opción de la aplicación que llega
  a la TRAZA** — A6 nunca pudo verlo porque midió sobre programas vacíos. Lo separa un fixture a
  profundidad 14 (Grupo 15).
- 📌 **Corrección de lo escrito a la tarde**: `ZigZag` **sí existe en el sintetizador**
  (`ZigZagMillingStrategySpec`, con toolpath propio). Lo que le falta es estar en
  `synthesize_pgmx_help.md` y, sobre todo, un ancla que no sea `N025` — serie N, época
  congelada. El fixture sigue haciendo falta, pero para **re-anclar**.
- ✅ **`AllowanceSide`/`AllowanceBottom` no tienen campo en la UI**, confirmado por Fermín (ayer
  salía de leer las capturas).


### 2026-09-08 (tarde) — La tanda 1 del fresado: la rampa son ATRIBUTOS, y el sintetizador se destraba
El lote se pidió a la mañana y a la tarde ya estaban los grupos 1 a 3: **35 pares y 12
capturas**. Auditoría por atributo, 35 de 35 en campo `A` con la herramienta del nombre.

- ⭐⭐⭐ **La rampa no es un campo de la ventana: son ATRIBUTOS DE OPERACIÓN.** La UI no tiene
  «Profundidad final» — se agregan puntos con `Operaciones > Atributos > Profundidad`
  (`Profundidad` + `Posición (%)`), y en el XML son `OperationAttribute i:type="DepthAttribute"`
  con `UPar` y `Depth`. ⇒ **el nodo `<Attributes>`, que estaba vacío en todos los `.pgmx` desde
  el principio, tiene dueño**; y sus hermanos de la cinta (`Velocidad`, `Microuniones`) son con
  toda probabilidad otros dos tipos. **El mecanismo NO es el del canal**, donde la rampa sí eran
  `Depth.StartDepth`/`EndDepth`.
- ⭐⭐ **Y con eso queda derivado el defecto que bloqueaba al sintetizador.**
  `build_line_geometry_profile` con dos `Z` sacaba el largo en 3D y la dirección plana; Maestro
  saca **las dos en 3D**, y el vector que la sesión del 09-07 había calculado a mano acierta a
  los **diecisiete dígitos** (`8 0 300.04166377354994` / `1 50 200 8 0.99986114003960003 0
  0.016664352333993333`). Los otros dos síntomas también: cada tramo arranca en la `Z` donde
  terminó el anterior, y la curva `Lift` arranca en la `Z` del **final** y ajusta su largo.
- ⭐ **7 de 7 herramientas explicadas por el catálogo** (Fermín hizo el Grupo 1 con las siete, no
  con dos), y una regla nueva que el canal no pudo separar: **el avance de la bajada es
  `DescentSpeed × 1000`** — la `E003` lo tiene en 3 y sale `F3000` mientras las otras seis dan
  `F2000`. Dos velocidades del catálogo en el mismo bloque.
- ⭐⭐ **Las geometrías**: `G3` antihorario / `G2` horario con **centro absoluto** en `I`/`J`; el
  círculo sale en **dos medias vueltas** y el punto de entrada es el ángulo elegido; `Invertir`
  **invierte el sentido de recorrido** (con la sierra sólo sacaba la cola); el costo en líneas es
  **`50 + N segmentos`**, exacto en siete casos.
- ⭐⭐⭐ **Maestro aproxima la elipse en 36 arcos DENTRO del `.pgmx`.** La geometría guarda
  `GeomEllipse` —cuya forma `dibujos.md` §12.2 había predicho sin fixture, y acierta— y el
  toolpath guarda los 36 arcos ya calculados. ⇒ **la traza puede tener una familia de curva
  distinta de la geometría**, y **el converter no tiene que saber aproximar**: lee el toolpath.
- ⭐⭐ **Un solo cambio de herramienta para N operaciones**: el `texto_PRUEBA` son **once**
  fresados (un contorno cerrado por letra, con sus agujeros) y emite **un** `T4`/`SYN`/`M06`; el
  corrector sí se re-emite once veces. Contesta por adelantado el Grupo 8 de la tanda 2.
- ⛔ **Tres cosas resultaron imposibles, y las tres con testigo en las capturas**: la
  `Sobremedida` no está en la ventana (`AllowanceBottom`/`Side` son campos sin UI), la `Cota de
  seguridad` es **un** solo campo (así que no se puede separar cuál gobierna la aproximación y
  cuál la salida), y `Canto a canto` es del `Canal`. Un fresado **sobre un punto** tampoco se
  puede crear: el ISO sale idéntico al programa vacío salvo el nombre.
- ⛔ **Y en Maestro siempre se dibuja primero** (dato de Fermín): la reutilización de geometría
  no es un caso especial, **es la única forma que existe**. Nuestro sintetizador hace lo
  contrario — crea la geometría con el mecanizado —, y eso queda escrito como divergencia
  consciente.
- 📌 **Nomenclatura para la tanda 2** (regla 3, la UI manda): la estrategia ofrece **cuatro** y
  una es **`ZigZag`**, que no existe en el sintetizador; `ContourParallel` no aparece en el
  `Fresado`. Y el multipaso se llama **`Conexión entre huecos`** (dos opciones, **sin
  `Automatic`**), **`Profundidad hueco`** y **`Último hueco`**.
- ⚠️ **Siete nombres que mienten**: los del Grupo 1 dicen `x50_x300_y150` y la traza es
  (50,200)→(350,200). Ninguna derivación se apoyó en el nombre — `fixtures.md` §2 funcionando —,
  queda anotado para renombrar.
- ⏭️ **Tanda 2 replanteada**: 44 archivos, cuatro dados de baja por imposibles o ya contestados,
  y un **Grupo 14** nuevo (el atributo `Velocidad`, el sentido de un contorno cerrado con
  `Invertir`, y el tramo vertical que cierra la regla de emisión de ejes).


### 2026-09-08 — Arranca D3 (el fresado), y los archivos viejos pagan antes que los nuevos
Se pidió el lote grande que faltaba. Pero antes de pedirlo se midió lo que ya había, y eso
devolvió **dos derivaciones y una corrección** sin gastar un solo fixture.

- ⭐⭐ **El «+20» de la cota de aproximación NO es una constante: es el plano de seguridad de la
  operación.** `canal.md` §19 la había cerrado como `ToolOffsetLength + 20` con tres
  herramientas, las tres con el plano en 20. Un fixture heredado del lote de dibujos lo tiene
  en **30** y su ISO aproxima en `Z155.400` en vez de `Z145.400`, y sale en `Z30.000` en vez de
  `Z20.000`. **Es la regla 4 del `CLAUDE.md` en un caso concreto**: un converter con el `20`
  adentro habría emitido la cota equivocada sin poder notar que no sabía. `fresado.md` §4bis.
  - 📌 Y reabre —bien— una predicción de A6: `SecurityDistance` (20 en el CNC, 30 en otra PC)
    se había medido sobre un programa vacío, donde no hay trayectoria. Si el `30` del archivo
    es el default de la PC donde se creó, Maestro lo **congela en el `.pgmx`** ⇒ el converter
    no necesita leer ese origen. Lo contesta una pregunta, no un fixture.
- ✅ **El campo no mueve el bloque del fresado.** El mismo programa en `A` y en `HG` difiere en
  seis líneas: los dos bloques de origen, el nombre, la marca del header y el índice del `EDK`.
  Ni una del fresado. ⇒ el lote D3 **no lleva grupo de campos**.
- 📌 **Y una corrección de `fresado.md` §1**, que es §2 de `fixtures.md` otra vez: decía «el
  único fixture, campo `HG`». Son **cinco archivos**, en **dos campos**, y el que nombraba es
  campo **`A`**. Salió de leer el atributo, no el nombre.
- ⏸ **Lote D3 pedido**: 61 archivos y 5 capturas, trece grupos, campo `A`, herramienta base
  `E004` (Ø4 — con la `E001` de Ø18,36 no hay círculo chico ni esquina viva, y el grupo grande
  es el de geometrías). Dos tandas; la primera son los grupos 1 a 3, que **destraban el defecto
  de `build_line_geometry_profile`** y abren las cuatro geometrías nunca probadas.
  - Lo que sólo este lote puede contestar: las geometrías, la **estrategia** (con el par que
    explica el **paro de máquina del 2026-07-30**), el **pasante** (que el canal no pudo: el
    disco entra 10 mm), la **sobremedida** (no existe en el canal), las **microuniones** y la
    **cara inferior**, que si se descarta en silencio es el cuarto caso de fail-loud.
- ❓ **Una incongruencia de nomenclatura planteada, sin tocar código** (regla 1): las specs de
  fresado se llaman por la **geometría** (`LineSpec`, `CircleSpec`, `PolylineSpec`,
  `ContourSpec`) y la del canal por la **operación** (`ChannelSpec`). En la UI todas son
  `Operaciones > Fresado`, y `LineSpec` compite con `DrawingSpec` por la palabra «línea».
  `fresado.md` §8. No bloquea el lote: el sintetizador está congelado hasta que cierre la rama D.


### 2026-09-07 — Se cierra D2, y se tapan tres agujeros de método
Día de cierre y de repaso. El lote D2 termina con los grupos 14 y 15, y Fermín preguntó si
quedaba algún agujero antes de seguir: quedaban tres, y ninguno era del canal.

- ✅ **D2 CERRADO**: quince grupos, **85 `.pgmx` y 65 `.iso`**. El Grupo 14 cerró las siete
  herramientas (7 de 7 explicadas por el catálogo), y el Grupo 15 hizo **la pasada de A5 sobre
  un mecanizado por primera vez** — ocho fixtures **con sus ocho capturas**, y **ningún
  parámetro de máquina toca la traza**. El espejo tecnológico, que era el candidato, no espeja
  nada, y esta vez el negativo **tiene testigo**.
- ⭐⭐ **El conteo del `Xmsg` cuenta CARACTERES del texto emitido**, y eso resuelve la anomalía
  que el perforado había dejado como *«al revés de lo esperado, sin explicación»*: `X92.500`
  tiene un carácter **menos** que `X100.000`. Cambia la naturaleza del bloqueo del
  byte-idéntico: no falta una tabla por tipo de operación, **falta contar la salida**.
- ⭐ **El `Stop` del `Xmsg` llega al ISO** como el campo `S` (`Nothing`→`S0`, `NoUnlock`→`S1`,
  `Unlock`→`S2`, los dos últimos con `M0`). Estaba listado como «sin barrer» en la rama C.
- ⛔ **Tercer caso de fail-loud**: un canal más corto que el acortamiento de `Corrección en
  longitud` **no se rechaza — se da vuelta**, y emite un corte invertido en el lugar equivocado.
- 🧹 **Los tres agujeros, tapados**:
  - **`B2` de `anatomia_iso.md`, abierto**: qué agrega cada operación al esqueleto. Y con un
    hallazgo propio — **no hay un bloque por operación, hay uno por FAMILIA DE EMISIÓN**, y la
    familia la decide la herramienta: el «Fresado» de una línea y el «Canal» con una `E004`
    dan **el mismo bloque de 51 líneas**. `?%ETK[7]` la nombra: 3 taladrado, 1 disco, 4 fresado.
  - **`experiments/fresado.md` creado**: la traza que vivía archivada en `dibujos.md` §13.1
    queda consolidada en la rama D, con lo mucho que le falta escrito.
  - **`perforado.md` §9 repasado**: cuatro de sus siete «abiertos» ya estaban cerrados por sus
    propios grupos. Es el modo de falla que la auditoría del 08-27 describió, y que ya nos
    costó un lote repetido.
- 📌 **Y un off-by-one corregido**: el programa vacío son **43** líneas —los veinte campos, y
  como `programa_vacio.md` decía— no 44; el taladro agrega **41**, no 40.


### 2026-09-06 — El canal queda derivado, y son DOS bloques según el cabezal
Cierre del lote D2 con los grupos 7 a 13, más varios archivos que Fermín agregó por su cuenta y
que resultaron decisivos. **65 `.pgmx` y 45 `.iso`.**

- ⭐⭐ **El `Canal` emite dos bloques distintos según el cabezal de su herramienta.** Con la
  sierra `082` (cabezal perforador) es el bloque derivado el 09-03; con una `E00x` del
  electromandril hay **cambio de herramienta** (`T n` · `SYN` · `M06`), otro `SHF` de cabezal,
  sin cola, el corte en el sentido dibujado, y **`?%ETK[7]=4` — el del fresado**. ⇒ **el tipo de
  mecanizado no es de la operación sino de la herramienta.**
- 📌 **Y obliga a acotar tres reglas del 09-03**, que eran de la sierra y no del canal: el
  sentido normalizado, la cola de cuatro movimientos y la restricción de ángulo. **Con fresa el
  canal en Y y en diagonal postprocesan sin problema.**
- ⭐⭐ **El hallazgo más útil para el converter (Grupo 13, idea de Fermín)**: el `.pgmx` guarda
  **siempre** la traza con la corrección aplicada, y `ActivateCNCCorrection` decide qué hace el
  ISO — con **CAD la copia**, con **C.N. la DESHACE** y emite la línea nominal más `G41`/`G42`.
  Por eso el archivo guarda **las dos geometrías**, la nominal de la feature y el toolpath
  corregido: el converter usa una u otra según el flag. Los radios de la ventana aparecen sólo
  con herramienta de electromandril, que era el misterio que quedaba.
- ⭐ **El desplazamiento lateral es ±`SVR` en las tres herramientas** (1.9 · 2.0 · 9.18): el 1,9
  de la sierra nunca fue un caso especial. Y la sierra trabaja **siempre en modo CAD**.
- ✅ **Dos números dejan de ser hipótesis**: el `G0 Z80.000` es **`ToolOffsetLength` + plano de
  seguridad** (tres herramientas), y el acortamiento de `Corrección en longitud` es
  **`√(p·(2r−p))`**, que acertó exacto con profundidad 5. Mi lectura anterior del 80 —«radio del
  disco + seguridad»— daba el mismo número sólo por casualidad.
- ✅ **P4 CERRADA**: la Sierra Horizontal da `SVR 50.000` = `Diameter`/2. `SVR` es el radio del
  **cuerpo** de la herramienta. Era la pregunta que `anatomia_iso.md` le había dejado a esta rama.
- ✅ **`Condición = False` borra el mecanizado del ISO** (sale el programa vacío); **`Invertir`
  sólo saca la cola**; y **`Canto a canto`** lleva el canal a los bordes con distancias extra que
  aceptan negativos — que es lo que hacen los ISO de producción.
- ⛔ **Segundo caso de la excepción de fail-loud** (`CLAUDE.md` §4): un canal con `Inclinación`
  ≠ 90 **postprocesa** aunque la `082` tenga el eje fijo, y el ISO que sale no es un canal
  —pierde el corrector, cambia la convención de la Z y cuenta el offset del huso dos veces—.
  Peor que el caso de la cara inferior: allá faltaba una operación, acá salen **coordenadas
  equivocadas**.
- ⚠️ **Dos nombres de fixture mintieron** (archivos `E001` y `E007` con la `E004` adentro),
  atrapados por la verificación por atributo. La regla de `fixtures.md` §2 pagó por segunda vez.
- ⏸ **Lote de cierre pedido** (grupos 14 y 15, 14 archivos): las cuatro herramientas que faltan,
  el canal más corto que el acortamiento, el conteo del `Xmsg` contra el contenido, y **la pasada
  de A5 sobre el canal** — la rutina permanente, que no se había hecho sobre ningún mecanizado.
- 🔎 **Pista abierta**: el `0,75` de la cola aparece **una sola vez en toda la configuración de
  máquina**, en `gendata.cfg` (posición 30 del segundo registro), con dos `1.00` al lado que son
  candidatos al milímetro del `G41`/`G42`. Si sale de ahí, dejan de ser constantes internas.
  Decisión de Fermín: perseguirlo en los archivos de programa de SCM.


### 2026-09-04 — El canal no es sólo de la sierra, y un fixture mal nombrado paga el día
El Grupo 2 del lote D2 resultó **imposible entero**, y el archivo que quedó de intentarlo valió
más que el grupo.

- ⛔ **Sin herramienta no hay canal**: al vaciar el desplegable, **`Aplicar` se deshabilita**.
  ⇒ un `Canal` **siempre** lleva `ToolKey` explícito, y **no hay resolución automática** como la
  que hacía el perforado por diámetro + punta. Con captura, así que es derivado y no «probable».
- ⛔ **`Anchura` no se edita nunca** —ni con el desplegable vacío, donde conserva el `3,8` de la
  sierra—: no se puede pedir un canal «de tal ancho».
- ⭐ **El archivo guardado como `…_NT_…` tiene la `E004` adentro** (ID 1903). El nombre afirma
  una cosa y el `.pgmx` dice otra: **la regla del `fixtures.md` §2, atrapada por la auditoría**.
  Y como el resto quedó igual, es **un par controlado sierra contra fresa** que da tres cosas:
  - **`Width` sigue a la herramienta** (3.8 = `BladeThickness` del disco → 4 = diámetro de la
    fresa) ⇒ `tool_width` no es parámetro de entrada nuestro;
  - **`SlotEndType` también**: `WoodruffSlotEndType` con `Radius 60` para el disco,
    `RadiusedSlotEndType` para la fresa ⇒ **`end_radius = 60` no es parámetro: es el radio del
    disco**, y el tipo de extremo lo elige la herramienta;
  - ⭐⭐ **`ActivateCNCCorrection` depende de la herramienta**: `false` con la sierra, `true` con
    la fresa. Es el campo exacto de la **regla 5** del `CLAUDE.md` ⇒ matiza lo de anoche: la
    traza del canal no era la incógnita **porque la corrección estaba en el medio y el offset
    era cero**; en cuanto el Grupo 5 mueva la corrección, la traza guardada va a traer el ±1,9 y
    esos fixtures los tiene que hacer Fermín.
- ⭐⭐ **Y el desplegable ofrece OCHO herramientas**, no una: la `082` más las siete `E00x` del
  electromandril. ⇒ el `Canal` produce **dos formas de bloque distintas** según el cabezal de su
  herramienta, y sólo derivamos una. **Grupo 11** agregado, con un experimento que vale por
  todos: la **`E002` (Sierra Horizontal)** falsa la regla del `SVR` —si es el radio del cuerpo,
  una fresa de Ø100 tiene que dar `SVR 50.000`—.
- 📌 **Corrección de ayer**: escribí que los radios `Corrección C.N.`/`CAD` desaparecen con la
  sierra elegida. Tampoco están con el desplegable vacío ⇒ **el disparador no es la herramienta**
  y no sabemos cuál es.


### 2026-09-03 (noche) — El primer canal: 8 de 8 predicciones, y el sentido lo pone el postproceso
Primer fixture del lote D2, hecho por Fermín. Dos archivos del mismo canal —campo `A`, que **no
postprocesa**, y campo `HG`, que sí—, más cuatro capturas de la ventana con la herramienta puesta.

- ⭐⭐ **El bloque del canal, derivado**: **52 líneas** insertadas de una sola vez en el programa
  vacío, y **las ocho predicciones comprobables aciertan** —`?%ETK[6]=82`, `?%ETK[1]=16`,
  `SVL 60.000`, `SVR 1.900`, `S4000M3`, los tres `SHF` del huso y `?%ETK[7]=1`—. La sierra queda
  descrita **entera por la configuración**: `def.tlgx` y el registro 82 de `spindles.cfg`.
- ⭐⭐ **El sentido de corte lo pone el POSTPROCESO.** El canal se creó de X=50 a X=350 y el ISO
  posiciona en 350 y corta hacia 50; el `.pgmx` guarda el sentido nominal (`1 50 200 8 1 0 0`).
  ⇒ el converter **no puede copiar el sentido del `.pgmx`**, tiene que aplicar la regla. Primera
  confirmación con evidencia de la época nueva de lo que la doc congelada afirmaba.
- ⭐ **La Z del canal no es la del taladro**: la cota es **la profundidad en negativo**
  (`Z−10.000`) y el largo de la herramienta entra por el `SHF[Z]` del huso, no por la cota. En el
  taladro era `espesor − prof + tool_offset`. Y el `SHF[Z]` del programa sale **sin** el término
  `+%ETK[114]/1000`.
- ⛔ **El rechazo en campo `A` era predecible — y mi predicción estaba mal.** `ChkPgm:
  Microinterruptor- de tope eje X (T= 82)`: `50 − 3685.850 − 96 = −3731.850` contra `−3702.000`.
  Yo había escrito que el canal no debía toparse porque la `082` comparte el offset X con la
  broca `006`; **comparé herramientas en vez de coordenadas** — la `006` entra porque sus
  fixtures están en X=100. En campo `A` la sierra no pasa de **X ≈ 79.85**. ⚖️ Decisión de
  Fermín: **todo el lote D2 va en `HG`**.
- ⭐ **Y el `.pgmx` de Maestro coincide con el de nuestro sintetizador**: las ocho geometrías
  serializadas, idénticas carácter por carácter. 📌 Corrige mi propio planteo: yo había dicho que
  «la traza ES la incógnita» porque un disco de Ø120 no puede entrar a pique. **Entra a pique**:
  la trayectoria guardada es la línea nominal y una bajada vertical, y lo que el disco necesita
  lo agrega el postproceso. Vale para el caso con defaults.
- 📸 **La ventana cambia según la herramienta**: con la `082` puesta, `Anchura` muestra **3,8 en
  gris** —el ancho sale del disco, no del usuario— y **desaparecen** la sección `Estrategia` y
  los radios `Corrección C.N.`/`CAD`. `Acercamiento/Alejamiento` viene deshabilitado y trae
  `Multipl. radio = 4`, que es el `RadiusMultiplier` del CNC. Y aparecen tres cosas que no
  estaban en ningún grupo: `Invertir`, `Canto a canto` y `Condición` ⇒ **Grupo 10** agregado.
- 🚧 Sin explicación: el **`0.75`** de la cola de cuatro movimientos —el mismo en producción y en
  el fixture— y el `G0 Z80.000` de aproximación (hipótesis: radio del disco + plano de seguridad).


### 2026-09-03 (tarde) — Arranca el Canal, y la configuración contesta antes que el primer fixture
Decisión de Fermín: después del perforado va el **canal**, porque es un mecanizado distinto
**del mismo cabezal**. Doc nuevo: `experiments/canal.md`.

- ✅ **Lo confirma la máquina, no la intuición**: en `def.tlgx` la `082` es
  `KindOfTool = XilogBoringUnitTool`, mientras la Sierra **Horizontal** (`E002`) es
  `XilogSpindleUnitTool` con `shStorePos = 2` — ésa sí va al electromandril.
- ⭐ **La nomenclatura queda fijada por la UI (regla 3): se llama `Canal`.** Fermín dejó la
  captura de la ventana. Está en el grupo **`Fresado`** de la cinta, junto a `Corte con
  cuchilla`, `Vaciado` y `Galceado` ⇒ **la UI agrupa por familia de operación, no por cabezal**.
- 📌 **Y la ventana destapa tres incongruencias del `ChannelSpec`**: `Anchura` aparece en gris
  (nuestro spec la toma como parámetro de entrada), `Inclinación °` vale 90 contra un
  `slot_angle` en radianes, y `Corrección herramienta` tiene **cuatro** botones contra tres
  valores nuestros. Todos los defaults del spec son de la época congelada: hipótesis, no
  evidencia.
- ⭐⭐ **Nueve predicciones falsables, todas sacadas de la configuración** —`def.tlgx` (que
  viaja dentro del `.pgmx`) y el registro **82** de `spindles.cfg`—, contrastadas contra los
  ISO de producción: `?%ETK[6]=82`, `SVL 60.000`, `S4000M3`, `SHF[X]=−96.000`,
  `SHF[Z]=+22.150`, `?%ETK[7]=1` (el tipo de mecanizado del canal), y la cara **única**
  (`st_OFace.Face1`).
- ⭐⭐ **Dos que valen aparte.** (1) **`?%ETK[1] = 16`**: la sierra tiene `shPlcOut = 37` y
  `2^(37−33) = 16` ⇒ `ETK[0]` lleva los bits de PLC 1-32 y **`ETK[1]` los 33-64**. Es la
  extensión natural de la regla `?%ETK[0] = 2^(pos1 − 1)` que derivó el Grupo 6 del perforado.
  (2) **`SVR 1.900` deja de ser una excepción**: `SVR` es el radio del *cuerpo* de la
  herramienta, y la vertical es un `UniversalBlade` (`BladeThickness/2 = 1.9`) mientras la
  horizontal está catalogada como `Endmill` (`Diameter/2 = 50`). Una sola regla, dos cuerpos —
  cierra la pregunta que `anatomia_iso.md` le había dejado expresamente a esta rama.
- ⚠️ **Una predicción se sale de la regla de D1**: `SHF[Y] = −pos24 − 1.9`. El espesor del
  disco entra **dos veces**, en el `SVR` y en el `SHF[Y]`. Lo decide el Grupo 5 del lote.
- ✅ **Y se descarta un riesgo, corrigiendo hacia atrás la rama C.** La `082` había sido
  **rechazada** en el lote C (`Bag.Oheads: Herramienta E82 no configurada`), y sin embargo el
  taller corta canales con ella desde 2023 — **3157 ISO** en `P:\USBMIX`. **Lectura de Fermín,
  confirmada: el rechazo es del contexto `Xn`** —que la pide como herramienta de cabezal—, no
  del mecanizado. ⇒ `operaciones_maquina.md` §14 decía que la `082` «no está configurada en la
  máquina» y **es falso**: no lo está **en el cabezal que el `Xn` usa**. Para el converter la
  regla cambia de forma: no es «¿existe la herramienta?» sino **«¿existe en el cabezal que
  esta operación usa?»**. Y el punto 3 de ese §14 —la ambigüedad `holder_key`/`name`— se queda
  sin premisa y hay que re-derivarlo.
- 📄 **Lote D2 pedido**: `…\Mecanizados\Canal\INSTRUCCIONES.md`, 23 archivos en nueve grupos,
  más cuatro capturas de las secciones plegadas de la ventana.
- ⚠️ **Procedencia, dicha en el doc**: los ISO de producción **no son fixtures** —no se sabe de
  qué `.pgmx` salieron, probablemente X-CAB (rama F, diferida)—. Sirven para formar hipótesis,
  no para derivar.


### 2026-09-03 — El perforado queda derivado, y el barrido del corpus corrige tres cosas
Cierre de la rama D1 con los grupos 3 a 11 (158 `.pgmx`), más un repaso sistemático de todo el
corpus pedido por Fermín.

- ✅ **El perforado, entero**: la cota lleva el `ToolOffsetLength` del catálogo (77 vertical, 65
  lateral); el huso sale de `spindles.cfg` y `?%ETK[0] = 2^(PLC−1)`; el patrón es azúcar en las
  seis caras; el ISO **respeta el orden de creación**, también entre caras; y la transición entre
  caras emite un `G53` que sigue **`DZ + 20 + max(77, seguridad + shf_z)`** con el **máximo de
  los dos husos** — doce transiciones verificadas.
- ⭐ **Dos rechazos resultaron predecibles desde la configuración** (la cónica y la broca `061`
  en campo A se pasan del `AP_MINQUOTA` del eje X). El converter puede anticiparlos.
- ⛔ **Pero la cara inferior NO se rechaza: se descarta en silencio.** No hay huso con `FACE=6`;
  el `.pgmx` guarda el agujero y el ISO sale sin él. ⚖️ **Excepción declarada por Fermín**: cuando
  el byte-idéntico y el fail-loud chocan, **gana el fail-loud**. Escrito en `CLAUDE.md` §4.
- 🔎 **El Optimizador no cambia nada, y se sabe por qué**: agrupa por `HoleType` (diámetro +
  profundidad + punta) y **ningún par de husos de esta máquina hace el mismo tipo de agujero**.
  No es que sea flojo: no hay nada que agrupar. Explica que el taller nunca le viera diferencia.
- 📌 **Tres correcciones que salieron del barrido del corpus** (1.679 claves aplanadas, pares que
  difieren en UNA sola clave):
  - la **herramienta elegida SÍ viaja al ISO** cuando contradice a la resolución automática (el
    caso de la broca `007`). Lo que estaba escrito era falso;
  - `WorkPiece/Name` **no** llega — nunca se había probado;
  - la normalización del campo (`A`↔`AB`, …) da ISO **byte-idéntico**, no sólo el mismo header.
- ⚠️ **Y el barrido destapó un punto ciego propio**: un par «aislado» no está aislado si la
  variable vive fuera del `.pgmx`. Sin excluir A5/A6, tres claves aparecían como que llegan al
  ISO y no llegan. Es la clase de los negativos sin testigo, vista desde el otro lado.
- ⭐ **El orden de ejecución no está en `<Features>` ni en `<Operations>`**, que son catálogos:
  vive en la **posición** de los `MachiningWorkingStep` del workplan. `Priority` existe y vale 0.
- 🐞 **Un bug de Maestro, anotado** (lectura de Fermín): con `StepDepth` que no divide exacto,
  Maestro guarda `4·4·2` y el CNC hace `3.33×3`. Se retoma con las estrategias de fresado.


### 2026-08-27 — El nombre de un fixture es una afirmación, y dos tercios del corpus no afirman nada
Arrancaba la rama D y quedó en suspenso por un dato de Fermín: **los archivos manuales pueden
tener errores, sobre todo en el nombre** — el caso concreto, un archivo con la marca `HG` que
quedó guardado en campo `A` porque el cambio no se aceptó. Antes de pedir 40 fixtures nuevos se
auditó el corpus entero.

- ⭐ **Regla fijada (Fermín): el nombre nunca es evidencia; se cita el atributo leído del
  `.pgmx`.** Y su consecuencia, que parece al revés: **conviene que el nombre afirme cuanto se
  pueda**, porque un nombre que afirma se puede atrapar mintiendo y uno que no afirma nada no se
  puede chequear.
- ⭐ **Decisión (Fermín): todos los fixtures llevan el campo en el nombre**, con el string de
  `ExecutionFields` tal cual (`A`…`H`, `AB`, `HG`, `EF`). La rama D necesita ejemplos en todos
  los campos, y así el chequeo es igualdad exacta de strings.
- ✅ **Auditoría de los 239 `.pgmx`**: **una sola contradicción**, y ya documentada
  (`pulgadas` → `IsMM=true`). **La marca `HG` acertó 30 de 30.** El lote C está limpio: 278
  afirmaciones verificadas, todas verdaderas.
- ⚠️ **Lo que sí falta: 159 de 239 archivos no afirman nada verificable**, y **46 son
  inverificables por construcción** — A5 (29) y A6 (17) varían cosas que viven en `Params.cfg` y
  `UI00.exe.Config`, no en el `.pgmx`.
  - ⇒ los negativos de esos lotes **no tienen testigo**: *«no llega al ISO»* y *«no lo puse»*
    son indistinguibles. Se leen como **probables**. A6 pide captura en su protocolo y la tiene
    en 9 de 17; **A5 no la pide y tiene 0 de 29**. La exigencia se generaliza.
- 📌 **Corrección mía, del tipo que la regla 2 del `CLAUDE.md` describe.** Volví a derivar la
  tabla de campos, la estructura de `fields.cfg`, la regla de la primera letra, la fórmula del
  origen y el `EDK` — **todo eso ya estaba en `anatomia_iso.md` B1c desde el 2026-08-10**, y
  mejor derivado (la primera letra sale de `CD` contra `DC`, no de dos puntos; el `EDK` es la
  MITAD de la mesa, no el área). Leí el doc por grep y me detuve justo antes de la sección. El
  costo: un lote de 12 fixtures propuesto que R002 ya había barrido.
- 📌 **Hallazgos archivados por LOTE y no por rama** — el patrón que la auditoría destapó, y que
  hace que un doc no sepa lo que ya se contestó:
  - `Repeticiones` no llega (08-22) estaba en `dibujos.md` §14.1 y `parametros_de_maquina.md`
    seguía listándolo como fixture a hacer → **registrado en A5**;
  - `Pulgadas`/`IsMM` no llega (08-22) estaba en `dibujos.md` §14.2 y
    `opciones_de_aplicacion.md` seguía diciendo «qué mirar» → **registrado en A6**;
  - **la primera traza de fresado de la época nueva** vive en `dibujos.md` §13.1 mientras la
    rama D figuraba como 🔮 sin arrancar → **avisado en el mapa**; falta consolidarla.
- 🧹 **Estados obsoletos corregidos**: A1 decía «⏸ postproceso» (R001 está postprocesado desde
  el 08-10), A5 decía que faltaba `Repeticiones`, y «¿el origen aparece en el ISO vacío?» seguía
  como pregunta abierta con la fórmula derivada 11/11 desde el 08-10.
- 📄 **Doc nuevo**: `iso/docs/fixtures.md` — dónde vive cada lote, la regla del nombre, la
  auditoría y la clase de negativos sin testigo.


### 2026-08-25 — El incremento del `Xmsg` depende del contenido, y la tabla se vuelve fórmula
Un solo fixture (`XMSG_dos_largo` = `xmsg_dos` con el primer mensaje más largo) y contesta lo
que complica.

- ⭐ **`incremento(Xmsg) = largo del texto + 7`.** El texto crece **+19** caracteres y el conteo
  del segundo mensaje se corre **+19 exactos** (225 → 244). Pendiente 1 fijada por el delta,
  ordenada 7 por los dos puntos.
- ⭐ **El largo del propio mensaje NO mueve su propio `N`**: los dos primeros mensajes dan
  **212** pese a medir 6 y 25 caracteres. ⇒ el conteo es la posición **al empezar** a emitir el
  elemento, no al terminar.
- ⭐ **El texto ocupa lugar en el conteo aunque NO aparezca en el ISO** ⇒ confirma que el conteo
  cuenta algo del **programa compilado**, donde el texto sí está. Cierra el círculo con el 22
  («el texto del `Xmsg` no viaja al ISO») y con el 24 («es determinista, no es offset de bytes»).
- ⚠️ **Lo que le hace a la tabla de incrementos**: deja de ser «un número por tipo» y pasa a ser
  **una fórmula por tipo**. El **+45 del `Xn` está medido una sola vez** (`ops_tres`, con
  `x-3700`, sin herramienta ni `Y`) y ahora hay que sospechar que también depende del contenido.
  ⇒ Fixtures que lo cierran: el mismo programa con `x-2500`, con `Y`, y con herramienta, cada
  uno con un `Xmsg` detrás.
- ⚠️ **¿Caracteres o bytes?** Los tres textos medidos son **ASCII puro**, así que las dos
  lecturas no se distinguen. Un primer mensaje **con acentos** en `xmsg_dos` las separa.
- ⛔ **`<a:IsAbsolute>` DESCARTADO** por decisión de Fermín: vale `false` en los 89 dibujos, no
  llega al ISO y no bloquea nada. No se genera fixture. Si algún día aparece un `.pgmx` con
  `true` —de X-CAB o de un DXF— se retoma con ese archivo como evidencia.
- 📌 Corrección mía: un `git add -A iso/docs` se tragó `plan_cierre_converter.md`, que
  está untracked a propósito desde el 08-06. Revertido en un commit aparte; el archivo sigue
  intacto en el árbol.


### 2026-08-24 — El número del `Xmsg` deja de ser un misterio, y la traza va en coordenadas de pieza
Tanda de Fermín con los fixtures pedidos, casi todos en **los dos campos** (A y HG) para poder
separar lo que con un campo solo se confundía.

- ⭐ **El número del `Xmsg` es un CONTEO.** Cada elemento que lo precede lo incrementa,
  con base **212** (campo A) / **213** (HG), **+13 por un `Xmsg`** y **+45 por un `Xn`** — los
  dos incrementos confirmados **en los dos campos por separado**. Y quedaron descartadas las cuatro
  hipótesis previas: no depende del texto, **es determinista** (repostprocesar da el mismo
  número), no es offset de bytes ni número de línea.
  - 🚧 Sigue bloqueando el byte-idéntico, pero **ya no es un misterio: es una tabla que se
    llena midiendo.** Cada mecanizado de la rama D puede aportar su incremento poniéndole un
    `Xmsg` detrás. Hoy tenemos tres entradas.
- ⭐ **La traza se emite en coordenadas de PIEZA.** Con el origen de la pieza movido a
  (100,50) —vive en `<b:_xP>`/`<b:_yP>`—, la geometría sale **byte a byte idéntica** y la
  traza del ISO también (`G0 X50 Y50` · `G1 X350`). El origen entra por el bloque
  `SHF`/`%Or`. Con origen (0,0) las dos lecturas coincidían.
  - Y de paso: el header confirma R001 (**`;H DX/DY` = dimensión + origen**: 400+100=500), y
    aparece que **hay dos bloques de origen** en el ISO —el del esqueleto y el del
    mecanizado— que **no son iguales** cuando el origen no es cero.
- ⚠️ **«Coordenadas absolutas» NO se guarda en el archivo, y NO es `<a:IsAbsolute>`.** Fermín
  lo vio en la UI —casilla marcada, campos en gris, archivo sin asterisco, y al reabrir
  desmarcada— y el archivo lo confirma: reguardado con la casilla puesta, el XML queda **byte
  a byte idéntico**. Los seis `IsAbsolute=true` del archivo son de `<Planes>`.
  - ⇒ **Refutada** la correspondencia que `dibujos.md` §2 daba por buena. Era una lectura
    razonable sin fixture — el patrón de la regla 1. Y `<a:IsAbsolute>` de la geometría vuelve
    a **DESCONOCIDO**.
  - 📌 Corrección mía: el 22 pedí rehacer ese fixture porque «no capturó el cambio». Estaba
    bien desde el principio; no hay nada que capturar. Hice repetir trabajo por dar por
    sentada una hipótesis.
- 📌 **Corrección de Fermín**: había escrito «una geometría que un mecanizado toma **sí llega**
  al ISO». Es **PUEDE llegar** — lo que llega es la **traza**, que se *calcula a partir de* la
  geometría. La corrección de fresa y la rebaba dan recorridos paralelos, el acercamiento y el
  alejamiento agregan segmentos, y el vaciado produce una traza compleja desde una o más
  geometrías. El propio fixture lo muestra: el XY coincide **porque la compensación está
  cancelada** (sólo hay `G40`), y aun así la traza agrega posicionamiento, bajada en Z y
  salida.

### 2026-08-22 — `Xmsg`, `Park`, y el segundo campo separando cosas
64 `.pgmx` y 60 `.iso`. Fermín rehízo el lote en **campo HG** además del original en **campo
A**, y eso resultó ser mucho más que una duplicación.

- ⭐ **El `Park` es lo mismo que el estacionamiento automático** de la ventana Opciones: el
  bloque en campo HG es exactamente el `$EMI_PARK_FINAL` que se había derivado de los fixtures
  `eafe_*` (B1d). Uno puesto a mano en la lista, el otro agregado por la aplicación.
  - Y **depende del campo**: HG usa `%ax0.pa21`, campo A usa **`%ax0.pa31`** y agrega un
    `_paras` por delante. ⇒ corrige el alcance de `emisor_iso.cfg`: ese bloque **no es fijo**.
- ⭐ **El texto del `Xmsg` NO viaja al ISO.** Dos textos distintos dan la misma línea. Sólo va
  un número.
- ⭐ **`?%ETK[8]=1` + `G40` son PREÁMBULO del bloque de operaciones**, no parte del `Xn`, y se
  emiten una vez aunque haya varias. Lo destapó `XN_dos`: el cuerpo del `Xn` son **seis**
  líneas y el del segundo `Xn` **cinco** —no repite el `MLV=0`—. Corrige lo escrito el 20.
- ✅ **`Y_iso = −Y_pgmx`**, con cinco valores en dos campos. El signo se invierte y es
  sistemático.
- ✅ **`Relative`**: `X_iso = X + SHF[X]` · `Y_iso = Y − SHF[Y]`. Con un solo campo las dos
  fórmulas daban lo mismo; con dos, no.
- ❌ **Dos campos que no llegan al ISO**: `Park.Stop` y `Electromandril` (`SpindleEnable`).
  Otra vez «el modo se pierde».
- ❌ **`Repeticiones = 3` no llega** (con testigo interno: el `.pgmx` sí cambia). Cierra el
  último parámetro que faltaba del barrido A5.
- ❌ **`Pulgadas` tampoco llega**, pero el `.pgmx` queda idéntico ⇒ **negativo sin testigo**:
  el archivo no puede probar que la opción estaba puesta. Anotado como «probable».
  - Dato de método: Fermín tuvo que **reiniciar Maestro** para que cada opción tomara efecto
    ⇒ **son opciones que se leen al arrancar la aplicación**, no en cada postproceso. Toca
    directamente la pregunta E2.
- ⚠️ **Un fixture que no postprocesa**: el `Xn` con la herramienta `082` da
  `[23,5] - Bag.Oheads: Herramienta E82 no configurada`. ⇒ **el catálogo de Maestro y la tabla
  de herramientas de la máquina son dos cosas distintas**, y la ambigüedad `holder_key` contra
  `name` **no es resoluble en esta máquina**.

### 2026-08-20 — El Xn, derivado de punta a punta, y el Z201 deja de ser un misterio
Fermín armó `Reinvestigación\Operaciones\` con **28 `.pgmx` manuales y sus 27 ISO**. Primera
rama con el **par completo**: los dibujos no llegaban al ISO, estas operaciones sí.

- ⭐ **`Z201.000` sale de `Params.cfg`**: es el `AP_PARKQTA` del eje Z —«cota de
  aparcamiento»—, `201000` micras. Cierra el hueco que `emisor_iso.cfg` declaraba desde el
  08-13 y que era la razón de que el bloque del `Xn` no estuviera en ese archivo. **Es
  configuración de máquina, no una constante.** (`AP_MAXQUOTA` del mismo eje vale igual, así
  que la evidencia no las separa.)
- ⭐ **Queda explicado el número mágico de la época anterior.** `X_PARK = -3700.0` era una
  constante interna que el `CLAUDE.md` cita como caso testigo. El `AP_MINQUOTA` del eje X es
  **`-3702.000`**: el −3700 era **un valor tipeado a mano dos milímetros adentro del tope
  mecánico**. No salía de la config porque es una elección del operario — por eso nunca se
  pudo derivar, y por eso estaba mal como default.
- ✅ **`Reference`** (`Absolute`/`Relative`) decide si la coordenada va tal cual o **se le
  suma el `SHF` del eje**: `-3700` relativo dio `X-7385.850`, y `-3700 + (-3685.850)` da
  exactamente eso. Los dos nodos `Xn` son idénticos salvo ese campo.
- ✅ **`Speed`**: `F = Speed × 1000`, y `Speed = 0` cambia el código de `G1` a **`G0`**. 8/8.
- ✅ **`Tool`**: `E00n` → `T n`, y agrega `SYN` + `M06` + un segundo bloque de cierre. El
  bloque pasa de **ocho a quince líneas**, y el orden de `G61` y `MLV=0` se invierte.
- ⭐ **«Sin `Y`» y «`Y`=0» son casos distintos, y el archivo lo dice**: `<Y i:nil="true"/>`
  contra `<Y>0</Y>`, y el ISO emite la `Y` sólo en el segundo. Es la evidencia directa de la
  incongruencia que el `CLAUDE.md` cita como caso testigo (`xn=None` significando «el Xn por
  defecto» en vez de «ninguno»).
- ⚠️ **El signo de la `Y` se invierte** (`-1000` → `Y1000.000`) y la `X` no. Peor: con esa
  inversión la posición cae **fuera del rango del eje Y**. Dos fixtures no alcanzan para
  inventar una regla: queda anotado, sin resolver.
- ⚠️ **El `T` no se puede separar**: en el catálogo `E001` tiene `holder_key=001`, así que
  «puesto en el almacén» y «nombre» dan lo mismo para las siete herramientas del lote. Lo
  decide un `Xn` con una herramienta numérica (`001` o `082`).
- 🔍 **Divergencia anotada para la pasada de código**: `_build_xn_step` elige la forma del
  `GeometryID` según `spec.y is None`, y la evidencia dice que **no depende de la `Y`** —
  además, su rama «con Y» escribe una forma que Maestro no usa en ninguno de los 27. No
  llega al ISO, pero está mal atado.
- ⏭️ **El código no se toca hasta estudiar todos los tipos de operación** (decisión de
  Fermín). Faltan `Xmsg`, `Park`, y el caso de varios `Xn` en un programa.

### 2026-08-19 — El lote de dibujos, y la primera geometría validada contra Maestro
Fermín armó `Dibujos\Rama G\` con **88 `.pgmx` manuales**, ocho familias, uno por dibujo.

- ⭐ **El espacio final es POR CÓDIGO DE CURVA**, no por geometría: la recta `1` lo lleva
  (130 casos), las cónicas `2` y `3` no (53). Vale dentro y fuera de los compuestos. Era el
  delta que el 08-18 había quedado con `n=1` — y confirma que al arco del sintetizador le
  sobraba ese byte mientras que a su círculo no.
- ⭐ **Polígono, polilínea y rectángulo son EL MISMO nodo.** Una sola firma estructural en los
  32 compuestos, y ninguna diferencia en el XML completo ⇒ **la herramienta de la UI se pierde
  en el archivo**. Es el patrón de siempre —el modo se pierde—, un nivel más arriba. El
  sintetizador necesita **un** builder, no tres.
- ✅ **`N̂z = +1` antihorario, `−1` horario** (8/8, con la descripción de Fermín), y barrido
  angular siempre positivo (20/20).
- ⚠️ **Retractada una acusación mía**: había dicho que la base fija del sintetizador era una
  conjetura que fallaba en 9 de 20 arcos. Es **una elección canónica válida**: los 20
  describen la misma curva, con el mismo sentido y los mismos extremos, muestreados a
  tolerancia 1e-6. Lo único que había que arreglar era el espacio.
- 🐛 **Y un error de lectura mío, corregido por Fermín**: leí `P` como punto inicial y `t1`
  como longitud, ignorando `t0`, y concluí que a tres rectángulos les sobraba un segmento. El
  segmento va de `P + t0·D` a `P + t1·D`; en los compuestos `t0` rara vez es 0. No sobraba
  nada: **cuando el trazo arranca en medio de un lado, ese lado va partido en dos miembros
  colineales** que comparten la recta base.
- ✅ **Código corregido y, por primera vez, geometría fijada contra Maestro.** Hasta hoy el
  arco, el círculo y la polilínea se validaban por roundtrip contra nosotros mismos, anclados
  en la serie N (época congelada). `tests/test_pgmx_dibujos_geometria.py` compara ahora contra
  11 fixtures versionados: **línea, arco y círculo salen byte a byte**. Suite **332**.
- 🔮 **Rama H abierta** (idea de Fermín): la **importación DXF** de Maestro — dibujar en
  AutoCAD y salir a la máquina. Con G como prerrequisito.
- **Falta**: el `texto` (única familia de la UI sin fixture), `GeomEllipse` en el sintetizador,
  y las cinco propiedades que el lote no puede derivar (plano, `IsAbsolute`, `Name`, `Z` y las
  fórmulas sobre geometría).

### 2026-08-18 — El sintetizador no sabe dibujar, y su geometría está anclada en la época congelada
Pregunta de Fermín: *¿nuestro sintetizador puede generar todos los tipos de dibujos?*

- ❌ **No, y de dos maneras.** La API pública sólo acepta **mecanizados** —no hay
  `geometries=`—, así que no puede dejar geometría suelta: de los ocho dibujos de la pestaña
  Dibujar sabe autorar **cero como dibujo**. Y de los tipos de geometría cubre **cinco de
  ocho**: faltan elipse y texto, y el rectángulo no existe como tipo propio.
- ⚠️ **El hallazgo de fondo no es el conteo, es la evidencia.** Sólo la **línea** tiene
  fixtures manuales de la época nueva. El arco, el círculo y la polilínea se validan por
  **roundtrip contra nosotros mismos**, y el docstring de `test_pgmx_arc_authoring.py`
  declara que su validación final fue **N040 — serie N, época congelada, no-fuente**.
  Verificado: **ningún test compara geometría sintetizada contra un `.pgmx` de Maestro**, y
  en el repo no hay ningún fixture de dibujo. Regla 5 en su forma más pura.
- ⭐ **Primer fixture de arco de la época nueva** (Fermín, 08-18), y da **dos deltas**: al
  arco le sobra el **espacio final** —la línea lo lleva, el arco no— y el builder de base
  fija emite `0` donde Maestro escribe `-0`. El `-0` no es un defecto funcional, pero delata
  que **la base fija es una conjetura**: Maestro la deriva.
- ⛔ **El código NO se tocó.** Es una sola observación, y este mismo doc registra dos reglas
  derivadas de tres o cuatro casos que **cayeron con el fixture siguiente**. Cambiar la
  serialización movería los bytes de todos los arcos —`leads.py` y los ocho del vaciado— sobre
  una sola medición. Hace falta un segundo arco.
- ✅ **Cerrado de paso un pendiente de `dibujos.md` §7**: los seis usos de tolerancia `1e-15`
  **sí** reciben valores leídos de un `.pgmx` (`adapters.py` arma specs desde un snapshot y
  los manda a serializar). Con el ruido de ~3·10⁻¹³ medido, la tolerancia queda 300 veces
  corta — no es defecto funcional, pero explica por qué releer y re-sintetizar no da
  byte-idéntico.
- ⏭️ **Se antepone la rama G a C**: el sintetizador es la fábrica de fixtures de toda la
  reinvestigación.

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
