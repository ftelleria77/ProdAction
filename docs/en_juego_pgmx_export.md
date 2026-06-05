# Nota Histórica: Flujo `export_pgmx`

El flujo anterior basado en `tools/export_pgmx.py` fue retirado del repo.

Desde ahora, toda la generación de archivos `.pgmx` debe resolverse únicamente
desde:

- `pgmx.synthesis`

La referencia operativa vigente es:

- `docs/synthesize_pgmx_help.md`

## Motivo

Se unificó la generación en un único módulo para evitar:
- reglas duplicadas de serialización
- diferencias de comportamiento entre exportar y sintetizar
- pérdidas de contexto sobre qué API pública debía usarse

## Regla actual

Si hace falta agregar o corregir una familia de mecanizado:
- se implementa en `pgmx.synthesis`
- se documenta en `docs/synthesize_pgmx_help.md`
- se refleja en los README que apuntan a esa guía
