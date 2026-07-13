# Memoria Temporal De Modularizacion Del Sintetizador PGMX

Estado: abierta, 2026-06-02.

Esta memoria registra la discusion modulo por modulo antes de escribir codigo.
Sirve como borrador operativo para implementar la modularizacion definida en
`docs/pgmx_synthesis_modularization_plan.md`.

Regla de uso:

- Cada item discutido se agrega aqui antes de tocar el codigo correspondiente.
- Las aclaraciones del usuario deben corregir esta memoria antes de ejecutar la
  migracion.
- El plan estable vive en `docs/pgmx_synthesis_modularization_plan.md`; esta
  memoria puede contener decisiones parciales, puntos abiertos y ajustes de
  alcance.

## Item 1 - Alcance Propuesto Para `pgmx.synthesis.__init__`

Fecha: 2026-06-03

Modulo objetivo:

- `pgmx/synthesis/__init__.py`

Rol propuesto:

- Ser la API publica estable del sintetizador.
- Reexportar contratos y builders sin exponer la organizacion interna como
  obligatoria para usuarios actuales.

Responsabilidades incluidas:

- Mantener imports historicos:
  - specs;
  - builders;
  - `build_synthesis_request(...)`;
  - `synthesize_request(...)`;
  - constantes publicas necesarias.
- Documentar version/superficie publica cuando corresponda.
- Delegar internamente hacia `common`, `milling` y `drilling`.

Responsabilidades excluidas:

- No debe contener logica productiva.
- No debe importar laboratorios.
- No debe forzar a usuarios a depender de `core.py`.

Criterio de migracion:

1. Mantener compatibilidad exacta mientras se mueven modulos.
2. Cambiar imports internos por reexports desde destino final.
3. Agregar smoke imports para detectar regresiones de fachada.

## Item 2 - Alcance Propuesto Para `pgmx.synthesis.core`

Fecha: 2026-06-03

Modulo objetivo:

- `pgmx/synthesis/core.py`

Rol propuesto:

- Ser una fachada interna temporal durante la migracion.
- Reducirse progresivamente a compatibilidad o desaparecer si deja de cumplir
  un rol real.

Responsabilidades incluidas durante la transicion:

- Reexportar nombres historicos.
- Mantener wrappers finos si son necesarios para no romper imports.
- Servir como punto de traslado controlado mientras se extrae una familia por
  vez.

Responsabilidades excluidas:

- No debe recibir logica nueva de mecanizados.
- No debe mantener dependencias productivas hacia laboratorios.
- No debe seguir acumulando helpers comunes una vez que existan en
  `common.*`.

Criterio de migracion:

1. Extraer comunes.
2. Extraer familias.
3. Convertir `core.py` en wrappers/reexports.
4. Eliminarlo o conservarlo solo si hay una razon de compatibilidad clara.

## Item 3 - Alcance Propuesto Para `pgmx.synthesis.common.program`

Fecha: 2026-06-03

Modulo objetivo:

- `pgmx/synthesis/common/program.py`

Rol propuesto:

- Ser el modulo transversal de orquestacion del sintetizador PGMX.
- Contener el estado de programa/pieza necesario para escribir el archivo
  final, sin pertenecer a una familia de mecanizado.
- Coordinar baseline, request, orden de mecanizados, hidratacion, reserva de
  IDs, insercion de features/operaciones/working steps y escritura del
  contenedor `.pgmx`.

Responsabilidades incluidas:

- Contratos de flujo:
  - `PgmxState`;
  - `PgmxSynthesisRequest`;
  - `PgmxSynthesisResult`;
  - `MachiningSpec`;
  - `build_synthesis_request(...)`;
  - `synthesize_request(...)`.
- Lectura y mezcla del estado de pieza:
  - nombre de pieza;
  - dimensiones;
  - origen;
  - `execution_fields`;
  - `PieceGeometry` desde `common.piece`.
- Orquestacion de mecanizados:
  - secuencia explicita por `ordered_machinings`;
  - secuencias historicas por listas separadas;
  - `machining_order`;
  - `XnSpec` como dato de programa, no como mecanizado con laboratorio propio.
- Coordinacion con `common.hydration` para decidir que specs se escriben por
  generacion pura y cuales reutilizan serializacion exacta.
- Coordinacion con modulos de familia para:
  - normalizar specs;
  - construir XML de feature/operacion/working step;
  - validar restricciones de programa y pieza.
- Escritura final:
  - carga del baseline;
  - reemplazo/actualizacion de nodos productivos;
  - empaquetado `.pgmx`;
  - preservacion de entradas no tocadas del contenedor.

Responsabilidades excluidas:

- No debe conocer detalles internos de cada mecanizado mas alla de su contrato
  publico y hooks de escritura.
- No debe implementar geometria, estrategias, leads, herramientas ni
  profundidad; debe delegar en `common.*` y en los modulos de familia.
- No debe depender de `machining_lab`.
- No debe mantener reglas historicas de `Vaciado`; esas reglas migran a
  `milling.pocket`.
- No debe ser API publica definitiva si `pgmx.synthesis.__init__` puede
  exponer una superficie mas estable.

Relaciones:

- `common.xml` provee helpers de nodos, namespaces e IDs.
- `common.piece` provee geometria/datos de pieza.
- `common.hydration` provee lectura de templates.
- `milling.*` y `drilling.*` proveen hooks por familia.
- `pgmx.synthesis.core` puede reexportar temporalmente esta funcionalidad
  durante la migracion.

Criterio de migracion:

1. Extraer dataclasses de estado/request/resultado y union `MachiningSpec`.
2. Extraer funciones de carga/escritura de contenedor que no sean XML atomico.
3. Definir una interfaz simple para que cada modulo de familia agregue su
   mecanizado al programa.
4. Mantener `build_synthesis_request(...)` y `synthesize_request(...)`
   accesibles desde `pgmx.synthesis`.
5. Validar orden de mecanizados, contenedor de salida y smoke imports de
   fachadas publicas.

Puntos abiertos:

- Definir si `PgmxState` conserva ese nombre o si se expone como `PieceState`
  mas `ProgramState`.
- Definir cuanto de la escritura final queda en `common.program` y cuanto en
  un futuro modulo de salida.

## Item 4 - Alcance Propuesto Para `pgmx.synthesis.common.xml`

Fecha: 2026-06-02

Modulo objetivo:

- `pgmx/synthesis/common/xml.py`

Rol propuesto:

- Centralizar las utilidades XML comunes del sintetizador PGMX.
- Ser la capa de bajo nivel para crear nodos Maestro, nombres calificados,
  namespaces, referencias por ID y serializaciones XML reutilizables.
- Evitar que cada familia de mecanizado vuelva a definir helpers propios para
  `ElementTree`, `xmlns`, `i:nil`, `i:type`, claves y referencias.

Responsabilidades incluidas:

- Constantes de namespaces Maestro ya usadas por el sintetizador:
  `PGMX_NS`, `XSI_NS`, `BASE_MODEL_NS`, `MILLING_NS`, `DRILLING_NS`,
  `PATTERNS_NS`, `GEOMETRY_NS`, `STRATEGY_NS`, `UTILITY_NS`, `XSD_NS`,
  `ARRAYS_NS` y `PARAMETRIC_NS`.
- Registro de namespaces globales de `ElementTree`.
- Helpers de nombres y nodos:
  - `_qname(...)`;
  - `_append_node(...)`;
  - `_set_xmlns(...)`;
  - construccion de nodos `nil`;
  - construccion de nodos con `i:type`.
- Helpers de referencias Maestro:
  - `Key`;
  - `ReferenceKey`;
  - referencias a `GeometryID`, `OperationIDs`, `WorkpieceID`, `ToolKey`,
    `FeatureID` y equivalentes.
- Normalizacion XML comun posterior a la escritura, especialmente donde Maestro
  exige prefijos o namespaces que `ElementTree` no conserva naturalmente.
- Serializacion numerica solo si se mantiene como detalle XML transversal; si
  la normalizacion numerica tiene reglas geometricas o de herramienta, deberia
  vivir en el modulo comun correspondiente.

Responsabilidades excluidas:

- No debe conocer familias de mecanizado (`line`, `slot`, `profile`, `circle`,
  `squaring`, `pocket`, `drilling`).
- No debe decidir profundidad, herramienta, estrategia, trayectoria ni orden de
  worksteps.
- No debe importar desde `pgmx.synthesis.milling`, `pgmx.synthesis.drilling`
  ni laboratorios. Los paquetes historicos `pgmx.vaciado` y
  `pgmx.vaciado_lab` son fuentes de migracion, no dependencias objetivo.
- No debe hidratar templates completos desde `source_pgmx_path`; eso pertenece
  a `common.hydration`.
- No debe construir features u operaciones completas; esos builders pertenecen
  a los modulos productivos por familia.

Dependencias permitidas:

- Libreria estandar: `xml.etree.ElementTree`, `re` si es necesario para
  normalizacion textual, y tipos basicos.
- Cero dependencias hacia modulos productivos de mecanizado.

Criterio de migracion:

1. Extraer primero constantes, `_qname`, `_append_node`, `_set_xmlns` y helpers
   de referencia desde `pgmx.synthesis.core` sin cambiar nombres internos.
2. Dejar reexports o imports en `core.py` para que el comportamiento siga igual.
3. Mover despues la normalizacion XML textual, con tests de snapshot/sintesis
   que prueben que la salida no cambia.
4. Recien cuando las familias esten separadas, decidir que helpers privados
   pasan a API interna estable y cuales quedan como detalle de implementacion.

Punto abierto:

- Definir si `_compact_number(...)` pertenece a `common.xml` por serializacion
  textual, o a otro modulo comun por ser regla transversal de formato numerico.

## Item 5 - Alcance Propuesto Para `pgmx.synthesis.common.geometry`

Fecha: 2026-06-02

Modulo objetivo:

- `pgmx/synthesis/common/geometry.py`

Rol propuesto:

