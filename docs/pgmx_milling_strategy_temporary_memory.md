# Memoria Temporal PGMX - Estrategia de Fresado

Este archivo registra hallazgos temporales sobre estrategia de fresado para
luego volcarlos, de manera ordenada, a:

- `tools/synthesize_pgmx.py`
- `docs/synthesize_pgmx_help.md`
- la documentacion publica que termine fijando la API de estrategias

## Alcance

Esta memoria se abre aparte de `docs/pgmx_temporary_memory.md` para no mezclar:

- hallazgos geometricos ya estabilizados
- reglas de taladrado ya relevadas
- decisiones nuevas sobre estrategia de fresado

En esta memoria vamos a relevar, validar y ordenar todo lo que determine como
se ejecuta un fresado una vez definida la geometria base.

## Caso En Curso

- Archivo semilla: `archive/maestro_examples/Pieza_800x760x18_EscuadradoAntihorario_E003_LineaCentral_E004.pgmx`
- Baseline usado por defecto: `tools/maestro_baselines/Pieza.xml`
- Pieza: `800 x 760 x 18`
- Origen: `5,5,9`

## Objetivo

Reconstruir paso a paso:

1. que parte de un fresado pertenece a la geometria y que parte pertenece a la estrategia
2. como serializa Maestro las variantes de herramienta, correccion, profundidad y sentido operativo
3. como modelar estrategias reutilizables en la API publica sin duplicar specs geometricas
4. que reglas y validaciones conviene fijar antes de ampliar el sintetizador

## Rondas

### Ronda 1 - Apertura de memoria

- Estado: abierta
- Archivo de referencia:
  - `archive/maestro_examples/Pieza_800x760x18_EscuadradoAntihorario_E003_LineaCentral_E004.pgmx`
- Hipotesis iniciales:
  - la geometria y la estrategia deben poder documentarse y evolucionar por separado
  - un mismo perfil de geometria puede admitir distintas estrategias de fresado
  - antes de extraer una spec publica nueva hace falta relevar que campos viven en la `Feature`, cuales en la `Operation` y cuales en el `ToolpathList`
- Primer foco de estudio:
  - escuadrado antihorario con `E003`
  - acercamiento y alejamiento lineal con multiplicador `4`
  - fresado lineal vertical centrado con `E004`
  - comportamiento pasante con `Extra = 1`
- Pendientes:
  - comparar casos manuales equivalentes re-guardados desde Maestro
  - identificar que atributos cambian al variar solo la estrategia manteniendo la misma geometria
  - decidir si la futura API necesita una `MillingStrategySpec` separada o si conviene enriquecer las specs ya existentes

### Ronda 2 - Taxonomia funcional inicial de estrategias

- Estado: completado
- Fuente:
  - definicion funcional provista por el usuario
- Observado:
  - para fresados, las estrategias posibles a relevar son:
    - `Unidireccional`
    - `Bidireccional`
    - `Helicoidal`
    - `ZigZag`
  - `Unidireccional` expone:
    - `Coneccion entre huecos`
    - `Habilitar multipaso`
    - `Profundidad hueco`
    - `Ultimo hueco`
  - `Bidireccional` expone:
    - `Habilitar multipaso`
    - `Profundidad hueco`
    - `Ultimo hueco`
  - `Helicoidal` expone:
    - `Profundidad hueco`
    - `Habilitar pasada final`
    - `Ultimo hueco`
  - `ZigZag` expone:
    - `Pasada avance`
    - `Pasada retorno`
    - `Ultimo hueco`
- Valores y defaults declarados:
  - `Unidireccional`
    - `Coneccion entre huecos = Salida a cota de seguridad` por defecto
    - alternativa: `En la pieza`
    - `Habilitar multipaso = Deshabilitado` por defecto
    - alternativa: `Habilitado`
    - `Profundidad hueco = 0` por defecto
    - `Ultimo hueco = 0` por defecto
  - `Bidireccional`
    - `Habilitar multipaso = Deshabilitado` por defecto
    - alternativa: `Habilitado`
    - `Profundidad hueco = 0` por defecto
    - `Ultimo hueco = 0` por defecto
  - `Helicoidal`
    - `Profundidad hueco = 0` por defecto
    - `Habilitar pasada final = Habilitado` por defecto
    - alternativa: `Deshabilitado`
    - `Ultimo hueco = 0` por defecto
  - `ZigZag`
    - `Pasada avance = 0` por defecto
    - `Pasada retorno = 0` por defecto
    - `Ultimo hueco = 0` por defecto
