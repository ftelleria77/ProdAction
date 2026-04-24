# Memoria Temporal En-Juego

Este archivo registra la base de trabajo para rehacer la sintesis del
`En-Juego`.

Estado actual:

- `app/ui.py` llama a `core/en_juego_synthesis.py`
- `core/en_juego_pgmx.py` fue eliminado porque el sistema aun no entro en
  produccion y no se conserva compatibilidad historica

La nueva estrategia debe:

- usar la disposicion relativa de piezas del panel de `Configurar En-Juego`
- leer los datos reales de cada `.pgmx` original con `tools/pgmx_snapshot.py`
- sintetizar la pieza compuesta con specs de `tools/synthesize_pgmx.py`

## Resumen Consolidado Del Flujo

- La UI usa `core/en_juego_synthesis.py` para crear el `.pgmx` compuesto.
- La disposicion del panel solo aporta composicion: identidad, posicion,
  rotacion y huella rectangular de cada instancia.
- Los mecanizados CAM reales se toman de los `.pgmx` originales mediante
  snapshot/adaptador.
- Se transfieren solo mecanizados de cara superior.
- Se excluye el escuadrado original de cada pieza.
- Se preserva el orden real de worksteps transferidos dentro de cada `.pgmx`.
- El escuadrado exterior global y las divisiones internas los genera el flujo
  `En-Juego`.
- El usuario decide si las divisiones se ejecutan antes o despues del
  escuadrado global.
- Las divisiones se calculan desde huellas rectangulares; el analisis de
  contornos reales complejos queda fuera del alcance inicial.
- En grillas, las divisiones deben ser lineas largas de borde a borde.
- En disposiciones escalonadas, se admiten polilineas/escalones por la linea
  media de la separacion.
- Primero se emiten divisiones completas de borde a borde y luego divisiones
  interrumpidas.
- La tolerancia confirmada es `0.1 mm`, evaluada por cada division.
- La sintesis debe bloquearse con aviso si hay solapes, separaciones no
  uniformes por division o distancias menores al diametro de la herramienta de
  division.
- La direccion de veta de la composicion se determina y guarda junto con la
  disposicion del `En-Juego`, tanto en corte manual como en nesting.
- En los diagramas de corte, las composiciones `En-Juego` reemplazan a las
  piezas involucradas al armar la lista que se envia al optimizador.

## Regla General

Se separan tres capas:

- visualizacion: queda en `app/ui.py` y no define la geometria CAM autoritativa
- lectura: sale de `tools/pgmx_snapshot.py`
- sintesis: sale de `tools/synthesize_pgmx.py`

## Datos Utiles Del Panel

El panel grafico aporta unicamente datos de composicion.

Por cada instancia:

- `instance_key`
- `piece_id`
- `copy_index`
- `x_mm`
- `y_mm`
- `rotation_deg`
- `color`
- `grain_direction`
- `grain_axis_local`
- `grain_axis_composition`

Estos datos representan:

- posicion relativa de cada pieza
- rotacion relativa de cada pieza
- identidad de cada copia dentro del conjunto
- color de la pieza asociada a la instancia
- direccion de veta efectiva de cada instancia dentro de la composicion

Ademas, al guardar la disposicion del `En-Juego`, debe persistirse metadata
global de composicion en `en_juego_composition`:

- `composition_grain_direction`
- `composition_grain_axis`
- `composition_grain_status`

Este guardado pertenece al panel de composicion y es independiente de que luego
se genere o no un `.pgmx`.

## Datos Utiles Del Modulo

Por cada `piece_row` seleccionado para `En-Juego`:

- `id`
- `name`
- `source`
- `thickness`
- `width`
- `height`
- `color`
- `grain_direction`
- `quantity`
- `en_juego`

Estos datos sirven para:

- vincular cada instancia con su `.pgmx` original
- validar espesor comun
- conservar metadatos de pieza
- conservar color/material visible de la pieza
- cubrir fallbacks si un snapshot viniera incompleto

## Datos Utiles Del Snapshot

Cada `.pgmx` original debe leerse con `read_pgmx_snapshot(...)`.

Bloques utiles:

- `workpiece`
- `planes`
- `geometries`
- `features`
- `operations`
- `working_steps`

Campos especialmente importantes:

- dimensiones reales del programa original desde `workpiece`
- geometria real desde `geometries`
- relacion `feature -> geometry`
- relacion `feature -> operation`
- `approach`, `retract`, `milling_strategy` y `toolpaths` desde `operations`
- orden real del workplan desde `working_steps`

## Datos Utiles De Configuracion

La sintesis debe tomar desde `Configurar En-Juego`:

- `origin_x`
- `origin_y`
- `origin_z`

Desde `Configurar Divisiones`:

- herramienta
- diametro
- pasante / no pasante
- profundidad / extra
- approach
- retract
- multipasada
- recorrido

Desde `Configurar Escuadrado`:

- herramienta
- diametro
- pasante / no pasante
- profundidad / extra
- approach
- retract
- sentido
- estrategia

## Regla Confirmada De Veta De Composicion

La direccion de veta del `En-Juego` guardado se determina a partir de la veta
efectiva de cada instancia colocada en el panel.

Esta regla pertenece al guardado de la composicion, no a la sintesis del
`.pgmx`. Debe aplicarse tambien cuando la opcion de corte sea `Corte Manual`.

No alcanza con copiar directamente el `grain_direction` original de la pieza,
porque el `.pgmx` original puede estar dibujado con sus ejes intercambiados
respecto de las dimensiones nominales de la pieza, y ademas la instancia puede
estar rotada dentro de la composicion.

Procedimiento confirmado:

1. Para cada instancia se toma el `grain_direction` original de la pieza:
   - `0`: sin veta
   - `1`: veta al alto
   - `2`: veta al ancho

2. Se determina el eje de veta local dentro del dibujo real de esa instancia.
   Para eso se comparan las dimensiones nominales de la pieza con las
   dimensiones dibujadas/guardadas en el layout (`width_mm`, `height_mm`).

3. Se aplica la rotacion de la instancia en la composicion:
   - con `rotation_deg = 0`, el eje local se conserva
   - con `rotation_deg = 90`, el eje local se intercambia: `X -> Y` y `Y -> X`

4. El resultado es el eje de veta efectivo dentro de la composicion:
   - eje `Y` de la composicion -> `composition_grain_direction = 1` / Alto
   - eje `X` de la composicion -> `composition_grain_direction = 2` / Ancho
   - sin piezas con veta -> `composition_grain_direction = 0`

Todas las piezas con veta deben coincidir en el mismo eje efectivo de
composicion. Si una instancia queda con veta efectiva en `X` y otra en `Y`, la
composicion tiene veta mixta y no puede representarse con una unica direccion
global sin avisar al usuario.

Los desplazamientos, separaciones y posiciones `x/y` no modifican la direccion
de veta. Solo importan:

- el `grain_direction` original
- la orientacion real del dibujo de la pieza
- la rotacion aplicada en el panel

## Regla Confirmada Para Diagramas De Corte

Al generar diagramas de corte, una composicion `En-Juego` guardada debe
reemplazar a las piezas individuales que la integran.

La sustitucion ocurre al armar la lista de piezas para optimizar:

- las piezas originales marcadas como `en_juego = true` no se envian
  individualmente al optimizador
- en su lugar se agrega una unica pieza compuesta `En-Juego`
- sus dimensiones salen de la huella total guardada en `en_juego_layout`
- su color sale de los colores guardados por instancia en el layout
- su espesor sale de las piezas originales involucradas
- su veta sale de `en_juego_composition`

Esta regla aplica tanto si el `En-Juego` esta configurado para `Corte Manual`
como para `Corte Nesting`; no depende de que exista o se genere un `.pgmx`.

Validaciones:

- si no hay layout guardado, no se aplica reemplazo
- si las piezas involucradas tienen distintos colores, no se puede formar una
  unica pieza compuesta para optimizar
- si tienen distintos espesores, no se puede formar una unica pieza compuesta
  para optimizar
- si la composicion tiene veta mixta, no se puede representar con una unica
  direccion de veta para optimizar

### Informacion visual de piezas en diagramas

En el esquema de corte, cada pieza debe distinguir dos medidas:

- medida final de la pieza
- medida real de corte en tablero

La etiqueta de identificacion de cada pieza debe mostrar:

- nombre/identificacion de la pieza
- medida del tamano final

Las cotas dibujadas sobre la pieza deben mostrar la medida real de corte:

- cota horizontal: ancho real de corte
- cota vertical: alto real de corte

