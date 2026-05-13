# ISO State Synthesis

Nueva memoria de trabajo para redisenar la generacion ISO desde cero sin
arrastrar la arquitectura por patrones de `iso_generation/`.

Ultima actualizacion: 2026-05-11

## Alcance

- Retirar `iso_generation/` de esta rama y concentrar el trabajo ISO nuevo en
  `iso_state_synthesis/`.
- Trabajar en la rama `iso-state-synthesis` para no afectar el flujo principal
  del sistema.
- Crear un entorno nuevo para investigar y luego implementar el enfoque por
  estado, parametros y diferenciales.
- No traer por ahora contenido de la memoria vieja ni del contrato viejo.
- Usar los mismos archivos `.pgmx` e `.iso` de estudio como corpus de
  investigacion cuando haga falta evidencia.
- Antes de empezar a codificar, repasar esta memoria completa con el usuario y
  depurar los detalles que el usuario vea necesarios.

## Objetivo Del Enfoque

Construir un traductor `.pgmx -> .iso` que pueda explicar cada linea emitida
como consecuencia de una de estas fuentes:

- un dato de la pieza;
- un dato del trabajo indicado en el `.pgmx`;
- un dato de herramienta o maquina;
- un estado que debe estar activo para ejecutar una etapa;
- un reset necesario despues de una etapa;
- una regla observada y documentada contra pares `.pgmx/.iso`.

El objetivo no es coleccionar combinaciones como `perfil + taladros laterales`
o `ranura + taladros`, sino entender que estado requiere cada etapa y emitir el
diferencial entre el estado actual y el estado objetivo.

## Principio De Diseno

Eliminar la idea de transiciones por combinacion de tipo de mecanizado.

El generador nuevo debe sintetizar el ISO desde datos observados, estados
requeridos y diferenciales entre etapas, no desde una lista creciente de
patrones como `polilinea -> taladros laterales` o `ranura -> taladros`.

Una combinacion nueva deberia fallar solamente si falta conocer:

- que datos pide una etapa;
- que estado objetivo necesita;
- que reset deja al terminar;
- como pasar desde el estado anterior al nuevo.

No deberia fallar por no existir un caso global con nombre propio.

## Vocabulario Inicial

- `Estado actual`: mapa de valores que el ISO ya dejo activos en un punto del
  programa. Incluye valores de pieza, herramienta, cara/plano, offsets,
  correctores, seguridad, posicion y cualquier variable modal observada.
- `Estado objetivo`: mapa de valores que deben estar activos antes de ejecutar
  una etapa concreta.
- `Diferencial`: conjunto ordenado de lineas ISO necesarias para transformar el
  estado actual en el estado objetivo.
- `Etapa`: momento ejecutable del programa. Puede ser preparacion de pieza,
  preparacion de herramienta, aproximacion, corte, retirada, reset o cierre.
- `Trabajo`: mecanizado pedido por el `.pgmx`, con su herramienta, cara,
  geometria, profundidad, sentido, compensacion, entradas/salidas y parametros
  propios.
- `Traza`: geometria ejecutable de un trabajo una vez traducida a movimientos
  ISO. No incluye por si sola la preparacion modal.
- `Reset`: cambio de estado que Maestro o la CNC dejan como condicion esperada
  despues de una etapa. Puede ser explicito en ISO o implicito por una familia
  de trabajo.
- `Fuente`: origen que justifica un valor. Debe ser una ruta dentro del `.pgmx`,
  una configuracion de maquina, una constante observada o una regla todavia
  marcada como hipotesis.

## Capas De Estado

Para no mezclar todo en una misma bolsa, el estado se va a separar inicialmente
en estas capas:

- `pieza`: dimensiones, origen, area/campo de trabajo, nombre de programa y
  datos de cabecera.
- `maquina`: configuracion, limites, parqueos, seguridad y valores que no nacen
  de una pieza puntual.
- `herramienta`: seleccion, spindle, velocidad, avance, largo, radio, offsets y
  habilitaciones asociadas.
- `trabajo`: cara/plano, familia de mecanizado, profundidad, lado de
  compensacion, estrategia de entrada/salida y datos propios de la operacion.
- `movimiento`: posicion conocida, modo de avance, corrector activo, marco
  modal y condiciones necesarias para interpretar la traza.
- `salida`: lineas emitidas, lineas obligadas aunque no cambie un valor, y
  resets pendientes.

Estas capas son un punto de partida. Si un valor no entra bien en ninguna,
conviene marcarlo como `sin_clasificar` antes que forzarlo.

## Configuracion De Maquina

El entorno nuevo tiene su propia copia local de investigacion:

- `iso_state_synthesis/machine_config/snapshot/xilog_plus`, copiada desde
  `S:\Xilog Plus`, excluyendo `Fxc`;
- `iso_state_synthesis/machine_config/snapshot/maestro/Cfgx`, copiada desde
  `S:\Maestro\Cfgx`;
- `iso_state_synthesis/machine_config/snapshot/maestro/Tlgx`, copiada desde
  `S:\Maestro\Tlgx`.

El manifiesto vive en
`iso_state_synthesis/machine_config/snapshot/manifest.csv` y registra ruta
fuente, ruta relativa, tamano y SHA256.

A partir de esta decision, cuando se investiguen datos de maquina para este
enfoque se debe consultar primero esta copia local. Las rutas `S:` quedan como
fuente original para refrescar el snapshot, no como dependencia cotidiana del
analisis.

Decision: `Xilog Plus/Fxc` queda fuera del snapshot porque se considera
biblioteca de plantillas/ciclos del software Xilog Plus, no configuracion
directa de maquina.

## Politica De Fuentes De Herramienta

Para explicar una herramienta usada por un `.pgmx`, la fuente principal es el
`def.tlgx` embebido dentro de ese mismo `.pgmx`.

Orden de preferencia:

1. `def.tlgx` embebido en el `.pgmx` estudiado.
2. `iso_state_synthesis/machine_config/snapshot/maestro/Tlgx/def.tlgx`.
3. `iso_state_synthesis/machine_config/snapshot/xilog_plus/Job/def.tlg`.
4. `spindles.cfg`, `pheads.cfg`, `oheads.cfg` y otros archivos Xilog solo como
   evidencia de contraste para cabezales, offsets fisicos o registros que no
   esten nombrados en el `def.tlgx`.

Motivo: el `.pgmx` transporta el toolset con el que Maestro genero o preparo
ese trabajo concreto. Las copias del snapshot describen la instalacion local,
pero pueden quedar desfasadas respecto del paquete que se esta traduciendo.

## Reglas Iniciales

- Esta memoria empieza de cero por decision del usuario.
- La memoria vieja solo se consulta si el usuario pide traer un dato concreto.
- La investigacion nueva de datos de maquina debe usar la copia local propia de
  `iso_state_synthesis/machine_config/snapshot`, no el snapshot historico de
  `iso_generation/`.
- Las decisiones nuevas deben registrarse aca antes de modificar codigo.
- El primer resultado esperado no es codigo, sino una memoria revisada y
  depurada que sirva como contrato de trabajo para este entorno.
- Cada regla nueva debe registrar su evidencia minima: que `.pgmx` se miro, que
  `.iso` se comparo y que diferencia explica.
- Un valor puede quedar como `hipotesis`, pero no como verdad silenciosa.
- La salida nueva debe poder explicar por que emite una linea y tambien por que
  decide no emitirla.
- Los nombres internos deben describir estado y responsabilidad, no casos de
  combinacion.

## Metodo De Investigacion

1. Elegir un par `.pgmx/.iso` pequeno.
2. Separar manualmente el ISO en etapas.
3. Para cada etapa, anotar:
   - estado recibido;
   - estado objetivo;
   - diferencial emitido;
   - traza ejecutada;
   - reset producido;
   - fuente de cada valor.
4. Repetir con una pieza casi igual que cambie una sola variable.
5. Mover el valor explicado a una regla de estado solo cuando sobreviva a la
   comparacion entre variantes.

Este metodo busca evitar que una coincidencia puntual se convierta demasiado
pronto en arquitectura.

