# pgmx/docs — Manual de Referencia SCM Group

Documentación extraída de los archivos CHM de SCM Group para uso interno
en el desarrollo del sintetizador ProdAction.

## Fuentes

| Directorio | Origen | Idioma | Páginas |
|---|---|---|---|
| [xilog_plus_pgm/](xilog_plus_pgm/) | `Xilog_Plus_Editor.chm` | Español | 45 |
| [maestro_scripting/](maestro_scripting/) | `XilogMaestroScripting.chm` | Inglés | 94 relevantes |

## Nota de encoding

El contenido de `xilog_plus_pgm/` fue extraído vía WebBrowser COM
(`mk:@MSITStore:`). El protocolo no envía headers `Content-Type`, lo que
causa que el browser detecte mal el charset antes de procesar el
`<meta charset="windows-1252">`. Los caracteres acentuados del español
(á, é, í, ó, ú, ñ, ü) aparecen como `?` (U+FFFD) en las secciones
descriptivas. Los nombres de instrucciones, parámetros y ejemplos de
código son ASCII puro y están perfectamente legibles.

El contenido de `maestro_scripting/` es todo inglés y no tiene problemas
de encoding.

## Uso recomendado

### Para entender los parámetros de cada operación de maquinado

- [maestro_scripting/01_create_operations.md](maestro_scripting/01_create_operations.md)
  — `CreateDrill`, `CreateSlot`, `CreateIso`, `CreatePark`, `CreateContourPocket`, etc.
  con firmas C# completas.

### Para entender el lenguaje PGM (instrucciones de Xilog Plus)

- [xilog_plus_pgm/05_2_instrucciones_basicas.md](xilog_plus_pgm/05_2_instrucciones_basicas.md)
  — Instrucciones básicas: G0, G1, G2, G3, XG0, SET, MSG, ISO, etc.
- [xilog_plus_pgm/05_3_instrucciones_completas.md](xilog_plus_pgm/05_3_instrucciones_completas.md)
  — Instrucciones completas (modo gráfico)
- [xilog_plus_pgm/05_1_header.md](xilog_plus_pgm/05_1_header.md)
  — Parámetros del encabezamiento (DX, DY, DZ, V, T, BX, BY, BZ...)

### Para entender el plano motorizado (PB)

- [xilog_plus_pgm/09_1_instruccion_pb.md](xilog_plus_pgm/09_1_instruccion_pb.md)
- [xilog_plus_pgm/09_13_reglas_estacionamiento.md](xilog_plus_pgm/09_13_reglas_estacionamiento.md)
