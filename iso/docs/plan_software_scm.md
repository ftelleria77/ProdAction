# Los dos programas de SCM: relevamiento y plan de investigación

**Documento vivo.** Qué son Maestro y Xilog Plus por dentro, qué se puede leer de cada uno, y
en qué orden conviene hacerlo. Motivado por Fermín (2026-08-30): los archivos de configuración
del CNC son la fuente, varios son **posicionales sin etiquetas**, y hasta ahora la única forma
de nombrarlos fue recorrer la UI.

> ⚠️ **Nada de esto reemplaza a los fixtures.** El byte-idéntico se valida contra lo que emite
> la máquina (regla 4). Los binarios dicen **qué puede pasar**; los fixtures, **qué pasa**. Lo
> que esta investigación aporta es el **mapa**: saber qué existe, para dejar de recorrer el
> territorio a ciegas y para poder decir qué NO cubrimos.

## 1. ⚠️ Primero, una corrección de procedencia

**`pgmx/data/tool_catalog.csv` lo armó Fermín con IA como resumen. NO es origen de datos.**
Y las derivaciones del perforado lo citaban como fuente: el `77`, el `65`, el `6000`.

**Re-ancladas el 2026-08-30 en `def.tlgx`**, que sí viene de la máquina — lo genera Maestro
importando el archivo de herramientas de Xilog Plus. Los doce registros coinciden sin mover un
número:

| | `def.tlgx` | el CSV |
|---|---|---|
| `ToolOffsetLength` | 77 verticales · 65 laterales · 60 sierra | idem |
| `Diameter`, `SinkingLength`, `PilotLength` | presentes | idem |
| `Maximum`/`Minimum`/`Standard` × 3 bloques | avance, penetración, rotación | idem |
| **`Description`** | **vacía en las doce** | **escrita a mano — y cruzada en 058/059** |

⇒ **El converter lee `def.tlgx`, no el CSV.** Y hay una ventaja: **`def.tlgx` viaja dentro de
cada `.pgmx`** (es uno de los tres miembros del ZIP), así que el catálogo de herramientas de un
programa siempre está a mano, sin depender del snapshot.

## 2. Los dos programas son de mundos distintos

| | **Maestro** | **Xilog Plus** |
|---|---|---|
| ubicación | `S:\Copia CNC\Maestro` (1.096 archivos) | `S:\Copia CNC\Xilog Plus` (1.880 archivos) |
| tecnología | **.NET gestionado**, ensamblados de 2013 | **nativo**, era VB6/C++, binarios de 2011 |
| pistas | 41 `ScmGroup.XCam.*.dll`, `.exe.config`, `.xml` de doc, `Ionic.Zip`, `CSScriptLibrary` | `.OCX`, `.tlb`, `Uninst.isu`, DLL **sin `FileVersion`** |
| qué se puede leer | **el esquema completo por reflexión** | tablas de cadenas, recursos, `.msg`, `.chm` |
| qué guarda | el modelo del `.pgmx` y de `def.tlgx` | **la configuración de la máquina**, sobre todo dimensiones |

**Esa asimetría ordena todo el plan**: en Maestro se puede preguntar por la estructura; en
Xilog Plus hay que leer lo que dejó escrito.

### Los 41 ensamblados de Maestro, y cómo mapean a nuestras ramas

```
MachiningDataModel  ToolDataModel  GeometryDataModel  ConfigDataModel  ProjectObjectModel
Post  XXLServices  PgmConverter  PgmXConverter  TlgConverter
DrillingOptimizer  Optimizer  Nesting  DXF  Sketcher  Scripting  WorkPlaneManager
GeometryService  Presentation  ControlsLibrary  CustomControls  XControl  XOM  Common …
```

Los nombres coinciden casi uno a uno con lo que venimos investigando: `MachiningDataModel` es
el `.pgmx`, `ToolDataModel` es `def.tlgx`, `Post` es el postproceso, `XXLServices` es la etapa 1,
**`DrillingOptimizer` es el botón Optimizador** del Grupo 8, y `PgmXConverter` es el XConverter
de la rama F.