## Primer Experimento Propuesto

Antes de codificar, hacer una tabla de estados para una pieza minima y dos
variantes cercanas:

- una pieza con una unica operacion simple;
- una variante que cambie solo la posicion de la traza;
- una variante que cambie solo el origen de pieza;
- una comparacion linea por linea que separe datos de pieza, datos de trabajo y
  datos de maquina.

Resultado esperado del experimento:

- una lista corta de campos de estado confirmados;
- una lista de campos dudosos;
- una primera forma de tabla `estado actual -> estado objetivo -> diferencial`;
- una decision sobre la estructura inicial que recien entonces se va a codificar.

Documentos de trabajo creados:

- `iso_state_synthesis/experiments/001_top_drill_state_table.md`
- `iso_state_synthesis/experiments/002_xilog_plus_documentation_survey.md`
- `iso_state_synthesis/experiments/003_boring_head_speed_state.md`
- `iso_state_synthesis/experiments/004_side_drill_state_table.md`
- `iso_state_synthesis/experiments/005_line_e004_state_table.md`
- `iso_state_synthesis/contracts/xiso_intermediate_contract.md`
- `iso_state_synthesis/model.py`
- `iso_state_synthesis/differential.py`
- `iso_state_synthesis/emitter.py`
- `iso_state_synthesis/pgmx_source.py`
- `iso_state_synthesis/cli.py`

Pares elegidos:

- base: `ISO_MIN_001_TopDrill_Base`
- cambio de traza: `ISO_MIN_002_TopDrill_Y60`
- cambio de origen: `ISO_MIN_006_TopDrill_OriginY10`

Decision de formato: la primera tabla vive en Markdown porque todavia es
material de discusion humana. Si el modelo se estabiliza, se pasa luego a CSV o
JSON para alimentar codigo.

Avance registrado el 2026-05-06:

- Se amplio la lectura del primer experimento con las seis variantes de taladro
  superior del fixture minimo (`001` a `006`).
- Quedo confirmada para este caso la regla de cabecera
  `DX/DY/DZ = dimension + origin`.
- Quedo confirmada la lectura de traza: cambiar `point_x` o `point_y` cambia
  solo el movimiento XY del taladro.
- Quedo confirmada para `Top Drill` con herramienta `005` la regla
  `Z ISO = toolpath_z local + ToolOffsetLength`. En el fixture base,
  `38 + 77 = Z115` y `8 + 77 = Z85`.
- La fuente principal de datos de herramienta debe ser el `def.tlgx` embebido
  dentro del propio `.pgmx`; ahi esta la longitud `77` de la herramienta `005`.
- `tools.pgmx_snapshot` ahora lee automaticamente ese `def.tlgx` embebido y lo
  expone como `tooling_entry_name`, `embedded_tools` y `embedded_spindles`.
- Las copias `maestro/Tlgx/def.tlgx` y `xilog_plus/Job/def.tlg` del snapshot
  confirman el mismo dato, pero quedan como respaldo/contraste de maquina.
- `S6000M3` queda explicado por `SpindleSpeed.Standard=6000` en el `def.tlgx`
  embebido.
- `F2000.000` queda explicado por `DescentSpeed.Standard=2`, emitido como
  `2 * 1000`.
- `SHF[X]=-64.000` y `SHF[Z]=-0.950` quedan explicados por la traslacion del
  spindle `005` en el `def.tlgx` embebido: `OX=64`, `OY=0`, `OZ=0.95`,
  emitida con signo negativo.
- Sigue como hipotesis pendiente `?%ETK[17]=257`; aparece como registro en
  `spindles.cfg` y `xilog_plus/Job/def.tlg`, pero falta clasificar su sentido.
- `NCI.CFG` y `NCI_ORI.CFG` confirman solo el reset comun `?%ETK[17]=0` en
  `$GEN_END`; no documentan el significado formal de cargar `257`.
- Se exploro el arbol instalado
  `C:\Program Files (x86)\Scm Group\Xilog Plus` en busca de documentacion
  tecnica sobre ISO. El resultado queda registrado en
  `iso_state_synthesis/experiments/002_xilog_plus_documentation_survey.md`.
- No se encontro un manual que describa completo el algoritmo `PGMX/PGM -> ISO`.
  La evidencia apunta a una cadena compuesta por modelo XISO/PGM interpretado,
  DLLs (`Pgm2Iso32`, `PppIso`, `PostISO`, `VtGenIso`, `IsoTrd`, `Xiso32`),
  `NCI.CFG` y configuracion de herramienta/cabezal.
- Los esquemas `XISO*.xsd` documentan un modelo intermedio util para etiquetar
  operaciones (`H`, `G0`, `G1`, `G2`, `G3`, etc.), pero no son por si solos la
  especificacion de la salida ISO final.
- `XISOProjectSchema` queda registrado como vocabulario intermedio candidato en
  `iso_state_synthesis/contracts/xiso_intermediate_contract.md`; por ahora no
  se exige emitir XML XISO valido en el MVP.
- Se creo el primer esqueleto ejecutable del sintetizador por estado:
  `model.py` define fuentes, valores, etapas, trazas y planes;
  `pgmx_source.py` convierte un `PgmxSnapshot` en plan interno; `cli.py` expone
  `py -3 -m iso_state_synthesis inspect-pgmx <archivo.pgmx>`.
- `differential.py` calcula el diferencial entre estado activo, estado objetivo
  y resets por etapa. El CLI expone
  `py -3 -m iso_state_synthesis evaluate-pgmx <archivo.pgmx>`.
- `StateValue.required=True` queda como primer mecanismo para representar
  valores/lineas obligatorias aunque el valor activo no cambie; el diferencial
  los clasifica como `force` o `force_reset`.
- `emitter.py` toma el `IsoStateEvaluation` y genera el primer ISO candidato
  explicado para `ISO_MIN_001_TopDrill_Base`, con fuente por linea. El CLI
  expone `emit-candidate` y `compare-candidate`.
- Validacion inicial del candidato contra Maestro:
  `py -3 -m iso_state_synthesis compare-candidate
  S:\Maestro\Projects\ProdAction\ISO\minimal_fixtures_2026-05-03\ISO_MIN_001_TopDrill_Base.pgmx
  P:\USBMIX\ProdAction\ISO\minimal_fixtures_2026-05-03\iso_min_001_topdrill_base.iso`
  devuelve `84 vs 84 lineas, 0 diferencias` bajo normalizacion.
- Validacion ampliada: el mismo emisor candidato compara `0 diferencias` contra
  las seis variantes Top Drill del fixture minimo (`001` base, `002` Y60,
  `003` X60, `004` DY200, `005` DX200, `006` OriginY10). Todas producen
  `84 vs 84 lineas` normalizadas.
- El primer plan materializa `program_header`, `machine_preamble`,
  `top_drill_prepare`, `top_drill_trace`, `top_drill_reset` y `program_close`
  para el fixture minimo de taladro superior, sin emitir ISO final.
- Se agrego metadata por linea en `ExplainedIsoLine.rule_status` para separar
  reglas Top Drill generalizadas en `001` a `006` de constantes de maquina/campo
  e hipotesis pendientes.
- La clasificacion inicial del emisor distingue `generalized_top_drill_001_006`,
  `identity_normalization_pending`, `machine_config_template`,
  `field_constant_pending_source`, `field_modal_pending_source`,
  `modal_frame_observed`, `top_drill_modal_observed`,
  `top_drill_reset_observed`, `machine_close_observed`,
  `machine_metric_hypothesis`, `boring_head_speed_change`,
  `repeated_modal_reset_hypothesis`, `modal_trace_hypothesis`,
  `top_drill_modal_hypothesis`, `modal_reset_hypothesis` y
  `machine_close_hypothesis`.
- Con las unidades `S:` y `P:` disponibles, se repitio `compare-candidate`
  despues de agregar `rule_status`: las seis variantes Top Drill del fixture
  minimo (`001` a `006`) siguen comparando `84 vs 84 lineas`, `0 diferencias`.
