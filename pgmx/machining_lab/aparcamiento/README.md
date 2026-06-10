# PGMX Aparcamiento Lab

Espacio de investigacion para entender y validar la operacion de maquina
`Aparcamiento` dentro de `.pgmx`.

Este laboratorio vive en `pgmx/machining_lab/aparcamiento/`. No es codigo
productivo: sirve para registrar evidencia, generar inspectores y derivar reglas
antes de promover cambios a `pgmx.snapshot`, `pgmx.processing` y
`pgmx.synthesis`.

## Alcance

- estructura XML interna del `Executable i:type="Aparcamiento"`;
- campos propios y su semántica operativa en Maestro;
- posicion dentro de fases y relacion con otros `Executable`.

## Carpeta Externa

Los ejemplos manuales y automaticos se trabajan fuera del repo en:

```text
S:\Maestro\Projects\ProdAction\PGMX\aparcamiento
```

Estructura esperada:

- `manual/`: ejemplos creados manualmente en Maestro.
- `generated/`: ejemplos sintetizados por ProdAction.
- `_analysis/`: reportes producidos por herramientas del laboratorio.

## Inspector De Descubrimiento

```powershell
py -3.14 -m pgmx.machining_lab.aparcamiento.scan_samples
```

Con rutas explicitas:

```powershell
py -3.14 -m pgmx.machining_lab.aparcamiento.scan_samples `
  --root 'S:\Maestro\Projects\ProdAction\PGMX\aparcamiento' `
  --output 'S:\Maestro\Projects\ProdAction\PGMX\aparcamiento\_analysis\aparcamiento_fields.csv'
```

El inspector vuelca columnas fijas de contexto (workplan, fase, step) mas
columnas dinamicas `child_<tag>` para cada nodo hijo encontrado en los
`Executable i:type="Aparcamiento"`. Esto permite descubrir el esquema XML sin
conocerlo de antemano.

## Criterio De Integracion

Cuando una regla quede validada:

- lectura y reconocimiento: `pgmx.snapshot`;
- sintesis: `pgmx.synthesis.common.program`;
- documentacion publica: `docs/pgmx_snapshot_help.md` y
  `docs/synthesize_pgmx_help.md`.
