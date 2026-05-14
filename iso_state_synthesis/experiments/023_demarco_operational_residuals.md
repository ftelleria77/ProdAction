# DeMarco Residuales Operativos

Fecha: 2026-05-14

Corpus:

- PGMX: `S:\Maestro\Projects\ProdAction\Prod 25-11-05 DeMarco`
- ISO: `P:\USBMIX\ProdAction\Prod 25-11-05 DeMarco`
- CSV base: `S:\Maestro\Projects\ProdAction\Prod 25-11-05 DeMarco\_analysis\block_transition_corpus_analysis.csv`
- Reporte enfocado: `S:\Maestro\Projects\ProdAction\Prod 25-11-05 DeMarco\_analysis\demarco_operational_diff_focus.md`

## Estado Base

Despues de la mejora hibrida de orden `B-BH-002`, DeMarco quedaba asi:

- `283` exactos
- `2` `header_only`
- `51` diferencias operativas
- `2` candidatos no soportados
- `46` sin ISO par

El frente mas grande era `stage:slot_milling_prepare` con `18` casos. Todos
eran secuencias:

```text
... slot_milling -> slot_milling ...
```

El candidato entraba al segundo slot con una preparacion completa:

```text
?%ETK[6]=82
G17
MLV=2
%Or[0].ofX=...
...
```

Maestro, en cambio, despues del reset parcial `B-BH-012`, emitia un puente
corto:

```text
?%ETK[8]=1
G40
G17
G0 X... Y... Z...
G0 X... Y... Z...
```

## Implementacion `T-BH-009`

Se agrego `T-BH-009 = top_slot -> top_slot` como transicion interna del cabezal
de perforacion/ranurado.

Regla aplicada:

- el catalogo selecciona `T-BH-009` cuando `previous_family` y `next_family`
  son `slot_milling`;
- el emisor no repite `B-BH-006` para el segundo slot;
- despues de `B-BH-012`, emite `?%ETK[8]=1`, `G40`, `G17`;
- la segunda traza arranca con dos rapidos `G0 X/Y/Z`: primero al rapid del
  slot anterior y luego al rapid del slot actual;
- luego continua con `D1`, `SVL/VL6`, `SVR/VL7`, bajada y corte normal de
  `B-BH-007`.

Caso representativo que quedo exacto:

```text
Cocina\mod 12,13,14 - bajo 3 cajones\Fondo.pgmx
```

Secuencia Maestro reproducida en el segundo slot:

```text
?%ETK[8]=1
G40
G17
G0 X991.550 Y568.100 Z80.000
G0 X991.550 Y565.100 Z80.000
D1
SVL 60.000
VL6=60.000
SVR 1.900
VL7=1.900
```

## Validacion Posterior

- DeMarco: `301` exactos, `2` `header_only`, `33` operativos, `2` no
  soportados, `46` sin ISO par.
- Cazaux: estable en `82` exactos y `22` `header_only`.
- `ISO/Cocina`: estable en `84/84`.
- Corpus raiz `Pieza*`: estable en `217/222`; los `5` residuales siguen siendo
  `Pieza_181..185` por la diferencia previa de `B-RH-002`.

Los `18` casos de `stage:slot_milling_prepare` quedaron cerrados.

## Distribucion De Los 33 Restantes

| frente | casos | lectura |
| --- | ---: | --- |
| `transition:T-XH-002` | `10` | `top_drill -> line_milling` hacia `OpenPolyline` `E001` con `side_of_feature` `Left/Right`; falta `?%ETK[8]=1`/`G40` antes de limpiar router |
| `block:B-BH-007` | `7` | salida de ranura antes de top drill; el candidato emite salida lateral completa, Maestro solo sube `G0 Z20.000` |
| `block:B-RH-002` | `6` | `LineHorizontal` `E004` en aplicados; Maestro arranca en `X-1.000`, candidato en `X0.000` |
| `block:B-BH-002` | `5` | diferencias de redondeo `X` de `0.003`; no parece orden ni herramienta |
| `transition:T-BH-003` | `4` | entre taladros laterales, Maestro reposiciona primero y el candidato antepone `G4F0.500` |
| `block:B-BH-005` | `1` | cota lateral de `Faja frontal`; Maestro `Y-80.000`, candidato `Y-200.000` |

## Proximo Orden Recomendado

1. `T-XH-002` lateral hacia `OpenPolyline` (`10` casos), con pruebas fuertes
   contra Cazaux para evitar reabrir lo ya cerrado. Hecho.
2. `B-BH-007` (`7` casos), probablemente ligado a la salida/entrada de ranura
   antes de top drill. Hecho; al despejar `T-XH-002`, el frente real subio a
   `11` y quedo cerrado.
3. `B-RH-002` (`6` casos), compensacion `-1 mm` en aplicados. Hecho.
4. `B-BH-002` (`5` casos), tratarlo como redondeo/formato, no como orden.
   Hecho como clasificacion `precision_only` del comparador.
5. `T-BH-003` (`4`) y `B-BH-005` (`1`) al final. Pendientes.

## Pasada Sobre Los 33

Despues de `T-BH-009`, los `33` operativos bajaron a `10`.

Reglas aplicadas:

- `T-XH-002`: cuando el retorno `top_drill -> line_milling` entra a un
  `OpenPolyline` lateral y el router previo tambien era `line_milling`
  `OpenPolyline` lateral con entrada `T-RH-001` o `T-XH-002`, Maestro emite
  `?%ETK[8]=1/G40` antes de limpiar `?%ETK[17]/M5/?%ETK[0]`.
- `B-BH-007`: en tandas `slot -> slot -> top_drill`, la salida completa del
  primer slot depende del top drill posterior a la tanda. Si la herramienta no
  es `001`, se omite la salida lateral completa y `T-BH-009` arranca desde el
  `cut_x` del slot anterior; si es `001`, se conserva la salida completa.
- `B-RH-002`: para `LineHorizontal/LineVertical` con compensacion lateral, sin
  leads y sin estrategia, se usa la regla de compensacion sin lead: rapid `1
  mm` antes, `G41/G42`, entrada a seguridad, bajada, corte, lift, `G40` y
  alejamiento `1 mm`.

Validacion posterior:

- DeMarco: `324` exactos, `2` `header_only`, `5` `precision_only`, `5`
  operativos, `2` no soportados, `46` sin ISO par.
- Cazaux: estable en `82` exactos y `22` `header_only`.
- `ISO/Cocina`: estable en `84/84`.
- Controles `Pieza_064` y `Pieza_065`: exactos.

## Clasificacion De Precision `B-BH-002`

Se agrego el estado `precision_only` al analisis de corpus. Aplica solo cuando
el archivo tiene la misma cantidad de lineas normalizadas, todas las diferencias
significativas son movimientos `G0/G1/G2/G3` equivalentes, los tokens no
numericos coinciden, y las coordenadas `X/Y/Z/I/J/K/R` difieren como maximo
`0.005 mm`.

No se cambio el emisor: los ISO candidatos siguen mostrando la coordenada
calculada. El cambio evita tratar como operativo un frente que por ahora es
ruido numerico de salida.

Casos separados:

| archivo | linea | Maestro | candidato |
| --- | ---: | --- | --- |
| `Lavadero\mod 1 - Torre\Lat_Izq.pgmx` | `180` | `G0 X1185.670 Y34.000 Z115.000` | `G0 X1185.667 Y34.000 Z115.000` |
| `Lavadero\mod 1 - Torre\Puerta_Izq.pgmx` | `207` | `G0 X1194.220 Y319.050 Z115.000` | `G0 X1194.217 Y319.050 Z115.000` |
| `Parrilla\mod 5 - Torre heladera\Lat_Der.pgmx` | `123` | `G0 X1228.670 Y616.000 Z115.000` | `G0 X1228.667 Y616.000 Z115.000` |
| `Parrilla\mod 5 - Torre heladera\Lat_Izq.pgmx` | `173` | `G0 X1344.330 Y616.000 Z115.000` | `G0 X1344.333 Y616.000 Z115.000` |
| `Parrilla\mod 5 - Torre heladera\Trasera.pgmx` | `123` | `G0 X1228.670 Y32.000 Z115.000` | `G0 X1228.667 Y32.000 Z115.000` |

## Pendientes Tras La Clasificacion

| frente | casos | estado |
| --- | ---: | --- |
| `transition:T-BH-003` | `4` | pausa lateral `G4F0.500` antes de repetir spindle; quitarla cierra DeMarco pero rompe Cazaux, por lo que falta una condicion mas fina |
| `block:B-BH-005` | `1` | orden/cota lateral intercalada entre dos bloques laterales separados por top drill; no conviene mezclarlo con la regla de `Left` angosto de Cazaux |

## Checkpoint De Cierre

Estado guardado para continuar:

- Cazaux queda cerrado en este corpus: `82` exactos y `22` `header_only`.
- `ISO/Cocina` queda cerrado: `84/84` exactos.
- DeMarco conserva `5` diferencias operativas reales: `4` de `T-BH-003` y
  `1` de `B-BH-005`.
- Los `5` `B-BH-002` no bloquean la estrategia de bloques: estan separados
  como `precision_only` y solo deberian reabrirse si se busca ISO byte-exacto.

Plan restante recomendado:

1. `T-BH-003`: armar una auditoria enfocada de pausas laterales. Comparar los
   `4` DeMarco donde Maestro reposiciona sin `G4F0.500` contra los Cazaux que
   si necesitan pausa. La regla candidata no debe ser "quitar pausa en
   side->side", sino condicionar la pausa por contexto de entrada/salida del
   bloque lateral, repeticion de spindle, cara y trabajo vecino.
2. Validar cualquier cambio de `T-BH-003` contra DeMarco, Cazaux, `ISO/Cocina`
   y controles `Pieza*`, porque ya hay evidencia de regresion si se quita la
   pausa globalmente.
3. `B-BH-005`: estudiar el caso unico
   `Cocina\Parte 2\mod 1 - Torre heladera\Faja frontal.pgmx` como problema de
   cota/orden lateral intercalado entre bloques separados por top drill. No
   mezclarlo con la regla Cazaux de `Left` angosto salvo que la evidencia
   confirme el mismo patron.
4. Precision numerica: mantenerla como clasificacion de reporte. Investigar la
   cuantizacion exacta de Maestro solo si el objetivo pasa de equivalencia
   operativa a igualdad byte-a-byte.
