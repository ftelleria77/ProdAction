# T-XH-001 Router A Side Drill - Cazaux

Fecha: 2026-05-14

## Objetivo

Cerrar el ultimo residual operativo Cazaux:

```text
Cocina\mod 6 - Torre horno\Lat_Der.pgmx line 540:
Maestro ?%ETK[17]=257 / candidato ?%ETK[0]=2147483648
```

El caso no era `router -> top_drill`, sino `line_milling -> side_drill Left`.

## Diagnostico

Secuencia relevante del PGMX:

```text
profile_milling
top_drill...
line_milling
line_milling
top_drill...
line_milling
side_drill Left
side_drill Left
side_drill Left
side_drill Left
```

La preparacion lateral despues de router ya emitia:

```text
MLV=1
SHF[Z]=25.000+%ETK[114]/1000
MLV=2
G17
?%ETK[6]=61
MLV=2
SHF[X]=-118.000
SHF[Y]=-32.000
SHF[Z]=66.300
?%ETK[0]=2147483648
```

Maestro inserta antes de la mascara:

```text
?%ETK[17]=257
S6000M3
?%ETK[0]=2147483648
```

El diferencial no traia `salida.etk_17` porque ya existia velocidad del cabezal
perforador en el programa, igual que en la regla previa `router -> top_drill`.

## Regla Aplicada

Punto de codigo:

`iso_state_synthesis/emitter.py::_emit_side_drill_prepare_after_router`

Si la entrada lateral `T-XH-001` viene desde `line_milling` y el diferencial no
trae cambio explicito de `salida.etk_17`, el emisor fuerza:

```text
?%ETK[17]=257
S...M3
?%ETK[0]=...
```

La regla queda acotada a `router -> side_drill` desde `line_milling`, sin tocar
entradas laterales desde otras familias.

## Evidencia

Control puntual:

```powershell
py -3 -m iso_state_synthesis.cli compare-candidate `
  'S:\Maestro\Projects\ProdAction\Prod 26-01-01 Cazaux\Cocina\mod 6 - Torre horno\Lat_Der.pgmx' `
  'P:\USBMIX\ProdAction\Prod 26-01-01 Cazaux\Cocina\mod 6 - Torre horno\Lat_Der.iso' `
  --candidate-output 'S:\Maestro\Projects\ProdAction\Prod 26-01-01 Cazaux\_analysis\candidate_Lat_Der_mod6.iso'
```

Resultado:

```text
Resultado: igual (630 vs 630 lineas, 0 diferencias)
```

Auditoria dedicada `T-XH-001`:

```powershell
py -3 -m tools.studies.iso.txh001_transition_audit_2026_05_13 `
  --label after_side_drill `
  --baseline-csv 'S:\Maestro\Projects\ProdAction\Prod 26-01-01 Cazaux\_analysis\txh001_transition_audit_before.csv'
```

Resultado:

| clase | cantidad |
| --- | ---: |
| `exact` | `50` |
| `header_only` | `21` |
| diferencias `T-XH-001` | `0` |

Validacion de corpus:

| corpus | resultado |
| --- | --- |
| `Prod 26-01-01 Cazaux` | `82` exactos, `22` `header_only`, `0` operativos |
| `ISO\Cocina` | `84` exactos |
| raiz `ISO\Pieza*.pgmx` | `217` exactos, `5` operativos |

Con este cambio, Cazaux queda sin residuales operativos en la lista estudiada.
