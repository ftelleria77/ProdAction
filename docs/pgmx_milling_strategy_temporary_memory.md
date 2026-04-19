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

### Ronda 17 - `Unidireccional` con correccion `Central`, `Derecha` e `Izquierda`

- Estado: completado
- Archivos comparados:
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Central_Unidireccional_SalidaCota_MP_Hab_PH0_UH0.pgmx`
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Derecha_Unidireccional_SalidaCota_MP_Hab_PH0_UH0.pgmx`
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Izquierda_Unidireccional_SalidaCota_MP_Hab_PH0_UH0.pgmx`
- Hallazgo principal:
  - la correccion lateral no cambia la estrategia `Unidireccional`
  - tampoco cambia `AllowMultiplePasses`, `PH`, `UH` ni
    `StrokeConnectionStrategy`
  - los cambios funcionales observados quedan acotados a:
    - `Feature/SideOfFeature`
    - desplazamiento lateral del `ToolpathList`
- Mapeo observado en la feature:
  - `Central` serializa:
    - `SideOfFeature = Center`
  - `Derecha` serializa:
    - `SideOfFeature = Right`
  - `Izquierda` serializa:
    - `SideOfFeature = Left`
- Mapeo observado en el `ToolpathList`:
  - caso `Central`
    - los tres toolpaths (`Approach`, `TrajectoryPath`, `Lift`) quedan sobre
      `x = 400`
  - caso `Derecha`
    - esos tres toolpaths pasan a `x = 402`
  - caso `Izquierda`
    - esos tres toolpaths pasan a `x = 398`
- Observacion geometrica:
  - el corrimiento observado es de `2 mm` respecto del eje central
  - esto es consistente con media herramienta para `E004 = 4 mm`
  - por lo tanto, la correccion lateral parece expresarse como un offset real del
    toolpath efectivo, no solo como una bandera semantica
- Lo que no cambia:
  - `ActivateCNCCorrection` sigue en `true` en los tres casos
  - la estructura sigue siendo:
    - `Approach = GeomTrimmedCurve`
    - `TrajectoryPath = GeomTrimmedCurve`
    - `Lift = GeomTrimmedCurve`
  - la estrategia sigue siendo:
    - `AllowMultiplePasses = true`
    - `AxialCuttingDepth = 0`
    - `AxialFinishCuttingDepth = 0`
    - `StrokeConnectionStrategy = LiftShiftPlunge`
- Conclusiones provisionales:
  - la correccion lateral no vive solo en el toolpath: tambien se declara en la
    feature mediante `SideOfFeature`
  - aun asi, el resultado mecanizable se expresa en el desplazamiento efectivo de
    `Approach`, `TrajectoryPath` y `Lift`
  - esto sugiere que la futura API de fresado deberia exponer una nocion publica
    de `side_of_feature` o `cutter_side`
- Pendientes:
  - relevar el mismo eje `Central/Derecha/Izquierda` en una variante con multipaso
    axial real (`PH > 0` o `UH > 0`)
  - verificar si el mismo corrimiento se observa igual con `Approach` y
    `Retract` habilitados

### Ronda 18 - Correccion `Central/Derecha/Izquierda` con multipaso real (`PH5_UH1`)

- Estado: completado
- Archivos comparados:
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Central_Unidireccional_SalidaCota_MP_Hab_PH5_UH1.pgmx`
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Derecha_Unidireccional_SalidaCota_MP_Hab_PH5_UH1.pgmx`
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Izquierda_Unidireccional_SalidaCota_MP_Hab_PH5_UH1.pgmx`
- Hallazgo principal:
  - la correccion lateral mantiene el mismo patron semantico que en `PH0_UH0`,
    pero ahora sobre un `TrajectoryPath` compuesto real
  - se conservan:
    - `AllowMultiplePasses = true`
    - `AxialCuttingDepth = 5`
    - `AxialFinishCuttingDepth = 1`
    - `StrokeConnectionStrategy = LiftShiftPlunge`
    - `ActivateCNCCorrection = false`
- Estructura observada:
  - `Approach = GeomTrimmedCurve`
  - `TrajectoryPath = GeomCompositeCurve`
  - `Lift = GeomTrimmedCurve`
  - `TrajectoryPath` contiene `17` miembros serializados y `4`
    `OperationAttribute` en los tres casos
- Patron de correccion observado:
  - caso `Central`
    - todos los segmentos quedan sobre `x = 400`
  - caso `Derecha`
    - todos los segmentos equivalentes pasan a `x = 402`
  - caso `Izquierda`
    - todos los segmentos equivalentes pasan a `x = 398`
- Alcance del desplazamiento:
  - no se desplaza solo la pasada final
  - se desplazan:
    - `Approach`
    - cada uno de los miembros del `TrajectoryPath` compuesto
    - `Lift`
  - por lo tanto, la correccion lateral afecta la trayectoria completa del
    mecanizado axialmente escalonado
- Conclusiones provisionales:
  - la correccion lateral es transversal a la estrategia axial
  - una vez resuelto el toolpath multipaso base, Maestro aplica el mismo offset
    lateral a toda la familia de segmentos resultante
  - el offset sigue siendo de `±2 mm`, consistente con media herramienta de
    `E004`
- Implicacion para la futura API:
  - la futura spec de fresado deberia permitir combinar:
    - estrategia axial (`PH`, `UH`, conexion entre pasadas)
    - lado de correccion (`Center`, `Right`, `Left`)
  - el sintetizador tendra que desplazar no solo la geometria simple, sino
    tambien todos los segmentos del `TrajectoryPath` compuesto cuando haya
    multipaso
- Pendientes:
  - verificar esta misma combinacion con `Approach` y `Retract` habilitados
  - usar estos hallazgos para pasar luego a `Bidireccional` con una base mas
    estable

### Ronda 19 - Correccion `Central/Derecha/Izquierda` con multipaso real (`PH5_UH1`) y `AcL4B_AlL4S`

