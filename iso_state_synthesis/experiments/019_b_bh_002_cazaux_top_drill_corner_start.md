# 019 - B-BH-002 Cazaux Top Drill Corner Start

Fecha: 2026-05-14

## Objetivo

Cerrar los dos residuales `B-BH-002` del corpus real Cazaux:

- `Cocina/mod 8 - Abierto/Lat_Der.pgmx`
- `Cocina/mod 8 - Abierto/Lat_Izq.pgmx`

Ambos tenian el mismo patron: bloque automatico de `4` top drills con una
sola herramienta efectiva `005`, pero con dos profundidades.

## Evidencia

Antes del cambio, la regla automatica arrancaba por menor `(X,Y)` y luego
seguia vecino mas cercano.

Maestro, en estos dos casos, arranca por el punto de maximo `X` y minimo `Y`:

```text
005@516,50
```

Despues de ese arranque, vuelve a comportarse como vecino mas cercano.

## Regla Aplicada

En `iso_state_synthesis/pgmx_source.py::_ordered_top_drill_block`:

- si el bloque tiene `Operation.ToolKey.name` explicito, se conserva el orden
  fuente;
- si el bloque automatico tiene exactamente `4` top drills, una sola herramienta
  efectiva por diametro y profundidades mixtas, se arranca en maximo `X` y
  minimo `Y`, y luego se usa vecino mas cercano;
- el resto conserva la regla automatica previa: vecino mas cercano desde menor
  `(X,Y)`.

## Prueba De Variante

La variante se probo contra los `60` casos comparables de top drill en Cazaux.

Resultado:

- regla previa: `58/60`;
- regla nueva: `60/60`;
- cambios de orden: solo los dos `mod 8 - Abierto`.

## Validacion

Comandos:

```powershell
py -3 -m tools.studies.iso.top_drill_corpus_order_analysis_2026_05_13
py -3 -m tools.studies.iso.block_transition_corpus_analysis_2026_05_13
py -3 -m tools.studies.iso.block_transition_corpus_analysis_2026_05_13 --pgmx-root 'S:\Maestro\Projects\ProdAction\ISO\Cocina' --iso-root 'P:\USBMIX\ProdAction\ISO\Cocina' --output-dir 'S:\Maestro\Projects\ProdAction\ISO\Cocina\_analysis'
```

Resultados:

| corpus | resultado |
| --- | ---: |
| top drill comparables Cazaux | `60/60` |
| Cazaux completo | `79` exactos, `22` `header_only`, `3` operativos |
| raiz `Pieza*` | `217/222` exactos |
| `ISO/Cocina` | `82/84` exactos |

## Pendiente

Quedan tres residuales operativos en Cazaux:

| frente | caso |
| --- | --- |
| `B-BH-005` | `Bano/Vanitory/Faja frontal.pgmx` |
| `B-RH-002` | `Cocina/mod 6 - Torre horno/Divisor_Horiz.pgmx` |
| `T-XH-001` | `Cocina/mod 6 - Torre horno/Lat_Der.pgmx` |
