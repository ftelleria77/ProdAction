# Auditoria Del Subsistema `pgmx/`

Estado: corte inicial del bloque `pgmx/`, 2026-06-06.

Este documento registra la auditoria productiva del subsistema PGMX despues de
cerrar los bloques `app/` y `core/`. La frontera actual queda dividida en
lectura/dibujo, snapshot, adaptacion, sintesis y laboratorio de mecanizados.

## Mapa Actual

| Zona | Modulos | Funcion |
| --- | --- | --- |
| Fachadas publicas del paquete | `pgmx.__init__` | Expone los subpaquetes vigentes: `processing`, `snapshot`, `adapters`, `synthesis` y `machining_lab`. |
| Lectura y dibujo productivo | `pgmx.processing` | Resuelve rutas de programas, lee dimensiones, extrae mecanizados, dibuja SVG, informa diferencias de dimensiones y repara ranuras invalidas. |
| Snapshot de Maestro | `pgmx.snapshot` | Normaliza un `.pgmx` existente en dataclasses con workpiece, variables, planos, geometrias, features, operaciones, worksteps y tooling embebido. |
| Adaptacion a specs | `pgmx.adapters` | Traduce snapshots al subconjunto publico del sintetizador y explica entradas no soportadas. |
| Sintesis PGMX | `pgmx.synthesis` | Escribe `.pgmx` desde specs publicos de fresado, pocket milling, taladros y orden de mecanizados. |
| Laboratorio | `pgmx.machining_lab.pocket_milling` | Conserva evidencia, memoria y exploracion de `ClosedPocket`/vaciado antes de promover reglas a produccion. |

## Procesos Donde Interviene

| Proceso | Entrada | Salida | Modulos PGMX |
| --- | --- | --- | --- |
| Inspeccion de modulo | Pieza + referencia `.pgmx` | Estado de programa, dimensiones y preview SVG | `pgmx.processing`, `pgmx.snapshot`. |
| Planillas y nesting | Proyecto procesado | Medidas reales, notas y dibujos de piezas | `pgmx.processing`. |
| Reparacion de ranuras | Programa con `SlotSide` vertical invalida | `.pgmx` rotado y re-sintetizado | `pgmx.processing`, `pgmx.adapters`, `pgmx.synthesis`. |
| En-Juego | PGMX individuales adaptables | PGMX compuesto | `pgmx.snapshot`, `pgmx.adapters`, `pgmx.synthesis`. |
| Re-sintesis/refactor | `.pgmx` Maestro existente | Specs publicos o razones de rechazo | `pgmx.snapshot`, `pgmx.adapters`. |
| Investigacion pocket | Corpus Maestro y trazas | Reglas candidatas y fixtures | `pgmx.machining_lab.pocket_milling`, `pgmx.synthesis.milling.pocket_trace`. |

## Subcorte Inicial

El primer subcorte revisa `pgmx.processing`, `pgmx.snapshot` y
`pgmx.adapters`, porque son las fachadas que conectan con `app/`, `core/` y
En-Juego.

Hallazgos:

- `pgmx.processing` sigue siendo el modulo mas cargado del bloque. Mantiene
  responsabilidades de lectura, dibujo, notas de dimensiones y reparacion de
  ranuras. Por ahora se conserva como frontera productiva, pero conviene
  seguir extrayendo helpers cuando aparezcan bugs o cambios de comportamiento.
- El renderer SVG tenia un bug de proyeccion lateral: cuando `projected_y` no
  estaba informado, usaba `op.x` como fallback. Se corrigio para usar `op.y`.
- `pgmx.snapshot` y `pgmx.adapters` tienen contratos publicos documentados y
  CLI vigente con `py -3 -m pgmx.snapshot` y `py -3 -m pgmx.adapters`.
- La cobertura directa de `pgmx.processing` era indirecta. Se agrego una suite
  focal para el renderer SVG.

## Subcorte Sintetizador

`pgmx.synthesis.core` y `pgmx.synthesis.__init__` se conservan como fachadas de
compatibilidad. La produccion real queda en:

| Familia | Modulos Productivos |
| --- | --- |
| Programa y estado | `pgmx.synthesis.common.program`, `common.output`. |
| XML e hidratacion | `pgmx.synthesis.common.xml`, `common.hydration`. |
| Pieza, geometria y profundidad | `pgmx.synthesis.common.piece`, `common.geometry`, `common.depth`. |
| Herramientas, estrategias y leads | `pgmx.synthesis.common.tools`, `common.strategy`, `common.leads`. |
| Fresados | `pgmx.synthesis.milling.line`, `slot`, `profile`, `circle`, `squaring`, `pocket`. |
| Pocket/vaciado | `pgmx.synthesis.milling.pocket_contract`, `pocket_rectangular`, `pocket_trace`. |
| Taladros | `pgmx.synthesis.drilling.single`, `drilling.pattern`. |

Hallazgos aplicados:

- Se retiro el fallback operativo a `tools/` para datos del sintetizador en
  modo empaquetado. Los datos versionados deben resolverse desde `pgmx/data` o
  `_internal/pgmx/data`.
- Se agrego cobertura para que `_module_data_dir()` ignore un directorio
  heredado `tools/` y prefiera el bundle PGMX vigente.
- Se actualizo el README de `pgmx.machining_lab.pocket_milling` para que el
  nombre principal sea pocket milling y Vaciado quede registrado como origen
  historico del laboratorio.

## Deuda Residual

- Separar gradualmente `pgmx.processing` en helpers internos cuando el siguiente
  cambio toque una responsabilidad concreta: resolucion de rutas, parser
  fallback, dibujo SVG, notas de dimensiones o reparacion `SlotSide`.
- Agregar fixtures chicos para `pgmx.snapshot` y `pgmx.adapters` que no dependan
  del corpus externo de Maestro.
- Completar una segunda pasada por `pgmx.synthesis.milling.pocket_trace`, porque
  sigue siendo el frente mas grande y conserva reglas historicas de laboratorio.
- Mantener `pgmx.machining_lab/pocket_milling` como laboratorio vivo; sus
  pendientes de vaciado no deben mezclarse con la API productiva sin evidencia.
