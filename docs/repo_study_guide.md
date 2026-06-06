# Guia Rapida De Estudio Del Repo

Esta guia resume como esta organizado ProdAction al 2026-06-06. Sirve para
entrar rapido al repo antes de tocar codigo.

## Estado actual

ProdAction es una aplicacion desktop de produccion para muebles/CNC. Hoy tiene
estos frentes grandes:

- gestion de proyectos, locales, modulos y piezas;
- lectura, adaptacion, reparacion y sintesis de `.pgmx` Maestro;
- planillas de produccion y diagramas de corte;
- sintesis ISO experimental a partir de estados PGMX;
- herramienta separada para piso/CNC basada en archivos `.iso`;
- estudios reproducibles archivados bajo `tools/studies/`.

El sintetizador PGMX real vive en `pgmx.synthesis` y expone
`SYNTHESIZER_VERSION = "1.6"`.

## Estructura principal

| Ruta | Rol |
| --- | --- |
| `main.py` | Entrada de la app PySide6. |
| `docs/repository_audit_inventory.md` | Inventario de auditoria por subsistema, modulo, proceso, tests y docs. |
| `docs/app_subsystem_audit.md` | Corte dedicado del subsistema `app/`, con flujos, correcciones y deuda residual aceptada. |
| `docs/core_subsystem_audit.md` | Corte dedicado del subsistema `core/`, iniciado por modelo/parser. |
| `app/ui.py` | Compone `ProjectDetailWindow` a partir de mixins. La logica de detalle vive en `app/project_detail_*.py`. |
| `app/main_window.py` | Ventana inicial de seleccion de proyectos. |
| `app/project_detail_*.py` | Flujos de detalle: procesamiento, inspeccion, salida, piezas, PGMX, colores y En-Juego. |
| `core/model.py` | Dataclasses: `Project`, `LocaleData`, `ModuleData`, `Piece`. |
| `core/parser.py` | Escaneo de carpetas, CSV y modulos. |
| `core/summary.py` | Resumen CSV y fachada historica de planillas. |
| `core/production_sheet.py` | Exportador Excel de planillas y fachada PDF historica. |
| `core/production_sheet_pdf.py` | Renderer PDF interactivo de planillas. |
| `core/nesting.py` | Fachada historica de diagramas de corte. |
| `core/nesting_service.py` | Orquestacion productiva de diagramas de corte. |
| `core/nesting_compat.py` | Contrato de aliases heredados de `core.nesting`. |
| `core/pgmx_processing.py` | Fachada compatible hacia `pgmx.processing`. |
| `pgmx/processing.py` | Lectura PGMX para dibujos/dimensiones y reparacion de ranuras invalidas. |
| `core/en_juego_synthesis.py` | Sintesis PGMX compuesta para En-Juego. |
| `core/en_juego_transform.py` | Transformaciones geometricas En-Juego sin IO PGMX. |
| `pgmx/synthesis/` | API publica para escribir `.pgmx` desde baseline Maestro. |
| `pgmx/snapshot.py` | Snapshot normalizado de `.pgmx` existentes. |
| `pgmx/adapters.py` | Adaptacion de snapshots hacia specs publicos. |
| `pgmx/machining_lab/pocket_milling/` | Laboratorio de evidencia para `ClosedPocket`/pocket milling. |
| `tools/studies/cut_diagrams/ordering_lab.py` | Laboratorio de algoritmos de guillotina. |
| `tools/studies/iso/minimal_fixtures_2026_05_03.py` | Generador archivado de fixtures minimos ISO. |
| `cnc_traceability/` | Subsistema de trazabilidad CNC compatible con Windows XP 32 bits. |
| `iso_state_synthesis/` | Subsistema experimental por estado para futura traduccion `.pgmx -> .iso`. |

## Flujos de aplicacion

### Procesar proyecto

Entrada desde `ProjectDetailWindow.process_project()` en
`app/project_detail_processing.py`.

Flujo:

1. valida estructura de proyecto/local/modulo;
2. escanea modulos con `core.parser`;
3. preserva configuracion previa cuando corresponde;
4. escribe `module_config.json` y `local_config.json`;
5. exporta `resumen_piezas.csv`;
6. genera SVG por pieza con `pgmx.processing.generate_project_piece_drawings`.

### Inspeccionar modulo

Entrada desde `ProjectDetailWindow.inspect_module()` en
`app/project_detail_inspection.py`.

Responsabilidades relevantes:

- editar piezas, cantidades, color, fuente `.pgmx` y observaciones;
- previsualizar SVG de pieza;
- configurar En-Juego;
- detectar ranuras `SlotSide` verticales no ejecutables;
- exponer el boton `Corregir PGMX` para reparar el programa asociado.

### Generar planillas

Entrada desde `ProjectDetailWindow.generate_sheets()` en
`app/project_detail_output.py`.

Genera:

- estructura de carpetas CNC por proyecto/local/modulo;
- PDF por local con `core.production_sheet.export_production_sheet_pdf`;
- Excel opcional con `core.production_sheet.export_production_sheet`.

### Diagramas de corte

Entrada desde `ProjectDetailWindow.show_cuts()` en
`app/project_detail_output.py`.

Motor:

- `core.nesting_service.generate_cut_diagrams(...)`;
- agrupa piezas por material/color y espesor;
- usa medidas reales del programa PGMX cuando existen;
- respeta En-Juego como pieza compuesta;
- usa tableros configurados si existen.