- Estado: completado
- Archivos comparados:
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Central_Unidireccional_SalidaCota_MP_Hab_PH5_UH1_AcL4B_AlL4S.pgmx`
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Derecha_Unidireccional_SalidaCota_MP_Hab_PH5_UH1_AcL4B_AlL4S.pgmx`
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Izquierda_Unidireccional_SalidaCota_MP_Hab_PH5_UH1_AcL4B_AlL4S.pgmx`
- Hallazgo principal:
  - la correccion lateral se mantiene plenamente compatible con:
    - multipaso axial real (`PH5_UH1`)
    - `Approach` lineal habilitado
    - `Retract` lineal habilitado
  - los parametros de entrada/salida se conservan en los tres casos:
    - `Approach.IsEnabled = true`
    - `Approach.RadiusMultiplier = 4`
    - `Approach.Speed = -1`
    - `Retract.IsEnabled = true`
    - `Retract.RadiusMultiplier = 4`
    - `Retract.Speed = -1`
- Estrategia axial conservada:
  - `AllowMultiplePasses = true`
  - `AxialCuttingDepth = 5`
  - `AxialFinishCuttingDepth = 1`
  - `StrokeConnectionStrategy = LiftShiftPlunge`
  - `ActivateCNCCorrection = false`
- Patron de correccion observado:
  - `Central`
    - `Approach`, `TrajectoryPath` y `Lift` quedan sobre `x = 400`
  - `Derecha`
    - esos mismos toolpaths quedan sobre `x = 402`
  - `Izquierda`
    - esos mismos toolpaths quedan sobre `x = 398`
- Alcance del desplazamiento:
  - el offset lateral afecta:
    - el `Approach` inclinado
    - los `17` miembros serializados del `TrajectoryPath`
    - el `Lift` inclinado
  - la correccion no altera:
    - angulos
    - radios multiplicadores
    - cantidad de miembros del `TrajectoryPath`
    - ni la estructura axial del multipaso
- Observacion geometrica:
  - el desplazamiento lateral sigue siendo de `±2 mm`
  - esto vuelve a coincidir con media herramienta para `E004 = 4 mm`
  - por lo tanto, el offset lateral parece aplicarse despues de resolver la
    forma completa del toolpath, incluyendo entrada, desbaste, pasada final y
    salida
- Conclusiones provisionales:
  - la correccion lateral es transversal no solo a la estrategia axial, sino
    tambien a `Approach` y `Retract`
  - el modelo mental mas estable hasta ahora es:
    1. Maestro resuelve la estrategia de fresado
    2. compone `Approach`, `TrajectoryPath` y `Lift`
    3. aplica el offset lateral completo segun `SideOfFeature`
- Implicacion para la futura API:
  - `side_of_feature` debe poder combinarse limpiamente con:
    - estrategia axial
    - `Approach`
    - `Retract`
  - el sintetizador debera poder desplazar toda la familia de toolpaths ya
    resueltos, no solo la geometria nominal
- Pendientes:
  - con este eje ya bastante cerrado, el siguiente paso natural sigue siendo
    pasar a `Bidireccional`

### Ronda 20 - Primera serializacion real de `Bidireccional`

- Estado: completado
- Archivos comparados:
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Central_Unidireccional_SalidaCota_MP_Hab_PH0_UH0.pgmx`
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Central_Bidireccional_PH0_UH0.pgmx`
- Hallazgo principal:
  - `Bidireccional` se serializa como:
    - `MachiningStrategy i:type="b:BidirectionalMilling"`
  - la familia de campos es muy parecida a `Unidireccional`
  - correccion posterior importante:
    - en estos archivos, los valores de `Approach` y `Retract` no deben
      interpretarse automaticamente como defaults propios de `Bidireccional`
    - el usuario confirmo que habia habilitado `Approach` y `Retract`,
      modificado sus parametros y luego vuelto a deshabilitarlos
    - por lo tanto, esos nodos pueden conservar valores editados aun estando en
      `IsEnabled = false`
- Mapeo observado respecto del caso unidireccional equivalente:
  - `MachiningStrategy`
    - `b:UnidirectionalMilling` -> `b:BidirectionalMilling`
  - `StrokeConnectionStrategy`
    - `LiftShiftPlunge` -> `Straghtline`
  - `ActivateCNCCorrection`
    - `true` -> `false`
  - `Approach`
    - en esta muestra observada:
      - `RadiusMultiplier: 1.2 -> 3`
      - `Speed: 0 -> -1`
      - `IsEnabled` se mantiene en `false`
      - `ApproachType = Line`
      - `ApproachMode = Down`
    - pero esos valores no quedan validados todavia como default real de la
      estrategia
  - `Retract`
    - en esta muestra observada:
      - `RadiusMultiplier: 1.2 -> 3`
      - `Speed: 0 -> -1`
      - `IsEnabled` se mantiene en `false`
      - `RetractType = Line`
      - `RetractMode = Up`
    - pero esos valores no quedan validados todavia como default real de la
      estrategia
- Valores observados en el primer caso `Bidireccional PH0_UH0`:
  - `AllowMultiplePasses = true`
  - `Overlap = 0`
  - `AxialCuttingDepth = 0`
  - `AxialFinishCuttingDepth = 0`
  - `Cutmode = Climb`
  - `RadialCuttingDepth = 0`
  - `RadialFinishCuttingDepth = 0`
  - `StrokeConnectionStrategy = Straghtline`
  - `ActivateCNCCorrection = false`
  - `Approach.IsEnabled = false`, `RadiusMultiplier = 3`, `Speed = -1`
  - `Retract.IsEnabled = false`, `RadiusMultiplier = 3`, `Speed = -1`
- Nota metodologica:
  - por la historia de edicion de estos archivos, hoy solo podemos afirmar que
    esos son los valores presentes en la muestra
  - todavia no alcanzan para declarar que sean defaults nativos de
    `Bidireccional`
- Toolpaths base observados:
  - `Approach`
    - `8 0 39`
    - `1 400 0 38 0 0 -1`
  - `TrajectoryPath`
    - `8 0 760`
    - `1 400 0 -1 0 1 0`
  - `Lift`
    - `8 0 39`
    - `1 400 760 -1 0 0 1`
- Conclusiones provisionales:
  - `Bidireccional` no es solo otro enum; trae al menos una politica de
    conexion propia (`Straghtline`) y un estado observado distinto en
    `ActivateCNCCorrection`
  - aun con `Approach` y `Retract` deshabilitados, esos nodos quedan
    explicitamente parametrizados, pero todavia no podemos afirmar que esos
    valores sean defaults nativos de la estrategia
- Pendientes:
  - relevar como cambian `PH` y `UH` dentro de `Bidireccional`
  - luego cruzarlo con correccion lateral y `Approach/Retract` habilitados

### Ronda 21 - `PH/UH` en `Bidireccional`

- Estado: completado
- Archivos comparados:
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Central_Bidireccional_PH0_UH0.pgmx`
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Central_Bidireccional_PH5_UH0.pgmx`
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Central_Bidireccional_PH5_UH1.pgmx`
  - `archive/maestro_examples/Pieza_800x760x18_LineaCentral_Central_Bidireccional_PH5_UH10.pgmx`
- Parametros estrategicos constantes en los cuatro casos:
  - `MachiningStrategy = b:BidirectionalMilling`
  - `AllowMultiplePasses = true`
  - `Overlap = 0`
  - `Cutmode = Climb`
  - `RadialCuttingDepth = 0`
  - `RadialFinishCuttingDepth = 0`
  - `StrokeConnectionStrategy = Straghtline`
  - `ActivateCNCCorrection = false`
- Parametros de `Approach/Retract` constantes en estas cuatro muestras:
  - `Approach.IsEnabled = false`
  - `Approach.RadiusMultiplier = 3`
  - `Approach.Speed = -1`
  - `Retract.IsEnabled = false`
  - `Retract.RadiusMultiplier = 3`
  - `Retract.Speed = -1`
- Nota metodologica:
  - estos valores de `Approach/Retract` quedaron contaminados por historia de
    edicion previa del archivo
  - por eso deben tratarse como constantes observadas en la muestra, no como
    defaults validados de `Bidireccional`
- Caso `PH0_UH0`:
  - `AxialCuttingDepth = 0`
  - `AxialFinishCuttingDepth = 0`
  - `TrajectoryPath` sigue siendo simple (`GeomTrimmedCurve`)
- Caso `PH5_UH0`:
  - `AxialCuttingDepth = 5`
  - `AxialFinishCuttingDepth = 0`
  - el `Approach` baja de `z = 39` a `z = 25`
  - `TrajectoryPath` pasa a `GeomCompositeCurve` con `7` miembros
  - el `Lift` termina en:
    - `1 400 0 -1 0 0 1`
- Caso `PH5_UH1`:
  - `AxialCuttingDepth = 5`
  - `AxialFinishCuttingDepth = 1`
  - `TrajectoryPath` compuesto con `9` miembros
  - el `Lift` termina en:
    - `1 400 760 -1 0 0 1`
- Caso `PH5_UH10`:
  - `AxialCuttingDepth = 5`
  - `AxialFinishCuttingDepth = 10`
  - `TrajectoryPath` compuesto con `5` miembros
  - el `Lift` termina en:
    - `1 400 760 -1 0 0 1`
- Patron axial observado:
  - `PH > 0` vuelve compuesto el `TrajectoryPath`, igual que en
    `Unidireccional`
  - `UH` no solo cambia la estrategia declarada; tambien recompone la cantidad
    de miembros del `TrajectoryPath`
  - con el mismo `PH = 5`:
    - `UH0` -> `7` miembros
    - `UH1` -> `9` miembros
    - `UH10` -> `5` miembros
- Diferencias relevantes respecto de `Unidireccional`:
  - en estos primeros casos no aparecen `RapidSpeedAttribute`
  - tampoco aparecen `OperationAttribute` dentro del `TrajectoryPath`
  - la topologia alterna el sentido de avance sobre la misma linea, en vez de
    modelar reconexiones altas separadas como en `SalidaCota`
  - `PH5_UH0` deja el `Lift` en `y = 0`, mientras que `PH5_UH1` y `PH5_UH10`
    lo dejan en `y = 760`