- Conclusiones provisionales para la API:
  - la futura spec publica de estrategia no deberia limitarse a un enum simple
  - cada familia de estrategia tiene parametros propios y defaults propios
  - algunos parametros son booleanos de habilitacion y otros son numericos
  - `Unidireccional` agrega un control que no aparece en las otras familias:
    `Coneccion entre huecos`
- Pendientes:
  - validar como serializa Maestro cada una de estas estrategias en `.pgmx`
  - confirmar si la ortografia exacta de UI es `Coneccion` o `Conexion`
  - mapear cada parametro a `Feature`, `Operation`, `MachiningStrategy` o `ToolpathList`
  - decidir nombres publicos estables en ingles o espanol dentro de `tools/synthesize_pgmx.py`

### Ronda 3 - Primera serializacion real de `Unidireccional`

- Estado: completado
- Archivos comparados:
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral.pgmx`
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional.pgmx`
- Contexto:
  - ambos archivos mantienen la misma pieza base y el mismo fresado lineal central
  - en Maestro solo se activo la estrategia `Unidireccional`
  - no se modificaron los parametros predeterminados de esa estrategia
- Hallazgo principal:
  - el diff XML limpio muestra exactamente un cambio funcional:
    - en la operacion con herramienta `E004`, `MachiningStrategy` deja de venir
      como `i:nil="true"` y pasa a serializarse como
      `i:type="b:UnidirectionalMilling"`
  - no cambian:
    - geometria
    - toolpaths
    - `Approach`
    - `Retract`
    - la otra operacion de escuadrado con `E003`
- Diferencia estructural exacta observada:
  - archivo sin estrategia:
    - `<MachiningStrategy i:nil="true" />`
  - archivo con estrategia:
    - `<MachiningStrategy i:type="b:UnidirectionalMilling"> ... </MachiningStrategy>`
- Campos serializados por Maestro dentro de `UnidirectionalMilling` aun sin tocar defaults:
  - `AllowMultiplePasses = false`
  - `Overlap = 0`
  - `AxialCuttingDepth = 0`
  - `AxialFinishCuttingDepth = 0`
  - `Cutmode = Climb`
  - `RadialCuttingDepth = 0`
  - `RadialFinishCuttingDepth = 0`
  - `StrokeConnectionStrategy = LiftShiftPlunge`
- Inferencias provisionales:
  - la estrategia vive en `Operation/MachiningStrategy`
  - Maestro deja defaults explicitos en XML; no los infiere por ausencia
  - `Unidireccional` afecta a la operacion seleccionada, no a toda la pieza
  - `StrokeConnectionStrategy = LiftShiftPlunge` es consistente con
    `Conexion entre huecos = Salida a cota de seguridad`
- Preguntas abiertas:
  - confirmar que `AllowMultiplePasses` corresponde exactamente a
    `Habilitar multipaso`
  - confirmar si `AxialCuttingDepth` y `AxialFinishCuttingDepth` son el mapeo de
    `Profundidad hueco` y `Ultimo hueco`
  - explicar por que Maestro serializa tambien `Overlap`,
    `RadialCuttingDepth`, `RadialFinishCuttingDepth` y `Cutmode` aunque la UI
    relevada para este caso no los destaque como parametros principales
  - relevar la variante `Conexion entre huecos = En la pieza` para descubrir el
    valor alternativo de `StrokeConnectionStrategy`

### Ronda 4 - `Unidireccional` con `Conexion entre huecos = En la pieza`

- Estado: completado
- Archivos comparados:
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional.pgmx`
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_EnLaPieza.pgmx`
- Contexto:
  - ambos archivos mantienen la misma estrategia `Unidireccional`
  - no se cambiaron los demas parametros
  - solo se modifico `Conexion entre huecos`
- Hallazgo principal:
  - el diff XML exacto muestra un unico cambio funcional:
    - `StrokeConnectionStrategy` pasa de `LiftShiftPlunge` a `Straghtline`
- Conclusiones provisionales:
  - el parametro de UI `Conexion entre huecos` mapea a
    `Operation/MachiningStrategy/StrokeConnectionStrategy`
  - con la opcion por defecto `Salida a cota de seguridad`, Maestro serializa:
    - `StrokeConnectionStrategy = LiftShiftPlunge`
  - con la opcion `En la pieza`, Maestro serializa:
    - `StrokeConnectionStrategy = Straghtline`
  - el valor alternativo observado queda escrito exactamente como
    `Straghtline`, incluyendo esa ortografia
  - no cambian:
    - geometria
    - toolpaths
    - `Approach`
    - `Retract`
    - ni ningun otro campo de `UnidirectionalMilling`
