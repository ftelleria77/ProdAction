# PGMX Machine Operations Lab

Espacio de investigacion para entender y validar operaciones de maquina y flujo
de programa Maestro dentro de `.pgmx`.

Este laboratorio vive en `pgmx/machining_lab/machine_operations/`. No es codigo
productivo: sirve para registrar evidencia, generar inspectores y derivar reglas
antes de promover cambios a `pgmx.snapshot`, `pgmx.processing` y
`pgmx.synthesis`.

## Alcance

- multiples `MainWorkplan` como fases operativas de programa;
- `Setup/WorkpieceSetup/Placement` por fase;
- operacion nula `Xn` para posicionar el cabezal y liberar acceso fisico a la
  pieza;
- mensaje/parada `Xmsg` para indicar acciones al operario y esperar
  confirmacion;
- orden real de `Executable` dentro de cada fase;
- compatibilidad con nombres libres de fase definidos por Maestro o por el
  usuario.

## Carpeta Externa

Los ejemplos manuales y automaticos se trabajan fuera del repo en:

```text
S:\Maestro\Projects\ProdAction\PGMX\machine_operations
```

Estructura esperada:

- `manual/`: ejemplos creados manualmente en Maestro.
- `generated/`: ejemplos sintetizados por ProdAction.
- `_analysis/`: reportes producidos por herramientas del laboratorio.

## Primer Inspector

```powershell
py -3 -m pgmx.machining_lab.machine_operations.scan_samples
```

Con rutas explicitas:

```powershell
py -3 -m pgmx.machining_lab.machine_operations.scan_samples `
  --root 'S:\Maestro\Projects\ProdAction\PGMX\machine_operations' `
  --output 'S:\Maestro\Projects\ProdAction\PGMX\machine_operations\_analysis\program_flow.csv'
```

## Criterio De Integracion

Cuando una regla quede validada:

- lectura y reconocimiento: `pgmx.snapshot`;
- dibujo 2D de la primera fase util: `pgmx.processing`;
- sintesis multifase y operaciones de maquina: `pgmx.synthesis.common.program`;
- documentacion publica: `docs/pgmx_snapshot_help.md` y
  `docs/synthesize_pgmx_help.md`.