Cuando hay adicional de escuadrado, ese adicional afecta a la medida real de
corte y por lo tanto debe verse reflejado en las cotas, pero no debe alterar la
medida final mostrada en la etiqueta.

Ademas, el esquema de cada tablero debe mostrar cotas exteriores para los
cortes principales de placa:

- si los cortes principales son verticales, las cotas se dibujan arriba de la
  placa
- si los cortes principales son horizontales, las cotas se dibujan a la derecha
  de la placa
- las cotas miden desde el borde de la placa al primer corte, entre cortes
  principales consecutivos, y desde el ultimo corte hasta el borde opuesto

El encabezado de cada hoja del diagrama debe organizarse asi:

- primera linea: datos de produccion y cliente
- segunda linea: color/material, espesor y leyenda `Placa n de total` por grupo
  de color/espesor
- tercera linea: datos tecnicos de base, margen y veta

No debe mostrarse en el encabezado:

- aprovechamiento
- leyenda de hoja A4/orientacion de pagina

## Reglas Confirmadas

1. La pieza resultante tendra como dimensiones la huella total del conjunto.

2. El origen de la pieza sintetizada saldra de la configuracion de
   `Configurar En-Juego`.

3. Se transferiran unicamente los mecanizados de la cara superior de las piezas
   originales.

4. Se excluira el escuadrado propio de cada pieza original.

5. Se creara un unico escuadrado nuevo siguiendo la huella total del conjunto,
   usando exclusivamente los parametros de `Configurar Escuadrado`.

6. Las divisiones entre piezas se generaran sobre la linea media de la
   separacion entre piezas, usando exclusivamente los parametros de
   `Configurar Divisiones`.

## Premisa Confirmada Del Sistema Local

Para construir la composicion `En-Juego`, primero se trabajara en un sistema
local de coordenadas cuyo origen cartesiano es `(0, 0)`.

Ese origen local se ubica en la interseccion entre:

- el borde izquierdo de la composicion
- el borde inferior de la composicion

Consecuencia operativa:

- todas las posiciones y rotaciones del layout se interpretan primero en este
  sistema local
- la huella total del conjunto tambien se calcula en este sistema local
- recien despues se aplican los valores `origin_x`, `origin_y` y `origin_z`
  configurados en `Configurar En-Juego` para la pieza sintetizada final

## Regla Confirmada De Traslacion Sin Rotacion

Si una pieza sin rotar esta ubicada en la posicion `(x0, y0)` dentro de la
composicion `En-Juego`, todas las coordenadas de sus geometrias pasan a quedar
referidas al origen local de la composicion.

Para transferir una coordenada `(x1, y1)` de una geometria original de la pieza
al sistema local de la composicion, basta con aplicar una traslacion directa:

- `x = x0 + x1`
- `y = y0 + y1`

Esta regla aplica al caso base sin rotacion.

Consecuencia operativa:

- el punto `(x1, y1)` de la pieza original se convierte en `(x0 + x1, y0 + y1)`
  dentro de la composicion
- el mismo criterio base debe aplicarse a vertices, centros, puntos de entrada,
  puntos de salida y demas coordenadas geometricas cuando la pieza no este
  rotada

## Regla Confirmada De Rotacion Y Traslacion

El panel de `Configurar En-Juego` ahora guarda `layout_version = 2` y conserva
dos capas de datos:

- datos visuales compatibles con el formato anterior: `x`, `y`, `rotation`
- datos normalizados para sintesis: `x_mm`, `y_mm`, `rotation_deg`,
  `footprint_x_mm`, `footprint_y_mm`, `footprint_width_mm`,
  `footprint_height_mm`, `width_mm`, `height_mm`

Para sintesis, `x_mm` y `y_mm` representan la posicion del punto `(0, 0)` CAM
de la pieza original despues de aplicar la rotacion y normalizar la composicion
al origen local inferior izquierdo.

Si una coordenada original de la pieza es `(x1, y1)`, y la instancia tiene:

- origen transformado `(x0, y0)`
- rotacion `a` en grados

entonces la coordenada transferida al sistema local de la composicion es:

- `x = x0 + x1 * cos(a) + y1 * sin(a)`
- `y = y0 - x1 * sin(a) + y1 * cos(a)`

Esta regla:

- se reduce a `x = x0 + x1`, `y = y0 + y1` cuando `a = 0`
- conserva el sentido geometrico de polilineas, circulos y taladros porque es
  una rotacion rigida sin espejo
