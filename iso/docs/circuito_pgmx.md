# De dónde vienen los `.pgmx` — el circuito real

**Documento vivo.** El converter no convierte «archivos de Maestro»: convierte los
`.pgmx` que existen en este taller, y no todos nacen igual. Este doc registra cada
origen, porque **cada uno puede escribir el XML a su manera** y el converter tiene que
aceptarlos a todos (o rechazarlos fail-loud, nunca convertirlos mal en silencio).

> **Nada en el circuito produce `.iso` salvo el postprocesador de Maestro.** Todas las
> herramientas de acá abajo terminan en un `.pgmx`; ninguna llega al `.iso`. Ese hueco
> es exactamente el que viene a llenar el converter.

## Los orígenes

| # | Origen | Cómo nace | Estado |
|---|---|---|---|
| 1 | **Maestro, a mano** | Fermín dibuja en el Editor y guarda | vigente |
| 2 | **Nuestro sintetizador** (`pgmx/synthesis`) | fixtures de la serie R | vigente (sólo investigación) |
| 3 | **X-CAB → XConverter** | X-CAB emite `.xcs` (scripting) y el XConverter lo convierte a `.pgmx` | **VIVO** (último lote 2026-07-10) |
| 3b | **EasyNest → XConverter** | ídem, por el camino del nesting | dormido (último 2024-03-25) |

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

**Dónde vive** (corrección de Fermín, 2026-08-10: son rutas **locales**; la unidad `X:`
es una copia **no funcional**, no mirar ahí):

```
C:\SPAI\X-CAB\PP\MSLPGMX\        el postprocesador de X-CAB — EN USO
C:\SPAI\X-CAB\PP\MSLPGMX\Tmp\    326 .xcs + los .bat de lote (último 2026-07-10)
C:\SPAI\EASYNEST\PP\MSLPGMX\     el de EasyNest (nesting) — 58 .xcs, último 2024-03-25
```

Los dos directorios traen el mismo juego de binarios (`pp.dll`, `GEA.dll`,
`Geniout32.dll`, `EditTools.exe`, `TTF16.ocx`, `SpreadsheetGear.dll`) y tres `.ini`:

- **`xconverter.ini`** — la instalación de Maestro, el `def.tlgx` a usar y dos flags.
  **Los dos no apuntan al mismo catálogo**:

  | | Maestro | `def.tlgx` | flags |
  |---|---|---|---|
  | X-CAB | `C:\Program Files (x86)\SCM Group\Maestro` | **`S:\Maestro\Tlgx\def.tlgx`** (el de red) | `0`, `0` |
  | EasyNest | ídem | `…\Maestro\Tlgx\def.tlgx` (el local) | `0`, `1` |

- **`PPMode.ini`** — `ExportCreateIsoCenterMilling=0`, `ToolFormat=0`, `Feeler=0`.
- **`cfg.ini`** — `ToolsNumCol=4`.

### El XConverter es una CLI que convierte entre formatos de ENTRADA

> ⚠️ **El XConverter NO produce ISO.** Tiene varios modos de conversión y **ninguno**
> emite `.iso` (dato de Fermín, 2026-08-10). Convierte archivos de un formato de entrada
> a otro —`.xcs` → `.pgmx`, `.csv` → `.mixx`— y ahí termina su trabajo. **El `.iso` lo
> produce únicamente el postprocesador de Maestro.** No hay nada en el circuito que haga
> lo que tiene que hacer nuestro converter; lo único aprovechable de acá es la **forma**
> de la CLI, no su función.

