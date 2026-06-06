# PGMX Machining Lab

Este paquete contiene laboratorios de investigacion por familia de mecanizado.
No es dependencia productiva directa del sintetizador PGMX.

## Frontera

- La produccion vive en `pgmx.synthesis`.
- La lectura/adaptacion viven en `pgmx.snapshot` y `pgmx.adapters`.
- La evidencia, memoria y analizadores exploratorios viven bajo
  `pgmx.machining_lab.<familia>`.
- Cuando una regla se estabiliza, debe migrar al modulo productivo de su familia
  y quedar cubierta por tests.

## Laboratorios Vigentes

| Ruta | Familia | Estado |
| --- | --- | --- |
| `pgmx.machining_lab.pocket_milling` | `ClosedPocket` / pocket milling | Laboratorio heredado del frente historico de Vaciado. |

## Documentacion

- Fronteras generales: `docs/laboratory_frontiers.md`.
- Inventario actual: `docs/repository_audit_inventory.md`.
- Pocket milling: `pgmx/machining_lab/pocket_milling/README.md`.
