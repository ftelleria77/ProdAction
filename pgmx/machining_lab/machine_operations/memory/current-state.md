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

## Pendientes

1. Reconocer fases en `pgmx.snapshot` sin perder compatibilidad con
   `snapshot.working_steps`.
2. Exponer campos completos de `Xmsg`: texto, parada, input y variable.
3. Ajustar `pgmx.processing` para dibujar solo la primera fase util.
4. Agregar contratos publicos de sintesis para fases y operaciones de maquina
   intercaladas.
