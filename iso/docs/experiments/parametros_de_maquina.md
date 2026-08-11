# Parámetros de máquina — barrido controlado (serie R_PM)

**Método propuesto por Fermín (2026-08-10).** Los cuatro parámetros de la ventana
`Máquinas → Parámetros → Parámetros de máquina` (más el checkbox de compatibilidad
tecnológica) no los expone nuestro sintetizador, así que los fixtures los hace Fermín
a mano: abre el archivo base, cambia **un** parámetro y guarda con otro nombre.

**Ampliación del método**: la sospecha no es sólo que estos parámetros muevan líneas del
esqueleto, sino que **cambien el comportamiento de los mecanizados**. Por eso el barrido
no se hace una vez y se archiva: **se repite sobre cada mecanizado básico** a medida que
los vayamos estudiando. Deja de ser un lote y pasa a ser una rutina de etapa.

## Punto de partida

`S:\Maestro\Projects\ProdAction\Programas Manuales\Reinvestigación\R_PV_manual_base.pgmx`
— autoría 100% Maestro, 400×400×18, origen 0/0/0, área HG, sin operaciones. Su ISO ya
está derivado línea por línea en `anatomia_iso.md`, así que **cualquier diferencia que
aparezca es del parámetro que se tocó.**

## Reglas del barrido

1. **Un parámetro por archivo.** Si un archivo cambia dos cosas y el ISO cambia en tres
   líneas, no se sabe cuál causó qué.
2. **Guardar como**, partiendo siempre del base sin modificar. Así el nombre interno de
   la pieza queda en `R_PV_manual_base` y sólo cambia el nombre del archivo — que es lo
   único que mueve la línea 1 del ISO.
3. **Si Maestro rechaza un valor, anotar el mensaje exacto.** El manual declara que
   `V=11` es «no admitido»; saber qué más rechaza dice qué combinaciones existen.
4. **Si un parámetro no cambia NADA en el ISO, es un resultado**, no un fracaso: significa
   que ese parámetro no viaja al postprocesado, y eso también hay que saberlo.

## Nombres

`R_PM_<parametro>_<valor>.pgmx` — `PM` por «parámetros de máquina». Genérico, sin nombres
de proyectos ni de fixtures (regla de nomenclatura de la época).

## Lista de variaciones

### Repeticiones (`Repetitions` · campo `R` del header)

En el base vale `1` y **el header no emite la letra `R`**. Interesa ver si aparece.

| Archivo | Qué cambiar |
|---|---|
| `R_PM_repeticiones_2.pgmx` | Repeticiones = 2 |
| `R_PM_repeticiones_10.pgmx` | Repeticiones = 10 |

### Bloqueo (`TableOptions` · campo `V`)

En el base vale `0`. El manual (§5.1 y §9.3) da una tabla de ~25 valores; estos cubren
las tres familias de dispositivo y los tres modos.

| Archivo | Qué cambiar | Qué dice el manual de ese valor |
|---|---|---|
| `R_PM_bloqueo_10.pgmx` | Bloqueo = 10 | ventosas, bloqueo manual |
| `R_PM_bloqueo_12.pgmx` | Bloqueo = 12 | ventosas, semiautomático |
| `R_PM_bloqueo_20.pgmx` | Bloqueo = 20 | bornes estándar, manual |
| `R_PM_bloqueo_21.pgmx` | Bloqueo = 21 | bornes estándar, automático |
| `R_PM_bloqueo_50.pgmx` | Bloqueo = 50 | «Default: depende del sistema configurado con Xilog3.cfg» |
| `R_PM_bloqueo_predefinido.pgmx` | dejar Bloqueo en 0 y **marcar el checkbox «predefinido»** | (es `UseDefaultForTableOptions`, que en el `.pgmx` va aparte) |
| `R_PM_bloqueo_11.pgmx` | Bloqueo = 11 | el manual lo declara **NO ADMITIDO** — se espera un error; anotar el mensaje |

### Opciones mecánicas (`MechanicalOptions` · campo `T`)

En el base vale `0`. Interesa sobre todo **si el número agrega las sub-opciones como
bitmask**, que es la hipótesis anotada y sin verificar.

| Archivo | Qué cambiar |
|---|---|
| `R_PM_mecanicas_laser.pgmx` | sólo `Láser` = Sí (el resto intacto) |
| `R_PM_mecanicas_elevadores.pgmx` | sólo `Elevadores` = Sí |
| `R_PM_mecanicas_laser_elevadores.pgmx` | `Láser` = Sí **y** `Elevadores` = Sí |
| `R_PM_mecanicas_barra_movil.pgmx` | sólo `Barra móvil` (si el desplegable lo permite) |
| `R_PM_mecanicas_topes_fila1.pgmx` | sólo `Fila 1 de topes` = Sí |
| `R_PM_mecanicas_areas_combinadas.pgmx` | sólo `Áreas combinadas` = Sí |

> Los tres primeros son los que responden el bitmask: si `Láser`→`T=10`,
> `Elevadores`→`T=1` y los dos juntos→`T=11`, el número agrega. La tabla del manual para
> `T` es `0/1/10/11/100/101/110/111` (láser × elevadores × TV Bar).

### Compatibilidad tecnológica en áreas especulares (`IsTechnologicalMirror`)

No aparece en el header. Interesa saber **si deja algún rastro en el ISO**.

| Archivo | Qué cambiar |
|---|---|
| `R_PM_espejo_tecnologico.pgmx` | marcar el checkbox |

### Área

Ya barrida en el lote **R002** (11 fixtures). No hace falta repetirla acá.

## Dónde guardarlos