- Conclusiones provisionales:
  - `Bidireccional` comparte la misma pareja de parametros axiales (`PH`, `UH`)
    pero los aplica sobre una topologia de trayectoria distinta
  - la futura spec publica probablemente podra reutilizar `PH` y `UH`, pero la
    serializacion y generacion de toolpaths tendra que ser especifica por
    estrategia
- Pendientes:
  - relevar `Bidireccional` con correccion `Derecha/Izquierda`
  - relevar `Bidireccional` con `Approach` y `Retract` habilitados

### Nota metodologica - `Approach` y `Retract`

- Estado: vigente
- Aclaracion:
  - para esta linea de trabajo, los defaults de UI de `Approach` y `Retract`
    se consideran de baja prioridad
  - incluso pueden terminar siendo reemplazados en el sintetizador por defaults
    propios definidos por familia de herramienta o por tipo de operacion
- Lo que si importa relevar:
  - cuando `Approach` esta habilitado, cambia la geometria real del toolpath de
    entrada
  - cuando `Retract` esta habilitado, cambia la geometria real del toolpath de
    salida
  - en particular, aparecen o cambian segmentos inclinados de entrada/salida
  - esos segmentos se combinan con:
    - la estrategia axial
    - la correccion lateral (`Center`, `Right`, `Left`)
    - y la posicion efectiva de inicio/fin del mecanizado
- Implicacion para la futura API:
  - `Approach` y `Retract` deben modelarse principalmente por su efecto
    geometrico sobre `ToolpathList`
  - no es necesario reconstruir ni respetar ciegamente los defaults de Maestro
    si mas adelante decidimos usar defaults propios del sintetizador

### Ronda 22 - Primer `Unidireccional` sobre escuadrado horario sin `Ac/Al`

- Estado: completado
- Archivos comparados:
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Horario_SinEstrategia_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Horario_Unidireccional_SalidaCota_MP_Hab_PH0_UH0_SinAcAl.pgmx`
- Hallazgo principal:
  - sobre el escuadrado horario, `Unidireccional PH0_UH0` agrega la
    `MachiningStrategy` pero todavia no dispara multipaso axial real
- Mapeo observado:
  - `MachiningStrategy`
    - `i:nil="true"` -> `b:UnidirectionalMilling`
  - `AllowMultiplePasses = true`
  - `AxialCuttingDepth = 0`
  - `AxialFinishCuttingDepth = 0`
  - `StrokeConnectionStrategy = LiftShiftPlunge`
  - `ActivateCNCCorrection` se mantiene en `true`
  - `Approach` y `Lift` quedan iguales al caso sin estrategia
- Geometria y compensacion:
  - `SideOfFeature` se mantiene en `Left` en toda la familia de escuadrados
    horarios relevada
  - el `TrajectoryPath` sigue teniendo `9` miembros y no aparecen:
    - `RapidSpeedAttribute`
    - `OperationAttribute`
- Observacion importante:
  - aunque el numero de miembros se conserva (`9 -> 9`), el `TrajectoryPath` no
    queda byte a byte identico al caso sin estrategia
  - Maestro reparametriza el primer y ultimo tramo del contorno, pero sin
    cambiar todavia la topologia general del recorrido
- Conclusiones provisionales:
  - para contorno cerrado, `PH0_UH0` funciona como una activacion semantica de
    estrategia, no como una activacion de capas
  - la forma axial fuerte aparece recien cuando `PH > 0` o cuando `UH` obliga a
    descomponer el recorrido

### Ronda 23 - `PH/UH` en `Unidireccional` sobre escuadrado horario sin `Ac/Al`

- Estado: completado
- Archivos comparados:
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Horario_Unidireccional_SalidaCota_MP_Hab_PH0_UH0_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Horario_Unidireccional_SalidaCota_MP_Hab_PH5_UH0_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Horario_Unidireccional_SalidaCota_MP_Hab_PH5_UH1_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Horario_Unidireccional_SalidaCota_MP_Hab_PH5_UH10_SinAcAl.pgmx`
- Parametros estrategicos constantes en los cuatro casos con estrategia:
  - `MachiningStrategy = b:UnidirectionalMilling`
  - `AllowMultiplePasses = true`
  - `StrokeConnectionStrategy = LiftShiftPlunge`
  - `SideOfFeature = Left`
  - no aparecen:
    - `RapidSpeedAttribute`
    - `OperationAttribute`
- Caso `PH5_UH0`:
  - `ActivateCNCCorrection: true -> false`
  - `AxialCuttingDepth = 5`
  - `AxialFinishCuttingDepth = 0`
  - el `Approach` baja de `z = 39` a `z = 25`
  - `Lift` se mantiene igual
  - `TrajectoryPath` pasa de `9` a `39` miembros
- Caso `PH5_UH1`:
  - `AxialCuttingDepth = 5`
  - `AxialFinishCuttingDepth = 1`
  - `TrajectoryPath` pasa a `49` miembros
  - `Approach` y `Lift` se mantienen iguales al caso `PH5_UH0`
- Caso `PH5_UH10`:
  - `AxialCuttingDepth = 5`
  - `AxialFinishCuttingDepth = 10`
  - `TrajectoryPath` pasa a `29` miembros
  - `Approach` y `Lift` se mantienen iguales al caso `PH5_UH0`
- Patron topologico observado:
  - el contorno base del escuadrado horario ocupa `9` miembros:
    - medio tramo inicial
    - 4 arcos de esquina
    - 3 tramos rectos completos
    - medio tramo final
  - cuando `PH > 0`, Maestro apila vueltas completas del perimetro y agrega
    entre ellas segmentos verticales de bajada
- Descomposicion observada:
  - `PH5_UH0`
    - `39 = 9 + 1 + 9 + 1 + 9 + 1 + 9`
    - capas observadas en `z = 13`, `8`, `3`, `-1`
    - bajadas intermedias de `5`, `5` y `4`
  - `PH5_UH1`
    - `49 = 9 + 1 + 9 + 1 + 9 + 1 + 9 + 1 + 9`
    - capas observadas en `z = 13`, `8`, `3`, `0`, `-1`
    - bajadas intermedias de `5`, `5`, `3` y `1`
  - `PH5_UH10`
    - `29 = 9 + 1 + 9 + 1 + 9`
    - capas observadas en `z = 13`, `9`, `-1`
    - bajadas intermedias de `4` y `10`
- Observacion fuerte:
  - para escuadrado cerrado, `UH` no cambia ni el `Approach` ni el `Lift`
  - su efecto visible cae en la cantidad de vueltas completas del perimetro y
    en las bajadas verticales que conectan esas vueltas
- Conclusiones provisionales:
  - en contorno cerrado, `Unidireccional` parece construirse como:
    1. una vuelta base del perimetro (`9` miembros)
    2. repeticion por capas axiales
    3. segmentos verticales de enlace entre capas
  - esto es distinto del caso lineal abierto, donde la topologia observada se
    organizaba alrededor de un recorrido ida/reconexion
- Pendientes:
  - relevar el mismo patron para escuadrado antihorario
  - comparar luego contra `Bidireccional` sobre escuadrado

### Ronda 24 - `EnLaPieza` vs `SalidaCota` en `Unidireccional` sobre escuadrado horario sin `Ac/Al`

