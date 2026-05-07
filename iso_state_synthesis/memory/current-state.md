# ISO State Synthesis

Nueva memoria de trabajo para redisenar la generacion ISO desde cero sin
arrastrar la arquitectura por patrones de `iso_generation/`.

Ultima actualizacion: 2026-05-07

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
- Seguir con los `Pieza*` sin candidato, priorizando los subcasos de fresado
  mas cercanos al soporte actual: circulos E004 con PH5/helicoidal,
  polilineas cerradas E003/E004 y variantes con leads `Line/Arc`.
