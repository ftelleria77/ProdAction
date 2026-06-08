# Inventario De Auditoria Del Repositorio

Estado: inventario operativo cerrado para auditoria general, 2026-06-07.

Este documento es la base de trabajo para auditar ProdAction modulo por modulo y
actualizar la documentacion vigente. No reemplaza las guias publicas; sirve para
mantener una matriz de control mientras se revisan los subsistemas.

## Regla De Lectura

- Cierre de la pasada general: `docs/general_audit_closure.md`.
- Codigo productivo: `app/`, `core/`, `pgmx/`, `iso_state_synthesis/` y
  `cnc_traceability/`.
- Laboratorios reproducibles: `tools/studies/` y
  `pgmx/machining_lab/pocket_milling/`.
- Documentacion vigente: `README.md`, `docs/README.md`,
  `docs/repo_study_guide.md`, `docs/architecture_reorganization.md`,
  `docs/laboratory_frontiers.md` y guias `*_help.md`.
- Memorias historicas: archivos `*_temporary_memory.md`, `memory/*.md` y
  `experiments/*.md`. Se corrigen solo si pueden confundirse con instrucciones
  vigentes; si no, se preservan como historial.

## Mapa General

| Subsistema | Rol | Procesos Donde Interviene | Tests Principales | Docs Relacionados |
| --- | --- | --- | --- | --- |
| `app/` | Aplicacion desktop PySide6 y flujos de UI. | Seleccion de proyectos, edicion de proyectos, inspeccion de modulos, acciones PGMX, En-Juego, exportaciones. | `tests/test_project_*`, `tests/test_production_*`. | `README.md`, `docs/repo_study_guide.md`, `docs/app_subsystem_audit.md`. |
| `core/` | Dominio compartido, parser, planillas, PDF, nesting y En-Juego. | Escaneo de proyectos, modelo de datos, resumen CSV, planillas Excel/PDF, diagramas de corte, composicion En-Juego. | `tests/test_core_*.py`, `tests/test_nesting_*`, `tests/test_summary_exports.py`, `tests/test_production_*`. | `docs/repo_study_guide.md`, `docs/core_subsystem_audit.md`, `docs/cut_diagrams_temporary_memory.md`, `docs/en_juego_synthesis_temporary_memory.md`. |
| `pgmx/` | Subsistema PGMX productivo. | Lectura de programas, dibujos de piezas, snapshot, adaptacion, sintesis PGMX, laboratorio pocket milling. | `tests/test_pgmx_*`, `tests/test_project_detail_pgmx.py`. | `docs/pgmx_subsystem_audit.md`, `docs/synthesize_pgmx_help.md`, `docs/pgmx_snapshot_help.md`, `docs/pgmx_adapters_help.md`, `docs/pgmx_synthesis_modularization_plan.md`, `pgmx/machining_lab/README.md`. |
| `iso_state_synthesis/` | Sintesis ISO experimental basada en estados. | Lectura de snapshot PGMX, plan de estados, diferencial, emision candidata ISO, comparacion. | `tests/test_iso_state_synthesis.py`. | `docs/iso_state_synthesis_subsystem_audit.md`, `iso_state_synthesis/README.md`, `iso_state_synthesis/memory/current-state.md`, `docs/iso_cnc_contract.md`. |
| `cnc_traceability/` | Visor CNC standalone compatible con Windows XP. | Lectura de indice, seguimiento de mecanizado, preparacion USBMIX, previews de piezas. | `tests/test_cnc_traceability.py` para helpers puros; UI/XP queda manual. | `docs/cnc_traceability_subsystem_audit.md`, `cnc_traceability/README.md`, `cnc_traceability/docs/contract.md`. |
| `tools/studies/` | Estudios reproducibles archivados. | Generacion de fixtures ISO, auditorias de corpus, laboratorio de ordenamiento de corte. | Se validan por `compileall`, imports/ejecucion puntual y corpus externo cuando aplica. | `docs/tools_studies_subsystem_audit.md`, `tools/studies/README.md`, `tools/studies/iso/README.md`. |
| `tests/` | Cobertura automatizada. | Verificacion de contratos publicos, helpers de UI, nesting, PGMX y planillas. | `py -3 -m unittest discover -s tests -p "test*.py"`. | Este inventario y docs de subsistema. |

