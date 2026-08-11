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

## Resultados

(a la espera de los fixtures)