- Centralizar el modelo geometrico reutilizable del sintetizador PGMX.
- Representar primitivas y perfiles antes de que una familia de mecanizado los
  convierta en `ManufacturingFeature`, `Operation` o `Toolpath`.
- Ser el lugar comun para lineas, arcos, puntos, perfiles compuestos, circulos,
  orientacion, bounding boxes, tangentes, reversion de perfiles y compensacion
  geometrica por lado/ancho de herramienta.

Responsabilidades incluidas:

- Dataclasses geometricas transversales:
  - `GeometryPrimitiveSpec`;
  - `GeometryProfileSpec`.
- Builders geometricos publicos o internos:
  - `build_line_geometry_primitive(...)`;
  - `build_arc_geometry_primitive(...)`;
  - `build_point_geometry_profile(...)`;
  - `build_line_geometry_profile(...)`;
  - `build_circle_geometry_profile(...)`;
  - `build_composite_geometry_profile(...)`;
  - `build_compensated_toolpath_profile(...)`.
- Operaciones reutilizables sobre perfiles:
  - calcular inicio/fin 2D y 3D;
  - obtener tangentes de entrada/salida;
  - invertir primitivas y perfiles;
  - cambiar cota Z de primitivas y perfiles;
  - calcular winding, area firmada y bounding box;
  - muestrear puntos auxiliares para arcos cuando haga falta clasificar o
    validar perfiles.
- Lectura/escritura textual de primitivas geometricas solo hasta el limite de
  `GeometryPrimitiveSpec` y `GeometryProfileSpec`. La construccion de una curva
  serializable completa no queda definida como responsabilidad de este modulo.
- Reglas geometricas transversales de compensacion:
  - offset de lineas/perfiles por `side_of_feature`;
  - compensacion de polilineas abiertas o cerradas;
  - arcos tangentes de esquinas exteriores cuando la regla sea geometrica y no
    especifica de una familia.

Responsabilidades excluidas:

- No debe crear features, operations, worksteps ni toolpaths completos.
- No debe decidir profundidad de corte ni niveles multipasada; eso pertenece a
  `common.depth` y a las estrategias/familias que consuman esos niveles.
- No debe resolver herramientas ni validar `sinking_length`; eso pertenece a
  `common.tools`.
- No debe decidir estrategia Maestro (`Unidirectional`, `Bidirectional`,
  `ContourParallel`, etc.); eso pertenece a `common.strategy` o a cada familia.
- No debe hidratar templates desde `source_pgmx_path`; solo puede parsear
  serializaciones geometricas que reciba como texto o nodo ya aislado.
- No debe depender de laboratorios (`pgmx.machining_lab` ni paquetes
  historicos de laboratorio) ni de modulos productivos de familias.

Relacion con `common.xml`:

- `common.geometry` puede usar funciones de formato y constantes XML solo si son
  necesarias para serializar una primitiva geometrica.
- La creacion de nodos XML concretos debe quedar en `common.xml` o en los
  builders de familia. `common.geometry` deberia preferir devolver specs,
  strings de serializacion o estructuras geometricas, no `ElementTree` completos.

Relacion con modulos de familia:

- `milling.line`, `milling.slot`, `milling.profile`, `milling.circle` y
  `milling.squaring` consumen este modulo para construir su geometria nominal y
  su toolpath efectivo.
- `milling.pocket` puede consumir utilidades basicas de perfiles cerrados, pero
  las reglas complejas de offset/puentes de pocket milling no deben entrar aqui
  hasta que se demuestre que son generales para otros mecanizados.
- `drilling.single` y `drilling.pattern` consumen principalmente puntos y
  referencias geometricas simples.

Criterio de migracion:

1. Extraer primero `GeometryPrimitiveSpec`, `GeometryProfileSpec` y builders
   geometricos publicos desde `pgmx.synthesis.core`.
2. Mantener `pgmx.synthesis` reexportando los mismos nombres para no romper API.
3. Mover helpers privados de perfiles por grupos pequenos:
   endpoint/tangentes, Z/reverse y bounding/winding.
4. Dejar para una etapa posterior la compensacion compleja de perfiles, porque
   toca muchos casos Maestro y debe validarse con fixtures de linea, perfil,
   circulo y escuadrado.

Puntos abiertos:

- Definir el destino de `_CurveSpec`. Correccion aceptada: no es una geometria
  pura; es una representacion intermedia de curva serializable que puede nacer
  desde `GeometryPrimitiveSpec`/`GeometryProfileSpec` o desde hidratacion, y
  despues alimentar XML. Candidatos:
  - `common.xml`, si se la trata como payload de serializacion Maestro;
  - `common.hydration`, solo para curvas leidas desde templates;
  - un modulo nuevo `common.curves` o `common.serialization`, si necesitamos
    separar curvas serializables de XML nodal.
- Definir si `_compact_number(...)` debe resolverse antes de mover
  serializadores geometricos. Si queda en `common.xml`, `common.geometry` no
  deberia formatear numeros directamente.

Clasificacion preliminar de specs geometricas:

- Nucleo directo de `common.geometry`:
  - `GeometryPrimitiveSpec`;
  - `GeometryProfileSpec`;
  - `Point2` / `Point3` como aliases de coordenadas;
  - `BBox` si se lo generaliza desde el contrato historico de pocket milling.
- Candidatas a mover o adaptar desde el contrato experimental heredado de
  pocket milling:
  - `PolylineContour`, si se vuelve una representacion general de contorno
    cerrado y no solo de pocket milling;
  - `TracePrimitive2D`, si se vuelve primitiva geometrica 2D generica;
  - `TracePrimitiveSequence2D`, si se vuelve secuencia generica de primitivas
    2D para toolpaths/offsets.
- Specs que no deberian vivir en `common.geometry`:
  - `PocketBossRouteSeedSpec`, porque representa una semilla `BossList`
    especifica de `ClosedPocket`/pocket milling;
  - `VaciadoGeometry`, porque es contrato de familia y debe integrarse en
    `milling.pocket` o desaparecer si `PocketSpec` absorbe su rol;
  - `OffsetFamily` y `RectangularNoIslandTracePlan`, porque son planificacion
    de trazas de pocket milling, no geometria comun;
  - specs de mecanizado completas como `LineSpec`, `PocketSpec`,
    `DrillSpec`, etc.

## Item 6 - Alcance Propuesto Para `pgmx.synthesis.common.depth`

Fecha: 2026-06-03

Modulo objetivo:

- `pgmx/synthesis/common/depth.py`

Rol propuesto:

- Centralizar el contrato de profundidad usado por las familias de mecanizado.
- Separar las reglas de profundidad pasante/no pasante, profundidad efectiva de
  herramienta y cota de corte de la serializacion XML y de la seleccion de
  herramienta.
- Dar a cada familia una forma unica de preguntar:
  - que valor numerico debe tener el feature;
  - hasta donde debe cortar la herramienta;
  - cual es la cota Z del toolpath;
  - si hacen falta expresiones parametricas de profundidad.

Responsabilidades incluidas:

- Dataclass comun:
  - `DepthSpec` como nombre conceptual general para fresado, vaciado, taladrado
    y futuras familias.
  - `MillingDepthSpec` queda como alias/fachada publica temporal durante la
    migracion para no romper la API actual.
- Builder/normalizador:
  - `build_milling_depth_spec(...)`;
  - `_normalize_milling_depth_spec(...)`.
- Calculos transversales para fresados:
  - profundidad serializada del feature;
  - profundidad total efectiva de herramienta;
  - cota `cut_z` del toolpath;
  - `overcut_length` derivado de `extra_depth`;
  - deteccion de profundidad pasante para expresiones parametricas.
- Calculos transversales para taladros:
  - profundidad serializada del feature de taladro;
  - profundidad total efectiva de herramienta;
  - deteccion de expresiones parametricas en taladros pasantes.
- Validaciones de consistencia de profundidad contra dimensiones de pieza:
  - `target_depth` no pasante no puede superar el espesor util;
  - `extra_depth` no puede ser negativo;
  - `extra_depth` solo aplica a pasantes.

Responsabilidades excluidas:

- No debe resolver ni validar herramientas por `sinking_length`; esa validacion
  pertenece a `common.tools`, aunque consuma profundidades calculadas por
  `common.depth`.
- No debe construir nodos XML de expresiones parametricas; eso pertenece a
  `common.xml` o `common.program`.
- No debe decidir estrategia multipasada (`AxialCuttingDepth`,
  `AxialFinishCuttingDepth`); esos campos pertenecen a `common.strategy`.
- No debe conocer features concretas como `ClosedPocket`, `SlotSide`,
  `RoundHole` o `ReplicateFeature`.
- No debe modelar planos/caras de pieza. Puede consumir informacion axial ya
  calculada por un modulo de geometria de pieza, pero no deberia decidirla.
- No debe importar modulos de familias ni laboratorios.

Relacion con `common.program` y `common.xml`:

- `common.depth` puede devolver decisiones como `uses_depth_expressions=True` y
  nombres de campos (`StartDepth`, `EndDepth`), pero no deberia crear los nodos
  `Expression`, `PropertyAccess` o equivalentes.
- `common.program` debe decidir donde insertar expresiones y reservar IDs.
- `common.xml` debe encargarse de escribir los nodos cuando reciba la decision
  ya calculada.

Relacion con `common.tools`:

- `common.tools` deberia pedir a `common.depth` la profundidad total efectiva y
  compararla contra `sinking_length`.
- `common.depth` no debe leer `tool_catalog.csv`.

Relacion con planos/caras:

- Correccion aceptada: planos/caras pertenecen a la geometria de la pieza, no a
  profundidad.
- `common.depth` deberia recibir el espesor util o span axial ya resuelto para
  calcular profundidad, pero no deberia saber como se obtiene ese span para
  `Top`, `Front`, `Back`, `Right` o `Left`.
-- Decision aceptada: esa informacion de pieza vive en
  `pgmx.synthesis.common.piece`.

Criterio de migracion:

