Guardar en esta carpeta los `.pgmx` manuales usados para ingeniería inversa.

Guia de uso del sintetizador: `docs/synthesize_pgmx_help.md`
Registro de familias geometricas: `docs/pgmx_geometry_registry.md`
Memoria activa de estrategia de fresado: `docs/pgmx_milling_strategy_temporary_memory.md`

## Proposito

Esta carpeta pasa a ser el espacio de trabajo para:

- casos manuales exportados y re-guardados desde Maestro
- comparaciones entre variantes de una misma geometria
- pruebas de profundidad, correccion, approach y retract
- cualquier `.pgmx` de estudio que no sea el baseline principal versionado

Estado esperado:

- la carpeta puede quedar vacia entre rondas de relevamiento
- dejar solo los casos manuales que estemos estudiando activamente
- cuando un lote de ejemplos ya no haga falta, se puede limpiar de nuevo y
  volver a poblarla con los siguientes casos

## Regla de organizacion

- `tools/maestro_baselines` queda reservado para el baseline base del repo:
  `Pieza.xml`, `Pieza.epl` y `def.tlgx`
- `archive/maestro_examples` concentra el resto de la ingeniería inversa

## Uso recomendado

- Guardar acá cada variante manual con nombres descriptivos.
- Si una regla ya quedó validada y documentada, mantener el archivo como referencia.
- Cuando una síntesis necesite hidratar serialización desde un caso manual, usar estos `.pgmx` como `source_pgmx_path`.
- No usar esta carpeta como baseline por defecto del sintetizador; para eso
  ahora existe `tools/maestro_baselines`.
