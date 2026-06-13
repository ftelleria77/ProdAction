# Machine Operations Lab - Estado Actual

Estado inicial: laboratorio creado para estudiar operaciones de maquina y flujo
multifase Maestro en archivos `.pgmx`.

## Decisiones

- El nombre de fase/workplan es libre y no debe interpretarse como regla
  geometrica fija.
- `Xn` es una operacion de maquina: posiciona el cabezal para dar acceso fisico
  a la pieza.
- `Xmsg` es una operacion de maquina: muestra un mensaje al operario y puede
  detener la ejecucion hasta confirmacion.
- Existen otras operaciones de maquina en Maestro, como `Aparcamiento` o `ISO`,
  que agregan funcionalidad al programa CNC. Quedan reconocidas como familia
  futura, pero fuera del alcance de investigacion e implementacion actual.
- En dibujo 2D se representara solamente la primera fase util con mecanizados.

## Evidencia Inicial

- Caso manual observado:
  `S:\Maestro\Projects\ProdAction\Prod-2026-01 - Vargas\Cocina\Mod.3 - BM-3C-PC-800\Lat_Der_Cajon_Inf.pgmx`.
  Contiene dos `MainWorkplan`, `Xn` entre fases, `Xmsg` con texto `Girar Pieza`
  y otro `Xn` final.
- Caso sintetico inicial generado por ProdAction:
  `generated/MachineOps_001_XN_only.pgmx`.
  - Pieza: `400 x 400 x 18`.
  - Origen de setup: `(5, 5, 25)`.
  - Mecanizados: ninguno.
  - Operacion de maquina: `Xn`, `Reference=Absolute`, `X=-2500`, `Y=nil`.
  - SHA256:
    `b042a3c7bbade2b0b7258c309c0398b0c31472e89e4667d05e117d2572da446b`.

## Ronda 1 - Xn Con Informacion De Herramienta

Corpus manual:

`S:\Maestro\Projects\ProdAction\PGMX\machine_operations\manual\MachineOps_001_XN_Tool_E00X.pgmx`

Archivos revisados:

| Archivo | Xn Tool/ID | Xn Tool/ObjectType | Xn Tool/Name |
| --- | --- | --- | --- |
| `MachineOps_001_XN_Tool_E001.pgmx` | `1900` | `ScmGroup.XCam.ToolDataModel.Tool.CuttingTool` | `E001` |
| `MachineOps_001_XN_Tool_E002.pgmx` | `1901` | `ScmGroup.XCam.ToolDataModel.Tool.CuttingTool` | `E002` |
| `MachineOps_001_XN_Tool_E003.pgmx` | `1902` | `ScmGroup.XCam.ToolDataModel.Tool.CuttingTool` | `E003` |
| `MachineOps_001_XN_Tool_E004.pgmx` | `1903` | `ScmGroup.XCam.ToolDataModel.Tool.CuttingTool` | `E004` |
| `MachineOps_001_XN_Tool_E005.pgmx` | `1904` | `ScmGroup.XCam.ToolDataModel.Tool.CuttingTool` | `E005` |
| `MachineOps_001_XN_Tool_E006.pgmx` | `1905` | `ScmGroup.XCam.ToolDataModel.Tool.CuttingTool` | `E006` |
| `MachineOps_001_XN_Tool_E007.pgmx` | `1906` | `ScmGroup.XCam.ToolDataModel.Tool.CuttingTool` | `E007` |

Hallazgos:

- Cambiar `Informacion de Herramientas` en Maestro no agrega features ni
  operations. El archivo sigue teniendo un unico `Executable i:type="Xn"`.
- La diferencia semantica contra `MachineOps_001_XN_only.pgmx` se limita al
  nodo `Xn/Tool`: `ID`, `ObjectType` y `Name`.
- `Xn` conserva `Reference=Absolute`, `X=-2500`, `Y=nil`, `Speed=0` y
  `SpindleEnable=Off`.
- `WorkpieceSetup/Placement` conserva el origen `(5, 5, 25)`.
- El XML manual guardado por Maestro tiene el mismo arbol de elementos que el
  generado por ProdAction, aunque cambia la serializacion de namespaces y el
  tamano del XML.
