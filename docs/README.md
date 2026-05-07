# Documentacion ProdAction

Este directorio esta pensado como punto de entrada para estudiar el repo sin
tener que leer todas las memorias historicas de una vez.

## Orden recomendado

1. `docs/repo_study_guide.md`
   - Mapa rapido de arquitectura, flujos y archivos importantes.
2. `docs/synthesize_pgmx_help.md`
   - Fuente de verdad para la API publica de sintesis `.pgmx`.
3. `docs/pgmx_snapshot_help.md` y `docs/pgmx_adapters_help.md`
   - Lectura/adaptacion de `.pgmx` existentes hacia specs publicos.
4. `docs/cut_diagrams_temporary_memory.md`
   - Estado del motor de diagramas de corte y algoritmos de guillotina.
5. `cnc_traceability/README.md`
   - Entrada del subsistema de trazabilidad CNC compatible con Windows XP.
6. `iso_state_synthesis/README.md`
   - Entrada del subsistema experimental por estado para futura traduccion
     `.pgmx -> .iso`.
7. `docs/iso_cnc_contract.md`
   - Contrato CNC/ISO observado: configuracion Maestro, toolset, variables y
     huecos pendientes para un sintetizador ISO.
8. `docs/iso_minimal_fixtures_plan.md`
   - Plan de reanudacion para generar `.pgmx` minimos comparables en la compu
     de fabrica y postprocesarlos con Maestro.
9. `docs/iso_synthesis_temporary_memory.md`
   - Ingenieria inversa del flujo PGMX -> Maestro/postprocesador -> ISO.

## Mapa por tema

| Tema | Fuente principal | Codigo principal |
| --- | --- | --- |
| App desktop | `docs/repo_study_guide.md` | `app/ui.py`, `main.py` |
| Modelo de datos | `docs/repo_study_guide.md` | `core/model.py` |
| Escaneo de proyectos | `docs/repo_study_guide.md` | `core/parser.py` |
| Planillas y PDF | `docs/repo_study_guide.md` | `core/summary.py` |
| Dibujos de piezas | `docs/repo_study_guide.md` | `core/pgmx_processing.py` |
| Sintesis PGMX | `docs/synthesize_pgmx_help.md` | `tools/synthesize_pgmx.py` |
| Snapshot/adaptacion PGMX | `docs/pgmx_snapshot_help.md`, `docs/pgmx_adapters_help.md` | `tools/pgmx_snapshot.py`, `tools/pgmx_adapters.py` |
| Reparacion SlotSide | `docs/repo_study_guide.md`, `docs/pgmx_temporary_memory.md` | `core/pgmx_processing.py`, `app/ui.py` |
| En-Juego | `docs/en_juego_synthesis_temporary_memory.md` | `core/en_juego_synthesis.py` |
| Diagramas de corte | `docs/cut_diagrams_temporary_memory.md` | `core/nesting.py` |
| Laboratorio de corte | `docs/cut_diagrams_temporary_memory.md` | `tools/studies/cut_diagrams/ordering_lab.py` |
| Trazabilidad CNC | `cnc_traceability/README.md`, `cnc_traceability/docs/contract.md`, `cnc_traceability/memory/current-state.md` | `cnc_traceability/viewer_xp.py` |
| Generacion ISO experimental | `iso_state_synthesis/README.md`, `iso_state_synthesis/memory/current-state.md`, `docs/iso_cnc_contract.md` | `iso_state_synthesis/` |
| Contrato CNC/ISO | `docs/iso_cnc_contract.md`, `docs/iso_minimal_fixtures_plan.md`, `docs/iso_synthesis_temporary_memory.md` | `tools/studies/iso/minimal_fixtures_2026_05_03.py` |

## Reglas de mantenimiento

- El README del repo debe ser resumen y puerta de entrada, no memoria tecnica
  extensa.
- Las guias `*_help.md` son fuente de verdad para APIs publicas.
- Las memorias `*_temporary_memory.md` pueden ser largas e historicas; cuando
  una decision se estabiliza, conviene copiar el resumen a una guia estable.
- Si cambia `tools.synthesize_pgmx.SYNTHESIZER_VERSION`, actualizar
  `README.md`, `docs/synthesize_pgmx_help.md` y cualquier memoria externa de
  trabajo que se este usando.
- Los scripts exploratorios o reproducibles de estudio deben vivir bajo
  `tools/studies/`; el nivel principal de `tools/` queda para herramientas
  publicas o de uso operativo.
- Si se agrega un flujo nuevo, actualizar primero esta pagina y luego la guia
  especifica del tema.