## 3. Lo que YA se probó que funciona (2026-08-30)

### ✅ Reflexión sobre los ensamblados, sin instalar nada

No hay `dotnet` CLI ni decompilador en esta máquina, pero **está el .NET Framework 4.0** y con
eso alcanza. Desde PowerShell, con un resolvedor de dependencias apuntado a la carpeta de
Maestro:

```powershell
[System.AppDomain]::CurrentDomain.add_ReflectionOnlyAssemblyResolve($resolvedor)
$a = [System.Reflection.Assembly]::ReflectionOnlyLoadFrom($dll)
$a.GetTypes()      # con try/catch: ReflectionTypeLoadException.Types trae los que sí cargaron
```

Resultado de la prueba:

- `ToolDataModel` → **125 tipos**, con los mismos nombres que el XML de `def.tlgx`
  (`CuttingTool`, `XilogHolderDataTool`, `DrillingToolDimension`…).
- `MachiningDataModel` → **856 tipos**, y ya de entrada la lista completa de familias:
  - features: `ContourFeature`, `ReplicateFeature`, **`SawCutFeature`**, **`ScrapingFeature`**,
    **`TrimmingFeature`**, **`ChamferFeature`**, **`EdgeBandingFeature`**,
    **`SlantedProfileFeature`**, `ProfileFeature`, `ToolpathFeature`…
  - operations: `DrillingOperation`, **`FreeformOperation`**, **`Two5DMillingOperation`**,
    `MillingMachiningOperation`, **`ScrapingOperation`**, **`TrimmingOperation`**…

⇒ **De esas familias, la reinvestigación tocó tres.** Esa lista es el mapa que faltaba.

### ✅ El catálogo de mensajes de error de Xilog

Los rechazos que venimos capturando a mano uno por uno **están enumerados** en
`Xilog Plus\Country\Spa\*.msg`:

| lo que vimos en pantalla | dónde está |
|---|---|
| `[23,6] - Bag. IJ: Área de trabajo no configurada` | `Sys.msg` **@006** |
| `[6,8] - ChkPgm línea 21: Microinterruptor- de tope eje X (T= 7)` | `Sys.msg` **@008** |
| `Herramienta E82 no configurada` | misma familia |

Y el catálogo trae los hermanos que todavía no provocamos: `@009` microinterruptor **+** de X,
`@010`/`@011` los de Y, y cientos más en `Cyc.msg`, `cnc.msg`, `axis.msg`, `macro.msg`.

⇒ **El converter puede anticipar y nombrar los rechazos igual que la máquina**, sin tener que
provocar cada uno. Y el número entre corchetes es (módulo, `@NNN`).

## 4. El plan, por rendimiento decreciente

### Fase 1 — El esquema del `.pgmx`, por reflexión · ⭐ la que más rinde

Volcar de `MachiningDataModel`, `ToolDataModel`, `GeometryDataModel` y `ConfigDataModel`:
jerarquía de tipos, propiedades con su tipo, **enums con todos sus valores**, y los atributos
de `DataContract`/`DataMember` (orden de serialización, `IsRequired`, defaults).

**Producto**: un mapa `tipo → campos → valores posibles`, y su cruce contra lo que la
reinvestigación derivó. Dos columnas: *visto en fixtures* y *existe en el modelo*.

**Por qué rinde**: hoy cada campo del `.pgmx` se descubre por diferencia entre dos archivos. El
modelo los lista todos, incluidos los que **ningún fixture nuestro tiene** — que son
exactamente los puntos ciegos que la regla 5 del `CLAUDE.md` manda buscar.

⚠️ **Límite duro**: dice qué se puede *escribir*, **no** qué llega al ISO. Eso sigue siendo
trabajo de fixtures.

### Fase 2 — El catálogo de mensajes · barata y cerrada

