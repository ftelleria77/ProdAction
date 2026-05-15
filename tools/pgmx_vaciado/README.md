# PGMX Vaciado

Espacio de investigacion para entender un nuevo tipo de mecanizados `.pgmx`
que vamos a nombrar como `Vaciado`.

Este directorio vive dentro de `tools/` porque el estudio depende del nucleo de
lectura y sintesis PGMX. No es codigo productivo: sirve para registrar memoria,
generar evidencia y probar estrategias antes de volcar cambios en los modulos
estables del repo.

## Carpeta Externa

Los ejemplos manuales y automaticos se trabajan fuera del repo en:

```text
S:\Maestro\Projects\ProdAction\PGMX
```

Estructura esperada:

- `manual/`: ejemplos creados o ajustados manualmente en Maestro.
- `generated/`: ejemplos generados por scripts tentativos.
- `_analysis/`: reportes CSV/Markdown producidos por las herramientas de este
  laboratorio.

## Memoria

Punto de entrada:

- `memory/current-state.md`

## Codigo Tentativo

Primer inspector:

```powershell
py -3 -m tools.pgmx_vaciado.scan_samples
```

Con rutas explicitas:

```powershell
py -3 -m tools.pgmx_vaciado.scan_samples `
  --root 'S:\Maestro\Projects\ProdAction\PGMX' `
  --output-dir 'S:\Maestro\Projects\ProdAction\PGMX\_analysis'
```

El inspector cataloga features, operaciones, geometrias, toolpaths,
profundidades y estrategias. No intenta resolver todavia como sintetizar ni
postprocesar `Vaciado`.

## Criterio De Integracion

Cuando una regla sobreviva a ejemplos manuales y automaticos, se migra fuera de
este laboratorio hacia los modulos correspondientes:

- lectura: `tools/pgmx_snapshot.py`;
- adaptacion: `tools/pgmx_adapters.py`;
- sintesis PGMX: `tools/synthesize_pgmx.py`;
- dibujo/visualizacion: `core/pgmx_processing.py`;
- ISO: `iso_state_synthesis/`.
