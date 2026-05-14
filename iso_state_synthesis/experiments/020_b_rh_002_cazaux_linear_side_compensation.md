# B-RH-002 Router Lineal Compensado - Cazaux

Fecha: 2026-05-14

## Objetivo

Cerrar el residual `B-RH-002` reaparecido en
`Cocina\mod 6 - Torre horno\Divisor_Horiz.pgmx`.

El primer delta era:

```text
linea 322: Maestro='G0 X5.000 Y601.720' / candidato='G0 X5.000 Y600.720'
```

Pero la diferencia completa estaba dentro de la traza `line_milling`:

```text
Maestro   G1 Y564.000 Z-13.000 F2000.000
Candidato G1 Z-13.000 F2000.000
Candidato G1 Y564.000 Z-13.000 F2000.000
```

El candidato tambien repetia el punto final nominal y no usaba el alejamiento
real de `Lift`.

## Lectura Del PGMX

El working step residual es `line_milling`:

| campo | valor |
| --- | --- |
| perfil | `LineVertical` |
| lado | `Right` |
| aproximacion | `Line Down`, multiplicador `4.0` |
| alejamiento | `Line Up`, multiplicador `4.0` |
| puntos nominales | `(5, 564) -> (5, 0)` |
| `Approach` | `(-4.18, 600.72, 38) -> (-4.18, 564, 5)` |
| `TrajectoryPath` | `(-4.18, 564, 5) -> (-4.18, 0, 5)` |
| `Lift` | `(-4.18, 0, 5) -> (-4.18, -36.72, 38)` |

Maestro programa la traza con el eje normal nominal (`X5.000`) y toma el eje
tangencial (`Y`) desde `Approach`/`Lift`.

## Regla Aplicada

Punto de codigo:

`iso_state_synthesis/emitter.py::_emit_line_milling_trace`

Para `LineHorizontal`/`LineVertical` con compensacion lateral, `approach_type =
Line`, `approach_mode = Down`, `retract_type = Line` y `retract_mode = Up`:

- conservar el eje normal nominal del perfil;
- tomar el eje tangencial de `Approach` y `Lift`;
- emitir el rapid un milimetro antes del primer punto de `Approach`;
- combinar desplazamiento tangencial y bajada Z en la entrada `Down`;
- cortar solo los puntos nominales, sin repetir el punto final;
- subir con el ultimo punto de `Lift`;
- emitir `G40` y un alejamiento final un milimetro despues del `Lift`.

El modo `Quote` queda fuera de la regla. Se probo incluirlo y generaba
regresiones en `Pieza_064.pgmx` y `Pieza_065.pgmx`.

## Evidencia

Control puntual:

```powershell
py -3 -m iso_state_synthesis.cli compare-candidate `
  'S:\Maestro\Projects\ProdAction\Prod 26-01-01 Cazaux\Cocina\mod 6 - Torre horno\Divisor_Horiz.pgmx' `
  'P:\USBMIX\ProdAction\Prod 26-01-01 Cazaux\Cocina\mod 6 - Torre horno\Divisor_Horiz.iso' `
  --candidate-output 'S:\Maestro\Projects\ProdAction\Prod 26-01-01 Cazaux\_analysis\candidate_Divisor_Horiz_mod6.iso'
```

Resultado:

```text
Resultado: igual (373 vs 373 lineas, 0 diferencias)
```

Validacion de corpus:

| corpus | resultado |
| --- | --- |
| `Prod 26-01-01 Cazaux` | `81` exactos, `22` `header_only`, `1` operativo |
| `ISO\Cocina` | `83` exactos, `1` operativo |
| raiz `ISO\Pieza*.pgmx` | `217` exactos, `5` operativos |

La unica frontera operativa restante en Cazaux es `T-XH-001`:

```text
Cocina\mod 6 - Torre horno\Lat_Der.pgmx line 540:
Maestro ?%ETK[17]=257 / candidato ?%ETK[0]=2147483648
```

Ese residual queda cerrado en
`iso_state_synthesis/experiments/021_txh001_cazaux_router_to_side_speed.md`.
