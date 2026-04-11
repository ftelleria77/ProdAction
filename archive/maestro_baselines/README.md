Guardar en esta carpeta los `.pgmx` base exportados y guardados manualmente desde Maestro.

Uso recomendado:
- Partir de un archivo sin mecanizados o de una variante minima y guardarla aca.
- Hacer las modificaciones manuales en Maestro sobre copias dentro de esta misma carpeta.
- Comparar siempre contra un baseline fresco del repo, sin usar archivos temporales en `S:/Maestro/...`.

Convencion sugerida de nombres:
- `baseline_sin_mecanizados.pgmx`
- `baseline_<experimento>.pgmx`
- `Pieza_sintetizada.pgmx`

Para sintetizar un archivo de prueba desde el baseline usando hallazgos ya guardados en `Pieza.pgmx`:

```powershell
cd C:\Users\fermi\Proyectos\my-python-api
python -m tools.synthesize_pgmx \
	--baseline "archive/maestro_baselines/baseline_sin_mecanizados.pgmx" \
	--source-pgmx "archive/maestro_baselines/Pieza.pgmx" \
	--piece-name "Pieza" \
	--execution-fields A \
	--output "archive/maestro_baselines/Pieza_sintetizada.pgmx"
```

Para sintetizar explicitamente la pieza actual con una linea en `Top` y un fresado asociado:

```powershell
cd C:\Users\fermi\Proyectos\my-python-api
python -m tools.synthesize_pgmx \
	--baseline "archive/maestro_baselines/baseline_sin_mecanizados.pgmx" \
	--source-pgmx "archive/maestro_baselines/Pieza.pgmx" \
	--piece-name "Pieza" \
	--length 400 \
	--width 400 \
	--depth 18 \
	--origin-x 5 \
	--origin-y 5 \
	--origin-z 25 \
	--line-x1 200 \
	--line-y1 0 \
	--line-x2 200 \
	--line-y2 400 \
	--line-feature-name "Fresado" \
	--line-tool-id 1902 \
	--line-tool-name E003 \
	--line-tool-width 9.52 \
	--output "archive/maestro_baselines/Pieza_sintetizada.pgmx"
```

Nota:
- Para piezas con mecanizados sintetizados, `--source-pgmx` permite hidratar los detalles de serializacion observados en Maestro para el feature/operation/toolpaths, aun cuando la pieza final se siga reconstruyendo sobre `baseline_sin_mecanizados.pgmx`.
- Para polilineas abiertas con fresado asociado, la API programatica de `tools.synthesize_pgmx` expone `build_polyline_milling_spec(...)` y ya sintetiza la compensacion lateral via `side_of_feature`; por ahora este caso no tiene flags CLI dedicados.
- En fresados lineales tambien se puede indicar la correccion de herramienta con `--line-side-of-feature Center|Right|Left`.
- En fresados lineales tambien se puede controlar la profundidad con `--line-through/--no-line-through`, `--line-extra-depth` y `--line-target-depth`.
- El parametro `Area` de `Parametros de Maquina` se controla con `--execution-fields` o su alias `--area`. Valores validados hasta ahora: `A`, `EF`, `HG`.
- Para habilitar el `Approach` con los defaults observados en Maestro (`Entrada=Lineal`, `Acercamiento=En Cota`, `Multipl. radio=2`, `Velocidad` vacia/null), alcanza con `--line-approach-enabled`.
- Si hace falta ajustar el detalle, tambien estan disponibles `--line-approach-mode`, `--line-approach-radius-multiplier`, `--line-approach-speed` y `--line-approach-arc-side`. Modos validados hasta ahora: `Quote` = `En Cota` y `Down` = `En bajada`.
- Para habilitar el `Retract` con los defaults observados en Maestro (`Salir=Lineal`, `Alejamiento=En Cota`, `Multipl. radio=2`, `Velocidad` vacia/null, `Sobreposicion=0`), alcanza con `--line-retract-enabled`.
- Si hace falta ajustar el detalle, tambien estan disponibles `--line-retract-mode`, `--line-retract-radius-multiplier`, `--line-retract-speed`, `--line-retract-arc-side` y `--line-retract-overlap`. Modos validados hasta ahora: `Quote` = `En Cota` y `Up` = `En subida`.
