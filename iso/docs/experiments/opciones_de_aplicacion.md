# Barrido de la ventana Opciones — serie R_OPC

**Método propuesto por Fermín (2026-08-10).** Tomar el archivo base manual y alterar de a
una las opciones de la ventana `Opciones` de Maestro, para ver cuáles cambian el ISO.

Es el **tercer origen** (ver `configuracion_aplicacion.md`): configuración global de la
aplicación, que no viaja en el `.pgmx` y sin embargo puede decidir el ISO.

## Por qué este barrido NO se hace como el de Parámetros de máquina

Aquel variaba el **programa**, así que cada variante era un `.pgmx` distinto. Éste varía
la **aplicación**: el `.pgmx` es siempre el mismo y lo que cambia es la máquina.

| | Parámetros de máquina (R_PM) | Opciones (R_OPC) |
|---|---|---|
| Qué cambia | el programa | la aplicación |
| Archivos `.pgmx` | uno por variante | **siempre el mismo** |
| Nombre del ISO | distinto por archivo | **el mismo — se pisa** |
| Al terminar | nada que deshacer | **hay que restaurar cada opción** |

⚠️ **Antes de empezar: copiar el `UI00.exe.Config` a un lado.** El barrido cambia la
configuración de la máquina donde se postprocesa. Si alguna opción queda sin restaurar,
los programas de producción salen distintos sin aviso. Al terminar, comparar el archivo
contra la copia: tiene que quedar igual.

## Flujo por opción

1. Cambiar **una** opción en la ventana Opciones · `Aplicar`.
2. Postprocesar `R_PV_manual_base.pgmx` (sin abrirlo ni tocarlo).
3. **Renombrar el ISO** a `r_pv_opc_<nombre>.iso` antes del siguiente, o se pisa.
4. Devolver la opción a su valor original.

Como el `.pgmx` no cambia, **la línea 1 del ISO es siempre la misma**: cualquier
diferencia que aparezca es de la opción, sin ruido de nombres.

## Paso 0 — el control, que además cierra un pendiente

**Postprocesar el base tal cual, sin cambiar ninguna opción**, en la PC donde se vaya a
hacer el barrido.

- Si el barrido se hace en la **PC de oficina técnica**: comparar ese ISO contra el del
  CNC responde, para el programa vacío, **el experimento de las dos PCs** que quedó
  pendiente en `configuracion_aplicacion.md` — y si da idéntico, el resto del barrido se
  puede hacer ahí sin tocar producción.
- Si se hace en el **CNC**: sirve igual como referencia y verifica que el postproceso es
  repetible.

Guardar como `r_pv_opc_control.iso`.

## Lista priorizada

### Prioridad 1 — pueden tocar lo único que tenemos derivado

| Opción (ventana) | Clave | Qué mirar en el ISO |
|---|---|---|
| **Parámetros → Post → «Configuraciones del tope de referencia»** (Scm anterior ↔ Morbidelli posterior) | `IsAreaScm` | **`%Or[0].of*` y `SHF[*]`**. La fórmula del origen (B1c de `anatomia_iso.md`) se derivó entera con `IsAreaScm=False`. Si al invertirlo cambia, lo derivado vale sólo para esta configuración. |
| **Parámetros → Post → «Notación de profundidad de trabajo»** (Scm Z negativa ↔ Morbidelli Z positiva) | `IsZetaScm` | el **signo** de `%Or[0].ofZ` y de `SHF[Z]`, y el `DZ` del header |

### Prioridad 2 — pueden agregar o sacar líneas

| Opción | Clave | Qué mirar |
|---|---|---|
| **Funciones CN → «Estacionamiento automático finalizada la ejecución»** | `IsFinalPark` | si aparece un bloque de park que el `.pgmx` no pide. La captura de la PC de casa lo mostraba MARCADO y el archivo decía `False` — contradicción sin saldar |
| **Funciones CN → «Modalidad de estacionamiento finalizada la ejecución»** | `FinalParkStopType` | ídem, con el modo de paro |
| **Funciones CN → «Estacionamiento barras cerca del tope»** | `ParkNextToSideStop` | ídem |
| **Funciones CN → «Estacionamiento en cada cambio fase con mesa manual»** | `IsParkOnWorkplanChange` | **necesita un programa con dos fases**: con una sola no puede manifestarse |

