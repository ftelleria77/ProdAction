# El corpus de fixtures de la reinvestigación

**Documento vivo.** Dónde viven los lotes, quién los hace, y **por qué el nombre de un
fixture no es evidencia**. Complementa la regla 5 del `CLAUDE.md` (quién hace los fixtures)
con la parte operativa: cómo se verifica que un fixture es lo que dice ser.

Los hallazgos de cada lote NO van acá: van al doc de la rama que contestan
(`experiments/<feature>.md`, `anatomia_iso.md`). Acá va el corpus y el método.

## 1. Dónde viven

Rutas simétricas bajo `PGMX_ROOT` (`S:\Maestro\Projects\ProdAction`) e `ISO_ROOT`
(`P:\USBMIX\ProdAction`), ver `iso/paths.py`.

| lote | carpeta | n | qué barre | doc |
|---|---|---|---|---|
| R001 | `R001_programa_vacio\` | 7 | el programa vacío, una opción por archivo | `experiments/programa_vacio.md` |
| R002 | `R002_areas\` | 11 | el área de trabajo (campos) | `anatomia_iso.md` B1c |
| gemelo manual | `Programas Manuales\Reinvestigación\` | 10 | el base manual y la ventana «Parámetro» | `experiments/parametros.md` |
| A5 | `…\Reinvestigación\Parámetros de Máquina\` | 29 | parámetros de máquina | `experiments/parametros_de_maquina.md` |
| A6 | `…\Reinvestigación\Opciones de Maestro\` | 17 | la ventana Opciones | `experiments/opciones_de_aplicacion.md` |
| G | `…\Reinvestigación\Dibujos\` y `Dibujos\Rama G\` | 115 | las ocho geometrías de la pestaña Dibujar | `experiments/dibujos.md` |
| C | `…\Reinvestigación\Operaciones\` | 68 | `Xn`, `Xmsg`, `Park` | `experiments/operaciones_maquina.md` |
| D1 | `…\Reinvestigación\Mecanizados\Perforado\` | 158 | el perforado — ✅ doce grupos, cerrado el 2026-09-03 (140 `.iso`) | `experiments/perforado.md` |
| D2 | `…\Reinvestigación\Mecanizados\Canal\` | 85 | el canal (Sierra Vertical X) — ✅ **quince grupos, CERRADO** el 2026-09-07 (65 `.iso`) | `experiments/canal.md` |
| D3 | `…\Reinvestigación\Mecanizados\Fresado\` | 183 | el fresado — 🔄 **grupos 1 a 12 cerrados** (174 `.iso` y 23 capturas): las geometrías, la rampa, la estrategia, el acercamiento, la matriz 7×7 de herramientas, la cara, el cruce `Invertir` × corrección, el conteo del `Xmsg` y el barrido A5; el 13 (microuniones) **postergado**; grupos 14 a 17 pendientes | `experiments/fresado.md` |

R001, R002, D1, D2 y D3 llevan un `INSTRUCCIONES.md` en la carpeta del lote, con el pedido que
les dio origen.

> ⚠️ **Y la tanda 1 volvió con siete nombres que mienten** (2026-09-08): los del Grupo 1 dicen
> `…_x50_x300_y150_…` y su traza es (50,200)→(350,200) — el mínimo que estaba pedido. Los
> siete `.pgmx` y los siete `.iso` lo contradicen, y el del `E004` es byte-idéntico al `prof10`
> del Grupo 2. **Ninguna derivación se apoyó en el nombre**, que es exactamente para lo que
> sirve §2; queda anotado para renombrar. El resto de la auditoría: **35 de 35** en campo `A`
> y con la herramienta que el nombre afirma.

> ⚠️ **Y el barrido A5 del fresado volvió con SEIS nombres que mienten** (2026-09-10): los
> `R_PV_EF_fresado_A5_bloqueo_*`, `_mecanicas_*` y `_repeticiones_3` dicen campo **`EF`** y el
> archivo está en **`A`**. Es el modo de falla literal que motiva §2 — el campo se cambia en la
> **misma ventana** que el parámetro que se está variando, y no queda aplicado al programa.
>
> 📌 **Y esta vez el error AYUDA**: como quedaron en `A`, igual que la referencia, el diff mide
> **sólo el parámetro**. Si hubieran quedado en `EF`, el efecto del campo se mezclaría con el
> del parámetro y ninguno de los seis pares serviría. Lo que hay que corregir es el nombre.
> Ver `experiments/fresado.md` §28.1.

> 📌 **El fresado ya tenía cinco archivos antes de su lote**, heredados de `Dibujos\Rama G\`
> (`…linea_01_fresada`, su `XMSG` y los `…origen_x100_y50_linea_fresada`, en campo `A` y `HG`).
> No están contados en la fila D3 porque viven en la carpeta del lote G. `fresado.md` §1 los
> listaba mal —«el único fixture, campo `HG`»— hasta que se leyó el atributo: son cinco y el
> que nombraba es campo `A`. Otra vez §2 de este documento.

> 📌 **Ojo con la etiqueta `D2`.** `perforado.md` §7bis menciona «el lote D2» hablando de un
> barrido de campos que **nunca existió**: el Grupo 2 de D1 lo contestó sin fixtures nuevos.
> El `D2` de esta tabla es el del **Canal**, y es el único. Los lotes intermedios (Dibujos, Operaciones) no lo tienen: el pedido quedó en el
doc de la rama (por ejemplo `dibujos.md` §11). **D1 vuelve al `INSTRUCCIONES.md` en la
carpeta** — viaja con los archivos, se imprime para trabajar en la PC del CNC, y sobrevive a
que el doc se reorganice.

## 2. El nombre de un fixture es una AFIRMACIÓN, no un hecho

Dato de Fermín (2026-08-27): **los archivos manuales pueden tener errores, sobre todo en el
nombre.** El caso concreto que lo motiva: un archivo guardado con la marca `HG` en el nombre
pero que quedó en campo `A` porque el cambio no se aceptó antes de guardar.

⇒ **Ninguna derivación cita un nombre de archivo. Cita el atributo leído del `.pgmx`.**

Y de ahí sale una consecuencia que parece al revés y no lo es: **conviene que el nombre
afirme cuanto se pueda**, porque *un nombre que afirma algo se puede atrapar mintiendo, y uno
que no afirma nada no se puede chequear*. Un fixture llamado `arco_07` no puede contradecir a
su archivo; uno llamado `R_PV_A_manual_perf_top_001_x100_y100_prof10`, sí.

### La marca del campo

**Decisión de Fermín (2026-08-27): todos los fixtures llevan en el nombre el campo en el que
están configurados**, como el string de `ExecutionFields` tal cual (`A`, `B`, … `H`, `AB`,
`HG`, `EF`), en la forma `R_PV_<campo>_manual_<lote>_<caso>`. Así el chequeo es igualdad
exacta de strings, sin tabla de traducción en el medio.

Antecedente que lo hacía falta: hasta el lote «Dibujos» un nombre sin marca era campo **HG**;
desde «Rama G» pasó a ser campo **A**. El mismo prefijo `R_PV_manual_base_linea…` significa
HG en `Dibujos\` y A en `Dibujos\Rama G\`. No contaminó ninguna derivación —los tres archivos
que no siguen la convención de su carpeta (`R_PV_manual_base_linea_cara2`,
`R_PV_manual_op_Xmsg_NP`, `R_PV_manual_param_radio_antes*`) no tienen `.iso`—, pero en la
rama D sí podría: el campo mueve el `SHF`/`%Or`, el bloque del `Park` y la base del conteo
del `Xmsg`.

## 3. La auditoría del 2026-08-27

Un script abrió los **239 `.pgmx`** del árbol de reinvestigación, extrajo lo que dice el
archivo y lo contrastó contra lo que afirma el nombre.

**Una sola contradicción**, y ya estaba documentada:

| archivo | el nombre afirma | el archivo dice |
|---|---|---|
| `R_PV_manual_base_pulgadas` | pulgadas → `IsMM=false` | `IsMM=true` |

Era el negativo sin testigo del 2026-08-22 (`dibujos.md` §14.2), no un hallazgo nuevo.

> ✅ **Y dejó de serlo el 2026-09-07.** Al refrescar el snapshot apareció que `UI00.exe.Config`
> tiene el `RapidFeed` en **164,042** — exactamente `50` convertido a unidades imperiales —, lo
> que **prueba que la aplicación estuvo en pulgadas**. El testigo no estaba en el `.pgmx` ni en
> el ISO: estaba en el tercer origen, y tardó dieciséis días en aparecer porque no lo
> muestreábamos. Detalle en `experiments/opciones_de_aplicacion.md`.
>
> 📌 **Lección de método**: cuando la variable vive fuera del `.pgmx`, el testigo también puede
> vivir fuera — y el archivo de configuración **queda escrito**. Antes de dar un negativo por
> «sin testigo», conviene preguntarse qué archivo del tercer origen tocó esa opción.

**La marca `HG` nunca mintió: 30 de 30** (5 en Rama G, 25 en Operaciones). El modo de falla
que motiva esta sección no ocurrió en el corpus — donde el nombre lo afirma.

**El lote C está limpio.** 278 afirmaciones verificadas en `Operaciones\` (X, Y,
`Absolute`/`Relative`, herramienta, `Speed`, electromandril, tipo y cantidad de elementos),
**todas verdaderas**; el único archivo sin afirmación es `R_PV_manual_op`, el base. Las
derivaciones de la rama C se apoyan en fixtures cuyo nombre coincide con su contenido.

**Lo que sí falta: 159 de 239 archivos no afirman nada verificable.**

## 4. La clase que NO se puede verificar desde el archivo

De esos 159, **46 son inverificables por construcción**: los lotes **A5** (29) y **A6** (17)
varían cosas que no viven en el `.pgmx` sino en `Params.cfg` y en `UI00.exe.Config`. Ahí el
nombre es el único registro de qué se puso.

Y el problema no es parejo:

- los fixtures cuya opción **sí** cambió el ISO tienen testigo — el propio ISO prueba que
  algo se movió;
- los que **no** lo cambiaron no tienen ninguno. Ahí *«no llega al ISO»* y *«no lo puse»* son
  indistinguibles.

⇒ **Un negativo sin testigo se escribe «probable», no «derivado».** Ya se hizo con `Pulgadas`
(`dibujos.md` §14.2); corresponde al resto de la clase.

### El testigo es la captura de la ventana

`opciones_de_aplicacion.md` ya lo exige en su protocolo — *«más una captura de la ventana con
la opción alterada, guardada junto al ISO: deja registrado el valor exacto y en qué máquina se
hizo»*. Lo que falta es cumplimiento y generalización:

| lote | fixtures | con captura |
|---|---|---|
| A6 (Opciones de Maestro) | 17 | **9** (en `experiments/evidencia/opciones_*`) |
| A5 (Parámetros de Máquina) | 29 | **0** — y su doc no pide captura |

⇒ **La exigencia de captura se generaliza a A5** y a cualquier lote futuro cuya variable no
viva en el `.pgmx` — empezando por la pasada de A5 sobre cada mecanizado de la rama D, que es
rutina permanente.

> ✅ **Cumplida por primera vez el 2026-09-07**, en el Grupo 15 del canal: **ocho fixtures,
> ocho capturas**. Y rindió — los dos negativos del grupo (`espejo_tecnologico` y
> `repeticiones_3`) quedan **derivados** en vez de «probables», que es exactamente la
> diferencia que esta sección pedía. Ver `experiments/canal.md` §24.

## 5. El verificador

Hoy vive fuera del repo (scratchpad de la sesión). Lee cada `.pgmx` del lote, extrae campo,
dimensiones, origen de pieza, repeticiones, `IsMM`, geometrías, features y la lista de
`Executable` con sus campos, y reporta las afirmaciones del nombre que el archivo contradice.

⏸ **Pendiente de decisión (Fermín)**: llevarlo a `iso/` con tests, para que corra sobre cada
lote nuevo antes de derivar nada.

## 6. El barrido del corpus entero (2026-09-03)

Pedido de Fermín: en vez de comparar pares elegidos a mano, **aplanar cada `.pgmx` a todas sus
claves** y preguntar, para cada una, qué le hace a su `.iso`.

**Método**: se aplana el XML a rutas `Nodo/Subnodo → valor`, se descartan los identificadores
internos (`Key/ID`, `_serializingKeys`, …) que cambian en cada guardado, y se buscan en todo el
corpus los **pares que difieren en UNA SOLA clave**. Es la variación controlada, pero encontrada
automáticamente y sobre todos los pares posibles.

387 `.pgmx` · **1.679 claves distintas** · 1.375 constantes · **304 que varían**.

### ⚠️ Un punto ciego que el propio barrido destapó

La primera corrida marcó `Repetitions`, `IsTechnologicalMirror` y `WorkPiece/Name` como que
**sí** llegan al ISO. Es falso: todos esos pares involucraban archivos del lote **A6**, cuya
variable —el estacionamiento automático— **no vive en el `.pgmx`**. Las dos líneas que aparecían
eran justamente ese bloque.

⇒ **Un par «aislado» no está aislado si la variable real vive fuera del archivo.** Es la clase
de los negativos sin testigo (§4), vista desde el otro lado. El barrido excluye A5 y A6.

### El inventario, sobre 218 pares limpios

**Llegan al ISO (10):**

| clave | aislada | mueve |
|---|---|---|
| `Features/…/Diameter` | 41 | 41 |
| `MachiningParameters/ExecutionFields` | 307 | 297 |
| `Operations/…/Technology/Feedrate` | 10 | 10 |
| `Operations/…/Technology/Spindle` | 10 | 10 |
| `Operations/…/ToolKey/Name` | 34 | **2** ⭐ |
| `Setup/…/Placement/_zP` (origen Z) | 12 | 12 |
| `Executable/Reference` · `Speed` · `Tool/Name` · `Y` (el `Xn`) | 2 · 24 · 58 · 21 | todas |

**No llegan (4):** `Repetitions` · `WorkPiece/Name` · `Executable/SpindleEnable` ·
`_serializationGeometryDescription` de una geometría sin mecanizado.

### Lo que el barrido encontró que no sabíamos

- ⭐⭐ **`ToolKey/Name` mueve el ISO en 2 de 34 pares** — y eso **refuta** la derivación de que
  la herramienta elegida no viaja. Detalle en `perforado.md` §2.
- ✅ **`WorkPiece/Name` no llega**, con 8 pares aislados. Nunca se había probado.
- ✅ **La normalización del campo, confirmada en los ocho**: los 10 pares donde
  `ExecutionFields` cambia y el ISO **no** se mueve son exactamente `A`↔`AB`, `B`↔`BA`,
  `C`↔`CD`, `D`↔`DC`, `E`↔`EF`, `F`↔`FE`, `G`↔`GH`, `H`↔`HG`. Pedir la letra sola o su par
  produce el ISO **byte-idéntico**, no sólo el mismo header.

## 7. ⚠️ Los fixtures están atados a una CALIBRACIÓN, no sólo a una versión de config

**Corte de época: 2026-09-07.** Fermín cambió la fresa de 4 mm (`E004`) y tuvo que **rehacer su
calibración**. Todo lo medido **hasta el 2026-09-06 inclusive** —ramas A, B, C, D1 y D2— se
postprocesó con la configuración anterior, que quedó guardada en
`iso/data/machine_config/historico/2026-09-06_antes_de_la_E004/` con su README.

### Qué implica, y es más que un número que cambió

El `SVL` que emite el ISO sale del `ToolOffsetLength` del catálogo, y **ese campo lo escribe la
calibración**: es una **medición**, no geometría declarada. ⇒ el `77` de las brocas verticales,
el `65` de las laterales y el `60` de la sierra —que `converter_magic_numbers.md` cuenta como
«resueltos (catálogo)»— son resultados de calibración, y **cambian cada vez que se toca una
herramienta**.

⇒ **Cada fixture está atado al estado de calibración del día en que se postprocesó.** Si alguna
vez un ISO viejo no reproduce, esto es lo primero que hay que mirar — antes de buscar un error
en el converter.

### Las tres reglas que salen de acá

1. **Un valor medido se verifica contra el catálogo de SU época**, no contra el vigente.
   `tests/test_pgmx_tlgx.py` está partido así a propósito: los números que salieron de un ISO
   se chequean contra el `def.tlgx` histórico, y sólo las reglas estructurales —que no dependen
   de una calibración— contra el vigente. Atarlos al catálogo de hoy convertiría cada cambio de
   herramienta del taller en un test roto, y afirmaría algo falso.
2. ⚠️ **El `tool_id` NO es estable.** Maestro **reasigna todos los identificadores** cada vez
   que regenera el catálogo: el 2026-09-07 se vio dos veces el mismo día, corridos **+40** y
   después **+60** (`001`: 1888 → 1928 → 1948). El `ID` sólo es coherente **dentro** de un
   `.pgmx`, junto al `def.tlgx` que ese archivo trae embebido. **Hacia afuera, una herramienta
   se identifica por nombre** (`082`, `E004`).
3. **Lo más seguro para releer un fixture es su propio catálogo**: `load_tlgx_from_pgmx()` lee
   el `def.tlgx` que viaja adentro del `.pgmx`, que siempre es el que le corresponde.

### Y una diferencia conocida entre las dos épocas, sin barrer

En el mismo refresco, `UI00.exe.Config` apareció con `RapidFeed` en **164,042** —el mismo valor
convertido a unidades imperiales—. A6 lo había medido sobre un programa vacío, donde una
velocidad de rápido no se ve.

✅ **Corregido en la máquina el 2026-09-07**: Fermín lo devolvió a **50** y el snapshot se
refrescó. ⇒ **entre la época de los fixtures y la actual ya no hay diferencia en este valor.**
Las únicas que quedan son el case del `IsMM` (`true` → `True`) y el `IsCamViewEnabled`, que
`configuracion_aplicacion.md` tiene documentado como la vista de cámara y no toca el ISO.

✅ **Chequeado el 2026-09-07 y no llega al ISO**: sobre seis ISO de producción con traza
(`Prod 26-08-05 Magliochetti`), **1418 líneas `G0` y ninguna lleva `F`** — los rápidos no
llevan velocidad, la pone el control. Los únicos avances que aparecen son 2000, 5000 y 1000,
todos `feed_rate × 1000` del catálogo.

> ⚠️ **Es un CHEQUEO, no una derivación** (decisión de Fermín): los archivos de producción **no
> son parte de la reinvestigación**, se usaron sólo para ver si algo dado por derivado se había
> movido. Si alguna vez hace falta afirmarlo, va con fixture propio.

### De paso, el modelo se contrastó contra producción y aguantó

Mismo chequeo, misma salvedad. Sobre esos seis ISO, que nunca habíamos mirado:

| | |
|---|---|
| pares `SVL`/`SVR` | **44 de 44** explicados por el catálogo de la época |
| máscara del huso `?%ETK[0] = 2^(plc−1)` | **6 de 6** (los `=0` son el cierre del bloque, no una selección) |

⇒ Ninguna de las reglas derivadas se movió con el cambio de configuración.