- Implicacion para la futura API:
  - `Unidireccional` necesita un parametro publico especifico para la
    conexion entre pasadas o entre huecos
  - ese parametro no debe inferirse desde otra parte de la operacion
- Pendientes:
  - decidir un nombre publico estable, por ejemplo
    `stroke_connection_strategy` o `between_strokes_connection`
  - relevar `Habilitar multipaso` para confirmar el mapeo de
    `AllowMultiplePasses`

### Ronda 5 - Convencion de nombres para variantes de estrategia

- Estado: completado
- Convencion declarada por el usuario:
  - los nombres de archivo pasan a describir las opciones activadas
  - ejemplo:
    - `SalidaCota`
    - `EnLaPieza`
    - `MP_Hab`
    - `PH0`
    - `UH0`
- Observado:
  - esta convencion es util como indice de relevamiento
  - pero el nombre externo del `.pgmx` no garantiza que los nombres internos del
    contenedor coincidan
  - ejemplo observado:
    - `Pieza_800x760x18_LineaCentral_Unidireccional_SalidaCota.pgmx`
      contiene internamente:
      - `Pieza_800x760x18_LineaCentral_Unidireccional.xml`
      - `Pieza_800x760x18_LineaCentral_Unidireccional.epl`
  - conclusion:
    - para validar hallazgos hay que confiar en el XML interno y no solo en el
      nombre del archivo

### Ronda 6 - `Habilitar multipaso` con `PH = 0` y `UH = 0`

- Estado: completado
- Archivos comparados:
  - rama `EnLaPieza`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_EnLaPieza.pgmx`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_EnLaPieza_MP_Hab_PH0_UH0.pgmx`
  - rama `SalidaCota`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_SalidaCota.pgmx`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_SalidaCota_MP_Hab_PH0_UH0.pgmx`
- Hallazgo confirmado en la rama `EnLaPieza`:
  - el unico cambio funcional es:
    - `AllowMultiplePasses: false -> true`
  - permanecen en `0`:
    - `AxialCuttingDepth`
    - `AxialFinishCuttingDepth`
  - se conserva:
    - `StrokeConnectionStrategy = Straghtline`
- Hallazgo confirmado en la rama `SalidaCota`:
  - el unico cambio funcional es:
    - `AllowMultiplePasses: false -> true`
  - permanecen en `0`:
    - `AxialCuttingDepth`
    - `AxialFinishCuttingDepth`
  - se conserva:
    - `StrokeConnectionStrategy = LiftShiftPlunge`
- Conclusiones provisionales:
  - `Habilitar multipaso` mapea de forma directa a `AllowMultiplePasses`
  - con `PH = 0` y `UH = 0`, Maestro sigue serializando esos valores de forma
    explicita
  - `PH` y `UH` todavia no cambian por si solos mientras queden en `0`
- Implicacion practica:
  - ya quedaron validadas las dos ramas limpias:
    - `SalidaCota + MP_Hab + PH0 + UH0`
    - `EnLaPieza + MP_Hab + PH0 + UH0`
  - `MP_Hab` puede relevarse de forma independiente del modo de conexion
- Pendientes:
  - relevar despues una variante con `PH` y/o `UH` distintos de `0`

### Ronda 7 - `Profundidad hueco = 5` con `UH = 0`

- Estado: completado
- Archivos comparados:
  - rama `SalidaCota`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_SalidaCota_MP_Hab_PH0_UH0.pgmx`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_SalidaCota_MP_Hab_PH5_UH0.pgmx`
  - rama `EnLaPieza`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_EnLaPieza_MP_Hab_PH0_UH0.pgmx`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_EnLaPieza_MP_Hab_PH5_UH0.pgmx`
- Hallazgo principal confirmado en ambas ramas:
  - `Profundidad hueco = 5` mapea a:
    - `AxialCuttingDepth: 0 -> 5`
  - `AxialFinishCuttingDepth` permanece en `0`
  - `AllowMultiplePasses` permanece en `true`
  - `StrokeConnectionStrategy` conserva el valor de cada rama:
    - `LiftShiftPlunge` en `SalidaCota`
    - `Straghtline` en `EnLaPieza`
