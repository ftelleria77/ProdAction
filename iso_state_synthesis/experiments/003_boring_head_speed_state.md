# Experimento 003 - Estado De Velocidad Del Cabezal Perforador

Fecha: 2026-05-06

## Proposito

Verificar si `?%ETK[17]=257` esta relacionado con el cambio de velocidad de
rotacion del cabezal perforador y no con una herramienta puntual.

## Fuentes Revisadas

- `iso_state_synthesis/machine_config/snapshot/maestro/Tlgx/def.tlgx`
- `iso_state_synthesis/machine_config/snapshot/xilog_plus/Job/def.tlg`
- `P:\USBMIX\ProdAction\ISO\pieza_001.iso`
- `P:\USBMIX\ProdAction\ISO\pieza_001_r.iso`
- `P:\USBMIX\ProdAction\ISO\pieza_006.iso`
- `P:\USBMIX\ProdAction\ISO\minimal_fixtures_2026-05-03\iso_min_010_leftdrill_base.iso`
- `P:\USBMIX\ProdAction\ISO\minimal_fixtures_2026-05-03\iso_min_011_rightdrill_base.iso`
- `P:\USBMIX\ProdAction\ISO\minimal_fixtures_2026-05-03\iso_min_012_frontdrill_base.iso`
- `P:\USBMIX\ProdAction\ISO\minimal_fixtures_2026-05-03\iso_min_013_backdrill_base.iso`

## Velocidades En `def.tlgx`

La velocidad se reviso tanto en la herramienta (`CoreTool/ToolTechnology`) como
en el spindle del agregado `BooringUnitHead`
(`SpindleComponent/SpindleTechnology`). Para estas herramientas coinciden.

| Herramienta | Spindle | Tipo | Diametro | Min | Standard | Max |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| `001` | 1 | broca vertical | 8 | 6000 | 6000 | 6000 |
| `002` | 2 | broca vertical | 15 | 4000 | 4000 | 4000 |
| `003` | 3 | broca vertical | 20 | 4000 | 4000 | 4000 |
| `004` | 4 | broca vertical | 35 | 4000 | 4000 | 4000 |
| `005` | 5 | broca vertical | 5 | 6000 | 6000 | 6000 |
| `006` | 6 | broca vertical | 4 | 6000 | 6000 | 6000 |
| `007` | 7 | broca vertical | 5 | 6000 | 6000 | 6000 |
| `058` | 58 | broca horizontal | 8 | 6000 | 6000 | 6000 |
| `059` | 59 | broca horizontal | 8 | 6000 | 6000 | 6000 |
| `060` | 60 | broca horizontal | 8 | 6000 | 6000 | 6000 |
| `061` | 61 | broca horizontal | 8 | 6000 | 6000 | 6000 |
| `082` | 82 | sierra vertical | 120 | 4000 | 4000 | 6000 |

Lectura: `082` tiene velocidad standard `4000` y maximo `6000`. La salida ISO
observada usa `S4000M3`.

## Evidencia ISO

En los fixtures minimos Top Drill (`001` a `006`) la herramienta usada es `005`,
por eso aparece:

```iso
?%ETK[17]=257
S6000M3
```

Los fixtures laterales `010` a `013` usan brocas horizontales del cabezal
perforador y tambien emiten `?%ETK[17]=257` seguido por `S6000M3`.

En `pieza_006.iso`, la sierra vertical `082` emite:

```iso
?%ETK[6]=82
...
?%ETK[17]=257
S4000M3
?%ETK[1]=16
```

En `pieza_001.iso` aparecen las brocas verticales `001` a `007` en secuencia:

- antes de la primera herramienta a `6000`, Maestro emite
  `?%ETK[17]=257` y `S6000M3`;
- al pasar de herramienta `001` a `002`, cambia la velocidad a `4000`, y
  Maestro emite `?%ETK[17]=257` y `S4000M3`;
- en las herramientas `003` y `004`, que siguen a `4000`, Maestro no repite
  `?%ETK[17]=257` ni `S4000M3`;
- al pasar a herramienta `005`, cambia de nuevo a `6000`, y Maestro emite
  `?%ETK[17]=257` y `S6000M3`;
- en `006` y `007`, que siguen a `6000`, Maestro no repite el cambio de
  velocidad.

En `pieza_001_r.iso`, que reordena los mismos taladros para alternar
repetidamente velocidades, Maestro emite `?%ETK[17]=257` en cada cambio de
velocidad:

| Herramienta | RPM objetivo | RPM activa previa | Emite `?%ETK[17]=257` | Emite velocidad |
| --- | ---: | ---: | --- | --- |
| `001` | 6000 | - | si, linea 43 | `S6000M3`, linea 44 |
| `002` | 4000 | 6000 | si, linea 65 | `S4000M3`, linea 66 |
| `005` | 6000 | 4000 | si, linea 86 | `S6000M3`, linea 87 |
| `003` | 4000 | 6000 | si, linea 107 | `S4000M3`, linea 108 |
| `006` | 6000 | 4000 | si, linea 128 | `S6000M3`, linea 129 |
| `004` | 4000 | 6000 | si, linea 149 | `S4000M3`, linea 150 |
| `007` | 6000 | 4000 | si, linea 170 | `S6000M3`, linea 171 |

Esta variante es mas fuerte que `pieza_001.iso` porque no deja dos herramientas
consecutivas con la misma velocidad, salvo el primer arranque desde estado
desconocido. Por lo tanto, cada herramienta requiere una nueva activacion de
velocidad del cabezal.

Conteo rapido sobre `P:\USBMIX\ProdAction\ISO`: cada vez que aparece
`?%ETK[17]=257`, la siguiente linea de spindle encontrada fue:

| Siguiente linea | Cantidad |
| --- | ---: |
| `S4000M3` | 89 |
| `S6000M3` | 160 |

## Conclusion Provisional

`?%ETK[17]=257` no codifica una velocidad fija. Es una activacion/preparacion
del estado de rotacion del cabezal perforador antes de emitir una nueva
velocidad `S...M3`.

Regla candidata:

- Si una etapa del `BooringUnitHead` requiere una velocidad distinta de la
  velocidad activa del cabezal, emitir `?%ETK[17]=257` y luego `S{rpm}M3`.
- Si la siguiente herramienta del mismo cabezal conserva la misma velocidad,
  no repetir `?%ETK[17]=257` ni `S{rpm}M3`.
- Al resetear la familia, Maestro emite `?%ETK[17]=0`.

## Implementacion En El Diferencial

La regla quedo volcada al codigo el 2026-05-06:

- `pgmx_source.py` incorpora `maquina.boring_head_speed` cuando la herramienta
  viene del `BooringUnitHead`.
- `differential.py` compara `maquina.boring_head_speed` contra la velocidad
  activa y agrega `salida.etk_17 = 257` solo cuando la velocidad cambia.
- `emitter.py` emite `?%ETK[17]=257` y `S...M3` desde ese diferencial de
  velocidad, no como constante obligatoria de cada herramienta.

Validacion:

| Pieza | Orden de herramientas | Activaciones calculadas |
| --- | --- | ---: |
| `Pieza_001.pgmx` | `001,002,003,004,005,006,007` | 3 |
| `Pieza_001_R.pgmx` | `001,002,005,003,006,004,007` | 7 |

Lectura: `Pieza_001_R` obliga un cambio de velocidad en cada trabajo y el
diferencial genera una activacion para cada uno. `Pieza_001` conserva velocidad
en `002 -> 003 -> 004` y `005 -> 006 -> 007`, por eso no repite la activacion
en esos pasos.
