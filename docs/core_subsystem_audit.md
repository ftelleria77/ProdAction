# Auditoria Del Subsistema Core

Estado: bloque auditado y cerrado para esta etapa, 2026-06-06.

Este documento registra la lectura actual del subsistema `core/`. Su objetivo es
separar contratos de dominio, servicios productivos, fachadas compatibles y
deuda residual antes de avanzar sobre refactors internos.

## Frontera

`core/` es la capa de dominio y servicios productivos compartidos. No debe
contener UI PySide6 ni decisiones de interaccion con el usuario. Sus salidas
principales alimentan `app/`, `pgmx/`, planillas, diagramas de corte y En-Juego.

Fronteras actuales:

- modelo de datos: `core.model`;
- escaneo de proyectos: `core.parser`;
- resumen/planillas/PDF: `core.summary`, `core.production_sheet*`,
  `core.production_pdf`;
- diagramas de corte: `core.nesting_service`, `core.nesting_*`;
- En-Juego productivo: `core.en_juego_transform`, `core.en_juego_synthesis`;
- fachadas compatibles: `core.nesting`, `core.nesting_compat`,
  `core.pgmx_processing`.

## Subcorte Modelo Y Parser

Estado: auditado y limpiado, 2026-06-06.

Responsabilidades actuales:

- `core.model`: dataclasses `Project`, `LocaleData`, `ModuleData`, `Piece` y
  normalizaciones compartidas de veta/observaciones.
- `core.parser.parse_cnc_file`: lectura tolerante de lineas simples de pieza en
  programas CNC/PGMX.
- `core.parser.load_module_summary`: lectura de CSV de modulo, tanto con
  encabezados como en formato posicional historico.
- `core.parser.scan_project`: escaneo de carpetas de modulos y armado de
  `ModuleData`.
- `core.parser.inspect_project_layout` y `scan_project_structure`:
  clasificacion proyecto/local/modulo para estructuras normalizadas.

Correcciones del subcorte:

- `load_module_summary()` ahora distingue CSV con encabezados antes de intentar
  el parseo posicional historico.
- Los aliases de encabezados son ordenados y deterministas; `largo` queda como
  alias de alto/height y no compite con ancho/width.
- El parseo con encabezados conserva `piece_name`, `thickness`, `source` y
  `piece_type`, ademas de cantidad, dimensiones, color y veta.
- Las dimensiones con coma decimal se normalizan antes de poblar metadata.
- Se agregaron `tests/test_core_model.py` y `tests/test_core_parser.py`.

## Deuda Residual Modelo Y Parser

- `load_module_summary()` sigue siendo una funcion amplia con helpers anidados.
  Queda estabilizada por tests, pero podria extraerse a un modulo dedicado si
  el parser crece.
- `parse_cnc_file()` mantiene heuristicas simples de texto; la lectura PGMX real
  sigue perteneciendo a `pgmx.processing`.
- `scan_project()` conserva el contrato historico de escanear subcarpetas como
  modulos; las estructuras proyecto/local/modulo usan `scan_project_structure()`.

## Subcorte Planillas Y PDF

Estado: auditado y limpiado, 2026-06-06.

Responsabilidades actuales:

- `core.summary`: export CSV y fachada compatible hacia planillas Excel/PDF.
- `core.production_sheet_data`: preparacion compartida de piezas, cantidades,
  dimensiones, settings de modulo y notas PGMX para planillas.
- `core.production_sheet_images`: conversion/preparacion de SVG/PNG, reemplazo
  visual En-Juego y popups PDF.
- `core.production_sheet`: exportador Excel productivo.
- `core.production_sheet_pdf`: renderer PDF interactivo.
- `core.production_pdf`: primitivas PDF/JavaScript de bajo nivel.

Correcciones del subcorte:

- `safe_float()`, `safe_int()`, `confirmed_dimension()` e
  `is_valid_thickness()` aceptan coma decimal a traves de la normalizacion
  central de `production_sheet_data`.
- Se agrego `tests/test_production_sheet_data.py` para helpers numericos,
  `piece_from_sheet_row()`, `derive_module_dimensions()` y
  `load_module_sheet_data()`.

Deuda residual:

- `export_production_sheet()` y `export_production_sheet_pdf()` siguen siendo
  renderers largos. Tienen helpers de datos/imagenes/PDF separados; conviene
  evitar refactors internos sin fixtures visuales o mocks mas completos.
- La disponibilidad de Pillow/CairoSVG/Qt sigue siendo opcional y se valida por
  fallback indirecto; no hay prueba visual completa del layout final.

## Subcorte Diagramas De Corte