## Cierre General 2026-06-07

La auditoria general queda cerrada para esta etapa. El resumen estable vive en
`docs/general_audit_closure.md`; este inventario queda como matriz de consulta
por subsistema, modulo, proceso, tests y documentacion.

No hay un bloque general pendiente de primera auditoria. Los pendientes
restantes son deuda aceptada o frentes especificos: validacion XP real de
`cnc_traceability/`, cobertura manual/corpus externo para `tools/studies/`,
reactivacion funcional opcional de `iso_state_synthesis/`, reproducibilidad de
dependencias y refinamientos puntuales de flujos amplios cuando aparezca una
necesidad funcional.

## Procesos Transversales

| Proceso | Entrada | Modulos Principales | Salida |
| --- | --- | --- | --- |
| App desktop | `main.py` | `app.ui`, `app.main_window`, mixins `app.project_detail_*`, `app.project_store`, `app.settings`. | UI de gestion de proyectos y modulos. |
| Escaneo de proyecto | Carpeta raiz de proyecto | `core.parser`, `core.model`, `app.project_store`. | `Project`, `LocaleData`, `ModuleData`, `Piece`. |
| Inspeccion de modulo | Proyecto + modulo | `app.project_detail_inspection`, `app.project_detail_piece_*`, `pgmx.processing`. | Tabla editable de piezas, programas, dibujos y estado. |
| PGMX lectura/dibujo | `.pgmx` o referencia de pieza | `pgmx.processing`, `pgmx.snapshot`, `pgmx.adapters`. | Dimensiones, operaciones, notas, SVG, issues de ranuras. |
| PGMX sintesis | Specs publicos + baseline Maestro | `pgmx.synthesis`, `pgmx.synthesis.common`, `pgmx.synthesis.milling`, `pgmx.synthesis.drilling`. | Archivo `.pgmx` sintetizado. |
| En-Juego | Piezas seleccionadas + PGMX existentes | `core.en_juego_synthesis`, `core.en_juego_transform`, `app.project_detail_en_juego_*`. | PGMX compuesto y estado persistido en modulo. |
| Planillas | `Project` | `core.production_sheet`, `core.production_sheet_data`, `core.production_sheet_images`, `core.production_sheet_pdf`. | Excel/PDF de produccion. |
| Diagramas de corte | `Project` + configuracion de tableros | `core.nesting_service`, `core.nesting_*`, `tools/studies/cut_diagrams/ordering_lab.py`. | PDF de diagramas de corte y placements. |
| ISO experimental | `.pgmx` + corpus ISO observado | `iso_state_synthesis.pgmx_source`, `differential`, `catalog`, `emitter`. | Plan/evaluacion/candidato ISO explicable. |
| Trazabilidad CNC | Indice de proyectos y archivos ISO | `cnc_traceability.viewer_xp`. | UI XP para estado de mecanizado y preparacion USB. |

## Inventario `app/`

