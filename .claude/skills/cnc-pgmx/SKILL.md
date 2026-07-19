---
name: cnc-pgmx
description: Work with CNC modeling and programming files centered on SCM/Xilog/Maestro PGMX and the ProdAction `pgmx` package. Use when the user asks to understand, read, inspect, synthesize, modify, validate, or generate reviewable CNC/PGMX/PGM machining artifacts, especially from natural-language piece requirements, existing `.pgmx` files, Xilog Plus PGM instructions, Maestro scripting operations, pocket milling/vaciado, drilling, phases/workplans, machine operations such as `Xn` and `Xmsg`, or ProdAction's PGMX snapshot/synthesis code.
---

# CNC PGMX

## Regla De Seguridad

Tratar toda salida CNC como **artefacto candidato para revision**, no como listo para ejecutar.

- Generar archivos para abrir, revisar, simular o comparar en software especifico.
- No afirmar que un programa esta listo para maquina sin validacion del usuario en el software/control real.
- Marcar supuestos sobre material, herramienta, cero pieza, orientacion, unidades, espesores, velocidades, profundidades y postprocesador.
- Si falta informacion critica, preguntar antes de producir codigo CNC ejecutable.

## Flujo Base

1. Identificar el objetivo: leer, explicar, convertir, modificar, sintetizar o validar.
2. Localizar el repo ProdAction:
   - Preferir copia local indicada por Nora: `C:\Dev\Repositorios\ProdAction`.
   - En entornos Unix/workspace, buscar una copia local razonable antes de usar GitHub.
   - Si no hay copia local, usar `https://github.com/ftelleria77/ProdAction/tree/main/pgmx` como fuente.
3. Leer primero la orientacion en `references/prodaction-pgmx-map.md`.
4. Segun la tarea, abrir solo las fuentes necesarias de ProdAction:
   - `pgmx/docs/README.md` para mapa documental.
   - `pgmx/docs/xilog_plus_pgm/` para lenguaje PGM/Xilog Plus.
   - `pgmx/docs/maestro_scripting/` para operaciones Maestro/C#.
   - `pgmx/snapshot.py` y `pgmx/adapters.py` para lectura/adaptacion de `.pgmx` existentes.
   - `pgmx/synthesis/` para generacion productiva.
   - `pgmx/machining_lab/` para evidencia experimental no productiva.
5. Producir una salida con:
   - Artefactos generados o cambios propuestos.
   - Supuestos tecnicos.
   - Validaciones realizadas.
   - Pasos de revision en software CNC/CAM.
   - Advertencias de ejecucion real.

## Cuando El Usuario Pide Una Pieza Nueva

Convertir el pedido natural a una especificacion antes de generar:

- Dimensiones de pieza: largo, ancho, espesor, unidades.
- Sistema de coordenadas y origen.
- Cara/superficie de trabajo.
- Operaciones: corte, ranura, taladro, bolsillo/vaciado, contorno, mensaje, cambio de herramienta, fases.
- Herramientas: diametro, tipo, numero, spindle/electromandril, velocidades si existen.
- Profundidades y pasadas.
- Formato objetivo: `.pgmx`, PGM/Xilog, DXF, STEP u otro.
- Software donde se va a revisar.

Si el usuario no especifica formato, proponer empezar por un archivo **revisable** en PGMX/PGM o por el formato que ya soporte ProdAction para ese caso.

## Contratos Iniciales Conocidos

- `pgmx.docs` contiene documentacion extraida de manuales SCM Group: Xilog Plus PGM en espanol y Maestro scripting en ingles.
- `xilog_plus_pgm` sirve para entender encabezado PGM e instrucciones como `G0`, `G1`, `G2`, `G3`, `XG0`, `SET`, `MSG`, `ISO` y PB.
- `maestro_scripting` sirve para firmas y parametros de operaciones como `CreateDrill`, `CreateSlot`, `CreateIso`, `CreatePark` y `CreateContourPocket`.
- `pgmx.snapshot` y `pgmx.adapters` son la puerta de lectura/adaptacion de `.pgmx` existentes.
- `pgmx.synthesis` contiene el camino productivo de generacion; sus subpaquetes incluyen `common`, `drilling` y `milling`.
- `pgmx.machining_lab` es evidencia y laboratorio. No tratarlo como contrato productivo hasta migrarlo a `pgmx.synthesis` con tests.
- El laboratorio vigente de operaciones de maquina cubre flujo de programa, fases/workplans, `Xn` y `Xmsg`.

## Manejo De Evidencia

- No inventar sintaxis PGMX si ProdAction tiene ejemplos o contratos que revisar.
- Preferir copiar la estructura de archivos PGMX existentes y modificar solo lo necesario.
- Cuando una regla venga de `machining_lab`, decir que es evidencia/laboratorio, no contrato final.
- Cuando una regla venga de `docs/`, distinguir manual SCM de comportamiento observado en archivos reales.
- Registrar hallazgos estables en la memoria del proyecto o en la skill solo si son reutilizables.

## Validacion Recomendada

Segun el entorno disponible:

- Ejecutar tests focales de ProdAction si se modifica `pgmx`.
- Ejecutar `python -m compileall pgmx` si se toca codigo Python.
- Abrir/simular el archivo generado en el software especifico antes de maquina.
- Comparar snapshots antes/despues cuando se modifica un `.pgmx` existente.

## Limites

- No prometer compatibilidad universal CNC: esta skill empieza centrada en SCM/Xilog/Maestro/PGMX y ProdAction.
- No generar instrucciones de maquina finales sin datos de herramienta, material, origen, sujecion y revision humana.
- No mezclar memoria global de Nora con detalles tecnicos largos: moverlos a referencias de esta skill o al repo ProdAction.