- `def.tlgx` conserva el mismo hash de contenido en todas las variantes
  revisadas; el cambio de herramienta se expresa por referencia al catalogo
  embebido, no por modificacion del catalogo.

Implicacion para sintesis:

- `XnSpec` debe admitir herramienta opcional (`tool_id`, `tool_name` o
  `ToolKey`) si queremos reproducir `Informacion de Herramientas`.
- La lectura de `pgmx.snapshot` deberia exponer la herramienta de operaciones
  de maquina, no solo `reference`, `x` e `y`.

## Ronda 2 - Xn Absolute vs Relative

Corpus manual:

- `S:\Maestro\Projects\ProdAction\PGMX\machine_operations\manual\MachineOps_001_XN_Absolute.pgmx`
- `S:\Maestro\Projects\ProdAction\PGMX\machine_operations\manual\MachineOps_001_XN_Relative.pgmx`

Archivos revisados:

| Archivo | Reference | X | Y | Tool |
| --- | --- | ---: | --- | --- |
| `MachineOps_001_XN_Absolute.pgmx` | `Absolute` | `-2500` | `nil` | `System.Object`, `ID=0` |
| `MachineOps_001_XN_Relative.pgmx` | `Relative` | `-2500` | `nil` | `System.Object`, `ID=0` |

Hallazgos:

- Ambos archivos tienen una unica fase, un unico `Executable i:type="Xn"`, sin
  features ni operations.
- Ambos conservan `WorkpieceSetup/Placement = (5, 5, 25)`.
- Ambos conservan `Speed=0`, `SpindleEnable=Off`, `Tool=System.Object ID=0` y
  `Y i:nil="true"`.
- La diferencia semantica exacta entre ambos XML es solo:
  `Xn/Reference = Absolute` vs `Xn/Reference = Relative`.
- `def.tlgx` conserva el mismo hash de contenido que las variantes anteriores.

Implicacion para sintesis:

- La normalizacion actual de `XnSpec.reference` con `Absolute/Relative` coincide
  con Maestro para esta ronda.
- El scanner del laboratorio debe conservar explicitamente `y_nil` para no
  confundir `Y` vacio/nulo con un valor numerico `0`.

## Ronda 3 - Xn Con Nombre De Texto

Corpus manual:

- `S:\Maestro\Projects\ProdAction\PGMX\machine_operations\manual\MachineOps_001_XN_TextName.pgmx`

Comparado contra:

- `S:\Maestro\Projects\ProdAction\PGMX\machine_operations\manual\MachineOps_001_XN_Absolute.pgmx`

Hallazgos:

- El archivo conserva una unica fase, un unico `Executable i:type="Xn"`, sin
  features ni operations.
- Conserva `WorkpieceSetup/Placement = (5, 5, 25)`.
- Conserva `Reference=Absolute`, `X=-2500`, `Y i:nil="true"`, `Tool=System.Object ID=0`,
  `Speed=0` y `SpindleEnable=Off`.
- La diferencia semantica exacta contra `MachineOps_001_XN_Absolute.pgmx` es
  solo `Xn/Name`: `Xn` -> `Operación Nula`.
- `def.tlgx` conserva el mismo hash de contenido que las variantes anteriores.

Implicacion para sintesis:

- `XnSpec` deberia admitir un `name` opcional para reproducir el texto visible
  de Maestro sin afectar la operacion de maquina.

## Ronda 4 - Xn Con Velocidad

Corpus manual:

- `S:\Maestro\Projects\ProdAction\PGMX\machine_operations\manual\MachineOps_001_XN_V2,5.pgmx`

Comparado contra:

- `S:\Maestro\Projects\ProdAction\PGMX\machine_operations\manual\MachineOps_001_XN_Absolute.pgmx`

Hallazgos:

- El archivo conserva una unica fase, un unico `Executable i:type="Xn"`, sin
  features ni operations.
- Conserva `WorkpieceSetup/Placement = (5, 5, 25)`.
- Conserva `Name=Xn`, `Reference=Absolute`, `X=-2500`, `Y i:nil="true"`,
  `Tool=System.Object ID=0` y `SpindleEnable=Off`.