1. Extraer el contrato como `DepthSpec`, manteniendo `MillingDepthSpec` como
   alias compatible, junto con `build_depth_spec(...)` y un wrapper
   `build_milling_depth_spec(...)` durante la migracion.
2. Extraer los calculos puros:
   `_feature_depth_value(...)`, `_tool_total_milling_depth(...)`,
   `_toolpath_cut_z(...)`, `_operation_overcut_length(...)` y
   `_uses_feature_depth_expressions(...)`.
3. Extraer los calculos equivalentes de taladro sin mover todavia
   `_drilling_axis_span(...)`; ese helper debe migrar a
   `common.piece`.
4. Dejar en `core.py`, `common.program` o `common.xml` la construccion de
   expresiones XML hasta separar la escritura del programa.
5. Mover validaciones de `sinking_length` despues, cuando exista
   `common.tools`.

Puntos abiertos:

- Definir el nombre publico final y el plazo para retirar o conservar
  `MillingDepthSpec` como alias.
- Definir en que etapa se crea `common.piece` y que alias se mantienen
  en `core.py` durante la migracion.

## Item 7 - Alcance Propuesto Para `pgmx.synthesis.common.piece`

Fecha: 2026-06-03

Modulo objetivo:

- `pgmx/synthesis/common/piece.py`

Rol propuesto:

- Modelar la pieza como contexto de mecanizado.
- Centralizar planos/caras, dimensiones utiles, origen y transformaciones
  locales que hoy se repiten entre fresado, taladrado multicara, reparacion y
  generacion de worksteps.
- Separar la geometria de pieza de la geometria de perfiles. `common.geometry`
  describe primitivas y curvas; `common.piece` describe la pieza, su volumen,
  caras, origen y sistemas locales.

Responsabilidades incluidas:

- Representacion comun del estado geometrico de pieza:
  - largo;
  - ancho;
  - espesor/profundidad;
  - origen X/Y/Z;
  - area/campo de ejecucion si se confirma que pertenece al contexto de pieza.
- Normalizacion y validacion de planos/caras:
  - `Top`;
  - `Front`;
  - `Back`;
  - `Right`;
  - `Left`.
- Helpers de dimensiones por plano:
  - dimensiones locales X/Y disponibles en cada cara;
  - span axial util de cada cara;
  - nombre de variable parametrica asociada al eje normal cuando corresponda.
- Transformaciones entre coordenadas locales de cara y coordenadas de pieza:
  - punto de entrada de taladro por cara;
  - direccion normal de mecanizado por cara;
  - ubicacion local de operaciones sobre planos laterales.
- Helpers de bounds por cara para validar que un mecanizado cae dentro de la
  pieza antes de serializarlo.

Responsabilidades excluidas:

- No debe construir primitivas, perfiles ni curvas de herramienta; eso pertenece
  a `common.geometry` y eventualmente `common.curves`.
- No debe decidir profundidad pasante/no pasante; eso pertenece a
  `common.depth`.
- No debe resolver herramientas ni catalogos; eso pertenece a `common.tools`.
- No debe crear XML, worksteps ni expresiones parametricas; eso pertenece a
  `common.xml` y `common.program`.
- No debe conocer reglas especificas de una familia salvo como helpers
  geometricos neutrales.

Relaciones:

- `common.depth` debe consumir spans axiales ya resueltos desde
  `common.piece`.
- `drilling.single` y `drilling.pattern` deben usarlo para coordenadas y
  direcciones multicara.
- `milling.line`, `milling.profile`, `milling.circle`, `milling.squaring` y
  `milling.pocket` pueden usarlo para validar bounds y tomar dimensiones de
  pieza.
- `common.program` puede usarlo para actualizar dimensiones/origen del baseline
  y para decidir expresiones parametricas, pero no debe duplicar sus reglas.

Criterio de migracion:

1. Crear el modulo despues de `common.geometry` y antes de terminar
   `common.depth`, porque `depth` debe depender de spans ya resueltos.
2. Mover o duplicar temporalmente helpers como:
   - `_plane_local_dimensions(...)`;
   - `_drilling_axis_span(...)`;
   - `_drilling_axis_variable_name(...)`;
   - `_drilling_entry_point_and_direction(...)`.
3. Mantener wrappers en `core.py` hasta que las familias usen el nuevo modulo.
4. Agregar tests focales para cada cara antes de migrar taladros multicara.

Puntos abiertos:

- Decision aceptada: `PgmxState` queda definido en `common.program` como estado
  de programa/baseline, no como geometria pura.
- Decision aceptada: el modulo se llama `common.piece`, no
  `common.piece_geometry`.
- Decision aceptada: `common.piece` define una dataclass `PieceGeometry`,
  salvo que durante la implementacion convenga generalizarla a `Piece`.
- Estructura conceptual:
  - `PieceGeometry`: dimensiones de pieza, origen y datos geometricos de
    planos/caras.
  - `PgmxState`: `piece_name`, `execution_fields` y `piece_geometry`.
- `execution_fields`/`Area` pertenece al estado de programa Maestro, no a la
  geometria de pieza.

## Item 8 - Alcance Propuesto Para `pgmx.synthesis.common.tools`

Fecha: 2026-06-03

Modulo objetivo:

- `pgmx/synthesis/common/tools.py`

Rol propuesto:

- Centralizar el acceso al catalogo de herramientas Maestro y las reglas
  transversales de identidad, tipo, diametro/ancho, grupo de uso y capacidad
  segura de herramienta.
- Dar a los modulos de fresado y taladrado una descripcion normalizada de la
  herramienta, sin que cada familia lea `tool_catalog.csv` ni replique
  validaciones.
- Para taladrado, separar la validacion de herramienta de la asignacion de
  `ToolKey`: el PGMX editable debe conservar la herramienta no resuelta y dejar
  la eleccion final a Maestro/postproceso y al futuro sintetizador ISO
  `iso_state_synthesis`.
- Separar la semantica de herramienta de la construccion XML de `ToolKey`.

Responsabilidades incluidas:

- Ruta y carga del catalogo:
  - `TOOL_CATALOG_PATH`;
  - lectura de `pgmx/synthesis/tool_catalog.csv`;
  - cacheo o carga controlada del catalogo.
- Busqueda y resolucion de entradas:
  - lookup por `tool_id`;
  - lookup por `tool_name`;
  - normalizacion de diametro/ancho cuando se use para seleccionar herramienta;
  - labels de herramienta para mensajes de error;
  - resolucion de herramienta solo para mecanizados que deban emitir una
    herramienta concreta en PGMX, no para taladrado por defecto.
- Dataclasses o tipos internos de herramienta:
  - `ToolCatalogEntry`, para representar una fila normalizada del catalogo;
  - `ResolvedTool` o `ToolSpec`, para representar la herramienta elegida para
    una operacion cuando corresponde;
  - `UnresolvedToolKey` o equivalente, para representar explicitamente el
    estado Maestro `ID = 0`, `Name = ""`, `ObjectType = System.Object`.
- Clasificacion transversal:
  - grupo de uso de herramienta;
  - tipo de herramienta;
  - deteccion de si una herramienta sirve para fresado, taladrado o sierra.
- Validaciones transversales:
  - tipo compatible con fresado;
  - tipo compatible con taladrado;
  - tipo compatible con sierra cuando el mecanizado lo requiera;
  - `sinking_length` suficiente para la profundidad efectiva recibida desde
    `common.depth`.
- Reglas de resolucion de taladros:
  - todos los taladros deben conservar `ToolKey` no resuelto en el PGMX
    editable, inclusive los verticales de cara superior;
  - la regla no resuelta debe aplicar tambien a patrones de taladrado;
  - la herramienta concreta queda delegada a Maestro/postproceso y, cuando este
    listo, al sintetizador ISO `iso_state_synthesis`;
  - cualquier dato de herramienta indicado por el usuario puede servir para
    validacion o documentacion de intencion, pero no debe forzar un `ToolKey`
    resuelto en la salida editable.

Responsabilidades excluidas:

- No debe construir nodos XML de `ToolKey`, `ReferenceKey` ni atributos
  `i:type`; eso pertenece a `common.xml` y a los builders que serializan la
  operacion.
- No debe calcular profundidad de corte; debe recibirla desde `common.depth`.
- No debe resolver spans, caras ni transformaciones de pieza; eso pertenece a
  `common.piece`.
- No debe decidir trayectorias, offsets, leads ni geometria de herramienta; eso
  pertenece a `common.geometry`, `common.strategy` o al modulo de familia.
- No debe construir specs completos como `LineSpec`, `PocketSpec`
  o `DrillSpec`.

Relaciones:

- `common.depth` calcula la profundidad efectiva requerida; `common.tools`
  compara ese valor contra `sinking_length`.
- `common.piece` resuelve cara/plano y span axial; `common.tools`
  puede consumir el nombre de cara para reglas de resolucion, pero no debe
  transformar coordenadas.
- `drilling.single` usa este modulo para emitir el estado no resuelto de
  herramienta y, si corresponde, validar la intencion de herramienta sin
  serializarla como `ToolKey` resuelto.
- `drilling.pattern` debe aplicar la misma politica que `drilling.single`.
- `iso_state_synthesis`, todavia en desarrollo, debera consumir el estado
  editable no resuelto y decidir herramienta final cuando sintetice ISO sin
  pasar por Maestro/postproceso.
- `milling.slot` usa este modulo para clasificar herramientas tipo sierra; las
  restricciones geometricas especificas de ranura deberian quedar en
  `milling.slot`.
- `common.program` y los modulos de familia usan el resultado normalizado para
  serializar la herramienta, pero la escritura XML queda fuera de
  `common.tools`.

Criterio de migracion:

1. Extraer primero carga, lookup y labels del catalogo desde
   `pgmx.synthesis.core`.
2. Crear una dataclass normalizada para filas del catalogo y otra, si hace
   falta, para la herramienta resuelta de una operacion.
3. Extraer validadores de grupo/tipo sin cambiar mensajes ni comportamiento.
4. Mover la politica de `ToolKey` no resuelto para taladros, manteniendo
   wrappers en `core.py` durante la migracion.