Parsear los 20 `.msg` de `Country\Spa\` a una tabla `(archivo, @NNN, texto, parámetros)`.

**Producto**: la lista de rechazos posibles, con su código. Alimenta el fail-loud del converter
y explica los `[n,m]` de las capturas.

### ⚠️ Los `.chm` NO sirven para esto (Fermín, 2026-08-30)

La ayuda es **documentación genérica del fabricante**: puede decir cómo se llama un campo en
general, pero **no** que la posición 23 de *este* archivo sea ese campo. Y menos con las
dimensiones de herramientas, que **se miden y se vuelcan una por una en la puesta en marcha**.

⇒ Los `.chm` quedan como **generadores de hipótesis**, nunca como evidencia. Todo lo que salga
de ahí se valida por otra vía.

### ✅ Fase 3 (reemplazada) — El binario que LEE los `.cfg` · resuelto el 2026-08-30

Buscando el nombre de los archivos en las tablas de cadenas aparecieron **ocho binarios** que
los mencionan: `Bag32.dll`, **`Dbms32.dll`**, **`ExtCad32.dll`**, `Grph32.dll`, `Nci.dll`,
`PanelMac.exe`, `Parsifal.exe`, `Xiso32.dll`.

⭐ **`ExtCad32.dll` trae el esquema**: por cada `.cfg`, la lista de campos con su **etiqueta** y
su **clave de 5 caracteres**, terminada por un marcador `[FILE ]=<ARCHIVO>.CFG`. Están
`GENDATA.CFG`, `PHEADS.CFG`, `SPINDLES.CFG`, `STOREPOS.CFG`, `SUPPORTS.CFG` y más.

Para `SPINDLES.CFG`:

```
[SPINN] Spindle number (1-96 / 1-999)      [FREQT] Frequency converter T. (0=NONE)
[PLC  ] Plc enabling (1-96)                [OFFSD] Offset D
[TYPE ] Type (0=ND,1=P=flat,2=F=lance,…)   [ANGAB] Angle A/B
[SERIE] Series (1=X,2=Y)                   [OFFSX] Offset X
[FACE ] Working side                       [OFFSY] Offset Y
[HEAD ] Head                               [OFFSZ] Offset Z
[MOTOR] Motor number (0-4)                 [OFFSR] Offset R
[FREQC] Frequency converter (0=NONE)       [TIMET] Time taken (secs)
[DBLSP] Double spindle selection
[TMOTO] T. Motor number (0-4)
```

#### Y se valida contra los datos de la máquina, sin depender de la doc

| índice | campo | qué dice el archivo | validación independiente |
|---|---|---|---|
| 2 | `TYPE` | `1` en las doce | `1 = P = flat`, y las doce **son brocas planas** (la cónica es punta, no tipo) |
| 3 | `SERIE` | 2 en los husos 2·3·58·59 · 1 en 4·5·6·7·60·61 | ⭐ **los de serie Y son exactamente los que tienen `OFFSY≠0`**, y los de serie X los que tienen `OFFSX≠0`. 6 de 6 |
| 4 | `FACE` | vert.=1 · 60=**2** · 61=**3** · 58=**4** · 59=**5** | ⭐ el orden coincide con el desplegable `Referencias` de la ventana Taladrado: **superior · derecho · izquierdo · delantero · trasero · inferior** |
| 1 | `PLC` | 1–7 verticales · **31** en 58/59 · **32** en 60/61 | ⭐ `?%ETK[0] = 2^(PLC − 1)`, ya derivado de los ISO |
| 23·24·25 | `OFFSX/Y/Z` | | ⭐ `SHF = −OFFS`, 33 valores verificados contra los ISO |

⇒ **Tres fuentes independientes coinciden**: el binario que lee el archivo, los datos de la
máquina y la UI. Eso es validación de verdad, no lectura de manual.

#### ⭐⭐ Y explica la «inversión» de las brocas delantera y trasera

El huso **58** tiene `FACE=4` (delantera) y el **59** `FACE=5` (trasera) — y los fixtures usan
el 58 para la cara delantera y el 59 para la trasera. **Los husos no están invertidos: la
máquina es coherente.**

Lo que está cruzado es **qué herramienta está montada en qué huso**: la herramienta `058` vive
en el huso **59** (trasero) y la `059` en el huso **58** (delantero). Es un **dato de montaje**,
no un error del software — y el CSV lo escribió al revés porque supuso que el número de
herramienta seguía al del huso.

#### Y `?%ETK[0]` deja de ser una coincidencia numérica

`PLC` es «Plc enabling (1-96)» ⇒ **el bit del PLC que habilita ese huso**. Coherente con lo ya
derivado del manual de SCM: `EDK`/`ETK` son registros de intercambio CNC↔PLC. La fórmula
`2^(PLC−1)` no es un ajuste: es lo que el campo significa.

#### ✅ El mapa posicional COMPLETO de `spindles.cfg` (2026-08-30)

Las claves no están sueltas en el binario: son una **tabla contigua de paso fijo de 8 bytes**
(7 de la clave + terminador `00`), escrita **en orden inverso**, de `[TIMET]` en el offset
46448 hasta `[SPINN]` en el 46584. Esa tabla **es** el orden de los campos.

Y el registro del archivo son **42 líneas**: **21 enteros** (0–20), **20 flotantes** (21–40) y
la línea del nombre (41). Los 18 campos se reparten entre los dos bloques:

| idx | clave | etiqueta | huso 58 |
|---|---|---|---|
| 0 | `SPINN` | Spindle number | 58 |
| 1 | `PLC` | **Plc enabling (1-96)** | 31 |
| 2 | `TYPE` | Type (1=P=flat…) | 1 |
| 3 | `SERIE` | Series (1=X, 2=Y) | 2 |
| 4 | `FACE` | **Working side** | 4 |
| 5 | `HEAD` | Head | 1 |
| 6 | `MOTOR` | Motor number (0-4) | 1 |
| 7 | `FREQC` | Frequency converter | 1 |
| 8·9·10 | `DBLSP`·`TMOTO`·`FREQT` | doble husillo, motor T., convertidor T. | 0 |
| 11–20 | — | *(reserva)* | 0 |
| 21 | `OFFSD` | Offset D | 0.00 |
| 22 | `ANGAB` | Angle A/B | 0.00 |
| **23** | **`OFFSX`** | **Offset X** | −32.00 |
| **24** | **`OFFSY`** | **Offset Y** | 21.75 |
| **25** | **`OFFSZ`** | **Offset Z** | −66.50 |
| 26 | `OFFSR` | Offset R | 0.00 |
| **27** | **`TIMET`** | **Time taken (secs)** | **0.50** |
| 28–40 | — | *(reserva)* | 0.00 |

**Verificación sobre los 1.000 registros del archivo: ningún índice sin nombre tiene un valor
distinto de cero.** Las 18 claves cubren todo lo que la máquina usa.

⇒ Cae de una el `0.50` del índice 27, que aparecía en las cuatro brocas laterales y estaba en
DESCONOCIDO: es el **tiempo de la operación en segundos**.

⇒ Y `OFFSX/Y/Z` quedan en 23/24/25 **por el binario que lee el archivo**, no por analogía: es
la confirmación independiente de los 33 valores que ya se habían derivado de los ISO.

> 📌 **El decompilador no hizo falta para esto.** Alcanzó con la tabla de descriptores del
> binario más la validación contra los datos. Queda instalado igual, porque las preguntas que
> siguen (el `G4F1.200`, el `+1` del pecking, el criterio del Optimizador) son de **código**,
> no de layout.

#### Lo que este método NO alcanza a mapear

El descriptor lista **18 campos** y el registro del archivo tiene **29 valores** (14 enteros +
15 flotantes). Los índices **8–22 y 26–28** siguen sin nombre.

⇒ **Acá sí conviene el decompilador** (idea de Fermín): el código que lee el archivo recorre
los campos en orden, y eso cierra el mapeo entero. Candidatos por nombre: **`Dbms32.dll`** (el
gestor de datos) y `ExtCad32.dll`.

### Fase 3bis — Los `.chm`, sólo como vocabulario



Cinco archivos de ayuda **en español**: `Testine.chm` (cabezales), `Xilog_Plus_WinXiso.chm`,
`Xilog_Plus_Editor.chm`, `Xilog_Plus_Epl.chm`, `Xilog_Plus_PanelMac.chm`.

`Testine.chm` es el candidato directo a **nombrar los campos posicionales de `spindles.cfg` y
`pheads.cfg`** — hoy los conocemos por posición (23/24/25 = offsets X/Y/Z) y derivados contra
el ISO, no por su nombre.

Ya estaba pedido como F0.5 del `plan_cierre_converter.md`; acá queda con destinatario concreto.

### Fase 4 — Los binarios nativos de Xilog · el caso duro

Ya hay herramienta: `iso/machining_lab/buscar_en_binarios.py`, con **dos puntos ciegos
declarados** (las raíces están fijas en las dos instalaciones y el filtro toma sólo
`.dll`/`.exe`). Ampliarla a `Country\*.dll` (`Resource32.dll`, `Parsifal.dll`, `Epl.dll`), a
los `.OCX` y al `amcompat.tlb` — una *type library*, que es legible como estructura.

**Producto**: procedencia de lo que hoy queda en DESCONOCIDO — `?%ETK[17]=257`, el `G4F1.200`
del cierre, el `+1` del pecking.

### Fase 5 — El Optimizador

`ScmGroup.XCam.DrillingOptimizer.dll` son **62 KB** — el más chico y el más acotado. Reflexión
sobre sus tipos y sus cadenas.

**Se complementa con el Grupo 8 de fixtures**, que ya está pedido: el binario dice **qué
criterios** tiene; los fixtures, **qué emite**. Y entre los dos contestan la pregunta que abrió
Fermín — si la optimización se guarda en el `.pgmx` o es del postproceso.

## 5. Criterio de corte

Si la Fase 1 no entrega el esquema (ensamblados ofuscados, dependencias irresolubles) o la
Fase 3 no nombra los campos posicionales, **se vuelve a recorrer la UI de Xilog Plus ventana
por ventana**, como en las investigaciones previas a ésta.

Ese recorrido no es el plan B por ser peor: es **más caro** (necesita a Fermín frente a la
máquina) y por eso va después. Pero es el único que da **la etiqueta que el operario ve**, que
es la nomenclatura que manda (regla 3).

---

## 6. Herramientas instaladas y prueba de factibilidad (2026-08-30)

### El bloqueo era UAC, no la red

`winget install` quedó **75 minutos sin producir salida**. No era la red (github y pypi
responden, sin proxy): la sesión **no está elevada** (`TECNICA2ermi`, administrador: False),
así que el instalador dejó un **UAC esperando en la consola de la máquina** — invisible en
remoto e inalcanzable desde acá.

⇒ **Regla para adelante: sólo herramientas portables, sin instalador.** Cualquier cosa que pida
admin se va a colgar igual.

### Lo instalado, los dos portables en el perfil del usuario

| herramienta | ruta | para qué |
|---|---|---|
| **Rizin 0.9.1** | `%LOCALAPPDATA%
izin` | binarios nativos de Xilog Plus |
| **dnSpyEx 6.6.0** | `%LOCALAPPDATA%\dnspy` (`dnSpy.Console.exe`) | ensamblados .NET de Maestro |

⚠️ **Rizin no trae decompilador**: ni `pdg` (el plugin de Ghidra) ni `pdc`. Carga bien el PE32
(`arch x86 · bits 32`) y sirve como **desensamblador y lector de estructura**, no más.

### ⭐ Y al probarlo apareció que el objetivo era el otro

Las dos preguntas de código que quedaban **no son nativas, son .NET**:

1. **el `+1` del pecking** — el `.pgmx` guarda la trayectoria **ya expandida** (§5ter), o sea
   que el ciclo lo calcula **Maestro**;
2. **el criterio del Optimizador** — `ScmGroup.XCam.DrillingOptimizer.dll`.

El decompilador nativo era la herramienta equivocada para las dos.

### ✅ La prueba: `DrillingOptimizer.dll` decompilado

`dnSpy.Console.exe -o <salida> <dll>` produce **C# real**. Sobre los 62 KB del optimizador: 13
archivos, **10 con nombre legible**.

| | |
|---|---|
| ✅ legible | tipos públicos, campos, firmas de métodos, enums, valores por defecto |
| ⚠️ ofuscado | **252 identificadores** privados y nombres de parámetros (`#=q…`) |