- La diferencia semantica exacta contra `MachineOps_001_XN_Absolute.pgmx` es
  solo `Xn/Speed`: `0` -> `2.5`.
- `def.tlgx` conserva el mismo hash de contenido que las variantes anteriores.

Implicacion para sintesis:

- `XnSpec` debe conservar un `speed` opcional para reproducir la velocidad de
  desplazamiento de la operacion nula.
- El scanner del laboratorio debe conservar `speed` y `spindle_enable` como
  campos propios de operaciones de maquina.

## Ronda 5 - Xn Con Electromandril Encendido

Corpus manual:

- `S:\Maestro\Projects\ProdAction\PGMX\machine_operations\manual\MachineOps_001_XN_EM_ON.pgmx`

Comparado contra:

- `S:\Maestro\Projects\ProdAction\PGMX\machine_operations\manual\MachineOps_001_XN_Absolute.pgmx`

Hallazgos:

- El archivo conserva una unica fase, un unico `Executable i:type="Xn"`, sin
  features ni operations.
- Conserva `WorkpieceSetup/Placement = (5, 5, 25)`.
- Conserva `Name=Xn`, `Reference=Absolute`, `Speed=0`, `X=-2500`,
  `Y i:nil="true"` y `Tool=System.Object ID=0`.
- La diferencia semantica exacta contra `MachineOps_001_XN_Absolute.pgmx` es
  solo `Xn/SpindleEnable`: `Off` -> `On`.
- `def.tlgx` conserva el mismo hash de contenido que las variantes anteriores.

Implicacion para sintesis:

- `XnSpec` debe conservar `spindle_enable` opcional para reproducir
  `EM_ON`/`EM_OFF`.

## Cierre - Operacion Nula `Xn`

Estado: evidencia de laboratorio cerrada.

Las opciones observadas de la operacion nula quedan cubiertas por el corpus
`MachineOps_001_XN_*.pgmx`:

| Campo Maestro | Nodo XML | Estado observado |
| --- | --- | --- |
| Nombre visible | `Executable/Name` | Default `Xn`; puede cambiar a texto libre. |
| Referencia | `Executable/Reference` | `Absolute` o `Relative`. |
| Velocidad | `Executable/Speed` | Default `0`; puede tomar valor decimal como `2.5`. |
| Electromandril | `Executable/SpindleEnable` | `Off` o `On`. |
| Informacion de herramienta | `Executable/Tool` | Default `System.Object ID=0`; puede referenciar `CuttingTool` `E001..E007`. |
| Posicion X | `Executable/X` | Valor numerico, observado `-2500`. |
| Posicion Y | `Executable/Y` | Puede quedar `i:nil="true"` cuando el campo esta vacio. |
| Pieza | `Executable/WorkpieceID` | Referencia a la pieza activa. |
| Geometria | `Executable/GeometryID` | `ID=0` con `ObjectType i:nil="true"` en los casos con `Y=nil`. |

Reglas cerradas:

- `Xn` es una operacion de maquina, no un feature ni una operation de
  mecanizado.
- No agrega entradas en `Features` ni en `Operations`.
- Vive como `Executable i:type="Xn"` dentro de `MainWorkplan/Elements`.
- Puede ubicarse dentro de una fase, entre fases o al final de un programa.
- La herramienta de `Xn`, cuando existe, se expresa como referencia al catalogo
  embebido; no modifica `def.tlgx`.
- Cambios de `Name`, `Reference`, `Speed`, `SpindleEnable` y `Tool` no alteran
  el resto del arbol Maestro del caso minimo.

Contrato objetivo para promocion:

```text
XnSpec(
  name: str = "Xn",
  reference: str = "Absolute",
  speed: float = 0,
  spindle_enable: str = "Off",
  x: float,
  y: float | None,
  tool_id: str | None,
  tool_name: str | None,
)
```

La promocion productiva queda pendiente para `pgmx.snapshot` y
`pgmx.synthesis.common.program`, pero el frente de investigacion de `Xn` queda
cerrado.

## Ronda 6 - Nombre Libre De Fase

Corpus manual:

- `S:\Maestro\Projects\ProdAction\PGMX\machine_operations\manual\MachineOps_001_XN_only_FaseInicial.pgmx`

Comparado contra:

- `S:\Maestro\Projects\ProdAction\PGMX\machine_operations\manual\MachineOps_001_XN_Absolute.pgmx`

Hallazgos:

- El archivo conserva una unica fase, un unico `Executable i:type="Xn"`, sin
  features ni operations.
- Conserva `CurrentWorkplanIndex=0`.
- Conserva la misma clave de fase:
  `ScmGroup.XCam.MachiningDataModel.ProjectModule.MainWorkplan`, `ID=1912`.
- Conserva `WorkpieceSetup/Placement = (5, 5, 25)`.
- Conserva todo el bloque `Xn`: `Name=Xn`, `Reference=Absolute`, `Speed=0`,
  `SpindleEnable=Off`, `X=-2500`, `Y i:nil="true"` y
  `Tool=System.Object ID=0`.
- La diferencia semantica exacta contra `MachineOps_001_XN_Absolute.pgmx` es
  solo `MainWorkplan/Name`: `Setup` -> `Fase Inicial`.
- `def.tlgx` conserva el mismo hash de contenido que las variantes anteriores.

Implicacion para sintesis:

- La fase debe tener `name` libre en el contrato futuro; no debe inferirse
  geometria ni comportamiento desde nombres como `Setup`, `Fase Inicial`,
  `Cara Interior` o equivalentes.
- `pgmx.snapshot` debe exponer el nombre de cada `MainWorkplan` como dato de
  programa/fase.

## Ronda 7 - Dos Fases, Segunda Fase Vacia

Corpus manual:

- `S:\Maestro\Projects\ProdAction\PGMX\machine_operations\manual\MachineOps_001_XN_only_FaseFinal.pgmx`

Comparado contra:

- `S:\Maestro\Projects\ProdAction\PGMX\machine_operations\manual\MachineOps_001_XN_only_FaseInicial.pgmx`

Hallazgos:

- `MachineOps_001_XN_only_FaseInicial.pgmx` tiene una fase:
  - `CurrentWorkplanIndex=0`;
  - `MainWorkplan ID=1912`;
  - `Name=Fase Inicial`;
  - `Setup ID=1913`;
  - `WorkpieceSetup/Placement=(5, 5, 25)`;
  - `Elements` contiene un unico `Executable i:type="Xn"`.
- `MachineOps_001_XN_only_FaseFinal.pgmx` tiene dos fases:
  - `CurrentWorkplanIndex=1`;
  - fase 1: `MainWorkplan ID=1912`, `Name=Fase Inicial`,
    `Setup ID=1913`, `Placement=(5, 5, 25)`, con el mismo `Xn`;
  - fase 2: `MainWorkplan ID=1932`, `Name=Fase Final`,
    `Setup ID=1933`, `Placement=(0, 0, 25)`, `Elements` vacio.
- No agrega features ni operations.
- `def.tlgx` conserva el mismo hash de contenido que las variantes anteriores.
- La diferencia estructural contra `FaseInicial` es:
  - `Project/CurrentWorkplanIndex`: `0` -> `1`;
  - `Project/Workplans`: pasa de 1 a 2 `MainWorkplan`.

Implicacion para lectura/sintesis:

- Una fase puede existir sin operaciones ni `Executable`.
- El scanner y `pgmx.snapshot` deben modelar fases/workplans como entidades
  propias, no solo como una lista plana de `working_steps`.
- `CurrentWorkplanIndex` debe conservarse como dato de programa. En este caso
  apunta a la segunda fase (`1`), pero queda pendiente confirmar si Maestro lo
  usa como fase activa, ultima editada o seleccionada.
- Cada fase tiene su propio `Setup/WorkpieceSetup/Placement`, aun cuando no
  tenga pasos.

## Ronda 8 - Dos Fases, Xn En Fase Final

Corpus manual:

- `S:\Maestro\Projects\ProdAction\PGMX\machine_operations\manual\MachineOps_001_XN_only_FaseFinal_XN.pgmx`

Comparado contra el estado actual de:

- `S:\Maestro\Projects\ProdAction\PGMX\machine_operations\manual\MachineOps_001_XN_only_FaseFinal.pgmx`