- Se verificaron las velocidades del `BooringUnitHead` en `def.tlgx`: brocas
  verticales `001/005/006/007` a `6000`, `002/003/004` a `4000`, brocas
  horizontales `058/059/060/061` a `6000`, y sierra vertical `082` standard
  `4000` con maximo `6000`.
- La evidencia ISO confirma que `?%ETK[17]=257` no representa una velocidad
  fija: aparece antes de `S4000M3` y antes de `S6000M3`, y no se repite cuando
  herramientas consecutivas conservan la misma velocidad. Queda como regla
  candidata de cambio/activacion de velocidad del cabezal perforador.
- `Pieza_001_R.pgmx` / `pieza_001_r.iso` refuerza la regla: reordena las brocas
  verticales como `001,002,005,003,006,004,007` para alternar `6000` y `4000`
  rpm, y Maestro emite `?%ETK[17]=257` antes de cada nueva `S...M3`.
- La regla quedo implementada en el calculo diferencial:
  `pgmx_source.py` agrega `maquina.boring_head_speed`, `differential.py` emite
  `salida.etk_17=257` solo si esa velocidad cambia, y `emitter.py` toma de ahi
  `?%ETK[17]=257` + `S...M3`.
- Validacion del diferencial: `Pieza_001.pgmx` calcula 3 activaciones de
  velocidad; `Pieza_001_R.pgmx` calcula 7 activaciones, una por cada alternancia
  `6000/4000`.
- El detalle quedo registrado en
  `iso_state_synthesis/experiments/003_boring_head_speed_state.md`.

Avance registrado el 2026-05-07:

- Se agrego soporte de estado para taladros laterales D8 del fixture minimo
  (`ISO_MIN_010` a `ISO_MIN_013`).
- La politica lateral queda documentada como estado de trabajo: cara, `ETK[8]`,
  spindle fisico, mascara `ETK[0]`, eje de avance, direccion y signo de la
  coordenada fija.
- Los offsets laterales `SHF[MLV=2]` se toman del `def.tlgx` embebido en cada
  `.pgmx`, aplicando signo negativo a la traslacion del spindle lateral.
- Se agrego soporte de estado para fresado lineal superior `E004`
  (`ISO_MIN_020` a `ISO_MIN_023`).
- El detector E004 reconoce `BottomAndSideFinishMilling` con `ToolKey=E004`,
  no solamente tipos cuyo nombre contenga `MillingOperation`.
- El bloque router E004 toma herramienta y tecnologia del `def.tlgx` embebido:
  `T4`, `ETK[9]=4`, `ETK[18]=1`, `S18000M3`, `SVL/VL6=107.200` y
  `SVR/VL7=2.000`.
- Los offsets del router `SHF[MLV=2]=(32.050, -246.650, -125.300)` se leen de
  `pheads.cfg`, valores numericos 308..310 con signo invertido.
- Para lineas E004 simples, la profundidad pasante se emite como
  `-(piece_depth + extra_depth)`.
- Para la variante `PH=5`, la traza se emite desde los puntos `TrajectoryPath`
  con regla `Z ISO = local_z - piece_depth`; con `SideOfFeature=Center` no hay
  `G41/G42`.
- Validacion completa del corpus minimo:
  - `ISO_MIN_001` a `006`: `84 vs 84 lineas`, `0 diferencias`.
  - `ISO_MIN_010` y `013`: `97 vs 97 lineas`, `0 diferencias`.
  - `ISO_MIN_011` y `012`: `88 vs 88 lineas`, `0 diferencias`.
  - `ISO_MIN_020`, `021` y `023`: `94 vs 94 lineas`, `0 diferencias`.
  - `ISO_MIN_022`: `108 vs 108 lineas`, `0 diferencias`.
- En este avance el emisor candidato quedo acotado a una sola familia de
  trabajo por programa. La siguiente capa importante era combinar multiples
  trabajos con el mismo modelo de diferenciales.
- El detalle queda registrado en
  `iso_state_synthesis/experiments/004_side_drill_state_table.md` y
  `iso_state_synthesis/experiments/005_line_e004_state_table.md`.

Correccion posterior del 2026-05-07 sobre corpus `Pieza*`:

- Se corrio `compare-candidate` sobre 105 pares `Pieza*.pgmx` /
  `pieza*.iso` desde `S:\Maestro\Projects\ProdAction\ISO` y
  `P:\USBMIX\ProdAction\ISO`.
- El emisor ahora rechaza planes con `unsupported_stage_family` antes de emitir
  un ISO parcial. Esto evita falsos `Resultado: distinto` cuando una familia no
  soportada, por ejemplo `Escuadrado_Antihorario_E001_Estandar`, fue omitida
  por el plan.
- El CLI `compare-candidate` y `emit-candidate` reportan esos casos como
  `Sin candidato: ...` en vez de mostrar traceback.
- Para `Top Drill`, `?%ETK[0]` dejo de ser constante `16`: ahora se modela como
  mascara de spindle vertical `2 ** (spindle - 1)`. La herramienta `005`
  mantiene `16`; la herramienta D8 `001` emite `1`.
- Para `Top Drill` pasante, si el toolpath local baja por debajo de `Z0` solo
  por `extra_depth`, la Z ISO se calcula clampando `local_z` a `0` antes de
  sumar `ToolOffsetLength`. Esto reproduce `Pieza_014`.
- Para secuencias de varios `Top Drill`, el emisor replica la preparacion
  incremental observada por Maestro: bloque completo solo en el primer trabajo,
  reposicion corta si se repite herramienta, cambio incremental si cambia
  herramienta, reset corto entre trabajos y reset completo solo al final.
- Se agrego soporte acotado para fresado de perfil `E001` sobre `Top` con
  contorno cerrado `ClosedPolylineMidEdgeStart`. Cubre
  acercamiento/alejamiento `Arc`, `Line`, deshabilitados, y estrategias PH5
  unidireccional/bidireccional observadas.
- El emisor ahora puede recorrer secuencias mixtas soportadas. Para `E001` ->
  `E004`, replica el reset intermedio de router y la preparacion incremental de
  E004 sin reemitir `?%ETK[6]`, `%Or[0]` ni `SHF[X/Y/Z]`.
- Para `E004` con acercamiento/alejamiento lineal habilitado, la traza usa
  `Approach`, `TrajectoryPath` y `Lift`; en `Right/Left` sin PH5 emite
  `G42/G41`, mientras que con PH5 conserva el toolpath offset y no compensa.
- Para `E004` de contorno `Center` sin estrategia ni acercamiento/alejamiento,
  se agregaron los subcasos `OpenPolyline` y `Circle`: usa toolpath directo,
  omite `Z` repetida en movimientos XY y en circulos emite arcos por centro
  `I/J`.
- Para contornos `OpenPolyline` y `Circle` sin lead con `SideOfFeature=Left` o
  `Right`, Maestro usa coordenada nominal con `G41/G42`. El lead corto de
  entrada/salida observado es fijo `1.000` sobre la tangente nominal, no depende
  del radio de herramienta. Esto suma `Pieza_016`, `017`, `023`, `024`,
  `027..030`, `096` y `097`.
- Para `OpenPolyline` con `SideOfFeature=Left/Right`, sin estrategia y con
  acercamiento/alejamiento `Line` o `Arc` en modo `Down/Up`, Maestro tambien
  usa coordenada nominal con `G41/G42`. En `Line`, el lead usa la tangente
  nominal con distancia `tool_radius * radius_multiplier` y un punto rapido
  `1.000` mas afuera. En `Arc`, el centro sale de desplazar el punto nominal por
  la normal del lado de compensacion y el punto rapido agrega `1.000` sobre esa
  normal. Esto suma `Pieza_092..095`.
- Para estudiar esa regla por herramienta, se genero la matriz espejo
  `router_compensation_tool_mirror_fixtures_2026-05-07` con
  `tools.studies.iso.router_compensation_tool_mirror_fixtures_2026_05_07`.
  Quedaron 24 `.pgmx` generados para `E001`, `E003`, `E004`, `E005`, `E006` y
  `E007`; los 4 casos `E002` quedaron pendientes manuales porque la generacion
  automatica bloquea `Sierra Horizontal`. Los 24 generados se leen con
  `inspect-pgmx` y emiten candidato con `emit-candidate`.
