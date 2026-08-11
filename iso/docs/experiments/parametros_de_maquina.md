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

## Resultados

(a la espera de los fixtures)