Hallazgos:

- Ambos archivos tienen dos fases, sin features ni operations.
- En el archivo base actual:
  - `CurrentWorkplanIndex=0`;
  - fase 1 `Fase Inicial`, `Placement=(5, 5, 25)`, contiene un unico `Xn`;
  - fase 2 `Fase Final`, `Placement=(0, 0, 25)`, tiene `Elements` vacio.
- En `MachineOps_001_XN_only_FaseFinal_XN.pgmx`:
  - `CurrentWorkplanIndex=1`;
  - fase 1 `Fase Inicial`, `Placement=(5, 5, 25)`, tiene `Elements` vacio;
  - fase 2 `Fase Final`, `Placement=(0, 0, 25)`, contiene un unico `Xn`.
- El `Xn` movido conserva la misma clave:
  `ScmGroup.XCam.MachiningDataModel.Xn`, `ID=1927`.
- El bloque `Xn` conserva `Name=Xn`, `Reference=Absolute`, `Speed=0`,
  `SpindleEnable=Off`, `X=-2500`, `Y i:nil="true"` y
  `Tool=System.Object ID=0`.
- La diferencia estructural exacta contra el archivo base actual es:
  - `Project/CurrentWorkplanIndex`: `0` -> `1`;
  - `Fase Inicial/Elements`: pasa de 1 `Executable` a 0;
  - `Fase Final/Elements`: pasa de 0 `Executable` a 1.
- `def.tlgx` conserva el mismo hash de contenido que las variantes anteriores.

Implicacion para lectura/sintesis:

- Las operaciones de maquina pertenecen al `Elements` de una fase concreta y
  pueden moverse entre fases sin cambiar su `Key`.
- La sintesis multifase debe permitir fases vacias y operaciones de maquina
  ubicadas en cualquier fase.
- `CurrentWorkplanIndex` acompaña la fase activa/seleccionada en estos casos,
  pero sigue pendiente confirmar si debe emitirse siempre como indice de la
  ultima fase creada, fase activa o fase seleccionada al guardar.

## Ronda 9 - Dos Fases, Un Xn En Cada Fase

Corpus manual:

- `S:\Maestro\Projects\ProdAction\PGMX\machine_operations\manual\MachineOps_001_XN_FI_XN_FF_XN.pgmx`

Comparado contra:

- `S:\Maestro\Projects\ProdAction\PGMX\machine_operations\manual\MachineOps_001_XN_only_FaseFinal_XN.pgmx`

Hallazgos:

- Ambos archivos tienen dos fases, sin features ni operations.
- En `MachineOps_001_XN_only_FaseFinal_XN.pgmx`:
  - `CurrentWorkplanIndex=1`;
  - `Fase Inicial` esta vacia;
  - `Fase Final` contiene un unico `Xn`, `ID=1927`, `X=-2500`.
- En `MachineOps_001_XN_FI_XN_FF_XN.pgmx`:
  - `CurrentWorkplanIndex=0`;
  - `Fase Inicial` contiene un `Xn` nuevo:
    - `ID=1934`;
    - `Name=Xn Fase Inicial`;
    - `Reference=Absolute`;
    - `Speed=0`;
    - `SpindleEnable=Off`;
    - `X=-2000`;
    - `Y i:nil="true"`;
    - `Tool=System.Object ID=0`;
  - `Fase Final` conserva el `Xn` anterior:
    - `ID=1927`;
    - `Name=Xn`;
    - `Reference=Absolute`;
    - `Speed=0`;
    - `SpindleEnable=Off`;
    - `X=-2500`;
    - `Y i:nil="true"`;
    - `Tool=System.Object ID=0`.
- `def.tlgx` conserva el mismo hash de contenido que las variantes anteriores.

Implicacion para lectura/sintesis:

- Una fase puede contener su propia operacion nula y un programa multifase puede
  tener multiples `Xn`.
- Agregar un `Xn` en otra fase crea un nuevo `Executable` con nueva `Key`, no
  reutiliza necesariamente el `Xn` existente.