- El usuario agrego manualmente los 4 `.pgmx` `E002`; la revision estructural
  de la carpeta completa dio 28/28 `.pgmx` correctos. Los ISO candidatos se
  generaron en la subcarpeta `candidate_iso` y el barrido contra los ISO de
  Maestro dio 28/28 exactos. El reporte quedo en
  `S:\Maestro\Projects\ProdAction\ISO\router_compensation_tool_mirror_fixtures_2026-05-07\validation_report.csv`.
- La regla de fresado lineal/contorno ya no esta atada a `ToolKey=E004`: acepta
  herramientas `E00x`, incluida `E002`, y toma numero, largo, radio, avances y
  velocidad desde el `def.tlgx` embebido. La validacion exacta disponible cubre
  `E004` y dos casos `E003`.
- Para ampliar esa evidencia, se genero la matriz espejo por herramienta con
  `tools.studies.iso.router_tool_mirror_fixtures_2026_05_07`: 28 `.pgmx` en
  `S:\Maestro\Projects\ProdAction\ISO\router_tool_mirror_fixtures_2026-05-07`
  mas `manifest.csv`, cubriendo `E001` a `E007` sobre linea vertical,
  polilinea abierta, circulo antihorario y circulo horario.
- Los ISO de Maestro para la matriz espejo quedaron en
  `P:\USBMIX\ProdAction\ISO\router_tool_mirror_fixtures_2026-05-07`.
  El barrido `compare-candidate` devuelve 28/28 exactos, sin candidatos
  faltantes y sin diferencias linea-a-linea.
- La matriz espejo confirmo una regla de resolucion de herramienta para el ISO:
  cuando el `ToolKey` de la operacion trae un `ID` y un `Name` que no apuntan a
  la misma herramienta embebida, Maestro resuelve el router por `Name`
  (`E004`, `E005`, etc.). El adaptador ISO prioriza ahora `Name` unico y solo
  cae al `ID` si el nombre no resuelve.
- Resultado nuevo del barrido `Pieza*`: 48 pares exactos
  (`Pieza_001`, `Pieza_001_R`, `Pieza_004`, `Pieza_012`, `Pieza_013`,
  `Pieza_014`, `Pieza_015`, `Pieza_016`, `Pieza_017`, `Pieza_018`,
  `Pieza_019`, `Pieza_020`, `Pieza_021`, `Pieza_022`, `Pieza_023`,
  `Pieza_024`, `Pieza_025`, `Pieza_026`, `Pieza_027`, `Pieza_028`,
  `Pieza_029`, `Pieza_030`, `Pieza_059`, `Pieza_060`, `Pieza_061`,
  `Pieza_062`,
  `Pieza_063`, `Pieza_064`, `Pieza_065`, `Pieza_066`, `Pieza_067`,
  `Pieza_068`, `Pieza_069`, `Pieza_070`, `Pieza_071`, `Pieza_084`,
  `Pieza_085`, `Pieza_086`, `Pieza_092`, `Pieza_093`, `Pieza_094`,
  `Pieza_095`, `Pieza_096`, `Pieza_097`, `Pieza_DosHuecos`,
  `Pieza_DosHuecos_Origen_5_5_25`, `Pieza_Hueco8`,
  `Pieza_Hueco8_Origen_5_5_25`) y 57 `Sin candidato` por soporte pendiente.
  No quedan diferencias linea-a-linea en candidatos emitidos.
- Se agrego soporte para fresados circulares router con estrategia
  `HelicalMillingStrategySpec`, `UnidirectionalMillingStrategySpec` y
  `BidirectionalMillingStrategySpec`, incluyendo lados `Center/Left/Right`.
  Los arcos se emiten desde las primitivas del toolpath; esto permite
  reproducir los centros `I/J` desplazados de la bajada helicoidal y el cambio
  de sentido por pasada en bidireccional. Validacion exacta:
  `Pieza_031..034`, `Pieza_047..058` y `Pieza_072..075`.
- Para circulos `Center` sin estrategia y con acercamiento/alejamiento
  `Line/Arc` en modos `Quote` o `Down/Up`, la entrada/salida se sintetiza
  geometricamente desde el punto inicial, el radio de herramienta y el
  `radius_multiplier`. Esto cubre los subcasos `Arco/Linea EnCota` y
  `Arco/Linea BajadaSubida`.
- Se agrego soporte para polilineas cerradas `ClosedPolylineMidEdgeStart`
  fuera de `E001`, manteniendo `E001` en la familia de perfil ya existente. En
  `Center`, la entrada/salida se calcula sobre la tangente inicial; en
  `Right/Left` con PH5 se usan las primitivas del toolpath para emitir esquinas
  `G2/G3`. Validacion exacta: `Pieza_037..046` y `Pieza_080..083`.
- Barrido actualizado de `Pieza*.pgmx` contra `pieza*.iso`: 82 pares exactos,
  23 `Sin candidato` y 0 diferencias linea-a-linea. Los pendientes son
  `Pieza`, `Pieza_000`, `Pieza_002`, `Pieza_003`,
  `Pieza_004_Repeticiones`, `Pieza_005..011`, `Pieza_035`, `Pieza_036`,
  `Pieza_076..079` y `Pieza_087..091`.
- Se agrego soporte para polilineas abiertas router `OpenPolyline` con
  estrategia PH5 `UnidirectionalMillingStrategySpec` /
  `BidirectionalMillingStrategySpec` en `Center`, tomando la trayectoria
  compensada del `TrajectoryPath` y evitando repetir `Z` en movimientos XY
  cuando Maestro no la emite. Validacion exacta: `Pieza_035` y `Pieza_036`.
- Para `OpenPolyline` `Center` sin estrategia y con acercamiento/alejamiento
  `Line/Arc` en modos `Quote` o `Down/Up`, la entrada/salida se sintetiza
  geometricamente desde la tangente inicial/final, el radio de herramienta y el
  `radius_multiplier`. Validacion exacta: `Pieza_076..079`.
- Se agrego soporte para ranuras `SlotSide` superiores con sierra vertical
  `082`. La preparacion usa el cabezal de sierra observado (`?%ETK[6]=82`,
  `S4000M3`, `?%ETK[1]=16`) y offsets del spindle embebido; el offset `Y`
  incorpora el radio efectivo de sierra (`tool_width / 2`). La traza entra por
  `X` maximo y corta hacia `X` minimo, como Maestro. Validacion exacta:
  `Pieza_006..011` y `Pieza_087..091`.
- Barrido actualizado de `Pieza*.pgmx` contra `pieza*.iso`: 99 pares exactos,
  6 `Sin candidato` y 0 diferencias linea-a-linea. Los pendientes son
  `Pieza`, `Pieza_000`, `Pieza_002`, `Pieza_003`,
  `Pieza_004_Repeticiones` y `Pieza_005`.
- Se agrego soporte para secuencias de taladros laterales D8 en varias caras
  y repeticiones del mismo spindle. El emisor distingue primer taladro, cambio
  de cara, cambio de mascara `ETK[0]`, repeticion de spindle y reset final.
  Validacion exacta: `Pieza_002` y `Pieza_003`.
- Se agrego expansion de patrones `ReplicateFeature` rectangulares para
  taladros superiores y laterales. Cada punto repetido entra al modelo como una
  etapa de taladro real, conservando el diferencial incremental entre puntos.
  Validacion exacta: `Pieza_004_Repeticiones` y `Pieza_005`.
- Se agrego emision para programas sin mecanizados, con dos variantes
  observadas: programa vacio con `Xn` explicito (`Pieza`) y programa vacio sin
  cierre `Xn` en el `.pgmx` (`Pieza_000`).
- Barrido final de `Pieza*.pgmx` contra `pieza*.iso`: 105 pares exactos,
  0 `Sin candidato`, 0 diferencias linea-a-linea y 0 ISO faltantes.