5. Mover la validacion de `sinking_length` despues de estabilizar
   `common.depth`, para que `tools` consuma profundidades ya calculadas.
6. Separar al final las restricciones especificas de `Sierra Vertical X`:
   clasificacion generica en `common.tools`, reglas de ranura en
   `milling.slot`.

Puntos abiertos:

- Elegir nombres finales: `ToolCatalogEntry`, `ResolvedTool`, `ToolSpec` o una
  combinacion menor.
- Definir si el mapa historico de auto-resolucion de taladros verticales se
  elimina, queda solo como compatibilidad de lectura, o se conserva para un
  modo experimental que no afecte la emision productiva.
- Definir si la normalizacion de diametro/ancho queda solo en herramientas o si
  parte de ella debe seguir cerca de los specs de familia por compatibilidad de
  API.

## Item 9 - Alcance Propuesto Para `pgmx.synthesis.common.strategy`

Fecha: 2026-06-03

Modulo objetivo:

- `pgmx/synthesis/common/strategy.py`

Rol propuesto:

- Centralizar las estrategias Maestro comunes que parametrizan como se ejecuta
  un mecanizado, sin generar por si mismo la geometria final de la trayectoria.
- Ser el contrato comun para el apartado Maestro `Estrategia`: normalizacion,
  defaults observados, validaciones y comparacion semantica.
- Respetar la separacion de Maestro entre `Estrategia` y
  `Acercamiento/Alejamiento`. Aunque esos apartados se serialicen cerca de la
  operacion, no deben confundirse dentro del modelo de dominio.
- Mantener separadas las decisiones de estrategia de:
  - la geometria de perfiles;
  - la profundidad efectiva;
  - la herramienta concreta;
  - el acercamiento/alejamiento;
  - la serializacion XML final.

Responsabilidades incluidas:

- Dataclasses de estrategia de fresado:
  - `UnidirectionalMillingStrategySpec`;
  - `BidirectionalMillingStrategySpec`;
  - `HelicalMillingStrategySpec`;
  - `ContourParallelMillingStrategySpec`;
  - union o alias `MillingStrategySpec`.
- Clasificacion por alcance:
  - estrategias compartidas por varias familias, como `Unidirectional` y
    `Bidirectional`;
  - estrategias especificas de una familia, como `Helical` para fresados
    circulares;
  - estrategias especificas de Vaciado/ClosedPocket, como `ContourParallel`
    / `Paralela a perfil`;
  - parametros con nombres similares entre estrategias distintas, sin asumir
    que significan lo mismo hasta tener evidencia Maestro.
- Builders y normalizadores publicos:
  - `build_unidirectional_milling_strategy_spec(...)`;
  - `build_bidirectional_milling_strategy_spec(...)`;
  - `build_helical_milling_strategy_spec(...)`;
  - `build_contour_parallel_milling_strategy_spec(...)`.
- Normalizacion de vocabulario Maestro/API:
  - `ConnectionMode`;
  - `StrokeConnectionStrategy`;
  - `RotationDirection`;
  - `Cutmode`;
  - nombres y sinonimos propios de cada estrategia, sin mezclar campos solo
    porque comparten etiqueta.
- Validaciones transversales de estrategia:
  - profundidades axiales/radiales de estrategia no negativas;
  - coherencia entre `AllowMultiplePasses` y profundidades de pasada;
  - coherencia entre `AllowsFinishCutting` y profundidad de terminacion;
  - tipos de estrategia admitidos por cada familia mediante un helper como
    `_ensure_milling_strategy_allowed(...)`.
- Comparacion semantica de estrategias para hidratacion/adaptacion:
  - clave de comparacion que abstraiga sinonimos API/Maestro;
  - resolucion de `ConnectionMode` en perfiles abiertos/cerrados.
- Defaults observados en Maestro:
  - defaults propios de cada estrategia;
  - valores default de `ContourParallel` usados por Vaciado/ClosedPocket.

Responsabilidades excluidas:

- No debe construir nodos XML `MachiningStrategy`, `Approach` ni `Retract`;
  esa escritura pertenece a `common.xml` o a los builders productivos de
  familia.
- No debe modelar `Acercamiento/Alejamiento`; ese apartado Maestro vive en
  `common.leads`.
- No debe generar toolpaths ni secuencias XYZ. Por ejemplo, una estrategia
  `ContourParallel` define `overlap`, direccion y conexion, pero no calcula la
  traza del vaciado.
- No debe decidir profundidades de feature ni cotas `cut_z`; eso pertenece a
  `common.depth`.
- No debe resolver herramientas ni validar catalogo; eso pertenece a
  `common.tools`.
- No debe saber dimensiones/caras de pieza; eso pertenece a `common.piece`.
- No debe hidratar templates completos; solo puede exponer helpers para
  comparar o normalizar estrategias extraidas por `common.hydration`.

Relaciones:

- `milling.line`, `milling.profile`, `milling.circle` y `milling.squaring`
  pueden consumir estrategias compartidas `Unidirectional/Bidirectional` cuando
  Maestro las admite para esa familia.
- `milling.circle` consume `HelicalMillingStrategySpec` como estrategia
  especifica de fresado circular.
- `milling.pocket` consume `ContourParallelMillingStrategySpec` para
  `ClosedPocket`/Vaciado; sus parametros no deben fusionarse automaticamente
  con parametros parecidos de otras estrategias.
- `common.hydration` puede usar la comparacion semantica de estrategias para
  decidir si una traza de template es reusable.
- `common.xml` o los builders de familia deben serializar los nodos Maestro a
  partir de las specs normalizadas.
- `common.leads` debera convivir con `common.strategy` sin depender de el salvo
  por reglas puntuales de compatibilidad observadas.

Criterio de migracion:

1. Extraer dataclasses y builders de estrategia desde `pgmx.synthesis.core`
   manteniendo nombres publicos y reexports.
2. Extraer normalizadores privados de vocabulario y profundidad de estrategia.
3. Extraer `_normalize_milling_strategy_spec(...)`,
   `_ensure_milling_strategy_allowed(...)` y helpers de comparacion semantica.
4. Separar las specs de estrategia por alcance de familia para que
   `ContourParallel`, `Helical` y futuras estrategias especificas no queden
   falsamente generalizadas por nombres de campos parecidos.
5. Dejar temporalmente `_build_milling_strategy_node(...)` en `core.py` o en el
   builder de familia hasta que exista el limite claro entre `common.xml` y
   `common.program`.
6. Validar con tests de fachada publica, adaptacion desde snapshots y sintesis
   de familias que usan cada estrategia.

Puntos abiertos:

- Decision aceptada: `Acercamiento/Alejamiento` vivira en
  `pgmx.synthesis.common.leads`. No pertenece a `common.strategy`.
- Definir si `ContourParallelMillingStrategySpec` sigue siendo comun o si una
  parte debe vivir en `milling.pocket` cuando aparezcan estrategias de vaciado
  que no apliquen a otros perfiles cerrados.
- Definir donde vive la serializacion de `MachiningStrategy`: por ahora no en
  `common.strategy`; candidato futuro `common.xml` si queda como nodo comun, o
  cada familia si la estructura depende demasiado del tipo de operacion.

## Item 10 - Alcance Propuesto Para `pgmx.synthesis.common.hydration`

Fecha: 2026-06-03

Modulo objetivo:

- `pgmx/synthesis/common/hydration.py`

Rol propuesto:

- Ser la infraestructura comun para leer un PGMX fuente (`source_pgmx_path`) y
  reutilizar material Maestro ya existente cuando el contrato solicitado
  coincide con la plantilla.
- Separar claramente dos caminos:
  - sintesis generativa, donde el sintetizador produce geometria y toolpaths
    desde reglas propias;
  - sintesis hidratada, donde se conserva una serializacion o traza Maestro
    existente porque todavia no conviene, o no es posible, regenerarla con
    garantia completa.
- Registrar la procedencia del material reutilizado para que no se confunda un
  caso hidratado con una regla productiva cerrada.

Responsabilidades incluidas:

- Carga de documento fuente:
  - abrir `.pgmx`, `Pieza.xml` o carpeta compatible;
  - devolver el XML principal, entradas auxiliares del contenedor y nombre de
    entrada XML;
  - exponer un objeto tipo `PgmxTemplateDocument` o equivalente.
- Payloads reutilizables:
  - `preferred_id_start` o rango sugerido de IDs cuando se conserva material
    Maestro;
  - curvas serializadas de geometria;
  - curvas serializadas de toolpath (`Approach`, `TrajectoryPath`, `Lift`);
  - secuencias XYZ extraidas desde curvas cuando se puedan leer con seguridad;
  - expresiones asociadas a una feature;
  - referencias a feature/operation/geometry del template.
- Contratos internos de resultado:
  - `HydrationPayload` o equivalente para datos crudos reutilizables;
  - `HydratedSpec` o wrappers por familia que combinen spec normalizada y
    payload reutilizable;
  - metadata de procedencia: ruta fuente, tipo de plantilla, secciones
    reutilizadas y secciones descartadas.
- Helpers compartidos para extractores de familia:
  - encontrar geometria, feature, operacion y workstep vinculados;
  - extraer curvas simples, compuestas y circulares como payload serializable;
  - extraer toolpaths por tipo;
  - calcular IDs preferidos desde geometria y expresiones;
  - comparar listas simples de puntos cuando la familia lo pida.
- Mecanismo de fallback:
  - si no hay `source_pgmx_path`, devolver spec sin payload hidratado;
  - si la plantilla no coincide, descartar el payload y permitir que la familia
    use su camino generativo;
  - nunca forzar reuse parcial sin que la familia lo declare compatible.

Responsabilidades excluidas:

- No debe decidir reglas geometricas ni generar toolpaths nuevos; eso pertenece
  a `common.geometry`, `common.strategy` o al modulo productivo de familia.