### Prioridad 3 — cambian el formato o las unidades

| Opción | Clave | Qué mirar |
|---|---|---|
| **Parámetros → Post → «Formato de salida»** (XXL / PGM / ISO) | `PostFileFormat` | el archivo entero: otra extensión y otro lenguaje. Sirve para saber qué son los otros dos formatos |
| **Idioma → «Unidad de medida»** (Milímetros / Pulgadas) | `IsMM` | `*MM` → `*IN` y **todas** las medidas del esqueleto — ⚠️ **medido el 2026-08-22: NO llega**, ver abajo |

### Prioridad 4 — probablemente no se vean sin operaciones

`SecurityDistance`, `MillingRetractDistance`, `RadiusMultiplier`, `RapidFeed`,
`IsCheckCollisionEnabled`, `IsBottomPlaneMachining`. Se anotan para no repetir el error
de esperar que se manifiesten en un programa vacío: **sin trayectoria no tienen dónde
mostrarse.** Van con los mecanizados.

## Cómo se procesan

Igual que el barrido anterior, con la referencia apuntando al control:

```
py -m iso.machining_lab.comparar_variantes <carpeta_de_los_iso> r_pv_opc_control.iso
```

## El método que quedó (Fermín, 2026-08-10)

Mejor que el que se había propuesto arriba, en un punto que importa: **el `.pgmx` se
guarda con nombre propio**, así que el archivo queda como registro de qué opción estaba
activa, el ISO sale con su nombre sin pisarse, y —sobre todo— **se puede chequear si el
`.pgmx` cambió**, que es una pregunta que el flujo original no permitía hacer.