- En el corpus real `Cocina` (`S:\Maestro\Projects\ProdAction\ISO\Cocina`
  contra `P:\USBMIX\ProdAction\ISO\Cocina`) se paso de 0/84 exactos a
  48/84 exactos, con 0 `Sin candidato` y 0 ISO faltantes. Los primeros cierres
  exactos nuevos incluyen `Aplicados/Frente_Aplicado 1450x873`,
  `Aplicados/Lat_Aplicado 873x800`, `Estante`, `Fondo`, `Puertita_izquierda`,
  `Faja frontal` y `Tapa` de torre.
- Correcciones confirmadas en esa tanda:
  - Los acercamientos/alejamientos de perfil E001 ahora usan primitivas reales
    `Approach` y `Lift` leidas del PGMX; si el PGMX trae un arco degenerado
    con radio cero, se vuelve al calculo anterior para no abortar.
  - El cierre `Xn` usa `program_close_x/program_close_y` leidos del PGMX tambien
    para cierres no-router cuando Maestro los emite.
  - `%Or[0].ofX/ofZ` usa escalado con precision `float32`, igual que Maestro.
  - Los bloques mixtos ya tienen transiciones incrementales observadas para
    `router -> top`, `router -> side`, `top -> side` y `top -> slot`.
  - Los taladros superiores en secuencias mixtas se ordenan desde las
    coordenadas PGMX con recorrido por columnas en serpiente; los laterales
    ordenan por cara y coordenada fija dentro del bloque.
  - `line_milling` y `slot_milling` ya no toman `tool_offset_length` del estado
    final del programa: la traza usa el offset requerido de su propia operacion.
- Pendiente especifico de `Cocina`: quedan 36 diferencias concentradas en
  `fajx`, laterales con reordenamiento de grupos `side/top`, transiciones
  `profile/line` de router-router y algunos bloques top con recorrido no
  rectangular.
- Avance del 2026-05-08 sobre `Cocina`:
  - Se cerro el primer `fajx` pendiente:
    `mod 1 - bajo 1 puerta IZQ/fajx 414` compara exacto
    (`369 vs 369 lineas`, `0 diferencias`).
  - La correccion no fue de coordenadas: se modelo el orden de vecindades
    mixtas `side -> top -> side` para una misma cara lateral, moviendo primero
    el bloque lateral de mayor alcance cuando Maestro lo ejecuta antes del
    bloque superior.
  - Se agrego la transicion incremental `side_drill -> top_drill`, el `G53 Z`
    lateral por formula de maquina (`DZ_cabecera + 2*SecurityDistance +
    max(SHF_Z lateral involucrado)`) y el prefijo de cierre lateral observado
    para cierre explicito `Xn` desde `Right`. La correccion del mismo dia
    reemplazo los valores constantes `149.*` por lectura de
    `Programaciones.settingsx` y `SHF_Z` de los spindles laterales.
  - Validacion especifica sobre
    `side_g53_z_fixtures_2026-05-03`: las secuencias `G53 Z` normalizadas
    coinciden en `20/20` fixtures. Los grupos A emiten `156.500/156.450` y los
    grupos B emiten `164.500/164.450`, siguiendo el cambio de `DZ_cabecera`.
  - Validacion despues del cambio: corpus raiz `Pieza*` queda `105/105`
    exacto; corpus `Cocina` queda `55/84` exacto, con `29` diferencias
    restantes, `0` ISO faltantes y `0` candidatos faltantes.

Avance del 2026-05-09 sobre `Cocina`:

- Se cerro `mod 1 - bajo 1 puerta IZQ/Lado_derecho.pgmx`: compara exacto
  contra Maestro (`499 vs 499 lineas`, `0 diferencias`).
- La primera correccion fue una transicion router-router con la misma
  herramienta (`profile_milling -> line_milling`): Maestro conserva `G17`,
  `MLV=2` y el estado router, eleva desde el ultimo punto emitido y entra al
  siguiente toolpath sin reset completo ni cambio `T/M06`.
- `line_milling_trace` ya toma `side_of_feature`, estrategia y parametros de
  acercamiento/alejamiento del trabajo actual, no del estado final del programa.
  Esto evita que trabajos posteriores contaminen la compensacion `G41/G42`.
- El ordenamiento de bloques `Top Drill` ahora elige la serpentina mas corta
  entre columnas y bandas horizontales. Esto reproduce los bloques no
  rectangulares de `Lado_derecho` sin romper el corpus raiz.
- La sierra `082` ya modela `maquina.boring_head_speed` como las brocas: solo
  emite `?%ETK[17]=257` + `S...M3` cuando cambia la velocidad activa. En la
  secuencia `Top Drill 002 -> SlotSide 082`, ambos quedan a `4000`, por lo que
  Maestro no repite la activacion.
- Se agrego transicion incremental `slot_milling -> top_drill`: reset parcial
  de ranura, limpieza de `ETK[1]` y preparacion del siguiente taladro superior
  sin cierre final de slot.
- Validacion despues del cambio: corpus raiz `Pieza*` queda `105/105` exacto;
  corpus `Cocina` queda `59/84` exacto, con `25` diferencias restantes,
  `0` ISO faltantes y `0` candidatos faltantes.

Avance registrado el 2026-05-10:

- Se preparo la tanda controlada `Pieza_098..Pieza_102` para estudiar
  `T-BH-002` (`top drill -> side drill`) cuando vuelva a estar disponible el
  postprocesado manual en Maestro/CNC.
- Los PGMX quedaron generados en `S:\Maestro\Projects\ProdAction\ISO` y el
  manifiesto en `S:\Maestro\Projects\ProdAction\ISO\Pieza_098_102_TBH002_manifest.csv`.
- Cobertura de la tanda: `Pieza_098` `Top -> Front`, `Pieza_099`
  `Top -> Right`, `Pieza_100` `Top -> Back`, `Pieza_101` `Top -> Left`, todas
  con velocidad esperada `6000 -> 6000`; `Pieza_102` controla cambio de
  velocidad `Top 002/D15 4000 -> Front 058/D8 6000`.
- Se agrego el generador reproducible
  `tools/studies/iso/tbh002_top_to_side_fixtures_2026_05_10.py`.
- Verificacion local: los cinco PGMX evaluan internamente como dos trabajos
  `top_drill -> side_drill` y el emisor candidato marca la entrada lateral con
  `incoming_transition_id=T-BH-002`. Actualizacion posterior 2026-05-11: los
  ISO `pieza_098..pieza_102` ya estan disponibles y comparan `5/5` exactos.

Avance registrado el 2026-05-10 para `T-BH-003`:

- Se amplio la serie controlada con `Pieza_103..Pieza_118`, una pieza para cada
  variante dirigida de `side drill -> side drill` entre `Front`, `Right`,
  `Back` y `Left`.
- Las primeras cuatro piezas cubren huecos consecutivos en la misma cara:
  `Front -> Front`, `Right -> Right`, `Back -> Back`, `Left -> Left`.
- Las doce restantes cubren todas las combinaciones entre caras distintas:
  `Front -> Right`, `Front -> Back`, `Front -> Left`, `Right -> Front`,
  `Right -> Back`, `Right -> Left`, `Back -> Front`, `Back -> Right`,
  `Back -> Left`, `Left -> Front`, `Left -> Right`, `Left -> Back`.
- Los PGMX quedaron generados en `S:\Maestro\Projects\ProdAction\ISO` y el
  manifiesto en
  `S:\Maestro\Projects\ProdAction\ISO\Pieza_103_118_TBH003_manifest.csv`.
- Se agrego el generador reproducible
  `tools/studies/iso/tbh003_side_to_side_fixtures_2026_05_10.py`.
- Verificacion local: los 16 PGMX evaluan como dos grupos `side_drill`; el
  segundo grupo queda con `incoming_transition_id=T-BH-003`; no hay warnings.
  Actualizacion posterior 2026-05-11: los ISO `pieza_103..pieza_118` ya estan
  disponibles y comparan `16/16` exactos.

Avance registrado el 2026-05-10 para ampliar `T-BH-001`:

- Se incorporo al plan de trabajo la continuidad `top drill -> top drill` sin
  cambio de herramienta, como subcaso de `T-BH-001`.
