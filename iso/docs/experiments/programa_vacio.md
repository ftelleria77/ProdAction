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
| `IsMM` | unidades en milímetros (true) | no (fijo) | ¿configurable en la UI? |
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

(nada aún — a la espera del postproceso del lote)

## Pendiente

- Postproceso del lote → `P:\USBMIX\ProdAction\R001_programa_vacio\` (Fermín).
- Capturas de la UI: ventana(s) de propiedades del programa/pieza donde viven las opciones
  de la tabla — para completar la columna "Nombre en la UI" y detectar opciones que la UI
  tenga y el XML de la plantilla no muestre (o al revés).
- Con el primer ISO: iniciar la anatomía línea por línea (parte, origen de cada valor).
- Decidir si las opciones que el synth no varía ameritan gemelos manuales (una opción por
  archivo, hechos en Maestro).