⇒ **La superficie pública se lee como documentación; la lógica interna se lee, pero con nombres
sin sentido.** Alcanza para preguntas dirigidas; para seguir un algoritmo entero cuesta.

### ⭐⭐ Y ya contestó la pregunta del Optimizador

```csharp
class MultipleDrillingSolution {
    double XPos, YPos, ZRot;          // ⭐ rota la solución
    ulong  Pattern;                   // ⭐ máscara de husos — el ETK[0]
    List<Hole> HoleList;
    List<int>  SpindleIndexList;
}
class DrillingSpindle {
    List<int> LinkedSpindles;
    bool IsCompatibleHole(Hole h);
    bool IsCompatibleHolePosition(Hole h, double unitX, double unitY);
}
class HoleType { double Diameter, Depth; Type Type; }   // agrupa por los tres
class HoleGrid { Hole[,] HoleMask; double[] XCoord, YCoord; … }
class DrillingOptimizerOptions { bool MirrorX, MirrorY, CheckMultiPlane = true; double Precision; }
```

⇒ **El Optimizador SÍ hace perforación multi-huso.** Agrupa por **tipo de agujero** (diámetro +
profundidad + tipo) y por **posición compatible** con el paso de los husos, arma una **máscara
de husos** y puede **rotar** la solución.

