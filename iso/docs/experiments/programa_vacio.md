# Programa vacío — configuración de programa (R001, reinicio de la investigación)

**Época nueva (2026-08-06).** Reinicio metódico de la investigación del converter, decidido
tras el rollback de la ejecución del plan (rama `respaldo/ejecucion-plan-f0-f3`). Etapa 1:
un programa SIN mecanizados. Su ISO es puro esqueleto — cada línea tiene que poder
atribuirse a la configuración del PROGRAMA (el `.pgmx`) o a la configuración de la MÁQUINA
(snapshot de la PC del CNC). Nada puede venir "de una operación" porque no hay ninguna.

Método de la época (directiva de Fermín):

1. Programa vacío → repaso de TODAS las opciones de configuración, una por una, con
   capturas de la UI de Maestro donde el nombre XML no mapee obvio a la UI.
2. Programas crecientes: agregar operaciones variando cada parámetro de manera controlada.
3. En paralelo: anatomía del `.iso` — reconocer las partes y el ORIGEN de cada línea, de
   cada parámetro, de cada valor numérico.
4. Nomenclatura de los algoritmos: GENÉRICA, con la terminología de Maestro. Prohibido
   nombrar por proyectos de producción o por fixtures de la investigación.
5. La serie N (archivada en `Investigacion iso_converter\` de S: y P:, 2026-08-07) NO se usa
   como evidencia en esta época: es material de consulta. La evidencia es la serie R.

## Inventario: qué guarda un `.pgmx` a nivel programa

Fuente: plantilla baseline `pgmx/data/maestro_baselines/Pieza.xml` (capturada de Maestro).

| Nodo del `.pgmx` | Qué es | ¿Nuestro synth lo varía? | Nombre en la UI |
|---|---|---|---|
| `WorkPiece/Length·Width·Depth` (+ `Geometry`, + variables `dx1/dy1/dz1` + `Expressions`) | dimensiones de la pieza; las variables reservadas están LIGADAS a las dimensiones vía `Expressions` | sí (`length/width/depth`) | a confirmar con captura |
| `Workplans/MainWorkplan/Setup/WorkpieceSetup/Placement` (`_xP/_yP/_zP` + vectores) | origen/colocación de la pieza en la fase | sí (`origin_x/y/z`) | a confirmar |
| `MachiningParameters (XilogHeaderParameters)/ExecutionFields` | campo de ejecución (`HG`/`EF`) | sí (`execution_fields`) | a confirmar |
| `…/WorkpieceOffsetX·Y·Z` | offset de la pieza | **no** | a confirmar |
| `…/Repetitions` | repeticiones (default 1) | **no** | a confirmar |
| `…/ContinuousCycle` | ciclo continuo (default false) | **no** | a confirmar |
| `…/IsTechnologicalMirror` | espejo tecnológico (default false) | **no** | a confirmar |
| `…/TableOptions` + `UseDefaultForTableOptions` | opciones de mesa (default 0/false) | **no** | a confirmar |
| `…/MechanicalOptions` | opciones mecánicas (default 0) | **no** | a confirmar |
| `…/IsRelatedToOppositeSideStop` | tope del lado opuesto (default false) | **no** | a confirmar |
| `IsMM` | unidades en milímetros (true) | no (fijo) | **Opciones → Idioma → «Unidad de medida»** (Milímetros/Pulgadas). Es global de la aplicación, no del programa ✓ |
| `Variables` (más allá de `dx1/dy1/dz1`) | variables de usuario (Double/Integer/Boolean; UnitLess/Length/Speed) | sí (`parametric_variables`) | a confirmar |
| `Planes` (Top/Bottom/Left/Right/Front/Back) | las 6 caras, derivadas de las dimensiones | automático (plantilla) | — (no editable directo) |
| `MainWorkplan/Elements` | mecanizados y operaciones de máquina (`Xn`/`Xmsg`/`Park`/`Iso`) | sí | lista de operaciones |
| `CurrentWorkplanIndex` | fase activa | sí (`current_workplan_index`) | selector de fase |
| `EnvironmentVariablesFileName` | archivo de variables de entorno (vacío en plantilla) | **no** | a confirmar |
| `GlobalSetup/GlobalFixtureSetup` | utillaje global (vacío en plantilla) | **no** | a confirmar |
| `Features`, `Geometries`, `Operations`, `ProjectAttributes` | colecciones (vacías sin mecanizados) | vía mecanizados | — |

## Lote R001 (`S:\Maestro\Projects\ProdAction\R001_programa_vacio\`)

Generador: `iso/machining_lab/r001_programa_vacio/generate.py`. Una opción variada por
archivo, siempre contra el base. Verificado con el lector de producción
(`pgmx.adapters.adapt_pgmx_path`): el base no tiene NINGÚN working step; `con_xn` tiene
exactamente un `Xn`; dims/origen/campo aplicados; `p1` escrita.

| Archivo | Varía | Pregunta que responde |
|---|---|---|
| `R_PV_base.pgmx` | — (400×400×18, origen 0/0/0, HG, sin Xn) | el esqueleto puro: qué emite el postprocesador sin operaciones |
| `R_PV_dim_500x350x25.pgmx` | dimensiones | dónde aparecen DX/DY/DZ en el ISO |
| `R_PV_origen_x100_y50.pgmx` | origen XY | dónde aparece el origen XY (¿y aparece siquiera?) |
| `R_PV_origen_z5.pgmx` | origen Z | ídem para Z |
| `R_PV_campo_EF.pgmx` | campo EF | qué cambia el campo en el ISO |
| `R_PV_con_xn.pgmx` | + un Xn default | el bloque EXACTO que un Xn agrega al esqueleto |
| `R_PV_variable_usuario.pgmx` | + variable `p1=100` sin uso | ¿una variable sin uso deja rastro en el ISO? |

Más el gemelo manual `R_PV_manual_base.pgmx` (crear EN MAESTRO, sin sintetizador): control
de circularidad — regla 5 del CLAUDE.md.

Si Maestro se NIEGA a postprocesar un programa sin operaciones, el mensaje exacto del
rechazo también es un dato del experimento (quedaría derivado: "el esqueleto solo se puede
observar con al menos N operaciones").

## Derivado

### 2026-08-09 — Hay un TERCER origen: la ventana Opciones de Maestro

Capturas de Fermín (19), transcriptas en el repo Nora:
`skills/cnc-scm-maestro/references/opciones-de-maestro.md` + las imágenes en
`references/pantallas/opciones-*-20260809.png`.

La premisa de esta etapa era que cada línea del ISO vacío se atribuye a la
configuración del **PROGRAMA** (el `.pgmx`) o a la de la **MÁQUINA** (snapshot de
la PC del CNC). **La dicotomía no alcanza.** La ventana Opciones (Home →
Visualización → Opciones, se abre sin ningún programa abierto) es configuración
**global de la aplicación**, no viaja en el `.pgmx`, y decide cosas que cambian
el ISO entero:

| Opción (nodo `Post`) | Valor visto | Qué decide |
|---|---|---|
| Formato de salida | XXL / PGM / **ISO** | que el postproceso emita ISO y no PGM |
| Configuraciones del tope de referencia | **Scm (anterior)** / Morbidelli (posterior) | desde qué tope se mide |
| Notación de profundidad de trabajo | **Scm (Z negativa)** / Morbidelli (Z positiva) | el SIGNO de todas las profundidades |

Y en el nodo `Parámetros` (raíz), valores que hasta ahora se habrían tomado por
constantes: `Distancia de seguridad desde la mesa de trabajo` = 20 ·
**`Paso de retroacción en los fresados` = 10** · `Multiplicador del radio en
aproximaciones/alejamientos` = 1,2 · `Velocidad rápida en los desplazamientos`
= 50. Y en `Funciones CN`: **`Estacionamiento automático finalizada la
ejecución`, MARCADO**, con `Modalidad de estacionamiento finalizada la ejecución`
= «Ningún paro».

Consecuencia para la regla 4 del `CLAUDE.md` («el convertidor no puede tener
constantes internas… todo sale de la config»): **una parte de esa config no está
ni en el `.pgmx` ni en los archivos de máquina, está acá.** El converter va a
necesitar leerla, y el snapshot de máquina (rama E) tiene que incluirla.

Derivado también, de `Idioma`: **`IsMM` es global de la aplicación**
(«Unidad de medida»: Milímetros / Pulgadas), no una propiedad elegible por
programa. Y de `Pieza`: las dimensiones por defecto de una pieza nueva son
1600 × 1200 × 18, con los nombres de UI **Longitud / Anchura / Espesor**.

**Hipótesis, no derivada** (la confirma o la mata el primer ISO de R001): si
«Estacionamiento automático finalizada la ejecución» está marcado, el
postprocesador podría agregar un park que el `.pgmx` NO pide. Si el ISO de
`R_PV_base` —un programa sin una sola operación— trae un park, viene de acá.

**El tercer origen tiene archivo**: `<Maestro>\UI00.exe.Config`, un `.config` de
.NET con ~175 claves en `<appSettings>`. Toda la ventana Opciones está ahí —
`PostFileFormat=ISO`, `IsZetaScm=True`, `IsAreaScm=True`, `SecurityDistance=20`,
`MillingRetractDistance=10`, `RadiusMultiplier=1,2`, `RapidFeed=50`, `IsMM=true`
— más claves sin UI conocida. La plantilla de fábrica es
`<Maestro>\Settings\default.settingsx`. Nada en `%APPDATA%` ni en el
`VirtualStore` de UAC. Mapeo UI↔clave y advertencias en el repo Nora:
`skills/cnc-scm-maestro/references/opciones-de-maestro.md`.

⚠️ Una contradicción sin resolver: la captura muestra «Estacionamiento automático
finalizada la ejecución» MARCADO y el archivo dice `IsFinalPark=False`. La
hipótesis del park automático depende de eso, así que **queda en suspenso hasta
saldarla**.

**Consecuencia para la rama E (snapshot de máquina)**: hoy
`iso/data/machine_config/` tiene 3 archivos (`NCI.CFG`, `NCI_ORI.CFG`,
`pheads.cfg`). La carpeta `<Xilog Plus>\Cfg\` de una instalación real tiene **83**.
Y falta por completo el lado Maestro (`UI00.exe.Config`, `Settings\`, `Cfgx\`,
`Tlgx\`). El snapshot actual es un recorte, no una copia.

**Pregunta abierta que bloquea el uso de los VALORES**: las rutas de `Carpetas`
apuntan todas a `C:\Program Files (x86)\Scm Group\...` y `Preferencias` está en
default de fábrica (nombre de proyecto `Progetto`, en italiano; los cinco
archivos por defecto vacíos). Eso no coincide con las rutas de producción
(`S:\Maestro\...`, salida `C:\PrgMaestro\USBMIX`). Hasta saber si esta
instalación es la que postprocesa de verdad, los valores de arriba valen como
«lo que mostraba esta instalación», no como la configuración del CNC.

## Pendiente

- Postproceso del lote → `P:\USBMIX\ProdAction\R001_programa_vacio\` (Fermín).
- Capturas de la UI: ventana(s) de propiedades del programa/pieza donde viven las opciones
  de la tabla — para completar la columna "Nombre en la UI" y detectar opciones que la UI
  tenga y el XML de la plantilla no muestre (o al revés).
- Con el primer ISO: iniciar la anatomía línea por línea (parte, origen de cada valor).
- Decidir si las opciones que el synth no varía ameritan gemelos manuales (una opción por
  archivo, hechos en Maestro).
