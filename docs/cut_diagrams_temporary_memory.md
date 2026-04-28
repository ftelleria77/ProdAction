# Memoria Temporal De Diagramas De Corte

Este archivo registra el analisis incremental del generador de diagramas de
corte y sus metodos de optimizacion. La intencion es ordenar primero el
conocimiento actual, luego ampliar esta memoria con casos y criterios, y recien
despues modificar el codigo.

## Estado Inicial Del Relevamiento

Fecha de inicio: 2026-04-27.

No habia una memoria dedicada exclusivamente a diagramas de corte.

Registros parciales existentes:

- `README.md` menciona esquemas de corte basicos sobre tableros y el proximo
  paso historico `core.nesting.first_fit_2d`.
- `docs/en_juego_synthesis_temporary_memory.md` contiene reglas confirmadas
  para como una composicion `En-Juego` debe reemplazar piezas individuales en
  diagramas de corte.
- `core/nesting.py` contiene la implementacion real de expansion de piezas,
  agrupacion por material/espesor, algoritmos de ubicacion y render PDF.
- `app/ui.py` expone la accion "Diagramas de Corte" y la configuracion de
  cortes desde la interfaz.

## Flujo Actual De Alto Nivel

La UI ejecuta `ProjectDetailWindow.show_cuts()` en `app/ui.py`.

Ese metodo:

- valida que existan modulos cargados
- arma un proyecto filtrado por locales seleccionados
- lee settings globales desde `app_settings.json`
- resuelve ancho/alto base de tablero, separacion, adicional de escuadrado,
  espesor de sierra, tableros configurados y modo de optimizacion
- llama a `core.nesting.generate_cut_diagrams(...)`
- escribe `diagramas_corte_a4.pdf` en la carpeta raiz del proyecto

`generate_cut_diagrams(...)` es la API principal actual del motor de corte.

## Settings Actuales

En `app/ui.py` existen tres modos visibles:

- `Sin optimizar`
- `Optimizacion longitudinal`
- `Optimizacion transversal`

Los settings principales son:

- `cut_board_width`
- `cut_board_height`
- `cut_piece_gap`
- `cut_squaring_allowance`
- `cut_saw_kerf`
- `cut_optimization_mode`
- `available_boards`

La UI de `CutsDialog` permite editar:

- modo de optimizacion
- adicional para escuadrado
- espesor de sierra

La UI de `BoardsDialog` administra tableros disponibles para diagramas.

## Expansion De Piezas

La expansion ocurre en `_expand_project_pieces(...)` dentro de
`core/nesting.py`.

Reglas observadas:

- agrupa piezas por `(material/color, espesor)`
- ignora piezas sin espesor valido
- respeta cantidad de pieza y cantidad de modulo
- ordena piezas del modulo usando `PIECE_TYPE_ORDER`
- intenta usar dimensiones reales del programa PGMX cuando existen
- aplica adicional de escuadrado a la medida real de corte
- conserva medida final de pieza separada de medida real de corte
- puede dividir cantidad requerida por `program_piece_yield` cuando el programa .PGMX produce mas de una pieza
- omite piezas anotadas con `exclude_from_cut_diagrams`

## Regla En-Juego

La memoria `docs/en_juego_synthesis_temporary_memory.md` confirma que una
composicion `En-Juego` guardada reemplaza a las piezas individuales al generar diagramas de corte.

Resumen de la regla:

- las piezas originales marcadas como `en_juego = true` no se envian individualmente al optimizador
- se agrega una unica pieza compuesta
- sus dimensiones salen de la huella total guardada en `en_juego_layout`
- su color y espesor deben poder representarse como un unico grupo
- su veta no puede ser mixta
- aplica tanto a `Corte Manual` como a `Corte Nesting`

La implementacion esta en `_build_en_juego_cut_piece(...)`.

## Tableros

Si hay tableros configurados, `_resolve_board_definition(...)` busca uno por:

- mismo color/material
- mismo espesor con tolerancia de `0.01`

Si hay varios tableros compatibles, elige el de mayor area.

