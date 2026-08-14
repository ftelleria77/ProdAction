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

> ⚠️ **El XConverter NO produce ISO.** Dato de Fermín (2026-08-10), **verificado contra
> la ayuda de la propia herramienta**: tiene **doce** modalidades de trabajo y ninguna
> emite `.iso`. Convierte entre formatos de entrada de Maestro (`.xcs`, `.xxl`, `.pgm`,
> `.csv` → `.pgmx`/`.mixx`), importa, optimiza y prepara chapado. **El `.iso` lo produce
> únicamente el postprocesador de Maestro.** Lo único aprovechable de acá es la **forma**
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

La ayuda de la propia herramienta (captura de Fermín, 2026-08-10, en el repo Nora:
`skills/cnc-scm-maestro/references/pantallas/xconverter-ayuda-linea-de-comando-20260810.png`)
da la sintaxis completa:

```
XConverter -s -i FILES [-t FILE] [-e FILE] [-o FILES] [-m N] [-r]
```

| Flag | Qué es |
|---|---|
| `-s` | sin interfaz gráfica. **«Por el momento es la única modalidad de trabajo soportada»** |
| `-i` | ficheros de entrada (lista) |
| `-t` | fichero de **herramientas** (`def.tlgx`) |
| `-e` | fichero de **cantos** (el `.edgx` de `EdgxDir`) |
| `-o` | ficheros de salida. **Si se omite, convierte igual**: un solo producto se llama `Output`; varios, el nombre de cada entrada con sufijo `_Output` |
| `-m N` | modalidad de trabajo (ver tabla). **Si no se especifica, usa `-m 1`** |
| `-c` | configuración a escribir en las opciones de Maestro. **Sólo se interpreta en `-m 9`** |
| `-r` | aparece en la sintaxis y **no está explicado** en la ayuda |

### Las doce modalidades — **ninguna produce `.iso`**

| `-m` | Qué hace |
|---|---|
| 0 | **`.xcs` → `.pgmx`** (con el fichero de herramientas indicado) |
| 1 | **Importación piezas**: crea **UN** `.pgmx` con todas las piezas de los `.pgmx` de entrada. A las variables duplicadas les pone `variable` + índice incremental |
| 2 | **Optimización**: los `.pgmx` de entrada se optimizan «con la optimización del recorrido herramienta habilitada» |
| 3 | Todas las anteriores juntas: `.xcs` → `.pgmx` → importados en uno solo → optimizado (los intermedios van a una carpeta temporal que se borra) |
| 4 | `.xxl` → `.pgmx` |
| 5 | **`.pgm` → `.pgmx`** |
| 6 | Optimización de `.xxl` para chapado |
| 7 | Simulación de `.xxl` para chapado (emite un `.txt` con posibles choques) |
| 8 | Generación de trayectoria de chapado y trabajos accesorios (refilado, retestado, raspado) |
| 9 | **Cambio de configuración**: «la configuración de la máquina predefinida indicada en las opciones de Maestro se sustituye por la especificada en la línea de comando» (con `-c`) |
| 10 | `.pgmx` → `.xxl` |
| 11 | Proyecto `.mixx` a partir de una lista `.csv` |

Como **referencia de interfaz** —no como herramienta a invocar— la forma sirve de espejo
para la app de conversión por lotes: *N* entradas y *N* salidas pareadas en una sola
llamada, el catálogo como parámetro explícito, un default sensato cuando no se nombran las
salidas, y escritura directa dentro del proyecto. **La función es otra**: el XConverter
alimenta a Maestro, no lo reemplaza.

### Qué nos enseña (aunque no lo usemos)

> **No vamos a usar el XConverter** (decisión de Fermín, 2026-08-10). Está acá porque
> hay que conocerlo: explica **de dónde salen** ciertos `.pgmx` del taller y **con qué
> forma llegan**. Nada de lo de abajo es una herramienta de nuestro flujo.

- **`-m 2` (optimización)** — reordena el recorrido de herramienta y **guarda el resultado
  en el `.pgmx`**. Si un archivo pasó por acá, su orden de operaciones no lo dibujó nadie:
  lo decidió el optimizador. El converter lee lo que quedó escrito; saber que ese orden
  tiene autor evita buscarle una intención que no tiene.
- **`-m 1` (importación de piezas)** — produce `.pgmx` **multi-pieza**, con renombrado
  automático de variables duplicadas (`variable` + índice). Es una de las formas en que
  puede llegar un multi-pieza cuando ese workstream arranque.