El default actual para guillotina longitudinal/transversal es
`brkga-tail`, definido por `CUT_GUILLOTINE_ALGORITHM_PREFERRED`.

`core.nesting` es una fachada historica. La implementacion productiva esta
separada en modulos `core.nesting_*`, y el contrato de compatibilidad para
laboratorios esta declarado en `core.nesting_compat`.

### Sintesis y adaptacion PGMX

Fuente de verdad: `docs/synthesize_pgmx_help.md`.

Specs publicos soportados por `pgmx.synthesis`:

- `LineMillingSpec`;
- `SlotMillingSpec`;
- `PolylineMillingSpec`;
- `CircleMillingSpec`;
- `SquaringMillingSpec`;
- `PocketMillingSpec`;
- `DrillingSpec`;
- `DrillingPatternSpec`;
- `XnSpec`.

Reglas importantes:

- baseline versionado: `pgmx/data/maestro_baselines/Pieza.xml` + `Pieza.epl` +
  `def.tlgx`;
- `build_synthesis_request(...)` usa ese baseline por default;
- `ordered_machinings` preserva orden exacto de worksteps;
- `machining_order` ordena familias cuando se pasan listas separadas;
- cuando una herramienta queda resuelta, se valida contra
  `pgmx/data/tool_catalog.csv`; cuando Maestro debe resolverla despues,
  `ToolKey` puede quedar vacio por contrato.

### Reparacion de ranuras invalidas

Problema:

- Maestro puede guardar una ranura `SlotSide` vertical con `Sierra Vertical X`;
- el CNC no puede ejecutarla de forma segura.

Codigo:

- deteccion: `get_invalid_slot_machining_issues(...)`;
- reparacion: `repair_invalid_slot_machining_by_rotating_ccw(...)`;
- implementacion: `pgmx/processing.py`;
- fachada historica: `core/pgmx_processing.py`;
- UI: boton `Corregir PGMX` en la inspeccion de modulo.

La reparacion rota el PGMX 90 grados antihorario, re-sintetiza los mecanizados
adaptables y reemplaza el archivo original si la validacion posterior no deja
issues.

### Trazabilidad CNC

Codigo: `cnc_traceability/viewer_xp.py`.

Entrada del subsistema: `cnc_traceability/README.md`.
Contrato: `cnc_traceability/docs/contract.md`.
Memoria: `cnc_traceability/memory/current-state.md`.

Caracteristicas:

- no depende de PySide6;
- usa solo standard library/Tkinter;
- pensado para empaquetar como ejecutable 32 bits compatible con Windows XP;
- funciona como herramienta auxiliar de trazabilidad de ejecucion, no como
  generador de programas;
- lee `cnc_project_viewer_index.json` o `prodaction_cnc_queue.json`;
- escanea `.iso` en una estructura de salida CNC;
- guarda avance en `cnc_progress.json`;
- prepara `USBMIX` borrando solo `.iso` existentes y copiando un unico `.iso`;
- no marca mecanizado automaticamente al copiar.

### ISO

No hay generador ISO nativo productivo. El estado actual es investigacion,
documentacion del postprocesado Maestro/CNC y el subsistema experimental por
estado `iso_state_synthesis/`.

Fuente historica: `docs/iso_synthesis_temporary_memory.md`.
Contrato CNC/ISO observado: `docs/iso_cnc_contract.md`.
Plan de fixtures minimos: `docs/iso_minimal_fixtures_plan.md`.
Generador de fixtures: `tools/studies/iso/minimal_fixtures_2026_05_03.py`.
Subsistema experimental: `iso_state_synthesis/README.md`.

Estado actual documentado:

- los fixtures minimos ya fueron generados, postprocesados y comparados;
- `docs/iso_cnc_contract.md` consolida reglas de cabecera, `HG`, taladros,
  router y herramientas especiales;
- `iso_state_synthesis/` contiene el esqueleto separado con adaptador PGMX,
  diferenciales de estado y emisor candidato explicado;
- el siguiente paso es extender el emisor multi-trabajo por diferenciales.

## Comandos utiles de verificacion

```powershell
py -3 -m compileall -q main.py app core pgmx iso_state_synthesis cnc_traceability tools tests
py -3 -m unittest discover -s tests -p "test*.py"
py -3 -m iso_state_synthesis --help
py -3 -m pgmx.synthesis --help
py -3 -m pgmx.snapshot --help
py -3 -m pgmx.adapters --help
py -3 -m tools.studies.iso.minimal_fixtures_2026_05_03 --output-dir tmp/iso_minimal_fixtures
py -3 -m tools.studies.cut_diagrams.ordering_lab --help
```

Prueba de humo PGMX recomendada:

1. sintetizar a `tmp/`;
2. adaptar con `pgmx.adapters`;
3. borrar el archivo temporal;
4. confirmar `git status --short --branch`.

## Riesgos actuales

- El frente `app/project_detail_*` sigue siendo amplio y conviene auditarlo por
  flujo, no por archivo aislado.
- `pgmx.processing` e `iso_state_synthesis.emitter` son modulos grandes con
  varias responsabilidades internas.
- La suite automatizada cubre app/core/PGMX/nesting/planillas, pero
  `iso_state_synthesis/`, `cnc_traceability/` y `tools/studies/` aun tienen
  cobertura dedicada limitada.
- `requirements.txt` no fija versiones.
- La investigacion ISO es extensa, pero aun no es API productiva.
- Las memorias historicas son utiles, pero conviene promover decisiones
  estables a guias cortas.
