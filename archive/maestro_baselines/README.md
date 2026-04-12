Guardar en esta carpeta los `.pgmx` base exportados y guardados manualmente desde Maestro.

Guia de uso de la API publica del sintetizador: `docs/synthesize_pgmx_help.md`

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
- El parametro `Area` de `Parametros de Maquina` se controla con `--execution-fields` o su alias `--area`. Si no se indica, la sintesis usa `HG` por defecto. Valores validados hasta ahora: `A`, `EF`, `HG`.
- Para habilitar el `Approach` con los defaults observados en Maestro (`Entrada=Lineal`, `Acercamiento=En Cota`, `Multipl. radio=2`, `Velocidad` vacia/null), alcanza con `--line-approach-enabled`.
- Si hace falta ajustar el detalle, tambien estan disponibles `--line-approach-type`, `--line-approach-mode`, `--line-approach-radius-multiplier`, `--line-approach-speed` y `--line-approach-arc-side`. Tipos validados hasta ahora: `Line` y `Arc`. Modos validados hasta ahora: `Quote` = `En Cota` y `Down` = `En bajada`. Para `Line` se validaron `Quote` y `Down`. Para `Arc` se valido `Quote`.
- Para habilitar el `Retract` con los defaults observados en Maestro (`Salir=Lineal`, `Alejamiento=En Cota`, `Multipl. radio=2`, `Velocidad` vacia/null, `Sobreposicion=0`), alcanza con `--line-retract-enabled`.
- Si hace falta ajustar el detalle, tambien estan disponibles `--line-retract-type`, `--line-retract-mode`, `--line-retract-radius-multiplier`, `--line-retract-speed`, `--line-retract-arc-side` y `--line-retract-overlap`. Tipos validados hasta ahora: `Line` y `Arc`. Modos validados hasta ahora: `Quote` = `En Cota` y `Up` = `En subida`. Para `Line` se validaron `Quote` y `Up`. Para `Arc` ya se validaron `Quote` y `Up`.

Hallazgos validados en Maestro al comparar escuadrados manuales:
- Si `Approach.IsEnabled=false`, Maestro conserva un toolpath vertical de `Approach` en la XY del punto de entrada.
- Si `Retract.IsEnabled=false`, Maestro conserva un toolpath vertical de `Lift` en la XY del punto de salida.
- Para `Arc + Quote`, el radio efectivo observado es `tool_width / 2 * (radius_multiplier - 1)`.
- Para `Line + Down`, la entrada observada es una sola recta oblicua desde `entry_point - direction * (tool_width / 2 * radius_multiplier)` hasta el punto de entrada del toolpath.
- Para `Line + Up`, la salida observada es una sola recta oblicua desde el punto de salida del toolpath hasta `exit_point + direction * (tool_width / 2 * radius_multiplier)`.
- En antihorario con `SideOfFeature=Right`:
- `Approach` usa `linea vertical + arco` con angulos `270° -> 360°`.
- `Lift` usa `arco + linea vertical` con angulos `0° -> 90°`.
- En horario con `SideOfFeature=Left`:
- `Approach` usa `linea vertical + arco` con angulos `90° -> 180°`.
- `Lift` usa `arco + linea vertical` con angulos `180° -> 270°`.
- En estos casos validados, `Approach`/`Lift` cambian sin alterar `TrajectoryPath`.

Resumen ordenado de la regla validada:
- Si `Approach.IsEnabled=false`, `Approach` queda como linea vertical en la XY de entrada.
- Si `Retract.IsEnabled=false`, `Lift` queda como linea vertical en la XY de salida.
- Para `Arc + Quote`, el radio efectivo observado es `tool_width / 2 * (radius_multiplier - 1)`.
- Para `Line + Down`, `Approach` usa una sola recta oblicua desde `entry_point - direction * (tool_width / 2 * radius_multiplier)` hasta `entry_point`.
- En antihorario con `SideOfFeature=Right`, `Line + Down` corre el punto inicial del `Approach` hacia la izquierda.
- En horario con `SideOfFeature=Left`, `Line + Down` corre el punto inicial del `Approach` hacia la derecha.
- Para `Line + Up`, `Lift` usa una sola recta oblicua desde `exit_point` hasta `exit_point + direction * (tool_width / 2 * radius_multiplier)`.
- En antihorario con `SideOfFeature=Right`, `Line + Up` corre el punto final del `Lift` hacia la derecha.
- En horario con `SideOfFeature=Left`, `Line + Up` corre el punto final del `Lift` hacia la izquierda.
- En antihorario con `SideOfFeature=Right`, `Approach` usa `linea vertical + arco` con angulos `270 -> 360`.
- En antihorario con `SideOfFeature=Right`, `Lift` usa `arco + linea vertical` con angulos `0 -> 90`.
- En horario con `SideOfFeature=Left`, `Approach` usa `linea vertical + arco` con angulos `90 -> 180`.
- En horario con `SideOfFeature=Left`, `Lift` usa `arco + linea vertical` con angulos `180 -> 270`.
- En estos casos validados, `Approach` y `Lift` cambian sin alterar `TrajectoryPath`.
- Para `Retract Arc + Up`, el radio efectivo sigue siendo `tool_width / 2 * (radius_multiplier - 1)`.
- Para `Retract Arc + Up`, el arco vive en el plano vertical definido por la direccion de salida y `Z`.
- En antihorario, `Retract Arc + Up` sale con arco `0 -> 90` y luego linea vertical.
- En horario, `Retract Arc + Up` sale con arco `180 -> 270` y luego linea vertical.
- Para `Retract Arc + Up`, el centro del arco queda en `exit_point + (0, 0, arc_radius)` y el final del arco en `exit_point + direction * arc_radius + (0, 0, arc_radius)`.