1. Partir del archivo base manual.
2. Cambiar **una** opción en la ventana Opciones.
3. Guardar el `.pgmx` con nombre propio en
   `S:\…\Programas Manuales\Reinvestigación\Opciones de Maestro\`.
4. Postprocesar.
5. **Devolver la opción a su valor original.**

Más una captura de la ventana con la opción alterada, guardada junto al ISO: deja
registrado el valor exacto y en qué máquina se hizo.

## Resultados

### `Distancia de seguridad desde la mesa de trabajo` = 25 (default del CNC: 20)

`SecurityDistance` · fixture `R_PV_manual_base_DSDMT_25.pgmx` · captura
`r_pv_manual_base_dsdmt_25.bmp`.

**El `.pgmx` es byte-idéntico al base.** XML de 18.567 bytes en los dos, sin una sola
diferencia; lo único que cambia en el ZIP son los nombres internos. ⇒ **La opción no se
escribe en el archivo**: no viaja con el programa.

> Matiz, para no leer de más: este programa **no tiene operaciones**, y la cota de
> seguridad es un parámetro de operación. Que no se congele acá prueba que no se guarda a
> nivel de PROGRAMA — no dice nada todavía sobre si se congela dentro de una operación al
> crearla. Eso lo responde el mismo experimento sobre un programa con un mecanizado.

**El ISO no cambia**: difiere sólo en la línea 1, que es el nombre del archivo.

⇒ Confirma la predicción de la prioridad 4: **`SecurityDistance` necesita trayectoria para
manifestarse.** Es un resultado con valor —acota dónde buscar— y no un experimento
fallido.

### Lo que la captura deja fijado, de yapa

La ventana muestra el nodo `Parámetros` (raíz) de la **PC del CNC**:

| Campo | Valor |
|---|---|
| Distancia de seguridad desde la mesa de trabajo | **25** (alterado; original 20) |
| Paso de retroacción en los fresados | 10 |
| Multiplicador del radio en aproximaciones/alejamientos | **4** |
| Velocidad rápida en los desplazamientos | 50 |
| Habilitar compatibilidad tecnológica en áreas **perpendiculares** en X o Y | desmarcado |
| **Estacionamiento automático finalizada la ejecución** | **DESMARCADO** |
| Modalidad de estacionamiento finalizada la ejecución | «Ningún paro» (en gris) |
| Estacionamiento en cada cambio fase con mesa manual | desmarcado |

Dos cosas que esto cierra:

1. **Se resuelve la contradicción del 2026-08-09.** Aquella captura mostraba
   «Estacionamiento automático finalizada la ejecución» **marcado** mientras el archivo
   decía `IsFinalPark=False`, y quedó anotada como inconsistencia sin saldar. No lo era:
   aquella captura era de la **PC de casa** y ésta es la del **CNC**, donde el checkbox
   está desmarcado y el config dice `False`. **Coherentes.** La UI y el archivo nunca se
   contradijeron; eran dos máquinas distintas.
2. Confirma en pantalla el `RadiusMultiplier = 4` del CNC (contra `2` en oficina técnica),
   que hasta ahora sólo se había leído del `UI00.exe.Config`.

⚠️ **Ojo con dos nombres casi iguales**, que son opciones distintas:

| Dónde | Texto | Alcance |
|---|---|---|
| Opciones → Parámetros | «áreas **perpendiculares** en X o Y» | global de la aplicación |
| Parámetros de máquina | «áreas **especulares** en X o Y» | del programa (`IsTechnologicalMirror`) |

### El reguardado: qué hace Maestro al «Guardar» sin renombrar

Fermín reabrió ese mismo archivo, lo guardó **sin cambiarle el nombre** y volvió a
postprocesar. Comparado contra la versión versionada (commit `f5febc4`):

| | antes | después de guardar |
|---|---|---|
| miembro XML del ZIP | `R_PV_manual_base_.xml` | **`R_PV_manual_base_DSDMT_25.xml`** |
| miembro `.epl` | `R_PV_manual_base_.epl` | **`R_PV_manual_base_DSDMT_25.epl`** |
| CRC del XML | `9c64dcab` | **`9c64dcab`** |
| tamaño del XML | 18.567 | 18.567 |
| el ISO | 675 bytes | **idéntico** |

⇒ **Guardar renombra los miembros del ZIP para que sigan al nombre del archivo, y no toca
el contenido.** El XML queda byte-idéntico (mismo CRC) y el ISO también. El nombre interno
se unifica solo; no hace falta hacer nada para arreglarlo.

### `Paso de retroacción en los fresados` = 15 (default: 10)

`MillingRetractDistance` · fixture `r_pv_manual_base_prf_15.pgmx`.

Mismo resultado que `SecurityDistance`: **XML byte-idéntico al base** (otra vez el CRC
`9c64dcab`) y **el ISO difiere sólo en la línea 1**.

⇒ Segunda confirmación de la prioridad 4: **necesita trayectoria para manifestarse.**

### `Multiplicador del radio en aproximaciones/alejamientos` = 3 (default del CNC: 4)

`RadiusMultiplier` · fixture `R_PV_manual_base_mrapal_3.pgmx`.

Tercer resultado igual: **XML byte-idéntico** e **ISO distinto sólo en la línea 1**.

Vale la pena que se haya probado igual, aunque estuviera anotado como «probablemente no se
vea sin operaciones»: **`RadiusMultiplier` es una de las dos claves en las que difieren el
CNC y la oficina técnica** (4 contra 2). Ahora está registrado que esa diferencia **no
puede manifestarse en un programa vacío**, y que el experimento de las dos PCs para esta
clave necesita sí o sí un fresado con acercamiento o alejamiento automático.

### Tabla de la familia «Acercamiento y alejamiento»

| Opción | Clave | Probado | XML | ISO |
|---|---|---|---|---|
| Distancia de seguridad desde la mesa de trabajo | `SecurityDistance` | 25 (def. 20) | idéntico | sólo el nombre |
| Paso de retroacción en los fresados | `MillingRetractDistance` | 15 (def. 10) | idéntico | sólo el nombre |
| Multiplicador del radio en aprox./alejamientos | `RadiusMultiplier` | 3 (def. 4) | idéntico | sólo el nombre |
| Velocidad rápida en los desplazamientos | `RapidFeed` | 40 (def. 50) | idéntico | sólo el nombre |

**Las cuatro dan lo mismo.** La familia entera gobierna **trazas**, así que su lugar de
prueba es un programa con mecanizado, no éste.

### ⭐ `Estacionamiento automático finalizada la ejecución` — SÍ llega al ISO

`IsFinalPark` + `FinalParkStopType` · fixtures `eafe_np`, `eafe_pdes`, `eafe_pes`.

**El primer parámetro de la ventana Opciones que cambia el ISO de un programa vacío.**
Con el checkbox marcado, el ISO pasa de 44 a **46 líneas**: se insertan dos, **entre el
`G40` (línea 21) y el `SYN`**, exactamente donde el `Xn` mete su bloque de ocho.

```
 SHF[Z]=18.000+%ETK[114]/1000
 ?%ETK[8]=1
 G40
