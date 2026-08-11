# El tercer origen: la configuración de la aplicación (`UI00.exe.Config`)

**Documento vivo.** El converter tiene tres fuentes (ver `anatomia_iso.md`): el
programa (`.pgmx`), la máquina (los `.cfg` del CNC) y **la aplicación** — la ventana
Opciones de Maestro, que no viaja en el archivo y sin embargo decide el ISO.

Vive en **`<Maestro>\UI00.exe.Config`**, un `.config` de .NET con ~170 claves en
`<appSettings>`. Mapeo UI↔clave y transcripción de la ventana en el repo Nora:
`skills/cnc-scm-maestro/references/opciones-de-maestro.md`.

## Hay TRES instalaciones de Maestro, y no están configuradas igual

Dato de Fermín (2026-08-10). No son dos: son tres, y sólo una postprocesa.

| # | Instalación | Sistema | Rutas | Rol |
|---|---|---|---|---|
| 1 | **PC del CNC** | **Windows XP 32 bits**, en español | `C:\Archivos de programa\Scm Group\…` (sin `(x86)`: en 32 bits no existe esa separación) · salida a `C:\PrgMaestro\USBMIX` | **la que postprocesa** |
| 2 | **Oficina técnica** | Windows 64 bits | `S:\Maestro\…` y `P:\USBMIX` — **unidades de red** | donde se crean los programas |
| 3 | **PC de casa** | Windows 64 bits | `C:\Program Files (x86)\Scm Group\…`, defaults de fábrica | copia de trabajo; **de acá salieron las capturas del 2026-08-09** |

Que el CNC corra **Windows XP de 32 bits** no es un detalle de color: explica la forma de
sus rutas y acota qué puede correr en esa máquina. (El repo ya tenía un precedente: el
visor de `cnc_traceability/` está escrito para XP 32 bits.)

## El config del CNC contra el de oficina técnica (2026-08-10)

Fermín extrajo el `UI00.exe.Config` de la **PC del CNC** y se comparó contra el de la
**PC de oficina técnica**.

|  | PC del CNC | Oficina técnica |
|---|---|---|
| claves | 172 | 170 |
| bytes | 11.815 | 10.778 |
| rutas | `C:\Archivos de programa\Scm Group\…` | `S:\Maestro\…` + `C:\Program Files (x86)\…` |
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

La ventana Opciones relevada ese día mostraba todas las rutas en
`C:\Program Files (x86)\Scm Group\Maestro\…`. **Salió de la PC de casa** (dato de
Fermín, 2026-08-10), una copia con los defaults de fábrica. Queda confirmada la
advertencia que se anotó aquel día: **esos valores no son los de ninguna de las dos
máquinas de trabajo**, y menos los del CNC.

⇒ Como **oficio** (qué campos tiene la ventana, cómo se llama cada uno, qué ofrece cada
control) esa transcripción sigue valiendo entera. Como **configuración**, no describe
nada de producción.

~~Queda en pie la contradicción anotada aquel día~~ — **RESUELTA el 2026-08-10.** Aquella
captura mostraba «Estacionamiento automático finalizada la ejecución» **marcado** mientras
el archivo decía `IsFinalPark=False`. La captura de la ventana Opciones **de la PC del
CNC** (fixture `dsdmt_25`) muestra ese checkbox **DESMARCADO**, y el `UI00.exe.Config` del
CNC dice `False`: **coherentes**. La UI y el archivo nunca se contradijeron — eran dos
máquinas distintas, y la del 09 era la de casa, que lo tiene marcado.