- Cambios operativos adicionales observados en ambas ramas:
  - `ActivateCNCCorrection` pasa de `true` a `false`
  - el `Approach` baja desde `z = 39` a `z = 25`
  - el `TrajectoryPath` deja de ser `GeomTrimmedCurve` y pasa a
    `GeomCompositeCurve`
  - el `TrajectoryPath` ya no representa una sola pasada final, sino una
    secuencia de pasadas escalonadas
- Patron observado en la secuencia de profundidades:
  - la trayectoria compuesta evidencia pasadas intermedias a profundidades
    separadas por `5`
  - para este caso pasante con `Extra = 1`, aparecen niveles compatibles con:
    - `13`
    - `8`
    - `3`
    - `-1`
  - esto es consistente con una profundizacion axial en pasos de `5` hasta la
    profundidad final
- Diferencia entre ramas en el toolpath multipaso:
  - `SalidaCota`
    - el `TrajectoryPath` incluye segmentos verticales de salida/entrada entre
      pasadas
    - aparecen `OperationAttribute` de tipo `RapidSpeedAttribute`
    - el comportamiento observado es coherente con levantar, desplazar y volver
      a entrar entre pasadas
  - `EnLaPieza`
    - el `TrajectoryPath` tambien se vuelve compuesto, pero sin
      `OperationAttribute` observables en este caso
    - la secuencia de segmentos queda serializada como movimiento continuo dentro
      de la pieza
- Conclusiones provisionales:
  - `PH` no solo cambia un campo de estrategia; tambien obliga a Maestro a
    recalcular el toolpath efectivo
  - la futura API no puede tratar `AxialCuttingDepth` como un metadato aislado:
    al sintetizarlo hay que regenerar el `TrajectoryPath` multipaso compatible
  - la estrategia de conexion entre pasadas sigue afectando la forma del
    `ToolpathList` incluso cuando `PH` ya es no nulo
- Pendientes:
  - relevar `Ultimo hueco` con un valor distinto de `0`
  - confirmar si `ActivateCNCCorrection = false` es una regla general del
    multipaso axial o una consecuencia particular de este tipo de fresado

### Ronda 8 - `Ultimo hueco = 10` con `PH = 5`

- Estado: completado
- Archivos comparados:
  - rama `SalidaCota`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_SalidaCota_MP_Hab_PH5_UH0.pgmx`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_SalidaCota_MP_Hab_PH5_UH10.pgmx`
  - rama `EnLaPieza`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_EnLaPieza_MP_Hab_PH5_UH0.pgmx`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_EnLaPieza_MP_Hab_PH5_UH10.pgmx`
- Hallazgo principal confirmado en ambas ramas:
  - `Ultimo hueco = 10` mapea a:
    - `AxialFinishCuttingDepth: 0 -> 10`
  - se conservan:
    - `AllowMultiplePasses = true`
    - `AxialCuttingDepth = 5`
    - `ActivateCNCCorrection = false`
    - `StrokeConnectionStrategy` propio de cada rama
- Cambios operativos adicionales observados en ambas ramas:
  - el `TrajectoryPath` multipaso sigue siendo `GeomCompositeCurve`
  - pero se simplifica:
    - pasa de `13` segmentos serializados a `9`
  - esto indica que Maestro recompone la estrategia de capas cuando existe una
    pasada final axial distinta de `0`
- Patron observado:
  - con `PH = 5` y `UH = 0`, el multipaso llegaba por capas hasta la profundidad
    final a traves de mas niveles intermedios
  - con `PH = 5` y `UH = 10`, desaparece al menos una capa intermedia y queda una
    secuencia mas corta antes de la pasada final
  - la evidencia mas clara es que el nivel asociado a la capa intermedia mas
    profunda deja de aparecer en la serializacion observada
- Diferencia entre ramas en el toolpath final:
  - `SalidaCota`
    - los `RapidSpeedAttribute` asociados al `TrajectoryPath` bajan de `3` a `2`
    - sigue habiendo levantadas y reconexiones fuera de la pieza entre capas
  - `EnLaPieza`
    - no aparecen `OperationAttribute` en este caso, igual que en `UH = 0`
    - la secuencia interna tambien se reduce de `13` a `9` miembros
- Conclusiones provisionales:
  - `UH` no es solo un campo decorativo: obliga a Maestro a recalcular el
    escalonado axial del `TrajectoryPath`
  - la futura API debe tratar `AxialCuttingDepth` y `AxialFinishCuttingDepth`
    como un par acoplado que determina la descomposicion real de pasadas
  - `UH` afecta tanto la cantidad de capas como la estructura de reconexion entre
    capas en la rama `SalidaCota`