| Modulo | Funcion En El Sistema | API Publica Principal |
| --- | --- | --- |
| `app.ui` | Entrada de la UI principal y ventana de detalle. | `run_app`, `ProjectDetailWindow`. |
| `app.main_window` | Ventana de seleccion/listado de proyectos. | `MainWindow`. |
| `app.project_dialogs` | Dialogos de creacion/edicion de proyectos y locales. | `EditLocalesDialog`, `EditProjectWindow`, `NewProjectDialog`. |
| `app.project_store` | Carga/persistencia de proyectos. | `load_project` y helpers internos de normalizacion/guardado. |
| `app.project_registry` | Registro persistente de proyectos. | Helpers internos `_read_registry`, `_write_registry`, `_find_registry_entry`. |
| `app.settings` | Configuracion global, herramientas, cortes y En-Juego. | `read_app_settings`, `normalize_cut_optimization_option`. |
| `app.runtime` | Rutas runtime de la app. | Constantes y helper interno de base dir. |
| `app.qt_helpers` | Helpers de ventanas/dialogos Qt. | Helpers internos compartidos. |
| `app.project_detail_dialog_lifecycle` | Confirmacion de guardado/cierre en dialogos del detalle. | `confirm_save_before_close`, `close_dialog_if_confirmed`, `install_reject_confirmation`. |
| `app.options_dialogs` | Dialogos de opciones generales. | `OptionsDialog`, `BoardsDialog`, `ToolsDialog`, `CutsDialog`, `PathsDialog`. |
| `app.options_helpers` | Helpers puros de dialogos de opciones. | `parse_non_negative_measure`. |
| `app.project_detail_core` | Estado y persistencia del detalle de proyecto. | `ProjectDetailCoreMixin`. |
| `app.project_detail_processing` | Procesamiento de proyectos/locales/modulos. | `ProjectDetailProcessingMixin`. |
| `app.project_detail_modules` | Listado y edicion tabular de modulos. | `ProjectDetailModulesMixin`. |
| `app.project_detail_inspection` | Inspeccion y edicion de piezas de modulo. | `ProjectDetailInspectionMixin`. |
| `app.project_detail_output` | Salidas: diagramas, planillas, dibujos, ISO. | `ProjectDetailOutputMixin`. |
| `app.project_detail_piece_rows` | Normalizacion/serializacion de filas de pieza. | `build_piece_from_row`, `serialize_piece_rows_for_config`, `build_module_pieces_from_rows`. |
| `app.project_detail_piece_table` | Construccion/configuracion de tabla de piezas. | `create_piece_table`, `configure_piece_table`. |
| `app.project_detail_piece_table_rows` | Render de filas y textos de programa/observaciones. | `render_piece_table_rows`, `filtered_piece_table_rows`. |
| `app.project_detail_piece_editor` | Valores y rows del editor de pieza. | `PieceEditorValues`, `build_piece_editor_row`. |
| `app.project_detail_piece_editor_dialog` | Dialogo Qt de alta/edicion de piezas. | `open_piece_editor_dialog`, `PieceEditorDialogContext`. |
| `app.project_detail_piece_actions` | Botonera lateral de acciones de pieza. | `ProjectDetailPieceActions`, `build_project_detail_piece_actions`. |
| `app.project_detail_selected_piece_actions` | Acciones sobre pieza seleccionada. | `select_source_for_selected_piece`, `edit_selected_piece`, `remove_selected_piece`, `repair_selected_invalid_pgmx`, `view_drawing_for_selected_piece`. |
| `app.project_detail_programs` | Seleccion/asignacion/apertura de programas PGMX. | `select_pgmx_program_file`, `assign_program_source_to_row`, `open_piece_program_in_default_app`. |
| `app.project_detail_pgmx` | Cache y mensajes de issues PGMX. | `invalid_slot_cache_key`, `get_cached_invalid_slot_issues`, `invalid_slot_message`. |
| `app.project_detail_drawings` | Creacion, borrado y apertura de dibujos SVG. | `ensure_piece_drawing_file`, `refresh_piece_drawing_file`, `open_piece_drawing_dialog`. |
| `app.project_detail_colors` | Colores de piezas y cambios por alcance. | `open_board_color_picker`, `apply_color_to_piece_row`, `apply_color_to_matching_rows`. |
| `app.project_detail_color_changes` | Aplicacion de cambios de color por modulo/ambiente. | `ColorChangeScopeResult`, `apply_scoped_color_change`. |
| `app.project_detail_selectors` | Dialogos de seleccion editable. | `EditableSelectionConfig`, `open_editable_selection_dialog`. |
| `app.project_detail_module_persistence` | Persistencia de configuracion de modulo inspeccionado. | `build_module_settings_payload`, `persist_inspected_module_config`. |
| `app.project_detail_module_settings_panel` | Panel de configuracion del modulo. | `ProjectDetailModuleSettingsPanel`, `build_project_detail_module_settings_panel`. |
| `app.project_detail_en_juego_state` | Estado persistido de En-Juego. | `configurable_en_juego_rows`, `en_juego_material_thickness_mm`, `store_en_juego_composition_layout`, `sync_en_juego_observations`. |
| `app.project_detail_en_juego_settings` | Normalizacion de settings/dialogos En-Juego. | `normalize_en_juego_dialog_settings`, `en_juego_effective_piece_spacing_mm`, `apply_en_juego_*_dialog_settings`. |
| `app.project_detail_en_juego_layout` | Layout puro de piezas En-Juego. | `collect_en_juego_instances`, `enforce_scene_piece_spacing`, `collect_en_juego_layout_data`. |
| `app.project_detail_en_juego_view` | Items/viewport Qt de composicion En-Juego. | `EnJuegoGraphicsView`, `EnJuegoPieceItem`, `rotate_en_juego_scene_item`. |
| `app.project_detail_en_juego_preview` | Render de preview en escena En-Juego. | `load_piece_drawing_data`, `build_piece_scene_item`. |
| `app.project_detail_en_juego_dimensions` | Controlador de cotas interactivas. | `EnJuegoDimensionAnnotator`. |
| `app.project_detail_en_juego_dialogs` | Paneles, toolbars y dialogos auxiliares. | `EnJuegoControlsPanel`, `EnJuegoViewToolbar`, `open_en_juego_*_settings_dialog`. |
| `app.project_detail_en_juego_configuration` | Dialogo principal de configuracion En-Juego. | `open_en_juego_configuration_dialog`. |
| `app.project_detail_en_juego_output` | Salida PGMX desde dialogo En-Juego. | `create_en_juego_pgmx_from_dialog`, `en_juego_creation_details`. |