- `CurrentWorkplanIndex` vuelve a cambiar segun la fase activa/seleccionada al
  guardar; en esta ronda queda `0` aunque existen dos fases.
- El contrato de sintesis debe permitir multiples `XnSpec` ubicados por fase y
  preservar orden/keys mediante reserva de IDs.

## Ronda 10 - Xmsg Con Modos De Paro

Corpus manual:

- `S:\Maestro\Projects\ProdAction\PGMX\machine_operations\manual\MachineOps_001_FI_XN_MSG_NP_FF_XN.pgmx`
- `S:\Maestro\Projects\ProdAction\PGMX\machine_operations\manual\MachineOps_001_FI_XN_MSG_PEI_FF_XN.pgmx`
- `S:\Maestro\Projects\ProdAction\PGMX\machine_operations\manual\MachineOps_001_FI_XN_MSG_PDEI_FF_XN.pgmx`

Comparado contra:

- `S:\Maestro\Projects\ProdAction\PGMX\machine_operations\manual\MachineOps_001_XN_FI_XN_FF_XN.pgmx`

Estructura comun:

- Dos fases, sin features ni operations.
- `CurrentWorkplanIndex=0`.
- `Fase Inicial`, `Placement=(5, 5, 25)`:
  - paso 1: `Xn`, `ID=1934`, `Name=Despeje de pieza`, `X=-2000`;
  - paso 2: `Xmsg`, `ID=1935`, `Name=Mensaje a operador`,
    `Text=Girar la Pieza`.
- `Fase Final`, `Placement=(0, 0, 25)`:
  - paso 1: `Xn`, `ID=1927`, `Name=Despeje y Fin`, `X=-2500`.
- `Xmsg/GeometryID` usa `ID=0` con `ObjectType i:nil="true"`.
- `Xmsg/WorkpieceID` referencia la pieza `ID=1917`.
- `Xmsg/IsInputEnable=false`.
- `Xmsg/Variable` queda vacio.
- `def.tlgx` conserva el mismo hash de contenido que las variantes anteriores.

Variantes observadas:

| Archivo | Paro Maestro | `Xmsg/Stop` |
| --- | --- | --- |
| `MachineOps_001_FI_XN_MSG_NP_FF_XN.pgmx` | Ningun paro | `Nothing` |
| `MachineOps_001_FI_XN_MSG_PEI_FF_XN.pgmx` | Paro con Espera de Inicio | `NoUnlock` |
| `MachineOps_001_FI_XN_MSG_PDEI_FF_XN.pgmx` | Paro con Desbloqueo y Espera de Inicio | `Unlock` |

Hallazgos:

- `Xmsg` es un `Executable i:type="Xmsg"` dentro de
  `MainWorkplan/Elements`.
- No agrega entradas en `Features` ni en `Operations`.
- Las tres variantes conservan la misma clave `Xmsg`, `ID=1935`.
- La diferencia semantica exacta entre las tres variantes es solo
  `Xmsg/Stop`.
- Al agregar el mensaje, Maestro tambien permite renombrar los `Xn` existentes
  (`Despeje de pieza`, `Despeje y Fin`), pero eso pertenece a `Xn/Name`, no al
  contrato propio de `Xmsg`.

Contrato objetivo para promocion:

```text
XmsgSpec(
  name: str = "Xmsg",
  text: str,
  stop: Literal["Nothing", "NoUnlock", "Unlock"],
  input_enabled: bool = False,
  variable_id: str | None = None,
)
```

Implicacion para lectura/sintesis:

- `pgmx.snapshot` debe exponer `Xmsg` como operacion de maquina con `text`,
  `stop`, `input_enabled`, `variable`, `geometry_ref` y `workpiece_ref`.
- La sintesis multifase debe permitir ubicar `XmsgSpec` en cualquier fase y
  preservar su orden respecto de `Xn` y mecanizados.

## Alcance Actual

- El contrato productivo inmediato de operaciones de maquina debe cubrir fases,
  `Xn` y `Xmsg`.
- Operaciones como `Aparcamiento` o `ISO` deben quedar reservadas para una
  extension futura. No se investigan, sintetizan ni exponen como contrato
  publico en esta etapa.

## Ronda 11 - Promocion Productiva Inicial

