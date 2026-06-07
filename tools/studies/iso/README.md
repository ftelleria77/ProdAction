# Estudios ISO

Esta carpeta contiene estudios reproducibles para investigar la relacion entre
programas Maestro editables (`.pgmx`) y la salida ISO postprocesada.

No es API productiva. Los scripts generan fixtures PGMX, comparan corpus
PGMX/ISO o auditan candidatos del sintetizador ISO. Si una regla se estabiliza,
debe migrar a `pgmx/`, `iso_state_synthesis/` o a una herramienta publica
documentada.

## Uso General

- Ejecutar desde la raiz del repo con `py -3 -m tools.studies.iso.<modulo>`.
- Preferir `--help` antes de correr un lote, porque varios scripts escriben
  fixtures en carpetas externas de trabajo.
- Mantener los nombres fechados: cada estudio debe conservar fecha, tema y
  objetivo.
- No agregar scripts nuevos en `tools/` raiz para este frente; usar esta
  carpeta o un paquete experimental documentado.

## Catalogo

| Script | Tipo | Proposito |
| --- | --- | --- |
| `minimal_fixtures_2026_05_03.py` | Fixtures PGMX | Tanda minima para aislar variables Maestro/ISO. |
| `side_g53_z_fixtures_2026_05_03.py` | Fixtures PGMX | Taladros laterales para estudiar estacionamiento intermedio `G53 Z`. |
| `router_tool_mirror_fixtures_2026_05_07.py` | Fixtures PGMX | Espejado de herramientas router para comparar salida ISO. |
| `router_compensation_tool_mirror_fixtures_2026_05_07.py` | Fixtures PGMX | Espejado con compensacion router para comparar trayectoria y herramienta. |
| `tbh001_same_tool_fixtures_2026_05_10.py` | Fixtures PGMX | Continuidad top-drill -> top-drill sin cambio de herramienta vertical. |
| `tbh002_top_to_side_fixtures_2026_05_10.py` | Fixtures PGMX | Transiciones top-drill -> side-drill. |
| `tbh003_side_to_side_fixtures_2026_05_10.py` | Fixtures PGMX | Transiciones side-drill -> side-drill entre caras laterales. |
| `tbh004_side_to_top_fixtures_2026_05_11.py` | Fixtures PGMX | Transiciones side-drill -> top-drill. |
| `tbh007_008_side_slot_fixtures_2026_05_11.py` | Fixtures PGMX | Transiciones internas de cabezal de perforado con ranuras laterales. |
| `txh001_002_router_boring_fixtures_2026_05_11.py` | Fixtures PGMX | Cambios router -> boring head y boring head -> router. |
| `txh002_e001_variants_fixtures_2026_05_11.py` | Fixtures PGMX | Variantes E001 para reingreso boring head -> router. |
| `txh_top_open_profile_direct_fixtures_2026_05_11.py` | Fixtures PGMX | Top-drill -> perfil abierto router sin trabajo router previo. |
| `txh_open_profile_reentry_fixtures_2026_05_11.py` | Fixtures PGMX | Top-drill -> segundo perfil abierto router con reingreso tipo Cocina. |
| `txh_open_profile_center_reentry_fixtures_2026_05_11.py` | Fixtures PGMX | Reingreso de perfil abierto con compensacion `Center`. |
| `txh_profile_top_chain_fixtures_2026_05_11.py` | Fixtures PGMX | Perfil/linea -> cadena top -> linea para aislar familia router. |
| `txh_profile_arc_top_chain_fixtures_2026_05_11.py` | Fixtures PGMX | Variante con arcos de entrada/salida habilitados. |
| `txh_roundtrip_router_top_fixtures_2026_05_11.py` | Fixtures PGMX | Router -> top drill -> router para estudiar reingresos. |
| `top_drill_ordering_fixtures_2026_05_13.py` | Fixtures y analisis | Genera y analiza orden de taladros superiores con herramientas mixtas. |
| `top_drill_corpus_order_analysis_2026_05_13.py` | Analisis | Compara orden PGMX, candidato actual e ISO Maestro en corpus pareado. |
| `txh001_transition_audit_2026_05_13.py` | Auditoria | Audita candidatos que ejercitan la transicion T-XH-001. |
| `block_transition_corpus_analysis_2026_05_13.py` | Auditoria | Clasifica residuales ISO por bloques y secuencias de transicion. |

## Estado De Auditoria 2026-06-07

| Grupo | Scripts | Estado |
| --- | --- | --- |
| Fixtures fechados | `minimal_*`, `side_g53_z_*`, `router_*`, `tbh*`, `txh*_fixtures*` | Laboratorio historico reproducible. Mantener fechados; no son API publica. |
| Ordenamiento top drill | `top_drill_ordering_fixtures_2026_05_13.py`, `top_drill_corpus_order_analysis_2026_05_13.py` | Evidencia viva para reglas de orden en `pgmx_source.py`; ejecutar solo con corpus Maestro/ISO pareado. |
| Auditoria de transiciones | `txh001_transition_audit_2026_05_13.py`, `block_transition_corpus_analysis_2026_05_13.py` | Herramientas vivas para comparar corpus contra el sintetizador actual; importan `iso_state_synthesis.comparison` y `iso_state_synthesis.work_groups`. |

Los estudios que comparan contra el sintetizador vigente deben importar
comparacion desde `iso_state_synthesis.comparison` y agrupamiento desde
`iso_state_synthesis.work_groups`. `iso_state_synthesis.emitter` queda reservado
para emitir candidatos explicados.

## Criterio De Promocion

Un estudio puede promoverse fuera de esta carpeta solo si:

- la regla observada esta validada contra corpus Maestro/ISO;
- el comportamiento ya no depende de inspeccion manual del lote;
- existe una API o contrato claro para `pgmx/` o `iso_state_synthesis/`;
- hay cobertura de tests o un comando reproducible que detecte regresiones.