## Inventario `core/`

| Modulo | Funcion En El Sistema | API Publica Principal |
| --- | --- | --- |
| `core.model` | Modelo de datos de proyectos, locales, modulos y piezas. | `Project`, `LocaleData`, `ModuleData`, `Piece`, helpers de veta/observaciones. |
| `core.parser` | Parseo CNC y escaneo de estructura de proyecto. | `parse_cnc_file`, `load_module_summary`, `scan_project`, `inspect_project_layout`, `scan_project_structure`. |
| `core.summary` | Export CSV y fachada compatible de resumen. | `export_summary`. |
| `core.production_sheet` | Export Excel y fachada historica PDF. | `export_production_sheet`, `export_production_sheet_pdf`. |
| `core.production_sheet_data` | Preparacion de filas/dimensiones para planillas. | `load_module_sheet_data`, `piece_from_sheet_row`, `derive_module_dimensions`. |
| `core.production_sheet_images` | Imagenes para Excel/PDF y reemplazo En-Juego en planillas. | `prepare_module_sheet_images`, `build_en_juego_sheet_svg`, `prepare_pdf_popup_drawing_image`. |
| `core.production_sheet_pdf` | Renderer PDF interactivo de planillas. | `export_production_sheet_pdf`. |
| `core.production_pdf` | Primitivas PDF/JS de bajo nivel. | `pdf_*` helpers. |
| `core.nesting` | Fachada compatible historica de nesting. | Reexporta `core.nesting_compat`. |
| `core.nesting_compat` | Contrato de aliases heredados. | `__all__` y reexports de nesting. |
| `core.nesting_model` | Dataclasses y constantes de corte. | `CutPiece`, `CutPlacement`, `CutBoard`, `SectionSelection`, `SectionCandidate`. |
| `core.nesting_boards` | Preparacion de tableros. | `normalize_board_definition`, `apply_board_margin`, `resolve_board_definition`. |
| `core.nesting_pieces` | Expansion y validacion de piezas para corte. | Helpers internos usados por `nesting_service`. |
| `core.nesting_strategy` | Ordenamiento, veta y seleccion de algoritmo. | `normalize_*`, `orientation_options`, `order_group_pieces`, `uses_guillotine_mode`. |
| `core.nesting_geometry` | Geometria rectangular para packers. | `rectangles_intersect`, `split_free_rectangle`, `prune_free_rectangles`, `occupied_span`. |
| `core.nesting_dispatch` | Despacho entre packers. | `pack_group_into_boards`. |
| `core.nesting_service` | Servicio productivo de diagramas. | `generate_cut_diagrams`. |
| `core.nesting_first_fit` | Compatibilidad first-fit. | `first_fit_2d`. |
| `core.nesting_free_rectangles` | Packer free-rectangles. | `placement_score`, `pack_group_into_boards_free_rectangles`. |
| `core.nesting_guillotine` | Packers guillotina. | `pack_group_into_boards_guillotine`, `pack_group_into_boards_guillotine_dimension_scan`. |
| `core.nesting_guillotine_sections` | Secciones y scoring guillotina. | `section_*`, `build_section_candidate`, `build_section_placements`. |
| `core.nesting_brkga` | BRKGA para cola guillotina preservando orden. | `pack_group_into_boards_guillotine_brkga_tail` y helpers de fitness/orden. |
| `core.nesting_pdf` | Renderer PDF de diagramas de corte. | `build_cut_diagram_pdf`. |
| `core.en_juego_transform` | Transformaciones geometricas para composicion En-Juego. | `EnJuegoTransform`, `transform_supported_spec`. |
| `core.en_juego_synthesis` | Sintesis PGMX compuesta En-Juego. | `create_en_juego_pgmx`, `EnJuegoPgmxResult`. |
| `core.pgmx_processing` | Fachada compatible hacia `pgmx.processing`. | Reexporta `pgmx.processing`. |

