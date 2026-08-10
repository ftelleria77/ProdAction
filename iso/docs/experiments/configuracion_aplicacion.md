# El tercer origen: la configuración de la aplicación (`UI00.exe.Config`)

**Documento vivo.** El converter tiene tres fuentes (ver `anatomia_iso.md`): el
programa (`.pgmx`), la máquina (los `.cfg` del CNC) y **la aplicación** — la ventana
Opciones de Maestro, que no viaja en el archivo y sin embargo decide el ISO.

Vive en **`<Maestro>\UI00.exe.Config`**, un `.config` de .NET con ~170 claves en
`<appSettings>`. Mapeo UI↔clave y transcripción de la ventana en el repo Nora:
`skills/cnc-scm-maestro/references/opciones-de-maestro.md`.

## Las dos instalaciones NO están configuradas igual (2026-08-10)

Fermín extrajo el `UI00.exe.Config` de la **PC del CNC** (la que postprocesa) y se
comparó contra el de la **PC de oficina técnica** (donde se crean los programas).

|  | PC del CNC | Oficina técnica |
|---|---|---|
| claves | 172 | 170 |
| bytes | 11.815 | 10.778 |
| rutas | `C:\Archivos de programa\Scm Group\…` (Windows en español) | `S:\Maestro\…` + `C:\Program Files (x86)\…` |
| salida del post | `C:\PrgMaestro\USBMIX` | `P:\USBMIX` |

**25 claves con valor distinto**, y de ellas **dos tocan directamente la traza**:

| Clave | CNC | Oficina | Qué es (nombre en Opciones) |
|---|---|---|---|
| **`RadiusMultiplier`** | **4** | **2** | «Multiplicador del radio en aproximaciones/alejamientos» |
| **`SecurityDistance`** | **20** | **30** | «Distancia de seguridad desde la mesa de trabajo» |

El resto de las diferencias son rutas, historial (`RecentFile1..10`), parámetros de
nesting (`SheetLenght`, `SheetWidth`, `TabThickness`), `OptimizationWaitingTime` y
`IsCamViewEnabled` — ninguna afecta el ISO de una pieza.

Dos claves existen **sólo en el CNC**: `EnvVarDir` y `TechnologiesDir`.

### Lo que SÍ coincide

Las doce claves restantes que la ventana Opciones expone y que podrían cambiar el ISO
están **iguales en las dos PCs**:

`PostFileFormat=ISO` · `IsAreaScm=False` · `IsZetaScm=False` · `IsMM=true` ·
`MillingRetractDistance=10` · `RapidFeed=50` · `IsBottomPlaneMachining=False` ·
`IsCheckCollisionEnabled=False` · `IsParkOnWorkplanChange=False` · `IsFinalPark=False` ·
`FinalParkStopType=0` · `ParkNextToSideStop=True` · `EnableOppositeSideStop=False`

## Por qué importa: la regla 4 en un caso concreto

`RadiusMultiplier` es el multiplicador del radio de los leads, y `SecurityDistance` es
la cota de seguridad por defecto. Son **exactamente** el tipo de valor que un converter
tomaría por constante interna — y la regla 4 lo prohíbe. Si hubiéramos cableado el 2 y
el 30 (los de la PC donde se dibuja), el ISO que produce la PC que postprocesa sería
otro.

## Lo que todavía NO está resuelto

Que los configs difieran **no prueba** que el ISO cambie. Falta separar dos
comportamientos posibles, clave por clave:

- **Default al crear**: Maestro usa el valor al dar de alta la operación y lo
  **congela dentro del `.pgmx`**. Entonces el config de la PC que dibuja importa, el de
  la que postprocesa no. (`SecurityDistance` huele a esto: la cota de seguridad es un
  parámetro de la operación y viaja en el archivo.)
- **Lectura al postprocesar**: el postprocesador consulta el config **en el momento**.
  Entonces manda la PC que postprocesa, y **el mismo `.pgmx` da ISOs distintos en dos
  máquinas**. (`PostFileFormat`, `IsZetaScm` e `IsAreaScm` sólo pueden ser de este tipo:
  deciden el formato de salida, que no es propiedad del programa.)

**El experimento que lo separa** (pendiente): un `.pgmx` con **una** operación de
fresado con acercamiento/alejamiento en modo automático —para que el lead salga del
`RadiusMultiplier` por defecto y no de un valor escrito a mano—, postprocesado en
**las dos** PCs. Si los ISO difieren en el radio del lead, `RadiusMultiplier` se lee al
postprocesar y el converter necesita el config del CNC.

> El experimento del programa vacío (2026-08-10) **no** sirve para esto: sin
> operaciones no hay leads ni cotas de seguridad, así que ninguna de las dos claves
> tiene dónde manifestarse. Por eso sus dos ISO salieron iguales.

## En el snapshot

`iso/data/machine_config/snapshot/maestro_ui/UI00.exe.Config` — el de la **PC del CNC**,
registrado en `manifest.csv` con su origen (`C:\Archivos de programa\Scm Group\Maestro`)
y su sha256. Es el que vale: el converter reproduce lo que emite la máquina que
postprocesa.

El de oficina técnica **no** se guarda: no es la máquina que postprocesa. Su interés es
comparativo y queda documentado acá.

## Nota sobre las capturas del 2026-08-09

La ventana Opciones relevada ese día mostraba **todas** las rutas en
`C:\Program Files (x86)\Scm Group\Maestro\…`. Con los dos configs a la vista se puede
cerrar la duda que quedó anotada: era la **PC de oficina técnica**, con las rutas
todavía en el default de fábrica — entre el 09 y el 10 se reapuntaron a `S:` y `P:`
(el archivo local se reescribió el 10 a las 11:18). No era, ni podía ser, la del CNC:
esa usa `C:\Archivos de programa\…`, la ruta de un Windows en español.

Queda en pie la contradicción anotada aquel día: la UI mostraba «Estacionamiento
automático finalizada la ejecución» **marcado** y el archivo dice `IsFinalPark=False`
— y ahora se sabe que **las dos** PCs tienen `False`. O el checkbox no corresponde a
esa clave, o la captura y el archivo no son del mismo momento.
