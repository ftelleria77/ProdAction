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
- Flujo unico de generacion `.pgmx`: `python -m tools.synthesize_pgmx`
- Guia completa del sintetizador: `docs/synthesize_pgmx_help.md`
- Registro de familias geometricas: `docs/pgmx_geometry_registry.md`
- Nota historica del flujo anterior: `docs/en_juego_pgmx_export.md`
- Baselines manuales de Maestro: `archive/maestro_baselines/`
- API programática para sintesis: `build_approach_spec(...)`, `build_retract_spec(...)`, `build_milling_depth_spec(...)`, `build_line_milling_spec(...)`, `build_polyline_milling_spec(...)`, `build_synthesis_request(...)` y `synthesize_request(...)` en `tools.synthesize_pgmx`
- API programatica para inspeccion/construccion geometrica: `read_pgmx_geometries(...)`, `build_line_geometry_profile(...)`, `build_circle_geometry_profile(...)`, `build_composite_geometry_profile(...)` y `build_compensated_toolpath_profile(...)`
- La sintesis de `.pgmx` permite fijar el area de `Parametros de Maquina` mediante `execution_fields` en la API o `--execution-fields/--area` en la CLI; si no se indica, usa `HG` por defecto.
Estado validado hasta ahora en `tools.synthesize_pgmx`:
- fresados lineales y polilineas abiertas
- lectura y clasificacion de geometria base: lineas, circulos y curvas compuestas abiertas/cerradas
- compensacion geometrica reusable para lineas, arcos, circulos y curvas compuestas abiertas/cerradas
- la sintesis publica completa de mecanizado sigue expuesta hoy via `LineMillingSpec` y `PolylineMillingSpec`
- `SideOfFeature` `Center|Right|Left`
- fresados pasantes y no pasantes, con `Extra`/`OvercutLength`
- en pasante, `Depth.StartDepth/EndDepth` queda ligado al `DepthName` real de la pieza y `Extra` desplaza `cut_z`
- `Approach` y `Retract` con `Line` y `Arc`
- para `Approach Line + Down` ya esta volcada la regla observada en Maestro: una sola bajada oblicua desde un punto previo desplazado segun la direccion de entrada
- para `Retract Line + Up` ya esta volcada la regla observada en Maestro: una sola subida oblicua hacia un punto final desplazado segun la direccion de salida
- para `Arc + Quote` ya esta volcada la regla observada en Maestro para entradas/salidas en sentido horario y antihorario, incluyendo el toolpath vertical cuando la estrategia esta deshabilitada
- para `Retract Arc + Up` ya esta volcada la regla observada en Maestro: arco en plano vertical segun la direccion de salida, seguido de linea vertical, sin alterar `TrajectoryPath`
