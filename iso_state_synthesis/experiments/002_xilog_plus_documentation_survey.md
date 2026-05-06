# Experimento 002 - Documentacion Xilog Plus E ISO

Fecha: 2026-05-06

## Proposito

Explorar el arbol instalado de Xilog Plus para ubicar documentacion tecnica o
archivos de soporte que expliquen como se arman los programas ISO.

La exploracion se hizo sobre:

- `C:\Program Files (x86)\Scm Group\Xilog Plus`

## Metodo

- Se listo el arbol completo por extension.
- Se aislaron ayudas `.chm` y `.hlp`.
- Se decompilaron ayudas relevantes con `hh.exe -decompile` en una carpeta
  temporal local.
- Se buscaron terminos `WinXiso`, `XISO`, `ISO`, `NCI`, `PostISO`,
  `Pgm2Iso`, `PppIso`, `VtGenIso`, `ETK`, `EDK`, `SHF`, `G71`, `G53`,
  `M58`, `utensile`, `testina`, `mandrino`, `programma` y variantes en
  Italiano/Ingles/Espanol.
- Se inspeccionaron archivos de configuracion y esquemas XML incluidos con el
  software.

## Fuentes Encontradas

Ayudas relevantes:

| Archivo | Lectura |
| --- | --- |
| `Xilog_Plus_Winxiso.chm` | Ayuda de WinXiso en Italiano. |
| `Country/Ita/Xilog_Plus_WinXiso.chm` | Misma familia de ayuda en Italiano. |
| `Country/Ing/Xilog_Plus_WinXiso.chm` | Misma ayuda en Ingles, util para terminos tecnicos. |
| `Country/Ita/Xilog_Plus_Editor.chm` | Manual del editor Xilog Plus; contiene `Programma ISO` y apendices. |
| `Country/Ing/Xilog_Plus_Editor.chm` | Version inglesa; contiene `ISO Program`, `CNC`, `WinXiso` y `Direct Management of ISO Programs`. |
| `Country/Ita/Testine.chm` | Manual de configuracion/programacion de testinas; util para parametros de cabezales especiales. |
| `Country/Ita/Xilog_Plus_PanelMac.chm` | Panel de maquina. Menos directo para sintesis ISO. |

Componentes binarios relevantes:

| Archivo | Lectura |
| --- | --- |
| `Bin/Winxiso.exe` | Interfaz/conversor historico. Las cadenas internas muestran modos `PGM -> ISO`, `XXL+BMP -> PGM`, `XXL+EPL -> PGM`, `PGM -> XXL`, `XXL -> PGM`. |
| `Bin/Pgm2Iso32.dll` | DLL de preparacion/generacion ISO; cadenas internas mencionan `SetUpDataForISO`, `CleanUpDataForISO`, `XabsToIsoBegin`, `PostISO_SetTargetCN`, `def.tlg`, `xxl2pgm2.pgm`. |
| `Bin/PostISO.dll` | Postprocesador; cadenas internas mencionan `PostISO_Initialize`, `PostISO_Generate`, `PostISO_Finalize`, `PostISO.cfg`, `Script.cfg`, familias `ISO-NUM`, `ISO-OSAI`, `ISO-ORCHESTRA`, `ISO-ESAGV`, y emisiones `ETK`/`EDK`. |
| `Bin/PppIso.dll` | Generacion grafica/embebida ISO; cadenas internas mencionan `GraphIsoGeneration_*`, `GetCode_ISO_*`, `GetParTool_*`, `GetParSpindle_*`, `LoadEmbIsoCode`. |
| `Bin/VtGenIso.dll` | Generadores por familia/dispositivo; contiene clases `VtGenIso_*` para `PB`, `PseudoIso_Iso`, `MotionCtr`, `CrossLaser`, etc. |
| `Bin/IsoTrd.dll` | Traductor XAbs a ISO; expone `XabsToIsoBegin`, `XabsToIsoTranslate`, `XabsToIsoEnd`. |
| `Bin/Xiso32.dll` | Compilador/interprete XISO; expone `xISOGen*`, `xISOBegin`, `xISOEnd`, lectura de PGM, herramientas y configuracion. |
| `Bin/Nci.dll`, `Bin/nci32.dll` | Integracion NCI/CNC; expone funciones de descarga/gestion ISO y generacion grafica. |

Esquemas XISO relevantes:

| Archivo | Lectura |
| --- | --- |
| `Bin/XmlSchema/XISOProjectSchema/XISOProjectSchema.xsd` | Define el modelo interpretado del lenguaje XISO: `H`, `G0`, `G1`, `G2`, `G3`, `TSET`, `PB`, etc. |
| `Bin/XmlSchema/XISOSourceProjectSchema/XISOSourceProjectSchema.xsd` | Define contenedor de lineas fuente XISO con texto original. |
| `Bin/XmlSchema/XISOConfigSchema/XISOConfigSchema.xsd` | Define subconjunto de configuracion Xilog usado por XISO. |
| `Bin/XmlSchema/XISOMachinerySchema/XISOMachinerySchema.xsd` | Define configuracion fisica de maquinaria/mesa/ejes. |
| `Bin/XmlSchema/XISOViewSolutionSchema/XISOViewSolutionSchema.xsd` | Une rutas a config, fuente, proyecto interpretado y maquinaria para visualizacion. |

