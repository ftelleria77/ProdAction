# ProdAction PGMX Map

Fuente principal: `ftelleria77/ProdAction/pgmx`.

## Directorios relevantes

- `pgmx/docs/`: manuales de referencia SCM Group extraidos de CHM.
  - `xilog_plus_pgm/`: Xilog Plus Editor / lenguaje PGM.
  - `maestro_scripting/`: Xilog Maestro Scripting / operaciones C#.
- `pgmx/snapshot.py`: lectura integral y normalizada de archivos `.pgmx` existentes.
- `pgmx/adapters.py`: adaptacion desde/hacia estructuras usadas por ProdAction.
- `pgmx/synthesis/`: generacion productiva PGMX.
  - `common/`: construccion comun de programas.
  - `drilling/`: taladrado.
  - `milling/`: fresado/vaciado.
- `pgmx/machining_lab/`: laboratorios de investigacion por familia de mecanizado.
  - `machine_operations/`: flujo de programa, fases/workplans, `Xn`, `Xmsg`.
  - `pocket_milling/`: `ClosedPocket` / pocket milling / frente historico de Vaciado.
  - `aparcamiento/`: plano motorizado / estacionamiento.

## Lecturas por tarea

### Entender parametros de operaciones

Leer `pgmx/docs/maestro_scripting/01_create_operations.md` para firmas de operaciones como `CreateDrill`, `CreateSlot`, `CreateIso`, `CreatePark`, `CreateContourPocket`.

### Entender PGM/Xilog

Leer:

- `pgmx/docs/xilog_plus_pgm/05_1_header.md` para encabezado: `DX`, `DY`, `DZ`, `V`, `T`, `BX`, `BY`, `BZ`.
- `pgmx/docs/xilog_plus_pgm/05_2_instrucciones_basicas.md` para instrucciones basicas: `G0`, `G1`, `G2`, `G3`, `XG0`, `SET`, `MSG`, `ISO`.
- `pgmx/docs/xilog_plus_pgm/05_3_instrucciones_completas.md` para modo grafico.
- `pgmx/docs/xilog_plus_pgm/09_1_instruccion_pb.md` y `09_13_reglas_estacionamiento.md` para PB y estacionamiento.

### Leer o modificar `.pgmx`

El `.pgmx` es un **ZIP con XML adentro** — ver `references/pgmx-file-format.md` (entradas del ZIP,
dónde está `ExecutionFields`/campo, `read_pgmx_snapshot`/`adapt_pgmx_path`, namespaces). No
re-derivar el formato. Para modificaciones, comparar snapshots y conservar estructura no tocada.

### Generar PGMX productivo

Leer `pgmx/synthesis/cli.py`, `pgmx/synthesis/core.py`, `pgmx/synthesis/common/`, y luego la familia concreta (`drilling`, `milling`, etc.).

### Investigar una regla no cerrada

Leer `pgmx/machining_lab/README.md` y el laboratorio de la familia. Tratar conclusiones como evidencia hasta que migren a `pgmx/synthesis` con tests.

## Estado inicial conocido desde Nora

- `Xn` es una operacion de maquina observada como `Executable i:type="Xn"` en `MainWorkplan/Elements`; no crea `Features` ni `Operations`.
- `Xmsg` es una operacion de maquina observada como `Executable i:type="Xmsg"`; conserva texto, parada, input, variable y referencias a pieza/geometria.
- Modos observados de `Xmsg/Stop`: `Nothing`, `NoUnlock`, `Unlock`.
- La promocion de `Xn` y `Xmsg` desde laboratorio hacia `pgmx.snapshot` y `pgmx.synthesis.common.program` era un frente recomendado.