Si no hay lista de tableros configurados, se usan las dimensiones base:

- ancho por defecto: `cut_board_width`
- alto por defecto: `cut_board_height`

El margen del tablero se descuenta antes de optimizar y luego
`_apply_board_margin(...)` desplaza las piezas al sistema completo de placa.

## Veta Y Rotacion

La funcion `_orientation_options(...)` genera orientaciones posibles para cada
pieza.

Reglas observadas:

- si la pieza puede rotar y no es cuadrada, considera orientacion normal y rotada
- si pieza y tablero tienen veta definida, filtra orientaciones para preservar alineacion
- en modo longitudinal prioriza piezas con mayor alto efectivo
- en modo transversal prioriza piezas con mayor ancho efectivo
- sin optimizacion prioriza no rotar y luego ubicar piezas grandes primero.

## Revision Del Orden Inicial Para Guillotina

El orden actual no equivale a ordenar todas las piezas por tamano o area de
mayor a menor.

Conclusiones del codigo:

- las piezas no quedan finalmente ordenadas por modulo; el orden por modulo y
  por `PIECE_TYPE_ORDER` solo existe durante `_expand_project_pieces(...)`
- despues, cada grupo completo de mismo material/espesor se vuelve a ordenar
  con `_order_group_pieces(...)`
- las composiciones `En-Juego` se agregan al final del recorrido de cada modulo,
  pero tambien entran en ese ordenamiento por grupo antes de optimizar
- las copias de una misma pieza se agregan consecutivamente y, si empatan en la
  clave de orden, Python conserva ese orden relativo
- cuando dos o mas piezas empatan exactamente en la clave de orden, el orden
  previo de expansion si puede sobrevivir como desempate implicito

La clave actual de `_order_group_pieces(...)` en guillotina es:

- dimension primaria preferida
- dimension secundaria preferida
- area

En longitudinal, la dimension primaria es el alto efectivo. En transversal, la
dimension primaria es el ancho efectivo.

Por eso una pieza de menor area puede quedar antes que otra de mayor area si es
mas larga en el eje de optimizacion. Ejemplo conceptual en longitudinal:

- pieza A: `100 x 2000`, area `200000`
- pieza B: `1000 x 1000`, area `1000000`

Con la regla actual, A queda antes que B porque su alto efectivo `2000` supera a
`1000`, aunque B tenga mucha mas area.

Ademas, las primeras secciones no reflejan necesariamente el orden de la lista.
El algoritmo genera tamanos de seccion desde las dimensiones primarias posibles,
toma solo algunos tamanos mayores (`max_section_sizes`) y para cada seccion
resuelve una combinacion de piezas compatibles. Esa combinacion prioriza lideres
dimensionales y ajuste de la seccion, no simplemente "siguiente pieza mas
grande de la lista".

Dentro de una seccion, `candidate.selections` se ordena con
`_section_selection_sort_key(...)`:

- primero piezas que coinciden exactamente con el tamano primario de la seccion
- luego piezas similares
- luego mayor ocupacion secundaria
- luego mayor area

Esto puede hacer que una pieza visualmente pequena aparezca al inicio de una
seccion si coincide mejor con el tamano primario de esa seccion.

### Caso Observado: Prod 2026-02 / Vargas / BCO18MDF 18mm

Proyecto local:

- nombre: `Prod 2026-02`
- cliente: `Vargas`
- ruta registrada: `C:/Proyectos/Prod 01-2026 - Vargas`
- grupo revisado: `BCO18MDF`, espesor `18`
- modo actual: `Optimizacion longitudinal`
- tablero configurado: `2600 x 1830`, margen `10`, sin veta

En la placa 3 del grupo, el dibujo queda con secciones principales verticales:

- primera seccion: piezas `400 x 742` finales, corte `410 x 752`
- segunda seccion: pieza `464 x 701` final, corte `474 x 711`
- tercera seccion: pieza `610 x 873` final, corte `620 x 883`

La pieza grande no llega tarde por haber sido agregada al final. Al reconstruir
la lista `remaining` al inicio de la placa 3, el orden de entrada es:

