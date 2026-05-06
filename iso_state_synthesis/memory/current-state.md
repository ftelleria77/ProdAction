# ISO State Synthesis

Nueva memoria de trabajo para redisenar la generacion ISO desde cero sin
arrastrar la arquitectura por patrones de `iso_generation/`.

Ultima actualizacion: 2026-05-06

## Alcance

- Dejar `iso_generation/` como esta.
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
- Extender el emisor general a multiples trabajos usando el mismo diferencial
  de `maquina.boring_head_speed`; el emisor candidato actual sigue acotado al
  fixture minimo Top Drill.
