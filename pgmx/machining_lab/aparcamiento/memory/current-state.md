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

## Pendientes

1. ~~Confirmar si `Limit` admite valores distintos de `Minimum`.~~
   Resuelto por `CreatePark` en el scripting API (`XilogMaestroScripting.chm`):
   ```csharp
   Operation CreatePark(string name, string stopType, Nullable<bool> toMinQuote)
   // toMinQuote = true  → Limit = "Minimum"  (lado izquierdo)
   // toMinQuote = false → Limit = "Maximum"  (lado derecho)
   // toMinQuote = null  → default (Minimum)
   ```
   `ParkSpec.limit` es un `bool` nullable que mapea a `Minimum`/`Maximum`.
   Pendiente: crear variante con `Maximum` en Maestro para confirmar el XML.
2. Confirmar el `ObjectType` exacto del `Key` de los tres archivos para asegurar
   que es `ScmGroup.XCam.MachiningDataModel.Park` de forma consistente.
3. ~~Actualizar el scanner para filtrar explicitamente `runtime_type == "Park"`.~~
   Resuelto: `scan_samples.py` filtra las filas a `runtime_type == "Park"` antes
   de escribir el CSV.
4. Cuando el contrato quede cerrado, promover a:
   - `pgmx.snapshot` (lectura);
   - `pgmx.synthesis.common.program` (sintesis: `ParkSpec`, `build_park_spec`);
   - `pgmx.synthesis.common.output` (namespace injection para `Park`).
