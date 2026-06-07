# Cierre De Auditoria General

Estado: cierre formal, 2026-06-07.

Este documento cierra la pasada general de auditoria y reorganizacion de
ProdAction para esta etapa. No reemplaza las auditorias por subsistema; resume
que quedo ordenado, donde esta documentado y que deuda queda aceptada para la
proxima etapa.

## Alcance Cerrado

La auditoria general queda cerrada sobre estos bloques:

| Bloque | Estado | Evidencia Principal |
| --- | --- | --- |
| `app/` | Auditado y documentado como capa desktop PySide6. | `docs/app_subsystem_audit.md`, `docs/repo_study_guide.md`. |
| `core/` | Auditado y documentado como dominio/servicios compartidos, con fachadas compatibles declaradas. | `docs/core_subsystem_audit.md`, `docs/repository_audit_inventory.md`. |
| `pgmx/` | Auditado como subsistema productivo PGMX, fuera de `tools/`. | `docs/pgmx_subsystem_audit.md`, `docs/synthesize_pgmx_help.md`. |
| `pgmx.synthesis/` | Modularizacion arquitectonica cerrada; pendientes futuros quedan en decisiones de producto o laboratorio. | `docs/pgmx_synthesis_modularization_plan.md`, `docs/pgmx_synthesis_modularization_temporary_memory.md`. |
| `pgmx.machining_lab/` | Frontera de laboratorio declarada; pocket milling absorbe la investigacion historica de Vaciado. | `pgmx/machining_lab/README.md`, `pgmx/machining_lab/pocket_milling/README.md`. |
| `iso_state_synthesis/` | Auditado como subsistema experimental por estado; la auditoria funcional queda pausada. | `docs/iso_state_synthesis_subsystem_audit.md`, `iso_state_synthesis/README.md`. |
| `cnc_traceability/` | Auditado como visor CNC standalone compatible XP, con cobertura focal de helpers puros. | `docs/cnc_traceability_subsystem_audit.md`, `tests/test_cnc_traceability.py`. |
| `tools/studies/` | Auditado como laboratorio reproducible, no API productiva. | `docs/tools_studies_subsystem_audit.md`, `tools/studies/README.md`. |
| Documentacion rectora | Indices y guias alineados con rutas vigentes. | `docs/README.md`, `docs/repository_audit_inventory.md`, `docs/repo_study_guide.md`, `docs/architecture_reorganization.md`. |

## Decisiones Estables

- El codigo productivo vive principalmente en `app/`, `core/` y `pgmx/`.
- `pgmx.synthesis` es la API publica vigente para sintetizar `.pgmx`; las
  fachadas historicas bajo `tools/` fueron retiradas.
- Vaciado queda integrado como `ClosedPocket`/pocket milling:
  contrato productivo en `pgmx.synthesis.milling.pocket_contract` y laboratorio
  en `pgmx.machining_lab.pocket_milling`.
- `core.summary`, `core.pgmx_processing` y `core.nesting` siguen como fachadas
  compatibles documentadas, no como destino para logica nueva.
- `iso_state_synthesis/` no dirige la arquitectura productiva mientras siga
  experimental; su auditoria funcional se retoma solo por decision explicita.
- `tools/studies/` conserva evidencia ejecutable. Una regla solo sale de ahi si
  se promueve con contrato y validacion al subsistema correspondiente.
- `cnc_traceability/` es una herramienta separada para piso/CNC, no reemplaza la
  aplicacion principal.

## Deuda Aceptada

Esta deuda queda registrada pero no bloquea el cierre general:

- `app/project_detail_*` conserva flujos amplios; se audita por workflow cuando
  se toque funcionalidad concreta.
- `pgmx.processing` sigue reuniendo lectura, dibujo y reparacion PGMX; ya esta
  documentado y con cobertura focal, pero puede subdividirse si crece.
- `iso_state_synthesis.emitter` sigue grande y experimental. La siguiente
  auditoria funcional ISO debe estudiar reglas concretas contra corpus, no
  reabrir la reorganizacion general.
- `cnc_traceability/` requiere validacion manual en la PC XP/CNC real:
  permisos, pantalla, unidades compartidas y comportamiento de `USBMIX`.
- `tools/studies/` no tiene suite automatizada completa porque depende de
  corpus externos y ejecuciones de estudio.
- `requirements.txt` no fija versiones; conviene tratarlo como frente de
  reproducibilidad separado.
- Las memorias historicas siguen siendo largas. Las decisiones estables deben
  promoverse gradualmente a guias cortas cuando vuelvan a usarse.

## Validacion Del Cierre

Baseline validado antes de este cierre:

```powershell
py -3 -m compileall -q main.py app core pgmx iso_state_synthesis cnc_traceability tools tests
py -3 -m unittest discover -s tests -p "test*.py"
```

Resultado de la ultima corrida registrada: 360 tests OK.

## Proxima Etapa Recomendada

No hay un bloque general sin auditar. La proxima etapa deberia elegirse como
frente especifico:

- reproducibilidad de entorno (`requirements.txt`, versiones y smoke commands);
- validacion real de `cnc_traceability/` en la PC del CNC;
- refinamiento funcional de `iso_state_synthesis/` si se decide reactivar ISO;
- trabajo de laboratorio pocket milling si se retoma investigacion de vaciados;
- reduccion puntual de un flujo amplio de `app/project_detail_*` solo cuando una
  necesidad funcional lo justifique.
