# Auditoria Del Subsistema App

Estado: bloque auditado y cerrado para esta etapa, 2026-06-06.

Este documento registra la lectura actual del subsistema `app/`. Su objetivo es
separar la frontera real de la UI, los flujos donde interviene cada grupo de
modulos y las deudas que conviene tratar en cortes posteriores.

## Frontera

`app/` es la capa desktop PySide6. Debe orquestar interaccion, dialogos,
seleccion de archivos/carpetas y mensajes al usuario, pero no debe convertirse
en fuente primaria de reglas de dominio.

Fronteras actuales:

- dominio de proyectos y piezas: `core.model`, `core.parser`, `app.project_store`;
- PGMX: `pgmx.processing`, `pgmx.snapshot`, `pgmx.adapters`, `pgmx.synthesis`;
- diagramas de corte: `core.nesting_service`;
- planillas/PDF: `core.production_sheet*`;
- ISO experimental: `iso_state_synthesis.emitter`;
- composicion En-Juego: UI en `app.project_detail_en_juego_*`, sintesis en
  `core.en_juego_synthesis`.

## Entradas

| Entrada | Rol |
| --- | --- |
| `main.py` | Ejecuta `app.ui.run_app()`. |
| `app.ui.run_app` | Crea `QApplication`, instancia `MainWindow` y entra en el loop Qt. |
| `app.main_window.MainWindow` | Lista, crea, abre y elimina proyectos. |
| `app.ui.ProjectDetailWindow` | Compone la ventana de detalle con mixins de procesamiento, modulos, inspeccion y salida. |

`ProjectDetailWindow` hereda de:

- `ProjectDetailCoreMixin`;
- `ProjectDetailProcessingMixin`;
- `ProjectDetailModulesMixin`;
- `ProjectDetailInspectionMixin`;
- `ProjectDetailOutputMixin`;
- `QMainWindow`.

## Grupos De Modulos

| Grupo | Modulos | Rol |
| --- | --- | --- |
| Shell de app | `ui`, `main_window`, `runtime`, `qt_helpers`, `ui_constants` | Arranque, ventana principal y utilidades Qt compartidas. |
| Proyecto y persistencia | `project_store`, `project_registry`, `project_dialogs` | Registro, carga/guardado y dialogos de proyecto/local. |
| Detalle base | `project_detail_core`, `project_detail_processing`, `project_detail_modules`, `project_detail_inspection`, `project_detail_output` | Flujos principales del detalle de proyecto. |
| Piezas | `project_detail_piece_*`, `project_detail_selected_piece_actions`, `project_detail_drawings`, `project_detail_pgmx`, `project_detail_programs` | Tabla, editor, acciones, PGMX asociado y dibujos SVG. |
| Colores y selectores | `project_detail_colors`, `project_detail_color_changes`, `project_detail_selectors` | Cambios de color por alcance y dialogos editables. |
| En-Juego UI | `project_detail_en_juego_*` | Dialogo, layout, preview, cotas, settings y salida PGMX compuesta. |
| Opciones | `options_dialogs`, `options_helpers`, `settings` | Configuracion de tableros, herramientas, cortes, plantillas, rutas y En-Juego. |

## Flujos Principales

| Flujo | Entrada UI | Modulos App | Dependencias Externas |
| --- | --- | --- | --- |
| Crear/abrir proyecto | `MainWindow.create_project`, `open_project` | `main_window`, `project_dialogs`, `project_store`, `project_registry` | `core.model`. |
| Procesar seleccion | `ProjectDetailWindow.process_project` | `project_detail_processing`, helpers de `project_detail_core` | `core.parser`, `pgmx.processing`, `core.summary`. |
| Listar/ordenar modulos | `ProjectDetailWindow.show_modules` | `project_detail_modules`, `project_detail_core` | `app.project_store`, `core.model`. |
| Inspeccionar modulo | `ProjectDetailWindow.inspect_module` | `project_detail_inspection`, `project_detail_piece_*`, `project_detail_pgmx`, `project_detail_drawings` | `pgmx.processing`, `core.model`. |
| Configurar En-Juego | Boton `Configurar En Juego` | `project_detail_en_juego_*`, `project_detail_inspection` | `core.en_juego_transform`, `core.en_juego_synthesis`, `pgmx.processing`. |
| Diagramas de corte | `ProjectDetailWindow.show_cuts` | `project_detail_output` | `core.nesting_service.generate_cut_diagrams`. |
| Planillas/estructura CNC/ISO | `ProjectDetailWindow.generate_sheets` | `project_detail_output` | `core.production_sheet*`, `pgmx.processing`, `iso_state_synthesis.emitter`. |