- Estado: completado
- Archivos comparados:
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Horario_Unidireccional_SalidaCota_MP_Hab_PH0_UH0_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Horario_Unidireccional_EnLaPieza_MP_Hab_PH0_UH0_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Horario_Unidireccional_SalidaCota_MP_Hab_PH5_UH0_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Horario_Unidireccional_EnLaPieza_MP_Hab_PH5_UH0_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Horario_Unidireccional_SalidaCota_MP_Hab_PH5_UH1_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Horario_Unidireccional_EnLaPieza_MP_Hab_PH5_UH1_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Horario_Unidireccional_SalidaCota_MP_Hab_PH5_UH10_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Horario_Unidireccional_EnLaPieza_MP_Hab_PH5_UH10_SinAcAl.pgmx`
- Hallazgo principal:
  - en esta familia de escuadrados horarios, cambiar `Conexion entre huecos`
    de `SalidaCota` a `EnLaPieza` solo cambia el campo de estrategia:
    - `StrokeConnectionStrategy: LiftShiftPlunge -> Straghtline`
- Lo que no cambia:
  - `MachiningStrategy` sigue siendo `b:UnidirectionalMilling`
  - `AllowMultiplePasses`
  - `AxialCuttingDepth`
  - `AxialFinishCuttingDepth`
  - `ActivateCNCCorrection`
  - `Approach`
  - `Lift`
  - `TrajectoryPath`
  - cantidad de miembros del `TrajectoryPath`
  - ausencia de:
    - `RapidSpeedAttribute`
    - `OperationAttribute`
- Validacion importante:
  - comparando los miembros serializados del `TrajectoryPath`, los toolpaths
    efectivos quedan identicos en los cuatro pares:
    - `PH0_UH0`
    - `PH5_UH0`
    - `PH5_UH1`
    - `PH5_UH10`
  - los hashes crudos del bloque XML cambian por detalles internos de
    serializacion, pero no por diferencia geometrica efectiva
- Conclusiones provisionales:
  - para el escuadrado horario sin `Ac/Al`, `SalidaCota` y `EnLaPieza` quedan
    indistinguibles a nivel de `ToolpathList`
  - en esta familia, la diferencia entre ambas opciones parece quedar solo como
    declaracion semantica en `MachiningStrategy`
- Pendientes:
  - verificar si esta equivalencia tambien se conserva en:
    - escuadrado antihorario
    - `Approach` / `Retract` habilitados
    - otras estrategias como `Bidireccional`

### Decision provisional - default de conexion en polilinea cerrada `Unidireccional`

- Estado: vigente
- Regla acordada:
  - para fresados de `polilinea cerrada`
  - si la estrategia es `Unidireccional`
  - el default del sintetizador debe ser:
    - `Conexion entre huecos = EnLaPieza`
    - es decir: `StrokeConnectionStrategy = Straghtline`
- Justificacion:
  - en los escuadrados horario y antihorario sin `Ac/Al` relevados hasta ahora,
    `SalidaCota` y `EnLaPieza` no cambian el `ToolpathList` efectivo
  - por lo tanto, conviene fijar un default estable y simple del lado del
    sintetizador
  - `SalidaCota` queda reservado como opcion explicita cuando el usuario la
    solicite
- Alcance actual:
  - esta decision ya queda sustentada por los casos relevados de escuadrado
    horario y antihorario
  - todavia conviene verificar si el mismo criterio se mantiene en:
    - polilineas cerradas no rectangulares
    - casos con `Approach` y `Retract` habilitados

### Ronda 25 - `Unidireccional` sobre escuadrado antihorario sin `Ac/Al`

- Estado: completado
- Archivos comparados:
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Antihorario_SinEstrategia_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Antihorario_Unidireccional_SalidaCota_MP_Hab_PH0_UH0_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Antihorario_Unidireccional_SalidaCota_MP_Hab_PH5_UH0_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Antihorario_Unidireccional_SalidaCota_MP_Hab_PH5_UH1_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Antihorario_Unidireccional_SalidaCota_MP_Hab_PH5_UH10_SinAcAl.pgmx`
- Hallazgo principal:
  - el patron axial de `Unidireccional` sobre escuadrado antihorario espeja al
    caso horario con la misma topologia de capas
- Mapeo observado:
  - `SideOfFeature = Right` en toda la familia antihoraria
  - `PH0_UH0`
    - agrega `MachiningStrategy = b:UnidirectionalMilling`
    - `AllowMultiplePasses = true`
    - `AxialCuttingDepth = 0`
    - `AxialFinishCuttingDepth = 0`
    - `StrokeConnectionStrategy = LiftShiftPlunge`
    - `ActivateCNCCorrection` se mantiene en `true`
    - `TrajectoryPath` sigue teniendo `9` miembros
  - `PH5_UH0`
    - `ActivateCNCCorrection: true -> false`
    - `AxialCuttingDepth = 5`
    - `TrajectoryPath` pasa a `39` miembros
    - el `Approach` baja de `z = 39` a `z = 25`
  - `PH5_UH1`
    - `AxialFinishCuttingDepth = 1`
    - `TrajectoryPath` pasa a `49` miembros
  - `PH5_UH10`
    - `AxialFinishCuttingDepth = 10`
    - `TrajectoryPath` pasa a `29` miembros
- Patron topologico observado:
  - igual que en horario, el contorno base ocupa `9` miembros
  - cuando `PH > 0`, Maestro apila vueltas completas del perimetro y agrega
    segmentos verticales de bajada entre capas
  - las capas observadas vuelven a ser:
    - `PH5_UH0` -> `z = 13`, `8`, `3`, `-1`
    - `PH5_UH1` -> `z = 13`, `8`, `3`, `0`, `-1`
    - `PH5_UH10` -> `z = 13`, `9`, `-1`
- Diferencia respecto del horario:
  - la geometria del perimetro queda espejada:
    - cambia el lado de compensacion (`Right` en vez de `Left`)
    - cambian los signos/direcciones de los tramos y arcos
  - pero no cambia la logica de conteo de miembros ni la descomposicion axial
- Conclusiones provisionales:
  - el modelo de `Unidireccional` sobre escuadrado cerrado parece estable en
    ambos sentidos:
    1. vuelta base de `9` miembros
    2. repeticion por capas
    3. bajadas verticales entre vueltas

### Ronda 26 - `EnLaPieza` vs `SalidaCota` en `Unidireccional` sobre escuadrado antihorario sin `Ac/Al`

- Estado: completado
- Archivos comparados:
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Antihorario_Unidireccional_SalidaCota_MP_Hab_PH0_UH0_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Antihorario_Unidireccional_EnLaPieza_MP_Hab_PH0_UH0_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Antihorario_Unidireccional_SalidaCota_MP_Hab_PH5_UH0_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Antihorario_Unidireccional_EnLaPieza_MP_Hab_PH5_UH0_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Antihorario_Unidireccional_SalidaCota_MP_Hab_PH5_UH1_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Antihorario_Unidireccional_EnLaPieza_MP_Hab_PH5_UH1_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Antihorario_Unidireccional_SalidaCota_MP_Hab_PH5_UH10_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Antihorario_Unidireccional_EnLaPieza_MP_Hab_PH5_UH10_SinAcAl.pgmx`
- Hallazgo principal:
  - igual que en el escuadrado horario, `EnLaPieza` y `SalidaCota` dejan el
    `ToolpathList` efectivo identico en los cuatro pares comparados
- Cambio firme observado:
  - `StrokeConnectionStrategy: LiftShiftPlunge -> Straghtline`
- Lo que no cambia en los cuatro pares:
  - `Approach`
  - `TrajectoryPath`
  - `Lift`
  - cantidad de miembros del `TrajectoryPath`
  - ausencia de:
    - `RapidSpeedAttribute`
    - `OperationAttribute`
- Observacion puntual:
  - en `PH0_UH0`, la muestra `EnLaPieza` tambien quedo con:
    - `ActivateCNCCorrection: true -> false`
  - aun asi, el `ToolpathList` efectivo sigue siendo identico al de
    `SalidaCota`
  - por ahora conviene tratar esto como hallazgo puntual de la muestra, no como
    regla general
- Conclusiones provisionales:
  - la equivalencia geometrica entre `EnLaPieza` y `SalidaCota` ya se sostiene
    tanto en escuadrado horario como en antihorario, al menos sin `Ac/Al`
  - esto fortalece la decision provisional de usar `EnLaPieza` como default en
    `polilinea cerrada + Unidireccional`

### Ronda 27 - `Bidireccional` sobre escuadrado cerrado sin `Ac/Al`

- Estado: completado
- Archivos comparados:
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Horario_Bidireccional_PH0_UH0_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Horario_Bidireccional_PH5_UH0_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Horario_Bidireccional_PH5_UH1_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Horario_Bidireccional_PH5_UH10_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Antihorario_Bidireccional_PH0_UH0_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Antihorario_Bidireccional_PH5_UH0_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Antihorario_Bidireccional_PH5_UH1_SinAcAl.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Antihorario_Bidireccional_PH5_UH10_SinAcAl.pgmx`
- Hallazgo principal:
  - `Bidireccional` sobre escuadrado cerrado conserva la misma grilla axial de
    capas que `Unidireccional`, pero cambia la forma en que se recorre cada
    vuelta del perimetro