1. `Lateral_Aplicado #3`, corte `620 x 883`, final `610 x 873`
2. `Lateral_Izq (Mod.1)`, corte `410 x 752`, final `400 x 742`
3. `Lateral_Der (Mod.1)`, corte `410 x 752`, final `400 x 742`
4. `Fondo_Cajon_Inf (Mod.3)`, corte `474 x 711`, final `464 x 701`
5. `Tras_Cajon_Inf (Mod.3)`, corte `260 x 711`
6. `Tras_Cajon_Sup (Mod.3)`, corte `260 x 711`

El orden visual diferente aparece por el puntaje de secciones:

- la seccion `410` hace coincidir exactamente dos laterales y suma mas
  `exact_area` que una seccion `620` con solo el `Lateral_Aplicado`
- el estado de tablero prioriza `grouped_area`/`exact_area` acumulada antes que
  respetar la pieza mas grande de la lista
- por eso la secuencia elegida puede ser `410`, `474`, `620`, aunque la pieza
  `620 x 883` fuera la primera restante

Hipotesis para optimizacion futura:

- si queremos que "piezas grandes primero" sea una regla fuerte, el puntaje de
  seccion/estado debe incluir una prioridad explicita por mayor pieza pendiente
  o mayor seccion primaria inicial
- si queremos cortes por familias dimensionales, el comportamiento actual es
  coherente, pero debe asumirse que puede dejar piezas grandes mas tarde
  visualmente

### Estrategia Experimental: Sin Veta Por Lado Mayor

Se decidio no tocar `core/nesting.py` para esta prueba. La variante vive en
`tools/cut_diagram_ordering_lab.py` como estrategia `no-grain-major-side`.

En modos guillotina longitudinal/transversal, cuando una pieza no tiene veta
(`PIECE_GRAIN_NONE`) la clave inicial de orden experimental es:

- mayor lado real de corte
- menor lado real de corte
- area real de corte

La intencion es probar si una pieza sin veta debe ordenarse sin depender de que
el lado mayor quede representado como alto o ancho efectivo. El flujo principal
queda intacto hasta validar resultados comparativos.

## Herramienta Experimental De Comparacion

Se agrego `tools/cut_diagram_ordering_lab.py` como laboratorio fuera del flujo
principal.

Objetivo:

- cargar un proyecto registrado
- aislar un grupo de color/material y espesor
- aplicar distintas estrategias de ordenamiento
- comparar el packer guillotina actual contra un packer experimental guiado por
  el orden recibido
- inspeccionar una placa puntual con piezas, medidas y posiciones

Ejemplo usado para el caso Vargas:

```powershell
python -m tools.cut_diagram_ordering_lab `
    --project-name "Prod 2026-02" `
    --material BCO18MDF `
    --thickness 18 `
    --strategy current `
    --strategy area-desc `
    --packer current `
    --packer order-driven `
    --show-board 3
```

Packers disponibles:

- `current`: usa `_pack_group_into_boards(...)`, es decir el algoritmo actual
- `measure-driven`: algoritmo experimental que ordena todas las medidas
  posibles de las piezas de mayor a menor y abre secciones desde la primera
  medida que quepa en el eje primario disponible
- `measure-match-split`: variante experimental de `measure-driven` que, despues
  de abrir una seccion, recorre subsecciones libres en orden superior/izquierdo
  y elige la pieza que mejor cubre el ancho disponible de la subseccion activa
- `measure-split`: variante experimental de `measure-driven` que, dentro de una
  seccion, mantiene rectangulos libres locales para permitir subsecciones
  laterales y debajo de cada pieza colocada
- `order-driven`: algoritmo experimental donde cada seccion nace de la primera
  pieza restante que entra en el tablero
- `surface-fit`: algoritmo experimental pensado para ordenar por superficie y,
  dentro de cada seccion, probar ambas orientaciones posibles para minimizar el
  sobrante en el eje secundario

Estrategias iniciales disponibles:

- `current`
- `input`
- `no-grain-major-side`
- `area-desc`
- `area-primary-desc`
- `max-side-desc`
- `primary-area-desc`
- `secondary-area-desc`

Resultado inicial observado:

- con el packer `current`, cambiar `current` por `area-desc` no altero la placa
  3 del caso Vargas, porque la seleccion de secciones domina el orden inicial
- con el packer `order-driven`, el ordenamiento si cambia fuertemente la
  composicion de la placa, por lo que sirve como banco de pruebas para estudiar
  criterios de orden antes de tocar el algoritmo principal

### Prueba: Superficie + Mejor Ajuste De Seccion

Comando:

```powershell
python -m tools.cut_diagram_ordering_lab `
    --project-name "Prod 2026-02" `
    --material BCO18MDF `
    --thickness 18 `
    --strategy area-desc `
    --packer current `
    --packer order-driven `
    --packer surface-fit `
    --show-board 3
```

Resultado en `BCO18MDF 18mm`:

- `current + area-desc`: 3 placas, 0 omitidas, utilizacion media `0.7358`
- `order-driven + area-desc`: 3 placas, 0 omitidas, utilizacion media `0.7358`
- `surface-fit + area-desc`: 4 placas, 0 omitidas, utilizacion media `0.5518`

Lectura preliminar:

- minimizar el sobrante dentro de cada seccion no garantiza menos placas
- al probar ambas orientaciones, `surface-fit` rota algunas piezas grandes para
  llenar mejor la altura/ancho secundario de la seccion
- esa decision puede consumir mas eje primario y abrir mas secciones, empeorando
  el resultado global
- para avanzar, conviene probar un puntaje mixto: buen llenado de seccion, pero
  penalizando fuertemente el consumo excesivo del eje primario o la creacion de
  nuevas secciones

### Prueba: Lista Descendente De Medidas

Se agrego el packer experimental `measure-driven`.

Metodologia:

1. Para cada pieza restante se generan entradas de medida desde todas sus
   orientaciones permitidas.
2. Cada entrada conserva:
   - pieza
   - ancho/alto resultante
   - si esta rotada
   - medida primaria que ocuparia como ancho de seccion
   - medida secundaria que ocuparia dentro de la seccion
3. Las entradas se ordenan de mayor a menor por medida primaria, area y medida
   secundaria.
4. Se abre una seccion con la primera medida que entra en el eje primario
   restante de la placa.
5. Se coloca la pieza asociada y se retira esa pieza de las candidatas.
6. En la misma seccion se siguen colocando piezas segun la lista descendente de
   medidas, siempre que entren en el ancho de seccion y en el espacio secundario
   restante.
7. Cuando ninguna medida entra en esa seccion, se abre una nueva seccion con la
   primera medida que quepa en el espacio primario sobrante.

Comando:

```powershell
python -m tools.cut_diagram_ordering_lab `
    --project-name "Prod 2026-02" `
    --material BCO18MDF `
    --thickness 18 `
    --strategy input `
    --packer current `
    --packer measure-driven `
    --show-board 3
```

Resultado en `BCO18MDF 18mm`:

- `current + input`: 3 placas, 0 omitidas, utilizacion media `0.7358`
- `measure-driven + input`: 3 placas, 0 omitidas, utilizacion media `0.7358`

Lectura preliminar:

- mantiene la misma cantidad total de placas que el algoritmo actual
- cambia significativamente la placa 3: pasa de 6 piezas en 3 secciones a 16
  piezas en 2 secciones
- usa rotaciones para convertir medidas grandes en ancho de seccion cuando la
  pieza no tiene veta
- parece una variante prometedora para estudiar diagramas mas compactos por
  placa, aunque falta revisar si el orden resultante es operativamente comodo
  para corte real

### Prueba: Medidas Descendentes Con Subsecciones

Se agrego el packer experimental `measure-split`.

Metodologia:

1. Igual que `measure-driven`, genera una lista descendente de todas las medidas
   posibles de las piezas restantes.
2. Abre una seccion con la primera medida que entra.
3. Dentro de esa seccion mantiene rectangulos libres locales.
4. Al colocar una pieza, divide el rectangulo libre usado en:
   - una subseccion lateral, a la derecha de la pieza
   - una subseccion inferior, debajo de la pieza
5. Sigue recorriendo la lista descendente de medidas para ubicar la primera pieza
   que entre en alguno de esos rectangulos libres.

Comando:

```powershell
python -m tools.cut_diagram_ordering_lab `
    --project-name "Prod 2026-02" `
    --material BCO18MDF `
    --thickness 18 `
    --strategy input `
    --packer current `
    --packer measure-driven `
    --packer measure-split `
    --show-board 3