- No debe decidir si una estrategia, profundidad, herramienta o lead
  son semanticamente equivalentes; debe delegar esas comparaciones a
  `common.strategy`, `common.depth`, `common.tools` y `common.leads`.
- No debe resolver herramientas ni `ToolKey`; con la regla nueva de taladrado,
  la herramienta final queda para Maestro/postproceso o `iso_state_synthesis`,
  no para hidratacion.
- No debe ser un laboratorio ni ocultar fronteras abiertas: si una familia
  depende de template para funcionar, esa dependencia debe quedar visible en
  metadata, tests y memoria del laboratorio.
- No debe escribir el PGMX final ni preservar entradas ZIP por si mismo; la
  escritura final pertenece a `common.program` o a la capa de salida.
- No debe reemplazar `pgmx.adapters`: adapters convierte snapshots Maestro en
  specs; hydration enriquece specs ya solicitadas con payload reusable.

Relaciones:

- `common.program` coordina la decision de hidratar cada spec usando
  `source_pgmx_path`, pero la compatibilidad fina debe vivir en cada familia.
- Los modulos de familia (`milling.line`, `milling.profile`,
  `milling.circle`, `milling.pocket`, `drilling.single`, etc.) usan helpers de
  `common.hydration` para leer material fuente y deciden si pueden reutilizarlo.
- `common.xml` aporta lectura/escritura nodal basica y normalizacion XML.
- `common.geometry` o un futuro `common.curves` interpreta payloads de curvas
  cuando hace falta comparar puntos.
- `common.strategy`, `common.depth`, `common.tools` y `common.leads`
  normalizan los datos extraidos antes de comparar.
- `pgmx.adapters` puede pasar `source_pgmx_path` al request para que la sintesis
  conserve serializaciones exactas del archivo original cuando corresponda.

Criterio de migracion:

1. Extraer primero la carga de contenedor/documento y los helpers de busqueda
   XML compartidos.
2. Crear tipos de payload hidratado independientes de una familia concreta.
3. Mover extractores de curvas/toolpaths y calculo de `preferred_id_start`.
4. Pasar los extractores especificos de linea, polilinea, circulo y pocket a
   sus modulos de familia, usando helpers de `common.hydration`.
5. Retirar de hidratacion cualquier resolucion de herramienta de taladrado y
   llevar esa regla a `common.tools`/familia/ISO segun corresponda.
6. Mantener wrappers en `core.py` durante la migracion para no romper la API ni
   los tests existentes.

Puntos abiertos:

- Definir el nombre del payload serializable de curva: puede quedarse como
  `_CurveSpec`, moverse a `common.hydration`, o abrirse un modulo
  `common.curves` si tambien lo consumen geometria y XML.
- Definir si los wrappers `_Hydrated*Spec` son una familia de dataclasses
  especifica por mecanizado o un wrapper generico `Hydrated[T]` con payloads
  tipados.
- Definir como se reporta la procedencia: solo metadata interna, logs de
  diagnostico, o campos visibles en tests/laboratorio.

## Item 11 - Alcance Propuesto Para `pgmx.synthesis.common.leads`

Fecha: 2026-06-03

Modulo objetivo:

- `pgmx/synthesis/common/leads.py`

Rol propuesto:

- Modelar el apartado Maestro `Acercamiento/Alejamiento` como contrato comun
  separado de `Estrategia`.
- Centralizar parametros, defaults, normalizacion y comparacion semantica de
  movimientos de entrada y salida que varias familias de mecanizado comparten.
- Evitar que `common.strategy` mezcle conceptos que Maestro presenta y edita
  como apartados distintos.

Responsabilidades incluidas:

- Dataclasses publicas o internas:
  - `ApproachSpec`, para `Acercamiento`;
  - `RetractSpec`, para `Alejamiento`;
  - union o wrapper futuro si conviene hablar de ambos como un par de leads.
- Builders y normalizadores:
  - `build_approach_spec(...)`;
  - `build_retract_spec(...)`;
  - `_normalize_approach_spec(...)`;
  - `_normalize_retract_spec(...)`.
- Normalizacion de vocabulario Maestro/API:
  - `ApproachType`;
  - `ApproachMode`;
  - `ApproachArcSide`;
  - `RetractType`;
  - `RetractMode`;
  - `RetractArcSide`.
- Parametros transversales:
  - habilitado/deshabilitado;
  - tipo de movimiento (`Line`, `Arc`, etc. segun evidencia);
  - modo (`Down`, `Up`, `Quote`, etc.);
  - `RadiusMultiplier`;
  - `Speed`;
  - lado de arco;
  - `OverLap` de alejamiento.
- Defaults observados:
  - specs deshabilitadas cuando no hay configuracion explicita;
  - defaults de Maestro para leads habilitados;
  - defaults especificos por familia solo si la familia los solicita
    explicitamente.
- Comparacion semantica para hidratacion:
  - decidir si el `Approach`/`Retract` extraido de un template coincide con la
    spec solicitada;
  - normalizar sinonimos antes de comparar.

Responsabilidades excluidas:

- No debe modelar el apartado `Estrategia`; eso pertenece a `common.strategy`.
- No debe generar curvas o toolpaths de approach/retract. Puede describir la
  configuracion, pero la geometria concreta de entrada/salida pertenece a
  `common.geometry` o al modulo productivo de familia.
- No debe serializar nodos XML `Approach`/`Retract`; esa escritura pertenece a
  `common.xml` o a los builders productivos.
- No debe calcular profundidad, cotas de seguridad ni clearance; eso pertenece
  a `common.depth`, `common.piece` y a la familia que construye la
  operacion.
- No debe resolver herramientas ni velocidades tecnologicas de corte; eso
  pertenece a `common.tools` o a un futuro modulo de tecnologia si aparece.

Relaciones:

- `milling.line`, `milling.profile`, `milling.circle`, `milling.squaring` y
  `milling.pocket` consumen `common.leads` cuando sus operaciones Maestro
  exponen `Approach` y `Retract`.
- `common.hydration` usa `common.leads` para normalizar y comparar leads
  extraidos desde templates.
- `common.strategy` convive con `common.leads`, pero no debe importar sus
  dataclasses salvo que una regla Maestro comprobada lo requiera.
- `common.xml` o los builders de familia escriben los nodos finales desde las
  specs normalizadas.

Criterio de migracion:

1. Extraer `ApproachSpec`, `RetractSpec`, builders y normalizadores desde
   `pgmx.synthesis.core` manteniendo reexports publicos.
2. Mover los normalizadores de vocabulario de approach/retract.
3. Actualizar hidratacion para comparar leads mediante `common.leads`.
4. Dejar la construccion XML de `Approach`/`Retract` donde este hasta separar
   `common.xml` y builders de familia.
5. Validar con familias que hoy usan leads: linea, polilinea, circulo,
   escuadrado y pocket milling.

Puntos abiertos:

- Confirmar si todos los mecanizados con `Approach`/`Retract` comparten los
  mismos campos o si alguna familia necesita una spec especializada.
- Definir si `Speed` de leads queda siempre aqui o si mas adelante se separa
  una capa de tecnologia/feeds.
- Definir si conviene un wrapper tipo `LeadPairSpec` para transportar
  approach/retract juntos en specs de familia.

## Item 12 - Alcance Propuesto Para `pgmx.synthesis.milling.line`

Fecha: 2026-06-03

Modulo objetivo:

- `pgmx/synthesis/milling/line.py`

Rol propuesto:

- Ser el modulo productivo para fresados lineales simples de Maestro.
- Tomar un segmento recto sobre una cara/plano y serializarlo como
  `GeneralProfileFeature` con geometria `GeomTrimmedCurve` y operacion
  `BottomAndSideFinishMilling`.
- Mantener separado este caso de:
  - ranuras `SlotSide`;
  - polilineas o perfiles compuestos;
  - circulos;
  - escuadrados;
  - pocket milling / `ClosedPocket`.

Responsabilidades incluidas:

- Contrato publico actual:
  - `LineSpec`;
  - `build_line_spec(...)`;
  - wrappers de compatibilidad exportados por `pgmx.synthesis`.
- Normalizacion de spec:
  - coordenadas inicial/final;
  - nombre de feature;
  - plano/cara;
  - `side_of_feature`;
  - herramienta y ancho;
  - cota de seguridad;
  - profundidad;
  - leads (`Approach`/`Retract`);
  - estrategia admitida.
- Estrategias permitidas:
  - `UnidirectionalMillingStrategySpec`;
  - `BidirectionalMillingStrategySpec`;
  - sin estrategia explicita cuando Maestro lo admite.
- Construccion geometrica propia:
  - geometria nominal de linea;
  - toolpath compensado segun `side_of_feature` y `tool_width`;
  - punto de entrada/salida del perfil para construir approach/lift cuando no
    vienen hidratados.
- Construccion productiva PGMX:
  - `GeomTrimmedCurve`;
  - `GeneralProfileFeature`;
  - `BottomAndSideFinishMilling`;
  - `WorkingStep`;
  - expresiones de profundidad cuando corresponda;
  - toolpaths `Approach`, `TrajectoryPath` y `Lift`.
- Hidratacion:
  - aceptar payloads de `common.hydration` para conservar serializaciones de
    geometria/toolpath cuando el template coincide exactamente;
  - rechazar reuse si no coinciden geometria, profundidad, herramienta,
    estrategia, leads o lado de feature.
- Adaptacion:
  - recibir desde `pgmx.adapters` geometria `GeomTrimmedCurve` con una sola
    primitiva `Line` y convertirla a `LineSpec`.

Responsabilidades excluidas:

- No debe manejar `SlotSide`; eso pertenece a `milling.slot`.
- No debe absorber polilineas de multiples segmentos ni perfiles con arcos; eso
  pertenece a `milling.profile`.
- No debe manejar circulos; eso pertenece a `milling.circle`.
- No debe decidir reglas generales de estrategia; debe consumir
  `common.strategy`.
- No debe modelar `Approach`/`Retract`; debe consumir `common.leads`.
- No debe resolver catalogo de herramientas; debe consumir `common.tools`.
- No debe calcular reglas generales de profundidad; debe consumir
  `common.depth`.