## Inventario `pgmx/`

| Modulo | Funcion En El Sistema | API Publica Principal |
| --- | --- | --- |
| `pgmx.processing` | Servicios PGMX para UI, nesting y planillas. | `resolve_piece_program_path`, `parse_pgmx_for_piece`, `build_piece_svg`, `get_pgmx_program_dimension_notes`, `repair_invalid_slot_pgmx_by_rotating_ccw`. |
| `pgmx.snapshot` | Snapshot normalizado de `.pgmx` existentes. | `read_pgmx_snapshot`, `snapshot_to_dict`, `write_pgmx_snapshot_json`, `main`, dataclasses `Pgmx*Snapshot`. |
| `pgmx.adapters` | Adaptacion de snapshots a specs del sintetizador. | `adapt_pgmx_snapshot`, `adapt_pgmx_path`, `adaptation_to_dict`, `write_pgmx_adaptation_json`, `main`. |
| `pgmx.synthesis` | API publica del sintetizador PGMX. | Reexports de specs/builders, `main`. |
| `pgmx.synthesis.__main__` | Entrada CLI. | `py -3 -m pgmx.synthesis`. |
| `pgmx.synthesis.cli` | CLI de sintesis. | `main`. |
| `pgmx.synthesis.core` | Fachada interna historica del sintetizador. | Reexports de `common`, `milling`, `drilling`. No debe recibir logica nueva. |
| `pgmx.synthesis.vaciado` | Estado de integracion pocket/vaciado. | `vaciado_support_status`, `adapt_pocket_milling_to_vaciado_contract`. |
| `pgmx.synthesis.common.program` | Orquestacion de programa PGMX. | `PgmxState`, `PgmxSynthesisRequest`, `build_synthesis_request`, `synthesize_request`, `synthesize_pgmx`. |
| `pgmx.synthesis.common.xml` | Helpers XML, IDs, namespaces y referencias. | `register_pgmx_namespaces` y helpers internos. |
| `pgmx.synthesis.common.output` | Finalizacion XML y escritura `.pgmx`. | Helpers internos `_write_pgmx_zip`, `_finalize_*`. |
| `pgmx.synthesis.common.geometry` | Contratos y parseo de geometria. | `GeometryPrimitiveSpec`, `GeometryProfileSpec`, builders de line/arc/circle/composite. |
| `pgmx.synthesis.common.piece` | Geometria de pieza, caras y transformaciones. | `PieceGeometry`. |
| `pgmx.synthesis.common.depth` | Profundidad de mecanizados. | `MillingDepthSpec`, `build_depth_spec`, `build_milling_depth_spec`. |
| `pgmx.synthesis.common.tools` | Catalogo y normalizacion de herramientas. | Helpers internos de tool catalog. |
| `pgmx.synthesis.common.strategy` | Estrategias Maestro por familia. | `UnidirectionalMillingStrategySpec`, `BidirectionalMillingStrategySpec`, `HelicalMillingStrategySpec`, `ContourParallelMillingStrategySpec`. |
| `pgmx.synthesis.common.hydration` | Carga de templates `.pgmx`/`Pieza.xml`. | `PgmxTemplateDocument`, `load_pgmx_template_document`. |
| `pgmx.synthesis.common.leads` | Acercamientos/alejamientos. | `ApproachSpec`, `RetractSpec`, `build_approach_spec`, `build_retract_spec`. |
| `pgmx.synthesis.milling.line` | Fresado lineal. | `LineMillingSpec`, `build_line_milling_spec`. |
| `pgmx.synthesis.milling.slot` | Ranura `SlotSide`. | `SlotMillingSpec`, `build_slot_milling_spec`. |
| `pgmx.synthesis.milling.profile` | Fresado de polilinea/perfil. | `PolylineMillingSpec`, `build_polyline_milling_spec`. |
| `pgmx.synthesis.milling.circle` | Fresado circular. | `CircleMillingSpec`, `build_circle_milling_spec`. |
| `pgmx.synthesis.milling.squaring` | Escuadrado exterior. | `SquaringMillingSpec`, `build_squaring_milling_spec`. |
| `pgmx.synthesis.milling.pocket` | Produccion `ClosedPocket`/pocket milling. | `PocketMillingSpec`, `PocketBossRouteSeedSpec`, builders. |
| `pgmx.synthesis.milling.pocket_contract` | Contrato promovido desde Vaciado V2. | `VaciadoGeometry`, `VaciadoStrategy`, `VaciadoDepth`, `plan_rectangular_no_islands`. |
| `pgmx.synthesis.milling.pocket_rectangular` | Reglas rectangulares cerradas. | `generate_rectangular_contour_parallel_path`, `generate_rectangular_contour_parallel_xyz_path`. |
| `pgmx.synthesis.milling.pocket_trace` | Motor productivo general de trazas pocket. | `generate_contour_parallel_pocket_trace`, `ContourParallelTracePlan`, `Trace*` dataclasses. |
| `pgmx.synthesis.drilling.single` | Taladro individual. | `DrillingSpec`, `build_drilling_spec`. |
| `pgmx.synthesis.drilling.pattern` | Patron rectangular de taladros. | `DrillingPatternSpec`, `build_drilling_pattern_spec`. |
| `pgmx.machining_lab.pocket_milling` | Laboratorio de evidencia pocket/vaciado. | `scan_samples`, `contour_parallel`, `island_analysis`, `trace_primitives`, `trace_engine`. |
| `pgmx.machining_lab.machine_operations` | Laboratorio de operaciones de maquina y flujo multifase PGMX. | `scan_samples`, memoria de `Xn`/`Xmsg`/`MainWorkplan`. |