⇒ Confirma la sospecha de Fermín, y explica por qué en el taller no le veían diferencia: **sin
optimizar, cada agujero es un movimiento** — la ganancia no está en la trayectoria sino en
cuántos husos bajan a la vez.

⚠️ Sigue haciendo falta el **Grupo 8 de fixtures**: el binario dice qué criterios tiene, pero
sólo el ISO dice qué emite — y sobre todo si la optimización queda guardada en el `.pgmx`.

### 🎁 De yapa, sin decompilar nada

Buscando cadenas apareció **`isotrd.dll`**, un **quinto binario del emisor** que no estaba en
la lista de cuatro de la rama B, con sus plantillas comentadas en italiano:

```
%sG4F%.*f ;(xISO%d-> timer pneumatica foratrice)
%sG4F%.*f ;(xISO%d-> Ritardo attesa pneumatica FUSI)
%s?%%ETK[16]=1 ;(xISO%d-> Testa pneumatica Up)
%s?%%ETK[16]=2 ;(xISO%d-> Testa pneumatica Down)
```

⇒ El **`G4F1.200`** del cierre del taladrado deja DESCONOCIDO: es el **temporizador neumático
de la perforadora**. Y `?%ETK[16]` queda nombrado: **cabezal neumático arriba/abajo**.

