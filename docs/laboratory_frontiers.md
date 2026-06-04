# Fronteras De Laboratorio

Estado: 2026-06-03

Este documento separa herramientas publicas, fachadas compatibles y frentes de
investigacion. La regla operativa es que el codigo productivo importe `pgmx/`,
`core/` o `app/`; las rutas bajo `tools/` solo deben ser CLIs publicas
historicas, fachadas de compatibilidad o laboratorios reproducibles.

## Herramientas Publicas PGMX

| Ruta principal | Fachada historica | Estado |
| --- | --- | --- |
| `pgmx.synthesis` | `tools.synthesize_pgmx`, `tools.pgmx_synthesis` | API/CLI publica vigente; las fachadas deben seguir importando y ejecutando `main()`. |
| `pgmx.snapshot` | `tools.pgmx_snapshot` | API/CLI publica vigente para inspeccion normalizada de `.pgmx`. |
| `pgmx.adapters` | `tools.pgmx_adapters` | API/CLI publica vigente para adaptar snapshots hacia specs de sintesis. |

Las fachadas anteriores se conservan por compatibilidad, pero no deben crecer
con logica nueva. La implementacion productiva vive en `pgmx/`.

## Laboratorio De Mecanizados PGMX

El laboratorio actual de `Vaciado` pasa a ser el piloto para un laboratorio
general de mecanizados del sintetizador, pero el nombre final de la familia es
`pocket_milling` / `ClosedPocket`. El plan de migracion esta en
`docs/pgmx_synthesis_modularization_plan.md`.

Destino propuesto:

| Ruta | Rol | Frontera |
| --- | --- | --- |
| `pgmx.machining_lab` | Laboratorio general de mecanizados | Destino futuro para evidencia, memoria y analizadores por familia. No debe ser dependencia productiva directa. |
| `pgmx.machining_lab.pocket_milling` | Laboratorio de `ClosedPocket` dentro del laboratorio general | Destino futuro del contenido actual de `pgmx.vaciado_lab`. |
| `pgmx.vaciado_lab` | Laboratorio historico durante la transicion | Debe desaparecer cuando memoria, tests y comandos migren a `pocket_milling`. |

## Pocket Milling PGMX

| Ruta | Rol | Frontera |
| --- | --- | --- |
| `pgmx.synthesis.milling.pocket` | Produccion `ClosedPocket`/pocket milling | Punto estable para que la sintesis PGMX escriba vaciados como parte de la familia pocket/cajeado. |
| `pgmx.machining_lab.pocket_milling` | Laboratorio y oraculo futuro | Puede usar trazas Maestro y memoria externa; no es dependencia productiva directa. |
| `pgmx.vaciado` | Contrato V2 historico | Debe integrarse en `pgmx.synthesis.milling.pocket` y desaparecer como paquete final. |
| `pgmx.vaciado_lab` | Laboratorio historico | Debe migrar a `pgmx.machining_lab.pocket_milling` y desaparecer como paquete final. |
| `tools.pgmx_vaciado*` | Fachadas historicas | Deben mantenerse solo durante la transicion de imports/CLIs hacia pocket milling. |

El tracker vivo historico del laboratorio sigue siendo
`pgmx/vaciado_lab/memory/current-state.md` hasta migrarlo a
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

## Candidatos De Limpieza Futura

- Migrar `pgmx.vaciado_lab` hacia `pgmx.machining_lab.pocket_milling` y luego
  retirar el paquete historico.
- Integrar `pgmx.vaciado` en `pgmx.synthesis.milling.pocket` y retirar el
  contrato V2 separado.
- Reducir referencias historicas `tools.pgmx_vaciado.*` cuando el frente migre
  al laboratorio general de pocket milling.
- Mantener `tools/synthesize_pgmx.py`, `tools/pgmx_snapshot.py` y
  `tools/pgmx_adapters.py` como fachadas minimas; cualquier funcion nueva debe
  nacer en `pgmx/`.
- Revisar periodicamente que `tools/studies/` no acumule scripts sin README,
  fecha, tema o criterio de promocion a API.