- Pendientes:
  - relevar si existe algun umbral o validacion entre `PH`, `UH` y la profundidad
    total del mecanizado
  - decidir como expresar esta logica en una futura spec publica sin prometer
    una reconstruccion manual del toolpath mas alla de lo que Maestro ya observo

### Ronda 9 - `Profundidad hueco = 15` con `UH = 10`

- Estado: completado
- Archivos comparados:
  - rama `SalidaCota`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_SalidaCota_MP_Hab_PH5_UH10.pgmx`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_SalidaCota_MP_Hab_PH15_UH10.pgmx`
  - rama `EnLaPieza`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_EnLaPieza_MP_Hab_PH5_UH10.pgmx`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_EnLaPieza_MP_Hab_PH15_UH10.pgmx`
- Hallazgo principal confirmado en ambas ramas:
  - `Profundidad hueco = 15` mapea a:
    - `AxialCuttingDepth: 5 -> 15`
  - se conservan:
    - `AxialFinishCuttingDepth = 10`
    - `AllowMultiplePasses = true`
    - `ActivateCNCCorrection = false`
    - `StrokeConnectionStrategy` propio de cada rama
- Cambios operativos adicionales observados en ambas ramas:
  - el `Approach` sube de `z = 25` a `z = 29`
  - el `TrajectoryPath` multipaso sigue siendo `GeomCompositeCurve`
  - pero vuelve a simplificarse:
    - pasa de `9` segmentos serializados a `5`
- Patron observado:
  - con `PH = 5` y `UH = 10`, la trayectoria todavia incluia una capa intermedia
    adicional antes de la pasada final
  - con `PH = 15` y `UH = 10`, esa capa desaparece y queda una secuencia mucho
    mas corta
  - la evidencia observable es que la serializacion ya no incluye el bloque
    asociado al nivel intermedio superior que antes aparecia como primer tramo de
    desbaste
- Diferencia entre ramas:
  - `SalidaCota`
    - los `RapidSpeedAttribute` bajan de `2` a `1`
    - sigue quedando una reconexion rapida entre capas fuera de la pieza
  - `EnLaPieza`
    - sigue sin `OperationAttribute`
    - la reduccion a `5` segmentos ocurre igual, pero sin marcadores de rapido
- Conclusiones provisionales:
  - al crecer `AxialCuttingDepth`, Maestro reduce la cantidad de niveles de
    desbaste realmente necesarios
  - el par `PH` + `UH` determina la cardinalidad del `TrajectoryPath`
    multipaso, no solo sus profundidades numericas
  - la estrategia de conexion sigue modificando el mismo patron base, pero con
    distinta cantidad de segmentos rapidos
- Pendientes:
  - relevar un caso donde `PH` sea tan grande que practicamente no haga falta
    mas de una pasada de desbaste
  - confirmar si existe una relacion sistematica entre el `Approach` inicial y la
    primera profundidad efectiva de desbaste

### Ronda 10 - `Profundidad hueco = 18` con `UH = 10`

- Estado: completado
- Archivos comparados:
  - rama `SalidaCota`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_SalidaCota_MP_Hab_PH15_UH10.pgmx`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_SalidaCota_MP_Hab_PH18_UH10.pgmx`
  - rama `EnLaPieza`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_EnLaPieza_MP_Hab_PH15_UH10.pgmx`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_EnLaPieza_MP_Hab_PH18_UH10.pgmx`
- Hallazgo principal confirmado en ambas ramas:
  - `Profundidad hueco = 18` mapea a:
    - `AxialCuttingDepth: 15 -> 18`
  - se conservan:
    - `AxialFinishCuttingDepth = 10`
    - `AllowMultiplePasses = true`
    - `ActivateCNCCorrection = false`
    - `StrokeConnectionStrategy` propio de cada rama
- Hallazgo operativo importante:
  - mas alla de `AxialCuttingDepth`, no cambia la forma funcional del mecanizado
  - el `Approach` sigue en `z = 29`
  - el `TrajectoryPath` sigue con la misma estructura de `5` segmentos
  - en `SalidaCota`, sigue habiendo `1` `RapidSpeedAttribute`
  - en `EnLaPieza`, sigue sin `OperationAttribute`
- Verificacion estructural:
  - al normalizar IDs internos de `ElementKey` y `_serializingKeys`, el
    `ToolpathList` de `PH15_UH10` y `PH18_UH10` queda identico en cada rama
  - esto indica que la diferencia adicional de `PH` ya no altera el toolpath
    efectivo observado