Estado: auditado y limpiado, 2026-06-06.

Responsabilidades actuales:

- `core.nesting_service`: API productiva `generate_cut_diagrams()`.
- `core.nesting_model`: tipos, constantes de corte, vetas y parametros BRKGA.
- `core.nesting_boards`: normalizacion de tableros, margenes y resolucion por
  material/espesor.
- `core.nesting_pieces`: expansion de piezas, dimensiones PGMX y composiciones
  En-Juego para corte.
- `core.nesting_strategy`, `geometry`, `dispatch`, `free_rectangles`,
  `guillotine`, `guillotine_sections`, `brkga`: estrategia y algoritmos de
  empaque.
- `core.nesting_pdf`: renderer imprimible de diagramas.
- `core.nesting`/`core.nesting_compat`: fachada compatible historica para API
  publica, tests y laboratorio de ordenamiento.

Correcciones del subcorte:

- `core.nesting_boards._safe_float()` acepta coma decimal en definiciones de
  tablero y margen.
- `core.nesting_pieces.safe_float()`, `safe_quantity()` y
  `has_valid_cut_dimensions()` aceptan coma decimal en piezas/configuracion.
- Se extendieron tests focales en `tests/test_nesting_boards.py` y
  `tests/test_nesting_pieces.py`.

Deuda residual:

- La fachada `core.nesting` conserva nombres privados historicos porque
  `tools.studies.cut_diagrams.ordering_lab` los usa declaradamente.
- Los algoritmos de empaque no se refactorizaron en este corte; ya tienen
  cobertura focal y cualquier cambio debe validarse con casos de corte reales.

## Subcorte En-Juego Productivo

Estado: auditado y limpiado, 2026-06-06.

Responsabilidades actuales:

- `core.en_juego_transform`: geometria CAM pura para trasladar/rotar specs
  PGMX adaptadas al sistema de la composicion En-Juego.
- `core.en_juego_synthesis`: resolucion de piezas/layout, transferencia de
  mecanizados superiores, calculo de divisiones, escuadrado y escritura final
  con `pgmx.synthesis`.

Correcciones del subcorte:

- `_parse_quantity()` acepta cantidades guardadas como enteros o decimales con
  punto/coma, de forma consistente con el resto del sistema.
- Se agregaron `tests/test_en_juego_transform.py` y
  `tests/test_en_juego_synthesis.py` para transformaciones, helpers seguros,
  validacion de solapes/divisiones y contrato de resultado.

Deuda residual:

- `create_en_juego_pgmx()` sigue siendo el orquestador productivo completo y
  depende de snapshots/adaptadores/PGMX reales. La cobertura agregada cubre
  reglas puras; los casos integrales deben validarse con fixtures PGMX.
- Las reglas geometricas de divisiones siguen concentradas en
  `core.en_juego_synthesis`; si crecen, conviene extraer un modulo de geometria
  En-Juego productiva.

## Subcorte Fachadas Compatibles

Estado: auditado y limpiado, 2026-06-06.

Fachadas vigentes:

- `core.summary`: mantiene `export_summary()` como API propia y reexporta
  planillas Excel/PDF para imports historicos.
- `core.pgmx_processing`: reexporta `pgmx.processing` y conserva `__getattr__`
  para imports historicos.
- `core.nesting`: reexporta exactamente el contrato declarado en
  `core.nesting_compat`.
- `core.nesting_compat`: declara nombres publicos, nombres de laboratorio y
  nombres legacy todavia vivos.

Correcciones del subcorte:

- Se agrego `tests/test_core_facades.py` para `core.pgmx_processing`,
  `core.summary` y la declaracion de `core.nesting`.

Deuda residual:

- Las fachadas siguen vigentes porque hay imports historicos/laboratorios que
  dependen de ellas. No se retiran en este bloque.
- `core.pgmx_processing` no debe recibir logica nueva; la implementacion
  productiva vive en `pgmx.processing`.

## Cierre Del Bloque Core

El bloque `core/` queda cerrado para esta etapa de auditoria/reorganizacion:

- contratos de modelo/parser documentados y cubiertos por tests focales;
- planillas/PDF estabilizadas en preparacion de datos y fachadas;
- diagramas de corte/nesting auditados con fachadas compatibles declaradas;
- En-Juego productivo cubierto en sus reglas puras principales;
- fachadas compatibles vigentes documentadas y testeadas.

Proximo bloque recomendado: `pgmx/`, empezando por `pgmx.processing`,
`pgmx.snapshot` y `pgmx.adapters`, antes de volver al sintetizador/laboratorio.