- No debe conocer el laboratorio ni depender de `machining_lab`.

Relaciones:

- `common.geometry` aporta primitivas, perfiles, compensacion y serializacion
  geometrica reusable.
- `common.piece` aporta plano/cara, dimensiones y validaciones de contexto.
- `common.depth` aporta profundidad efectiva, `cut_z`, overcut y expresiones.
- `common.tools` valida herramienta, tipo y capacidad.
- `common.strategy` valida que la estrategia sea lineal admitida.
- `common.leads` normaliza y compara acercamiento/alejamiento.
- `common.hydration` entrega payloads del PGMX fuente; `milling.line` decide si
  los reutiliza.
- `common.program` orquesta la aplicacion del mecanizado, reserva IDs y escribe
  el programa final.

Criterio de migracion:

1. Extraer `LineSpec`, `build_line_spec(...)` y
   `_normalize_line_milling_spec(...)` desde `pgmx.synthesis.core`.
2. Mover la construccion de geometria/toolpath lineal, manteniendo helpers
   compartidos en `common.geometry`.
3. Mover `_extract_line_milling_template(...)`,
   `_can_hydrate_exact_serialization(...)` y `_hydrate_line_milling_spec(...)`
   usando `common.hydration`.
4. Mover `_append_line_milling(...)` y la parte lineal de
   `_build_line_operation(...)`, dejando en comunes solo helpers compartidos.
5. Mantener reexports y wrappers en `pgmx.synthesis.core` mientras dure la
   migracion.
6. Validar con tests de API publica, adaptacion desde snapshot y sintesis de
   linea simple.

Puntos abiertos:

- Definir si `_build_line_operation(...)` se queda en `milling.line` o si se
  divide en un helper comun para operaciones `BottomAndSideFinishMilling` que
  tambien usan profile/circle/squaring.
- Definir si el builder publico debe conservar para siempre el prefijo
  historico `line_*` en sus parametros o si se agrega una API nueva mas limpia
  con wrapper compatible.
- Definir si la compensacion por `side_of_feature` queda totalmente en
  `common.geometry` o si `milling.line` conserva la politica de uso para este
  mecanizado.

## Item 13 - Alcance Propuesto Para `pgmx.synthesis.milling.slot`

Fecha: 2026-06-03

Modulo objetivo:

- `pgmx/synthesis/milling/slot.py`

Rol propuesto:

- Ser el modulo productivo para ranuras lineales Maestro serializadas como
  `SlotSide`.
- Mantener este mecanizado separado de `milling.line`, aunque ambos usen una
  recta como geometria base, porque la feature Maestro, las reglas de
  herramienta y los parametros propios no son los mismos.
- Representar el alcance actualmente validado:
  - ranura superior sobre `Top`;
  - geometria `GeomTrimmedCurve` con una sola primitiva `Line`;
  - recorrido horizontal ejecutable con `Sierra Vertical X`;
  - operacion `BottomAndSideFinishMilling` asociada a feature `SlotSide`.

Responsabilidades incluidas:

- Contrato publico actual:
  - `ChannelSpec`;
  - `build_channel_spec(...)`;
  - wrappers de compatibilidad exportados por `pgmx.synthesis`.
- Normalizacion de spec:
  - coordenadas inicial/final;
  - longitud no nula;
  - nombre de feature;
  - plano/cara;
  - `side_of_feature`;
  - herramienta y ancho;
  - cota de seguridad;
  - profundidad;
  - leads (`Approach`/`Retract`);
  - parametros propios de ranura.
- Parametros propios de `SlotSide`:
  - `material_position`;
  - `side_offset`;
  - `end_radius`;
  - `slot_angle`.
- Defaults productivos actuales:
  - `feature_name = "Canal"`;
  - `plane_name = "Top"`;
  - `tool_id = "1899"`;
  - `tool_name = "082"`;
  - `tool_width = 3.8`;
  - profundidad no pasante con `target_depth = 10.0`;
  - `material_position = "Left"`;
  - `side_offset = 0.0`;
  - `end_radius = 60.0`;
  - `slot_angle = 1.5707963267948966`.
- Construccion productiva PGMX:
  - feature `a:SlotSide`;
  - geometria lineal;
  - operacion de fresado compatible;
  - `WorkingStep`;
  - toolpaths `Approach`, `TrajectoryPath` y `Lift` cuando correspondan.
- Validacion de herramienta:
  - consumir `common.tools` para exigir una herramienta compatible con
    `Sierra Vertical X`;
  - evitar que ranuras `SlotSide` se emitan con herramientas ordinarias de
    fresado cuando Maestro/CNC requieren la sierra.
- Adaptacion:
  - aceptar desde `pgmx.adapters` una feature `SlotSide` con geometria simple
    de linea;
  - conservar como no soportados los casos que hoy no son ejecutables o no
    estan validados, por ejemplo `SlotSide` vertical con `Sierra Vertical X`.
- Hidratacion:
  - por ahora no tiene reuse exacto especifico; el estado actual normaliza la
    spec y genera la ranura;
  - si en el futuro aparece una diferencia de serializacion Maestro que exija
    template, debera consumir `common.hydration` con las mismas reglas de
    validacion que las demas familias.

Responsabilidades excluidas:

- No debe manejar fresado lineal `GeneralProfileFeature`; eso pertenece a
  `milling.line`.
- No debe absorber polilineas, perfiles con arcos ni contornos compuestos; eso
  pertenece a `milling.profile`.
- No debe manejar circulos, escuadrados ni pocket milling.
- No debe generalizar ranuras curvas o de multiples segmentos sin evidencia
  Maestro y validacion productiva.
- No debe decidir el catalogo de herramientas; debe consumir `common.tools`.
- No debe resolver postprocesamiento ISO ni reparaciones de orientacion; esas
  responsabilidades pertenecen a `pgmx.processing` e `iso_state_synthesis`.
- No debe modelar estrategias de fresado: el contrato actual expone
  `milling_strategy` como `None`.
- No debe conocer el laboratorio ni depender de `machining_lab`.

Relaciones:

- `common.geometry` aporta la primitiva lineal y helpers de serializacion.
- `common.piece` aporta plano/cara y futuras validaciones contra la pieza.
- `common.depth` aporta profundidad efectiva y expresiones.
- `common.tools` aporta la clasificacion y validacion de `Sierra Vertical X`.
- `common.leads` normaliza y compara acercamiento/alejamiento.
- `common.program` orquesta IDs, aplicacion del mecanizado y escritura final.
- `common.hydration` queda como dependencia potencial para futuros templates.
- `pgmx.adapters` conserva la lectura de snapshots, pero puede delegar
  predicados de dominio en `milling.slot`.

Criterio de migracion:

1. Extraer `ChannelSpec`, `build_channel_spec(...)` y
   `_normalize_slot_milling_spec(...)` desde `pgmx.synthesis.core`.
2. Mover la construccion de feature `SlotSide` y `_append_slot_milling(...)`.
3. Revisar si `_build_line_operation(...)` queda como helper compartido para
   operaciones `BottomAndSideFinishMilling` o si se divide por familia.
4. Mover reglas especificas de validez de `SlotSide` a helpers del modulo,
   manteniendo `pgmx.adapters` como fachada de adaptacion.
5. Mantener reexports y wrappers en `pgmx.synthesis.core` mientras dure la
   migracion.
6. Validar con tests de API publica, adaptacion de snapshot, reparacion
   `SlotSide` en `pgmx.processing` y sintesis de ranura horizontal.

Puntos abiertos:

- Definir si el alcance `Top` + recorrido horizontal + `Sierra Vertical X` es
  una restriccion permanente del mecanizado o solo el subconjunto validado por
  ahora.
- Definir si `slot_angle` debe derivarse siempre de la orientacion geometrica o
  conservarse como campo explicito Maestro.
- Definir si futuras ranuras con herramienta de fresado comun siguen siendo
  `SlotSide` o pasan a otra familia de mecanizado.
- Definir si se necesitara hidratacion exacta para ranuras o si la generacion
  pura actual es suficiente.

## Item 14 - Alcance Propuesto Para `pgmx.synthesis.milling.profile`

Fecha: 2026-06-03

Modulo objetivo:

- `pgmx/synthesis/milling/profile.py`

Rol propuesto:

- Ser el modulo productivo para fresados sobre perfiles abiertos o cerrados que
  no son una linea simple, una ranura, un circulo puro, un escuadrado ni un
  `ClosedPocket`.
- Cubrir el contrato actual de `PolylineSpec` y preparar el lugar para
  perfiles compuestos con arcos cuando exista evidencia Maestro suficiente.

Responsabilidades incluidas:

- Contrato publico actual:
  - `PolylineSpec`;
  - `build_polyline_spec(...)`;
  - normalizacion de puntos y cierre de perfil.
- Soporte actual:
  - polilineas lineales abiertas;
  - polilineas lineales cerradas;
  - `GeneralProfileFeature`;
  - geometria `GeomCompositeCurve` sin arcos en el adaptador actual.
- Estrategias admitidas:
  - `UnidirectionalMillingStrategySpec`;
  - `BidirectionalMillingStrategySpec`;
  - sin estrategia explicita cuando Maestro lo admite.
- Reglas productivas:
  - validar segmentos no degenerados;
  - bloquear combinaciones que Maestro no postprocesa, por ejemplo polilinea
    abierta multisegmento con estrategia multipasada PH y `Retract Arc + Up`;
  - construir geometria, feature, operacion y working step.
- Hidratacion:
  - conservar serializacion exacta de polilineas cuando el template coincide;
  - rechazar reuse si difieren geometria, profundidad, herramienta, estrategia
    o leads.
- Adaptacion:
  - convertir snapshots `GeomCompositeCurve` lineales en `PolylineSpec`;
  - mantener arcos como no soportados hasta que exista spec de perfil compuesto.

Responsabilidades excluidas:

