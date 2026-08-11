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
| **Idioma → «Unidad de medida»** (Milímetros / Pulgadas) | `IsMM` | `*MM` → `*IN` y **todas** las medidas del esqueleto |

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
| Velocidad rápida en los desplazamientos | `RapidFeed` | — | — | — |

Tres de cuatro dan lo mismo. La familia entera gobierna **trazas**, así que su lugar de
prueba es un programa con mecanizado, no éste.

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
