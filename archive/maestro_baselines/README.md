Guardar en esta carpeta solo el baseline versionado y sus archivos asociados.

Guia de uso de la API publica del sintetizador: `docs/synthesize_pgmx_help.md`
Registro de familias geometricas relevadas en estos baselines: `docs/pgmx_geometry_registry.md`

## Baseline principal versionado

Desde ahora, el baseline base del repo ya no vive en `Pieza.pgmx`.
La fuente de verdad pasa a ser el baseline desempaquetado:

- `Pieza.xml`
- `Pieza.epl`
- `def.tlgx`

Ese conjunto es el que debe usarse para sintetizar nuevas piezas.
`tools.synthesize_pgmx` ya sabe cargarlo de tres maneras:

- pasando `archive/maestro_baselines/Pieza.xml`
- pasando la carpeta `archive/maestro_baselines`
- pasando un `.pgmx` historico, si hace falta compatibilidad

## Uso recomendado

- Partir siempre del baseline versionado (`Pieza.xml` + `Pieza.epl` + `def.tlgx`).
- Los estudios manuales y casos de ingeniería inversa ya no van acá: ahora viven en `archive/maestro_examples`.
- Comparar siempre contra un baseline fresco del repo, sin usar archivos temporales en `S:/Maestro/...`.
- Si ya existe un caso manual estudiado para la misma familia de mecanizado, usarlo como `--source-pgmx` o `source_pgmx_path` para hidratar serializacion observada en Maestro.

## Convencion sugerida de nombres

- `Pieza_<experimento>.pgmx`
- `Pieza_sintetizada.pgmx`

## Ejemplo CLI minimo

```powershell
cd C:\Users\fermi\OneDrive\Repoositorios\ProdAction
python -m tools.synthesize_pgmx \
    --baseline "archive/maestro_baselines/Pieza.xml" \
    --piece-name "Pieza" \
    --output "archive/maestro_examples/Pieza_sintetizada.pgmx"
```

## Ejemplo CLI con fresado lineal

```powershell
cd C:\Users\fermi\OneDrive\Repoositorios\ProdAction
python -m tools.synthesize_pgmx \
    --baseline "archive/maestro_baselines/Pieza.xml" \
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
    --output "archive/maestro_examples/Pieza_sintetizada.pgmx"
```

## Notas

- Para piezas con mecanizados sintetizados, `--source-pgmx` permite hidratar los detalles de serializacion observados en Maestro para el feature, la operation y los toolpaths.
- Para estudiar familias geometricas puras sin mecanizado, usar `read_pgmx_geometries(...)` sobre los `.pgmx` manuales de `archive/maestro_examples`.
- Para estudiar o reutilizar la correccion geometrica observada en Maestro, usar `build_compensated_toolpath_profile(...)`.
- Las reglas de `Approach` y `Retract` ya quedaron unificadas sobre el toolpath efectivo:
- `Approach` usa punto y tangente de entrada.
- `Retract` usa punto y tangente de salida.
- Por eso las reglas aprendidas en escuadrados ahora se reutilizan como regla general para cualquier geometria compensada.
- En fresados lineales se puede indicar la correccion de herramienta con `--line-side-of-feature Center|Right|Left`.
- En fresados lineales tambien se puede controlar la profundidad con `--line-through/--no-line-through`, `--line-extra-depth` y `--line-target-depth`.
- El parametro `Area` de `Parametros de Maquina` se controla con `--execution-fields` o `--area`. Si no se indica, la sintesis usa `HG` por defecto.