## Inventario `iso_state_synthesis/`

| Modulo | Funcion En El Sistema | API Publica Principal |
| --- | --- | --- |
| `iso_state_synthesis.model` | Modelo de estados, etapas, cambios y evaluaciones. | `IsoStatePlan`, `IsoStateEvaluation`, `StateVector`, `StateStage`, `StageDifferential`. |
| `iso_state_synthesis.pgmx_source` | Construccion de planes desde snapshots PGMX. | `build_state_plan_from_pgmx`, `build_state_plan_from_snapshot`. |
| `iso_state_synthesis.differential` | Calculo de cambios entre etapas. | `evaluate_pgmx_state_plan`, `evaluate_state_plan`. |
| `iso_state_synthesis.catalog` | Catalogo de bloques/transiciones ISO observadas. | `head_for_family`, `block_id_for_stage_key`, `select_transition_id`. |
| `iso_state_synthesis.comparison` | Comparacion normalizada entre candidato explicado e ISO Maestro. | `compare_candidate_to_iso`, `IsoCandidateComparison`, `IsoLineDifference`. |
| `iso_state_synthesis.work_groups` | Agrupamiento `prepare/trace/reset` y planificacion de transiciones entre trabajos. | Helpers internos `_work_stage_groups`, `_plan_work_groups`. |
| `iso_state_synthesis.program_lines` | Builders puros de lineas ISO para cabecera, preambulo, marcos y cierres de programa. | Helpers internos `_program_*`, `_piece_frame_*`, `_common_program_close_*`. |
| `iso_state_synthesis.boring_head_lines` | Builders puros de lineas ISO para preparaciones, activacion/mask, pausa, seleccion lateral y resets del cabezal de perforacion/ranurado. | Helpers internos `_top_drill_*`, `_side_drill_*`, `_boring_head_*`, `_side_plane_selection_lines`, `_slot_milling_*`. |
| `iso_state_synthesis.boring_trace_lines` | Builders puros de trazas ISO para Top Drill y Side Drill. | Helpers internos `_top_drill_trace_lines`, `_side_drill_trace_lines`. |
| `iso_state_synthesis.router_milling_lines` | Builders puros de preparacion, traza y reset ISO para fresados router lineales. | Helpers internos `_line_milling_*`, geometria de leads y compensacion. |
| `iso_state_synthesis.profile_milling_lines` | Builders puros de trazas ISO para fresado de perfil E001 y estrategia PH5. | Helper interno `_profile_milling_trace_lines`. |
| `iso_state_synthesis.slot_milling_lines` | Builders puros de traza ISO para SlotSide. | Helper interno `_slot_milling_trace_lines`. |
| `iso_state_synthesis.transition_lines` | Builders puros de lineas ISO para transiciones entre familias. | Helpers internos `_router_*`, `_boring_to_router_*`, `_top_to_slot_*`, `_side_to_slot_*`, `_slot_to_slot_*`. |
| `iso_state_synthesis.errors` | Excepciones compartidas del emisor candidato. | `IsoCandidateEmissionError`. |
| `iso_state_synthesis.emitter` | Orquestacion de emision candidata ISO explicable. | `emit_candidate_for_pgmx`, `emit_candidate_from_evaluation`. |
| `iso_state_synthesis.cli` | CLI experimental. | `main`. |
| `iso_state_synthesis.__main__` | Entrada `py -3 -m iso_state_synthesis`. | Delegacion a CLI. |
| `iso_state_synthesis.machine_config/` | Configuracion observada de maquina. | Documentacion/datos, no modulo Python. |

