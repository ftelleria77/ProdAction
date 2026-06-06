# Documentacion ProdAction

Este directorio esta pensado como punto de entrada para estudiar el repo sin
tener que leer todas las memorias historicas de una vez.

## Orden recomendado

1. `docs/architecture_reorganization.md`
   - Rumbo actual para ordenar codigo, fronteras y migracion por etapas.
2. `docs/repository_audit_inventory.md`
   - Inventario de auditoria por subsistema, modulos, procesos, tests y docs.
3. `docs/repo_study_guide.md`
   - Mapa rapido de arquitectura, flujos y archivos importantes.
4. `docs/app_subsystem_audit.md`
   - Auditoria del subsistema desktop PySide6: flujos, modulos, correcciones y
     deuda residual aceptada.
5. `docs/synthesize_pgmx_help.md`
   - Fuente de verdad para la API publica de sintesis `.pgmx`.
6. `docs/pgmx_synthesis_modularization_plan.md`
   - Plan para modularizar el sintetizador por familias de mecanizado e
     integrar Vaciado como `ClosedPocket`/pocket milling.
7. `docs/pgmx_synthesis_modularization_temporary_memory.md`
   - Memoria temporal para discutir el alcance modulo por modulo antes de
     escribir codigo.
8. `docs/pgmx_snapshot_help.md` y `docs/pgmx_adapters_help.md`
   - Lectura/adaptacion de `.pgmx` existentes hacia specs publicos.
9. `pgmx/machining_lab/README.md` y
   `pgmx/machining_lab/pocket_milling/README.md`
   - Laboratorio general de mecanizados PGMX y laboratorio de
     `ClosedPocket`/pocket milling.
10. `docs/cut_diagrams_temporary_memory.md`
   - Estado del motor de diagramas de corte y algoritmos de guillotina.
11. `docs/laboratory_frontiers.md`
   - Fronteras entre herramientas publicas, fachadas compatibles y laboratorios.
12. `cnc_traceability/README.md`
   - Entrada del subsistema de trazabilidad CNC compatible con Windows XP.
13. `iso_state_synthesis/README.md`
   - Entrada del subsistema experimental por estado para futura traduccion
     `.pgmx -> .iso`.
14. `docs/iso_cnc_contract.md`
   - Contrato CNC/ISO observado: configuracion Maestro, toolset, variables y
     huecos pendientes para un sintetizador ISO.
15. `docs/iso_minimal_fixtures_plan.md`
   - Plan de reanudacion para generar `.pgmx` minimos comparables en la compu
     de fabrica y postprocesarlos con Maestro.
16. `docs/iso_synthesis_temporary_memory.md`
   - Ingenieria inversa del flujo PGMX -> Maestro/postprocesador -> ISO.

## Mapa por tema