- En codigo, `select_transition_id` ahora clasifica todo `top_drill ->
  top_drill` como `T-BH-001`; el subcaso se decide por si la herramienta cambia
  o se conserva.
- Se preparo la tanda `Pieza_119..Pieza_122`: `001/D8` en fila, `001/D8` en
  columna, `001/D8` repetido tres veces y `002/D15` a `4000`.
- Los PGMX quedaron generados en `S:\Maestro\Projects\ProdAction\ISO` y el
  manifiesto en
  `S:\Maestro\Projects\ProdAction\ISO\Pieza_119_122_TBH001_same_tool_manifest.csv`.
- Se agrego el generador reproducible
  `tools/studies/iso/tbh001_same_tool_fixtures_2026_05_10.py`.
- Verificacion local: todos los PGMX evaluan como grupos `top_drill`; las
  entradas posteriores a la primera quedan con `incoming_transition_id=T-BH-001`;
  no hay warnings. Actualizacion posterior 2026-05-11: los ISO
  `pieza_119..pieza_122` ya estan disponibles y comparan `4/4` exactos.

Avance registrado el 2026-05-11 para `T-BH-004`:

- Se analizo la matriz completa `side drill -> top drill`: cuatro caras
  laterales (`Front`, `Right`, `Back`, `Left`) por siete brocas verticales
  superiores (`001..007`), total 28 variantes.
- Las brocas laterales salen siempre de velocidad `6000`; las llegadas a
  `001`, `005`, `006` y `007` conservan `6000`, mientras que las llegadas a
  `002`, `003` y `004` prueban cambio `6000 -> 4000`.
- Se preparo la tanda `Pieza_123..Pieza_150`: `Front/Right/Back/Left` hacia
  `001`, `002`, `003`, `004`, `005`, `006` y `007`.
- Los PGMX quedaron generados en `S:\Maestro\Projects\ProdAction\ISO` y el
  manifiesto en
  `S:\Maestro\Projects\ProdAction\ISO\Pieza_123_150_TBH004_manifest.csv`.
- Se agrego el generador reproducible
  `tools/studies/iso/tbh004_side_to_top_fixtures_2026_05_11.py`.
- Verificacion local: los 28 PGMX evaluan como dos grupos `side_drill ->
  top_drill`; el segundo grupo queda con `incoming_transition_id=T-BH-004`; no
  hay warnings. El emisor candidato genera ISO para los 28 casos. Actualizacion
  posterior 2026-05-11: los ISO `pieza_123..pieza_150` ya estan disponibles y
  comparan `28/28` exactos.

Cierre registrado el 2026-05-11 para `Pieza_098..150`:

- Ya estan disponibles los ISO Maestro `pieza_098..pieza_150.iso` en
  `P:\USBMIX\ProdAction\ISO`.
- Se cerraron contra Maestro las tandas pendientes:
  - `T-BH-002` (`top drill -> side drill`): `Pieza_098..102`, `5/5` exactos.
  - `T-BH-003` (`side drill -> side drill`): `Pieza_103..118`, `16/16`
    exactos.
  - `T-BH-001` sin cambio de herramienta: `Pieza_119..122`, `4/4` exactos.
  - `T-BH-004` (`side drill -> top drill`): `Pieza_123..150`, `28/28`
    exactos.
- El emisor ahora usa reset parcial del cabezal de perforacion/ranurado en
  transiciones mixtas internas: no cierra con `G61`, `?%ETK[0]=0`,
  `?%ETK[17]=0`, `G4F1.200`, `M5` ni `D0` cuando el siguiente trabajo sigue en
  el mismo cabezal.
- Para `T-BH-003` aislado, el marco lateral se restaura segun cara saliente y
  cara entrante; las transiciones aisladas de dos laterales hacia o desde
  `Back/Left` usan la cota fija espejo necesaria para reproducir Maestro sin
  alterar bloques laterales largos.
- Validacion de regresion en ese punto: corpus raiz `Pieza*.pgmx` con ISO
  Maestro disponible quedo `157/157` exacto; `Cocina` se conservo en `59/84`
  exactos.

Avance registrado el 2026-05-11 para `T-BH-007` y `T-BH-008`:

- Se preparo la tanda controlada `Pieza_151..Pieza_158` para estudiar las
  transiciones internas pendientes con sierra vertical:
  - `T-BH-007` (`side drill -> top slot`): `Pieza_151..154`, una por cada cara
    lateral `Front/Right/Back/Left`, con cambio esperado `6000 -> 4000`.
  - `T-BH-008` (`top slot -> side drill`): `Pieza_155..158`, una por cada cara
    lateral `Front/Right/Back/Left`, con cambio esperado `4000 -> 6000`.
- Los PGMX quedaron generados en `S:\Maestro\Projects\ProdAction\ISO` y el
  manifiesto en
  `S:\Maestro\Projects\ProdAction\ISO\Pieza_151_158_TBH007_008_manifest.csv`.
- Se agrego el generador reproducible
  `tools/studies/iso/tbh007_008_side_slot_fixtures_2026_05_11.py`.
- Verificacion local: `Pieza_151..154` evaluan como
  `side_drill -> slot_milling` con `incoming_transition_id=T-BH-007`;
  `Pieza_155..158` evaluan como `slot_milling -> side_drill` con
  `incoming_transition_id=T-BH-008`; no hay warnings y el emisor candidato
  genera ISO preliminar para los 8 casos. Actualizacion posterior 2026-05-11:
  los ISO `pieza_151..pieza_158` ya estan disponibles y comparan `8/8`
  exactos.

Avance registrado el 2026-05-11 para `T-XH-001` y `T-XH-002`:

- Se preparo la tanda controlada `Pieza_159..Pieza_164` para estudiar cambios
  entre cabezal router y cabezal de perforacion/ranurado:
  - `T-XH-001` (`router -> boring head`): `Pieza_159` (`line_milling ->
    top_drill`), `Pieza_160` (`line_milling -> side_drill`) y `Pieza_161`
    (`line_milling -> slot_milling`).
  - `T-XH-002` (`boring head -> router`): `Pieza_162` (`top_drill ->
    line_milling`), `Pieza_163` (`side_drill -> line_milling`) y `Pieza_164`
    (`slot_milling -> line_milling`).
- Los PGMX quedaron generados en `S:\Maestro\Projects\ProdAction\ISO` y el
  manifiesto en
  `S:\Maestro\Projects\ProdAction\ISO\Pieza_159_164_TXH001_002_manifest.csv`.
- Se agrego el generador reproducible
  `tools/studies/iso/txh001_002_router_boring_fixtures_2026_05_11.py`.
- Verificacion local: las piezas evaluan como dos grupos con el
  `incoming_transition_id` esperado (`T-XH-001` en `Pieza_159..161` y
  `T-XH-002` en `Pieza_162..164`); no hay warnings y el emisor candidato
  genera ISO preliminar para los 6 casos. Actualizacion posterior 2026-05-11:
  los ISO `pieza_159..pieza_164` ya estan disponibles y comparan `6/6`
  exactos.

Cierre registrado el 2026-05-11 para `Pieza_151..164`:

- Ya estan disponibles los ISO Maestro `pieza_151..pieza_164.iso` en
  `P:\USBMIX\ProdAction\ISO`.
- Se cerraron contra Maestro las cuatro transiciones pendientes:
  - `T-BH-007` (`side drill -> top slot`): `Pieza_151..154`, `4/4` exactos.
  - `T-BH-008` (`top slot -> side drill`): `Pieza_155..158`, `4/4` exactos.
  - `T-XH-001` (`router -> boring head`): `Pieza_159..161`, `3/3` exactos.
  - `T-XH-002` (`boring head -> router`): `Pieza_162..164`, `3/3` exactos.