## Inventario `cnc_traceability/`

| Modulo | Funcion En El Sistema | API Publica Principal |
| --- | --- | --- |
| `cnc_traceability.viewer_xp` | App Tkinter standalone compatible XP para piso CNC. | `CncProjectViewerApp`, `ProjectWindow`, `PiecePreviewWindow`, `main` y helpers de lectura/progreso/USBMIX. |

## Inventario `tools/studies/`

| Ruta | Funcion En El Sistema | API Publica Principal |
| --- | --- | --- |
| `tools/studies/cut_diagrams/ordering_lab.py` | Laboratorio archivado de algoritmos/ordenamientos de corte. | `run_experiments`, `order_pieces`, `pack_*`, `main`. |
| `tools/studies/iso/*.py` | Laboratorio auditado de fixtures, ordenamiento y auditorias fechadas del corpus ISO. | Patron comun: `build_fixtures`, `generate`, `parse_args`, `main`; auditorias vivas: `block_transition_corpus_analysis_2026_05_13.py`, `txh001_transition_audit_2026_05_13.py`. |

## Cobertura De Tests

| Area | Suites |
| --- | --- |
| App/options/project detail | `tests/test_options_helpers.py`, `tests/test_project_detail_*.py`, `tests/test_project_store.py`. |
| Core/model/parser | `tests/test_core_model.py`, `tests/test_core_parser.py`. |
| Core/fachadas | `tests/test_core_facades.py`, `tests/test_nesting_compat.py`, `tests/test_summary_exports.py`. |
| Core En-Juego | `tests/test_en_juego_transform.py`, `tests/test_en_juego_synthesis.py`, `tests/test_project_detail_en_juego_*.py`. |
| En-Juego UI/layout/output | `tests/test_project_detail_en_juego_*.py`. |
| Planillas/PDF | `tests/test_summary_exports.py`, `tests/test_production_sheet_data.py`, `tests/test_production_pdf.py`, `tests/test_production_sheet_images.py`. |
| Nesting | `tests/test_nesting_*.py`. |
| PGMX | `tests/test_pgmx_processing.py`, `tests/test_pgmx_synthesis_package.py`, `tests/test_pgmx_public_facades.py`, `tests/test_pgmx_vaciado_v2.py`, `tests/test_pgmx_vaciado.py`, `tests/test_project_detail_pgmx.py`. |
| ISO experimental | `tests/test_iso_state_synthesis.py`. |
| Trazabilidad CNC | `tests/test_cnc_traceability.py`. |
| Gaps conocidos | `cnc_traceability/` no tiene cobertura automatizada de UI/XP real; `tools/studies/` no tiene suite dedicada completa; `iso_state_synthesis/` tiene cobertura inicial pero no fixtures PGMX/ISO reales. |

Comando de validacion general:

```powershell
py -3 -m unittest discover -s tests -p "test*.py"
```

## Puntos A Auditar En La Documentacion

1. Hecho: confirmar que los documentos rectores describen `pgmx.*` como API actual y
   no las fachadas retiradas bajo `tools/`.