- Conclusiones provisionales:
  - para este caso concreto, `PH = 15` ya habia alcanzado el mismo regimen
    operativo que `PH = 18`
  - una vez superado cierto umbral, aumentar `AxialCuttingDepth` puede dejar de
    producir cambios reales en el `TrajectoryPath`
  - ese umbral parece depender de la profundidad total restante luego de reservar
    la pasada final de `UH = 10`
- Implicacion para la futura API:
  - no conviene prometer una relacion lineal entre `PH` y cantidad de pasadas
  - hay que contemplar saturacion: distintos valores de `PH` pueden colapsar al
    mismo toolpath efectivo
- Pendientes:
  - relevar si el mismo efecto de saturacion aparece con otros valores de `UH`
  - decidir si en la documentacion publica conviene hablar de
    `AxialCuttingDepth solicitado` frente a `toolpath efectivo resultante`

### Ronda 11 - `Ultimo hueco = 5` con `PH = 18`

- Estado: completado
- Archivos comparados:
  - rama `SalidaCota`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_SalidaCota_MP_Hab_PH18_UH10.pgmx`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_SalidaCota_MP_Hab_PH18_UH5.pgmx`
  - rama `EnLaPieza`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_EnLaPieza_MP_Hab_PH18_UH10.pgmx`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_EnLaPieza_MP_Hab_PH18_UH5.pgmx`
- Hallazgo principal confirmado en ambas ramas:
  - `Ultimo hueco = 5` mapea a:
    - `AxialFinishCuttingDepth: 10 -> 5`
  - se conservan:
    - `AxialCuttingDepth = 18`
    - `AllowMultiplePasses = true`
    - `ActivateCNCCorrection = false`
    - `StrokeConnectionStrategy` propio de cada rama
- Cambios operativos observados en ambas ramas:
  - el `Approach` sube de `z = 29` a `z = 34`
  - el `TrajectoryPath` mantiene `5` segmentos, o sea no cambia la cardinalidad
  - pero si cambian los niveles Z efectivos de la trayectoria
- Patron observado en `SalidaCota`:
  - cambian los dos primeros miembros de la trayectoria:
    - `9 -> 4`
    - `29 -> 34`
  - los miembros posteriores permanecen iguales
  - esto es consistente con una bajada de la pasada final, manteniendo la
    reconexion por cota de seguridad
- Patron observado en `EnLaPieza`:
  - cambian los cuatro primeros miembros de la trayectoria:
    - `9 -> 4`
    - `19 -> 14`
    - `20 -> 15`
  - la trayectoria continua dentro de la pieza se recompone mas profundamente que
    en la rama `SalidaCota`
- Conclusiones provisionales:
  - aun cuando `PH = 18` ya habia saturado el patron de desbaste, `UH` sigue
    modificando el toolpath efectivo
  - `UH` no solo cambia el espesor de la pasada final; tambien desplaza los
    niveles Z visibles en `Approach` y en la trayectoria compuesta
  - la sensibilidad a `UH` es mayor en la rama `EnLaPieza`, donde la continuidad
    interna obliga a reacomodar mas segmentos
- Implicacion para la futura API:
  - la saturacion observada para `PH` no debe extrapolarse a `UH`
  - `AxialFinishCuttingDepth` sigue siendo estructuralmente relevante incluso
    cuando `AxialCuttingDepth` ya no cambia la cardinalidad del toolpath
- Pendientes:
  - relevar una combinacion donde `UH` sea muy pequeno o muy grande respecto de
    la profundidad final restante
  - confirmar si existe una formula simple entre profundidad final objetivo y el
    `Approach` inicial observado

### Ronda 12 - `Ultimo hueco = 2` con `PH = 0`

- Estado: completado
- Archivos comparados:
  - rama `SalidaCota`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_SalidaCota_MP_Hab_PH0_UH0.pgmx`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_SalidaCota_MP_Hab_PH0_UH2.pgmx`
  - rama `EnLaPieza`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_EnLaPieza_MP_Hab_PH0_UH0.pgmx`
    - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_EnLaPieza_MP_Hab_PH0_UH2.pgmx`
- Hallazgo principal confirmado en ambas ramas:
  - `Ultimo hueco = 2` mapea a:
    - `AxialFinishCuttingDepth: 0 -> 2`
  - se conservan:
    - `AxialCuttingDepth = 0`
    - `AllowMultiplePasses = true`
    - `StrokeConnectionStrategy` propio de cada rama
