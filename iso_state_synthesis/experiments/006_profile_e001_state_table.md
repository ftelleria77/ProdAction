# Profile E001 State Table

## Alcance

Registro del 2026-05-07 para la ampliacion del emisor candidato al fresado de
perfil `E001` sobre plano `Top`, usando el corpus historico `Pieza*` de:

- `S:\Maestro\Projects\ProdAction\ISO`
- `P:\USBMIX\ProdAction\ISO`

El soporte agregado queda acotado a perfiles cerrados `ClosedPolylineMidEdgeStart`
con herramienta `E001`. Cubre acercamiento/alejamiento `Arc`, `Line`,
deshabilitados, y estrategias PH5 unidireccional/bidireccional observadas en el
corpus.

## Preparacion Router

`E001` usa el mismo bloque base de router que `E004`, cambiando los valores de
herramienta:

| Estado | Valor | ISO |
| --- | ---: | --- |
| Herramienta | `T1` | `T1` |
| Router tool code | `1` | `?%ETK[9]=1` |
| Activacion router | `1` | `?%ETK[18]=1` |
| Velocidad | `18000` | `S18000M3` |
| Largo | `125.400` | `SVL 125.400`, `VL6=125.400` |
| Radio | `9.180` | `SVR 9.180`, `VL7=9.180` |

En el marco inicial de pieza para `E001` estandar, Maestro emite un reset modal
adicional antes del tercer `?%ETK[8]=1`:

```iso
?%ETK[8]=1
G40
?%ETK[8]=1
G40
?%ETK[7]=0
?%ETK[8]=1
G40
```

## Traza De Perfil

Para el perfil rectangular antihorario con `SideOfFeature=Right`, Maestro usa
compensacion `G42` y emite el contorno nominal. Los offsets de entrada/salida se
calculan con `radio = tool_width / 2`.

Para `Approach=Arc/Quote`, la entrada baja primero en Z y despues hace el arco:

```iso
G1 X181.640 Y-18.360 Z20.000 F2000.000
G1 Z-19.000 F2000.000
G2 X200.000 Y0.000 I200.000 J-18.360 F2000.000
```

Para `Approach=Arc/Down`, la bajada se integra en el arco:

```iso
G1 X181.640 Y-18.360 Z20.000 F2000.000
G2 X200.000 Y0.000 Z-19.000 I200.000 J-18.360 F2000.000
```

La salida replica la misma diferencia: `Retract=Quote` separa arco y subida; en
`Retract=Up` la subida se integra en el arco de salida.

## Secuencia E001 A E004

Cuando un `E001` es seguido por un `E004`, Maestro no cierra el programa entre
ambos trabajos. Emite un bloque intermedio de router, cambia herramienta y luego
prepara `E004` de forma incremental:

- no repite `?%ETK[6]=1`;
- no reemite `%Or[0]` ni `SHF[X/Y/Z]` del router;
- conserva `T4`, `?%ETK[9]=4`, `?%ETK[18]=1`, `S18000M3`, `G17`, `MLV=2` y
  `?%ETK[13]=1`.

Para `E004` con acercamiento/alejamiento lineal habilitado, el emisor toma los
toolpaths `Approach`, `TrajectoryPath` y `Lift`. Si `SideOfFeature` es `Right`
o `Left` y no hay estrategia PH5, Maestro usa coordenada nominal con
compensacion `G42` o `G41`. Si hay estrategia PH5, conserva el toolpath offset y
no emite `G41/G42`.

## Variantes De Entrada Y PH5

Reglas agregadas despues de la primera validacion:

- `SideOfFeature=Right` emite `G42`; `SideOfFeature=Left` emite `G41`.
- Sin acercamiento/alejamiento, Maestro entra y sale con una linea corta de
  `overcut_length` sobre X y no usa arco ni linea lateral.
- Con `Line/Quote`, baja primero en Z y despues entra linealmente a la cota de
  corte.
- Con `Line/Down`, integra la bajada en la linea de entrada; `Line/Up` integra
  la subida en la linea de salida.
- Con PH5, Maestro no usa `G41/G42`; emite directamente los toolpaths
  `Approach`, `TrajectoryPath` y `Lift`, reconstruyendo los arcos de esquina
  desde los puntos offset del toolpath.
- En PH5, el marco inicial no incluye el reset extra `?%ETK[7]=0` que si aparece
  en las variantes E001 sin estrategia.

## Validacion

| Variante | Resultado |
| --- | --- |
| `Pieza_018` | `103 vs 103 lineas`, `0 diferencias` |
| `Pieza_019` | `103 vs 103 lineas`, `0 diferencias` |
| `Pieza_020` | `105 vs 105 lineas`, `0 diferencias` |
| `Pieza_021` | `105 vs 105 lineas`, `0 diferencias` |
| `Pieza_059` | `136 vs 136 lineas`, `0 diferencias` |
| `Pieza_060` | `136 vs 136 lineas`, `0 diferencias` |
| `Pieza_061` | `136 vs 136 lineas`, `0 diferencias` |
| `Pieza_062` | `136 vs 136 lineas`, `0 diferencias` |
| `Pieza_063` | `143 vs 143 lineas`, `0 diferencias` |
| `Pieza_064` | `147 vs 147 lineas`, `0 diferencias` |
| `Pieza_065` | `147 vs 147 lineas`, `0 diferencias` |
| `Pieza_066` | `156 vs 156 lineas`, `0 diferencias` |
| `Pieza_067` | `156 vs 156 lineas`, `0 diferencias` |
| `Pieza_068` | `156 vs 156 lineas`, `0 diferencias` |
| `Pieza_069` | `150 vs 150 lineas`, `0 diferencias` |
| `Pieza_070` | `150 vs 150 lineas`, `0 diferencias` |
| `Pieza_071` | `150 vs 150 lineas`, `0 diferencias` |
| `Pieza_084` | `105 vs 105 lineas`, `0 diferencias` |
| `Pieza_085` | `103 vs 103 lineas`, `0 diferencias` |
| `Pieza_086` | `103 vs 103 lineas`, `0 diferencias` |

Barrido completo posterior del corpus `Pieza*`: `34` pares exactos, `71` sin
candidato, `0` candidatos distintos.
