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
cd C:\Users\fermi\Proyectos\my-python-api
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución

```powershell
python main.py
```

## Flujo de la aplicación
1. Crear nuevo proyecto (nombre + carpeta raíz)
2. Escoger carpeta raíz para módulos
3. Exportar resumen CSV con `core.summary.export_summary`
4. (Próximo paso) Ejecutar nesting con `core.nesting.first_fit_2d`

## Sintesis PGMX
- Estado actual del sintetizador Maestro: `v1.0`
- Flujo unico de generacion `.pgmx`: `python -m tools.synthesize_pgmx`
- Guia completa del sintetizador: `docs/synthesize_pgmx_help.md`
- Registro de familias geometricas: `docs/pgmx_geometry_registry.md`
- Nota historica del flujo anterior: `docs/en_juego_pgmx_export.md`
- Baseline principal versionado: `tools/maestro_baselines/Pieza.xml` junto con `Pieza.epl` y `def.tlgx`
- `build_synthesis_request(...)` y la CLI usan `tools/maestro_baselines` como baseline por defecto si no se indica otro
- Ejemplos y estudios manuales para ingeniería inversa: `archive/maestro_examples/`
- API programática para sintesis: `build_approach_spec(...)`, `build_retract_spec(...)`, `build_milling_depth_spec(...)`, `build_unidirectional_milling_strategy_spec(...)`, `build_bidirectional_milling_strategy_spec(...)`, `build_line_milling_spec(...)`, `build_polyline_milling_spec(...)`, `build_squaring_milling_spec(...)`, `build_drilling_spec(...)`, `build_synthesis_request(...)` y `synthesize_request(...)` en `tools.synthesize_pgmx`
- API programatica para inspeccion/construccion geometrica: `read_pgmx_geometries(...)`, `build_point_geometry_profile(...)`, `build_line_geometry_profile(...)`, `build_circle_geometry_profile(...)`, `build_composite_geometry_profile(...)` y `build_compensated_toolpath_profile(...)`
- La sintesis de `.pgmx` permite fijar el area de `Parametros de Maquina` mediante `execution_fields` en la API o `--execution-fields/--area` en la CLI; si no se indica, usa `HG` por defecto.
- La seguridad de profundidad usa `tools/tool_catalog.csv`: la profundidad total del fresado o del taladro no puede superar `sinking_length` de la herramienta cuando `ToolKey` queda resuelto.
- Constante publica de version: `tools.synthesize_pgmx.SYNTHESIZER_VERSION`
Estado validado hasta ahora en `tools.synthesize_pgmx`:
- fresados lineales y polilineas lineales abiertas/cerradas
- escuadrado exterior del contorno de pieza via `SquaringMillingSpec`
- taladros puntuales sobre `Top`, `Front`, `Back`, `Right` y `Left` via `DrillingSpec`
- lectura y clasificacion de geometria base: puntos, lineas, circulos y curvas compuestas abiertas/cerradas
- compensacion geometrica reusable para lineas, arcos, circulos y curvas compuestas abiertas/cerradas
- la sintesis publica completa de mecanizado sigue expuesta hoy via `LineMillingSpec`, `PolylineMillingSpec`, `SquaringMillingSpec` y `DrillingSpec`
- `SideOfFeature` `Center|Right|Left`
- fresados pasantes y no pasantes, con `Extra`/`OvercutLength`
- taladros pasantes y no pasantes, con `Extra` aplicado sobre `TrajectoryPath`
- en pasante, `Depth.StartDepth/EndDepth` queda ligado al `DepthName` real de la pieza y `Extra` desplaza `cut_z`
- `Approach` y `Retract` con `Line` y `Arc`
- estrategias publicas `Unidireccional` y `Bidireccional` para linea simple, polilinea lineal abierta/cerrada y escuadrado
- para `Approach Line + Down` ya esta volcada la regla observada en Maestro: una sola bajada oblicua desde un punto previo desplazado segun la direccion de entrada
- para `Retract Line + Up` ya esta volcada la regla observada en Maestro: una sola subida oblicua hacia un punto final desplazado segun la direccion de salida
- para `Arc + Quote` ya esta volcada la regla observada en Maestro para entradas/salidas en sentido horario y antihorario, incluyendo el toolpath vertical cuando la estrategia esta deshabilitada
- para `Retract Arc + Up` ya esta volcada la regla observada en Maestro: arco en plano vertical segun la direccion de salida, seguido de linea vertical, sin alterar `TrajectoryPath`
- esas reglas de entrada/salida ya quedaron unificadas sobre la tangente de entrada/salida del toolpath efectivo, no sobre una familia geometrica puntual
- caso manual validado: escuadrado exterior con `E001`, pasante + `Extra=1`, `Approach Arc + Quote x2` y `Retract Arc + Quote x2`; hoy ya queda expuesto por `SquaringMillingSpec`, con 4 orientaciones validas de `MidEdgeStart`, ambas combinaciones exteriores `CounterClockwise + Right` / `Clockwise + Left`, y `origin_x/y/z` limitado a `WorkpieceSetup/Placement`

Flujo recomendado de alto nivel:
- describir cada mecanizado con specs (`LineMillingSpec`, `PolylineMillingSpec`, `SquaringMillingSpec`, `DrillingSpec`)
- armar el request con `build_synthesis_request(...)`
- ejecutar `synthesize_request(...)`
- para una guia paso a paso con ejemplos completos, ver `docs/synthesize_pgmx_help.md`