Configuracion relevante:

| Archivo | Lectura |
| --- | --- |
| `Cfg/NCI.CFG` | Plantilla NCI activa para prologo/epilogo ISO; contiene `$GEN_INIT`, `$GEN_END`, `ETK`, `_paras`, `G0 G53 Z`, `M58`. |
| `Cfg/NCI_ORI.CFG` | Variante original/base de plantilla NCI. |
| `Cfg/Nci.ini` y `Bin/nci.ini` | Opciones NCI32DLL y parametros del modo CNC. |
| `Cfg/Params.cfg` | Parametros de controlador/ejes usados por expresiones como `ax[2].pa[22]`. |
| `Cfg/spindles.cfg`, `Cfg/pheads.cfg`, `Cfg/oheads.cfg` | Configuracion historica de spindles/cabezales; util como contraste para offsets y registros numericos. |
| `Job/def.tlg` | Tabla operativa legacy de herramientas usada por Xilog Plus. |
| `Cfg/country.cfg`, `Cfg/Tools.ini` | Unidades/idiomas y conteo de herramientas. |

## Lecturas Documentadas En Ayuda

- `WinXiso` esta documentado como conversor `XXL <-> PGM` y puede ser llamado
  desde CAD/CAM por `WinExec` o `ShellExecute`.
- La ayuda de `WinXiso` documenta opciones para generar `.INF` con resultado
  de traduccion y `.LST` con listado del programa.
- El editor Xilog Plus documenta que los programas ISO editables usan extension
  `.CNC`; la edicion no es asistida y se hace como texto.
- El apendice del editor documenta `CNC` como formato de programas ISO,
  importacion `CNC -> PGM`, exportacion `PGM -> XXL`, gestion directa de
  programas ISO en maquinas NUM, convencion de nombres `.CNC`, `M201` antes de
  `M02`, y uso de `gendata.cfg` para programas con o sin saltos.

## Lectura Tecnica

No se encontro una ayuda de usuario que describa de punta a punta el algoritmo
exacto `PGMX/PGM -> ISO`. La documentacion encontrada explica:

- edicion de ISO `.CNC`;
- conversion historica `XXL <-> PGM`;
- importacion/exportacion desde el editor;
- gestion directa de ISO en el CNC;
- modelo XISO en esquemas XML;
- parametros y errores del entorno.

La logica real de postprocesado parece estar repartida en DLLs:

```text
XISO / PGM interpretado
  -> Pgm2Iso32.dll / PppIso.dll
  -> PostISO.dll / VtGenIso.dll / IsoTrd.dll
  -> NCI.CFG + configuracion de herramientas/cabezales/ejes
  -> ISO/CNC final
```

Para el sintetizador nuevo, esto implica que el contrato observable debe
separar:

- modelo XISO/trabajo interpretado;
- datos de pieza y toolpath del `.pgmx`;
- datos de herramienta/cabezal;
- plantillas y parametros NCI de maquina;
- reglas observadas del postprocesador.

## Impacto Para ISO State Synthesis

- `NCI.CFG` debe permanecer como fuente primaria de prologo/epilogo de maquina
  cuando una linea exista literalmente en esa plantilla.
- Los esquemas `XISO*.xsd` deben tratarse como documentacion del modelo
  intermedio XISO, no como prueba suficiente de la salida ISO final.
- Las DLLs confirman nombres de capas reales del software, pero no reemplazan
  la validacion por pares `.pgmx/.iso`.
- El `def.tlgx` embebido en cada `.pgmx` sigue siendo la fuente principal de
  herramienta para ese trabajo concreto; `Job/def.tlg`, `spindles.cfg` y
  `pheads.cfg` quedan como respaldo/contraste de configuracion instalada.
- `?%ETK[17]=257` sigue sin significado formal documentado. La exploracion
  confirma que `ETK` es usado por el postprocesador, pero no identifica el
  sentido especifico de ese indice. `NCI.CFG` y `NCI_ORI.CFG` solo documentan
  el reset comun `?%ETK[17]=0` en `$GEN_END`.

## Pendientes Derivados

- Copiar o generar un snapshot pequeno de los esquemas `XISO*.xsd` dentro de
  `iso_state_synthesis` si se decide usarlos como contrato de desarrollo.
- Usar el modelo `XISOProjectSchema` para etiquetar operaciones `H/G0/G1/G2/G3`
  contra las etapas observadas, siguiendo
  `iso_state_synthesis/contracts/xiso_intermediate_contract.md`.
- Mantener `ETK[17]` como hipotesis hasta tener una variante que cambie ese
  valor o una fuente configuracional que lo nombre.

Completado el 2026-05-06:

- `tools.pgmx_snapshot` lee `def.tlgx` directamente desde el `.pgmx` y expone
  herramientas/spindles embebidos en el JSON del snapshot.