## Comentarios Y Docstrings

El codigo tiene docstrings de modulo en la mayoria de archivos y comentarios
operativos en bloques complejos. Eso ayuda a ubicar el tema de cada modulo, pero
no alcanza por si solo para auditar el sistema leyendo solo comentarios.

Observaciones:

- No aparecen `TODO`/`FIXME` activos en `app/`.
- Los comentarios utiles explican operaciones puntuales, como relectura de
  `module_config.json`, creacion de configuracion base o reintentos de salida.
- Muchas reglas importantes viven en nombres de funciones y en la estructura de
  callbacks anidados, no en comentarios.
- Para auditoria real, este documento y `docs/repository_audit_inventory.md`
  son necesarios como mapa externo.

## Correcciones Aplicadas En Este Corte

- `app.project_detail_processing` ahora importa `QApplication`, requerido por
  `QApplication.processEvents()` durante el procesamiento.
- `app.project_detail_output` ahora importa `QApplication`, requerido por
  `QApplication.processEvents()` durante la generacion de planillas/salidas.
- `app.project_detail_core` ahora importa `_show_centered`, requerido por
  `edit_project()`.
- `app.project_detail_output.show_cuts()` usa
  `core.nesting_service.generate_cut_diagrams`, que es la API productiva actual.
- Se retiraron imports no usados de `core.nesting.generate_cut_diagrams` en
  mixins que no generan diagramas.

## Subcorte `project_detail_output`

Estado: auditado y limpiado, 2026-06-05.

Responsabilidades actuales:

- `show_cuts()`: lee settings de corte, llama a
  `core.nesting_service.generate_cut_diagrams` y reporta el resultado al
  usuario.
- `generate_sheets()`: crea estructura de salida CNC, regenera dibujos, emite
  ISO candidato desde PGMX, genera PDFs por local y opcionalmente Excel.
- Helpers privados de salida: nombres seguros, rutas relativas al proyecto,
  carpeta CNC por proyecto/modulo y nombres ISO sin colision.

Correcciones del subcorte:

- Se redujo el bloque de imports a las dependencias usadas por el modulo.
- Se eliminaron imports locales duplicados dentro de
  `_export_project_iso_files()` y `generate_sheets()`.
- Se agrego `tests/test_project_detail_output.py` para helpers puros de rutas,
  nombres y deduplicacion de ISO.

## Subcorte `project_detail_processing`

Estado: auditado y limpiado, 2026-06-05.

Responsabilidades actuales:

- `add_locale()`: crea un local nuevo, escribe configuracion base y actualiza
  el proyecto persistido.
- `_ensure_project_structure_ready()`: detecta modulos sueltos en la raiz y
  pide un local destino antes de procesar.
- `process_project()`: escanea locales/modulos, resuelve reprocesamiento,
  normaliza piezas, escribe configs, exporta resumen y genera dibujos SVG.

Correcciones del subcorte:

- Se redujo el bloque de imports a las dependencias usadas por el mixin.
- Se eliminaron imports locales duplicados dentro de
  `_ensure_project_structure_ready()` y `process_project()`.
- Se mantuvo intacto el flujo largo de `process_project()`; por ahora queda
  documentado como frontera a cubrir con mocks antes de refactors internos.

## Subcorte `project_detail_inspection`

Estado: auditado con limpieza minima, 2026-06-05.

Responsabilidades actuales:

- `inspect_module()`: abre el dialogo de piezas del modulo seleccionado.
- Construye la tabla de piezas, acciones laterales, panel de settings,
  reparacion PGMX, dibujos SVG, cambios de color y configuracion En-Juego.
- Coordina helpers ya extraidos en `project_detail_piece_*`,
  `project_detail_pgmx`, `project_detail_drawings`,
  `project_detail_module_persistence` y `project_detail_en_juego_*`.