- No debe manejar una linea simple cuando corresponda `milling.line`.
- No debe manejar `SlotSide`; eso pertenece a `milling.slot`.
- No debe absorber circulos puros mientras `milling.circle` exista como modulo.
- No debe manejar contornos de escuadrado exterior detectables como
  `milling.squaring`.
- No debe manejar `ClosedPocket`; eso pertenece a `milling.pocket`.

Relaciones:

- `common.geometry` aporta perfiles, primitivas y validacion geometrica.
- `common.strategy` aporta reglas de estrategia compartidas.
- `common.leads`, `common.depth`, `common.tools` y `common.piece` aportan las
  reglas transversales.
- `common.hydration` aporta templates exactos.
- `pgmx.adapters` conserva lectura de snapshots y puede delegar predicados de
  dominio.

Criterio de migracion:

1. Extraer `PolylineSpec`, builder y normalizador.
2. Extraer reglas de postprocesabilidad Maestro.
3. Mover construccion de geometria compuesta lineal y `_append_polyline_milling`.
4. Mover hidratacion exacta de polilineas.
5. Mantener wrappers y reexports durante la transicion.
6. Validar con tests de polilinea abierta, cerrada, adapter y casos bloqueados.

Puntos abiertos:

- Definir una spec general para perfiles con arcos o ampliar
  `PolylineSpec`.
- Definir si `circle.py` permanece separado o si en una etapa futura se integra
  como caso particular de perfil.

## Item 15 - Alcance Propuesto Para `pgmx.synthesis.milling.circle`

Fecha: 2026-06-03

Modulo objetivo:

- `pgmx/synthesis/milling/circle.py`

Rol propuesto:

- Ser el modulo productivo para fresados circulares Maestro basados en centro,
  radio y sentido de giro.
- Mantener una familia separada de `profile` mientras el contrato circular
  tenga estrategia, geometria e hidratacion propias.

Responsabilidades incluidas:

- Contrato publico actual:
  - `CircleSpec`;
  - `build_circle_spec(...)`;
  - normalizacion de centro, radio, winding y lado de feature.
- Validaciones:
  - radio mayor que cero;
  - plano/cara soportado;
  - herramienta y profundidad;
  - leads;
  - estrategia permitida.
- Estrategias admitidas:
  - `UnidirectionalMillingStrategySpec`;
  - `BidirectionalMillingStrategySpec`;
  - `HelicalMillingStrategySpec`;
  - sin estrategia explicita cuando Maestro lo admite.
- Construccion productiva:
  - geometria circular;
  - feature de perfil general circular;
  - operacion `BottomAndSideFinishMilling`;
  - working step;
  - trayectorias de approach/retract compatibles.
- Hidratacion y adaptacion:
  - adaptar snapshots `GeomCircle` con centro/radio resolubles;
  - conservar template exacto cuando la geometria y parametros coinciden.

Responsabilidades excluidas:

- No debe modelar cualquier arco parcial de un perfil compuesto.
- No debe absorber perfiles circulares si Maestro los guarda como otra familia
  distinta.
- No debe manejar estrategias circulares no validadas.
- No debe decidir catalogo de herramientas ni postprocesamiento ISO.

Relaciones:

- `common.geometry` aporta primitiva/serializacion circular.
- `common.strategy` distingue estrategias compartidas y helicoidal.
- `common.leads`, `common.depth`, `common.tools`, `common.piece` y
  `common.hydration` aportan las reglas transversales.
- `milling.profile` puede compartir helpers, pero no debe depender
  circularmente de `circle`.

Criterio de migracion:

1. Extraer `CircleSpec`, builder y normalizador.
2. Extraer construccion de geometria circular, operacion y working step.
3. Mover hidratacion exacta circular.
4. Mantener reexports publicos.
5. Validar con tests de sintesis circular, estrategia helicoidal y adaptacion
   `GeomCircle`.

Puntos abiertos:

- Definir si `circle.py` queda como familia permanente o como wrapper
  especializado sobre `profile.py`.

## Item 16 - Alcance Propuesto Para `pgmx.synthesis.milling.squaring`

Fecha: 2026-06-03

Modulo objetivo:

- `pgmx/synthesis/milling/squaring.py`

Rol propuesto:

- Ser el modulo productivo para escuadrado exterior del contorno de la pieza.
- Representar un mecanizado de fresado completo sobre el perimetro, no una
  polilinea generica.

Responsabilidades incluidas:

- Contrato publico actual:
  - `ContourSpec`;
  - `build_contour_spec(...)`;
  - normalizacion de `start_edge`, `winding` y `start_coordinate`.
- Defaults productivos actuales:
  - herramienta `1900` / `E001`;
  - ancho `18.36`;
  - profundidad pasante con `extra_depth = 1.0`;
  - approach/retract en arco, modo `Quote`, radio `2.0`, lado `Automatic`.
- Reglas de lado:
  - `side_of_feature` derivado del `winding`;
  - no expuesto como campo independiente.
- Construccion productiva:
  - contorno exterior segun dimensiones de pieza;
  - feature de perfil general;
  - operacion `BottomAndSideFinishMilling`;
  - working step.
- Adaptacion:
  - detectar firma de escuadrado desde snapshots antes de tratar el caso como
    polilinea comun.

Responsabilidades excluidas:

- No debe manejar cualquier polilinea rectangular; solo escuadrado de pieza.
- No debe manejar pocket milling ni contornos internos.
- No debe definir dimensiones de pieza; debe consumir `common.piece`.
- No debe decidir estrategias generales.

Relaciones:

- `common.piece` aporta dimensiones y caras de la pieza.
- `common.geometry` construye el contorno.
- `common.strategy`, `common.leads`, `common.depth` y `common.tools` aportan
  reglas transversales.
- `milling.profile` puede compartir la escritura de operacion, pero el
  significado de escuadrado queda en este modulo.

Criterio de migracion:

1. Extraer `ContourSpec`, builder y normalizador.
2. Extraer deteccion/construccion del contorno exterior.
3. Mover `_append_squaring_milling(...)` y helpers asociados.
4. Mantener deteccion de adapter antes de `PolylineSpec`.
5. Validar con tests de escuadrado y combinaciones con taladros/fresados.

Puntos abiertos:

- Definir si escuadrados parciales o por caras pasan por este modulo o por una
  familia nueva.

## Item 17 - Alcance Propuesto Para `pgmx.synthesis.milling.pocket`

Fecha: 2026-06-03

Modulo objetivo:

- `pgmx/synthesis/milling/pocket.py`

Rol propuesto:

- Ser el modulo productivo unico para `ClosedPocket` / pocket milling.
- Absorber el mecanizado historico llamado `Vaciado` como caso de esta familia.
- Promover desde el laboratorio solo reglas cerradas, con tests y evidencia
  Maestro.

Responsabilidades incluidas:

- Contratos actuales y futuros:
  - `PocketSpec`;
  - `PocketBossRouteSeedSpec`;
  - `build_pocket_spec(...)`;
  - `build_pocket_boss_route_seed_spec(...)`;
  - wrappers historicos necesarios mientras migra `pgmx.vaciado`.
- Alcance productivo actual:
  - `ClosedPocket` superior sobre `Top`;
  - contornos cerrados lineales;
  - islas cuando la serializacion/regla este cerrada;
  - estrategia `ContourParallelMillingStrategySpec`;
  - allowances de fondo y lateral;
  - rutas/semillas de islas cuando sean resolubles.
- Reglas propias:
  - `effective_contour_offset = tool_width / 2 + allowance_side`;
  - `radial_step = tool_width * (1 - overlap)`;
  - validacion de contornos cerrados;
  - resolucion de bosses/islas;
  - promocion de reglas generativas puras solo desde casos validados.
- Hidratacion:
  - conservar template exacto cuando el caso no tenga regla generativa cerrada;
  - rechazar reuse si difieren contorno, islas, profundidad, herramienta,
    estrategia, allowances o leads.
- Adaptacion:
  - convertir snapshots `ClosedPocket` a `PocketSpec` para lectura;
  - reportar claramente cuando la serializacion productiva de un caso aun no
    esta implementada.
- Integracion historica:
  - retirar como destino final `pgmx.vaciado`;
  - retirar como destino final `pgmx.vaciado_lab`;
  - migrar el laboratorio a `pgmx.machining_lab.pocket_milling`.

Responsabilidades excluidas:

- No debe ser un modulo generico de offsets para cualquier perfil.
- No debe depender productivamente del laboratorio.
- No debe mezclar parametros de `ContourParallel` con estrategias similares de
  otras familias.
- No debe postprocesar ISO; eso pertenece a `iso_state_synthesis`.
- No debe mantener nombres publicos `Vaciado` como contrato final, salvo
  fachadas temporales de compatibilidad.

Relaciones:

- `common.geometry` aporta soporte basico para contornos cerrados.
- Reglas complejas de offsets, bridges, bosses y trazas pertenecen a este
  modulo o al laboratorio, no a `common.geometry`.
- `common.strategy` aporta el contrato `ContourParallel`, pero los defaults y
  restricciones de pocket se aplican aqui.
- `common.hydration` aporta templates/source-pgmx.
- `common.program` coordina escritura y orden.
- `pgmx.machining_lab.pocket_milling` investiga reglas no promovidas.

Criterio de migracion:

1. Extraer `PocketSpec`, `PocketBossRouteSeedSpec` y builders.
2. Mover normalizacion y validacion de contornos/islas.
3. Mover generacion `ClosedPocket`, estrategias, boss lists y working steps.
4. Migrar reglas cerradas desde `pgmx.vaciado_lab` sin arrastrar el laboratorio.
5. Dejar fachadas historicas solo mientras los imports externos existan.
6. Validar con tests de vaciado, v2, adapters y corpus generado.

Puntos abiertos:

- Definir si `PocketSpec` queda como contrato publico final o si se crea
  una spec nueva con nombre de familia Maestro.
- Definir la frontera exacta entre regla productiva y laboratorio cuando una
  familia de islas queda parcialmente cerrada.

