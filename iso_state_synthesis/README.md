# ISO State Synthesis

Entorno nuevo para investigar y disenar la generacion ISO por estado,
parametros y diferenciales.

En la rama `iso-state-synthesis`, este paquete reemplaza al laboratorio
historico `iso_generation/`, que fue retirado del arbol de trabajo para evitar
mantener dos enfoques paralelos en la misma rama.

Punto de entrada de memoria:

- `memory/current-state.md`

Material de trabajo:

- `experiments/`
- `contracts/`
- `machine_config/`

## Primer esqueleto ejecutable

El paquete `iso_state_synthesis` contiene la estructura interna inicial del
sintetizador por estado:

- `model.py`: dataclasses de fuentes, valores de estado, etapas, trazas y plan.
- `pgmx_source.py`: adaptador desde `tools.pgmx_snapshot` hacia un plan de
  estados.
- `differential.py`: calculo de cambios entre estado activo, estado objetivo y
  resets.
- `emitter.py`: emisor candidato explicativo para el subset soportado, con
  fuente por linea.
- `cli.py`: inspeccion del plan interno desde linea de comandos.

Uso inicial:

```powershell
py -3 -m iso_state_synthesis inspect-pgmx `
  S:\Maestro\Projects\ProdAction\ISO\minimal_fixtures_2026-05-03\ISO_MIN_001_TopDrill_Base.pgmx
```

Salida JSON:

```powershell
py -3 -m iso_state_synthesis inspect-pgmx <archivo.pgmx> --json
```

Evaluar diferenciales de estado:

```powershell
py -3 -m iso_state_synthesis evaluate-pgmx <archivo.pgmx>
```

Emitir el primer ISO candidato explicado:

```powershell
py -3 -m iso_state_synthesis emit-candidate <archivo.pgmx> --output tmp\candidato.iso
```

La salida JSON de `emit-candidate --json` conserva, para cada linea, la fuente,
la confianza y `rule_status`. Ese campo separa reglas ya generalizadas en el
fixture Top Drill `001` a `006` de constantes de maquina/campo e hipotesis
pendientes.

Compararlo contra Maestro:

```powershell
py -3 -m iso_state_synthesis compare-candidate <archivo.pgmx> <maestro.iso>
```

Esta estructura todavia no emite ISO final. Por ahora materializa evidencia,
fuentes, estado objetivo, traza y resets candidatos para poder validar el modelo
antes de escribir el emisor.

Estado actual del emisor candidato:

- Soporta las seis variantes Top Drill del fixture minimo
  `ISO_MIN_001` a `ISO_MIN_006`.
- Produce 84 lineas normalizadas por variante y compara igual contra los ISO
  Maestro correspondientes.
- Clasifica cada linea emitida con `rule_status`, sin cambiar el texto ISO
  candidato.
- El diferencial ya modela la velocidad activa del `BooringUnitHead` como
  `maquina.boring_head_speed` y genera `?%ETK[17]=257` solo cuando esa velocidad
  cambia entre trabajos.
- Sigue siendo un emisor explicativo acotado, no un traductor ISO general.