- deja sin cambios `side_of_feature`, `winding`, herramienta, profundidad,
  approach, retract y estrategia
- aplica a puntos de lineas, vertices de polilineas, centros de circulos y
  centros de taladros

La implementacion inicial de esta regla quedo en `core/en_juego_transform.py`.

## Correccion Confirmada Del Panel De Composicion

El panel ya no debe usar `sceneBoundingRect()` como huella autoritativa para
espaciar piezas, porque incluye el trazo visual del rectangulo.

La huella nominal se calcula desde `mapRectToScene(rect())`.

Consecuencia validada:

- con herramienta de division de `4 mm`, la separacion normalizada entre piezas
  queda en `4 mm`
- se elimino el excedente de `1.3 mm` que provenia del trazo visual del panel

Al reabrir una disposicion ya guardada, el panel no debe ejecutar
automaticamente `enforce_minimum_piece_spacing()`, porque esa autocorreccion
puede reordenar piezas intencionalmente desplazadas. La separacion minima puede
aplicarse cuando el usuario cambia explicitamente el modo de corte o durante la
interaccion de arrastre, pero no como efecto secundario de abrir el dialogo.

El panel muestra una capa visual de cotas que no participa del guardado ni del
snap:

- cotas de separaciones mayores a la separacion minima vigente
- cotas de desfasajes entre bordes de piezas vecinas
- valores expresados en milimetros, recalculados al mover o rotar piezas

Estas cotas usan la misma huella nominal `mapRectToScene(rect())` que el layout
de sintesis.

Las cotas deben dibujarse fuera de las piezas, pero dentro de la huella de la
composicion siempre que haya espacio libre entre piezas. Al hacer click sobre
una cota se abre un editor numerico en milimetros y el panel desplaza la pieza
asociada hasta alcanzar el valor indicado:

- en cotas horizontales de separacion se mueve la pieza derecha
- en cotas verticales de separacion se mueve la pieza inferior
- en cotas de desfasaje se mueve la pieza comparada contra la primera pieza de
  referencia
- si el desfasaje es vertical, la cota se dibuja arriba de la pieza que esta
  mas abajo
- si el desfasaje es horizontal, la cota se dibuja hacia la derecha de la pieza
  que esta mas a la izquierda

## Criterio Confirmado Para Detectar El Escuadrado Original

El escuadrado original de cada pieza debe detectarse como un fresado que:

- recorre una polilinea cerrada
- da una vuelta completa por el borde exterior de la pieza
- puede estar en sentido horario o antihorario

La relacion entre sentido y correccion debe ser consistente:

- `Clockwise` / `CW` -> correccion `Left`
- `CounterClockwise` / `CCW` -> correccion `Right`

Por lo tanto, se consideran candidatos validos a escuadrado original:

- perfil exterior cerrado + `CW` + `Left`
- perfil exterior cerrado + `CCW` + `Right`

Y deben descartarse como escuadrado original:

- `CW` + `Right`
- `CCW` + `Left`
- correccion `Center`

La deteccion no debe depender de que el arranque este exactamente en el punto
medio del borde. Basta con que la polilinea cerrada recorra el borde exterior
completo, que su bbox coincida con la pieza y que la relacion
`winding -> side_of_feature` sea valida.

La deteccion del adaptador quedo ajustada en `tools/pgmx_adapters.py`.

## Definicion De Huella Total

La huella total del conjunto es el rectangulo minimo que contiene a todas las
piezas de la composicion ya posicionadas y rotadas.

Valores utiles:

- `min_x`
- `min_y`
- `max_x`
- `max_y`
- `ancho_total = max_x - min_x`
- `alto_total = max_y - min_y`

## Orden Confirmado De Worksteps

El nuevo programa `En-Juego` debe ordenar los worksteps en estos bloques base:

1. mecanizados superiores transferidos desde cada pieza original, excluyendo el
   escuadrado original y preservando el orden interno real del workplan de cada
   `.pgmx`
2. divisiones internas generadas por `En-Juego` y escuadrado exterior global
   generado por `En-Juego`, con orden configurable por el usuario
3. `Xn` final

Cuando haya varias instancias, el bloque de mecanizados transferidos se ordena
por instancia segun el orden de composicion resuelto para el layout.

