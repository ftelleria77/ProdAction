# De dónde vienen los `.pgmx` — el circuito real

**Documento vivo.** El converter no convierte «archivos de Maestro»: convierte los
`.pgmx` que existen en este taller, y no todos nacen igual. Este doc registra cada
origen, porque **cada uno puede escribir el XML a su manera** y el converter tiene que
aceptarlos a todos (o rechazarlos fail-loud, nunca convertirlos mal en silencio).

## Los orígenes

| # | Origen | Cómo nace | Estado |
|---|---|---|---|
| 1 | **Maestro, a mano** | Fermín dibuja en el Editor y guarda | vigente |
| 2 | **Nuestro sintetizador** (`pgmx/synthesis`) | fixtures de la serie R | vigente (sólo investigación) |
| 3 | **X-CAB → XConverter** | X-CAB/EasyNest emite `.xcs` (scripting) y el XConverter lo convierte a `.pgmx` | **a confirmar si sigue en uso** |

### 1. Maestro a mano

El caso de referencia. Serializa con el namespace por defecto repetido en cada elemento
(97 declaraciones `xmlns` en un programa vacío).

### 2. Nuestro sintetizador

Mismo documento, distinta escritura: usa prefijos declarados una vez (20 declaraciones).
**Verificado el 2026-08-10** contra un gemelo manual: mismos tags, mismas cantidades,
mismos valores; sólo cambia el estilo. Ver `experiments/programa_vacio.md`.

### 3. X-CAB → `.xcs` → XConverter → `.pgmx`

Dato de Fermín (2026-08-10). **X-CAB** (de SPAI, el mismo software cuyos módulos
`.vts_cab` interpreta el proyecto X-CAB Interpreter) genera archivos **`.xcs`** escritos
en **Xilog Maestro Scripting Language (MSL)**, y una herramienta llamada **XConverter**
los convierte a `.pgmx`.

**Dónde vive** (unidad `X:`, el share de X-CAB):

```
X:\EASYNEST\PP\MSLPGMX\          el conversor: pp.dll, GEA.dll, Geniout32.dll,
                                 EditTools.exe, TTF16.ocx, SpreadsheetGear.dll
X:\EASYNEST\PP\MSLPGMX\Tmp\      ~140 archivos .xcs (los generados)
X:\EASYNEST\Job\                 los .pgmx resultantes
```

Su configuración son tres `.ini` chicos:

- **`xconverter.ini`** — cuatro líneas: la carpeta de Maestro
  (`C:\Program Files (x86)\SCM Group\Maestro`), la ruta del `def.tlgx` que usa, y dos
  flags (`0`, `1`).
- **`PPMode.ini`** — `ExportCreateIsoCenterMilling=0`, `ToolFormat=0`, `Feeler=0`.
- **`cfg.ini`** — `ToolsNumCol=4`.

**Qué es un `.xcs`**: código MSL plano, una llamada por línea, del mismo lenguaje que
documenta `pgmx/docs/maestro_scripting/`. Ejemplo real (`Tmp\test1.xcs`, placa de
nesting de 2600×1500×18):

```
SetMachiningParameters("A",1,0,0,false);
CreateFinishedWorkpieceBox("test1",2600.000, 1500.000, 18.000);
SetWorkpieceSetupPosition(0.000,0.000,9.000,0);
SelectWorkplane("Top");
CreateDrill("XBO_1",492, 148, 12, 5,"XBO_1", TypeOfProcess.Drilling, "-1","-1",0, -1, -1, "P", 0);
…
SetApproachStrategy(true,false,2.000);
SetRetractStrategy(true,false,2.000,0);
CreatePolyline("GEO_1", 50.000, 359.000);
AddSegmentToPolyline(50.000,668.000);
…
CreateRoughFinish("LAV_1",18.100,"",TypeOfProcess.GeneralRouting,"E001","3",1,-1,-1,-1,0);
```

**Lo que ya se aprovechó de esto** (2026-08-10): la firma de `SetMachiningParameters`
en la doc de SCM dice a qué letra del header `;H` corresponde cada parámetro, y con eso
quedaron **derivadas** cuatro letras del header del ISO —`-`, `V`, `T`, `C`— que estaban
en hipótesis o en desconocido. Ver `experiments/anatomia_iso.md`.

**Observaciones sobre el flujo:**

- Es el camino del **nesting**: piezas del tamaño de la placa entera (2600×1500×18) y
  `SetWorkpieceSetupPosition(…, 9.000, …)` — origen Z a media placa.
- `SetMachiningParameters("A", …)` fija el **área "A"**, no `HG`. Un `.pgmx` de esta
  fuente trae otro campo de ejecución que los que venimos mirando.
- El XConverter apunta a **su propio `def.tlgx`** y a **su propia instalación de
  Maestro** (`C:\Program Files (x86)\…`, o sea 64 bits: no es la del CNC, que es XP 32
  bits). Es decir: **una cuarta instalación de Maestro en el circuito**, con su propio
  `UI00.exe.Config`. Ver `experiments/configuracion_aplicacion.md`.
- Los `.xcs` de `Tmp\` son de **2022** (abril a agosto). Eso no prueba que el flujo esté
  muerto —`Tmp` puede limpiarse—, pero tampoco que esté vivo.

## Preguntas abiertas

1. **¿El flujo X-CAB → XConverter sigue en uso?** Decide si sus `.pgmx` son alcance del
   converter o historia. Los `.xcs` que quedaron son de 2022.
2. Si está en uso: ¿esas piezas se postprocesan en la PC del CNC como todas las demás?
3. ¿El `.pgmx` que emite el XConverter tiene una forma propia de serializar (una tercera,
   además de la de Maestro y la nuestra)? Se responde abriendo uno de `X:\EASYNEST\Job\`.
4. ¿Hay otros orígenes que todavía no estén en esta lista?

## Por qué importa

Un converter validado sólo contra `.pgmx` de dos orígenes tiene un punto ciego del
tamaño del tercero. Es el mismo patrón que la regla 5 del `CLAUDE.md` advierte para los
fixtures: *preguntate qué no puede contener tu corpus por venir de tu propia autoría.*