+G0G53 X%ax0.pa21/1000 Y%ax1.pa22/1000
+_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )
 SYN
```

Esto **confirma la hipótesis que quedó anotada el 2026-08-09** y estaba en suspenso: sí,
el postprocesador agrega un estacionamiento que el `.pgmx` **no pide**, y sale de la
ventana Opciones. Un programa sin una sola operación termina con dos líneas de
movimiento a coordenadas de máquina.

**Los tres modos de paro dan el MISMO ISO.** `Ningún paro`, `Paro con espera de start` y
`Paro con desbloqueo y espera de start` producen archivos idénticos entre sí (salvo el
nombre). ⇒ **`FinalParkStopType` no llega al ISO**; sólo llega el hecho de que el
estacionamiento esté activo.

> Es el mismo patrón que en los parámetros de máquina, donde manual / automático /
> semiautomático de cada familia de bloqueo daban todos el mismo `V`: **el modo se
> pierde, la función llega.** Dos familias distintas, misma forma.

Dos observaciones sobre las líneas agregadas:

- La segunda es **idéntica a la línea 5 del preámbulo**
  (`_paras( 0x00, X, 3, %ax[0].pa[21]/1000, %ETK[500] )`), pero **con dos espacios
  finales**, mientras la del preámbulo no tiene ninguno. La misma instrucción se escribe
  distinto según dónde aparece — importa para el byte-idéntico.
- La primera usa la notación **sin corchetes** (`%ax0.pa21` en vez de `%ax[0].pa[21]`), que
  hasta ahora no habíamos visto en el esqueleto. Las dos formas conviven en el mismo
  archivo.
- El relevamiento de manuales ya había traído estas dos líneas casi iguales desde la macro
  `Fxc\Mbd\Park.pgm`, con el comentario italiano *«Ripristino corsa totale asse X»*. Ahí
  la primera usaba `pa31` y la segunda cerraba con `%ax[0].pa[22]/1000` en vez de
  `%ETK[500]`: son variantes de la misma macro.

### Las otras tres del lote

| Fixture | Opción | ISO |
|---|---|---|
| `ecfmm` | Estacionamiento en cada cambio fase con mesa manual (`IsParkOnWorkplanChange`) | sólo el nombre |
| `hctapXY` | Habilitar compatibilidad tecnológica en áreas **perpendiculares** en X o Y | sólo el nombre |
| `VRD_40` | Velocidad rápida en los desplazamientos = 40 (def. 50) (`RapidFeed`) | sólo el nombre |

El de `ecfmm` no era concluyente con una sola fase — **se resolvió abajo**.

### `Estacionamiento en cada cambio fase con mesa manual`, con fases de verdad

`IsParkOnWorkplanChange` · fixtures `2fases`, `2fases_ecfmm`, `3fases`, `3fases_ecfmm`.

Fermín armó programas con **dos y tres fases** (`Fase1`, `Fase2`, `Fase3`) y postprocesó
cada uno **con y sin** la opción activada. Los `.pgmx` traen las fases de verdad: 2 y 3
`MainWorkplan` con su `Setup` propio, contra 1 del base.

**Los cuatro ISO son idénticos al base**: 44 líneas, sin una sola diferencia fuera del
nombre del archivo. Y el cruce lo confirma por partida doble:

| Comparación | Resultado |
|---|---|
| `2fases` vs `2fases_ecfmm` | idénticos |
| `3fases` vs `3fases_ecfmm` | idénticos |
| `2fases` vs `3fases` | idénticos |

⇒ Dos cosas, y conviene no mezclarlas:

1. **Las fases VACÍAS no dejan ningún rastro en el ISO.** Un programa con tres fases sin
   operaciones emite exactamente lo mismo que uno con una. El ISO no lleva marca de fase
   por el solo hecho de que la fase exista.
2. **`IsParkOnWorkplanChange` no llegó**, ni con dos fases ni con tres.

⚠️ **Lo segundo todavía no está cerrado.** Las fases están vacías, y un «estacionamiento
en cada cambio de fase» bien puede necesitar que haya **algo que ejecutar** en cada una
para que el cambio ocurra. El fixture prueba que la opción no se manifiesta con fases
vacías; no prueba que no se manifieste nunca. Se cierra con un programa de dos fases
**con un mecanizado en cada una** (rama D).

Con `VRD_40` se completa la familia «Acercamiento y alejamiento»: **las cuatro no llegan
al ISO de un programa vacío.**

### ⭐ Las dos de `Parámetros → Post`: la prioridad 1 no llega (2026-08-12)

`IsAreaScm` e `IsZetaScm` · fixtures `ctr_scm` y `npt_scm`. **Las dos claves valen `False`
en el CNC**, así que ponerlas en «Scm» es un cambio real, no un no-op.

| Fixture | Opción | Clave | XML | ISO |
|---|---|---|---|---|
| `ctr_scm` | Configuraciones del tope de referencia = **Scm (anterior)** | `IsAreaScm` | idéntico | **sólo el nombre** |
| `npt_scm` | Notación de profundidad de trabajo = **Scm (Z negativa)** | `IsZetaScm` | idéntico | **sólo el nombre** |
| `htcivp` | Habilitar trabajos en cara inferior con volcado de pieza | `IsBottomPlaneMachining` | idéntico | sólo el nombre |
| `acccgt` | Habilitar control de colisión del cabezal al generar traza | `IsCheckCollisionEnabled` | idéntico | sólo el nombre |

**Ninguna de las cuatro llega al ISO de un programa vacío.** Las dos primeras eran las de
prioridad 1 —las que podían invalidar lo derivado—, así que el resultado hay que leerlo
con precisión, porque las dos no dicen lo mismo:

- **`IsAreaScm` (el tope de referencia) es el resultado fuerte.** El origen SÍ está en el
  vacío (`%Or[0].of*`, `SHF[*]`) y **no se movió ni un micrón**. La advertencia que estaba
  escrita en B1c —«lo derivado vale sólo para este tope»— se relaja: la fórmula del origen
  **no depende de esta opción**. Tiene explicación, además: el origen sale de `fields.cfg`,
  que es configuración de **máquina**, y esta opción es de **aplicación**.
- **`IsZetaScm` (la notación de Z) es un resultado débil**, y conviene no cobrarlo de más.
  Lo que la opción gobierna es la **profundidad de trabajo**, y un programa sin operaciones
  no tiene ninguna: `SHF[Z]` y `ofZ` son el ORIGEN, no una profundidad. Es el mismo caso
  que la familia de acercamiento y alejamiento — **necesita trayectoria para manifestarse**,
  y su lugar de prueba es un mecanizado con profundidad.

⚠️ **Estos cuatro fixtures no traen captura de la ventana.** Los anteriores sí. Para los
que dan negativo la captura es la única prueba de que la opción estaba efectivamente
alterada al postprocesar; sin ella, el resultado se apoya en el procedimiento y no en el
archivo. Vale la pena para `ctr_scm`, que es el que sostiene una afirmación fuerte.

### El CRC que se repite

Los cinco `.pgmx` mirados hasta ahora —el base, el `DSDMT_25` antes y después del
reguardado, el `PRF_15` y el `mrapal_3`— tienen **el mismo CRC de XML: `9c64dcab`**.
Ninguna de estas opciones de la ventana Opciones deja rastro en el archivo: son de la
aplicación, no del programa, y eso queda probado por identidad de bytes y no por lectura
de campos.

## Cómo se procesa la serie

`iso/machining_lab/procesar_opciones.py` recorre la carpeta entera y contesta las dos
preguntas por fixture —¿cambió el `.pgmx`? ¿cambió el `.iso`?—, que son independientes:
una opción puede no estar en el archivo y aun así decidir el ISO, que es justamente lo que
se busca.

```
py -m iso.machining_lab.procesar_opciones
```

### De yapa: qué nombre usa el ISO, con los tres separados

En este fixture conviven **tres nombres distintos** (aclaración de Fermín): guardó desde
Maestro como `R_PV_manual_base_` y **después renombró el archivo desde el explorador de
Windows**.

| Qué | Nombre |
|---|---|
| el archivo `.pgmx` (renombrado en Windows) | `r_pv_manual_base_dsdmt_25` |
| el miembro `.xml` dentro del ZIP (el «Guardar como» de Maestro) | `R_PV_manual_base_` |
| la pieza (panel Pieza) | `R_PV_manual_base` |

Y el ISO emitió **`% r_pv_manual_base_dsdmt_25.pgm`**: el del **archivo**. Los otros dos
no aparecen en ninguna línea.

⇒ **La línea 1 sale del nombre del ARCHIVO**, no del XML interno ni del nombre de la
pieza. Ya se había derivado del par `manual_base` / `manual_base_CNC`, pero ahí los tres
nombres coincidían; acá están separados y se ve cuál gana.

⇒ Y **renombrar un `.pgmx` desde el explorador no lo rompe**: Maestro lo abrió y lo
postprocesó con el miembro del ZIP llamándose distinto. El nombre interno es
independiente del nombre del archivo.

## `Pulgadas` (`IsMM`) — no llega, pero el fixture no tiene testigo (2026-08-22)

Registrado acá el 2026-08-27. El fixture es `R_PV_manual_base_pulgadas`, de la tanda de
dibujos; el detalle original está en `dibujos.md` §14.2, pero **la opción es de esta ventana
y su casa es este doc**. Cierra la prioridad 3 de la lista de arriba.

- **El ISO no cambia**: sigue diciendo `*MM` y todas las medidas quedan en milímetros.
- **El `.pgmx` tampoco cambia**: `<IsMM>` sigue en `true`, y el XML queda byte-idéntico al
  base.

⚠️ **Y ahí está el problema: el archivo no puede probar que la opción estaba puesta.** Si
`IsMM` no se escribe en el `.pgmx` y tampoco llega al ISO, entonces *«la opción no llega»* y
*«la opción no quedó aplicada»* producen exactamente los mismos dos archivos.

⇒ Se anota como **probable**, no como derivado. Es el caso testigo de toda la clase descrita
en `iso/docs/fixtures.md` §4.

> Dato de método que salió del mismo lote: Fermín tuvo que **reiniciar Maestro** para que cada
> opción tomara efecto ⇒ **son opciones que se leen al arrancar la aplicación**, no en cada
> postproceso. Toca directamente la pregunta E2 (separar «default al crear» de «lectura al
> postprocesar»), y **agranda el riesgo del negativo sin testigo**: si el reinicio se saltea,
> el fixture sale idéntico al base por una razón que no es la que se quería medir.
