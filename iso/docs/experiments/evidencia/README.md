# Evidencia versionada de experimentos

Los fixtures de la reinvestigación viven fuera del repo, por la convención de
`iso/paths.py`: los `.pgmx` en `S:\Maestro\Projects\ProdAction\…` y los `.iso` en
`P:\USBMIX\ProdAction\…`, en rutas simétricas.

**Esta carpeta es la excepción**: acá se copian los archivos de un experimento **cuando el
paso siguiente los va a sobreescribir**. Sin esto, «lo comparamos volviendo un commit
atrás» no funciona — nunca estuvieron versionados y no hay a qué volver.

Criterio para copiar algo acá:

- el archivo se va a **pisar** en el paso siguiente del experimento, y
- su contenido es la evidencia de un hallazgo ya documentado.

No es un espejo de `S:` ni de `P:`: sólo lo que está por perderse. Las capturas se guardan
convertidas a `.png` (los `.bmp` de la PC del CNC pesan ~4 MB y comprimen a ~140 KB sin
perder legibilidad).

## Contenido

### `opciones_dsdmt_25/`

Fixture del barrido de la ventana Opciones (`experiments/opciones_de_aplicacion.md`):
«Distancia de seguridad desde la mesa de trabajo» = 25, contra el 20 del CNC.

| Archivo | Qué es |
|---|---|
| `R_PV_manual_base_DSDMT_25.pgmx` | el programa; **byte-idéntico al base** en su XML |
| `r_pv_manual_base_dsdmt_25.iso` | su ISO; difiere del base **sólo en la línea 1** |
| `r_pv_manual_base_dsdmt_25.png` | la ventana Opciones del CNC con la opción alterada |

Se versionó porque el paso siguiente —reabrir y volver a guardar **sin renombrar**, para
ver si el nombre interno del ZIP se unifica— sobreescribía los tres.

**El `.pgmx` de esta carpeta es el de DESPUÉS del reguardado.** La versión previa (con el
miembro llamándose `R_PV_manual_base_.xml`) está en el commit `f5febc4`:

```
git show f5febc4:iso/docs/experiments/evidencia/opciones_dsdmt_25/R_PV_manual_base_DSDMT_25.pgmx
```

### `paso0_oficina_tecnica/`

El paso 0 de la serie R_OPC: el programa base postprocesado en la **PC de oficina técnica**,
sin tocar ninguna opción. **No produjo `.iso`** — produjo los tres archivos de la etapa
intermedia, que es justamente el hallazgo (ver `emisor_iso.md`).

| Archivo | Qué es |
|---|---|
| `R_PV_manual_base_Of_Tec.xxl` | el programa en XXL, **texto legible**: el paso del medio |
| `R_PV_manual_base_Of_Tec.pgm` | el mismo, compilado a binario |
| `R_PV_manual_base_Of_Tec.inf` | log del compilador: `[LINES]=16`, `[ERRORS]=0` |

Se versionaron porque el próximo intento en esa PC los sobreescribe, y porque el `.xxl` es
la única muestra que tenemos de la etapa intermedia.

### `opciones_prf_15/`

«Paso de retroacción en los fresados» = 15, contra el 10 del CNC
(`MillingRetractDistance`). Mismo resultado que el anterior: XML byte-idéntico al base,
ISO distinto sólo en la línea 1.
