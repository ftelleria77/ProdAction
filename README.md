# CNC Furniture Project Manager

Aplicación Python para:
- Generar y gestionar proyectos de mobiliario modulares
- Escanear carpetas de módulos con archivos CNC
- Resumir piezas en planillas
- Generar esquemas de corte básicos sobre tableros de melamina

## Requisitos
- Python 3.10+
- Paquetes: `PySide6`, `pandas`, `openpyxl`, `pillow`, `cairosvg`

## Instalación

```powershell
cd C:\Dev\Repositorios\ProdAction
py -3 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución

```powershell
py -3 main.py
```

## Suite de tests

```powershell
pip install -r requirements-dev.txt
py -3 -m pytest -q
```

**El runner es `pytest`, no `unittest`.** Once tests de `tests/test_pgmx_reader.py`
están escritos como funciones sueltas y `unittest discover` **no los recolecta**:
corre 291 y da verde sin haberlos ejecutado. El conteo de la suite que registra la
bitácora de la reinvestigación (`iso/docs/hoja_de_ruta.md`) es siempre el de pytest.

## Orientacion rapida del repo
- Indice ordenado de documentacion: `docs/README.md`
- Cierre formal de auditoria general: `docs/general_audit_closure.md`
- Inventario de auditoria por subsistema: `docs/repository_audit_inventory.md`
- Rumbo de reorganizacion de arquitectura: `docs/architecture_reorganization.md`
- Guia rapida para estudiar el repo: `docs/repo_study_guide.md`
- Para PGMX, usar como fuente de verdad operativa `docs/synthesize_pgmx_help.md`, `docs/pgmx_snapshot_help.md` y `docs/pgmx_adapters_help.md`

## Flujo de la aplicación
1. Crear nuevo proyecto (nombre + carpeta raíz)
2. Escoger carpeta raíz para módulos
3. Exportar resumen CSV con `core.summary.export_summary`
4. Generar diagramas de corte con `core.nesting_service.generate_cut_diagrams`

## Sintesis PGMX
- Estado actual del sintetizador Maestro: `v1.6`
- Flujo unico de generacion `.pgmx`: `py -3 -m pgmx.synthesis`
- Guia completa del sintetizador: `docs/synthesize_pgmx_help.md`
- Guia del snapshot integral de `.pgmx`: `docs/pgmx_snapshot_help.md`
- Guia de adaptacion de `.pgmx` existentes hacia specs publicos: `docs/pgmx_adapters_help.md`
- Registro de familias geometricas: `docs/pgmx_geometry_registry.md`
- Nota historica del flujo anterior: `docs/en_juego_pgmx_export.md`
- Baseline principal versionado: `pgmx/data/maestro_baselines/Pieza.xml` junto con `Pieza.epl` y `def.tlgx`
- `build_synthesis_request(...)` y la CLI usan `pgmx/data/maestro_baselines` como baseline por defecto si no se indica otro
- Ejemplos y estudios manuales para ingeniería inversa: `archive/maestro_examples/`
- API programática para sintesis: `build_approach_spec(...)`, `build_retract_spec(...)`, `build_milling_depth_spec(...)`, `build_unidirectional_milling_strategy_spec(...)`, `build_bidirectional_milling_strategy_spec(...)`, `build_xn_spec(...)`, `build_line_spec(...)`, `build_channel_spec(...)`, `build_polyline_spec(...)`, `build_circle_spec(...)`, `build_contour_spec(...)`, `build_pocket_spec(...)`, `build_drill_spec(...)`, `build_drill_pattern_spec(...)`, `build_parametric_variable_spec(...)`, `build_synthesis_request(...)` y `synthesize_request(...)` en `pgmx.synthesis`
- API programatica para inspeccion/construccion geometrica: `read_pgmx_geometries(...)`, `build_point_geometry_profile(...)`, `build_line_geometry_profile(...)`, `build_circle_geometry_profile(...)`, `build_composite_geometry_profile(...)` y `build_compensated_toolpath_profile(...)`
- API programatica para snapshot integral de un `.pgmx`: `read_pgmx_snapshot(...)`, `snapshot_to_dict(...)` y `write_pgmx_snapshot_json(...)` en `pgmx.snapshot`
- API programatica para adaptar `.pgmx` existentes al subset publico del sintetizador: `adapt_pgmx_snapshot(...)`, `adapt_pgmx_path(...)`, `adaptation_to_dict(...)` y `write_pgmx_adaptation_json(...)` en `pgmx.adapters`
- `PgmxAdaptationResult.build_synthesis_request(...)` convierte el material adaptable a un `PgmxSynthesisRequest`; por defecto arma familias publicas, y `build_synthesis_request(..., ordered_machinings=...)` permite preservar una secuencia exacta cuando el flujo lo necesita
- La sintesis de `.pgmx` permite fijar el area de `Parametros de Maquina` mediante `execution_fields` en la API o `--execution-fields/--area` en la CLI; si no se indica, usa `HG` por defecto.
- La seguridad de profundidad usa `pgmx/data/tool_catalog.csv`: la profundidad total del fresado o del taladro no puede superar `sinking_length` de la herramienta cuando `ToolKey` queda resuelto.
- Constante publica de version: `pgmx.synthesis.SYNTHESIZER_VERSION`
- Nueva helper publica de estrategias: `build_helical_milling_strategy_spec(...)`
- `Helicoidal` queda soportada por ahora para circulos cerrados via `CircleSpec`
- en `CircleSpec`, `SideOfFeature` conserva el circulo nominal y desplaza el radio efectivo del toolpath segun winding + `tool_width / 2`
- todo `.pgmx` sintetizado incluye un `Xn` final configurable via `XnSpec` / `build_xn_spec(...)`
Estado validado hasta ahora en `pgmx.synthesis`:
- fresados lineales y polilineas lineales abiertas/cerradas
- ranuras lineales `SlotSide` horizontales con `Sierra Vertical X`
- fresados circulares cerrados via `CircleSpec`
- escuadrado exterior del contorno de pieza via `ContourSpec`
- pocket milling / `ClosedPocket` via `PocketSpec`
- taladros puntuales sobre `Top`, `Front`, `Back`, `Right` y `Left` via `DrillSpec`
- patrones rectangulares de taladros via `DrillPatternSpec`
- lectura y clasificacion de geometria base: puntos, lineas, circulos y curvas compuestas abiertas/cerradas
- compensacion geometrica reusable para lineas, arcos, circulos y curvas compuestas abiertas/cerradas
- la sintesis publica completa de mecanizado sigue expuesta hoy via `LineSpec`, `ChannelSpec`, `PolylineSpec`, `CircleSpec`, `ContourSpec`, `PocketSpec`, `DrillSpec` y `DrillPatternSpec`
- `SideOfFeature` `Center|Right|Left`
- fresados pasantes y no pasantes, con `Extra`/`OvercutLength`
- taladros pasantes y no pasantes, con `Extra` aplicado sobre `TrajectoryPath`
- en pasante, `Depth.StartDepth/EndDepth` queda ligado al `DepthName` real de la pieza y `Extra` desplaza `cut_z`
- `Approach` y `Retract` con `Line` y `Arc`
- estrategias publicas `Unidireccional` y `Bidireccional` para linea simple, polilinea lineal abierta/cerrada, circulo y escuadrado
- estrategia publica `Helicoidal` para circulo cerrado con vuelta final opcional
- para `Approach Line + Down` ya esta volcada la regla observada en Maestro: una sola bajada oblicua desde un punto previo desplazado segun la direccion de entrada
- para `Retract Line + Up` ya esta volcada la regla observada en Maestro: una sola subida oblicua hacia un punto final desplazado segun la direccion de salida
- para `Arc + Quote` ya esta volcada la regla observada en Maestro para entradas/salidas en sentido horario y antihorario, incluyendo el toolpath vertical cuando la estrategia esta deshabilitada
- para `Retract Arc + Up` ya esta volcada la regla observada en Maestro: arco en plano vertical segun la direccion de salida, seguido de linea vertical, sin alterar `TrajectoryPath`
- por limitacion de Maestro, `Retract Arc + Up` queda bloqueado en polilineas abiertas de varios segmentos con estrategia multipasada `PH`
- esas reglas de entrada/salida ya quedaron unificadas sobre la tangente de entrada/salida del toolpath efectivo, no sobre una familia geometrica puntual
- caso manual validado: escuadrado exterior con `E001`, pasante + `Extra=1`, `Approach Arc + Quote x2` y `Retract Arc + Quote x2`; hoy ya queda expuesto por `ContourSpec`, con 4 orientaciones validas de `MidEdgeStart`, ambas combinaciones exteriores `CounterClockwise + Right` / `Clockwise + Left`, y `origin_x/y/z` limitado a `WorkpieceSetup/Placement`

Flujo recomendado de alto nivel:
- describir cada mecanizado con specs (`LineSpec`, `ChannelSpec`, `PolylineSpec`, `CircleSpec`, `ContourSpec`, `PocketSpec`, `DrillSpec`, `DrillPatternSpec`)
- armar el request con `build_synthesis_request(...)`
- ejecutar `synthesize_request(...)`
- para una guia paso a paso con ejemplos completos, ver `docs/synthesize_pgmx_help.md`