- Mapeo observado en ambos sentidos:
  - `MachiningStrategy = b:BidirectionalMilling`
  - `AllowMultiplePasses = true`
  - `StrokeConnectionStrategy = Straghtline`
  - `PH0_UH0`
    - `AxialCuttingDepth = 0`
    - `AxialFinishCuttingDepth = 0`
    - `ActivateCNCCorrection = true`
    - `TrajectoryPath` con `9` miembros
  - `PH5_UH0`
    - `AxialCuttingDepth = 5`
    - `AxialFinishCuttingDepth = 0`
    - `ActivateCNCCorrection = false`
    - `Approach` baja de `z = 39` a `z = 25`
    - `TrajectoryPath` con `39` miembros
  - `PH5_UH1`
    - `AxialFinishCuttingDepth = 1`
    - `TrajectoryPath` con `49` miembros
  - `PH5_UH10`
    - `AxialFinishCuttingDepth = 10`
    - `TrajectoryPath` con `29` miembros
- Patron de miembros:
  - igual que en `Unidireccional` cerrado:
    - base `9` miembros por vuelta
    - mas segmentos verticales entre capas
  - por lo tanto, se repite la misma descomposicion de conteo:
    - `PH5_UH0` -> `39 = 9 + 1 + 9 + 1 + 9 + 1 + 9`
    - `PH5_UH1` -> `49 = 9 + 1 + 9 + 1 + 9 + 1 + 9 + 1 + 9`
    - `PH5_UH10` -> `29 = 9 + 1 + 9 + 1 + 9`
- Hallazgo topologico fuerte:
  - la diferencia real respecto de `Unidireccional + EnLaPieza` aparece cuando
    `PH > 0`
  - en `Bidireccional`, las vueltas completas del perimetro alternan su sentido
    de recorrido entre capa y capa
  - en cambio, en `Unidireccional`, todas las vueltas mantienen el mismo
    sentido geometrico y solo cambian de cota
- Interpretacion operativa:
  - en contorno cerrado, `Bidireccional` parece significar:
    1. construir una vuelta completa del perimetro
    2. bajar en Z
    3. recorrer la siguiente vuelta en el sentido opuesto
    4. repetir alternando hasta llegar a la pasada final
- Diferencia respecto del caso lineal abierto:
  - en la linea abierta, `Bidireccional` alternaba el sentido sobre la misma
    linea recta
  - en contorno cerrado, la alternancia se da por vueltas completas del
    perimetro, no por tramos parciales del contorno
- Observacion sobre sentidos:
  - `Horario` y `Antihorario` siguen espejandose limpiamente:
    - `Horario` -> `SideOfFeature = Left`
    - `Antihorario` -> `SideOfFeature = Right`
  - la cuenta de miembros y la logica axial son identicas en ambos
  - lo que cambia es la orientacion de cada vuelta

### Ronda 28 - `Bidireccional` vs `Unidireccional + EnLaPieza` sobre escuadrado cerrado

- Estado: completado
- Archivos comparados:
  - familias `Horario` y `Antihorario`
  - para `PH0_UH0`, `PH5_UH0`, `PH5_UH1` y `PH5_UH10`
- Hallazgo principal:
  - en `PH0_UH0`, `Bidireccional` y `Unidireccional + EnLaPieza` dejan
    `ToolpathList` identico a nivel geometrico
  - la diferencia real entre ambas estrategias aparece recien cuando `PH > 0`
- Coincidencias observadas:
  - `AllowMultiplePasses`
  - `AxialCuttingDepth`
  - `AxialFinishCuttingDepth`
  - `StrokeConnectionStrategy = Straghtline`
  - `Approach`
  - `Lift`
  - cantidad total de miembros del `TrajectoryPath`
- Diferencia estructural con `PH > 0`:
  - `Unidireccional + EnLaPieza`
    - mantiene el mismo sentido de vuelta en todas las capas
  - `Bidireccional`
    - invierte el sentido de la vuelta siguiente despues de cada bajada axial
- Observacion puntual:
  - en `Antihorario + PH0_UH0`, la muestra relevada de `Unidireccional +
    EnLaPieza` tenia `ActivateCNCCorrection = false`, mientras que
    `Bidireccional PH0_UH0` quedo con `true`
  - aun asi, el `ToolpathList` sigue siendo identico
  - esto conviene tratarlo como diferencia puntual de la muestra, no como regla
    de implementacion
- Conclusiones provisionales:
  - para contorno cerrado, `Bidireccional` no necesita una regla axial nueva de
    conteo de capas
  - lo que necesita es una regla topologica distinta:
    - alternar el winding efectivo de cada vuelta completa del perimetro

### Decision provisional - estrategia preferida para escuadrados con multiples pasadas

- Estado: vigente
- Regla acordada:
  - para `escuadrados`
  - si hay `multiples pasadas`:
    - `PH > 0`
    - o `UH > 0`
  - la estrategia preferida del sintetizador debe ser `Unidireccional`
- Justificacion:
  - en contorno cerrado, `Unidireccional` ya quedo bien caracterizado:
    - misma vuelta base
    - repeticion clara por capas
    - enlazado vertical simple entre capas
  - ademas, para `polilinea cerrada + Unidireccional`, ya adoptamos como
    default `EnLaPieza`
  - `Bidireccional` queda como variante soportada, pero con una topologia mas
    especifica:
    - alterna el sentido de cada vuelta completa del perimetro
- Implicacion para la futura API:
  - si el usuario no especifica estrategia en un escuadrado con multiples
    pasadas, el sintetizador deberia preferir `Unidireccional`
  - `Bidireccional` queda reservado como opcion explicita

### Ronda 29 - `Unidireccional` sobre escuadrado con `Acercamiento/Alejamiento Arco 2 En Cota`