Los `.bat` que quedan en `Tmp\` muestran cómo se lo invoca:

```bat
chcp 850
"C:\Program Files (x86)\SCM Group\Maestro\Xconverter.exe" -s -m 0 ^
-i "C:\SPAI\X-CAB\PP\MSLPGMX\Tmp\Lateral_IzqN1.xcs" ^
-i "…\TapaN1.xcs" ^                       (24 entradas en el lote real)
-o "S:\Maestro\Projects\BM-3C-PC-800\Lateral_IzqN1.pgmx" ^
-o "S:\Maestro\Projects\BM-3C-PC-800\TapaN1.pgmx" ^
-t "S:\Maestro\Tlgx\def.tlgx"
```

| Flag | Qué es |
|---|---|
| `-s` | silencioso (sin UI) |
| `-m` | modo de conversión. Vistos en los `.bat`: `0` = `.xcs` → `.pgmx` · `11` = `.csv` → `.mixx`. **Hay más modos; ninguno produce `.iso`.** |
| `-i` | entrada, **repetible** |
| `-o` | salida, **repetible**, pareada por orden con las `-i` |
| `-t` | catálogo de herramientas (`def.tlgx`) |

De acá se puede tomar **la forma de invocación**, que es la que va a necesitar la app de
conversión por lotes: *N* entradas y *N* salidas pareadas en una sola llamada, el catálogo
como parámetro explícito, y la escritura directa dentro del proyecto
(`S:\Maestro\Projects\<proyecto>\`). **La función es otra**: el XConverter alimenta a
Maestro, no lo reemplaza.

El ejecutable vive en la carpeta de Maestro: `XConverter.exe` (52 KB, **2013**). Al lado
hay un **`Xconverter.exe.new`** (449 KB, 2023) que **no está en uso** — una versión más
nueva sin activar. Anotarlo antes de sacar conclusiones sobre el comportamiento del
conversor: puede que la que corre no sea la última.

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

- **X-CAB emite piezas de mueble, una por archivo.** Los nombres del último lote lo
  dicen: `Lateral_Izq`, `Lateral_Der`, `Tapa`, `Fondo`, `Trasera`, `Faja frontal`,
  `Fren_Cajon_Sup`, `Tras_Cajon_Inf`… Salen a
  `S:\Maestro\Projects\<proyecto>\<pieza>.pgmx`.
- El sufijo `F6` de algunos archivos (`FondoN1F6.xcs`, `Lat_Izq_Cajon_SupN0F6.xcs`)
  aparea con el campo `f6_source` que la app ya maneja por pieza — **son la segunda cara**
  (el `.pgmx` de la vuelta), no una variante.
- **EasyNest** es el camino del nesting: placas enteras (2600×1500×18) con
  `SetWorkpieceSetupPosition(…, 9.000, …)` — origen Z a media placa.
- `SetMachiningParameters("A", …)` fija el **área "A"**, no `HG`: los `.pgmx` de esta
  fuente traen otro campo de ejecución que los que venimos mirando.
- El XConverter corre contra la instalación de Maestro de **64 bits** de esta PC — no la
  del CNC (XP 32 bits). Con su propio `UI00.exe.Config`, que es un origen más de
  configuración en el circuito. Ver `experiments/configuracion_aplicacion.md`.

## Preguntas abiertas

1. ~~¿El flujo sigue en uso?~~ **RESPONDIDA (2026-08-10): X-CAB SÍ** (326 `.xcs`, último
   lote el 2026-07-10); **EasyNest parece dormido** (58 `.xcs`, último 2024-03-25).
   ⇒ Los `.pgmx` de X-CAB **son alcance del converter**.
2. ¿El `.pgmx` que emite el XConverter serializa de una **tercera** forma, distinta de
   la de Maestro y de la nuestra? Se responde abriendo uno de los que salieron a
   `S:\Maestro\Projects\BM-3C-PC-800\`.
3. ¿Un `.pgmx` de X-CAB abierto y re-guardado en Maestro cambia de forma? (Si el operario
   los toca antes de postprocesar, el converter ve la forma re-guardada, no la original.)
4. ¿`Xconverter.exe.new` (2023) reemplaza al `XConverter.exe` (2013) en algún momento?
   Un cambio de versión del emisor cambia lo que hay que reproducir.
5. ¿Hay otros orígenes que todavía no estén en esta lista?

## Por qué importa

Un converter validado sólo contra `.pgmx` de dos orígenes tiene un punto ciego del
tamaño del tercero. Es el mismo patrón que la regla 5 del `CLAUDE.md` advierte para los
fixtures: *preguntate qué no puede contener tu corpus por venir de tu propia autoría.*
