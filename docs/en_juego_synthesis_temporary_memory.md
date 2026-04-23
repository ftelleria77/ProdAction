# Memoria Temporal En-Juego

Este archivo registra la base de trabajo para rehacer la sintesis del
`En-Juego` sin depender de `core/en_juego_pgmx.py`.

La nueva estrategia debe:

- usar la disposicion relativa de piezas del panel de `Configurar En-Juego`
- leer los datos reales de cada `.pgmx` original con `tools/pgmx_snapshot.py`
- sintetizar la pieza compuesta con specs de `tools/synthesize_pgmx.py`

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

Estos datos representan:

- posicion relativa de cada pieza
- rotacion relativa de cada pieza
- identidad de cada copia dentro del conjunto

## Datos Utiles Del Modulo

Por cada `piece_row` seleccionado para `En-Juego`:

- `id`
- `name`
- `source`
- `thickness`
- `width`
- `height`
- `grain_direction`
- `quantity`
- `en_juego`

Estos datos sirven para:

- vincular cada instancia con su `.pgmx` original
- validar espesor comun
- conservar metadatos de pieza
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

## Pendientes

Quedan por definir en rondas siguientes:

- criterio exacto para detectar el escuadrado original de cada pieza
- reglas para construir divisiones en composiciones complejas
- forma exacta de trasladar y rotar toolpaths y geometria transferida
- reglas de prioridad y orden de los worksteps del nuevo programa