- Hallazgo operativo importante:
  - aun con `PH = 0`, Maestro deja de tratar la trayectoria como pasada unica
  - `ActivateCNCCorrection` pasa de `true` a `false`
  - el `Approach` baja de `z = 39` a `z = 37`
  - el `TrajectoryPath` pasa de `GeomTrimmedCurve` a `GeomCompositeCurve`
  - la trayectoria resultante queda con `5` segmentos en ambas ramas
- Patron observado en `SalidaCota`:
  - aparece una pasada efectiva a `z = 1`
  - la reconexion se hace por cota alta, con `1` `RapidSpeedAttribute`
  - la secuencia observada es:
    - corte a `z = 1`
    - reconexion por `z = 37/39`
    - pasada final a `z = -1`
- Patron observado en `EnLaPieza`:
  - tambien aparece una pasada efectiva a `z = 1`
  - la continuidad interna agrega niveles:
    - `11`
    - `12`
  - no aparecen `OperationAttribute`
- Conclusiones provisionales:
  - `UH` por si solo ya alcanza para disparar un regimen multipaso, incluso cuando
    `PH = 0`
  - esto sugiere que Maestro interpreta `AxialFinishCuttingDepth` como una capa
    final reservada sobre la cual igual necesita construir un desbaste previo
  - por lo tanto, `PH = 0` no significa necesariamente `sin escalonado axial`
    si `UH` es no nulo
- Implicacion para la futura API:
  - la combinacion `PH = 0, UH > 0` debe considerarse valida y con semantica
    propia
  - no se puede modelar `UH` solo como refinamiento opcional de un `PH` ya activo
- Pendientes:
  - relevar si existe algun caso en el que `PH = 0` y `UH` muy grande vuelva a
    colapsar a una sola pasada efectiva
  - contrastar este comportamiento con otra estrategia distinta de
    `Unidireccional`

### Ronda 13 - `Unidireccional` + `Acercamiento lineal 2 en bajada`

- Estado: completado
- Archivos comparados:
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_SalidaCota_MP_Hab_PH5_UH0.pgmx`
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_SalidaCota_MP_Hab_PH5_UH0_Ac_L2B.pgmx`
- Hallazgo principal:
  - activar `Acercamiento lineal 2 en bajada` no cambia la estrategia
    `Unidireccional` ni el multipaso axial
  - los cambios funcionales caen en:
    - `Operation/Approach`
    - `ToolpathList/Toolpath[Type=Approach]`
- Mapeo observado en `Approach`:
  - `IsEnabled: false -> true`
  - `RadiusMultiplier: 1.2 -> 2`
  - `Speed: 0 -> -1`
  - se conservan:
    - `ApproachType = Line`
    - `ApproachMode = Down`
    - `ApproachArcSide = Automatic`
- Efecto observado en el `Toolpath` de `Approach`:
  - deja de ser una bajada vertical simple
  - pasa a una entrada lineal inclinada serializada como:
    - `8 0 25.317977802344327`
    - `1 400 -4 38 0 0.15799050110667287 -0.98744063191670539`
- Efecto sobre el `TrajectoryPath`:
  - al normalizar IDs, la trayectoria multipaso queda funcionalmente igual al
    caso base
  - se regeneran claves internas (`_serializingKeys`, `ElementKey`), pero no
    cambian los miembros serializados del desbaste/pasada final
- Conclusiones provisionales:
  - `Approach` se compone por fuera de la estrategia axial
  - el multipaso `PH5_UH0` no se reestructura por habilitar solo el
    acercamiento; se mantiene el mismo `TrajectoryPath`
  - la futura API puede modelar `Approach` como capa transversal reutilizable
    sobre una estrategia de fresado ya resuelta

### Ronda 14 - `Unidireccional` + `Acercamiento lineal 2 en bajada` + `Alejamiento lineal 2 en subida`

- Estado: completado
- Archivos comparados:
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_SalidaCota_MP_Hab_PH5_UH0_Ac_L2B.pgmx`
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_SalidaCota_MP_Hab_PH5_UH0_Ac_L2B_Al_L2S.pgmx`
- Hallazgo principal:
  - agregar `Alejamiento lineal 2 en subida` tampoco cambia la estrategia
    `Unidireccional` ni el `TrajectoryPath`
  - los cambios funcionales caen en:
    - `Operation/Retract`
    - `ToolpathList/Toolpath[Type=Lift]`
- Mapeo observado en `Retract`:
  - `IsEnabled: false -> true`
  - `RadiusMultiplier: 1.2 -> 2`
  - `Speed: 0 -> -1`
  - se conservan:
    - `RetractType = Line`
    - `RetractMode = Up`
    - `RetractArcSide = Automatic`
    - `OverLap = 0`