- Reglas nuevas codificadas:
  - `side drill -> top slot` conserva el cabezal compartido, emite pausa
    lateral si viene otro trabajo, retorna a Top con reset parcial y, desde
    `Back/Left`, restaura marco lateral derecho antes de `?%ETK[8]=1`.
  - `top slot -> side drill` usa reset parcial de sierra, limpia `?%ETK[1]` y
    prepara lateral sin cierre completo del cabezal.
  - `router -> boring head` distingue `line_milling` inicial de router previo
    encadenado: la seleccion `?%ETK[8]=1/G40` se conserva cuando el router
    saliente ya venia de otra transicion router, pero no en el fixture aislado
    `line_milling -> top_drill`.
  - `boring head -> router` emite limpieza segun familia saliente y preparacion
    router incremental sin recomponer el marco completo.
- Validacion de regresion actualizada: corpus raiz `Pieza*.pgmx` queda
  `171/171` exacto; `Cocina` mejora a `61/84` exactos.

Avance registrado el 2026-05-11 para `T-XH-002` con `OpenPolyline`:

- Se volco al emisor el cierre de la serie controlada `Pieza_192..208`, que
  aisla `top_drill -> OpenPolyline E001` con router previo opcional,
  compensacion `Right/Left/Center`, approach/retract `Arc Down/Up` y controles
  sin approach/retract.
- El doble `?%ETK[7]=0` antes de volver al router quedo modelado como regla de
  entrada a `OpenPolyline`: se emite cuando `SideOfFeature` es `Left/Right` o
  cuando `Center` mantiene approach/retract activo; no se emite para `Center`
  sin approach/retract.
- La preparacion `boring head -> router` ahora distingue:
  - `?%ETK[6]=1` se emite al volver de brocas superiores distintas de `001`;
  - `?%ETK[9]=n` se omite cuando un router previo ya habia seleccionado la
    misma herramienta;
  - el orden confirmado es `?%ETK[6]=1`, luego `?%ETK[9]=n` cuando ambas lineas
    aplican.
- La traza `OpenPolyline` ahora separa compensacion CNC de trayectoria:
  `Right -> G42 ... G40`, `Left -> G41 ... G40`, `Center` sin
  `G41/G42/G40`. Las `OpenPolyline` que salen del rectangulo nominal de la
  pieza repiten `Z` en los segmentos de corte; las internas conservan `Z`
  modal.
- Se ajusto la seleccion `?%ETK[8]=1/G40` en `router -> top_drill` para no
  romper la tanda controlada `Pieza_192..208` y conservar el caso real de
  perfil de Cocina que empieza sobre el borde superior.
- Validacion especifica: `Pieza_192..208` compara `17/17` exacto contra
  Maestro.
- Validacion de regresion raiz: `Pieza*.pgmx` con ISO disponible queda
  `210/215` exacto. Los residuales son `Pieza_181..185`, con diferencias
  geometricas de 1 mm en una tanda de perfil previa a este cierre.
- Validacion de `Cocina` tras este avance: `47/84` exactos, con diferencias
  abiertas fuera de la regla controlada de `OpenPolyline`.

## Preguntas Abiertas

- Que variables observadas son realmente estado modal y cuales son solo
  comandos repetidos por seguridad.
- Que resets dependen de la familia de herramienta y cuales dependen de la
  etapa exacta ejecutada.
- Como convertir un `StateValue.required=True` en una linea ISO concreta sin
  perder la explicacion de fuente.
- Como distinguir entre posicion fisica conocida y posicion logica suficiente
  para emitir el proximo bloque.
- Que nivel de detalle del `.pgmx` conviene conservar crudo para no perder
  evidencia.
- Como registrar una regla que funciona para el corpus actual pero todavia no
  esta demostrada causalmente.
- Si conviene incorporar al snapshot de `iso_state_synthesis` una copia
  controlada de los esquemas `XISO*.xsd` del arbol instalado de Xilog Plus.

## Recordatorio De Seguridad PGMX

- El sintetizador/conversor ISO debe describir y reproducir lo que trae el
  `.pgmx` sin imponer politica de uso de herramienta. La responsabilidad de
  elegir una fresa valida para el trabajo queda fuera de la conversion.
- Al final de esta investigacion, ningun trabajo del conversor ISO debe quedar
  asociado a una herramienta o grupo de herramientas en particular. Cuando se
  escriba `perfil E001`, `polilinea E003/E004`, `Line E004` o una frase similar,
  debe leerse como evidencia historica del caso que permitio inferir la regla,
  no como frontera de soporte final. La regla estable debe describir geometria,
  operacion, compensacion, trayectoria, estado y datos de herramienta leidos del
  `.pgmx`.
- La generacion automatica de `.pgmx` si debe incorporar reglas adicionales de
  seguridad antes de producir archivos operativos. La intencion de esas reglas
  es evitar que un ISO convertido desde un `.pgmx` generado automaticamente
  pueda causar danos en la maquina.
- Esas reglas deberan validarse por familia de operacion, herramienta,
  profundidad, compensacion, acercamiento/alejamiento, plano, limites de pieza,
  colisiones posibles, velocidades/avances y cualquier estado modal que pueda
  dejar a la maquina en una condicion peligrosa.
- Mantener separadas estas dos politicas: conversion de `.pgmx` existente
  contra Maestro como evidencia; generacion automatica de `.pgmx` con guardas
  preventivas propias.
- El experimento de piezas espejo por herramienta quedo en
  `iso_state_synthesis/experiments/007_router_tool_mirror_fixtures_plan.md`.
  Sirve para confirmar con Maestro la generalizacion `E00x` del fresado
  lineal/contorno. La carpeta generada de trabajo es
  `S:\Maestro\Projects\ProdAction\ISO\router_tool_mirror_fixtures_2026-05-07`.

## Plan Tentativo

1. Revisar y aprobar esta memoria como contrato inicial.
2. Armar el primer experimento manual de tabla de estados.
3. Definir el formato de evidencia y de tabla antes de escribir codigo.
4. Crear la primera estructura interna del entorno. Hecho: paquete
   `iso_state_synthesis` con modelo, adaptador PGMX y CLI.
5. Implementar lectura de evidencia sin emitir ISO. Primer paso hecho para el
   fixture minimo de taladro superior.
6. Implementar calculo de estados objetivo para un caso minimo. Primer paso
   hecho para cabecera, preambulo, preparacion/traza/reset de top drill.
7. Implementar el diferencial y comparar contra Maestro solo para ese caso.
   Primer paso hecho: se calcula el diferencial interno por etapa, todavia sin
   comparador linea-a-linea contra Maestro.
8. Ampliar por capas de estado, no por combinaciones de mecanizados.

## Pendiente Inmediato

- Mantener como hipotesis pendientes las repeticiones `ETK[8]/G40` y resets
  `G61/G64/SYN` hasta que una variante nueva los explique.
- Avance registrado el 2026-05-12: se recupero la regla de seleccion de cara
  superior en las transiciones desde perfiles router reales hacia taladro
  superior, y en el retorno posterior desde taladro superior a router cuando
  hereda esa misma condicion del perfil previo. La condicion observada que no
  rompe las piezas sinteticas es: perfil cerrado sin desplazamiento extra de
  salida (`leadout == exit`) o primer punto del contorno sobre el borde superior
  de pieza. La serie sintetica `Pieza_190/191/193/198` queda protegida porque
  conserva el desplazamiento extra de salida donde Maestro no emite
  `?%ETK[8]=1/G40`.
- Validacion posterior al avance 2026-05-12:
  - `Cocina`: `65/84` exactos; se supera el piso previo `61/84`.
  - Corpus raiz `Pieza*`: `210/215` exactos; siguen fuera solo
    `Pieza_181..185` por la diferencia geometrica previa.
  - Controles puntuales exactos: `mod 1 - bajo 1 puerta IZQ/Puertita_izquierda`,
    `Pieza_190`, `Pieza_191`, `Pieza_193` y `Pieza_198`.
