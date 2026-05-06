# XISO Intermediate Contract Notes

Fecha: 2026-05-06

## Fuente

Esquema instalado revisado:

- `C:\Program Files (x86)\Scm Group\Xilog Plus\Bin\XmlSchema\XISOProjectSchema\XISOProjectSchema.xsd`

El esquema no esta copiado todavia dentro de `iso_state_synthesis`. Si pasa a
ser contrato activo, conviene crear una copia controlada o una tabla derivada
pequena con los elementos usados por el modelo nuevo.

## Decision De Uso

`XISOProjectSchema` se va a tratar como vocabulario intermedio candidato, no
como especificacion final de la salida ISO.

La razon es que el esquema describe el proyecto XISO interpretado y sus
instrucciones (`H`, `B`, `G0`, `G1`, etc.), pero las lineas finales de ISO
observadas tambien dependen de `NCI.CFG`, DLLs del postprocesador y
configuracion de herramienta/cabezal.

## Mapeo Inicial

| Elemento XISO | Lectura para el modelo nuevo |
| --- | --- |
| `XISOProject` | Contenedor del programa interpretado; requiere `H` y luego instrucciones. |
| `H` | Cabecera de pieza/trabajo: `DX`, `DY`, `DZ`, `IntFLD`, unidad y opciones. |
| `CData` | Datos comunes producidos por el interprete; contiene `KeyId`, `Depth` y `Tool`. |
| `Tool` | Herramienta en la instruccion XISO: `Id`, `ToolType`, `Diameter`, `Length`. |
| `B` | Foratura/taladro con `X`, `Y`, `Z`, `E`, `V`, `S`, `T`, `G`, `D`, `a`. |
| `BR` | Taladro con eje rotante. |
| `BO` | Taladro optimizado. |
| `G0` | Inicio de fresado. |
| `G1` | Fresado lineal. |
| `G2` | Fresado circular horario. |
| `G3` | Fresado circular antihorario. |
| `Contour`, `ContourR`, `Contour3D` | Contenedores de trayectorias utiles de herramienta. |
| `PB` | Posicionamiento de barra/campo auxiliar. |

## Limites

- `XISOProjectSchema` no explica por si solo `MLV`, `SHF`, `%Or`, `ETK`, `EDK`,
  `_paras`, `M58`, `G61`, `G64`, `SYN` ni los resets finales.
- Para taladro superior minimo, `B` puede ayudar a etiquetar la etapa de
  taladro, pero la preparacion ISO observada sigue necesitando la capa de
  estado de maquina/herramienta.
- El `Tool.Length` XISO es compatible conceptualmente con la regla observada
  `toolpath_z + ToolOffsetLength`, pero la fuente primaria para el trabajo
  concreto sigue siendo el `def.tlgx` embebido en el `.pgmx`.

## Proximo Uso Practico

Cuando el modelo de estados empiece a materializarse en codigo, agregar una
tabla de vocabulario `xiso_statement` para etiquetar evidencias y etapas. No
exigir que el primer MVP emita XML XISO valido: primero debe explicar el ISO
observado por capas de estado.
