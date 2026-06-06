# Fronteras De Laboratorio

Estado: 2026-06-05

Este documento separa herramientas publicas, fachadas compatibles y frentes de
investigacion. La regla operativa es que el codigo productivo importe `pgmx/`,
`core/` o `app/`; las rutas bajo `tools/` quedan para estudios reproducibles,
no para APIs productivas.

## Herramientas Publicas PGMX

| Ruta principal | CLI publica | Estado |
| --- | --- | --- |
| `pgmx.synthesis` | `py -3 -m pgmx.synthesis` | API/CLI publica vigente. |
| `pgmx.snapshot` | `py -3 -m pgmx.snapshot` | API/CLI publica vigente para inspeccion normalizada de `.pgmx`. |
| `pgmx.adapters` | `py -3 -m pgmx.adapters` | API/CLI publica vigente para adaptar snapshots hacia specs de sintesis. |

La implementacion productiva vive en `pgmx/`. Las fachadas PGMX bajo `tools/`
fueron retiradas.

## Fachadas Compatibles Vigentes

| Ruta | Destino | Criterio |
| --- | --- | --- |
| `core.nesting` | `core.nesting_compat` | Conserva aliases historicos de diagramas de corte para UI, tests y laboratorios. |
| `core.pgmx_processing` | `pgmx.processing` | Conserva imports historicos mientras la app y docs terminan de migrar. |
| `core.summary` | `core.summary` + reexports de planillas | Mantiene el CSV como API propia y compatibilidad para exportadores historicos. |

## Laboratorio De Mecanizados PGMX

El laboratorio historico de `Vaciado` quedo integrado como piloto del
laboratorio general de mecanizados del sintetizador. El nombre final de la
familia es `pocket_milling` / `ClosedPocket`. El plan de migracion esta en
`docs/pgmx_synthesis_modularization_plan.md`.

Mapa vigente:

| Ruta | Rol | Frontera |
| --- | --- | --- |
| `pgmx.machining_lab` | Laboratorio general de mecanizados | Paquete vigente para evidencia, memoria y analizadores por familia. No debe ser dependencia productiva directa. |
| `pgmx.machining_lab.pocket_milling` | Laboratorio de `ClosedPocket` dentro del laboratorio general | Destino vigente del laboratorio historico de Vaciado. |

## Pocket Milling PGMX

| Ruta | Rol | Frontera |
| --- | --- | --- |
| `pgmx.synthesis.milling.pocket` | Produccion `ClosedPocket`/pocket milling | Punto estable para que la sintesis PGMX escriba vaciados como parte de la familia pocket/cajeado. |
| `pgmx.synthesis.milling.pocket_contract` | Contrato promovido de pocket milling | Fuente real de las dataclasses y helpers antes separados como V2 de Vaciado. |
| `pgmx.machining_lab.pocket_milling` | Laboratorio y oraculo | Puede usar trazas Maestro y memoria externa; no es dependencia productiva directa. |

El tracker vivo del laboratorio es
`pgmx/machining_lab/pocket_milling/memory/current-state.md`. Antes de responder
que falta o de extender ese frente, leer ese archivo y
`tests/test_pgmx_vaciado.py`.
Las suites `tests.test_pgmx_vaciado_v2` y `tests.test_pgmx_vaciado` corren por
defecto; los casos dependientes del corpus externo de Maestro se saltan solo si
ese corpus no esta disponible.

## Estudios Reproducibles

| Ruta | Estado | Criterio |
| --- | --- | --- |
| `tools/studies/cut_diagrams/ordering_lab.py` | Laboratorio vigente | Banco de pruebas de ordenamientos/packers; depende de `core.nesting_compat` y de los servicios publicos de `app` para cargar proyectos/settings reales. |
| `tools/studies/iso/*.py` | Estudios historicos reproducibles | Fixtures y auditorias ISO fechadas, catalogadas en `tools/studies/iso/README.md`; no son APIs productivas. |
| `iso_state_synthesis/` | Subsistema experimental pausado | Paquete separado para futura traduccion `.pgmx -> .iso`; `iso_state_synthesis.emitter` aun no esta terminado y no debe dirigir arquitectura productiva salvo reactivacion explicita. |

Todo estudio nuevo debe entrar bajo `tools/studies/<tema>/` con nombre fechado o
descriptivo. Si se estabiliza como API o flujo operativo, debe migrar a `pgmx/`,
`core/` o una CLI publica documentada.

## Fachadas Retiradas

- `pgmx.vaciado`.
- `pgmx.vaciado_lab`.
- `tools.pgmx_synthesis`.
- `tools.pgmx_vaciado`.
- `tools.pgmx_vaciado_v2`.
- `tools.synthesize_pgmx`.
- `tools.pgmx_snapshot`.
- `tools.pgmx_adapters`.

## Candidatos De Limpieza Futura

- Revisar periodicamente que `tools/studies/` no acumule scripts sin README,
  fecha, tema o criterio de promocion a API.