```

Resultado en `BCO18MDF 18mm`:

- `current + input`: 3 placas, 0 omitidas, utilizacion media `0.7358`
- `measure-driven + input`: 3 placas, 0 omitidas, utilizacion media `0.7358`
- `measure-split + input`: 3 placas, 0 omitidas, utilizacion media `0.7358`

Lectura preliminar:

- en este caso `measure-split` produjo la misma placa 3 que `measure-driven`
- la placa 3 queda con 16 piezas en 2 secciones
- no se ve mejora adicional porque las medidas lideres elegidas para abrir
  seccion ya ocupan todo el ancho de seccion, dejando poca o ninguna subseccion
  lateral util
- la variante puede seguir siendo util para casos donde la pieza que abre la
  seccion no cubra el ancho completo o donde haya muchas piezas angostas que
  puedan combinarse lateralmente

### Prueba: Medidas Descendentes Con Mejor Coincidencia Local

Se agrego el packer experimental `measure-match-split`.

Metodologia:

1. Igual que `measure-driven`, genera la lista descendente de todas las medidas
   posibles.
2. La primera medida que entra abre la seccion y coloca la pieza asociada.
3. Cada pieza colocada divide el rectangulo libre en dos subsecciones:
   - una subseccion lateral
   - una subseccion inferior
4. A diferencia de `measure-split`, no toma simplemente la primera medida global
   que entra. Primero toma la subseccion libre activa en orden
   superior/izquierdo y prueba las medidas restantes para elegir la que deje
   menos ancho libre dentro de esa subseccion.

Comando:

```powershell
python -m tools.cut_diagram_ordering_lab `
    --project-name "Prod 2026-02" `
    --material BCO18MDF `
    --thickness 18 `
    --strategy input `
    --packer current `
    --packer measure-driven `
    --packer measure-split `
    --packer measure-match-split `
    --show-board 3
```

Resultado en `BCO18MDF 18mm`:

- `current + input`: 3 placas, 0 omitidas, utilizacion media `0.7358`
- `measure-driven + input`: 3 placas, 0 omitidas, utilizacion media `0.7358`
- `measure-split + input`: 3 placas, 0 omitidas, utilizacion media `0.7358`
- `measure-match-split + input`: 3 placas, 0 omitidas, utilizacion media
  `0.7358`

Lectura preliminar:

- para el caso Vargas, `measure-match-split` produjo la misma placa 3 que
  `measure-split`
- esto ocurre porque las subsecciones laterales que quedan despues de colocar
  piezas grandes no tienen suficiente ancho/alto compatible con las piezas
  pendientes
- el algoritmo queda disponible para probar casos donde existan piezas angostas
  o bajas que puedan completar esas subsecciones laterales
- PDF experimental generado:
  `C:/Proyectos/Prod 01-2026 - Vargas/diagramas_corte_a4_measure_match_split.pdf`

Revision de veta:

- en `BCO18MDF 18mm`, las 41 piezas llegan al optimizador como `Sin veta`
- las piezas con veta declarada del ejemplo estan en `ROBLE18 18mm`
- se detecto que algunas piezas `ROBLE18`, especialmente tapas de cajon, tienen
  las dimensiones finales en un eje y las dimensiones PGMX de corte en el eje
  invertido
- el algoritmo experimental ahora filtra orientaciones de piezas con veta
  usando los ejes finales de la pieza, no solo los ejes ya resueltos del PGMX
