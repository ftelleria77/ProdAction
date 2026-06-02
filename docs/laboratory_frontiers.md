# Fronteras De Laboratorio

Estado: 2026-06-02

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

## Vaciado PGMX

| Ruta | Rol | Frontera |
| --- | --- | --- |
| `pgmx.vaciado` | Contrato V2 experimental | Puede ser integrado por `pgmx.synthesis.vaciado`. No debe depender del motor legado. |
| `pgmx.synthesis.vaciado` | Handoff productivo | Punto estable para que la sintesis PGMX conozca el contrato V2. |
| `pgmx.vaciado_lab` | Laboratorio y oraculo | Puede usar trazas Maestro y memoria externa; no es dependencia productiva directa. |
| `tools.pgmx_vaciado` | Fachada historica hacia `pgmx.vaciado_lab` | Debe mantenerse como compatibilidad de imports/CLIs mientras la memoria viva lo referencie. |
| `tools.pgmx_vaciado_v2` | Fachada historica hacia `pgmx.vaciado` | Debe mantenerse solo como alias compatible del contrato V2. |

El tracker vivo del laboratorio Vaciado es
`pgmx/vaciado_lab/memory/current-state.md`. Antes de responder que falta o de
extender ese frente, leer ese archivo y `tests/test_pgmx_vaciado.py`.

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

- Reducir referencias historicas `tools.pgmx_vaciado.*` en memorias cuando el
  frente Vaciado se reactive y se migren comandos a `pgmx.vaciado_lab.*`.
- Mantener `tools/synthesize_pgmx.py`, `tools/pgmx_snapshot.py` y
  `tools/pgmx_adapters.py` como fachadas minimas; cualquier funcion nueva debe
  nacer en `pgmx/`.
- Revisar periodicamente que `tools/studies/` no acumule scripts sin README,
  fecha, tema o criterio de promocion a API.