| Tema | Fuente principal | Codigo principal |
| --- | --- | --- |
| Inventario de auditoria | `docs/repository_audit_inventory.md` | `app/`, `core/`, `pgmx/`, `iso_state_synthesis/`, `cnc_traceability/`, `tools/studies/` |
| Arquitectura del repo | `docs/architecture_reorganization.md` | `app/main_window.py`, `app/project_dialogs.py`, `app/project_detail_core.py`, `app/project_detail_dialog_lifecycle.py`, `app/project_detail_processing.py`, `app/project_detail_modules.py`, `app/project_detail_inspection.py`, `app/project_detail_color_changes.py`, `app/project_detail_module_persistence.py`, `app/project_detail_module_settings_panel.py`, `app/project_detail_colors.py`, `app/project_detail_piece_editor.py`, `app/project_detail_piece_editor_dialog.py`, `app/project_detail_piece_actions.py`, `app/project_detail_piece_table.py`, `app/project_detail_piece_table_rows.py`, `app/project_detail_programs.py`, `app/project_detail_pgmx.py`, `app/project_detail_en_juego_state.py`, `app/project_detail_en_juego_layout.py`, `app/project_detail_en_juego_view.py`, `app/project_detail_en_juego_preview.py`, `app/project_detail_en_juego_dimensions.py`, `app/project_detail_en_juego_configuration.py`, `app/project_detail_en_juego_settings.py`, `app/project_detail_en_juego_dialogs.py`, `app/project_detail_en_juego_output.py`, `app/project_detail_piece_rows.py`, `app/project_detail_drawings.py`, `app/project_detail_selectors.py`, `app/project_detail_output.py`, `app/runtime.py`, `app/project_registry.py`, `app/project_store.py`, `app/settings.py`, `app/qt_helpers.py`, `app/options_dialogs.py`, `app/options_helpers.py`, `app/ui_constants.py`, `app/ui.py` |
| App desktop | `docs/repo_study_guide.md`, `docs/app_subsystem_audit.md` | `app/ui.py`, `app/main_window.py`, `app/project_detail_*.py`, `main.py` |
| Modelo de datos | `docs/repo_study_guide.md` | `core/model.py` |
| Escaneo de proyectos | `docs/repo_study_guide.md` | `core/parser.py` |
| Planillas y PDF | `docs/repo_study_guide.md` | `core/summary.py`, `core/production_sheet.py`, `core/production_sheet_pdf.py` |
| Dibujos de piezas | `docs/repo_study_guide.md` | `pgmx/processing.py`, `core/pgmx_processing.py` |
| Sintesis PGMX | `docs/synthesize_pgmx_help.md`, `docs/pgmx_synthesis_modularization_plan.md`, `docs/pgmx_synthesis_modularization_temporary_memory.md` | `pgmx/synthesis/` |
| Snapshot/adaptacion PGMX | `docs/pgmx_snapshot_help.md`, `docs/pgmx_adapters_help.md` | `pgmx/snapshot.py`, `pgmx/adapters.py` |
| Pocket milling PGMX | `pgmx/machining_lab/pocket_milling/README.md`, `pgmx/machining_lab/pocket_milling/memory/current-state.md`, `docs/laboratory_frontiers.md` | `pgmx/synthesis/milling/pocket.py`, `pgmx/synthesis/milling/pocket_contract.py`, `pgmx/machining_lab/pocket_milling/` |
| Reparacion SlotSide | `docs/repo_study_guide.md`, `docs/pgmx_temporary_memory.md` | `pgmx/processing.py`, `core/pgmx_processing.py`, `app/project_detail_pgmx.py`, `app/project_detail_programs.py`, `app/project_detail_selected_piece_actions.py` |
| En-Juego | `docs/en_juego_synthesis_temporary_memory.md` | `core/en_juego_synthesis.py`, `core/en_juego_transform.py` |
| Diagramas de corte | `docs/cut_diagrams_temporary_memory.md` | `core/nesting_service.py`, `core/nesting_compat.py` |
| Laboratorios y fachadas | `docs/laboratory_frontiers.md`, `docs/pgmx_synthesis_modularization_plan.md` | `tools/`, `pgmx/machining_lab/`, `tools/studies/`, `iso_state_synthesis/` |
| Laboratorio de corte | `docs/cut_diagrams_temporary_memory.md`, `docs/laboratory_frontiers.md` | `tools/studies/cut_diagrams/ordering_lab.py` |
| Trazabilidad CNC | `cnc_traceability/README.md`, `cnc_traceability/docs/contract.md`, `cnc_traceability/memory/current-state.md` | `cnc_traceability/viewer_xp.py` |
| Generacion ISO experimental | `iso_state_synthesis/README.md`, `iso_state_synthesis/memory/current-state.md`, `docs/iso_cnc_contract.md` | `iso_state_synthesis/` |
| Contrato CNC/ISO | `docs/iso_cnc_contract.md`, `docs/iso_minimal_fixtures_plan.md`, `docs/iso_synthesis_temporary_memory.md` | `tools/studies/iso/README.md`, `tools/studies/iso/` |

## Reglas de mantenimiento

- El README del repo debe ser resumen y puerta de entrada, no memoria tecnica
  extensa.
- Las guias `*_help.md` son fuente de verdad para APIs publicas.
- Las memorias `*_temporary_memory.md` pueden ser largas e historicas; cuando
  una decision se estabiliza, conviene copiar el resumen a una guia estable.
- Si cambia `pgmx.synthesis.SYNTHESIZER_VERSION`, actualizar
  `README.md`, `docs/synthesize_pgmx_help.md` y cualquier memoria externa de
  trabajo que se este usando.
- Los scripts exploratorios o reproducibles de estudio deben vivir bajo
  `tools/studies/`; el nivel principal de `tools/` queda para herramientas
  publicas o de uso operativo.
- Si se agrega un flujo nuevo, actualizar primero esta pagina y luego la guia
  especifica del tema.