- con esta correccion, `measure-match-split` mantiene 1 placa para `ROBLE18`
  pero ubica las tapas como `806.1 x 353.6` y `806.1 x 180.4`, respetando la
  veta longitudinal del tablero
- el PDF experimental fue regenerado en la misma ruta

## Algoritmos De Ubicacion

Hay tres caminos internos.

### Sin Optimizar

`_pack_group_into_boards_free_rectangles(...)`

Metodologia actual:

- mantiene una lista de rectangulos libres
- prueba piezas restantes, orientaciones y rectangulos libres
- elige el mejor candidato por desperdicio y ajuste
- ubica la pieza, divide rectangulos libres y poda rectangulos contenidos
- repite hasta no poder ubicar mas piezas en el tablero

Este camino no genera guias de cortes principales.

### Optimizacion Longitudinal / Transversal

`_pack_group_into_boards_guillotine(...)`

Metodologia actual:

- activa cuando el modo es longitudinal o transversal
- trabaja por secciones tipo guillotina sobre un eje primario
- usa busqueda tipo beam search con ancho distinto segun si hay veta de tablero
- arma candidatos de seccion a partir de medidas posibles de piezas restantes
- selecciona combinaciones por area agrupada, area usada y avance sobre el eje
- genera `main_cut_positions` y `main_cut_orientation` para dibujar cortes
  principales

### Variante Dimension Scan

`_pack_group_into_boards_guillotine_dimension_scan(...)`

Metodologia actual:

- existe como variante interna de guillotina
- usa mas candidatos por estado que el algoritmo actual
- puntua por cantidad de piezas ubicadas, area usada, avance y cantidad de
  secciones
- se selecciona mediante `guillotine_algorithm='dimension-scan'`

Observacion: la UI actual no parece exponer esta variante; `show_cuts()` llama a
`generate_cut_diagrams(...)` sin pasar `guillotine_algorithm`, por lo que queda
el default `current`.

## Render Del PDF

El render ocurre en `_build_printable_pdf(...)` y `_build_board_print_image(...)`.

Metodologia actual:

- usa Pillow para generar imagenes por placa
- exporta PDF multipagina
- usa A4 vertical u horizontal segun proporcion del tablero
- dibuja encabezado con produccion, cliente, material, espesor, numero de placa,
  base, margen y veta
- dibuja cada pieza como rectangulo con color derivado del material
- dibuja cotas internas de corte de cada pieza
- dibuja etiqueta central con identificacion y medida final
- en guillotina dibuja guias punteadas de cortes principales
- si hay cortes principales verticales, dibuja cotas exteriores arriba
- si hay cortes principales horizontales, dibuja cotas exteriores a la derecha

## Preguntas Abiertas Para Optimizar

- Definir que significa "mejor" para el usuario: menos tableros, cortes mas
  simples, menos desperdicio, menos rotaciones, continuidad de veta, o menor
  tiempo de corte.
- Decidir si los modos longitudinal/transversal deben representar cortes reales
  de sierra o solo una preferencia de orientacion.
- Evaluar si `cut_piece_gap + cut_saw_kerf` como separacion total y
  `section_kerf = cut_saw_kerf` en guillotina duplican algun efecto o si
  representan dos conceptos distintos.
- Exponer o descartar la variante `dimension-scan`.
- Crear casos de prueba comparables para medir cantidad de tableros,
  utilizacion, piezas omitidas y legibilidad del diagrama.
- Revisar si la seleccion de tablero por mayor area alcanza cuando existen
  varios formatos del mismo material/espesor.
- Revisar si conviene soportar multiples formatos de tablero por grupo, no solo
  elegir uno.
- Revisar si la utilizacion debe calcularse contra area total del tablero o area
  util descontando margen.

## Proximo Paso Sugerido

Ordenar esta memoria en secciones estables:

- objetivos de optimizacion
- entradas y restricciones
- algoritmos actuales
- casos de prueba
- metricas de comparacion
- cambios propuestos

Despues, construir una bateria de escenarios antes de modificar el motor.