Estado: promocion inicial ejecutada.

Cambios productivos:

- `pgmx.snapshot` ahora expone:
  - `current_workplan_index`;
  - `workplans` como entidades propias;
  - origen de setup por fase;
  - `working_steps` compatibles con la vista plana historica, pero enriquecidos
    con `workplan_index`, `workplan_id`, `workplan_name`, `geometry_ref`,
    `workpiece_ref`, `tool_ref`, `speed`, `spindle_enable`, `text`, `stop`,
    `input_enabled` y `variable_ref`;
  - `machine_operations` como vista filtrada de `Xn` y `Xmsg`.
- `pgmx.synthesis.common.program` ahora expone:
  - `WorkplanSpec`;
  - `MachineOperationSpec`;
  - `XmsgSpec`;
  - `build_workplan_spec(...)`;
  - `build_xmsg_spec(...)`;
  - `XnSpec` ampliado con `name`, `speed`, `spindle_enable`, herramienta y
    coordenadas.
- `synthesize_request(...)` conserva el comportamiento historico cuando no se
  pasan `workplans`: sigue agregando el `Xn` final mediante `xn`.
- Cuando se pasan `workplans`, la sintesis usa el contrato multifase explicito
  y ubica `Xn`/`Xmsg` por fase.
- `pgmx.processing` toma solamente la primera fase util con mecanizados para el
  dibujo 2D.

Validacion:

- `tests.test_pgmx_machine_operations`: OK.
- `tests.test_pgmx_processing`: OK.
- `tests.test_pgmx_synthesis_package`: OK.
- `tests.test_pgmx_public_facades`: OK.
- `tests.test_project_detail_pgmx`: OK.
- `py -3 -m pgmx.machining_lab.machine_operations.scan_samples`: OK.
- `py -3 -m compileall pgmx`: OK.

## Ronda 12 - Semantica De `Xn/Y`

Estado: regla promovida a codigo productivo.

Regla operativa:

- `Xn/X` es una coordenada explicita de destino.
- `Xn/Y` puede ser un valor numerico `float` o puede ser nulo.
- Si `Y` es numerico, la operacion nula mueve el cabezal hasta `(X, Y)`.
- Si `Y` es nulo, la operacion nula mueve el cabezal hasta la posicion `X`
  indicada y conserva la coordenada `Y` actual.

Caso de referencia:

- `S:\Maestro\Projects\ProdAction\Prod-2026-01 - Vargas\Cocina\Mod.3 - BM-3C-PC-800\Fondo.pgmx`
  contiene un `Xn` final con `X=-2300`, `Y=0`, `Tool=E001`.

Cambios productivos:

- `XnSpec.y` sigue siendo `float | None`.
- La sintesis serializa `Y i:nil="true"` cuando `XnSpec.y is None`.
- La sintesis serializa `Y=<numero>` cuando `XnSpec.y` es numerico.
- Para `Y` numerico se emite `GeometryID` como referencia `ID=0`,
  `ObjectType=System.Object`, siguiendo el caso observado en `Fondo.pgmx`.
- `pgmx.adapters` conserva la ultima operacion `Xn` del snapshot como
  `PgmxAdaptationResult.xn` y la pasa a `build_synthesis_request(...)`, para
  no perder `X`, `Y`, nombre, velocidad, electromandril ni herramienta.

## Ronda 13 - Mecanizados Por Fase

Estado: promocion productiva ejecutada y validada.

Regla operativa:

- `WorkplanSpec` ahora puede contener `machinings`, ademas de
  `machine_operations`.
- Los mecanizados de cada fase se serializan en el `MainWorkplan/Elements`
  correspondiente.
- Dentro de cada fase, el orden queda:
  1. mecanizados declarados en `machinings`;
  2. operaciones de maquina declaradas en `machine_operations`.
- El comportamiento historico se mantiene cuando no se usan `workplans`:
  el request de una sola fase sigue agregando el `Xn` final por `xn`.

Caso sintetizado:

- `S:\Maestro\Projects\ProdAction\Prod-2026-01 - Vargas\Cocina\Mod.3 - BM-3C-PC-800\Fondo_DobleFase.pgmx`
  se genero con baseline limpio y se hidrato desde:
  - `Fondo.pgmx` para la fase `Cara_Superior`;
  - `FondoF6.pgmx` para la fase `Cara_Inferior`.
- `Cara_Superior` conserva origen `(5, 5, 25)`, contiene los 10 mecanizados
  adaptados de `Fondo.pgmx`, cierra con el `XN` del archivo principal y luego
  agrega `Xmsg` con nombre/texto `Girar Pieza` y `Stop=NoUnlock`.
- `Cara_Inferior` usa origen `(0, 0, 25)`, contiene los 16 taladros adaptados
  de `FondoF6.pgmx` y cierra con el mismo `XN` del archivo principal.
- Correccion posterior: no usar `Fondo.pgmx` como `baseline_path` para este
  archivo combinado. Eso deja features/operaciones/expresiones originales
  huerfanas y puede provocar en Maestro `VariableValueNotValid` al aplicar la
  pieza. Usar `source_pgmx_path=Fondo.pgmx` solo para hidratacion.
- Segunda correccion posterior: Maestro rechazo el archivo con un error de
  deserializacion de `Xmsg`:
  `MachiningDataModel.ProjectModule:Xmsg` no era un tipo conocido para
  `Executable`.
  La causa era que el finalizador XML solo agregaba el namespace base al primer
  `Xn`; los `Xmsg` y los `Xn` siguientes quedaban con `i:type` resuelto contra
  el namespace heredado de `ProjectModule`. El finalizador ahora aplica
  `xmlns="http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel"`
  a todos los `Executable i:type="Xn"` y `Executable i:type="Xmsg"`.

Validacion:

- `read_pgmx_snapshot(...)` lee dos workplans:
  - `Cara_Superior`: 12 working steps;
  - `Cara_Inferior`: 17 working steps.
- El archivo corregido tiene 26 features, 26 operaciones y 29 working steps.
- El XML crudo del PGMX corregido contiene 2 `Xn` y 1 `Xmsg` con namespace
  base explicito sobre el `Executable`.
- `tests.test_pgmx_machine_operations`: OK.
- `tests.test_pgmx_synthesis_package`: OK.
- `py -3 -m compileall pgmx`: OK.
- `py -3 -m unittest discover tests`: 367 tests OK.

## Ronda 14 - Validacion En Maestro De Doble Fase

Estado: validado. Frente cerrado.

Archivo validado:

- `S:\Maestro\Projects\ProdAction\Prod-2026-01 - Vargas\Cocina\Mod.3 - BM-3C-PC-800\Fondo_DobleFase.pgmx`

Maestro abrio el archivo sin errores. El usuario lo guardo sin modificaciones como
`Fondo_DobleFase(Maestro).pgmx`. Comparacion XML entre sintetizado y re-guardado:

- 9552 tags identicos.
- Un unico token distinto: `<CurrentWorkplanIndex>0</CurrentWorkplanIndex>`
  en el sintetizado vs. `<CurrentWorkplanIndex>1</CurrentWorkplanIndex>`
  en el guardado por Maestro.
- La diferencia se explica porque Maestro actualiza `CurrentWorkplanIndex`
  al indice de la fase seleccionada al momento de guardar. No es un error
  estructural; el archivo es semanticamente identico.

Regla confirmada:

- `CurrentWorkplanIndex` es un campo de estado de UI que Maestro actualiza
  al guardar. La sintesis puede emitir cualquier valor valido; Maestro lo
  sobreescribe al abrir y guardar.

## Pendientes

1. ~~Validar en Maestro `Fondo_DobleFase.pgmx` con dos fases, mecanizados por
   fase, `Xn` y `Xmsg`.~~ Resuelto — Ronda 14.
2. Si aparece necesidad real, estudiar `Xmsg/Variable` e `IsInputEnable=true`.
3. Definir intercalacion libre entre mecanizados y operaciones de maquina
   dentro de una misma fase solo si aparece un caso real que necesite mezclar
   `Xn`/`Xmsg` entre mecanizados.
4. Mantener `Aparcamiento` e `ISO` fuera de alcance hasta que el usuario abra
   explicitamente ese frente.