## Item 18 - Alcance Propuesto Para `pgmx.synthesis.drilling.single`

Fecha: 2026-06-03

Modulo objetivo:

- `pgmx/synthesis/drilling/single.py`

Rol propuesto:

- Ser el modulo productivo para taladros puntuales Maestro sobre caras de la
  pieza.
- Aplicar la regla general acordada: todos los taladros conservan `ToolKey` no
  resuelto hasta Maestro/postproceso, salvo que el usuario pida explicitamente
  una herramienta.

Responsabilidades incluidas:

- Contrato publico actual:
  - `DrillSpec`;
  - `build_drill_spec(...)`;
  - normalizacion de punto, diametro, cara, profundidad y familia de broca.
- Caras soportadas:
  - `Top`;
  - `Front`;
  - `Back`;
  - `Right`;
  - `Left`.
- Reglas de herramienta:
  - `tool_resolution = "Auto"` por defecto;
  - `tool_id = "0"` y `tool_name = ""` como estado no resuelto;
  - soporte para herramienta explicita solo como excepcion consciente;
  - verticales de cara superior incluidos en la misma regla.
- Reglas de profundidad:
  - taladros pasantes y no pasantes;
  - familia `Flat`/`Conical`;
  - compatibilidad con expresiones de profundidad cuando corresponda.
- Construccion productiva:
  - feature de taladro;
  - operacion `DrillingOperation`;
  - working step;
  - entrada/direccion segun cara de pieza.
- Adaptacion:
  - convertir snapshots `RoundHole` puntuales en `DrillSpec`;
  - conservar herramienta explicita solo si el snapshot la trae resuelta.

Responsabilidades excluidas:

- No debe manejar patrones repetidos; eso pertenece a `drilling.pattern`.
- No debe resolver herramienta final de produccion; Maestro/postproceso e
  `iso_state_synthesis` toman esa decision.
- No debe modelar fresado circular como taladro.
- No debe depender del laboratorio.

Relaciones:

- `common.piece` aporta caras, ejes y dimensiones locales.
- `common.depth` aporta profundidad efectiva y expresiones.
- `common.tools` aplica la politica de herramienta no resuelta.
- `common.geometry` aporta puntos.
- `common.program` coordina escritura.

Criterio de migracion:

1. Extraer `DrillSpec`, builder, normalizador y helpers de eje/cara.
2. Mover construccion de feature/operacion/working step de taladro.
3. Mover reglas de profundidad y ToolKey no resuelto hacia helpers comunes
   cuando sean reutilizables.
4. Mantener reexports publicos.
5. Validar con tests de taladros por cara, tool auto/explicit y sintesis.

Puntos abiertos:

- Definir si los helpers de eje de taladro viven en `common.piece` o quedan en
  `drilling.single` con fachada comun.

## Item 19 - Alcance Propuesto Para `pgmx.synthesis.drilling.pattern`

Fecha: 2026-06-03

Modulo objetivo:

- `pgmx/synthesis/drilling/pattern.py`

Rol propuesto:

- Ser el modulo productivo para patrones rectangulares de taladros Maestro
  serializados como `ReplicateFeature`.
- Reutilizar la semantica de `drilling.single` para el taladro base.

Responsabilidades incluidas:

- Contrato publico actual:
  - `DrillPatternSpec`;
  - `build_drill_pattern_spec(...)`;
  - normalizacion de punto base, diametro, columnas, filas, separaciones y
    profundidad.
- Alcance actual:
  - patron rectangular;
  - `RotationAngle = 0`;
  - `RowLayoutAngle = 90`;
  - al menos dos huecos;
  - base feature `RoundHole`.
- Reglas compartidas:
  - misma politica de `ToolKey` no resuelto que `drilling.single`;
  - mismas caras, profundidad y familia de broca;
  - reutilizacion del taladro base hidratado/normalizado.
- Construccion productiva:
  - feature base;
  - `ReplicationPattern`;
  - feature replicada;
  - operacion `DrillingOperation`;
  - working step;
  - expresiones de profundidad de patron cuando correspondan.
- Adaptacion:
  - convertir snapshots `ReplicateFeature` compatibles en
    `DrillPatternSpec`;
  - marcar como no soportados patrones rotados, no rectangulares o con
    profundidad/herramienta no representable.

Responsabilidades excluidas:

- No debe modelar un unico taladro; para eso se usa `DrillSpec`.
- No debe manejar patrones circulares o arbitrarios sin evidencia Maestro.
- No debe resolver herramienta final.
- No debe duplicar toda la logica de `drilling.single`; debe reutilizarla.

Relaciones:

- `drilling.single` aporta la definicion del taladro base.
- `common.piece`, `common.depth`, `common.tools`, `common.geometry` y
  `common.program` aportan reglas transversales.
- `pgmx.adapters` lee snapshots y puede delegar validaciones de patron.

Criterio de migracion:

1. Extraer `DrillPatternSpec`, builder y normalizador.
2. Extraer helpers de `ReplicateFeature` y expresiones de profundidad.
3. Reutilizar la hidratacion/normalizacion de `drilling.single` para el taladro
   base.
4. Mantener reexports publicos.
5. Validar con tests de patron rectangular, rechazo de patron invalido y
   sintesis.

Puntos abiertos:

- Definir si patrones no rectangulares entran en este modulo con otra spec o en
  un modulo futuro.

## Item 20 - Alcance Propuesto Para `pgmx.machining_lab`

Fecha: 2026-06-03

Modulo/directorio objetivo:

- `pgmx/machining_lab/`

Rol propuesto:

- Ser el laboratorio general de investigacion del sintetizador PGMX.
- Reemplazar laboratorios con nombre historico de mecanizado, especialmente
  `pgmx/vaciado_lab`.
- Permitir que cada familia tenga evidencia, memoria y comandos reproducibles
  antes de promover reglas a produccion.

Subdirectorios objetivo:

- `pocket_milling/`;
- `line_milling/`;
- `slot_milling/`;
- `profile_milling/`;
- `squaring/`;
- `drilling/`.

Responsabilidades incluidas:

- Guardar memorias vivas por familia:
  - `memory/current-state.md`;
  - ledger de casos cerrados/parciales/pendientes;
  - comandos de generacion y validacion;
  - fixtures o rutas externas documentadas.
- Alojar scripts de estudio cuando haya una pregunta abierta real.
- Servir como frontera entre investigacion y produccion:
  - laboratorio estudia;
  - modulo `pgmx.synthesis.*` produce.

Responsabilidades excluidas:

- No debe ser dependencia directa de produccion.
- No debe ser API publica.
- No debe contener fachadas historicas bajo `tools/` salvo transicion
  documentada.

Criterio de migracion:

1. Crear README general.
2. Migrar `pgmx/vaciado_lab` a `pgmx/machining_lab/pocket_milling`.
3. Dejar fachadas historicas solo mientras los comandos/tests migran.
4. Crear laboratorios nuevos solo cuando exista una investigacion concreta.
5. Actualizar documentacion y tests de importacion.

Puntos abiertos:

- Definir para cada familia el comando canonico de regeneracion/validacion de
  corpus.
- Definir cuando se considera que una regla sale del laboratorio y entra en
  produccion.

## Decision Transversal - `Vaciado` Absorbido Por `milling.pocket`

Fecha: 2026-06-03

- Decision aceptada: `Vaciado` no tendra modulo productivo separado ni contrato
  V2 propio como paquete final.
- El contrato experimental `pgmx.vaciado` debe desaparecer como frontera propia
  y su contenido util debe integrarse en `pgmx.synthesis.milling.pocket`.
- El destino productivo de este mecanizado es `pgmx.synthesis.milling.pocket`,
  porque corresponde a la familia Maestro `ClosedPocket`/cajeado/pocket.
- `pgmx.vaciado_lab` tambien debe desaparecer como paquete final.
- El laboratorio general de esta familia se llamara
  `pgmx.machining_lab.pocket_milling`, no `pgmx.machining_lab.vaciado`.
- Las fachadas historicas pueden mantenerse temporalmente por compatibilidad,
  pero no deben contener logica nueva ni quedar como aliases permanentes.

## Decision Transversal - `program.py` Dentro De `common`

Fecha: 2026-06-03

- Decision aceptada: el modulo de programa pertenece a
  `pgmx.synthesis.common.program`.
- `common.program` contiene el estado y la orquestacion transversal del PGMX:
  request, `PgmxState`, baseline, worksteps, aplicacion de mecanizados,
  expresiones, reserva de IDs y escritura final.
- No es una familia de mecanizado y no debe quedar al mismo nivel que
  `milling/` o `drilling/`.
- `pgmx.synthesis.core` puede mantener fachadas temporales durante la migracion,
  pero la ubicacion objetivo es `common.program`.

## Cierre Del Registro De Modulos Del Mapa Objetivo

Fecha: 2026-06-03

Con los items anteriores, el mapa objetivo queda registrado para:

- `pgmx.synthesis.__init__`;
- `pgmx.synthesis.core`;
- `pgmx.synthesis.common.program`;
- `pgmx.synthesis.common.xml`;
- `pgmx.synthesis.common.geometry`;
- `pgmx.synthesis.common.depth`;
- `pgmx.synthesis.common.piece`;
- `pgmx.synthesis.common.tools`;
- `pgmx.synthesis.common.strategy`;
- `pgmx.synthesis.common.hydration`;
- `pgmx.synthesis.common.leads`;
- `pgmx.synthesis.milling.line`;
- `pgmx.synthesis.milling.slot`;
- `pgmx.synthesis.milling.profile`;
- `pgmx.synthesis.milling.circle`;
- `pgmx.synthesis.milling.squaring`;
- `pgmx.synthesis.milling.pocket`;
- `pgmx.synthesis.drilling.single`;
- `pgmx.synthesis.drilling.pattern`;
- `pgmx.machining_lab`.

Este registro es memoria temporal de arquitectura. No implica movimiento de
codigo todavia. La implementacion debe avanzar por migraciones controladas,
manteniendo reexports, tests y comportamiento actual.