- Estado: completado
- Archivos comparados:
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Horario_Unidireccional_PH0_UH0_AcA2C_AlA2C.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Horario_Unidireccional_PH5_UH0_AcA2C_AlA2C.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Horario_Unidireccional_PH5_UH1_AcA2C_AlA2C.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Horario_Unidireccional_PH5_UH10_AcA2C_AlA2C.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Antihorario_Unidirecional_PH0_UH0_AcA2C_AlA2C.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Antihorario_Unidirecional_PH5_UH0_AcA2C_AlA2C.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Antihorario_Unidirecional_PH5_UH1_AcA2C_AlA2C.pgmx`
  - `archive/maestro_examples/Pieza_300x300x18_Escuadrado_Antihorario_Unidirecional_PH5_UH10_AcA2C_AlA2C.pgmx`
- Observacion de nomenclatura:
  - los cuatro archivos `Antihorario` quedaron guardados como
    `Unidirecional` sin la segunda `c`
  - para el relevamiento vamos a tomarlos como parte de la misma familia
- Hallazgo principal:
  - estos archivos quedaron sobre la rama `EnLaPieza`
  - es decir:
    - `StrokeConnectionStrategy = Straghtline`
  - comparados contra sus pares `EnLaPieza` sin `Ac/Al`, el
    `TrajectoryPath` queda identico en los ocho casos
- Parametros observados:
  - `Approach.IsEnabled = true`
  - `ApproachType = Arc`
  - `ApproachMode = Quote`
  - `Approach.RadiusMultiplier = 2`
  - `Approach.Speed = -1`
  - `Retract.IsEnabled = true`
  - `RetractType = Arc`
  - `RetractMode = Quote`
  - `Retract.RadiusMultiplier = 2`
  - `Retract.Speed = -1`
  - `Retract.OverLap = 0`
- ArcSide observado:
  - `Horario`
    - `ApproachArcSide = Left`
    - `RetractArcSide = Left`
  - `Antihorario`
    - `ApproachArcSide = Right`
    - `RetractArcSide = Right`
- Efecto geometrico observado:
  - `Approach` deja de ser `GeomTrimmedCurve` y pasa a `GeomCompositeCurve`
    con `2` miembros
  - `Lift` deja de ser `GeomTrimmedCurve` y pasa a `GeomCompositeCurve`
    con `2` miembros
  - `TrajectoryPath` no cambia
- Estructura observada de `Approach/Lift`:
  - `Approach`
    1. un tramo lineal exterior
    2. un arco de cuarto de vuelta que enlaza con el primer punto del mecanizado
  - `Lift`
    1. el arco complementario de salida
    2. un tramo lineal exterior de retirada
- Patron espacial:
  - los segmentos exteriores se apoyan sobre `y = -18.36`
  - esto coincide con un desplazamiento de `2 * 9.18`, donde:
    - `9.18 = tool_width / 2` para `E001`
  - el centro del arco queda sobre `x = 150`, `y = -18.36`
  - en `Horario`, la entrada/salida exterior se corre hacia `x = 159.18` y
    `x = 140.82`
  - en `Antihorario`, ese corrimiento se espeja
- Independencia respecto de `PH/UH`:
  - el patron de `Approach/Lift` es el mismo para:
    - `PH0_UH0`
    - `PH5_UH0`
    - `PH5_UH1`
    - `PH5_UH10`
  - lo unico que sigue variando con `PH/UH` es la cota de entrada a la primera
    vuelta, igual que en los casos sin `Ac/Al`
- Conclusiones provisionales:
  - en escuadrado `Unidireccional + EnLaPieza`, habilitar `AcA2C_AlA2C` no
    altera la estrategia axial ni la topologia del `TrajectoryPath`
  - su efecto cae exclusivamente en los toolpaths de entrada/salida
  - el sentido del escuadrado se refleja limpiamente en el `ArcSide` de
    `Approach` y `Retract`

### Ronda 30 - Formalizacion de la API publica para estrategias de fresado

- Estado: completado
- Cambios volcados al codigo:
  - se agregaron las specs publicas:
    - `UnidirectionalMillingStrategySpec`
    - `BidirectionalMillingStrategySpec`
  - se agregaron las builders publicas:
    - `build_unidirectional_milling_strategy_spec(...)`
    - `build_bidirectional_milling_strategy_spec(...)`
  - `LineMillingSpec`, `PolylineMillingSpec`, `CircleMillingSpec` y
    `SquaringMillingSpec` ahora aceptan `milling_strategy`
- Alcance implementado:
  - linea simple:
    - `Unidireccional`
    - `Bidireccional`
  - polilinea lineal abierta o cerrada:
    - `Unidireccional`
    - `Bidireccional`
  - circulo cerrado:
    - `Unidireccional`
    - `Bidireccional`
  - escuadrado:
    - `Unidireccional`
    - `Bidireccional`
- Reglas volcadas:
  - `Unidireccional`
    - `connection_mode = Automatic`
      - linea simple -> `SafetyHeight`
      - polilinea cerrada / escuadrado -> `InPiece`
  - si `PH > 0` o `UH > 0`, la builder publica activa
    `AllowMultiplePasses = true` automaticamente
  - si `PH = 0` y `UH = 0`, la estrategia se serializa pero el
    `TrajectoryPath` sigue siendo de una sola pasada
  - si hay multipaso real:
    - `ActivateCNCCorrection = false`
- Topologia implementada:
  - linea simple `Unidireccional`
    - misma pasada efectiva en el mismo sentido
    - retornos entre capas segun `SafetyHeight` o `InPiece`
  - linea simple `Bidireccional`
    - alternancia del sentido de cada pasada
  - polilinea abierta `Unidireccional`
    - recorre el perfil abierto completo
    - retorno entre capas por el perfil invertido a cota de reconexion
  - polilinea abierta `Bidireccional`
    - alternancia del sentido del perfil abierto completo entre pasada y pasada
  - contorno cerrado `Unidireccional`
    - misma vuelta completa repetida a distintas cotas
  - contorno cerrado `Bidireccional`
    - alternancia del winding efectivo entre vuelta y vuelta
- Integracion con `Approach/Retract`:
  - el `TrajectoryPath` ahora se sintetiza en 3D con la cota real de la
    primera y ultima pasada
  - `Approach` y `Lift` ya toman esas cotas reales, en vez de depender siempre
    de `cut_z` final
- Verificaciones realizadas:
  - compilacion: `py -3 -m py_compile tools\\synthesize_pgmx.py`
  - linea simple `Unidireccional InPiece PH5_UH0`
  - linea simple `Bidireccional PH5_UH1`
  - circulo cerrado `Unidireccional InPiece PH5_UH10`
  - escuadrado `Unidireccional Automatic PH5_UH10`
  - polilinea cerrada lineal `Bidireccional PH5_UH0`
- Documentacion formal actualizada:
  - `docs/synthesize_pgmx_help.md`
  - `README.md`

### Ronda 31 - `Unidireccional + EnLaPieza` sobre la `Tapa` sintetizada

- Estado: completado
- Archivos revisados:
  - `archive/maestro_examples/Tapa_v11_sintetizada_Unidireccional_EnLaPieza_PH0_UH0.pgmx`
  - `archive/maestro_examples/Tapa_v11_sintetizada_Unidireccional_EnLaPieza_PH5_UH0.pgmx`
  - `archive/maestro_examples/Tapa_v11_sintetizada_Unidireccional_EnLaPieza_PH5_UH1.pgmx`
  - `archive/maestro_examples/Tapa_v11_sintetizada_Unidireccional_EnLaPieza_PH5_UH10.pgmx`
- Referencia base usada para contrastar:
  - `archive/maestro_examples/Tapa_v11_sintetizada.pgmx`
- Hallazgo principal:
  - en esta familia, la estrategia `Unidireccional + EnLaPieza` se activo solo
    sobre el fresado circular interior `Fresado`
  - el escuadrado `LAV_1` queda sin estrategia en los cuatro archivos
  - los `8` taladros tampoco cambian
- Parametros estrategicos constantes en los cuatro casos del circulo:
  - `MachiningStrategy = b:UnidirectionalMilling`
  - `AllowMultiplePasses = true`
  - `StrokeConnectionStrategy = Straghtline`
  - `SideOfFeature = Left`
  - `Approach.IsEnabled = false`
  - `Retract.IsEnabled = false`
- Cambio estructural inmediato respecto del archivo base:
  - en `Tapa_v11_sintetizada.pgmx`, el circulo ya tenia:
    - `TrajectoryPath = GeomCompositeCurve` con `2` semicircunferencias
    - `Approach = GeomTrimmedCurve`
    - `Lift = GeomTrimmedCurve`
    - `ActivateCNCCorrection = true`
  - al activar `Unidireccional + EnLaPieza`, el `Approach` y el `Lift` se
    mantienen como `GeomTrimmedCurve`, pero:
    - `ActivateCNCCorrection: true -> false`
- Patron topologico observado en el circulo:
  - una vuelta completa del contorno circular ocupa `2` miembros:
    - semicircunferencia 1
    - semicircunferencia 2
  - cada reconexion entre capas agrega `1` miembro lineal vertical
  - por eso, para el circulo cerrado:
    - `PH0_UH0` -> `2`
    - `PH5_UH0` -> `11 = 2 + 1 + 2 + 1 + 2 + 1 + 2`
    - `PH5_UH1` -> `14 = 2 + 1 + 2 + 1 + 2 + 1 + 2 + 1 + 2`
    - `PH5_UH10` -> `8 = 2 + 1 + 2 + 1 + 2`
- Capas observadas en `TrajectoryPath` del circulo:
  - `PH0_UH0`
    - niveles: `z = 0`
    - sin conectores verticales intermedios
  - `PH5_UH0`
    - niveles: `z = 13`, `8`, `3`, `0`
    - conectores verticales: `5`, `5`, `3`
  - `PH5_UH1`
    - niveles: `z = 13`, `8`, `3`, `1`, `0`
    - conectores verticales: `5`, `5`, `2`, `1`
  - `PH5_UH10`
    - niveles: `z = 13`, `10`, `0`
    - conectores verticales: `3`, `10`
- Patron espacial observado:
  - todos los enlaces entre capas del circulo caen en el mismo punto XY
  - ese punto es el arranque del circulo compensado:
    - `x = 281.32`
    - `y = 200`
  - esto coincide con:
    - centro nominal `(200, 200)`
    - radio nominal `90.5`
    - compensacion `Left` con `E001` (`tool_width = 18.36`)
    - radio efectivo `90.5 - 9.18 = 81.32`
  - como el perfil circular cerrado empieza y termina en el mismo punto,
    `EnLaPieza` no necesita segmentos horizontales de reconexion:
    alcanza con bajadas verticales puras entre una vuelta y la siguiente
- `Approach` y `Lift` del circulo:
  - siguen siendo segmentos verticales simples
  - `PH0_UH0`
    - `Approach` baja de `z = 38` a `z = 0`
    - `Lift` sube de `z = 0` a `z = 38`
  - `PH5_UH0`, `PH5_UH1`, `PH5_UH10`
    - `Approach` baja de `z = 38` a `z = 13`
    - `Lift` sube de `z = 0` a `z = 38`
- Lo que no cambia en `LAV_1`:
  - `MachiningStrategy` sigue en `nil`
  - `Approach` sigue como `GeomCompositeCurve` de `2` miembros
  - `TrajectoryPath` sigue como `GeomCompositeCurve` de `9` miembros
  - `Lift` sigue como `GeomCompositeCurve` de `2` miembros
- Conclusiones provisionales:
  - el modelo de `Unidireccional` para contorno cerrado tambien se sostiene en
    un `GeomCircle`, no solo en escuadrados/polilineas cerradas
  - cambia la unidad base del lazo:
    - escuadrado cerrado -> `9` miembros por vuelta
    - circulo cerrado -> `2` miembros por vuelta
  - `PH` y `UH` siguen determinando:
    - cantidad de vueltas
    - cotas intermedias
    - magnitud de las bajadas entre vueltas
  - en un circulo cerrado, `EnLaPieza` se degrada geometricamente a una
    secuencia de conectores verticales en el mismo XY de arranque/cierre
  - para esta familia puntual, activar la estrategia sobre el circulo no arrastra
    cambios colaterales al escuadrado ni a los taladros

### Decision de cierre - Sintetizador Maestro `v1.0`

- Estado: vigente
- Se establece esta etapa del sintetizador como `v1.0`
- Alcance consolidado del hito:
  - baseline versionado por defecto
  - taladros puntuales multicara
  - linea simple
  - polilinea lineal abierta/cerrada
  - escuadrado
  - estrategias publicas `Unidireccional` y `Bidireccional`
  - `Approach` y `Retract` ya desacoplados de la estrategia axial
- Criterio operativo:
  - nuevos hallazgos y nuevas familias deben considerarse ampliaciones sobre
    `v1.0`, no redefiniciones del alcance ya estabilizado

### Ronda 32 - `Helicoidal` sobre el circulo de la `Tapa` sintetizada

- Estado: completado
- Archivos revisados:
  - `archive/maestro_examples/Tapa_v11_sintetizada_Helicoidal_PH0_PasadaFinal_Deshabilitada.pgmx`
  - `archive/maestro_examples/Tapa_v11_sintetizada_Helicoidal_PH5_PasadaFinal_Deshabilitada.pgmx`
  - `archive/maestro_examples/Tapa_v11_sintetizada_Helicoidal_PH0_PasadaFinal_Habilitada_UH0.pgmx`
  - `archive/maestro_examples/Tapa_v11_sintetizada_Helicoidal_PH5_PasadaFinal_Habilitada_UH0.pgmx`
  - `archive/maestro_examples/Tapa_v11_sintetizada_Helicoidal_PH5_PasadaFinal_Habilitada_UH1.pgmx`
  - `archive/maestro_examples/Tapa_v11_sintetizada_Helicoidal_PH5_PasadaFinal_Habilitada_UH10.pgmx`
- Referencia base usada para contrastar:
  - `archive/maestro_examples/Tapa_v11_sintetizada.pgmx`
- Hallazgo principal:
  - en esta familia, la estrategia `Helicoidal` se activa solo sobre el
    fresado circular interior `Fresado`
  - el escuadrado `LAV_1` queda sin estrategia en los seis archivos
  - los `8` taladros tampoco cambian
- Mapeo UI -> XML observado:
  - `Helicoidal` se serializa como `MachiningStrategy = b:HelicMilling`
  - `Profundidad hueco` -> `AxialCuttingDepth`
  - `Habilitar pasada final` -> `AllowsFinishCutting`
  - `Ultimo hueco` -> `AxialFinishCuttingDepth`
- Parametros estrategicos constantes en los seis casos del circulo:
  - `AllowMultiplePasses = false`
  - `Overlap = 0`
  - `Cutmode = Climb`
  - `RadialCuttingDepth = 0`
  - `RadialFinishCuttingDepth = 0`
  - `StrokeConnectionStrategy = Straghtline`
  - `SideOfFeature = Left`
  - `Approach.IsEnabled = false`
  - `Retract.IsEnabled = false`
  - `ActivateCNCCorrection = false`
- Cambio estructural inmediato respecto del archivo base:
  - en `Tapa_v11_sintetizada.pgmx`, el circulo tenia:
    - `TrajectoryPath = GeomCompositeCurve` con `2` semicircunferencias planas
      a `z = 0`
    - `Approach = GeomTrimmedCurve`
    - `Lift = GeomTrimmedCurve`
    - `ActivateCNCCorrection = true`
  - al activar `Helicoidal`, el `Approach` y el `Lift` se mantienen como
    `GeomTrimmedCurve`, pero:
    - `ActivateCNCCorrection: true -> false`
    - el `TrajectoryPath` pasa a contener una helice 3D continua y, si
      corresponde, una vuelta final plana a `z = 0`
- Patron topologico observado en el circulo:
  - una vuelta helicoidal completa ocupa `2` miembros curvos
  - cada semicircunferencia helicoidal baja `PH / 2`
  - con `pasada final deshabilitada`, el toolpath termina cuando la helice
    alcanza `z = 0`
  - con `pasada final habilitada` y `UH = 0`, Maestro agrega `1` vuelta plana
    final a `z = 0`, compuesta por `2` miembros curvos
  - con `pasada final habilitada` y `UH > 0`, Maestro:
    - detiene la helice en `z = UH`
    - agrega `1` conector lineal vertical hasta `z = 0`
    - agrega `1` vuelta plana final a `z = 0`
- Conteos y cotas observadas:
  - `PH0_PasadaFinal_Deshabilitada`
    - `TrajectoryPath` con `2` miembros
    - cotas muestreadas: `18`, `9`, `0`
  - `PH5_PasadaFinal_Deshabilitada`
    - `TrajectoryPath` con `8` miembros
    - descomposicion: `8 = 2 + 2 + 2 + 2`
    - cotas muestreadas: `18`, `15.5`, `13`, `10.5`, `8`, `5.5`, `3`, `1.5`,
      `0`
  - `PH0_PasadaFinal_Habilitada_UH0`
    - `TrajectoryPath` con `4` miembros
    - descomposicion: `4 = 2 helicoidales + 2 planos finales`
    - cotas muestreadas: `18`, `9`, `0`, `0`, `0`
  - `PH5_PasadaFinal_Habilitada_UH0`
    - `TrajectoryPath` con `10` miembros
    - descomposicion: `10 = 8 helicoidales + 2 planos finales`
    - cotas muestreadas: `18`, `15.5`, `13`, `10.5`, `8`, `5.5`, `3`, `1.5`,
      `0`, `0`, `0`
  - `PH5_PasadaFinal_Habilitada_UH1`
    - `TrajectoryPath` con `11` miembros
    - descomposicion: `11 = 8 helicoidales + 1 vertical + 2 planos finales`
    - cotas muestreadas: `18`, `15.5`, `13`, `10.5`, `8`, `5.5`, `3`, `2`,
      `1`, `0`, `0`, `0`
  - `PH5_PasadaFinal_Habilitada_UH10`
    - `TrajectoryPath` con `7` miembros
    - descomposicion: `7 = 4 helicoidales + 1 vertical + 2 planos finales`
    - cotas muestreadas: `18`, `15.5`, `13`, `11.5`, `10`, `0`, `0`, `0`
- Patron espacial observado:
  - el arranque del circulo helicoidal sigue cayendo en el mismo punto XY del
    circulo compensado:
    - `x = 281.32`
    - `y = 200`
  - esto sigue coincidiendo con:
    - centro nominal `(200, 200)`
    - radio nominal `90.5`
    - compensacion `Left` con `E001` (`tool_width = 18.36`)
    - radio efectivo `90.5 - 9.18 = 81.32`
  - cuando `UH > 0`, el conector vertical de terminacion tambien cae en ese
    mismo XY
- `Approach` y `Lift` del circulo:
  - se mantienen constantes en los seis archivos
  - `Approach` baja siempre de `z = 38` a `z = 18`
  - `Lift` sube siempre de `z = 0` a `z = 38`
  - a diferencia de `Unidireccional + EnLaPieza`, la estrategia helicoidal no
    modifica la cota final del `Approach`
- Lo que no cambia en `LAV_1`:
  - `MachiningStrategy` sigue en `nil`
  - `Approach` sigue como `GeomCompositeCurve` de `2` miembros
  - `TrajectoryPath` sigue como `GeomCompositeCurve` de `9` miembros
  - `Lift` sigue como `GeomCompositeCurve` de `2` miembros
- Conclusiones provisionales:
  - para un circulo cerrado, `Helicoidal` no se modela como una secuencia de
    vueltas 2D a distintas cotas enlazadas por conectores explicitos
  - el desbaste queda serializado como una helice 3D continua, compuesta por
    semicircunferencias con descenso axial incorporado
  - `AxialCuttingDepth` controla el descenso total por vuelta completa:
    - cada semicircunferencia baja `PH / 2`
  - `AllowsFinishCutting` no altera el paso de la helice:
    - solo decide si se agrega o no una vuelta plana final a `z = 0`
  - `AxialFinishCuttingDepth` solo se vuelve visible cuando la pasada final
    esta habilitada:
    - fija la cota donde termina la helice de desbaste
    - y determina la bajada vertical restante hasta `z = 0`
  - `AllowMultiplePasses` permanece en `false` incluso cuando hay varias
    vueltas helicoidales, asi que no debe reutilizarse como indicador de
    multipaso real para esta familia

### Ronda 33 - Circulo `Antihorario` con correccion `Central/Derecha/Izquierda`

- Estado: completado
- Archivos revisados:
  - `archive/maestro_examples/Tapa_v11_sintetizada_Circulo_Antihorario_Correccion_Central.pgmx`
  - `archive/maestro_examples/Tapa_v11_sintetizada_Circulo_Antihorario_Correccion_Derecha.pgmx`
  - `archive/maestro_examples/Tapa_v11_sintetizada_Circulo_Antihorario_Correccion_Izquierda.pgmx`
- Referencia base usada para contrastar:
  - `archive/maestro_examples/Tapa_v11_sintetizada.pgmx`
- Hallazgo principal:
  - en esta familia, la variacion `Central/Derecha/Izquierda` no cambia ni la
    geometria nominal del circulo ni la ausencia de estrategia
  - lo que cambia es:
    - `Feature.SideOfFeature`
    - el radio efectivo del `Toolpath`
    - y por arrastre el punto XY de `Approach`, `TrajectoryPath` y `Lift`
- Parametros constantes en los tres archivos del circulo:
  - `Geometry = GeomCircle`
  - `Winding = CounterClockwise`
  - centro nominal `(200, 200)`
  - radio nominal `90.5`
  - `ActivateCNCCorrection = true`
  - `MachiningStrategy = nil`
  - `Approach.IsEnabled = false`
  - `Retract.IsEnabled = false`
  - `TrajectoryPath = GeomCompositeCurve` con `2` semicircunferencias planas
    a `z = 0`
  - `Approach` y `Lift` siguen como `GeomTrimmedCurve` verticales
- Mapeo observado de correccion:
  - `Central`
    - `SideOfFeature = Center`
    - radio efectivo del toolpath: `90.5`
    - punto de arranque: `(290.5, 200)`
  - `Derecha`
    - `SideOfFeature = Right`
    - radio efectivo del toolpath: `99.68 = 90.5 + 9.18`
    - punto de arranque: `(299.68, 200)`
  - `Izquierda`
    - `SideOfFeature = Left`
    - radio efectivo del toolpath: `81.32 = 90.5 - 9.18`
    - punto de arranque: `(281.32, 200)`
- Regla observada para circulo antihorario:
  - con `Winding = CounterClockwise`:
    - `Right` expande el radio
    - `Left` contrae el radio
    - `Center` conserva el radio nominal
- Hallazgo estructural importante:
  - la geometria declarada del circulo no se reescribe
  - en los tres archivos, el nodo geometrico sigue declarando:
    - centro `(200, 200)`
    - radio `90.5`
  - la correccion lateral aparece entonces como:
    1. declaracion semantica en `Feature.SideOfFeature`
    2. desplazamiento real en el `Toolpath`
- Topologia observada del circulo en los tres casos:
  - `TrajectoryPath` siempre ocupa `2` miembros:
    - semicircunferencia `0 -> pi`
    - semicircunferencia `pi -> 2pi`
  - por lo tanto, la correccion lateral no altera:
    - el conteo de miembros
    - el winding
    - la descomposicion topologica del contorno
  - solo altera el radio al que esas mismas semicircunferencias son ejecutadas
- `Approach` y `Lift` del circulo:
  - `Central`
    - `Approach`: `(290.5, 200, 38) -> (290.5, 200, 0)`
    - `Lift`: `(290.5, 200, 0) -> (290.5, 200, 38)`
  - `Derecha`
    - `Approach`: `(299.68, 200, 38) -> (299.68, 200, 0)`
    - `Lift`: `(299.68, 200, 0) -> (299.68, 200, 38)`
  - `Izquierda`
    - `Approach`: `(281.32, 200, 38) -> (281.32, 200, 0)`
    - `Lift`: `(281.32, 200, 0) -> (281.32, 200, 38)`
- Relacion con la pieza base actual:
  - el `Fresado` de `Tapa_v11_sintetizada.pgmx` ya coincide con el caso
    `Antihorario + Izquierda`
  - es decir:
    - `SideOfFeature = Left`
    - `Winding = CounterClockwise`
    - radio efectivo `81.32`
- Lo que no cambia en `LAV_1`:
  - `SideOfFeature` sigue en `Left`
  - `MachiningStrategy` sigue en `nil`
  - `Approach`, `TrajectoryPath` y `Lift` no cambian
- Conclusiones provisionales:
  - para un circulo cerrado sin estrategia axial, la correccion lateral sigue
    el mismo esquema conceptual ya observado en fresados lineales:
    - `Center` = nominal
    - `Right/Left` = offset real de `tool_width / 2`
  - en un circulo antihorario, el signo del offset queda fijado por el winding:
    - `Right` hacia afuera
    - `Left` hacia adentro
  - la futura API publica no deberia modelar esta correccion como un cambio de
    geometria nominal
  - la geometria debe seguir siendo el circulo nominal, y la correccion debe
    expresarse aparte mediante `SideOfFeature`
