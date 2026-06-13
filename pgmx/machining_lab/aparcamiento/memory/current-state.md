# Aparcamiento Lab - Estado Actual

Estado inicial: laboratorio creado para estudiar la operacion de maquina
`Aparcamiento` en archivos `.pgmx`.

## Decisiones

- La operacion de aparcamiento se llama `Park` en el XML interno de Maestro.
  Vive como `Executable i:type="Park"` dentro de `MainWorkplan/Elements`.
  El nombre visible en la UI de Maestro es "Aparcamiento"; el tipo serializado
  es "Park".
- Su estructura XML quedo revelada en la Ronda 1 con tres variantes de modo
  de paro.
- El frente quedo abierto explicitamente a partir de esta sesion. Anteriormente
  estaba reservado como familia futura en el lab de machine_operations.

## Referencia

- Lab de machine_operations:
  `pgmx/machining_lab/machine_operations/memory/current-state.md`.
- El patron de investigacion es identico: corpus manual en `S:\...manual\`,
  scanner de descubrimiento, rondas documentadas, promocion cuando las reglas
  esten validadas.

## Corpus

Archivo baseline sintetico:

`S:\Maestro\Projects\ProdAction\PGMX\aparcamiento\generated\Aparcamiento_Baseline.pgmx`
- Pieza `400 x 400 x 18`, origen `(5, 5, 25)`, una fase vacia, sin `Xn`.
- SHA256: `16770755fc7117b45ccbad3bfefdfac08421554bd740b55b6e9900bb255b766d`

## Ronda 1 - Modos De Paro De Park

Corpus manual:

- `S:\Maestro\Projects\ProdAction\PGMX\aparcamiento\manual\Aparcamiento_Baseline_Park_NP.pgmx`
- `S:\Maestro\Projects\ProdAction\PGMX\aparcamiento\manual\Aparcamiento_Baseline_Park_PEI.pgmx`
- `S:\Maestro\Projects\ProdAction\PGMX\aparcamiento\manual\Aparcamiento_Baseline_Park_PDEI.pgmx`

Comparado contra:

- `S:\Maestro\Projects\ProdAction\PGMX\aparcamiento\generated\Aparcamiento_Baseline.pgmx`

Hallazgos:

- El tipo XML interno es `i:type="Park"`, no `"Aparcamiento"`. El nombre
  en la UI de Maestro es "Aparcamiento"; en el XML serializado es "Park".
- Los tres archivos tienen una fase, un unico `Executable i:type="Park"`.
- `Park` no referencia geometria ni pieza: `GeometryID` y `WorkpieceID`
  estan vacios o nulos, a diferencia de `Xn` y `Xmsg` que referencian
  la pieza activa.
- Los campos propios de `Park` son exactamente dos: `Limit` y `Stop`.
- `Limit` es `Minimum` en las tres variantes. Representa la posicion de
  aparcamiento; queda pendiente confirmar si existe `Maximum` u otros valores.
- `Stop` sigue la misma convencion que `Xmsg`:

| Archivo | Paro Maestro | `Park/Stop` |
| --- | --- | --- |
| `Aparcamiento_Baseline_Park_NP.pgmx` | Ningun paro | `Nothing` |
| `Aparcamiento_Baseline_Park_PEI.pgmx` | Paro con Espera de Inicio | `NoUnlock` |
| `Aparcamiento_Baseline_Park_PDEI.pgmx` | Paro con Desbloqueo y Espera de Inicio | `Unlock` |

Estructura completa del nodo `Park`:

| Nodo XML | Valor observado | Notas |
| --- | --- | --- |
| `Key/ID` | asignado por Maestro | clave unica del step |
| `Key/ObjectType` | `ScmGroup.XCam.MachiningDataModel.Park` | tipo de objeto |
| `Name` | `Park` | texto libre, default "Park" |
| `Description` | `""` | siempre vacio |
| `IsEnabled` | `true` | |
| `Priority` | `0` | |
| `GeometryID` | vacio / nil | sin geometria |
| `WorkpieceID` | vacio | sin referencia a pieza |
| `Limit` | `Minimum` | posicion de aparcamiento |
| `Stop` | `Nothing` / `NoUnlock` / `Unlock` | modo de paro |

Campos ausentes respecto de `Xn`: `X`, `Y`, `Speed`, `SpindleEnable`, `Tool`,
`Reference`.

Campos ausentes respecto de `Xmsg`: `Text`, `IsInputEnable`, `Variable`.

Contrato objetivo provisional para promocion:

```text
ParkSpec(
  name: str = "Park",
  limit: str = "Minimum",
  stop: str = "Nothing",   # Nothing | NoUnlock | Unlock
)
```

## Ronda 2 - Validacion De Limit=Maximum

Estado: validado. Frente cerrado.

Hallazgos:

- La UI de Maestro no expone la opcion de posicion de aparcamiento (`Limit`).
  Maestro siempre crea `Park` con `Limit=Minimum` desde la interfaz.
- `Limit=Maximum` solo es alcanzable via scripting API (`toMinQuote=false`) o
  sintetizando el XML directamente.
- Se sintetizo `Aparcamiento_Park_Maximum.pgmx` con `ParkSpec(limit='Maximum')`.
  Maestro lo abrio sin errores y lo re-guardo preservando `Limit=Maximum`.
- La UI no distingue visualmente entre `Minimum` y `Maximum`.

Archivos de evidencia:

- `S:\Maestro\Projects\ProdAction\PGMX\aparcamiento\generated\Aparcamiento_Park_Maximum.pgmx`
- `S:\Maestro\Projects\ProdAction\PGMX\aparcamiento\generated\Aparcamiento_Park_Maximum(Maestro).pgmx`

Reglas cerradas:

- `Limit` acepta `Minimum` y `Maximum`. Default: `Minimum`.
- `ObjectType` del `Key` de `Park` es `ScmGroup.XCam.MachiningDataModel.Park`
  de forma consistente en los tres archivos manuales.
- `ParkSpec` promovido a produccion con `limit: str = "Minimum"` y aliases
  en `_normalize_park_limit()`.

## Pendientes

1. ~~Confirmar si `Limit` admite valores distintos de `Minimum`.~~
   Resuelto — Ronda 2: `Maximum` valido y preservado por Maestro.
2. ~~Confirmar el `ObjectType` exacto del `Key` de los tres archivos.~~
   Resuelto: `ScmGroup.XCam.MachiningDataModel.Park` en los tres.
3. ~~Actualizar el scanner para filtrar explicitamente `runtime_type == "Park"`.~~
   Resuelto: `scan_samples.py` filtra las filas a `runtime_type == "Park"`.
4. ~~Promover a snapshot, synthesis y output.~~
   Resuelto: `ParkSpec`, `build_park_spec` y namespace injection para `Park`
   ya estan en produccion.