⏸ El **valor** `1.200` no aparece en el snapshot; falta ubicar de qué archivo sale.

---

## 7. Ejecución del plan (2026-08-30)

### ✅ Fase 1 — El esquema del `.pgmx`, volcado

Reflexión sobre cuatro ensamblados, con el resolvedor de dependencias apuntado a la carpeta de
Maestro. Volcado a `esquema/*.tsv` (tipos públicos, herencia, propiedades con su tipo, y enums
con todos sus valores):

| ensamblado | tipos | líneas de esquema |
|---|---|---|
| `MachiningDataModel` | 856 | 998 |
| `ConfigDataModel` | 173 | 503 |
| `ToolDataModel` | 125 | 308 |
| `GeometryDataModel` | 79 | 193 |

#### ⭐ El cruce: qué existe contra qué vimos

Leídos los **358 `.pgmx`** del árbol de reinvestigación y extraídos sus `i:type`:

| familia | el modelo tiene | los fixtures vieron | sin ver |
|---|---|---|---|
| **Features** | 16 | **2** (`GeneralProfileFeature`, `ReplicateFeature` — más `RoundHole`, que no lleva el sufijo) | `ContourFeature`, `SawCutFeature`, `ScrapingFeature`, `TrimmingFeature`, `ChamferFeature`, `EdgeBandingFeature`, `SlantedProfileFeature`, `EndTrimmingFeature`, `ToolpathFeature`… |
| **Operations** | 11 | **1** (`DrillingOperation`) | `MillingMachiningOperation`, `Two5DMillingOperation`, `FreeformOperation`, `ScrapingOperation`, `TrimmingOperation`, `EdgeBandingOperation`, `EndTrimmingOperation` |
| **Executables** (Funciones C.N.) | 7 | **3** (`Xn`, `Xmsg`, `Park`) | **`Iso`**, `NCFunction`, `ProgramStructure`, `WorkingStep` |

