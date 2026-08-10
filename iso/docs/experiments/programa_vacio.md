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
| `WorkPiece/Length·Width·Depth` (+ variables `dx1/dy1/dz1` + `Expressions`) | dimensiones de la pieza; las variables reservadas están LIGADAS a las dimensiones vía `Expressions` | sí (`length/width/depth`) | **panel Pieza → «Dimensiones pieza» → `DX` / `DY` / `DZ`** ✓ |
| `WorkPiece/Geometry` (`i:type="WorkpieceBoxGeometry"`) | forma de la pieza | no (siempre box) | **panel Pieza → «Modo»: `Rectangular` / `Extrusión`** — sólo al crear ✓ |
| `Workplans/MainWorkplan/Setup/WorkpieceSetup/Placement` (`_xP/_yP/_zP` + vectores) | origen/colocación de la pieza en la fase | sí (`origin_x/y/z`) | **panel Pieza → «Posicionamiento» → `X origen` / `Y origen` / `Z origen`**, debajo del desplegable «Fases de trabajo» ✓ |
| `MachiningParameters (XilogHeaderParameters)/ExecutionFields` | campo de ejecución (`HG`/`EF`) | sí (`execution_fields`) | **Parámetros de máquina → «Área»** (desplegable) ✓ |
| `…/WorkpieceOffsetX·Y·Z` | offset de la pieza | **no** | **no está** en Parámetros de máquina — sigue sin ubicar |
| `…/Repetitions` | repeticiones (default 1) | **no** | **Parámetros de máquina → «Repeticiones»** ✓ |
| `…/ContinuousCycle` | ciclo continuo (default false) | **no** | **no está** en Parámetros de máquina — sigue sin ubicar |
| `…/IsTechnologicalMirror` | espejo tecnológico (default false) | **no** | **Parámetros de máquina → «Habilitar compatibilidad tecnológica en áreas especulares en X o Y»** (checkbox) ✓ |
| `…/TableOptions` + `UseDefaultForTableOptions` | opciones de mesa (default 0/false) | **no** | **Parámetros de máquina → «Bloqueo»** (valor) + checkbox «predefinido» — correspondencia por forma, sin verificar |
| `…/MechanicalOptions` | opciones mecánicas (default 0) | **no** | **Parámetros de máquina → «Opciones mecánicas»** (valor + 15 sub-desplegables) ✓ |
| `…/IsRelatedToOppositeSideStop` | tope del lado opuesto (default false) | **no** | **no está** en Parámetros de máquina — sigue sin ubicar (en Opciones existe el global `EnableOppositeSideStop`) |
| `IsMM` | unidades en milímetros (true) | no (fijo) | **Opciones → Idioma → «Unidad de medida»** (Milímetros/Pulgadas). Es global de la aplicación, no del programa ✓ |
| `Variables` (más allá de `dx1/dy1/dz1`) | variables de usuario (Double/Integer/Boolean; UnitLess/Length/Speed) | sí (`parametric_variables`) | **panel «Parámetros»** (abajo izq.; al aplicar muestra `dx1`/`dy1`/`dz1`; su barra de iconos agrega/importa/borra) ✓ |
| `Planes` (Top/Bottom/Left/Right/Front/Back) | las 6 caras, derivadas de las dimensiones | automático (plantilla) | — (no editable directo) |
| `MainWorkplan/Elements` | mecanizados y operaciones de máquina (`Xn`/`Xmsg`/`Park`/`Iso`) | sí | lista de operaciones |
| `CurrentWorkplanIndex` | fase activa | sí (`current_workplan_index`) | **panel Pieza → «Posicionamiento» → desplegable «Fases de trabajo»** (`Setup`); también pestaña `Fases` del árbol Proyecto ✓ |
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

**Consecuencia para la rama E (snapshot de máquina)**: el snapshot tiene que
incluir la configuración de la aplicación, que hoy no está.

