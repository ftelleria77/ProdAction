# Guia Rapida De Estudio Del Repo

Esta guia resume como esta organizado ProdAction al 2026-05-02. Sirve para
entrar rapido al repo antes de tocar codigo.

## Estado actual

ProdAction es una aplicacion desktop de produccion para muebles/CNC. Hoy tiene
cuatro frentes grandes:

- gestion de proyectos, locales, modulos y piezas;
- lectura, adaptacion, reparacion y sintesis de `.pgmx` Maestro;
- planillas de produccion y diagramas de corte;
- herramienta separada para piso/CNC basada en archivos `.iso`.

El sintetizador PGMX real vive en `tools/synthesize_pgmx.py` y expone
`SYNTHESIZER_VERSION = "1.6"`.

## Estructura principal

| Ruta | Rol |
| --- | --- |
| `main.py` | Entrada de la app PySide6. |
| `app/ui.py` | UI principal y coordinacion de flujos. Archivo grande; leer por secciones/metodos. |
| `core/model.py` | Dataclasses: `Project`, `LocaleData`, `ModuleData`, `Piece`. |
| `core/parser.py` | Escaneo de carpetas, CSV y modulos. |
| `core/summary.py` | Resumen CSV, Excel y PDF de produccion. |
| `core/nesting.py` | Expansion de piezas, nesting, guillotina y PDF de corte. |
| `core/pgmx_processing.py` | Lectura PGMX para dibujos/dimensiones y reparacion de ranuras invalidas. |
| `core/en_juego_synthesis.py` | Sintesis PGMX compuesta para En-Juego. |
| `tools/synthesize_pgmx.py` | API publica para escribir `.pgmx` desde baseline Maestro. |
| `tools/pgmx_snapshot.py` | Snapshot normalizado de `.pgmx` existentes. |
| `tools/pgmx_adapters.py` | Adaptacion de snapshots hacia specs publicos. |
| `tools/studies/cut_diagrams/ordering_lab.py` | Laboratorio de algoritmos de guillotina. |
| `tools/studies/iso/minimal_fixtures_2026_05_03.py` | Generador archivado de fixtures minimos ISO. |
| `cnc_traceability/` | Subsistema de trazabilidad CNC compatible con Windows XP 32 bits. |
| `iso_generation/` | Subsistema experimental para futura traduccion `.pgmx -> .iso`. |

## Flujos de aplicacion

### Procesar proyecto

Entrada desde `ProjectDetailWindow.process_project()` en `app/ui.py`.

Flujo:

1. valida estructura de proyecto/local/modulo;
2. escanea modulos con `core.parser`;
3. preserva configuracion previa cuando corresponde;
4. escribe `module_config.json` y `local_config.json`;
5. exporta `resumen_piezas.csv`;
6. genera SVG por pieza con `core.pgmx_processing.generate_project_piece_drawings`.

### Inspeccionar modulo

Entrada desde `ProjectDetailWindow.inspect_module()` en `app/ui.py`.

Responsabilidades relevantes:

- editar piezas, cantidades, color, fuente `.pgmx` y observaciones;
- previsualizar SVG de pieza;
- configurar En-Juego;
- detectar ranuras `SlotSide` verticales no ejecutables;
- exponer el boton `Corregir PGMX` para reparar el programa asociado.

### Generar planillas

Entrada desde `ProjectDetailWindow.generate_sheets()`.

Genera:

- estructura de carpetas CNC por proyecto/local/modulo;
- PDF por local con `core.summary.export_production_sheet_pdf`;
- Excel opcional con `core.summary.export_production_sheet`.

### Diagramas de corte

Entrada desde `ProjectDetailWindow.show_cuts()`.

Motor:

- `core.nesting.generate_cut_diagrams(...)`;
- agrupa piezas por material/color y espesor;
- usa medidas reales del programa PGMX cuando existen;
- respeta En-Juego como pieza compuesta;
- usa tableros configurados si existen.

El default actual para guillotina longitudinal/transversal es
`brkga-tail`, definido por `CUT_GUILLOTINE_ALGORITHM_PREFERRED`.

### Sintesis y adaptacion PGMX

Fuente de verdad: `docs/synthesize_pgmx_help.md`.

Specs publicos soportados por `tools.synthesize_pgmx`:

- `LineMillingSpec`;
- `SlotMillingSpec`;
- `PolylineMillingSpec`;
- `CircleMillingSpec`;
- `SquaringMillingSpec`;
- `DrillingSpec`;
- `DrillingPatternSpec`;
- `XnSpec`.

Reglas importantes:

- baseline versionado: `tools/maestro_baselines/Pieza.xml` + `Pieza.epl` +
  `def.tlgx`;
- `build_synthesis_request(...)` usa ese baseline por default;
- `ordered_machinings` preserva orden exacto de worksteps;
- `machining_order` ordena familias cuando se pasan listas separadas;
- `ToolKey` resuelto activa validaciones contra `tools/tool_catalog.csv`.

### Reparacion de ranuras invalidas

Problema:

- Maestro puede guardar una ranura `SlotSide` vertical con `Sierra Vertical X`;
- el CNC no puede ejecutarla de forma segura.

Codigo:

- deteccion: `get_invalid_slot_machining_issues(...)`;
- reparacion: `repair_invalid_slot_machining_by_rotating_ccw(...)`;
- implementacion: `core/pgmx_processing.py`;
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
documentacion del postprocesado Maestro/CNC y un subsistema experimental
separado para iniciar la traduccion `.pgmx -> .iso`.

Fuente historica: `docs/iso_synthesis_temporary_memory.md`.
Contrato CNC/ISO observado: `docs/iso_cnc_contract.md`.
Plan de fixtures minimos: `docs/iso_minimal_fixtures_plan.md`.
Generador de fixtures: `tools/studies/iso/minimal_fixtures_2026_05_03.py`.
Subsistema experimental: `iso_generation/README.md`.

Estado actual documentado:

- los fixtures minimos ya fueron generados, postprocesados y comparados;
- `docs/iso_cnc_contract.md` consolida reglas de cabecera, `HG`, taladros,
  router y herramientas especiales;
- `iso_generation/` contiene el esqueleto separado con lector/adaptador PGMX,
  emision inicial de cabecera y comparador normalizado;
- el siguiente paso es implementar el MVP operativo por familias.

## Comandos utiles de verificacion

```powershell
python -m compileall main.py app core tools
python -c "import app.ui, core.parser, core.nesting, core.summary, core.pgmx_processing, core.en_juego_synthesis; print('core imports ok')"
python -c "from tools import synthesize_pgmx as sp; print(sp.SYNTHESIZER_VERSION)"
python -m tools.studies.iso.minimal_fixtures_2026_05_03 --output-dir tmp/iso_minimal_fixtures
python -m iso_generation --help
python -m tools.synthesize_pgmx --help
python -m tools.pgmx_snapshot --help
python -m tools.pgmx_adapters --help
python -m tools.studies.cut_diagrams.ordering_lab --help
```

Prueba de humo PGMX recomendada:

1. sintetizar a `tmp/`;
2. adaptar con `tools.pgmx_adapters`;
3. borrar el archivo temporal;
4. confirmar `git status --short --branch`.

## Riesgos actuales

- `app/ui.py` y `tools/synthesize_pgmx.py` concentran muchas responsabilidades.
- No hay suite formal de tests automatizados.
- `requirements.txt` no fija versiones.
- La investigacion ISO es extensa, pero aun no es API productiva.
- Las memorias historicas son utiles, pero conviene promover decisiones
  estables a guias cortas.