- Efecto observado en el `Toolpath` de `Lift`:
  - deja de ser una salida vertical simple
  - pasa a una salida lineal inclinada serializada como:
    - `8 0 39.204591567825318`
    - `1 400 760 -1 0 0.10202886549856947 0.99478143861105239`
- Efecto sobre el `TrajectoryPath`:
  - los miembros serializados del multipaso permanecen iguales
  - solo se regeneran IDs internos del `ToolpathList`
- Conclusiones provisionales:
  - `Approach` y `Retract` parecen ser ortogonales a `Unidireccional`
  - al menos en este caso, Maestro no recompone la estrategia axial por
    habilitar entrada/salida lineales; solo recompone los toolpaths de entrada y
    salida
- Pendientes:
  - relevar el mismo cruce pero sobre la rama `EnLaPieza`
  - relevar si este desacople sigue valiendo con `UH` no nulo

### Ronda 15 - `Unidireccional PH5_UH10` + `Acercamiento lineal 2 en bajada`

- Estado: completado
- Archivos comparados:
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_SalidaCota_MP_Hab_PH5_UH10.pgmx`
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_SalidaCota_MP_Hab_PH5_UH10_Ac_L2B.pgmx`
- Hallazgo principal:
  - el cruce con `UH = 10` repite el mismo patron observado en `UH = 0`
  - activar `Acercamiento lineal 2 en bajada` no cambia la estrategia axial ni
    la trayectoria multipaso interna
  - los cambios funcionales caen en:
    - `Operation/Approach`
    - `ToolpathList/Toolpath[Type=Approach]`
- Mapeo observado en `Approach`:
  - `IsEnabled: false -> true`
  - `RadiusMultiplier: 1.2 -> 2`
  - `Speed: 0 -> -1`
  - se conservan:
    - `ApproachType = Line`
    - `ApproachMode = Down`
    - `ApproachArcSide = Automatic`
- Efecto observado en el `Toolpath` de `Approach`:
  - vuelve a aparecer la misma entrada lineal inclinada ya relevada:
    - `8 0 25.317977802344327`
    - `1 400 -4 38 0 0.15799050110667287 -0.98744063191670539`
- Efecto sobre el `TrajectoryPath`:
  - los `9` miembros serializados del multipaso `PH5_UH10` permanecen iguales
  - solo se regeneran IDs internos asociados a la curva compuesta y sus
    atributos rapidos
- Conclusiones provisionales:
  - el desacople entre `Approach` y estrategia axial tambien vale con `UH` no
    nulo
  - el `Approach` no recompone las capas internas del `TrajectoryPath`

### Ronda 16 - `Unidireccional PH5_UH10` + `Acercamiento lineal 2 en bajada` + `Alejamiento lineal 2 en subida`

- Estado: completado
- Archivos comparados:
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_SalidaCota_MP_Hab_PH5_UH10_Ac_L2B.pgmx`
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Unidireccional_SalidaCota_MP_Hab_PH5_UH10_Ac_L2B_Al_L2S.pgmx`
- Hallazgo principal:
  - agregar `Alejamiento lineal 2 en subida` mantiene el mismo patron observado
    en `UH = 0`
  - la estrategia axial y los `9` miembros del `TrajectoryPath` permanecen
    iguales
  - los cambios funcionales caen en:
    - `Operation/Retract`
    - `ToolpathList/Toolpath[Type=Lift]`
- Mapeo observado en `Retract`:
  - `IsEnabled: false -> true`
  - `RadiusMultiplier: 1.2 -> 2`
  - `Speed: 0 -> -1`
  - se conservan:
    - `RetractType = Line`
    - `RetractMode = Up`
    - `RetractArcSide = Automatic`
    - `OverLap = 0`
- Efecto observado en el `Toolpath` de `Lift`:
  - vuelve a aparecer la misma salida lineal inclinada ya observada:
    - `8 0 39.204591567825318`
    - `1 400 760 -1 0 0.10202886549856947 0.99478143861105239`
- Conclusiones provisionales:
  - el desacople entre `Retract` y estrategia axial tambien vale cuando `UH`
    es no nulo
  - para la familia `Unidireccional` relevada hasta ahora, `Approach` y
    `Retract` siguen comportandose como capas ortogonales a `MachiningStrategy`
- Pendientes:
  - contrastar este mismo cruce sobre la rama `EnLaPieza`
  - pasar luego a `Bidireccional`