> **Corregido el 2026-08-10 tras contar los archivos.** Esta sección decía que
> `iso/data/machine_config/` tenía «3 archivos» y que el snapshot era «un recorte,
> no una copia». **Es falso**: el snapshot tiene **91 archivos** — 82 en
> `xilog_plus/Cfg/` (incluidos `fields.cfg`, `spindles.cfg`, `pheads.cfg`,
> `Params.cfg`), `xilog_plus/axis.ini`, `maestro/Cfgx/` (3) y `maestro/Tlgx/` (3,
> con `def.tlgx`), más un `manifest.csv` que registra el origen
> (`source_root = S:\Xilog Plus`) con sha256 por archivo. Los «3» eran los que el
> converter de la época anterior LEÍA, no los que el snapshot contiene.
> Lo que falta de verdad es puntual: **`UI00.exe.Config` y `Settings\`** del lado
> Maestro — es decir, el tercer origen. E1 no es «copiar todo de nuevo»: es
> agregar esos dos.

**Pregunta abierta que bloquea el uso de los VALORES**: las rutas de `Carpetas`
apuntan todas a `C:\Program Files (x86)\Scm Group\...` y `Preferencias` está en
default de fábrica (nombre de proyecto `Progetto`, en italiano; los cinco
archivos por defecto vacíos). Eso no coincide con las rutas de producción
(`S:\Maestro\...`, salida `C:\PrgMaestro\USBMIX`). Hasta saber si esta
instalación es la que postprocesa de verdad, los valores de arriba valen como
«lo que mostraba esta instalación», no como la configuración del CNC.

### 2026-08-10 — La ventana donde nace el programa: el panel Pieza

Dos capturas de Fermín (el panel recién abierto y el mismo panel tras pulsar
`Aplicar`), en el repo Nora:
`skills/cnc-scm-maestro/references/pantallas/crear-proyecto-panel-pieza-20260810.png`
y `…-aplicado-20260810.png`. Transcripción campo por campo en el README de esa
carpeta.

**Home → Crear → Proyecto** abre el panel **Pieza**, acoplado a la derecha. Es
donde nace un programa, y cierra cuatro filas del inventario:

| Fila del inventario | Dónde está en la UI |
|---|---|
| `Length` / `Width` / `Depth` | «Dimensiones pieza» → **`DX` / `DY` / `DZ`** |
| `Placement/_xP·_yP·_zP` | «Posicionamiento» → **`X origen` / `Y origen` / `Z origen`** |
| `Variables` de usuario | panel **«Parámetros»** (abajo a la izquierda) |
| `CurrentWorkplanIndex` | desplegable **«Fases de trabajo»** |

Lo que la captura fija, más allá del mapeo:

- **El origen pertenece a la FASE, no a la pieza.** Los tres `origen` viven
  dentro de «Posicionamiento», debajo del desplegable «Fases de trabajo». Es
  exactamente lo que dice el `.pgmx` (el `Placement` cuelga del `WorkpieceSetup`
  del workplan), pero hasta ahora era una lectura nuestra del XML: acá se ve.
- **Una magnitud, cuatro nombres.** `DX/DY/DZ` en este panel · `Longitud /
  Anchura / Espesor` en `Opciones > Parámetros > Pieza` · `Length/Width/Depth`
  en el XML · `dx1/dy1/dz1` en las variables. Los cuatro son legítimos (regla 3:
  los nombres del XML vienen de Maestro y son intocables), pero **la UI misma
  usa dos nombres distintos para lo mismo según la ventana**: al nombrar en
  nuestro código hay que decir cuál se está citando.
- **`Modo`: `Rectangular` / `Extrusión`** — un campo que el inventario no tenía.
  Está sólo en la toma 1 y **desaparece tras aplicar**: es una decisión de
  creación, no una propiedad editable después. Nuestro synth escribe siempre
  `WorkpieceBoxGeometry` (= Rectangular); **qué escribe `Extrusión` en el `.pgmx`
  es desconocido**, y una pieza extruida bien podría no ser un box.
- El botón de confirmación dice **`Aplicar`** (no «Aceptar»), y a su lado hay
  `Deshacer`.
- La barra de estado expone, sin abrir ningún menú: fase activa (`Setup`),
  catálogo de herramientas (**`def.tlgx`** — el mismo del que sale nuestro
  `tool_catalog.csv`), modo de ratón y unidad (`Milímetros`).

**Lo que este panel NO tiene**, y por lo tanto sigue faltando ubicar: el campo
de ejecución (`HG`/`EF`) y **todo el bloque `XilogHeaderParameters`** — offset
de pieza, repeticiones, ciclo continuo, espejo tecnológico, opciones de mesa y
mecánicas, tope del lado opuesto. Son propiedades del programa que viajan en el
`.pgmx`; la ventana que las edita todavía no está capturada. Candidatos a mirar:
la pestaña `Máquinas` de la cinta y el diálogo `CAM`.

⚠️ **Incongruencia a resolver (regla 1).** El panel abre con `DX/DY/DZ` =
**300 / 300 / 18**, pero `Opciones > Parámetros > Pieza` declara como default de
pieza nueva **1600 × 1200 × 18**. Las dos lecturas posibles cambian cosas
distintas:

- *El panel recuerda lo último usado.* Entonces un `.pgmx` nuevo nace con
  valores que dependen del historial de esa instalación — un rastro más del
  tercer origen, y un dato que ningún archivo del proyecto explica.
- *La instalación de la captura del 09 no es la misma que la del 10.* Entonces
  la advertencia que ya arrastra `opciones-de-maestro.md` (rutas de fábrica, no
  las de producción) se confirma, y los valores de aquella ventana no describen
  la máquina que postprocesa.

Cuál de las dos sea cambia si el `UI00.exe.Config` que haya que leer es el de la
PC del CNC o el de la de oficina técnica.

### 2026-08-10 (b) — «Parámetros de máquina» y las cuatro pestañas restantes

Cinco capturas más de Fermín, en el repo Nora
(`skills/cnc-scm-maestro/references/pantallas/`): `parametros-de-maquina-20260810.png`
y `editor-cinta-{dibujar,operaciones,maquinas,instrumentos}-20260810.png`.
Transcripción completa en el README de esa carpeta.

**`Máquinas → Parámetros → Parámetros de máquina`** es la ventana que faltaba: ahí
viven las propiedades del programa que no son geometría. Cierra cinco filas más:

| Fila del `.pgmx` | En la ventana |
|---|---|
| `ExecutionFields` | **«Área»** (desplegable, mostraba `HG`) |
| `Repetitions` | **«Repeticiones»** (`1`) |
| `MechanicalOptions` | **«Opciones mecánicas»** (`0`) + 15 sub-desplegables |
| `TableOptions` + `UseDefaultForTableOptions` | **«Bloqueo»** (`0`) + checkbox «predefinido» |
| `IsTechnologicalMirror` | **«Habilitar compatibilidad tecnológica en áreas especulares en X o Y»** |

**El campo de ejecución se llama «Área» en la UI.** Nuestro vocabulario («campo»)
no es el de la ventana — anotarlo antes de nombrar nada nuevo (regla 3).

**Hipótesis por verificar**: tanto «Opciones mecánicas» como «Bloqueo» son UN número
con un panel de sub-opciones debajo (láser, elevadores, cinco filas de topes, ventosas,
Combiflex, FX…; y dispositivo/tipo de bloqueo). La forma sugiere que el entero AGREGA
las sub-opciones como bitmask, pero **no está verificado**: se confirma cambiando una
sub-opción y mirando cómo se mueve el número y el XML.

**Siguen sin ubicar tres filas**: `WorkpieceOffsetX/Y/Z`, `ContinuousCycle` y
`IsRelatedToOppositeSideStop` no aparecen en esta ventana. (De la última, en Opciones
existe el interruptor GLOBAL `EnableOppositeSideStop`: puede que la del programa sólo
se muestre cuando el global está habilitado.)

**Las cinco `Funciones C.N.` de la pestaña Máquinas son las operaciones de máquina**,
con su nombre de UI: `ISO` = `Iso` · **`Operación nula` = `Xn`** · **`Impresión mensaje`
= `Xmsg`** · **`Aparcamiento` = `Park`** · y una quinta, **`Palpación`**, que no tiene
equivalente en nuestro modelo. Con esto, el trío que la regla 2 del `CLAUDE.md` cita
como ejemplo de operaciones distintas queda confirmado desde la UI misma, sin depender
de evidencia de la época congelada.

Y el grupo `Fresado` da los cinco nombres canónicos: **`Fresado` · `Canal` · `Corte con
cuchilla` · `Vaciado` · `Galceado`** (con `Perforado` como grupo aparte). `Corte con
cuchilla` no está en nuestro modelo.

⚠️ **Dato a interpretar con cuidado**: en la pestaña Máquinas, **`Post` y `Verificación
proyecto` están en GRIS**. El programa estaba abierto, sin operaciones y sin guardar.
Cuál de las dos condiciones lo deshabilita decide algo de R001: si es «sin operaciones»,
entonces **el programa vacío no se puede postprocesar** y el ISO del esqueleto puro no
existe como archivo — habría que derivarlo del programa más chico que Maestro acepte.

**Para la rama E**: `Instrumentos → Programaciones → Backup` / `Restore` es el mecanismo
propio de Maestro para llevarse y traer la configuración. Mirarlo antes de inventar un
procedimiento de extracción a mano.

### 2026-08-10 (c) — El gemelo manual, y qué hace el re-guardado en otra PC

Fermín construyó el gemelo manual **y** un experimento de dos máquinas:

1. Creó `R_PV_manual_base.pgmx` a mano en Maestro, en la PC de **oficina técnica**
   (400×400×18, origen 0/0/0, área HG, sin operaciones, nombre interno de pieza
   `R_PV_manual_base`). Esa instalación **no** es la que postprocesa, y tiene su
   propio `UI00.exe.Config`.
2. Lo llevó a la **PC del CNC**, lo abrió y lo postprocesó → `r_pv_manual_base.iso`.
3. Ahí mismo lo re-guardó como `R_PV_manual_base_CNC.pgmx` y volvió a postprocesar
   → `r_pv_manual_base_cnc.iso`.

Los cuatro archivos viven en `…\Programas Manuales\Reinvestigación\` (lado S:) y
`P:\USBMIX\ProdAction\Programas Manuales\Reinvestigación\` (lado P:).

**Resultado 1 — el re-guardado NO toca el programa.** El XML de los dos `.pgmx` es
**byte-idéntico**: mismo tamaño (18.567) y mismo CRC (`9c64dcab`). Los 16 bytes que
difieren entre los ZIP son sólo los nombres internos (`R_PV_manual_base.xml/.epl` vs
`…_CNC.xml/.epl`, cuatro caracteres más, dos veces cada uno por el índice del ZIP).
⇒ **Abrir y guardar un `.pgmx` en la PC del CNC no le imprime nada de esa
instalación.**

**Resultado 2 — los dos ISO son iguales salvo el nombre.** Única diferencia:
`% r_pv_manual_base.pgm` vs `% r_pv_manual_base_cnc.pgm`. Cuatro bytes.

⚠️ **Lo que este experimento NO responde**: los dos ISO se postprocesaron en la
**misma** PC. Que el `.pgmx` no cambie no dice nada sobre si el `UI00.exe.Config` de
la máquina que postprocesa cambia el ISO. Eso lo responde postprocesar **el mismo**
`.pgmx` en las **dos** PCs y comparar — sigue pendiente.

**Resultado 3 — Maestro SÍ postprocesa un programa sin operaciones.** El ISO del
esqueleto existe: 43 líneas, 666 bytes. El gris de `Post` en la captura de la cinta
era por el archivo sin guardar, no por la falta de mecanizados. Queda cerrada la
pregunta abierta del lote R001, y **la etapa B1 arranca**: anatomía línea por línea
en `anatomia_iso.md`.

**Resultado 4 — el control de circularidad (regla 5) da bien.** Comparado el `.pgmx`
manual contra nuestro `R_PV_base.pgmx` sintetizado (misma pieza declarada):

- **mismos tags, en las mismas cantidades** — ninguno sobra ni falta de ningún lado;
- **mismos valores** en todo lo que el inventario mira: `Length/Width/Depth`,
  `ExecutionFields=HG`, `Repetitions=1`, `ContinuousCycle=false`,
  `IsTechnologicalMirror=false`, `TableOptions=0`, `UseDefaultForTableOptions=false`,
  `MechanicalOptions=0`, `IsRelatedToOppositeSideStop=false`,
  `WorkpieceOffsetX/Y/Z=0`, `IsMM=true`;
- **sólo cambia la forma de serializar**: el de Maestro repite el namespace por
  defecto en cada elemento (97 declaraciones `xmlns`, XML de 18.567 bytes); el
  nuestro usa prefijos declarados una vez (20 declaraciones, 13.245 bytes). Mismo
  documento, distinta escritura.

⇒ **Para un programa sin operaciones, el sintetizador escribe lo mismo que Maestro.**
Queda validado como fábrica de fixtures de la etapa 1. (La diferencia de estilo
importa para el lector del converter, que debe aceptar los dos.)

**Bonus — `def.tlgx` viaja DENTRO del `.pgmx`.** Los dos ZIP traen el catálogo de
herramientas embebido (73.449 bytes, fecha 2025-02-01, **mismo CRC en ambos**). O sea:
el catálogo no hay que ir a buscarlo a la PC, viaja con el archivo. Y re-guardar en el
CNC no lo reemplazó — aunque eso no prueba que nunca lo reemplace: puede que ambas PCs
tengan el mismo. Pendiente de separar.

## Pendiente

- Postproceso del lote → `P:\USBMIX\ProdAction\R001_programa_vacio\` (Fermín). Con el
  esqueleto ya derivado, cada fixture ahora responde una fila concreta de
  `anatomia_iso.md`.
- **El experimento que falta**: postprocesar el MISMO `.pgmx` en las dos PCs
  (oficina técnica y CNC) y comparar los ISO. Es lo único que separa «el tercer origen
  se lee al postprocesar» de «se congela al autorar».
- Verificar si `Opciones mecánicas` y `Bloqueo` son bitmask de sus sub-opciones.
- Ubicar las tres filas que faltan: `WorkpieceOffsetX/Y/Z`, `ContinuousCycle`,
  `IsRelatedToOppositeSideStop`.
- Con el primer ISO: iniciar la anatomía línea por línea (parte, origen de cada valor).
- Decidir si las opciones que el synth no varía ameritan gemelos manuales (una opción por
  archivo, hechos en Maestro).
- Averiguar qué escribe el modo **`Extrusión`** en el `.pgmx` (hoy sólo conocemos
  `WorkpieceBoxGeometry`).