- Analisis manual posterior, sin tocar codigo: los `19` residuales de `Cocina`
  se agrupan en cinco frentes, no en una sola transicion:
  - `9` casos de ordenamiento de taladros superiores: aplicar/estudiar
    `B-BH-001/002/003`, `T-XH-001` y `T-BH-001`. Maestro mezcla brocas
    `005/002/001` por recorrido espacial; el candidato todavia conserva un
    orden que a veces prioriza herramienta o recorrido incorrecto. Punto de
    decision: `iso_state_synthesis/pgmx_source.py::_ordered_top_drill_block`.
  - `7` casos de traza router incremental: aplicar/estudiar `B-RH-002` con
    `T-RH-001`. En algunas entradas sobra `MLV=2` tras `G17`; en otras falta
    repetir `Z` en el tramo largo de corte. Punto de decision:
    `iso_state_synthesis/emitter.py::_emit_line_milling_trace`.
  - `1` caso de ordenamiento de laterales: aplicar/estudiar `B-BH-005` y
    posiblemente `T-BH-003`. Maestro no ejecuta todo `Back` y luego todo
    `Front`; parte el bloque para optimizar recorrido. Punto de decision:
    `iso_state_synthesis/pgmx_source.py::_ordered_side_drill_block`.
  - `1` caso de traza de sierra vertical: aplicar/estudiar `B-BH-007`; Maestro
    hace una salida con `G0 Z20` donde el candidato la mantiene como `G1`.
    Punto de decision: `iso_state_synthesis/emitter.py::_emit_slot_milling_trace`.
  - `1` caso `side_drill -> router`: aplicar/estudiar `T-XH-002`; Maestro
    restaura marco lateral antes de volver a Top/router, mientras el candidato
    selecciona Top demasiado temprano. Punto de decision:
    `iso_state_synthesis/emitter.py::_emit_boring_to_router_transition`.
- Proximo paso recomendado: no avanzar automaticamente. Primero armar una mini
  tanda aislada de ordenamiento `top_drill` mixto (`005/002/001`), con perfil
  router previo y sin perfil router previo. Si Maestro confirma la hipotesis,
  aplicar una regla reusable de ordenamiento antes de tocar el emisor.
- Avance 2026-05-13: se agrego la mini tanda reproducible de ordenamiento
  `top_drill` mixto en
  `tools/studies/iso/top_drill_ordering_fixtures_2026_05_13.py` y la ficha
  `iso_state_synthesis/experiments/009_top_drill_ordering_fixtures.md`.
  Genera `Pieza_209..214` con huecos `005/002/001`, orden fuente mezclado o
  inverso, y contextos sin router previo, con linea previa y con perfil previo.
  El script tambien puede analizar `pieza_209..214.iso` cuando Maestro los haya
  postprocesado. No se debe tocar `_ordered_top_drill_block` hasta leer esa
  comparacion.
- Resultado 2026-05-13 de `Pieza_209..214`: Maestro conservo el orden fuente
  del `.pgmx` en `6/6` casos. En `209..210`, el candidato ya coincidia porque
  no reordena archivos solo `top_drill`; en `211..214`, el candidato actual
  falla porque reordena el bloque superior al haber router previo. Se probo
  localmente preservar orden fuente de forma global: la mini tanda quedaba
  `6/6`, la matriz raiz `Pieza*` quedaba `217/222` con residuales `181..185`,
  pero `Cocina` caia a `30/84`. Ese cambio no se conserva. La regla queda
  abierta. Estado estable posterior: `Pieza* 213/222` exactos, con residuales
  `181..185` y `211..214`; `Cocina 65/84` exactos. Antes de tocar
  `_ordered_top_drill_block`, comparar el orden de
  `WorkingStep` crudo contra el orden ISO en una pieza residual real de
  `Cocina` para detectar que metadato distingue PGMX sinteticos de PGMX reales.
- Seguimiento 2026-05-13 con Cazaux: se agrego
  `tools/studies/iso/top_drill_corpus_order_analysis_2026_05_13.py` y la ficha
  `iso_state_synthesis/experiments/010_top_drill_cazaux_corpus.md`. El corpus
  `S:\Maestro\Projects\ProdAction\Prod 26-01-01 Cazaux` tiene `104/104` pares
  PGMX/ISO contra `P:\USBMIX\ProdAction\Prod 26-01-01 Cazaux`. En los `60`
  casos comparables de top drill, el orden crudo del PGMX coincide `0/60` y la
  regla candidata coincide `58/60`; los `34` `count_mismatch` quedan fuera de
  la decision de orden. Todos los casos Cazaux con top drill tienen
  `top_tool_key_mode=auto`, a diferencia de `Pieza_209..214`, que usan
  `ToolKey` explicito.
- Regla aplicada 2026-05-13: `_ordered_top_drill_block` conserva el orden fuente
  cuando todos los pasos del bloque tienen `Operation.ToolKey.name` explicito;
  si el bloque viene automatico/embebido, usa vecino mas cercano desde la menor
  coordenada `(X,Y)`. Validacion despues del cambio: `Pieza_209..214` `6/6`,
  matriz raiz `Pieza*` `217/222`, `Cocina` `68/84`, Cazaux completo `62/104`.
  Los dos residuales de orden Cazaux son `Cocina\mod 8 - Abierto\Lat_Der.pgmx`
  y `Cocina\mod 8 - Abierto\Lat_Izq.pgmx`; parecen requerir una regla
  secundaria de arranque, no cambiar la regla general.
- Seguimiento 2026-05-13 por bloques/transiciones: se agrego
  `tools/studies/iso/block_transition_corpus_analysis_2026_05_13.py` y
  `iso_state_synthesis/experiments/011_block_transition_cazaux_strategy.md`.
  El clasificador usa las explicaciones del emisor (`stage_key`, `block_id`,
  `transition_id`) para ubicar la primera diferencia significativa. Separando
  deltas menores de cabecera `%Or`, Cazaux queda `62` exactos, `20`
  `header_only` y `22` residuales operativos. Frentes operativos: `B-RH-002`
  `9`, `T-XH-001` `4`, `B-BH-005` `3`, `B-BH-007` `3`, `B-BH-002` `2` y
  `T-XH-002` `1`. Orden recomendado: primero `B-RH-002`
  (`_emit_line_milling_trace`), luego `T-XH-001`
  (`_emit_top_drill_prepare_after_router`), despues `B-BH-007`, `B-BH-005`,
  `B-BH-002` residual y `T-XH-002`.
- Mejora 2026-05-13 de `B-RH-002`: se agrego la ficha
  `iso_state_synthesis/experiments/012_b_rh_002_cazaux_router_trace.md` y se
  ajusto `iso_state_synthesis/emitter.py::_emit_line_milling_trace`. Maestro
  conserva `MLV=2` en `profile_milling -> line_milling`, pero lo omite en
  `line_milling -> line_milling`; ademas, las `OpenPolyline` compensadas
  repiten `Z` cuando salen del rectangulo nominal o cuando el corte es
  superficial (`cut_z > -pieza.depth`). Validacion Cazaux: `65` exactos, `21`
  `header_only`, `18` residuales operativos, con `B-RH-002` bajando de `9` a
  `0` como primer frente. La nueva prioridad queda en `T-XH-001`
  (`5/18` residuales).
- Mejora 2026-05-13 de `T-XH-001`: se agrego
  `tools/studies/iso/txh001_transition_audit_2026_05_13.py` y la ficha
  `iso_state_synthesis/experiments/013_txh001_cazaux_transition_audit.md`.
  La lista base de Cazaux tiene `71` candidatos con `T-XH-001`: `33` exactos,
  `20` `header_only`, `13` con otros frentes y `5` con diferencia propia de
  `T-XH-001`. Se ajusto
  `iso_state_synthesis/emitter.py::_emit_top_drill_prepare_after_router` para
  reactivar `?%ETK[17]=257`/`S...M3` cuando la entrada a `top_drill` viene de
  `line_milling` y el diferencial no trae cambio explicito de `etk_17`. Lista
  posterior: `33` siguen exactos, `20` siguen `header_only`, `13` quedan sin
  cambio en otros frentes, `5` despejan `T-XH-001` hacia el siguiente frente y
  `0` empeoran. El corpus completo queda `65` exactos, `21` `header_only`,
  `18` residuales; primeros frentes: `B-BH-007` `8`, `T-XH-002` `5`,
  `B-BH-005` `3`, `B-BH-002` `2`. Validacion ampliada: raiz `Pieza*`
  estable en `217/222`; `ISO\Cocina` sube de `68/84` a `72/84`.
