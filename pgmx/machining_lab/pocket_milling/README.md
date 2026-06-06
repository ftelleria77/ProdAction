# PGMX Pocket Milling Lab

Espacio de investigacion para entender y validar mecanizados `.pgmx` de la
familia `ClosedPocket`/pocket milling.

Este laboratorio vive en `pgmx/machining_lab/pocket_milling/`. No es codigo
productivo: sirve
para registrar memoria, generar evidencia, comparar contra Maestro y probar
estrategias antes de volcar reglas cerradas en los modulos estables.

Este paquete reemplaza al laboratorio historico de Vaciado y funciona como
laboratorio general de pocket milling. Las rutas historicas `pgmx.vaciado_lab`
y `tools.pgmx_vaciado*` fueron retiradas; los comandos e imports del
laboratorio deben usar `pgmx.machining_lab.pocket_milling`.

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

## Codigo De Laboratorio

Primer inspector:

```powershell
py -3 -m pgmx.machining_lab.pocket_milling.scan_samples
```

Con rutas explicitas:

```powershell
py -3 -m pgmx.machining_lab.pocket_milling.scan_samples `
  --root 'S:\Maestro\Projects\ProdAction\PGMX' `
  --output-dir 'S:\Maestro\Projects\ProdAction\PGMX\_analysis'
```

El inspector cataloga features, operaciones, geometrias, toolpaths,
profundidades y estrategias. No intenta resolver todavia como sintetizar ni
postprocesar pocket milling arbitrario.

Analisis especifico de islas:

```powershell
py -3 -m pgmx.machining_lab.pocket_milling.island_analysis `
  --root 'S:\Maestro\Projects\ProdAction\PGMX' `
  --output-dir 'S:\Maestro\Projects\ProdAction\PGMX\_analysis\vaciado_islands_analysis'
```

Este reporte separa `BossGeometryList`, `BossList`, toolpaths y trayectorias
para `Vaciado_022` y `Vaciado_027..031`. Es descriptivo: la sintesis
productiva con islas sigue bloqueada hasta derivar la regla de offsets y
puentes internos.

## Criterio De Integracion

Cuando una regla sobreviva a ejemplos manuales y automaticos, se migra fuera de
este laboratorio hacia los modulos correspondientes:

- lectura: `pgmx.snapshot`;
- adaptacion: `pgmx.adapters`;
- sintesis PGMX: `pgmx.synthesis` y, para `ClosedPocket`/Vaciado,
  `pgmx.synthesis.milling.pocket`;
- contrato promovido de pocket milling:
  `pgmx.synthesis.milling.pocket_contract`;
- dibujo/visualizacion: `pgmx.processing`;
- ISO: `iso_state_synthesis/`.

Las fachadas PGMX bajo `tools/` fueron retiradas. Usar `pgmx.snapshot`,
`pgmx.adapters`, `pgmx.synthesis` y sus entradas `python -m pgmx.*`.