La ventana `Configurar En-Juego` expone `division_squaring_order`:

- `division_then_squaring`: `Dividir -> Escuadrar`
- `squaring_then_division`: `Escuadrar -> Dividir`

Este control solo queda activo en modo `Corte Nesting`, igual que el cuadro
`Origen`.

## Datos No Autoritativos Para Sintesis

No deben usarse como fuente CAM:

- el preview SVG
- el dibujo interno del panel
- `parse_pgmx_for_piece(...)`
- los rectangulos visuales del panel
- los contornos inferidos desde la vista

## Memoria Operativa Recomendada

### `layout_memory`

- `instance_key`
- `piece_id`
- `copy_index`
- `source_pgmx`
- `x_mm`
- `y_mm`
- `rotation_deg`
- `color`
- `grain_direction`
- `grain_axis_local`
- `grain_axis_composition`

### `snapshot_memory`

- `source_pgmx`
- `workpiece`
- `planes`
- `geometries`
- `features`
- `operations`
- `working_steps`

### `settings_memory`

- `origin`
- `division_settings`
- `squaring_settings`

### `composition_memory`

- instancias resueltas
- transformaciones a aplicar a cada geometria original
- huella total del conjunto
- direccion de veta efectiva guardada de la composicion
- specs finales a sintetizar

## Objetivo Tecnico Inicial

La nueva sintesis debe:

1. leer la disposicion del panel
2. abrir el snapshot de cada `.pgmx` original
3. tomar solo mecanizados reales de la cara superior
4. excluir el escuadrado original de cada pieza
5. transformar la geometria segun `x`, `y` y `rotation`
6. calcular la huella total real de la composicion
7. sintetizar:
   - un escuadrado exterior global
   - las divisiones interiores
   - los mecanizados superiores transferidos

## Reglas Confirmadas Para Divisiones Complejas

### Vecindad valida

Dos piezas son vecinas candidatas cuando:

- sus huellas no se solapan
- estan separadas por una distancia positiva sobre `X` o sobre `Y`
- sus lados enfrentados comparten un tramo util sobre el eje perpendicular

Cuando la separacion es horizontal, se comparan las proyecciones verticales
de ambas piezas. Cuando la separacion es vertical, se comparan las
proyecciones horizontales.

Ejemplo de solape parcial de proyecciones:

- pieza A: `Y = 0..700`
- pieza B: `Y = 300..500`
- si B esta a la derecha de A, solo se enfrentan en el tramo `Y = 300..500`

Ese concepto sirve para detectar que tramo de lados realmente esta enfrentado.

### Grillas

Cuando la disposicion sea una grilla, las divisiones se generan como lineas
largas de borde a borde de la huella total, no como divisiones cortas
independientes por cada par de piezas.

### Divisiones escalonadas

Se permiten divisiones con polilineas/escalones cuando la disposicion no pueda
resolverse con una unica linea recta.

La division escalonada debe seguir la linea media de la separacion entre piezas.

### Prioridad de divisiones

Puede darse que una division entre dos piezas quede interrumpida por la linea de
division de una tercera pieza.

Orden confirmado:

1. primero las divisiones que pasan de un borde exterior al otro borde exterior
   de la huella total
2. despues las divisiones interrumpidas

### Validaciones que bloquean la sintesis

La sintesis no debe continuar y debe informar al usuario cuando:

- la separacion entre piezas no es uniforme
- se detectan solapes entre piezas
- alguna distancia entre piezas es menor que el diametro de la herramienta de
  division seleccionada

Las piezas del `En-Juego` son siempre rectangulares y el panel de visualizacion
solo permite rotaciones de `+/- 90` grados. Por lo tanto no se esperan
irregularidades geometricas.

Tolerancia confirmada:

- `0.1 mm`

Si una diferencia de posicion, alineacion o separacion supera `0.1 mm`, debe
asumirse como error, interrumpirse la sintesis y avisar al usuario.

La tolerancia se evalua por cada division, no globalmente en todo el
`En-Juego`.

### Fuente geometrica

Por ahora, para definir divisiones se usa la huella rectangular de composicion
guardada por el panel.

No se implementa todavia el analisis de contornos reales complejos. Si aparece
un caso puntual que lo requiera, se desarrollara en una ronda posterior.

## Pendientes

No quedan definiciones pendientes para las reglas iniciales de divisiones.