2. Hecho: separar claramente `core.nesting` y `core.pgmx_processing` como fachadas
   compatibles todavia existentes.
3. Hecho: verificar que `iso_state_synthesis.emitter` figure como experimental e
   incompleto cuando corresponda.
4. Hecho: revisar `docs/repo_study_guide.md` contra el mapa real de `app/` y `core/`.
5. Hecho: revisar `docs/synthesize_pgmx_help.md`, `docs/pgmx_snapshot_help.md` y
   `docs/pgmx_adapters_help.md` contra las CLIs finales `py -3 -m pgmx.*`.
6. Hecho: abrir auditoria dedicada de `app/` en
   `docs/app_subsystem_audit.md`.
7. Vigente: evitar editar memorias historicas salvo para agregar nota de estado actual en
   trackers vivos.

## Hallazgos Y Acciones Aplicadas

- No quedan imports Python hacia las fachadas PGMX retiradas bajo `tools/` o
  `pgmx.vaciado*`.
- Las menciones restantes a esas fachadas en documentos rectores aparecen como
  historial o como lista de rutas retiradas; deben conservarse solo si ayudan a
  explicar la migracion.
- `docs/repo_study_guide.md` fue revisado contra este inventario y quedo
  alineado con `app/project_detail_*`, `pgmx.*`, ISO experimental y
  `tools/studies/`.
- `docs/architecture_reorganization.md` y
  `docs/pgmx_synthesis_modularization_plan.md` quedaron separados entre estado
  actual, historial de etapas, rutas retiradas y pendientes de laboratorio.
- `pgmx/machining_lab/README.md` queda agregado como frontera general; el punto
  de entrada especifico de pocket milling sigue siendo
  `pgmx/machining_lab/pocket_milling/README.md`.
- `docs/app_subsystem_audit.md` queda agregado como corte de auditoria profunda
  del subsistema desktop; el bloque `app/` queda cerrado para esta etapa con
  deuda residual documentada.
- `docs/core_subsystem_audit.md` queda agregado como corte de auditoria del
  subsistema `core/`; el primer subcorte estabiliza modelo/parser y el contrato
  de CSV con encabezados en `core.parser.load_module_summary`.
- El subcorte planillas/PDF de `core/` estabiliza normalizacion numerica con
  coma decimal en `core.production_sheet_data` y agrega cobertura focal.
- El subcorte diagramas de corte de `core/` mantiene `core.nesting` como
  fachada compatible declarada y estabiliza coma decimal en helpers numericos de
  `core.nesting_boards` y `core.nesting_pieces`.
- El subcorte En-Juego productivo de `core/` agrega cobertura para
  transformaciones, validadores puros y contrato de resultado; la generacion
  integral sigue dependiendo de fixtures PGMX reales.
- El subcorte fachadas compatibles de `core/` agrega cobertura explicita para
  `core.pgmx_processing`, `core.summary` y `core.nesting`.
- El bloque `core/` queda cerrado para esta etapa.
- El subcorte inicial de `pgmx/` agrega `docs/pgmx_subsystem_audit.md`,
  documenta fachadas/snapshot/adaptacion y corrige la proyeccion lateral de
  SVG en `pgmx.processing.build_piece_svg`.
- El subcorte de sintetizador PGMX retira el fallback operativo a `tools/` para
  datos empaquetados; el runtime vigente debe usar `pgmx/data` o
  `_internal/pgmx/data`.
- El subcorte inicial de `iso_state_synthesis/` agrega
  `docs/iso_state_synthesis_subsystem_audit.md` y cobertura pura para modelo,
  diferenciales, catalogo y comparacion de candidatos.
- El subcorte de `iso_state_synthesis.emitter` extrae los builders internos de
  `line_milling_trace`: center con leads, estrategias, compensacion lateral,
  sin-leads generico y fallback final quedan cubiertos en tests puros.
- `docs/cnc_traceability_subsystem_audit.md` agrega el corte del visor CNC
  standalone y `tests/test_cnc_traceability.py` fija helpers puros de indice,
  escaneo, resolucion de pieza y progreso.
- `docs/tools_studies_subsystem_audit.md` agrega el corte de laboratorios
  reproducibles; `tools/studies/` queda clasificado como evidencia ejecutable,
  no como API productiva.