- **`-m 9` (cambio de configuración)** — existe un mecanismo programático para sustituir
  la configuración de máquina de las Opciones de Maestro. Dato del ecosistema: **el tercer
  origen es escribible desde afuera de la UI**, así que un valor puede haber cambiado sin
  que nadie haya tocado una ventana. Ver `experiments/configuracion_aplicacion.md`.
- **`-m 5` (`.pgm` → `.pgmx`)** — existe el camino inverso, pero para **PGM**, que es el
  otro formato de salida de Maestro (`PostFileFormat`: XXL / PGM / ISO). **No hay
  equivalente para ISO** en ninguna dirección: por eso el converter no tiene con qué
  compararse ni de dónde copiar.

El ejecutable vive en la carpeta de Maestro: `XConverter.exe` (52 KB, **2013**), escrito en
.NET/WPF (`/XConverter;component/app.xaml`).

> ✅ **`Xconverter.exe.new` NO es un XConverter más nuevo** (resuelto 2026-08-14, ver
> pregunta 4). Los 449 KB del 2023 son un **lanzador hecho en el taller**: mensajes en
> castellano con erratas (`archvos`, `Comiezno`, `Finalziacion`), un `ShellExecute` de
> **`XXL2.bat`**, cronómetro del proceso y renombrado de originales a `.old`. El formato de
> hora `hh:nn:ss:zzz` es de Delphi, no de .NET. Y el `XConvert.exe` que invocan los
> `_nuevo.bat` **no existe** en la carpeta: quedó sólo su `.config`. No hay ningún cambio de
> versión del conversor esperando a entrar.

**Un detalle de nomenclatura que conviene tener escrito**: los lotes se llaman **`XXL2.bat`**
pero la modalidad que invocan es `-m 0`, que lee **`.xcs`** — no `.xxl`. En los directorios de
trabajo hay 326 `.xcs` y **cero** `.xxl`. El nombre quedó de cuando X-CAB emitía XXL; el paso
se sigue llamando así en el taller aunque el archivo ya no lo sea.

Pista abierta, sin confirmar: dentro de `XConverter.exe` la cadena `\temp.xxl` está pegada a
las del progreso de la conversión (`Start Esporta` · `Carica Configurazione macchina` ·
`Crea xcs file` · `Fine Genera pgmx`), lo que sugiere que el camino `.xcs` → `.pgmx` arma un
**XXL temporal** por dentro. Contigüidad no es prueba.

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

**Todas DIFERIDAS hasta terminar la reinvestigación** (decisión de Fermín, 2026-08-10).
El orden del método manda: primero se cierra la serie R desde el programa vacío; el
origen X-CAB se estudia después, con la anatomía del ISO ya derivada. Este doc queda
como el registro de lo que hay que retomar, no como un frente activo.

1. ~~¿El flujo sigue en uso?~~ **RESPONDIDA (2026-08-10): X-CAB SÍ** (326 `.xcs`, último
   lote el 2026-07-10); **EasyNest parece dormido** (58 `.xcs`, último 2024-03-25).
   ⇒ Los `.pgmx` de X-CAB **son alcance del converter**.
2. ⏳ ¿El `.pgmx` que emite el XConverter serializa de una **tercera** forma, distinta de
   la de Maestro y de la nuestra? Se responde abriendo uno de los que salieron a
   `S:\Maestro\Projects\BM-3C-PC-800\`.
3. ⏳ ¿Un `.pgmx` de X-CAB abierto y re-guardado en Maestro cambia de forma? (Si el
   operario los toca antes de postprocesar, el converter ve la forma re-guardada, no la
   original.)
4. ~~¿`Xconverter.exe.new` (2023) reemplaza al `XConverter.exe` (2013) en algún momento?~~
   **RESPONDIDA (2026-08-14): NO.** No es un XConverter: es un lanzador Delphi hecho en el
   taller que corre `XXL2.bat` y renombra archivos. Su binario objetivo (`XConvert.exe`) ni
   siquiera está instalado. Detalle arriba.
5. ⏳ ¿Hay otros orígenes que todavía no estén en esta lista?

## Por qué importa

Un converter validado sólo contra `.pgmx` de dos orígenes tiene un punto ciego del
tamaño del tercero. Es el mismo patrón que la regla 5 del `CLAUDE.md` advierte para los
fixtures: *preguntate qué no puede contener tu corpus por venir de tu propia autoría.*
