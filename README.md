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

## Exportación PGMX En Juego
- Flujo estable actual, todavía aislado del flujo principal.
- Script: `python -m tools.export_pgmx`
- Documentación: `docs/en_juego_pgmx_export.md`
- Baselines manuales de Maestro: `archive/maestro_baselines/`
- Soporta `--template-pgmx` para usar un baseline local del repo como plantilla de salida.
- Sintesis de baselines manuales: `python -m tools.synthesize_pgmx`
- API programática para sintesis: `build_approach_spec(...)`, `build_retract_spec(...)`, `build_milling_depth_spec(...)`, `build_line_milling_spec(...)`, `build_polyline_milling_spec(...)`, `build_synthesis_request(...)` y `synthesize_request(...)` en `tools.synthesize_pgmx`
- La sintesis de `.pgmx` tambien permite fijar el area de `Parametros de Maquina` mediante `execution_fields` en la API o `--execution-fields/--area` en la CLI.