Correcciones del subcorte:

- `get_pgmx_program_dimension_notes` quedo declarado como dependencia de
  modulo en lugar de reimportarse dentro de callbacks internos.
- El preview de programas PGMX huerfanos se movio a
  `project_detail_piece_rows`.
- Las reglas puras de seleccion/movimiento de filas visibles se movieron a
  `project_detail_piece_table_rows`.
- Las acciones de editar y eliminar pieza seleccionada se movieron a
  `project_detail_selected_piece_actions`.
- La confirmacion de guardado/cierre del dialogo de inspeccion se movio a
  `project_detail_dialog_lifecycle`.
- Se agregaron tests focalizados para estas extracciones.
- No se dividio `inspect_module()` en este corte. La funcion sigue siendo el
  ensamblador principal del dialogo y debe modularizarse con tests especificos
  de callbacks/estado antes de extraer bloques.

## Subcorte En-Juego UI

Estado: auditado y limpiado, 2026-06-06.

Responsabilidades actuales:

- `project_detail_en_juego_configuration`: ensambla el dialogo principal,
  escena, lista de piezas, controles, persistencia de layout y creacion PGMX.
- `project_detail_en_juego_dialogs`: construye paneles y dialogos secundarios
  de division/escuadrado.
- `project_detail_en_juego_settings`, `state`, `layout`, `view`, `preview`,
  `dimensions` y `output`: concentran reglas auxiliares ya testeadas.

Correcciones del subcorte:

- El calculo de separacion efectiva entre piezas se movio a
  `project_detail_en_juego_settings.en_juego_effective_piece_spacing_mm`.
- El filtro de filas configurables para En-Juego se movio a
  `project_detail_en_juego_state.configurable_en_juego_rows`.
- El espesor material efectivo, la normalizacion de layout guardado y la
  escritura de layout/composicion se movieron a
  `project_detail_en_juego_state`.
- El refresco de controles manual/nesting se movio a
  `project_detail_en_juego_dialogs.apply_en_juego_cut_mode_controls`.
- Se agregaron tests focalizados para estas reglas.

## Subcorte Opciones Y Settings

Estado: auditado y limpiado, 2026-06-06.

Responsabilidades actuales:

- `options_dialogs`: dialogos Qt para tableros, herramientas, cortes, rutas y
  plantillas manuales.
- `settings`: normalizacion, lectura/escritura y defaults de configuracion de
  app, tableros, herramientas, cortes y En-Juego.

Correcciones del subcorte:

- La validacion pura de medidas no negativas se movio a
  `options_helpers.parse_non_negative_measure`.
- `PieceTemplateEditDialog` reutiliza `configured_board_colors`,
  `preferred_color_index` y `parse_optional_piece_float` en lugar de duplicar
  reglas.
- Se corrigieron imports faltantes de `QInputDialog` y
  `normalize_piece_grain_direction`.
- Se agrego `tests/test_options_helpers.py`.

## Cierre Del Bloque App

El bloque `app/` queda cerrado para esta etapa de reorganizacion/auditoria:

- fronteras de UI y dependencias externas documentadas;
- imports faltantes corregidos;
- dependencias obsoletas hacia `core.nesting.generate_cut_diagrams` retiradas
  de los mixins del detalle;
- reglas puras extraidas de salida, procesamiento, inspeccion, En-Juego y
  opciones;
- cobertura focalizada agregada para los helpers extraidos.

## Deuda Residual Aceptada

- `options_dialogs.py`, `settings.py`, `project_detail_en_juego_dialogs.py` y
  el cuerpo interno de `project_detail_inspection.inspect_module()` siguen
  siendo bloques grandes, pero sus fronteras y reglas auxiliares principales
  quedan documentadas/testeadas.
- Hay varios `except Exception` silenciosos o muy amplios en helpers de UI y
  persistencia. No todos son bugs, pero deben revisarse si se audita
  observabilidad o recuperacion de errores.
- Los flujos completos `process_project`, `show_cuts` y `generate_sheets`
  tienen poca cobertura directa por su dependencia de Qt, dialogos y
  filesystem; conviene agregar tests con mocks antes de refactors profundos.