*(Parte de los «sin ver» son clases base abstractas — `MachiningFeature`, `Operation`,
`ManufacturingFeature` — que nunca aparecen serializadas.)*

⇒ **Ese es el mapa que faltaba.** La reinvestigación no estaba equivocada, estaba **incompleta
sin saber cuánto**: hoy puede decir que cubrió 1 de 11 operaciones, y cuáles son las otras diez.

⇒ Y aparece **`Iso`** como Executable — la quinta Función C.N. que `programa_vacio.md` había
listado desde la UI y que nunca se tocó.

### ✅ Fase 2 — El catálogo de mensajes, extraído

**5.017 mensajes** de los 20 `.msg` de `Country\Spa\`, volcados a `iso/docs/mensajes_xilog.tsv`
(`archivo · @NNN · texto`).

> ⏸ **Ese `.tsv` queda UNTRACKED a propósito**, como `plan_cierre_converter.md`. Son 250 KB de
> cadenas de un producto de SCM, y el precedente del manual de diagnóstico —que no se copió al
> repo por la reserva de propiedad impresa en cada página— pide preguntar antes. Se regenera en
> segundos desde la instalación. **Decisión pendiente de Fermín**: dejarlo afuera, commitear
> sólo el subconjunto que el converter cita, o incorporarlo entero.

| archivo | mensajes |
|---|---|
| `Sys.msg` | 1.367 |
| `cnc.msg` | 653 |
| `Cyc.msg` | 587 |
| `PviBeR.msg` | 582 |
| `axis.msg` | 409 |

Los dos rechazos que veníamos capturando de a uno quedan ubicados: `Sys.msg @006` («Área de
trabajo no configurada») y `Sys.msg @008` («Microinterruptor- de tope eje X (T=%c%d)»).

⇒ El converter puede **anticipar y nombrar** cualquier rechazo con el texto exacto de la
máquina, en vez de provocarlo.

### ✅ Fase 3 — Los `.cfg` posicionales

Nueve descriptores extraídos de `ExtCad32.dll`. **Dos mapeados y validados contra los datos**
(`fields.cfg` y `spindles.cfg`, los que alimentan al converter); el resto, con el descriptor
guardado y el reparto posicional pendiente. Detalle en `iso/docs/cfg_posicionales.md`.

📌 **Corrección que salió de ahí**: lo que este documento llamaba «el habilitado» del registro
de `fields.cfg` (índice 1, que vale 1 en A–H y 0 en I–P) es en realidad **`SPECY` — "Y mirror
image"**. Los campos I–P no están «deshabilitados»: son **registros vacíos**. No hay campo de
habilitación en el descriptor.

> ⭐ Y `SPECY = 1` en los ocho campos reales es un **candidato** para explicar por qué la `Y` se
> invierte en el `Xn`. Candidato, no derivación: el taladrado **no** invierte la Y, así que un
> espejo por campo no puede ser toda la historia.
