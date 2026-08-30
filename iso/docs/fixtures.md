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
| D1 | `…\Reinvestigación\Mecanizados\Perforado\` | 72 | el perforado — 🔄 grupos 0, 1 y 2 hechos | `experiments/perforado.md` |

R001, R002 y D1 llevan un `INSTRUCCIONES.md` en la carpeta del lote, con el pedido que les
dio origen. Los lotes intermedios (Dibujos, Operaciones) no lo tienen: el pedido quedó en el
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

Es el negativo sin testigo del 2026-08-22 (`dibujos.md` §14.2), no un hallazgo nuevo.

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

## 5. El verificador

Hoy vive fuera del repo (scratchpad de la sesión). Lee cada `.pgmx` del lote, extrae campo,
dimensiones, origen de pieza, repeticiones, `IsMM`, geometrías, features y la lista de
`Executable` con sus campos, y reporta las afirmaciones del nombre que el archivo contradice.

⏸ **Pendiente de decisión (Fermín)**: llevarlo a `iso/` con tests, para que corra sobre cada
lote nuevo antes de derivar nada.