Mismo criterio que el gemelo manual:
`S:\Maestro\Projects\ProdAction\Programas Manuales\Reinvestigación\`
y postprocesar a `P:\USBMIX\ProdAction\Programas Manuales\Reinvestigación\`.

## Cómo se procesan

`iso/machining_lab/comparar_variantes.py` toma una carpeta de ISOs y un archivo de
referencia, y saca el diff de cada uno contra la referencia mostrando **sólo** las líneas
que cambian. Con un parámetro por archivo, esa lista de líneas ES la respuesta.

```
py -m iso.machining_lab.comparar_variantes "P:\USBMIX\ProdAction\Programas Manuales\Reinvestigación" r_pv_manual_base.iso
```

## Resultados — 29 fixtures manuales de Fermín (2026-08-10)

Fermín barrió bastante más de lo que pedía la lista: las nueve combinaciones de bloqueo
(tres familias de dispositivo × tres modos), las quince sub-opciones mecánicas y el
espejo tecnológico. Postprocesó 28; uno dio error.

Carpetas: `S:\…\Programas Manuales\Reinvestigación\Parámetros de Máquina\` y su simétrica
en `P:`. Referencia: el ISO del gemelo manual.

**Todas las diferencias, sin excepción, están en la línea del header `;H`.** Ninguna
tocó el resto del esqueleto.

### Grupo 1 — llegan al ISO (16 fixtures)

**Mueven el campo `V`** (los que tocan «Bloqueo»):

| Opción de la UI | `TableOptions` en el `.pgmx` | `V` en el ISO |
|---|---|---|
| Vacuostatos, manual | 10 | **2** |
| Vacuostatos, automático | 11 | **2** |
| Vacuostatos, semiautomático | 12 | **2** |
| Presostatos, manual | 20 | **1** |
| Presostatos, automático | 21 | **1** |
| Presostatos, semiautomático | 22 | **1** |
| Vacuostatos + presostatos | 30 | **3** |
| Vac. + pres., automático | 31 | **3** |
| Vac. + pres., manual | 30 | **3** |
| Equipamiento | 40 | **4** |
| Bornes, manual | 60 | **10** |
| Bornes, automático | 61 | **10** |
| Bornes, semiautomático | 62 | **10** |
| checkbox «predefinido» | 0 (+ `UseDefaultForTableOptions=true`) | **9** |

**Mueven el campo `T`** (los que tocan «Opciones mecánicas»):

| Opción | `MechanicalOptions` | `T` en el ISO |
|---|---|---|
| Elevadores | 1 | **1** |
| Láser | 10 | **10** |

### Grupo 2 — NO llegan al ISO (12 fixtures)

El ISO sale idéntico al base salvo el nombre del archivo. `T` queda en `0`.

| Opción | `MechanicalOptions` | potencia de 2 |
|---|---|---|
| Fila 1 de topes | 65 536 | 2¹⁶ |
| Fila 2 de topes | 131 072 | 2¹⁷ |
| Fila 3 de topes | 262 144 | 2¹⁸ |
| Fila 4 de topes | 524 288 | 2¹⁹ |
| Fila 5 de topes | 1 048 576 | 2²⁰ |
| Áreas combinadas | 16 777 216 | 2²⁴ |
| Controlar posición de las ventosas | 33 554 432 | 2²⁵ |
| Deshabilita C.U. enmascarado | 67 108 864 | 2²⁶ |
| Adquisición BZ y DZ de palpadura | 134 217 728 | 2²⁷ |
| Habilitación vacío suplementario | 8 589 934 592 | 2³³ |
| Preparado para FX | 34 359 738 368 | 2³⁵ |
| **Compatibilidad tecnológica** (`IsTechnologicalMirror=true`) | — | — |

### Grupo 3 — no se pudo postprocesar (1 fixture)

**`Preparado para Combiflex`** (`MechanicalOptions = 17 179 869 184` = 2³⁴). El
postprocesador aborta:

```
Winxiso
[16,133] - xMETADb: (Línea 1) Área de trabajo inválida
```

Captura: `R_PV_manual_base_Combiflex.bmp`, en la carpeta de los ISO. El error es de
**Winxiso** (el postprocesador), no de Maestro al abrir: el `.pgmx` se abre bien. Y la
línea que declara inválida es la 1, donde está el área — con el área en `HG`, la misma
que funciona en los otros 28.

### Observaciones para estudiar juntos

Estas son cosas que la tabla muestra, no interpretaciones de qué significan:

1. **El valor del `.pgmx` y el del ISO no son el mismo número.** `TableOptions=60` sale
   como `V=10`; `20` sale como `1`; `10` sale como `2`. Hay una traducción en el medio.
2. **El modo (manual / automático / semiautomático) no sobrevive al ISO.** Los tres
   valores de cada familia —60/61/62, 20/21/22, 10/11/12— dan el **mismo** `V`. Lo que
   llega es la familia de dispositivo, no el modo.
3. **Los valores del `.pgmx` que no llegan al ISO son potencias de 2**, de 2¹⁶ para
   arriba. Los dos que sí llegan (elevadores = 1, láser = 10) coinciden exactamente con
   la tabla decimal del campo `T` del manual (`0/1/10/11/100/101/110/111`).
4. **El espejo tecnológico no deja ningún rastro** en el ISO.
5. El manual declara `V=11` como «no admitido», pero acá `TableOptions=11` (vacuostatos
   automático) **se postprocesó sin problema** y salió como `V=2`. Los números del `.pgmx`
   y los del manual del header no están en la misma escala.
6. El único que rompe el postproceso es Combiflex, y el mensaje habla del **área**, no de
   la opción mecánica.
